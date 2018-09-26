#!/usr/bin/evn python
# -*- coding: utf-8 -*-

# Closeness ertekek szamolasa az egyes node-okhoz
# Ha a megadott graf mar rendelkezik closeness mezovel,
# akkor nem csinal semmit

from tools import helpers, misc
import argparse_general
import argparse
import logging
import igraph as i

misc.logger_setup()
logger = logging.getLogger('compnet.add_closeness')
logging.getLogger('compnet').setLevel(logging.INFO)


def main():
    parser = argparse.ArgumentParser(
        parents=[argparse_general.commonParser, ],
        description='Calculate closeness values and save the graph with them',
        **argparse_general.commonParams)

    parser.add_argument(
        'network',
        help='Input network. Use any format which compatible with igraph')
    parser.add_argument(
        'out',
        help='File path to save the graph with closeness values. GML extension required.'
    )

    arguments = parser.parse_args()
    arguments.verbose = min(len(helpers.LEVELS), arguments.verbose)
    logging.getLogger('compnet').setLevel(helpers.LEVELS[arguments.verbose])

    g = helpers.load_network(arguments.network)
    out = arguments.out
    purify(g, out)


def purify(g, out):

    try:
        closeness = g.vs['closeness']
        if closeness is None:
            raise KeyError
        logger.info('GML file already have closeness attr, doing nothing.')
        return closeness
    except KeyError:
        logger.info('Computing closeness, this could take a while.')
        closeness = g.closeness(mode=i.ALL)
        g.vs['closeness'] = closeness
        g.write_gml(out)
        return closeness


if __name__ == '__main__':
    main()
