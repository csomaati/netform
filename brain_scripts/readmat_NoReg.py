import sys
sys.path.append("..")

# import copy
import scipy.io as sio
import numpy as np
import json
import igraph
import logging
import random
import copy
import argparse
from tools import helpers, misc
import tools.progressbar1 as progressbar1


(MSG_MEASUREMENT, MSG_FINISHED,
 MSG_PERPATHALL, MSG_PERPATHREAL, MSG_PEREND) = range(0, 5)

X, Y, Z = range(0, 3)

misc.logger_setup()
logger = logging.getLogger('compnet.brain_logger')
logger.setLevel(logging.INFO)
np.set_printoptions(precision=2)


def meta_analyzer(meta):
    logger.info('                 [bb]VF[/]           [bb]NONVF[/]')
    for i in range(-9, 18):
        tmp = [x for x in meta if x[helpers.SH_LEN] * (1+0.1*(i-1)) < x[helpers.TRACE_LEN] and x[helpers.TRACE_LEN] <= x[helpers.SH_LEN] * (1 + 0.1*i)]
        if len(tmp) < 1: continue
        vf = len([x for x in tmp if x[helpers.IS_VF_CLOSENESS] == 1])
        len_tmp = [x[helpers.TRACE_LEN] for x in tmp]
        # vfcloseness = len([x for x in tmp if x[IS_VF_CLOSENESS] == 1])
        nonvf = len([x for x in tmp if x[helpers.IS_VF_CLOSENESS] == 0])
        allt = float(len(tmp))
        logger.info('%2.3f < x < %2.3f -- %5d[%6.2f%%]\t%5d[%6.2f%%] -- %d/%4.2f/%d' % ((1+0.1*(i-1)), (1+0.1*i), vf, 100*(vf/allt), nonvf, 100*(nonvf/allt), min(len_tmp), np.mean(len_tmp), max(len_tmp)))


def meta_hop_analyzer(meta):
    logger.info('                 [bb]VF[/]           [bb]NONVF[/]')
    for i in range(0, 18):
        tmp = [x for x in meta if x[helpers.TRACE_LEN] == x[helpers.SH_LEN] + i]
        if len(tmp) < 1: continue
        vf = len([x for x in tmp if x[helpers.IS_VF_CLOSENESS] == 1])
        len_tmp = [x[helpers.TRACE_LEN] for x in tmp]
        # vfcloseness = len([x for x in tmp if x[IS_VF_CLOSENESS] == 1])
        nonvf = len([x for x in tmp if x[helpers.IS_VF_CLOSENESS] == 0])
        allt = float(len(tmp))
        logger.info('%d -- %5d[%6.2f%%]\t%5d[%6.2f%%] -- %d/%4.2f/%d' % (i, vf, 100*(vf/allt), nonvf, 100*(nonvf/allt), min(len_tmp), np.mean(len_tmp), max(len_tmp)))


def vf_ratio_analyzer(meta):
    print '        VF_RATIO          ORIG_RATIO'
    for i in range(0, 18):
        tmp = [x for x in meta if x[int(helpers.HOP_STRETCH)] == i]
        if len(tmp) < 1: continue
        real = np.mean([x[helpers.VF_RATIO] for x in tmp])
        original = np.mean([x[helpers.VF_ORIG_RATIO] for x in tmp])
        comp_greedy = np.mean([x[helpers.GREEDY_COMP] for x in tmp])
        gt_greedy = np.mean([x[helpers.GREEDY_GT] for x in tmp])
        nons_greedy = np.mean([x[helpers.NONSTRICT_GREEDY] for x in tmp])
        print '%2d -- %6.2f\t\t%6.2f\t\t%6.2f\t%6.2f\t%6.2f' % (i, real, original, comp_greedy, gt_greedy, nons_greedy)


def distance(coord_s, coord_t):
    s = np.asarray(coord_s)
    t = np.asarray(coord_t)
    return np.linalg.norm(s - t)


def trace_length(g, trace):
    trace_length = 0
    edges = zip(trace, trace[1:])
    for edge in edges:
        eid = g.get_eid(edge[0], edge[1])
        trace_length += g.es[eid]['length']

    return trace_length


