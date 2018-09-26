import numpy
import random
import igraph
import argparse
from tools import helpers
import tools.progressbar1 as progressbar1

(TRACE, TRACE_LEN, SH_LEN, SH_VF_LEN, IS_VF, STRETCH,
 IN_VF_PRED, IS_LP_F, IS_LP_ALL, IS_VF_CLOSENESS) = range(0, 10)

def main():
    parser = argparse.ArgumentParser(description='Display statistical informations',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('network')
    parser.add_argument('metadata')
    parser.add_argument('--locations')
    parser.add_argument('out', type=str, help='Plot name pre')

    arguments = parser.parse_args()

    g = helpers.load_network(arguments.network)
    meta = helpers.load_from_json(arguments.metadata)
    if arguments.locations:
        locations = helpers.load_from_json(arguments.locations)
    else:
        locations = None

    f_name = arguments.out

    print
    print '------'
    print 'Graph: %s' % arguments.network
    print 'META: %s' % arguments.metadata
    print 'OUT: %s' % f_name
    print '------'
    print

    generate_db(g, meta, locations, f_name)

    # helpers.save_to_json(arguments.output, result)


def generate_db(g, meta, locations, f_name):

    print 'Traceroute count %d' % len(meta)
    meta = [x for x in meta if x[TRACE_LEN] - x[SH_LEN] > 0]
    print 'Stretched traceroute count %d' % len(meta)

    weights = {
        x['name']: {
            'sh': 0,
            'real': 0,
            'vfreal': 0,
            'randomsh': 0
        }
        for x in g.vs}

    random_paths = []

    if locations is None:
        rands = numpy.random.randint(0, 10000, len(weights) * 2)
        loc = zip(rands[::2], rands[1::2])
        locations = {n: {'x': loc[idx][0], 'y': loc[idx][1]} for idx, n in enumerate(weights.iterkeys())}

    # check locations
    delkeys = []
    for x in weights:
        try:
            locations[x]
        except KeyError:
            delkeys.append(x)

    print 'Get closeness'
    progress = progressbar1.AnimatedProgressBar(end=len(weights), width=15)
    for cntr, x in enumerate(weights):
        progress += 1
        progress.show_progress()
        weights[x]['closeness'] = g.closeness(x, mode=igraph.OUT)

    print 'Trace calculation'
    progress = progressbar1.AnimatedProgressBar(end=len(meta), width=15)
    for cntr, m in enumerate(meta):
        progress += 1
        progress.show_progress()
        trace = m[TRACE]
        # for x in trace:
        #     if x in delkeys: continue
        for node in trace:
            weights[node]['real'] += 1
            if m[IS_VF_CLOSENESS]:
                weights[node]['vfreal'] += 1

        sh_paths = g.get_all_shortest_paths(trace[0], trace[-1])
        sh_paths = [[g.vs[x]['name'] for x in p] for p in sh_paths]
        random_path = random.choice(sh_paths)
        random_paths.append(random_path)

        for node in random_path:
            weights[node]['randomsh'] += 1

        for sh_path in sh_paths:
            for node in sh_path:
                weights[node]['sh'] += 1

    print 'Delete nodes because has no location: %s' % delkeys
    g.delete_vertices([g.vs.find(x).index for x in delkeys])
    print 'Nodes remained in graph: %d' % g.vcount()

    with open('%s.csv' % f_name, 'w') as f:
        f.write('NODE;CLOSENESS;X;Y;SH;REAL;VFREAL;RANDOMSH\n')
        for node, w in weights.iteritems():
            struct = '{node};{closeness};{locx};{locy};{sh};{real};{vfreal};{randomsh}\n'
            f.write(struct.format(node=node, sh=w['sh'], real=w['real'],
                                  vfreal=w['vfreal'], randomsh=w['randomsh'],
                                  closeness=w['closeness'],
                                  locx=float(locations[node]['x']),
                                  locy=float(locations[node]['y'])))

    randomsh_hops = [y for x in random_paths for y in zip(x, x[1:])]
    randomsh_edges = (dict(source=s, target=t) for s, t in randomsh_hops)
    randomsh_graph = igraph.Graph.DictList(edges=randomsh_edges, vertices=None)
    randomsh_graph.simplify()
    randomsh_graph.save('%srandomsh.gml' % f_name)

    trace_hops = [y for x in meta for y in zip(x[TRACE], x[TRACE][1:])]
    trace_edges = (dict(source=s, target=t) for s, t in trace_hops)
    trace_graph = igraph.Graph.DictList(edges=trace_edges, vertices=None)
    trace_graph.simplify()
    trace_graph.save('%strace.gml' % f_name)

    g.save('%scalculation_graph.gml' % f_name)


if __name__ == '__main__':
    main()
