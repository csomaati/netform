from tools.valley_free_tools import VFT as vft
import tools.progressbar1 as progressbar1
from tools import helpers, misc
import collections
import argparse
import logging
import igraph
import random

misc.logger_setup()
logger = logging.getLogger('compnet.random_sh_routing')
logging.getLogger('compnet').setLevel(logging.INFO)


def main():
    parser = argparse.ArgumentParser(description=('SANDBOX mode. ',
                                                  'Write something ',
                                                  'useful here'),
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--progressbar', action='store_true')
    parser.add_argument('--verbose', '-v', action='count', default=0)
    parser.add_argument('--edge-drop', dest='edge_drop', type=float,
                        default=0.0)
    parser.add_argument('--closeness-limit', dest='closeness_limit', type=float,
                        default=0.0)
    parser.add_argument('network')
    parser.add_argument('traceroutes')

    arguments = parser.parse_args()

    show_progress = arguments.progressbar

    arguments.verbose = min(len(helpers.LEVELS), arguments.verbose)
    logging.getLogger('compnet').setLevel(helpers.LEVELS[arguments.verbose])

    g = helpers.load_network(arguments.network)
    traceroutes = helpers.load_from_json(arguments.traceroutes)

    logger.info('ecount: %d' % g.ecount())
    logger.info('vcount: %d' % g.vcount())
    logger.info('trace count: %d' % len(traceroutes))

    g_dummy = g.copy()
    progress = progressbar1.DummyProgressBar(end=10, width=15)
    if show_progress:
        progress = progressbar1.AnimatedProgressBar(end=len(traceroutes),
                                                    width=15)

    closeness_list = []
    for x in g_dummy.vs:
        progress += 1
        progress.show_progress()
        closeness_list.append((x.index, g_dummy.closeness(x)))

    end = int(arguments.closeness_limit * g_dummy.vcount())
    logger.debug('Top node count: %d' % end)
    top_nodes = sorted(closeness_list, key=lambda x: x[1], reverse=True)[:end]
    top_nodes_index = [x[0] for x in top_nodes]
    top_nodes_name = [g_dummy.vs[x[0]]['name'] for x in top_nodes]
    top_edges = [e for e in g_dummy.es if e.source in top_nodes_index and e.target in top_nodes_index]
    logger.debug('Top edge count: %d' % len(top_edges))
    random.shuffle(top_edges)
    edge_drop = top_edges[:int(len(top_edges) * arguments.edge_drop)]
    logger.debug('Dropped edge count: %d' % len(edge_drop))
    # edges = [x.index for x in g_dummy.es]
    # random.shuffle(edges)
    # edge_drop = edges[:int(g.ecount() * arguments.edge_drop)]
    g_dummy.delete_edges(edge_drop)

    traceroutes = traceroutes[:10000]

    all_edges = []
    for trace in traceroutes:
        edges = zip(trace, trace[1:])
        edges = [tuple(sorted(e)) for e in edges]
        all_edges.extend(edges)

    all_edges = list(set(all_edges))
    top_edges = [e for e in all_edges if e[0] in top_nodes_name and e[1] in top_nodes_name]
    logger.info('TOP edge count in real traceroutes: %d' % len(top_edges))

    found_top_edges = []
    increments = []
    for trace in traceroutes:
        edges = zip(trace, trace[1:])
        edges = [tuple(sorted(e)) for e in edges]
        top_edges = [x for x in edges if x[0] in top_nodes_name and x[1] in top_nodes_name]
        found_top_edges.extend(top_edges)
        found_top_edges = list(set(found_top_edges))
        increments.append(len(found_top_edges))

    logger.info('Found top edge count: %d' % len(found_top_edges))

    dummy_sh_traceroutes_meta = []
    original_sh_traceroutes_meta = []
    stretches = []
    progress = progressbar1.DummyProgressBar(end=10, width=15)
    if show_progress:
        progress = progressbar1.AnimatedProgressBar(end=len(traceroutes),
                                                    width=15)
    for trace in traceroutes:
        progress += 1
        progress.show_progress()
        s, t = trace[0], trace[-1]
        # logger.debug('Get shortest paths from {s} to {t}'.format(s=s, t=t))
        sh_dummy = random.choice(g_dummy.get_shortest_paths(s, t))
        sh_original = random.choice(g.get_shortest_paths(s, t))
        stretch = len(sh_dummy) - len(sh_original)
        dummy_sh_traceroutes_meta.append((sh_dummy, stretch))
        original_sh_traceroutes_meta.append((sh_original, 0))
        stretches.append(stretch)
        # logger.debug('Stretch: %d' % stretch)
        # logger.debug('SH DUMMY: %s' % [g_dummy.vs[x]['name'] for x in sh_dummy])
        # logger.debug('SH ORIG: %s' % [g.vs[x]['name'] for x in sh_original])

    dummy_sh_meta = [(x[0], x[1], vft.is_valley_free(g_dummy, x[0], vft.CLOSENESS)) for x in dummy_sh_traceroutes_meta]
    dummy_sh_len_hist = collections.Counter([len(x[0]) for x in dummy_sh_traceroutes_meta])
    original_sh_len_hist = collections.Counter([len(x[0]) for x in original_sh_traceroutes_meta])
    original_len_hist = collections.Counter([len(x) for x in traceroutes])
    stretches = [x for x in stretches if x >= 0]
    stretch_hist = collections.Counter(stretches)

    import matplotlib.pyplot as plt
    print
    print [(x, 100*y/float(len(traceroutes)), y) for x, y in stretch_hist.iteritems()]
    plt.plot([x for x in stretch_hist.iterkeys()], [x for x in stretch_hist.itervalues()], 'g^')
    plt.ylabel('some numbers')
    # plt.show()

    logger.info('Dummy VF stat')
    max_stretch = max(dummy_sh_meta, key=lambda x: x[1])[1]
    for stretch in range(0, max_stretch + 1):
        stretched_traces = [x for x in dummy_sh_meta if x[1] == stretch]
        count = len(stretched_traces)
        vf_count = len([x for x in stretched_traces if x[2]])
        vf_perc = vf_count / float(count)
        nonvf_count = count - vf_count
        nonvf_perc = nonvf_count / float(count)
        logger.info('{stretch} -- {vf_perc}[{vf_count}]\t{nonvf_perc}[{nonvf_count}]'.format(stretch=stretch,
                                                                                             vf_perc=vf_perc,
                                                                                             vf_count=vf_count,
                                                                                             nonvf_perc=nonvf_perc,
                                                                                             nonvf_count=nonvf_count))
    import matplotlib.pyplot as plt
    plt.plot(increments, 'g^')
    plt.ylabel('some numbers')
    plt.show()

if __name__ == '__main__':
    main()