def is_greedy_nonstrict(g, trace):
    # print 'Trace: %s' % [g.vs[x]['name'] for x in trace]
    hops = zip(trace, trace[1:])
    dest = g.vs[trace[-1]]
    for hop in hops:
        s, t = g.vs[hop[0]], g.vs[hop[1]]
        distance_s_dest = distance(s['coord'], dest['coord'])
        distance_t_dest = distance(t['coord'], dest['coord'])
        if distance_s_dest < distance_t_dest:
            return False

    return True


def is_vf(trace):
    top_node = None
    for idx in range(0, len(trace) - 2):
        if trace[idx] > trace[idx + 1] and trace[idx + 1] < trace[idx + 2]:
            return (False, None)
        if trace[idx] < trace[idx + 1] and trace[idx + 1] > trace[idx + 2]:
            top_node = idx + 1
    return (True, top_node)

# == FILES == #
functional_path = 'agriffa_40subj_08012013_functional_NOGlobalRegression.mat'
structural_path = 'data_agulyas_23022016_agriffa.mat'

# == VARS == #
MAX_STRETCH = 4

# Resolution index
res = 4

# Id of participant
user_range = range(0, 40)

# Adjacency threshold
adjacency_threshold = 0.0001

# Time range for calculations
time_range = range(100, 200)

# Correlation boundaries
corr_limit = [0.90, 1]

# TS limit
ts_limit = 0.0

logger.info('Load functional measurements from [s]%s[/]' % functional_path)
functional_mat = sio.loadmat(functional_path,
                             variable_names=('TS', 'FC_pearson'))

logger.info('Load structural measurements from [s]%s[/]' % structural_path)
structural_mat = sio.loadmat(structural_path,
                             variable_names=('SC_density', 'centroids'))


logger.info('Generate adjacency matrix for all user')

# Unweighted case
adjacency_matrice = structural_mat['SC_density'][0, res][:, :, :]
adjacency_matrice[adjacency_matrice > adjacency_threshold] = 1
adjacency_matrice[adjacency_matrice <= adjacency_threshold] = 0

logger.info('Generate correlation matrix for all voxel pairs in al user')
correlation_matrix = functional_mat['FC_pearson'][0, res][:, :, :]
correlation_matrix[np.isnan(correlation_matrix)] = 0
correlation_matrix = (corr_limit[0] < correlation_matrix) * (correlation_matrix < corr_limit[1])

logger.info('Generate activity matrix for all user in all time slot')
activity_matrix = functional_mat['TS'][0, res][:, :, :]
activity_matrix[np.isnan(activity_matrix)] = 0
activity_tmp = np.copy(activity_matrix)
activity_matrix[activity_tmp > ts_limit] = 1
activity_matrix[activity_tmp <= ts_limit] = 0
del activity_tmp

voxel_coords = structural_mat['centroids'][0, res]

meta = []
vf_ratio = []

progress = progressbar1.AnimatedProgressBar(end=len(user_range)*len(time_range), width=15)

measurement_id = helpers.id_generator(32)
web_log = {
    'measurement_id': measurement_id,
    'msg_type': MSG_MEASUREMENT,
    'resolution': res,
    'user_range': user_range,
    'adjacency_threshold': adjacency_threshold,
    'time_range': time_range,
    'corr_limit': corr_limit,
    'max_stretch': MAX_STRETCH,
    'ts_limit': ts_limit
}
logger.log(misc.WEB, json.dumps(web_log))

body = """
Dear Sir/Madam
Somebody just started a new calculation.
The parameter set is:
max stretch = %d
res = %d
user_range = %s
adjacency_threshold = %f
time_range = %s
corr_limit = %s
TS_limit (aka gamma) = %s

Check out current results at: https://csoma.tmit.bme.hu/compnet/details.php?id=%s

Or all previous measurements at https://csoma.tmit.bme.hu/compnet/results.php
""" % (MAX_STRETCH, res, user_range, adjacency_threshold, time_range, corr_limit, ts_limit, measurement_id)
logger.log(misc.MAIL, body)

