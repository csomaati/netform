import random
from tools import helpers
import argparse
import tools.progressbar1 as progressbar1
import igraph as i
from tools.valley_free_tools import VFT as vft
import sys


def main():
    parser = argparse.ArgumentParser(description='Calculate meta information for real traces', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('network')
    parser.add_argument('traceroutes')
    parser.add_argument('output')
    parser.add_argument('--maxi', type=int, default=500)

    # for paralelization
    parser.add_argument('--lower-bound', '-lb', type=int, default=0, dest='lb')
    parser.add_argument('--upper-bound', '-ub', type=int, default=-1, dest='ub')

    arguments = parser.parse_args()

    g = helpers.load_as_inferred_links(arguments.network)
    traceroutes = helpers.load_from_json(arguments.traceroutes)

    # traceroutes = random.sample(traceroutes, arguments.maxi)

    arguments.lb = arguments.lb if 0 <= arguments.lb <= len(traceroutes) else 0
    arguments.ub = arguments.ub if 0 <= arguments.ub <= len(traceroutes) else len(traceroutes)

    result = filter(g, traceroutes[arguments.lb:arguments.ub])

    helpers.save_to_json(arguments.output, result)


def filter(g, traceroutes):
    results = list()

    # remove traces with unknown nodes
    traceroutes = vft.trace_in_vertex_id(g, traceroutes)

    progress = progressbar1.AnimatedProgressBar(end=len(traceroutes), width=15)
    for trace in traceroutes:
        progress += 1
        progress.show_progress()

        if not vft.trace_exists(g, trace):
            print 'BUG?'
            continue

        for x in range(0, g.vcount()):
            g.vs[x]['traces'] = dict()

        trace = tuple(trace)
        s, t = trace[0], trace[-1]

        sh_len = g.shortest_paths(s, t, mode=i.ALL)[0][0]
        sh_len += 1  # igraph's hop count to node count

        all_routes = helpers.dfs_mark(g, s, t, sh_len + 1)
        # all_routes2 = helpers.dfs_simple(g, s, t, sh_len + 1, ())

        # if set(all_routes) - set(all_routes2) != set(all_routes2) - set(all_routes):
        #     print 'AJAJAJ'
        #     print all_routes
        #     print '----------'
        #     print all_routes2

        sh_routes = [x for x in all_routes if len(x) == sh_len]

        all_vf_routes = [x for x in all_routes if vft.is_valley_free(g, x)]
        prediction_set = set(sh_routes) | set(all_vf_routes)

        result = [trace, len(trace), sh_len,
                  len(sh_routes), trace in sh_routes,
                  len(all_vf_routes), trace in all_vf_routes,
                  len(all_routes), trace in all_routes,
                  len(prediction_set), trace in prediction_set,
                  vft.is_valley_free(g, trace),
                  # sh_routes, all_vf_routes, all_routes,
                  vft.trace_to_string(g, trace)]

        results.append(result)

    print >> sys.stderr, ('TRACE\tTRACE_LEN\tSH_LEN',
                          '\t#SH_ROUTE\tOK',
                          '\t#ALL_VF\tOK',
                          '\t#ALL_ROUTE\tOK',
                          '\t#PREDICTION_SET\tOK',
                          '\tIS_VF',
                          # '\tSH_ROUTES\tALL_VF_ROUTES\tALL_ROUTE',
                          '\tTRACE_STR')
    for result in results:
        result = [str(r) for r in result]
        print >> sys.stderr, '\t'.join(result)

    return results

if __name__ == '__main__':
    main()
