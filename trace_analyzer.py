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
    parser.add_argument('meta')
    parser.add_argument('--top-node-ratio',
                        type=float, default=.1, dest='top_node_ratio')

    parser.add_argument('--progressbar', action='store_true')
    parser.add_argument('--verbose', '-v', action='count', default=0)

    arguments = parser.parse_args()

    arguments.verbose = min(len(helpers.LEVELS), arguments.verbose)
    logging.getLogger('compnet').setLevel(helpers.LEVELS[arguments.verbose])

    g = helpers.load_network(arguments.network)
    meta = helpers.load_from_json(arguments.meta)
    logger.info('Graph loaded from: %s' % arguments.network)
    logger.info('Graph vertex count: %d' % g.vcount())

    end = int(g.vcount() * arguments.top_node_ratio)
    logger.info('Top node count: %d' % end)

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
        g.save('%s_with_closeness.gml' % arguments.network)
        nodes = [(x.index, x['closeness']) for x in g.vs]

    nodes = sorted(nodes, reverse=True, key=lambda x: x[1])
    top_nodes = set([x[0] for x in nodes[:end]])

    purify(g, meta, top_nodes, arguments.progressbar)


def purify(g, meta, top_nodes, show_progress):

    progress = progressbar1.DummyProgressBar(end=10, width=15)
    if show_progress:
        progress = progressbar1.AnimatedProgressBar(end=len(meta),
                                                    width=15)

    logger.info('Purify')

    triplet_count_closeness = 0
    top_nodes_triplet_closeness = 0
    triplet_count_prelabeled = 0
    top_nodes_triplet_prelabeled = 0
    triplet_count_degree = 0
    top_nodes_triplet_degree = 0

    for row in meta:
        progress += 1
        progress.show_progress()

        trace = row[helpers.TRACE]
        trace = vft.trace_in_vertex_id(g, [trace, ])[0]

        if row[helpers.IS_VF_CLOSENESS] == 0:
            logger.debug('Closeness valley')
            vt = vft.get_valley_triplets(g, trace, vft.CLOSENESS)
            triplet_count_closeness += len(vt)
            for trip in vt:
                if any([x in top_nodes for x in trip]):
                    top_nodes_triplet_closeness += 1

        if row[helpers.IS_VF_PRELABELED] == 0:
            logger.debug('Prelabeled valley')
            vt = vft.get_valley_triplets(g, trace, vft.PRELABELED)
            triplet_count_prelabeled += len(vt)
            for trip in vt:
                if any([x in top_nodes for x in trip]):
                    top_nodes_triplet_prelabeled += 1
         
        if row[helpers.IS_VF_DEGREE] == 0:
            logger.debug('Degree valley')
            vt = vft.get_valley_triplets(g, trace, vft.DEGREE)
            triplet_count_degree += len(vt)
            for trip in vt:
                if any([x in top_nodes for x in trip]):
                    top_nodes_triplet_degree += 1

    print
    try:
        ratio_closeness = top_nodes_triplet_closeness / float(triplet_count_closeness)
    except ZeroDivisionError:
        ratio_closeness = 0.0
    try:
        ratio_prelabeled = top_nodes_triplet_prelabeled / float(triplet_count_prelabeled)
    except ZeroDivisionError:
        ratio_prelabeled = 0.0
    try:
        ratio_degree = top_nodes_triplet_degree / float(triplet_count_degree)
    except ZeroDivisionError:
        ratio_degree = 0.0
    logger.info('CLOSENESS: %6.3f[%d/%d]' % (ratio_closeness, top_nodes_triplet_closeness, triplet_count_closeness))
    logger.info('PRELABELED: %6.3f[%d/%d]' % (ratio_prelabeled, top_nodes_triplet_prelabeled, triplet_count_prelabeled))
    logger.info('DEGREE: %6.3f[%d/%d]' % (ratio_degree, top_nodes_triplet_degree, triplet_count_degree))


if __name__ == '__main__':
    main()
