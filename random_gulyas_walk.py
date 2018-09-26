from tools import helpers, misc
import random
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
    parser.add_argument('meta')
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

    parser.add_argument('--try-per-trace',
                        type=int, default=1, dest='try_per_trace')

    arguments = parser.parse_args()

    arguments.verbose = min(len(helpers.LEVELS), arguments.verbose)
    logging.getLogger('compnet').setLevel(helpers.LEVELS[arguments.verbose])

    g = helpers.load_network(arguments.network)

    meta = helpers.load_from_json(arguments.meta)

    arguments.lb = arguments.lb if 0 <= arguments.lb <= len(meta) else 0
    arguments.ub = arguments.ub if 0 <= arguments.ub <= len(meta) else len(meta)

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

    meta = meta[arguments.lb:arguments.ub]
    # update meta at place
    purify(g, meta, flags, arguments.try_per_trace, arguments.progressbar)
    logger.info('Save to %s' % arguments.output)
    helpers.save_to_json(arguments.output, meta)


def purify(g, meta, flags, try_per_trace, show_progress=False):

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

    # Randomize stretch dispersion
    stretches = [x[helpers.HOP_STRETCH] for x in meta]
    # a veletlen stretchek az eredeti stretchek veletlen, nem
    # visszateveses mintavetelezese. Mindez annyiszor, ahany
    # veletlen utat akarunk generalni minden valos trace vegpontja
    # kozott.
    stretch_list = [random.sample(stretches, len(stretches))
                    for x in xrange(0, try_per_trace)]
    # A kovetkezo ciklusban minden meta sorhoz rogton kiszamolunk
    # annyi random utat, amennyit parameterben megadtunk. Ehhez at kell
    # alakitani a stretch lista strukturat, hogy minden elem egy meta sorhoz
    # tartalmazza a random stretch ertekeket
    #
    # Pelda: elozo lepesnel kijott ez: [ [1,2,3,4], [2,4,1,3], [3,1,4,2] ]
    # vagyis elso lepesben a metaban tarolt tracek rendre 1,2,3,4 stretchet
    # kell felvegyenek, a masodikban 2,4,1,3 stb. A ciklusban viszont a meta
    # elso elemehez rogton ki akarjuk szamolni a veletlen stretchekhez tartozo
    # random utakat, vagyis [ [1,2,3], [2,4,1], [3,1,4], [4,3,2] ] formaban
    # van szukseg az ertekekre
    stretch_list = zip(*stretch_list)

    progress = progressbar1.DummyProgressBar(end=10, width=15)
    if show_progress:
        progress = progressbar1.AnimatedProgressBar(end=len(meta), width=15)

    for idx, record in enumerate(meta):
        progress += 1
        progress.show_progress()

        trace = vft.trace_in_vertex_id(g, [record[helpers.TRACE], ])
        if len(trace) != 1:
            print 'PROBLEM'
            print record
            continue
        trace = trace[0]

        if len(trace) == 1: continue

        sh_len = record[helpers.SH_LEN]
        s, t = trace[0], trace[-1]

        is_vf_prelabeled_l = []
        is_lp_prelabeled_hard_l = []
        is_lp_prelabeled_soft_l = []

        is_vf_degree_l = []
        is_lp_degree_hard_l = []
        is_lp_degree_soft_l = []

        is_vf_closeness_l = []
        is_lp_closeness_hard_l = []
        is_lp_closeness_soft_l = []

        stretch_dist = stretch_list[idx]
        real_stretch_dist = []
        for current_stretch in stretch_dist:
            random_length = sh_len + current_stretch
            random_path = helpers.random_route_walk(g, s, t, random_length)
            real_stretch_dist.append(len(random_path) - sh_len)
            if len(random_path) == 0:
                empty += 1

            if flags[FLAG_PRELABELED]:
                (is_vf_prelabeled,
                 is_lp_prelabeled_soft,
                 is_lp_prelabeled_hard) = vf_attributes(g,random_path,
                                                   vft.PRELABELED,
                                                   flags[FLAG_LP_SOFT],
                                                   flags[FLAG_LP_HARD],
                                                   vf_g_pre)
                is_vf_prelabeled_l.append(is_vf_prelabeled)
                is_lp_prelabeled_soft_l.append(is_lp_prelabeled_soft)
                is_lp_prelabeled_hard_l.append(is_lp_prelabeled_hard)

            if flags[FLAG_DEGREE]:
                (is_vf_degree,
                 is_lp_degree_soft,
                 is_lp_degree_hard) = vf_attributes(g, random_path,
                                                    vft.DEGREE,
                                                    flags[FLAG_LP_SOFT],
                                                    flags[FLAG_LP_HARD],
                                                    vf_g_degree)
                is_vf_degree_l.append(is_vf_degree)
                is_lp_degree_soft_l.append(is_lp_degree_soft)
                is_lp_degree_hard_l.append(is_lp_degree_hard)

            if flags[FLAG_CLOSENESS]:
                (is_vf_closeness,
                 is_lp_closeness_soft,
                 is_lp_closeness_hard) = vf_attributes(g, random_path,
                                                       vft.CLOSENESS,
                                                       flags[FLAG_LP_SOFT],
                                                       flags[FLAG_LP_HARD],
                                                       vf_g_closeness)
                is_vf_closeness_l.append(is_vf_closeness)
                is_lp_closeness_soft_l.append(is_lp_closeness_soft)
                is_lp_closeness_hard_l.append(is_lp_closeness_hard)

        result = {
            helpers.RANDOM_GULYAS_WALK_ROUTES_RQ_STRETCH: stretch_dist,
            helpers.RANDOM_GULYAS_WALK_ROUTES_STRETCH: real_stretch_dist,
            helpers.RANDOM_GULYAS_WALK_ROUTES_VF_PRELABELED: is_vf_prelabeled_l,
            helpers.RANDOM_GULYAS_WALK_ROUTES_VF_DEGREE: is_vf_degree_l,
            helpers.RANDOM_GULYAS_WALK_ROUTES_VF_CLOSENESS: is_vf_closeness_l,
            helpers.RANDOM_GULYAS_WALK_ROUTES_LP_SOFT_PRELABELED: is_lp_prelabeled_soft_l,
            helpers.RANDOM_GULYAS_WALK_ROUTES_LP_HARD_PRELABELED: is_lp_prelabeled_hard_l,
            helpers.RANDOM_GULYAS_WALK_ROUTES_LP_SOFT_DEGREE: is_lp_degree_soft_l,
            helpers.RANDOM_GULYAS_WALK_ROUTES_LP_HARD_DEGREE: is_lp_degree_hard_l,
            helpers.RANDOM_GULYAS_WALK_ROUTES_LP_SOFT_CLOSENESS: is_lp_closeness_soft_l,
            helpers.RANDOM_GULYAS_WALK_ROUTES_LP_HARD_CLOSENESS: is_lp_closeness_hard_l,
        }

        record.update(result)


def vf_attributes(g, trace, vfmode, get_lp_soft, get_lp_hard, vf_g=None):
    is_vf = int(vft.is_valley_free(g, trace, vfmode))
    is_lp_soft = -1
    is_lp_hard = -1
    if is_vf:
        if get_lp_soft:
            lp_soft = vft.is_local_preferenced(g, trace,
                                               vf_g=vf_g,
                                               first_edge=True,
                                               vfmode=vfmode)
            is_lp_soft = int(lp_soft)
        else:
            is_lp_prelabeled_soft = -1

        if get_lp_hard:
            lp_hard = vft.is_local_preferenced(g, trace,
                                               vf_g=vf_g,
                                               first_edge=False,
                                               vfmode=vfmode)
            is_lp_hard = int(lp_hard)
        else:
            is_lp_hard = -1

    return (is_vf, is_lp_soft, is_lp_hard)
    

if __name__ == '__main__':
    main()
