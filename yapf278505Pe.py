import tools.progressbar1 as progressbar1
from tools import helpers, misc
import igraph
from tools.valley_free_tools import VFT as vft, LinkDir
import argparse
import logging
import pretty_plotter
import collections
import random
import numpy as np

misc.logger_setup()
logger = logging.getLogger('compnet.syntetic_routing')
logging.getLogger('compnet').setLevel(logging.INFO)


def main():
    formatter = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(
        description=('Syntetic route generator'), formatter_class=formatter)

    parser.add_argument('--progressbar', action='store_true')
    parser.add_argument('--verbose', '-v', action='count', default=0)

    # for paralelization
    parser.add_argument('--lower-bound', '-lb', type=int, default=0, dest='lb')
    parser.add_argument(
        '--upper-bound', '-ub', type=int, default=-1, dest='ub')

    parser.add_argument('network')
    parser.add_argument('meta')
    parser.add_argument('out')

    subparsers = parser.add_subparsers(help=('Sub commands to switch '
                                             'between different functions'))

    trace_dir_help = 'Analyze original route direction decisions'
    trace_dir_arg = subparsers.add_parser('trace-dir', help=trace_dir_help)
    trace_dir_arg.set_defaults(dispatch=trace_dir)

    upwalker_help = 'How many up step required unnecessary?'
    upwalker_arg = subparsers.add_parser('upwalker', help=upwalker_help)
    upwalker_arg.add_argument(
        '--mode', default='count', choices=['count', 'deepness'])
    upwalker_arg.set_defaults(dispatch=upwalker)

    arguments = parser.parse_args()

    arguments.verbose = min(len(helpers.LEVELS), arguments.verbose)
    logging.getLogger('compnet').setLevel(helpers.LEVELS[arguments.verbose])

    g = helpers.load_network(arguments.network)
    g = g.simplify()

    meta = helpers.load_from_json(arguments.meta)
    meta = [
        m for m in meta
        if m[helpers.IS_VF_CLOSENESS] == 1 and len(m[helpers.TRACE]) > 1 and m[
            helpers.TRACE][0] != m[helpers.TRACE][-1]
    ]

    arguments.lb = arguments.lb if 0 <= arguments.lb <= len(meta) else 0
    arguments.ub = arguments.ub if 0 <= arguments.ub <= len(meta) else len(
        meta)
    meta = meta[arguments.lb:arguments.ub]

    vf_g = vft.convert_to_vf(g, vfmode=vft.CLOSENESS)

    arguments.dispatch(g, meta, vf_g, arguments)


def upwalker_deepness(g, meta, vf_g, arguments):
    N = g.vcount()
    progress = progressbar1.DummyProgressBar(end=10, width=15)
    if arguments.progressbar:
        progress = progressbar1.AnimatedProgressBar(end=len(meta), width=15)

    res = {'trace': [], 'sh': [], 'stretch': []}
    graph_max = max([x['closeness'] for x in g.vs])
    for m in meta:
        progress += 1
        progress.show_progress()

        trace = m[helpers.TRACE]
        s, t = trace[0], trace[-1]
        sh_trace = g.get_all_shortest_paths(s, t)
        sh_trace = random.choice(sh_trace)
        sh_closeness = [g.vs[x]['closeness'] for x in sh_trace]
        trace_closeness = [g.vs.find(x)['closeness'] for x in trace]

        stretch = m[helpers.HOP_STRETCH] if m[helpers.HOP_STRETCH] else len(
            trace) - len(sh_trace)
        trace_max = max(trace_closeness)
        sh_max = max(sh_trace)

        res['trace'].append([
            min(trace_closeness), np.average(trace_closeness),
            np.median(trace_closeness), np.max(trace_closeness)
        ])

        res['sh'].append([
            min(sh_closeness), np.average(sh_closeness),
            np.median(sh_closeness), np.max(sh_closeness)
        ])
        res['stretch'].append(stretch)

        with open('{}_trace{}'.format(arguments.out, len(trace)), 'a') as fo:
            for x in trace_closeness:
                fo.write('{} '.format(x / float(graph_max)))

            fo.write('\n')

        with open('{}_sh{}'.format(arguments.out, len(sh_trace)), 'a') as fo:
            for x in sh_closeness:
                fo.write('{} '.format(x / float(graph_max)))

            fo.write('\n')

    with open(arguments.out, 'w') as f:
        f.write(
            'TRACE_MIN\tTRACE_AVG\tTRACE_MEDIAN\tTRACE_MAX\tSH_MIN\tSH_AVG\tSH_MEDIAN\tSH_MAX\tTRACE_MAX\tGRAPH_MAX\tSH_MAX\tSTRETCH\n'
        )
        for idx in xrange(max(len(res['trace']), len(res['sh']))):
            f.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
                res['trace'][idx][0], res['trace'][idx][1], res['trace'][idx][
                    2], res['trace'][idx][3], res['sh'][idx][0], res['sh'][
                        idx][1], res['sh'][idx][2], res['sh'][idx][3],
                trace_max, graph_max, sh_max, res['stretch'][idx]))