for user in user_range:

    msg = "Get structural map for user [bb]%d[/] as an igraph object" % user
    logger.info(msg)
    adjacency_matrix = adjacency_matrice[:, :, user]
    str_map_gt = igraph.Graph.Adjacency(adjacency_matrix.tolist(),
                                        mode=igraph.ADJ_UNDIRECTED)
    str_map_gt = str_map_gt.simplify()
    # inf_edge = [e.index for e in str_map_gt.es if e['weight'] == float('Inf')]
    # logger.debug('Infinite field count: %d' % len(inf_edge))
    # str_map_gt.delete_edges(inf_edge)

    logger.info("Initialize graph's variables")
    for node in str_map_gt.vs:
        node['name'] = 'user%02d_idx%d' % (user, node.index)
        node['closeness'] = str_map_gt.closeness(node)
        node['rank'] = str_map_gt.degree(node, mode=igraph.ALL)
        node['traces'] = dict()
        # coords in (X, Y, Z) format
        node['coord'] = (voxel_coords[node.index, X, user],
                         voxel_coords[node.index, Y, user],
                         voxel_coords[node.index, Z, user])
        node['X'] = voxel_coords[node.index, X, user]
        node['Y'] = voxel_coords[node.index, Y, user]
        node['Z'] = voxel_coords[node.index, Z, user]

    for edge in str_map_gt.es:
        s, t = edge.source, edge.target
        length = distance(str_map_gt.vs[s]['coord'],
                          str_map_gt.vs[t]['coord'])
        str_map_gt.es[edge.index]['length'] = length

    str_map_gt.save('brain_str_map_gt_user_SQ8t7_%d.gml' % user, format='gml')

    # Extract pairs with high correlation
    ids = np.argwhere(correlation_matrix[:, :, user])

    # remove duplicates
    sorted_ids = np.sort(ids).tolist()
    functionally_connected_pairs = list(set([tuple(x) for x in sorted_ids]))

    # pair_activity_matrix = np.zeros((len(functionally_connected_pairs),
    #                                  len(time_range)))

    # Activity matrix for a user
    user_activity = activity_matrix[:, :, user]

    real_connected_pairs_pertime = []
    trace_count_per_pontpair_pertime = []
    vf_trace_count_per_pontpair_pertime = []
    active_node_count_pertime = []

    top_nodes = []
    top_nodes_pertime = []
    top_nodes_trace_pertime = []

    user_traces = []

    msg = 'Functionally connected node pairs: [b]{pairs}[/]'
    msg = msg.format(pairs=len(functionally_connected_pairs))
    logger.info(msg)

    # Generate graph for time instant t
    for time in time_range:
        progress += 1
        progress.show_progress()

        # Remove inactive nodes
        str_map = copy.deepcopy(str_map_gt)
        nodes_to_remove = np.argwhere(user_activity[:, time] == 0)
        str_map.delete_vertices(nodes_to_remove)
        # giant = str_map.clusters().giant()

        nodes_remained = [int(x['name'][10:]) for x in str_map.vs]

        active_node_count_pertime.append(str_map.vcount())

        current_top_nodes = []
        active_pair_counter = 0
        trace_count_per_pontpair = np.empty(len(functionally_connected_pairs))
        trace_count_per_pontpair.fill(np.NAN)
        vf_trace_count_per_pontpair = np.empty(len(functionally_connected_pairs))
        vf_trace_count_per_pontpair.fill(np.NAN)

        for idx, (s, t) in enumerate(functionally_connected_pairs):
            # Skip node pairs with non active nodes
            if (s not in nodes_remained) or (t not in nodes_remained): continue
            if s == t: continue

            # pair_activity_matrix[idx, time] = 1
            # continue

            active_pair_counter += 1
            # logger.debug('From [bb]%s[/] to [bb]%s[/]' % (s, t))

            # Nodes' ID in filtered graph (after node removal)
            component_s = str_map.vs.find(name='user%02d_idx%d' % (user, s))
            component_t = str_map.vs.find(name='user%02d_idx%d' % (user, t))

            all_path_vf = []
            real_path_vf = []

            gt_greedy = []
            nons_greedy = []
            component_greedy = []

            # possible 'real' traces
            component_paths = str_map.get_all_shortest_paths(component_s,
                                                             component_t)

            # No path with active nodes between s and t
            if len(component_paths) < 1 or len(component_paths[0]) < 1:
                continue

            component_paths = [random.choice(component_paths), ]

            len_component = len(component_paths[0])

            gt_path = str_map_gt.get_all_shortest_paths(s, t)
            len_original = len(gt_path[0])

            stretch = len_component - len_original

            if stretch > MAX_STRETCH: continue
            # if len_original * MAX_STRETCH < len_component: continue
            logger.debug('STRETCH: %f, LEGTH: %f, ORIGINAL:%f' % (stretch, len_component, len_original))

            distance_map = None
            # if len_component > 3:
            #    distance_map = np.asarray(str_map_gt.shortest_paths(target=t)) + 1
            # all_paths = helpers.dfs_mark(copy.deepcopy(str_map_gt), s, t, len_component, distance_map)
            all_paths = []
            all_long_paths = [x for x in all_paths if len(x) == len_component]

            logger.debug('Component path count: %d' % len(component_paths))
            for p in component_paths:
                nonstrict_greedy = is_greedy_nonstrict(str_map, p)
                is_vf_p, top_node = is_vf([str_map.vs[x]['closeness'] for x in p])
                top_node = p[top_node] if top_node is not None else None
                named_p = [str_map.vs[x]['name'] for x in p]
                user_traces.append(named_p)
                path_meta = {
                    helpers.TRACE: named_p,
                    helpers.TRACE_LEN: len_component,
                    helpers.SH_LEN: len_original,
                    helpers.IS_VF_CLOSENESS: is_vf_p,
                    helpers.HOP_STRETCH: stretch
                }
                meta.append(path_meta)
                real_path_vf.append(1 if is_vf_p else 0)
                nons_greedy.append(1 if nonstrict_greedy else 0)
                web_log = {
                    'measurement_id': measurement_id,
                    'msg_type': MSG_PERPATHREAL,
                    's': s,
                    't': t,
                    'path': p,
                    'is_vf': 1 if is_vf_p else 0,
                    'component_len': len_component,
                    'original_len': len_original,
                    'stretch': stretch,
                    'is_greedy': 1 if nonstrict_greedy else 0,
                    'user': user,
                    'time': time
                }
                logger.log(misc.WEB, json.dumps(web_log))
                if top_node is not None:
                    top_nodes.append(top_node)
                    current_top_nodes.append(top_node)

            trace_count_per_pontpair[idx] = len(component_paths)
            vf_trace_count_per_pontpair[idx] = sum(real_path_vf)

            for p in all_paths:
                is_vf_p, top_node = is_vf([str_map_gt.vs[x]['closeness'] for x in p])
                all_path_vf.append(1 if is_vf_p else 0)
                web_log = {
                    'measurement_id': measurement_id,
                    'msg_type': MSG_PERPATHALL,
                    's': s,
                    't': t,
                    'path': p,
                    'is_vf': 1 if is_vf_p else 0,
                    'path_length': len(p),
                    'component_len': len_component,
                    'original_len': len_original,
                    'stretch': stretch,
                    'user': user,
                    'time': time
                }
                logger.log(misc.WEB, json.dumps(web_log))

            vf_ratio.append(('-', len_component, len_original,
                             '-', stretch,
                             np.mean(real_path_vf), np.mean(all_path_vf),
                             np.mean(component_greedy), np.mean(gt_greedy),
                             max(nons_greedy)))

            web_log = {
                'measurement_id': measurement_id,
                'msg_type': MSG_PEREND,
                's': s,
                't': t,
                'component_path_count': len(component_paths),
                'gt_path_count': len(gt_path),
                'component_len': len_component,
                'gt_len': len_original,
                'all_long_path_count': len(all_long_paths),
                'component_path_vf_mean': np.mean(real_path_vf),
                'all_long_path_vf_mean': np.mean(all_path_vf),
                'nonstrict_greedy_mean': np.mean(nons_greedy),
                'user': user,
                'time': time
            }

            logger.log(misc.WEB, json.dumps(web_log))


            logger.debug('All path with length [bb]%d[/] has [p]%d[/] more elements' % (len_component, (len(all_long_paths) - len(component_paths))))
            logger.debug('REAL: %f[%d/%d] ALL: %f[%d/%d]' % (np.mean(real_path_vf), sum(real_path_vf), len(real_path_vf), np.mean(all_path_vf), sum(all_path_vf), len(all_path_vf)))

        real_connected_pairs_pertime.append(active_pair_counter)
        trace_count_per_pontpair_pertime.append(trace_count_per_pontpair)
        vf_trace_count_per_pontpair_pertime.append(vf_trace_count_per_pontpair)

        top_nodes_trace_pertime.append(len(current_top_nodes))
        current_top_nodes = set(current_top_nodes)
        top_nodes_pertime.append(len(current_top_nodes))

        # logger.info('Trace count: %d' % len(user_traces))
        helpers.save_to_json('traces_user_SQ8t7_%d.json' % user, user_traces)


    # print 'saved %s' % user
    # np.savetxt('user-small%s.csv' % user, pair_activity_matrix, delimiter=';')

    trace_count_per_pontpair_pertime = np.matrix(trace_count_per_pontpair_pertime)
    vf_trace_count_per_pontpair_pertime = np.matrix(vf_trace_count_per_pontpair_pertime)

    print
    tmp = [100 * x / float(len(functionally_connected_pairs))
               if len(functionally_connected_pairs) > 0 else 0
           for x in real_connected_pairs_pertime]
    logger.debug('Active pontpairs per timeslot in percentage: \n%s' % np.reshape(tmp, (-1, 10)))
    logger.debug('All trace count per timeslot: \n%s' % np.reshape(np.nansum(trace_count_per_pontpair_pertime, axis=1), (-1, 10)))
    logger.debug('VF  trace count per timeslot: \n%s' % np.reshape(np.nansum(vf_trace_count_per_pontpair_pertime, axis=1), (-1, 10)))
    logger.debug('AVG VF trace count per pontpair in timeslots: \n%s' % np.reshape(np.nanmean(vf_trace_count_per_pontpair_pertime, axis=1), (-1, 10)))
    logger.debug('Turn nodes in current user per timeslot \n%s' % np.reshape(top_nodes_pertime, (-1, 10)))
    logger.debug('Trace count with turn node per timeslot \n%s' % np.reshape(top_nodes_trace_pertime, (-1, 10)))
    logger.debug('Active node count per timeslot: \n%s' % np.reshape(active_node_count_pertime, (-1, 10)))
    logger.info('Turn node per user [p]%s[/] pert timeslot average [g]%s[/]' % (len(set(top_nodes)), np.mean(top_nodes_pertime)))
    logger.info('VF route ratio: %f[%d]' %  (np.nansum(vf_trace_count_per_pontpair_pertime) / np.nansum(trace_count_per_pontpair_pertime),np.nansum(vf_trace_count_per_pontpair_pertime)))
    logger.info('------------')

