import tools.progressbar1 as progressbar1
from tools import helpers, misc
from tools.valley_free_tools import VFT as vft, LinkDir
import igraph
import argparse
import logging
import collections
import random
import pretty_plotter
import numpy as np

misc.logger_setup()
logger = logging.getLogger('compnet.syntetic_routing')


def color_plot(g, g_col, g_labels, path):
    logger.info('Plot')
    e_colors = []
    for e in g_col.es:
        col = 'black' if e['dir'] == LinkDir.U else 'red'
        e_colors.append(col)
    igraph.plot(g, path, vertex_label=g_labels.vs['name'],
                edge_label=g_labels.es['dir'],
                vertex_size=0.2,
                edge_color=e_colors)


def trace_to_string(labeled_g, trace):
    edges = zip(trace, trace[1:])
    dirs = []
    for e in edges:
        UP, DOWN, PEER = 'U', 'D', 'P'
        g_edge = labeled_g.get_eid(e[0], e[1], True, False)
        ss = labeled_g.vs[labeled_g.es[g_edge].source]['name']
        if e[0] != ss:
            UP, DOWN = DOWN, UP
        if g_edge == -1: raise RuntimeError('No such edge %s' % (e, ))
        dir = labeled_g.es[g_edge]['dir']
        if dir == LinkDir.U: dirs.append(UP)
        elif dir == LinkDir.D: dirs.append(DOWN)
        elif dir == LinkDir.P: dirs.append(PEER)
        else: ajaj()

    return ''.join(dirs)