def upwalker(g, meta, vf_g, arguments):
    if arguments.mode == 'count':
        upwalker_counter(g, meta, vf_g, arguments)
    elif arguments.mode == 'deepness':
        upwalker_deepness(g, meta, vf_g, arguments)
    else:
        raise RuntimeError("Unknown upwalk mode {}".format(arguments.mode))


def upwalker_counter(g, meta, vf_g, arguments):
    N = g.vcount()
    progress = progressbar1.DummyProgressBar(end=10, width=15)
    if arguments.progressbar:
        progress = progressbar1.AnimatedProgressBar(end=len(meta), width=15)

    # trace_up_map = {}
    # random_up_map = {}

    trace_up_counter = []
    random_up_counter = []

    for m in meta:
        progress += 1
        progress.show_progress()

        trace = m[helpers.TRACE]
        trace_dir = vft.trace_to_string(g, trace)
        trace_up_count = trace_dir.count('U')
        trace_up_counter.append(trace_up_count)
        # trace_up_map[trace_up_count] = trace_up_map.get(trace_up_count, 0) +
        # 1

        s, t = trace[0], trace[-1]
        s_idx, t_idx = vft.node_to_nodeid(g, s), vft.node_to_nodeid(g, t)

        random_vf_route = helpers.random_route_walk(
            vf_g,
            s_idx,
            t_idx + N,
            len(trace),
            named=False,
            weight_field='VFweight')
        random_vf_route = vft.vf_route_converter(random_vf_route, N)
        random_vf_dir = vft.trace_to_string(g, random_vf_route)
        random_vf_count = random_vf_dir.count('U')
        random_up_counter.append(random_vf_count)
        # random_up_map[random_vf_count] = random_up_map.get(random_vf_count,
        # 0) + 1

    real_counter = collections.Counter(trace_up_counter)
    real_up = ' '.join(
        ['%s: %s' % (k, real_counter[k]) for k in sorted(list(real_counter))])
    random_counter = collections.Counter(random_up_counter)
    random_up = ' '.join([
        '%s: %s' % (k, random_counter[k])
        for k in sorted(list(random_counter))
    ])

    logger.info('')
    logger.info('Real trace UP counter: %s' % real_up)
    logger.info('Random vf trace up counter: %s' % random_up)

    helpers.save_to_json(arguments.out, {
        'REAL': dict(real_counter),
        'RANDOM': dict(random_counter)
    })

    keys = sorted(set(list(real_counter) + list(random_counter)))
    logger.info('IDX;REAL;RANDOM')
    for k in keys:
        logger.info('%s;%d;%d' % (k, real_counter[k], random_counter[k]))


