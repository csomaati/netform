#!/usr/bin/evn python
# -*- coding: utf-8 -*-

# A Barabasi altal felvetett kerdesek megvalaszolasara
# szolgalo mereseket elvegzo kod

from tools import helpers, misc
import argparse_general
import argparse
import logging
import math
import random

misc.logger_setup()
logger = logging.getLogger('compnet.barabasi_method')
logging.getLogger('compnet').setLevel(logging.INFO)


def barabasi_cost(g, trace):
    cost = 0
    edges = zip(trace, trace[1:])  # ABCD -> AB, BC, CD
    for edge in edges:
        eid = g.get_eid(edge[0], edge[1])
        cost += g.es[eid]['weight']

    return cost


def main():
    parser = argparse.ArgumentParser(
        description="Implementation of Barabasi's ide",
        parents=[argparse_general.commonParser, ],
        **argparse_general.commonParams)

    parser.add_argument('network')
    parser.add_argument('meta')
    parser.add_argument('output', type=argparse.FileType('w'))

    arguments = parser.parse_args()

    arguments.verbose = min(len(helpers.LEVELS), arguments.verbose)
    logging.getLogger('compnet').setLevel(helpers.LEVELS[arguments.verbose])

    g = helpers.load_network(arguments.network)
    g = g.simplify()

    meta = helpers.load_from_json(arguments.meta)

    betweenness = g.edge_betweenness()
    maxb = max(betweenness)

    weights = [math.log(maxb / x) for x in betweenness]
    g.es['weight'] = weights

    for m in meta:
        trace = m[helpers.TRACE]
        trace_id = [g.vs.find(x).index for x in trace]

        s, t = trace_id[0], trace_id[-1]

        barabasi_path = random.choice(
            g.get_shortest_paths(
                s, t, weights='weight'))

        shortest_path = random.choice(g.get_shortest_paths(s, t))

        bcost = barabasi_cost(g, barabasi_path)
        shcost = barabasi_cost(g, shortest_path)
        trcost = barabasi_cost(g, trace_id)

        shdelta = shcost - bcost
        trdelta = trcost - bcost

        delta = shdelta - trdelta

        print delta

        # print "Barabasi: (%d)%s %s" % (len(barabasi_path), barabasi_cost(g, barabasi_path), barabasi_path)
        # print "Shortest: (%d)%s %s" % (len(shortest_path), barabasi_cost(g, shortest_path), shortest_path)
        # print "Trace   : (%d)%s %s" % (len(trace_id), barabasi_cost(g, trace_id), trace_id)
        # if barabasi_cost(g, shortest_path)  > barabasi_cost(g, trace_id):
        #    raw_input()


if __name__ == "__main__":
    main()
