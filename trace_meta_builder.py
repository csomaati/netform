from tools import helpers, misc
import logging
import argparse
import statistics
import tools.progressbar1 as progressbar1
import igraph as i

from tools.valley_free_tools import VFT as vft

misc.logger_setup()
logger = logging.getLogger('compnet.trace_meta_builder')
logging.getLogger('compnet').setLevel(logging.INFO)

FLAG_DEGREE = 'flag_degree'
FLAG_CLOSENESS = 'flag_closeness'
FLAG_PRELABELED = 'flag_prelabeled'
FLAG_LP_HARD = 'lp_hard'
FLAG_LP_SOFT = 'lp_soft'


def main():
    parser = argparse.ArgumentParser(description='Calculate meta information for real traces', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('network')
    parser.add_argument('traceroutes')
    parser.add_argument('output', type=argparse.FileType('w'))

    # parser.add_argument('--vfmode', type=str, default='labeled', dest='vfmode',
    #                     choices=['labeled', 'closeness'])

    # for paralelization
    parser.add_argument('--lower-bound', '-lb', type=int, default=0, dest='lb')
    parser.add_argument('--upper-bound', '-ub', type=int, default=-1, dest='ub')

    parser.add_argument('--progressbar', action='store_true')
    parser.add_argument('--verbose', '-v', action='count', default=0)

    parser.add_argument('--with-prelabeled', action='store_true')
    parser.add_argument('--with-closeness', action='store_true')
    parser.add_argument('--with-degree', action='store_true')

    parser.add_argument('--with-lp-hard', action='store_true')
    parser.add_argument('--with-lp-soft', action='store_true')
    # parser.add_argument('--with-lp', action='store_true')
    # parser.add_argument('--with-vf', action='store_true')

    arguments = parser.parse_args()

    arguments.verbose = min(len(helpers.LEVELS), arguments.verbose)
    logging.getLogger('compnet').setLevel(helpers.LEVELS[arguments.verbose])

    g = helpers.load_network(arguments.network)

    traceroutes = helpers.load_from_json(arguments.traceroutes)

    arguments.lb = arguments.lb if 0 <= arguments.lb <= len(traceroutes) else 0
    arguments.ub = arguments.ub if 0 <= arguments.ub <= len(traceroutes) else len(traceroutes)

    flags = {
        FLAG_PRELABELED: arguments.with_prelabeled,
        FLAG_CLOSENESS: arguments.with_closeness,
        FLAG_DEGREE: arguments.with_degree,
        FLAG_LP_HARD: arguments.with_lp_hard,
        FLAG_LP_SOFT: arguments.with_lp_soft
    }

    # if arguments.vfmode == 'labeled': mode = vft.ORDER_PRELABELED
    # elif arguments.vfmode == 'closeness': mode = vft.ORDER_CLOSENESS
    # else: raise RuntimeError('Unhandled vfmode')

    traceroutes = traceroutes[arguments.lb:arguments.ub]
    result = purify(g, traceroutes, flags, arguments.progressbar)
    logger.info('Save to %s' % arguments.output)
    helpers.save_to_json(arguments.output, result)


def purify(g, traceroutes, flags, show_progress=False):
    results = list()

    # remove traces with unknown nodes
    traceroutes = vft.trace_in_vertex_id(g, traceroutes)

    # generate valley-free graph
    if flags[FLAG_PRELABELED]:
        logger.info('Generate VF_G_PRE')
        vf_g_pre = vft.convert_to_vf(g, vfmode=vft.PRELABELED)
    else:
        logger.info('Skip prelabeled graph')
    if flags[FLAG_DEGREE]:
        logger.info('Generate VF_G_DEGREE')
        vf_g_degree = vft.convert_to_vf(g, vfmode=vft.DEGREE)
    else:
        logger.info('Skip degree graph')
    if flags[FLAG_CLOSENESS]:
        logger.info('Generate VF_G_CLOSENESS')
        vf_g_closeness = vft.convert_to_vf(g, vfmode=vft.CLOSENESS)
    else:
        logger.info('Skip closeness graph')

    progress = progressbar1.DummyProgressBar(end=10, width=15)
    if show_progress:
        progress = progressbar1.AnimatedProgressBar(end=len(traceroutes),
                                                    width=15)
    for trace in traceroutes:
        progress += 1
        progress.show_progress()

        logger.debug('Current trace: %s' % ([g.vs[x]['name'] for x in trace]))

        if len(trace) == 1: continue

        s, t = trace[0], trace[-1]

        is_vf_prelabeled = -1
        is_lp_prelabeled_hard = -1
        is_lp_prelabeled_soft = -1

        is_vf_degree = -1
        is_lp_degree_hard = -1
        is_lp_degree_soft = -1

        is_vf_closeness = -1
        is_lp_closeness_hard = -1
        is_lp_closeness_soft = -1

        trace_len = len(trace)
        sh_len = g.shortest_paths(s, t, mode=i.OUT)[0][0]
        sh_len += 1  # convert hop count to node Counter

        if flags[FLAG_PRELABELED]:
            is_vf_prelabeled = vft.is_valley_free(g, trace, vft.PRELABELED)
            is_vf_prelabeled = int(is_vf_prelabeled)
            if is_vf_prelabeled:
                if flags[FLAG_LP_SOFT]:
                    lp_soft = vft.is_local_preferenced(g, trace,
                                                       vf_g=vf_g_pre,
                                                       first_edge=True,
                                                       vfmode=vft.PRELABELED)
                    is_lp_prelabeled_soft = 1 if lp_soft else 0
                else:
                    is_lp_prelabeled_soft = -1

                if flags[FLAG_LP_HARD]:
                    lp_hard = vft.is_local_preferenced(g, trace,
                                                       vf_g=vf_g_pre,
                                                       first_edge=False,
                                                       vfmode=vft.PRELABELED)
                    is_lp_prelabeled_hard = 1 if lp_hard else 0
                else:
                    is_lp_prelabeled_hard = -1

        if flags[FLAG_DEGREE]:
            is_vf_degree = vft.is_valley_free(g, trace, vft.DEGREE)
            is_vf_degree = int(is_vf_degree)
            if is_vf_degree:
                if flags[FLAG_LP_SOFT]:
                    lp_soft = vft.is_local_preferenced(g, trace,
                                                       vf_g=vf_g_degree,
                                                       first_edge=True,
                                                       vfmode=vft.DEGREE)
                    is_lp_degree_soft = 1 if lp_soft else 0
                else:
                    is_lp_degree_soft = -1

                if flags[FLAG_LP_HARD]:
                    lp_hard = vft.is_local_preferenced(g, trace,
                                                       vf_g=vf_g_degree,
                                                       first_edge=False,
                                                       vfmode=vft.DEGREE)
                    is_lp_degree_hard = 1 if lp_hard else 0
                else:
                    is_lp_degree_hard = -1

        if flags[FLAG_CLOSENESS]:
            is_vf_closeness = vft.is_valley_free(g, trace, vft.CLOSENESS)
            is_vf_closeness = int(is_vf_closeness)
            if is_vf_closeness:
                if flags[FLAG_LP_SOFT]:
                    lp_soft = vft.is_local_preferenced(g, trace,
                                                       vf_g=vf_g_closeness,
                                                       first_edge=True,
                                                       vfmode=vft.CLOSENESS)
                    is_lp_closeness_soft = 1 if lp_soft else 0
                else:
                    is_lp_closeness_soft = -1
                if flags[FLAG_LP_HARD]:
                    lp_hard = vft.is_local_preferenced(g, trace,
                                                       vf_g=vf_g_closeness,
                                                       first_edge=False,
                                                       vfmode=vft.CLOSENESS)
                    is_lp_closeness_hard = 1 if lp_hard else 0
                else:
                    is_lp_closeness_hard = -1

        if False:
            sh_vf_len = vft.get_shortest_vf_route(g, s, t, mode='vf',
                                                  vf_g=vf_g_pre, _all=True,
                                                  vfmode=vft.PRELABELED)
            # ugy tunik, mintha nem mindig lenne pontos? fentartassal kezelendo
            # ez az ertek azert is kerult bele, hogy ellenorizzuk
            in_vf_prediction = 1 if sh_vf_len and trace in sh_vf_len else 0
        else:
            sh_vf_len = -1
            in_vf_prediction = -1

        sh_vf_len = len(sh_vf_len[0]) if isinstance(sh_vf_len, list) else -1
        percentage_stretch = trace_len / float(sh_len)

        named_trace = [g.vs[_id]["name"] for _id in trace]

        result = {
            helpers.TRACE: named_trace,
            helpers.TRACE_LEN: trace_len,
            helpers.SH_LEN: sh_len,
            helpers.SH_VF_LEN: sh_vf_len,
            helpers.IS_VF_PRELABELED: is_vf_prelabeled,
            helpers.IS_VF_DEGREE: is_vf_degree,
            helpers.IS_VF_CLOSENESS: is_vf_closeness,
            helpers.HOP_STRETCH: trace_len - sh_len,
            helpers.PERC_STRETCH: percentage_stretch,
            helpers.IN_VF_PRED: in_vf_prediction,
            helpers.IS_LP_SOFT_PRELABELED: is_lp_prelabeled_soft,
            helpers.IS_LP_HARD_PRELABELED: is_lp_prelabeled_hard,
            helpers.IS_LP_SOFT_DEGREE: is_lp_degree_soft,
            helpers.IS_LP_HARD_DEGREE: is_lp_degree_hard,
            helpers.IS_LP_SOFT_CLOSENESS: is_lp_closeness_soft,
            helpers.IS_LP_HARD_CLOSENESS: is_lp_closeness_hard,
        }

        results.append(result)

    # print >> sys.stderr, ('TRACE\tTRACE_LEN\tSH_LEN\tSH_VF_LEN\tIS_VF',
    #                       '\tSTRETCH\tIN_VF_PREDICTION\tIS_LP_F\tIS_LP_ALL')
    # for result in results:
    #     result = [str(r) for r in result]
    #     print >> sys.stderr, '\t'.join(result)

    # statistic = statistics.purify(g, results,
    #                               'nc+ec+tc+rt+vf+vf_closeness+pred+lp_soft_prelabeled+lp_hard_prelabeled+lp_soft_degree+lp_hard_degree+lp_soft_closeness+lp_hard_closeness'.split('+'))
    # statistics.stat_printer(statistic)

    return results

if __name__ == '__main__':
    main()
