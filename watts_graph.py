import tools.progressbar1 as progressbar1
from tools import helpers, misc
import argparse
import logging
import igraph

misc.logger_setup()
logger = logging.getLogger('compnet.watts_graph_generator')
logging.getLogger('compnet').setLevel(logging.INFO)


def get_provider_edge_highest_closeness(g, watts_graph, n):
    neighbors = g.neighbors(n, mode=igraph.OUT)
    # no neighbors with higher closeness - root node
    if len(neighbors) == 0: return None
    closenesses = [(g.vs[x]['name'], g.vs[x]['closeness']) for x in neighbors]
    top_node = max(closenesses, key=lambda x: x[1])
    # out edge neihbors must has higher closeness
    assert n['closeness'] < top_node[1]
    watts_s = watts_graph.vs.find(n['name'])
    watts_t = watts_graph.vs.find(top_node[0])
    watts_eid = watts_graph.get_eid(watts_s, watts_t)
    return watts_eid


def get_watts_route(g, s, t):
    if isinstance(s, basestring):
        s = g.vs.find(s).index

    if isinstance(t, basestring):
        t = g.vs.find(t).index

    logger.debug('Get route from {s} to {t}'.format(s=g.vs[s]['name'],
                                                    t=g.vs[t]['name']))
    if s == t: return [s, ]
    # check customer cone
    neighbors = g.neighbors(s, mode=igraph.IN)
    logger.debug('Neighbors: %s' % [g.vs[x]['name'] for x in neighbors])
    distances = g.shortest_paths(source=neighbors,
                                 target=t,
                                 mode=igraph.IN)
    logger.debug('Distances: %s' % distances)
    candidates = zip(neighbors, [x[0] for x in distances])
    logger.debug('Candidates before filter: %s' % candidates)
    candidates = filter(lambda x: x[1] < float('inf'), candidates)
    logger.debug('Candidates after filter: %s' % [(g.vs[x[0]]['name'], x[1]) for x in candidates])

    if len(candidates) < 1:
        logger.debug('Provider mode')
        # provider
        eids = [g.get_eid(s, x) for x in g.neighbors(s, mode=igraph.OUT)]
        provider_eids = [x for x in eids if g.es[x]['provider'] == 1]
        if len(provider_eids) < 1: raise RuntimeError('No route')
        provider_eid = provider_eids[0]
        logger.debug('Provider: %s' % g.vs[g.es[provider_eid].target]['name'])
        provider = g.es[provider_eid].target
        next_hop = provider
    else:
        logger.debug('Customer mode')
        next_hop = min(candidates, key=lambda x: x[1])[0]
        # next_hop = random.choice(candidates)[0]
        logger.debug('Next hop: %s' % g.vs[next_hop]['name'])

    logger.debug('Before next recursion')
    # raw_input()
    return [s, ] + get_watts_route(g, next_hop, t)


def watts_trace_gen(g, traceroutes, show_progress=False):
    watts_traceroutes = []
    progress = progressbar1.DummyProgressBar(end=10, width=15)
    if show_progress:
        progress = progressbar1.AnimatedProgressBar(end=len(traceroutes), width=15)
    for trace in traceroutes:
        progress += 1
        progress.show_progress()
        s, t = trace[0], trace[-1]
        logger.debug('Get route from {s} to {t}'.format(s=s, t=t))
        logger.debug('Original trace[[g]%d[/]]: %s' % (len(trace), trace))
        try:
            watts_trace = get_watts_route(g, s, t)
            watts_trace = [g.vs[x]['name'] for x in watts_trace]
            watts_traceroutes.append(watts_trace)
            logger.debug('Watts trace[[p]%d[/]]: %s' % (len(watts_trace),
                                                        watts_trace))
        except RuntimeError:
            logger.warning('[b]No watts route[/]')

    return watts_traceroutes


