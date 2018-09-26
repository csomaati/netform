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
    parser = argparse.ArgumentParser(description='Save closeness values for all node', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('network')
    parser.add_argument('out')

    parser.add_argument('--progressbar', action='store_true')
    parser.add_argument('--verbose', '-v', action='count', default=0)

    arguments = parser.parse_args()

    arguments.verbose = min(len(helpers.LEVELS), arguments.verbose)
    logging.getLogger('compnet').setLevel(helpers.LEVELS[arguments.verbose])

    g = helpers.load_network(arguments.network)
    logger.info('Graph loaded from: %s' % arguments.network)
    logger.info('Graph vertex count: %d' % g.vcount())

    if 'closeness' not in g.vs:
        logger.info('Calculate closeness values')
        progress = progressbar1.DummyProgressBar(end=10, width=15)
        if arguments.progressbar:
            progress = progressbar1.AnimatedProgressBar(end=g.vcount(),
                                                        width=15)
        for n in g.vs:
            progress += 1
            progress.show_progress()
            closeness = g.closeness(n, mode=igraph.OUT)
            n['closeness'] = closeness
        g.save(arguments.out)

if __name__ == '__main__':
    main()