def trace_dir(g, meta, vf_g, arguments):
    N = g.vcount()
    vf_sum_lp_w = sum([e['LPweight'] for e in vf_g.es])

    out_instead_core = 0
    core_instead_out = 0
    in_customer = 0
    in_customer_but_use_up = 0

    progress = progressbar1.DummyProgressBar(end=10, width=15)
    if arguments.progressbar:
        progress = progressbar1.AnimatedProgressBar(end=len(meta), width=15)

    for m in meta:
        progress += 1
        progress.show_progress()

        trace = m[helpers.TRACE]
        first_edge = [trace[0], trace[1]]
        first_hop_type = vft.edge_dir(g, first_edge, vfmode=vft.CLOSENESS)
        s_idx = vft.node_to_nodeid(g, trace[0])
        t_idx = vft.node_to_nodeid(g, trace[-1])

        sh_vf = vf_g.get_all_shortest_paths(s_idx + N, t_idx + N)
        if len(sh_vf) > 0:
            in_customer += 1
            if first_hop_type != LinkDir.D:
                in_customer_but_use_up += 1

        if first_hop_type == LinkDir.D:
            # 'remove' all downward path:
            for neighbor in vf_g.neighbors(s_idx + N, mode=igraph.OUT):
                down_edge = vf_g.get_eid(s_idx + N, neighbor, directed=True)
                vf_g.es[down_edge]['LPweight_old'] = vf_g.es[down_edge][
                    'LPweight']
                vf_g.es[down_edge]['LPweight'] = vf_sum_lp_w + 1

            lp_sh = vft.get_shortest_vf_route(
                g, s_idx, t_idx, mode='lp', vf_g=vf_g, vfmode=vft.CLOSENESS)
            pretty_plotter.pretty_plot(g, trace, lp_sh, [])
            first_new_edge = [lp_sh[0], lp_sh[1]]
            first_new_hop_type = vft.edge_dir(
                g, first_new_edge, vfmode=vft.CLOSENESS)
            if first_hop_type != first_new_hop_type:
                out_instead_core += 1
                print ''
                print "Original trace: %s" % trace
                print 'Original trace dir: %s' % vft.trace_to_string(g, trace)
                print 'Original closeness: %s' % [
                    g.vs.find(x)['closeness'] for x in trace
                ]
                print 'LP trace: %s' % [g.vs[x]['name'] for x in lp_sh]
                print 'LP dir: %s' % vft.trace_to_string(g, lp_sh)
                print 'LP closeness: %s' % [
                    g.vs.find(x)['closeness'] for x in lp_sh
                ]
                # raw_input()
            for neighbor in vf_g.neighbors(s_idx + N, mode=igraph.OUT):
                down_edge = vf_g.get_eid(s_idx + N, neighbor, directed=True)
                vf_g.es[down_edge]['LPweight'] = vf_g.es[down_edge][
                    'LPweight_old']

        elif first_hop_type == LinkDir.U:
            lp_sh = vft.get_shortest_vf_route(
                g, s_idx, t_idx, mode='lp', vf_g=vf_g, vfmode=vft.CLOSENESS)
            lp_dir = vft.trace_to_string(g, lp_sh)

            # if lp_dir[1:].startswith('U') or lp_dir[1:].startswith('D'):
            #     continue
            first_new_edge = [lp_sh[0], lp_sh[1]]
            first_new_hop_type = vft.edge_dir(
                g, first_new_edge, vfmode=vft.CLOSENESS)
            if first_hop_type != first_new_hop_type:
                core_instead_out += 1
                print ''
                print "Original trace: %s" % trace
                print 'Original trace dir: %s' % vft.trace_to_string(g, trace)
                print 'Original closeness: %s' % [
                    g.vs.find(x)['closeness'] for x in trace
                ]
                print 'LP trace: %s' % [g.vs[x]['name'] for x in lp_sh]
                print 'LP dir: %s' % vft.trace_to_string(g, lp_sh)
                print 'LP closeness: %s' % [
                    g.vs.find(x)['closeness'] for x in lp_sh
                ]
                pretty_plotter.pretty_plot(g, trace, lp_sh, [])
                # raw_input()

    logger.info('Core instead down: %d' % core_instead_out)
    logger.info('Down instead core: %d' % out_instead_core)
    logger.info('In customer cone: %d' % in_customer)
    logger.info('In customer but use UP: %d' % in_customer_but_use_up)


if __name__ == '__main__':
    main()