def watts_converter(network, show_progress=False):
    logger.info('Get giant component')
    g = network.clusters().giant()
    logger.info('Calculate closeness')
    closenesses = []
    progress = progressbar1.DummyProgressBar(end=g.vcount(), width=15)
    if show_progress:
        progress = progressbar1.AnimatedProgressBar(end=g.vcount(), width=15)

    for x in g.vs:
        progress += 1
        progress.show_progress()
        closenesses.append(g.closeness(x, mode=igraph.ALL))
    g.vs['closeness'] = closenesses

    logger.info('Add edges')

    new_edge_list = []
    watts_graph = g.copy()
    watts_graph.delete_edges(watts_graph.es)
    watts_graph.to_directed()
    progress = progressbar1.DummyProgressBar(end=g.ecount(), width=15)
    if show_progress:
        progress = progressbar1.AnimatedProgressBar(end=g.ecount(), width=15)
    for e in g.es:
        progress += 1
        progress.show_progress()
        s, t = e.source, e.target
        if g.vs[s]['closeness'] > g.vs[t]['closeness']:
            t, s = s, t

        new_edge_list.append((s, t))

    watts_graph.add_edges(new_edge_list)
    for e in watts_graph.es:
        e['provider'] = False

    logger.info('Get provider edges')
    progress = progressbar1.DummyProgressBar(end=g.vcount(), width=15)
    if show_progress:
        progress = progressbar1.AnimatedProgressBar(end=g.vcount(), width=15)
    for n in g.vs:
        progress += 1
        progress.show_progress()
        provider_eid = get_provider_edge_highest_closeness(g, watts_graph, n)
        if provider_eid is None: continue
        watts_graph.es[provider_eid]['provider'] = True

    return watts_graph


def wrap_watts_trace_gen(args):
    g = helpers.load_network(args.network)
    traceroutes = helpers.load_from_json(args.original_traceroutes)
    max_c = len(traceroutes)
    args.lb = args.lb if 0 <= args.lb <= max_c else 0
    args.ub = args.ub if 0 <= args.ub <= max_c else max_c

    args.lb, args.ub = (min(args.lb, args.ub), max(args.lb, args.ub))
    traceroutes = traceroutes[args.lb:args.ub]

    watts_traceroutes = watts_trace_gen(g, traceroutes, args.progressbar)

    helpers.save_to_json(args.traceroute_dest, watts_traceroutes)


def wrap_watts_converter(args):
    g = helpers.load_network(args.source_network)
    watts_g = watts_converter(g, args.progressbar)
    watts_g.save(args.target)


def main():
    parser = argparse.ArgumentParser(description=('SANDBOX mode. ',
                                                  'Write something ',
                                                  'useful here'),
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--progressbar', action='store_true')
    parser.add_argument('--verbose', '-v', action='count', default=0)

    subparsers = parser.add_subparsers(help='Sub commands',
                                       dest='subcommand')

    convert_parser = subparsers.add_parser('convert',
                                           help='Convert different networks')
    convert_parser.add_argument('source_network',
                                help='source network path',
                                metavar='source_network')
    convert_parser.add_argument('target',
                                help='target file to save watts network')
    convert_parser.set_defaults(handler=wrap_watts_converter)

    trace_parser = subparsers.add_parser('trace_parser',
                                         help='Create traces based on original traceroutes')
    trace_parser.add_argument('network',
                              help='Watts like network path')
    trace_parser.add_argument('original_traceroutes',
                              metavar='original-traceroutes',
                              help='File path containing original traceroute paths')
    trace_parser.add_argument('traceroute_dest',
                              metavar='traceroute-dest',
                              help='File path to save new traceroutes, generated in watts like graph')
    # for paralelization
    trace_parser.add_argument('--lower-bound', '-lb', type=int,
                              default=0, dest='lb')
    trace_parser.add_argument('--upper-bound', '-ub', type=int,
                              default=-1, dest='ub')
    trace_parser.set_defaults(handler=wrap_watts_trace_gen)

    # LEVELS = [logging.CRIRTICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG, logging.NOTSET]
    LEVELS = [logging.ERROR,
              logging.WARNING,
              logging.INFO,
              logging.DEBUG,
              logging.NOTSET]

    arguments = parser.parse_args()

    arguments.verbose = min(len(LEVELS), arguments.verbose)
    logging.getLogger('compnet').setLevel(LEVELS[arguments.verbose])

    arguments.handler(arguments)


if __name__ == '__main__':
    main()