def main():
    parser = argparse.ArgumentParser(description=('Syntetic route generator'),
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--progressbar', action='store_true')
    parser.add_argument('--verbose', '-v', action='count', default=0)

    parser.add_argument('network')
    parser.add_argument('meta')
    parser.add_argument('all_trace_out', metavar='all-trace-out')
    parser.add_argument('syntetic_out', metavar='syntetic-out')
    parser.add_argument('--trace-count', '-tc', type=int,
                        dest='trace_count', default=5000)
    parser.add_argument('--random-sample', dest='random_sample',
                        action='store_true')

    parser.add_argument('--closeness-error', '-ce', type=float,
                        dest='closeness_error', default=0.0)

    parser.add_argument('--core-limit-percentile', '-cl', type=int,
                        dest='core_limit', default=0)

    parser.add_argument('--toggle-node-error-mode', action='store_true')

    arguments = parser.parse_args()

    arguments.verbose = min(len(helpers.LEVELS) - 1, arguments.verbose)
    logging.getLogger('compnet').setLevel(helpers.LEVELS[arguments.verbose])

    show_progress = arguments.progressbar

    g = helpers.load_network(arguments.network)
    g = g.simplify()

    meta = helpers.load_from_json(arguments.meta)

    if arguments.random_sample:
        random.shuffle(meta)

    meta = meta[:arguments.trace_count]

    N = g.vcount()

    cl = sorted([x['closeness'] for x in g.vs], reverse=True)
    logger.info('Min closeness: %s' % np.min(cl))
    logger.info('Max closeness: %s' % np.max(cl))
    logger.info('Mean closenss: %s' % np.mean(cl))
    logger.info('10%% closeness: %s' % np.percentile(cl, 10))
    logger.info('90%% closeness: %s' % np.percentile(cl, 90))

    logger.info('Core limit: [r]%d%%[/]' % arguments.core_limit)
    change_probability = 100 * arguments.closeness_error
    logger.info('Change probability: [r]%6.2f%%[/]' % change_probability)

    core_limit = np.percentile(cl, arguments.core_limit)
    logger.info('Core limit in closeness: [bb]%f[/]' % core_limit)

    if arguments.toggle_node_error_mode:
        logger.info('[r]Node error mode[/]')
        msg = ("If given node's closeness >= core_limit then the new ",
               "closeness in this node is ",
               #"rand(closeness_error ... old closeness)"
               "OLD_CLOSENSS * +/- closeness_error%")
        logger.info(''.join(msg))
        logger.info('Minimum node closeness: [g]%f[/]' % arguments.closeness_error)
        for n in g.vs:
            if n['closeness'] < core_limit:
                continue
            # sign = -1 if random.uniform(-1, 1) < 0 else 1
            # n['closeness'] = n['closeness'] * (1 + sign * arguments.closeness_error)

            new_closeness = random.uniform(arguments.closeness_error,
                                          n['closeness'])
            n['closeness'] = new_closeness

    g_labeled = vft.label_graph_edges(g, vfmode=vft.CLOSENESS)
    peer_edge_count = len([x for x in g_labeled.es if x['dir'] == LinkDir.P])
    logger.info('Peer edge count: %d' % peer_edge_count)

    changed_edges = []

    if not arguments.toggle_node_error_mode:
        msg = ("If the closeness values of the endpoints in given edge is ",
               "larger than the core_limit and ",
               "random(0,1) < closeness_error then change the direction ",
               "for this edge")
        logger.info(''.join(msg))

        changed_u = changed_d = 0
        changed_edges = []
        changed_edgess = []
        for edge in g_labeled.es:
            s, t = edge.source, edge.target
            s_cl = g_labeled.vs[s]['closeness']
            t_cl = g_labeled.vs[t]['closeness']

            if (s_cl < core_limit or t_cl < core_limit): continue
            if random.uniform(0, 1) > arguments.closeness_error: continue
            # if abs(s_cl - t_cl) / min(s_cl, t_cl) > 0.02: continue

            new_edge_dir = LinkDir.U if random.uniform(0, 1) > 0.5 else LinkDir.D
            
            if new_edge_dir != edge['dir']:
                if edge['dir'] == LinkDir.U:
                    changed_u += 1
                else:
                    changed_d += 1

                edge['dir'] = new_edge_dir
                changed_edges.append(edge)
                changed_edgess.append((edge.source, edge.target))

            # if edge['dir'] == LinkDir.U:
            #     changed_u += 1
            #     changed_edgess.append((edge.source, edge.target))
            #     edge['dir'] = LinkDir.D
            #     changed_edges.append(edge)
            # elif edge['dir'] == LinkDir.D:
            #     changed_d += 1
            #     changed_edgess.append((edge.source, edge.target))
            #     edge['dir'] = LinkDir.U
            #     changed_edges.append(edge)
        logger.info('E count: %d' % g_labeled.ecount())
        logger.info('Changed U: %d' % changed_u)
        logger.info('Changed D: %d' % changed_d)
        logger.info('Changed: %d' % (changed_d + changed_u))

    changed_e = [(g_labeled.vs[e.source]['name'], g_labeled.vs[e.target]['name']) for e in changed_edges]
    changed_e = changed_e + [(x[1], x[0]) for x in changed_e]

    changed_e = set(changed_e)

    vf_g_closeness = vft.convert_to_vf(g, vfmode=vft.CLOSENESS,
                                       labeled_graph=g_labeled)

    # e_colors = []
    # for e in vf_g_closeness.es:
    #     if e.source < N and e.target < N: col = 'grey'
    #     elif e.source < N and e.target >= N: col = 'blue'
    #     elif e.source >= N and e.target >= N: col = 'red'
    #     else: col = 'cyan'
    #     e_colors.append(col)
    # igraph.plot(vf_g_closeness, "/tmp/closeness.pdf",
    #             vertex_label=vf_g_closeness.vs['name'],
    #             vertex_size=0.2,
    #             edge_color=e_colors)

    pairs = [(g.vs.find(x[helpers.TRACE][0]).index,
              g.vs.find(x[helpers.TRACE][-1]).index,
              tuple(x[helpers.TRACE])) for x in meta]

    # pairs = list(set(pairs))

    # random.shuffle(pairs)

    # visited = set()
    # pairs2 = []
    # for x in pairs:
    #     k = (x[0], x[1])
    #     if k in visited: continue
    #     visited.add(k)
    #     visited.add((k[1], k[0]))
    #     pairs2.append(x)

    # pairs = pairs2

    traces = [x[2] for x in pairs]

    stretches = []
    syntetic_traces = []
    sh_traces = []
    base_traces = []
    original_traces = []
    bad = 0

    progress = progressbar1.DummyProgressBar(end=10, width=15)
    if show_progress:
        progress = progressbar1.AnimatedProgressBar(end=len(pairs), width=15)

    for s, t, trace_original in pairs:
        progress += 1
        progress.show_progress()

        trace_original_idx = [g.vs.find(x).index for x in trace_original]
        logger.debug('Original trace: %s -- %s -- %s', [g.vs[x]['name'] for x in trace_original_idx],
                         vft.trace_to_string(g, trace_original_idx, vft.CLOSENESS),
                         [g.vs[x]['closeness'] for x in trace_original_idx])

        sh_routes = g.get_all_shortest_paths(s, t)
        sh_len = len(sh_routes[0])

        sh_routes_named = [[g.vs[y]['name'] for y in x] for x in sh_routes]
        sh_trace_name = random.choice(sh_routes_named)
        base_trace_name = random.choice(sh_routes_named)

        candidates = vf_g_closeness.get_all_shortest_paths(s + N, t + N)
        candidates = [vft.vf_route_converter(x, N) for x in candidates]
        # candidates = []

        if len(candidates) == 0:
            candidates = vft.get_shortest_vf_route(g_labeled, s, t, mode='vf',
                                                   vf_g=vf_g_closeness,
                                                   _all=True,
                                                   vfmode=vft.CLOSENESS)

        if len(candidates) == 0:
            s_name, t_name = g.vs[s]['name'], g.vs[t]['name']
            logger.debug("!!!No syntetic route from %s to %s" % (s_name,
                                                                 t_name))
            continue

        logger.debug('Candidates from %s to %s:' % (g.vs[s]['name'],
                                                    g.vs[t]['name']))
        
        for c in candidates:
            logger.debug('%s -- %s -- %s' % ([g.vs[x]['name'] for x in c],
                                             vft.trace_to_string(g_labeled, c, vft.PRELABELED),
                                             [g.vs[x]['closeness'] for x in c]))

        chosen_one = random.choice(candidates)
        chosen_one_name = [g.vs[x]['name'] for x in chosen_one]

        # print chosen_one
        # print trace_original
        # pretty_plotter.pretty_plot(g, trace_original_idx,
        #                            chosen_one, changed_edgess,
        #                            spec_color=(0, 0, 0, 155))

        hop_stretch = len(chosen_one) - sh_len
        stretches.append(hop_stretch)

        trace_original_e = zip(trace_original, trace_original[1:])
        chosen_one_e = zip(chosen_one_name, chosen_one_name[1:])
        trace_affected = any([x in changed_e for x in trace_original_e])
        chosen_affected = any([x in changed_e for x in chosen_one_e])
        logger.debug('Trace affected: %s' % trace_affected)
        logger.debug('Chosen affected: %s' % chosen_affected)
        
        # if hop_stretch > 2:
        #     logger.debug('Base: %s' % trace_to_string(g_labeled, base_trace_name))
        #     logger.debug('SH: %s' % trace_to_string(g_labeled, sh_trace_name))
        #     logger.debug('Trace: %s' % trace_to_string(g_labeled, trace_original))
        #     logger.debug('Syntetic: %s' % trace_to_string(g_labeled, chosen_one_name))

        if trace_affected or chosen_affected or hop_stretch > 2:
            # pretty_plotter.pretty_plot_all(g, traces,
            #                                chosen_one, changed_edgess,
            #                                spec_color=(0, 0, 0, 255))
            bad += 1

        syntetic_traces.append(chosen_one_name)
        sh_traces.append(sh_trace_name)
        base_traces.append(base_trace_name)
        original_traces.append(trace_original)
        logger.debug('From %s to %s chosen one %s' % (g.vs[s]['name'],
                                                      g.vs[t]['name'],
                                                      chosen_one_name))

    result = zip(base_traces, sh_traces, original_traces, syntetic_traces)
    helpers.save_to_json(arguments.all_trace_out, result)
    helpers.save_to_json(arguments.syntetic_out, syntetic_traces)

    print 'Bad: %d' % bad

    c = collections.Counter(stretches)
    trace_count = len(syntetic_traces)
    logger.info('Stretch dist:')
    for k in c:
        logger.info('\t%d: %5.2f%%[%d]' % (k, 100 * c[k] / float(trace_count), c[k]))
    logger.info('Valid route count: %d' % trace_count)
    logger.info('Route count parameter: %d' % arguments.trace_count)
    logger.info('Generated valid pair count: %d' % len(pairs))

    # color_plot(g, g_labeled, g_labeled, '/tmp/after.pdf')
    
if __name__ == '__main__':
    main()
