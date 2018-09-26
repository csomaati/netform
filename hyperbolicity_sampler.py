import random
from tools import helpers, misc
import argparse
import tools.progressbar1 as progressbar1
from tools.valley_free_tools import VFT as vft
import numpy as np
import logging
import igraph

misc.logger_setup()
logger = logging.getLogger('compnet.random_walking')
logging.getLogger('compnet').setLevel(logging.INFO)


def main():
    parser = argparse.ArgumentParser(description='SANDBOX mode. Write something useful here', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('network')
    parser.add_argument('--sample-size',
                        type=int, default=1000, dest='sample_size')

    parser.add_argument('--node-drop',
                        type=float, default=.1, dest='node_drop')

    parser.add_argument('--progressbar', action='store_true')
    parser.add_argument('--verbose', '-v', action='count', default=0)

    arguments = parser.parse_args()

    arguments.verbose = min(len(helpers.LEVELS), arguments.verbose)
    logging.getLogger('compnet').setLevel(helpers.LEVELS[arguments.verbose])

    g = helpers.load_network(arguments.network)
    g = g.components().giant()
    logger.info('Graph loaded from: %s' % arguments.network)
    logger.info('Graph vertex count: %d' % g.vcount())

    end = int(g.vcount() * arguments.node_drop)
    logger.info('Remaining node count: %d' % end)

    try:
        nodes = [(x.index, x['closeness']) for x in g.vs]
    except KeyError:
        logger.info('Calculate closeness values')
        progress = progressbar1.DummyProgressBar(end=10, width=15)
        if arguments.progressbar:
            progress = progressbar1.AnimatedProgressBar(end=g.vcount(),
                                                        width=15)
        for n in g.vs:
            progress += 1
            progress.show_progress()
            closeness = g.closeness(n)
            n['closeness'] = closeness
        g.save('with_closeness.gml')
        nodes = [(x.index, x['closeness']) for x in g.vs]

    nodes = sorted(nodes, reverse=True, key=lambda x: x[1])
    top_nodes = [x[0] for x in nodes[:end]]

    delete_nodes  = [x.index for x in g.vs if x.index not in top_nodes]
    g.delete_vertices(delete_nodes)

    logger.info('Left nodes: %d' % g.vcount())

    purify(g, arguments.sample_size, arguments.progressbar)


def hyperbolicity(g, quadruplet):
    a, b, c, d = (0, 1, 2, 3)
    distances = g.shortest_paths(quadruplet, quadruplet)
    S1 = distances[a][b] + distances[c][d]
    S2 = distances[a][c] + distances[b][d]
    S3 = distances[a][d] + distances[b][c]

    if S1 == float('inf'): S1 = float('-inf')
    if S2 == float('inf'): S2 = float('-inf')
    if S3 == float('inf'): S3 = float('-inf')

    logger.debug('Ss: %s %s %s' % (S1, S2, S3))

    M1, M2 = sorted((S1, S2, S3), reverse=True)[:2]
    logger.debug('Max: %s %s' % (M1, M2))
    return abs(M1 - M2)


def purify(g, sample_size, show_progress):

    nodes = range(0, g.vcount())
    samples = [random.sample(nodes, 4) for idx in range(0, sample_size)]

    progress = progressbar1.DummyProgressBar(end=10, width=15)
    if show_progress:
        progress = progressbar1.AnimatedProgressBar(end=len(samples),
                                                    width=15)

    logger.info('Avg distance calculation')
    avg_len = g.average_path_length()
    logger.info('Avg len: %d' % avg_len)

    hbcs = []
    for quadruplet in samples:
        progress += 1
        progress.show_progress()
        hbc = hyperbolicity(g, quadruplet)
        hbcs.append(hbc)

    avg_hbc = sum(hbcs) / float(len(hbcs))

    logger.info('Avg hbc num: %f' % avg_hbc)

    logger.info('Avg hbc: %f' % (avg_hbc / float(avg_len)))


if __name__ == '__main__':
    main()
