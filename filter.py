#!/usr/bin/evn python
# -*- coding: utf-8 -*-

# A kulso forrasokbol szamazo meresekben gyakran vannak a mi mereseink
# szempontjabol irrelevans, ertelmezhetetlen vagy szuksegtelen adatok.
# Ezzel a programmal parameterezhetoen ki lehet szurni bizonyos
# kategoriakba eso mereseket.

from tools.valley_free_tools import VFT as vft
import tools.progressbar1 as progressbar1
from tools import helpers, misc
import argparse_general
import argparse
import logging

misc.logger_setup()
logger = logging.getLogger('compnet.converter')
logging.getLogger('compnet').setLevel(logging.INFO)


def main():
    parser = argparse.ArgumentParser(
        description='Filter out non vf and non lp traceroutes from given traceroute list',
        parents=[argparse_general.commonParser, ],
        **argparse_general.commonParams)

    parser.add_argument('network')
    parser.add_argument('traceroutes')
    parser.add_argument(
        '--filter',
        default='sh+loop+ex+lp',
        help='Possible values: sh (short), loop (AS number repetition), ex (non existent), vf (non valley free), lp (non local preferenced), or any combination with + sign. Note that lp automatically means vf+lp'
    )
    parser.add_argument(
        '--lp-type',
        default='first',
        choices=['first', 'all'],
        dest='first_edge')
    parser.add_argument('output')

    arguments = parser.parse_args()

    arguments.verbose = min(len(helpers.LEVELS), arguments.verbose)
    logging.getLogger('compnet').setLevel(helpers.LEVELS[arguments.verbose])

    arguments.first_edge = arguments.first_edge == 'first'
    if arguments.first_edge:
        logger.debug('LP only first edge')
    else:
        logger.debug('LP all edge')

    g = helpers.load_network(arguments.network)
    traceroutes = helpers.load_from_json(arguments.traceroutes)

    arguments.lb = arguments.lb if 0 <= arguments.lb <= len(traceroutes) else 0
    arguments.ub = arguments.ub if 0 <= arguments.ub <= len(
        traceroutes) else len(traceroutes)

    arguments.filter = arguments.filter.replace('lp', 'vf+lp')

    filters = arguments.filter.split('+')

    result = filter(g, traceroutes[arguments.lb:arguments.ub], filters,
                    arguments.first_edge)

    helpers.save_to_json(arguments.output, result)


def filter(g,
           traceroutes,
           filters=['sh', 'loop', 'ex', 'vf', 'lp'],
           first_edge=True):

    logger.info('Traceroutes: %d', len(traceroutes))
    # remove empty traces
    traceroutes = [x for x in traceroutes if len(x) > 0]
    logger.info('Non empty traceroutes: %d', (len(traceroutes)))
    traceroutes = [x for x in traceroutes if len(x) > 1]
    logger.info('Larger than one hop traceroutes: %d', (len(traceroutes)))
    # remove traces with unknown nodes
    traceroutes, _ = vft.trace_clean(g, traceroutes)
    logger.info('Ignored: %d', _)
    traceroutes = vft.trace_in_vertex_id(g, traceroutes)
    logger.info('Trace count: %d', len(traceroutes))
    progress = progressbar1.AnimatedProgressBar(end=len(traceroutes), width=15)

    good_traceroutes = traceroutes[:]
    if 'sh' in filters:
        logger.debug('Remove short traces')
        good_traceroutes = [x for x in good_traceroutes if len(x) >= 3]
        logger.debug('Remained: %d', len(good_traceroutes))

    if 'loop' in filters:
        logger.debug('Remove traces with loops')
        good_traceroutes = [
            x for x in good_traceroutes if len(set(x)) == len(x)
        ]
        logger.debug('Remained: %d' % len(good_traceroutes))

    if 'ex' in filters:
        logger.debug('Remove non existent traces')
        good_traceroutes = [
            x for x in good_traceroutes if vft.trace_exists(g, x)
        ]
        logger.debug('Remained: %d', len(good_traceroutes))

    if 'vf' in filters:
        logger.debug('Remove non vf traces')
        good_traceroutes = [
            x for x in good_traceroutes if vft.is_valley_free(g, x)
        ]
        logger.debug('Remained: %d' % len(good_traceroutes))

    if 'lp' in filters:
        logger.debug('Remove non lp traces')
        good_traceroutes = [
            x for x in good_traceroutes
            if vft.is_local_preferenced(
                g, x, first_edge=first_edge)
        ]
        logger.debug('Remained: %d' % len(good_traceroutes))

    # convert back node ids to node names

    good_traceroutes = [[g.vs[id]["name"] for id in trace]
                        for trace in good_traceroutes]
    logger.debug(len(good_traceroutes))

    return good_traceroutes


if __name__ == '__main__':
    main()
