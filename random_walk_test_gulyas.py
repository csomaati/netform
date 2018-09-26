import random
from tools import helpers, misc
import argparse
import tools.progressbar1 as progressbar1
from tools.valley_free_tools import VFT as vft
import numpy as np
import logging
from itertools import repeat

misc.logger_setup()
logger = logging.getLogger('compnet.random_walking')
logging.getLogger('compnet').setLevel(logging.INFO)


def main():
    parser = argparse.ArgumentParser(description='SANDBOX mode. Write something useful here', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('network')
    parser.add_argument('meta')
    parser.add_argument('out')
    parser.add_argument('--route-count',
                        type=int, default=1000, dest='route_count')
    parser.add_argument('--try-per-trace',
                        type=int, default=1, dest='try_per_trace')
    parser.add_argument('--with-lp', action='store_true', dest='with_lp')

    # for paralelization
    parser.add_argument('--lower-bound', '-lb',
                        type=int, default=0, dest='lb')
    parser.add_argument('--upper-bound', '-ub',
                        type=int, default=-1, dest='ub')

    parser.add_argument('--progressbar', action='store_true')
    parser.add_argument('--verbose', '-v', action='count', default=0)

    arguments = parser.parse_args()

    g = helpers.load_network(arguments.network)
    meta = helpers.load_from_json(arguments.meta)
    out = arguments.out

    arguments.verbose = min(len(helpers.LEVELS), arguments.verbose)
    logging.getLogger('compnet').setLevel(helpers.LEVELS[arguments.verbose])

    max_c = len(meta)

    arguments.lb = arguments.lb if 0 <= arguments.lb <= max_c else 0
    arguments.ub = arguments.ub if 0 <= arguments.ub <= max_c else max_c

    arguments.lb, arguments.ub = (min(arguments.lb, arguments.ub),
                                  max(arguments.lb, arguments.ub))

    meta = meta[arguments.lb:arguments.ub]

    purify(g, meta, out,
           arguments.route_count,
           arguments.try_per_trace,
           arguments.progressbar,
           arguments.with_lp)


def purify(g, meta_original, out,
           count=1000, try_per_race=1, show_progress=False, with_lp=True):

    empty = 0
    # remove traces with already calculated random paths
    logger.warn('[r]ONLY NOT FILLED PATHS[/]')
    meta_filled = [x for x in meta_original
                   if helpers.RANDOM_WALK_RUN_COUNT not in x]

    # Filter if interested only in routes of stretch 1
    # meta_filled = [x for x in meta_original
    #                if x[helpers.TRACE_LEN]-x[helpers.SH_LEN] == 1]



    ## traces with a maximum stretch
    # logger.warn('[r]!!!ONLY WITH STRETCH[/]')
    # meta = [x for x in meta if x[helpers.STRETCH] > -1]

    # # shorter meta records
    # logger.warn('[r]!!!ONLY SHORT TRACES[/]')
    # meta = [x for x in meta if len(x[helpers.TRACE]) < 5]

    # meta_map = {tuple(x[helpers.TRACE]): x for x in meta_filled}

    logger.info('All trace count: %d' % len(meta_filled))
    tr_count = min(len(meta_filled), count)
    meta_random = random.sample(meta_filled, tr_count)
    logger.info('Chosen subset count: %d' % len(meta_random))

    # real_vf_degree = [x for x in meta_random if x[helpers.IS_VF_DEGREE] == 1]
    # real_nonvf_degree = [x for x in meta_random if x[helpers.IS_VF_DEGREE] == 0]
    # assert len(real_nonvf_degree) == tr_count - len(real_vf_degree)

    # real_vf_prelabeled = [x for x in meta_random if x[helpers.IS_VF_PRELABELED] == 1]
    # real_nonvf_prelabeled = [x for x in meta_random if x[helpers.IS_VF_PRELABELED] == 0]
    # assert len(real_nonvf_prelabeled) == tr_count - len(real_vf_prelabeled)

    # real_vf_closeness = [x for x in meta_random if x[helpers.IS_VF_CLOSENESS] == 1]
    # real_nonvf_closeness = [x for x in meta_random if x[helpers.IS_VF_CLOSENESS] == 0]
    # assert len(real_nonvf_closeness) == tr_count - len(real_vf_closeness)

    # logger.info('Real vf degree: %f[%d]' % ((len(real_vf_degree) / float(tr_count),
    #                                  len(real_vf_degree))))
    # logger.info('Real nonvf degree: %f[%d]' % ((len(real_nonvf_degree) / float(tr_count),
    #                                     len(real_nonvf_degree))))

    # logger.info('Real vf prelabeled: %f[%d]' % ((len(real_vf_prelabeled) / float(tr_count),
    #                                  len(real_vf_prelabeled))))
    # logger.info('Real nonvf prelabeled: %f[%d]' % ((len(real_nonvf_prelabeled) / float(tr_count),
    #                                     len(real_nonvf_prelabeled))))
    # logger.info('Real vf closeness: %f[%d]' % ((len(real_vf_closeness)/float(tr_count), len(real_vf_closeness))))
    # logger.info('Real nonvf closeness: %f[%d]' % ((len(real_nonvf_closeness)/float(tr_count), len(real_nonvf_closeness))))

    # traceroutes = [x[helpers.TRACE] for x in meta_random]
    # traceroutes = vft.trace_in_vertex_id(g, traceroutes)

    try:
       meta_random[0][helpers.TRACE]
    except Exception:
       meta_random = [{helpers.TRACE: x} for x in meta_random]

    progress = progressbar1.DummyProgressBar(end=10, width=15)
    if show_progress:
        progress = progressbar1.AnimatedProgressBar(end=len(meta_random),
                                                    width=15)

    stretch_list = []    
    max_stretch = max([x[helpers.TRACE_LEN] - x[helpers.SH_LEN] for x in meta_random])
    for stretch in range(0, max_stretch+1):
        metas = [x for x in meta_random
                 if x[helpers.TRACE_LEN] - x[helpers.SH_LEN] == stretch]
        stretch_list.extend(list(repeat(stretch, len(metas))))
        
    # print(stretch_list)    
    lenghts = random.shuffle(stretch_list)

    strx_array = []
    
    for idx, trace_meta in enumerate(meta_random):
        progress += 1
        progress.show_progress()
        # print(trace_meta[helpers.TRACE])
        shl = trace_meta[helpers.SH_LEN]
        trace = vft.trace_in_vertex_id(g, [trace_meta[helpers.TRACE], ])
        if len(trace) != 1:
            print 'PROBLEM'
            print trace_meta
            continue
        trace = trace[0]
        # print(trace)
        random_walk_closeness_route_vf = 0
        random_walk_closeness_route_lp_soft = 0
        random_walk_closeness_route_lp_hard = 0
        random_walk_degree_route_vf = 0
        random_walk_degree_route_lp_soft = 0
        random_walk_degree_route_lp_hard = 0
        random_walk_prelabeled_route_vf = 0
        random_walk_prelabeled_route_lp_soft = 0
        random_walk_prelabeled_route_lp_hard = 0

        s, t = trace[0], trace[-1]
        for counter in xrange(0, try_per_race):
            # random_path = helpers.random_route_walk(g, s, t, len(trace)) # Modified
            random_path = helpers.random_route_walk(g, s, t, shl+stretch_list[idx]) # Modified
            if len(random_path) == 0:
                empty += 1
            if vft.is_valley_free(g, random_path, vfmode=vft.CLOSENESS):
                random_walk_closeness_route_vf += 1
                if (len(random_path) == shl + 1):
                    strx_array.append(1) 
                if with_lp:
                    lp_soft = vft.is_local_preferenced(g, random_path,
                                                       first_edge=True,
                                                       vfmode=vft.CLOSENESS)
                    lp_hard = vft.is_local_preferenced(g, random_path,
                                                       first_edge=False,
                                                       vfmode=vft.CLOSENESS)
                    if lp_soft:
                        random_walk_closeness_route_lp_soft += 1
                    if lp_hard:
                        random_walk_closeness_route_lp_hard += 1
            else:
                if (len(random_path) == shl + 1):
                    strx_array.append(0) 
                        
            # if vft.is_valley_free(g, random_path, vfmode=vft.DEGREE):
            #     random_walk_degree_route_vf += 1
            #     if with_lp:
            #         lp_soft = vft.is_local_preferenced(g, random_path,
            #                                            first_edge=True,
            #                                            vfmode=vft.DEGREE)
            #         lp_hard = vft.is_local_preferenced(g, random_path,
            #                                            first_edge=False,
            #                                            vfmode=vft.DEGREE)
            #         if lp_soft:
            #             random_walk_degree_route_lp_soft += 1
            #         if lp_hard:
            #             random_walk_degree_route_lp_hard += 1

            # if vft.is_valley_free(g, random_path, vfmode=vft.PRELABELED):
            #     random_walk_prelabeled_route_vf += 1
            #     if with_lp:
            #         lp_soft = vft.is_local_preferenced(g, random_path,
            #                                            first_edge=True,
            #                                            vfmode=vft.PRELABELED)
            #         lp_hard = vft.is_local_preferenced(g, random_path,
            #                                            first_edge=False,
            #                                            vfmode=vft.PRELABELED)
            #         if lp_soft:
            #             random_walk_prelabeled_route_lp_soft += 1
            #         if lp_hard:
            #             random_walk_prelabeled_route_lp_hard += 1

            # sanity check
#             if random_path[0] != s or random_path[-1] != t:
#                 logger.error('ALERT')

            if len(random_path) != len(set(random_path)):
                logger.error('LENGTH ERROR')

        extra_meta = {
            helpers.RANDOM_WALK_RUN_COUNT: try_per_race,
            helpers.RANDOM_WALK_VF_CLOSENESS_ROUTE: random_walk_closeness_route_vf,
            helpers.RANDOM_WALK_VF_DEGREE_ROUTE: random_walk_degree_route_vf,
            helpers.RANDOM_WALK_VF_PRELABELED_ROUTE: random_walk_prelabeled_route_vf,
        }
        if with_lp:
            extra_meta.update({
                helpers.RANDOM_WALK_LP_SOFT_CLOSENESS_ROUTE: random_walk_closeness_route_lp_soft,
                helpers.RANDOM_WALK_LP_HARD_CLOSENESS_ROUTE: random_walk_closeness_route_lp_hard,
                helpers.RANDOM_WALK_LP_SOFT_DEGREE_ROUTE: random_walk_degree_route_lp_soft,
                helpers.RANDOM_WALK_LP_HARD_DEGREE_ROUTE: random_walk_degree_route_lp_hard,
                helpers.RANDOM_WALK_LP_SOFT_PRELABELED_ROUTE: random_walk_prelabeled_route_lp_soft,
                helpers.RANDOM_WALK_LP_HARD_PRELABELED_ROUTE: random_walk_prelabeled_route_lp_hard
            })

        trace_meta.update(extra_meta)

    ## save modified meta
    # all meta_* get only references from meta_original
    helpers.save_to_json(out, meta_random)
    # meta_mod = [x for x in meta_map.itervalues()]
    # helpers.save_to_json(out, meta_mod)

    # calculate results
    # real_vf = [x[helpers.IS_VF_CLOSENESS] for x in meta_random]
    # real_vf_ratio = np.mean(real_vf)

    random_walk_vf_ratio_per_element = [x[helpers.RANDOM_WALK_VF_CLOSENESS_ROUTE] / x[helpers.RANDOM_WALK_RUN_COUNT] for x in meta_random]
    random_walk_vf_ratio = np.mean(random_walk_vf_ratio_per_element)
    # print results
    logger.info('')
    logger.info('Empty: %d' % empty)
    logger.info('Tested trace count: %d' % len(meta_random))
    # logger.info('VF ratio in tested traces: %f' % real_vf_ratio)
    logger.info('VF ratio in random walks: %f' % random_walk_vf_ratio)
    logger.info('VF ratio in random walks for path stretch 1: %f' % np.mean(strx_array))

if __name__ == '__main__':
    main()

# def a(meta):
#  print '                 VF           NONVF          CLOSENESS'
#  for i in range(0, 18):
#   tmp = [x for x in meta if x[TRACE_LEN] == x[SH_LEN]+i]
#   if len(tmp) < 1: continue
#   vf = len([x for x in tmp if x[IS_VF] == 1])
#   vfcloseness = len([x for x in tmp if x[IS_VF_CLOSENESS] == 1])
#   nonvf = len([x for x in tmp if x[IS_VF] == 0])
#   # if i > 1:
#   #     k = [x[0] for x in tmp if x[IS_VF] == 1]
#   #     return k
#   allt = float(len(tmp))
#   print '%2d -- %5d[%6.2f%%]\t%5d[%6.2f%%]\t%5d[%6.2f%%]' % (i, vf, 100*(vf/allt), nonvf, 100*(nonvf/allt), vfcloseness, 100*(vfcloseness/allt))



# def vf(arr):
#     for i in range(0, len(arr)-2):
#         a, b, c = arr[i:i+3]
#         if (a>b and b==c) or (a>b and b<c) or (a==b and b==c) or (a==b and b<c): return False
#     return True


# import igraph as i
# import argparse
# from tools import helpers
# import random
# import copy
# import tools.progressbar1 as progressbar1
# from tools.valley_free_tools import VFT as vft
# import numpy as np
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_pdf import PdfPages

# # g_r_c = helpers.load_as_inferred_links('/mnt/ADAT/measurements3/data/airport/converted/topo_trace_rank_route_cheapest')
# g_r_c = i.load('/mnt/ADAT/measurements3/data/misc_networks/word_cooc.gml')
# degree_key = {x.index:g_r_c.degree(x.index) for x in g_r_c.vs}
# closeness_key = {x.index:g_r_c.closeness(x.index) for x in g_r_c.vs}
# max_random_graph = g_r_c.Degree_Sequence(g_r_c.degree(mode=i.ALL, loops=False), method='vl')
# rand_degree_key = {x.index:max_random_graph.degree(x.index) for x in max_random_graph.vs}
# rand_closeness_key = {x.index:max_random_graph.closeness(x.index) for x in max_random_graph.vs}


# def rich_club_coeff(g, k, ranks):
#     e_k = [x for x in g.es if ranks[x.source] >= k and ranks[x.target] >= k]
#     n_k = len([x for x in ranks.itervalues() if x >= k])

#     e_k2 = 2 * len(e_k)

#     if e_k2 < 1: return 0
#     if n_k < 2: raise RuntimeError('Never ever, previous if reached sooner')

#     fi_k = e_k2 / float(n_k * (n_k - 1))
#     return fi_k

# ratio_values = []
# steps = np.arange(min(closeness_key.itervalues()), max(closeness_key.itervalues())+1, 0.01)
# for k in steps:
#     fi = rich_club_coeff(g_r_c, k, closeness_key)
#     fi_ran = rich_club_coeff(max_random_graph, k, rand_closeness_key)
#     if fi_ran == 0: ratio = 0.0
#     else: ratio = fi/float(fi_ran)
#     ratio_values.append(ratio)

# # i.plot(g.degree_distribution(), log="xy")
# fig, ax = plt.subplots()
# ax.axhline(y=1, xmin=1, xmax=len(ratio_values))
# ax.plot(steps, ratio_values, 'o')
# ax.set_xlabel('k')
# ax.set_ylabel('P_ran(k)')
# ax.set_title('Rich club coeff ratio')
# ax.set_xscale('log')
# ax.set_yscale('log')
# # ax.set_ylim(0.0, max(2.0, max(ratio_values)))
# # ax.set_xlim([1, 10000])
# ax.yaxis.grid(True, which='major')

# plt.show()
