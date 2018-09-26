from tools import helpers, misc
import logging
import argparse
import random
import tools.progressbar1 as progressbar1
import igraph
import numpy as np
from operator import itemgetter

misc.logger_setup()
logger = logging.getLogger('compnet.pretty_plotter')
logging.getLogger('compnet').setLevel(logging.INFO)

def main():
    parser = argparse.ArgumentParser(description='Pretty plot',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('network')
    parser.add_argument('meta')
    # parser.add_argument('output')

    parser.add_argument('--progressbar', action='store_true')
    parser.add_argument('--verbose', '-v', action='count', default=0)

    arguments = parser.parse_args()

    arguments.verbose = min(len(helpers.LEVELS), arguments.verbose)
    logging.getLogger('compnet').setLevel(helpers.LEVELS[arguments.verbose])

    g = helpers.load_network(arguments.network)
    meta = helpers.load_from_json(arguments.meta)

    edges = [(e.source, e.target) for e in g.es]
    rand_edges = random.sample(edges, 40)

    progress = progressbar1.DummyProgressBar(end=10, width=15)

    if arguments.progressbar:
        progress = progressbar1.AnimatedProgressBar(end=len(meta),
                                                    width=15)  

    for m in meta[:15]:
        progress += 1
        progress.show_progress()
        trace = m[helpers.TRACE]
        if len(trace) < 3: continue
        s, t = trace[0], trace[-1]
        sh = g.get_shortest_paths(s, t)[0]
        pretty_plot(g, trace, sh, rand_edges)

        
def rgb_to_hex(rgba):
    r, g, b, a = rgba
    return '#%02x%02x%02x%02x' % (r, g, b, a)


def coordxy(r, a):
    return (r*np.cos(a), r*np.sin(a))


def spiral_closeness(g):
    c_db = [(x.index, x['closeness']) for x in g.vs]
    c_db = sorted(c_db, key=itemgetter(1), reverse=True)
    coords = []
    layer_capacity = 1
    layer_level = 0
    in_layer = 0
    for x in np.arange(0, g.vcount()):
        r = layer_level
        a = in_layer * (np.pi / 2 / layer_capacity) + np.pi / 4

        coords.append(coordxy(r, a))

        in_layer += 1
        if in_layer >= layer_capacity + 1:
            layer_capacity += 1
            layer_level += 1
            in_layer = 0

    tmp = zip(*c_db)
    tmp.append(coords)
    c_db = zip(*tmp)
    c_db = sorted(c_db, key=itemgetter(0))

    layout = zip(*c_db)[2]

    return layout


def paint_edge(ecolors, edges, new_color):
    for idx in edges:
        old_color = ecolors[idx]
        new_value = np.add(old_color, new_color)
        new_value[new_value > 255] = 255
        new_value[new_value < 0] = 0
        ecolors[idx] = new_value

        
def pretty_plot(g, trace, alter, spec_edges,
                basic_color=None, trace_color=None,
                alter_color=None, spec_color=None):

    if basic_color is None: basic_color = (0, 0, 0, 0)
    if trace_color is None: trace_color = (255, 0, 0, 10)
    if alter_color is None: alter_color = (0, 200, 0, 10)
    if spec_color is None: spec_color = (-255, -255, -255, 0)

    layout = spiral_closeness(g)

    ecolor = [basic_color[:] for x in xrange(0, g.ecount())]

    trace_hops = zip(trace, trace[1:])
    trace_e = [g.get_eid(x[0],x[1]) for x in trace_hops]
    paint_edge(ecolor, trace_e, trace_color)

    alter_hops = zip(alter, alter[1:])
    alter_e = [g.get_eid(x[0], x[1]) for x in alter_hops]
    paint_edge(ecolor, alter_e, alter_color)

    spec_e = [g.get_eid(x[0], x[1]) for x in spec_edges]
    paint_edge(ecolor, spec_e, spec_color)

    ecolor = [rgb_to_hex(x) for x in ecolor]

    vcolor = ['black' for x in xrange(g.vcount())]
    vsize = [0.05 for x in xrange(g.vcount())]

    s, t = g.vs.find(trace[0]).index, g.vs.find(trace[-1]).index
    vsize[s] = 5
    vcolor[s] = 'red'
    vsize[t] = 5
    vcolor[t] = 'blue'

    igraph.plot(g, layout=layout, vertex_size=vsize, edge_color=ecolor,
                vertex_color=vcolor)


def pretty_plot_all(g, traces, alter, spec_edges,
                basic_color=None, trace_color=None,
                alter_color=None, spec_color=None):

    if basic_color is None: basic_color = (0, 0, 0, 4)
    if trace_color is None: trace_color = (255, 0, 0, 10)
    if alter_color is None: alter_color = (0, 200, 0, 10)
    if spec_color is None: spec_color = (-255, -255, -255, 0)

    layout = spiral_closeness(g)

    ecolor = [basic_color[:] for x in xrange(0, g.ecount())]

    ecolor = [rgb_to_hex(x) for x in ecolor]

    vcolor = ['black' for x in xrange(g.vcount())]
    vsize = [1 for x in xrange(g.vcount())]

    for x in traces:
        s, t = x[0], x[-1]
        sidx = g.vs.find(s).index
        tidx = g.vs.find(t).index
        vcolor[sidx] = 'green'
        vcolor[tidx] = 'blue'
        vsize[sidx] = 4
        vsize[tidx] = 4

    v = random.choice([x for x in g.vs])
    n = g.neighbors(v)

    es = [g.get_eid(v.index, x, directed=False) for x in n]
    for e in es:
        ecolor[e] = 'red'

    igraph.plot(g, layout=layout, vertex_size=vsize, edge_color=ecolor,
                vertex_color=vcolor)

if __name__ == '__main__':
    main()