helpers.save_to_json('meta2.json', meta)
helpers.save_to_json('vf_ratio2.json', vf_ratio)
web_log = {
    'measurement_id': measurement_id,
    'msg_type': MSG_FINISHED
}
logger.log(misc.WEB, json.dumps(web_log))
body = """
Hey, a calculation finished just now.
The parameter set was:
max_stretch = %d
res = %d
user_range = %s
adjacency_threshold = %f
time_range = %s
corr_limit = %s
TS_limit (aka gamma) = %s

Check out new results at: https://csoma.tmit.bme.hu/compnet/details.php?id=%s

Or all previous measurements at https://csoma.tmit.bme.hu/compnet/results.php
""" % (MAX_STRETCH, res, user_range, adjacency_threshold, time_range, corr_limit, ts_limit, measurement_id)

logger.log(misc.MAIL, body)

meta_analyzer(meta)
meta_hop_analyzer(meta)
# vf_ratio_analyzer(vf_ratio)

traces = [x[helpers.TRACE] for x in meta]
helpers.save_to_json('traces.json', traces)
# vfcount = sum([x[3] for x in meta])
# print 'VF ratio: %f[%d/%d]' % (vfcount/len(meta), vfcount, len(meta))

# print(str_map.clusters())

# Unused code from here
# mat_structural['SC_density'][0,4][:,:,0][id[:,0],id[:,1]]
# mat_functional['FC_pearson'].shape
# mat_ts_reg = sio.loadmat('agriffa_40subj_08012013_functional_WithGlobalRegression.mat',variable_names='TS')

# mat_ts['TS'].shape
# mat_ts['TS'][0,4].shape

# Some plotting
# plt.figure(1)
# plt.subplot(211)
# plt.plot(mat_ts['TS'][0,4][-2,:,0])
# plt.subplot(212)
# plt.plot(mat_ts['TS'][0,4][0,:,0])
# plt.show()
