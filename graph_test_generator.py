import igraph
import random
import argparse
import logging

from tools import helpers, misc

misc.logger_setup()
logger = logging.getLogger('compnet.graph_test_gen')
logging.getLogger('compnet').setLevel(logging.INFO)
graphs = ['ring', 'star', '2tree', 'full']
graphs_map = {
    'ring': igraph.Graph.Ring,
    'star': igraph.Graph.Star,
    'full': igraph.Graph.Full
}


def main():
    parser = argparse.ArgumentParser(description=('Generate test graphs'),
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('graph_out', metavar='graph-out')
    parser.add_argument('trace_out', metavar='trace-out')
    parser.add_argument('--progressbar', action='store_true')
    parser.add_argument('--verbose', '-v', action='count', default=0)

    parser.add_argument('--node-count', '-nc', type=int,
                        dest='node_count', default=100)
    parser.add_argument('--network-type',
                        choices=[x for x in graphs_map.iterkeys()],
                        default='star')
    parser.add_argument('--trace-count', type=int, default=50)

    arguments = parser.parse_args()

    arguments.verbose = min(len(helpers.LEVELS), arguments.verbose)
    logging.getLogger('compnet').setLevel(helpers.LEVELS[arguments.verbose])

    show_progress = arguments.progressbar
    
    # g = graphs_map[arguments.network_type](arguments.node_count)
    # g = igraph.Graph.Barabasi(900, 9)
    # for n in g.vs:
    #     n['closeness'] = g.closeness(n)
    #     n['name'] = 'V%d' % n.index

    # g.save(arguments.graph_out)
    g = igraph.load(arguments.graph_out)

    pairs = [random.sample(xrange(0, g.vcount()), 2) for x in xrange(0, arguments.trace_count)]
    pairs = [[g.vs[x[0]]['name'], g.vs[x[1]]['name']] for x in pairs]

    traces = []
    for p in pairs:
        trace = random.choice(g.get_all_shortest_paths(p[0], p[1]))
        trace = [g.vs[x]['name'] for x in trace]
        traces.append(trace)

    helpers.save_to_json(arguments.trace_out, traces)

if __name__ == '__main__':
    main()
