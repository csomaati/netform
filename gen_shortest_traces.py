#!/usr/bin/evn python
# -*- coding: utf-8 -*-

# A parameterben kapott halozat veletlenszeru pontparjai kozotti
# legrovidebb utakat szamolja ki es menti el a parameterben
# kapott kimeneti fajlba.

import tools.progressbar1 as progressbar1
from tools import helpers, misc
import argparse_general
import argparse
import random
import logging

misc.logger_setup()
logger = logging.getLogger('compnet.gen_shortest_trace')
logging.getLogger('compnet').setLevel(logging.INFO)


def main():
    parser = argparse.ArgumentParser(
        description='Generate shortest path between random endpoins',
        parents=[argparse_general.commonParser, ],
        **argparse_general.commonParams)

    parser.add_argument('network')
    parser.add_argument('out')
    parser.add_argument(
        '--route-count', type=int, default=1000, dest='route_count')

    arguments = parser.parse_args()

    g = helpers.load_network(arguments.network)
    # g = g.components().giant()
    out = arguments.out

    arguments.verbose = min(len(helpers.LEVELS), arguments.verbose)
    logging.getLogger('compnet').setLevel(helpers.LEVELS[arguments.verbose])

    purify(g, out, arguments.route_count, arguments.progressbar)


def purify(g, out, count=1000, show_progress=False):

    logger.info('Started')
    nodes = range(0, g.vcount())
    endpoints = [random.sample(nodes, 2) for idx in range(0, count)]

    progress = progressbar1.DummyProgressBar(end=10, width=15)
    if show_progress:
        progress = progressbar1.AnimatedProgressBar(
            end=len(endpoints), width=15)
    traces = []
    for endpoint in endpoints:
        progress += 1
        progress.show_progress()
        src, dst = endpoint
        trace = g.get_shortest_paths(src, dst)[0]
        if len(trace) > 0:
            traces.append([g.vs[x]['name'] for x in trace])

    logger.info('Len last trace: %d' % len(trace))
    helpers.save_to_json(out, traces)


if __name__ == '__main__':
    main()
