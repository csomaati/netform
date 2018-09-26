from tools import helpers, misc
import argparse
from tools.valley_free_tools import VFT as vft
from collections import Counter
import collections
import json
import igraph
import numpy as np
import logging

logger = logging.getLogger('compnet.statistics')


def main():
    parser = argparse.ArgumentParser(description='Display statistical informations',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('network')
    parser.add_argument('metadata')
    parser.add_argument('out', type=str, help='folder path for results')

    parser.add_argument('--stretch-stat',
                        dest='stretch_stat',
                        action='store_true')

    parser.add_argument('--eye-stat',
                        dest='eye_stat',
                        action='store_true')

    parser.add_argument('--eye-stat-basic',
                        dest='eye_stat_basic',
                        action='store_true')

    parser.add_argument('--ba-stat',
                        dest='ba_stat',
                        nargs='+')

    parser.add_argument('--degree-dist',
                        dest='degree_dist',
                        action='store_true')

    parser.add_argument('--simple-load',
                        dest='simple_load',
                        action='store_true')

    parser.add_argument('--load2d')

    parser.add_argument('--stats',
                        dest='stats',
                        action='store_true')

    parser.add_argument('--upwalk')

    parser.add_argument('--verbose', '-v', action='count', default=0)

    arguments = parser.parse_args()

    arguments.verbose = min(len(helpers.LEVELS), arguments.verbose)
    logging.getLogger('compnet').setLevel(helpers.LEVELS[arguments.verbose])

    g = helpers.load_network(arguments.network)
    meta = helpers.load_from_json(arguments.metadata)

    out_folder_path = arguments.out
    if out_folder_path.endswith('/'):
        out_folder_path = out_folder_path[:-1]

    # print 'WIKI MODE!!!!!'
    # meta = [x for x in meta if x[helpers.SH_LEN] == 4 and x[helpers.TRACE_LEN] < 10]

    # print 'ONLY WITH RANDOM NONVF WALK'
    # meta = [x for x in meta if helpers.RANDOM_NONVF_WALK_RUN_COUNT in x]

    if arguments.stretch_stat:
        logger.info('Generate stretch statistics')
        stretch_stat(meta, out_folder_path)

    if arguments.eye_stat:
        logger.info('Generate Eye statistics')
        eye_stat(meta, out_folder_path)

    if arguments.eye_stat_basic:
        logger.info('Generate Basic Eye statistics')
        eye_stat_basic(meta, out_folder_path)

    if arguments.ba_stat:
        logger.info('Generate Barabasi-Albert statistics')
        ba_stat(meta, arguments.ba_stat, out_folder_path)

    if arguments.degree_dist:
        logger.info('Generate degree distributions')
        degree_distribution_stat(g, out_folder_path)

    if arguments.load2d:
        logger.info('Generate load stat')
        tr = helpers.load_from_json(arguments.load2d)
        load2d(g, tr, out_folder_path)

    if arguments.simple_load:
        logger.info('Generate simple load based on meta')
        simple_load(g, meta, out_folder_path)

    if arguments.stats:
        logger.info('Stat gen')
        stats(g, meta  )
        # stat_printer(statistic)

    if arguments.upwalk:
        logger.info('Upwalk')
        upwalk(arguments.upwalk, out_folder_path)


def _load(g, traceroutes):
    trace_nodes = [y for x in traceroutes for y in x]
    trace_counter = collections.Counter(trace_nodes)
    trace_list = [[node, trace_counter[node], g.vs.find(node)['closeness']]
                  for node in trace_counter]
    trace_list = sorted(trace_list, key=lambda x: x[2])

    return trace_list


def _fwrite(data, field, fname, header):
    with open(fname, 'w') as f:
        f.write(header)
        for k, v in data.iteritems():
            f.write('%s;%s;%s\n' % (k, v[field], v['CLOSENESS']))

    
def load2d(g, syntetic_meta, out_folder_path):

    nodes = [vs['name'] for vs in g.vs]
    node_map = {
        x: {
            'BASE': 0,
            'SH': 0,
            'TR': 0,
            'SR': 0,
            'CLOSENESS': g.vs.find(x)['closeness']
        } for x in nodes
    }
   
    BASE, SH, TR, SR = zip(*syntetic_meta)

    BASE_list = _load(g, BASE)
    SH_list = _load(g, SH)
    TR_list = _load(g, TR)
    SR_list = _load(g, SR)

    for n in BASE_list:
        node_map[n[0]]['BASE'] += n[1]
    for n in SH_list:
        node_map[n[0]]['SH'] += n[1]
    for n in TR_list:
        node_map[n[0]]['TR'] += n[1]
    for n in SR_list:
        node_map[n[0]]['SR'] += n[1]

    header = 'NODE;COUNT;CLOSENESS\n'
    _fwrite(node_map, 'BASE', '%s/base_list.csv' % out_folder_path, header)
    _fwrite(node_map, 'SH', '%s/sh_list.csv' % out_folder_path, header)
    _fwrite(node_map, 'TR', '%s/tr_list.csv' % out_folder_path, header)
    _fwrite(node_map, 'SR', '%s/sr_list.csv' % out_folder_path, header)


def simple_load(g, meta, out_folder_path):
    nodes = [vs['name'] for vs in g.vs]
    node_map = {
        x: {
            'SIMPLE': 0,
            'CLOSENESS': g.vs.find(x)['closeness']
        } for x in nodes
    }

    traces = [x[helpers.TRACE] for x in meta]
    SIMPLE_list = _load(g, traces)
    for n in SIMPLE_list:
        node_map[n[0]]['SIMPLE'] += n[1]

    header = 'NODE;COUNT;CLOSENESS\n'
    _fwrite(node_map, 'SIMPLE', '%s/simple_list.csv' % out_folder_path, header)


def stats(g, meta ):
    res = dict()
    res['01. Node count'] = g.vcount()
    res['02. Edge count'] = g.ecount()
    res['03. avg. degree'] = np.mean(g.degree(mode=igraph.OUT))
    res['04. avg. clust.'] = g.transitivity_avglocal_undirected()
    res['05. avg. dist.'] = g.average_path_length()
    res['06. diameter'] = g.diameter()
    res['07. Trace count'] = len(meta)
    res['08. Trace avg. len'] = np.mean([len(x[helpers.TRACE]) for x in meta])
    res['09. VF ratio'] = sum([x[helpers.IS_VF_CLOSENESS] for x in meta])
    res['10. LP ratio'] = sum([x[helpers.IS_LP_SOFT_CLOSENESS] for x in meta])
    res['11. VF distribution'] = ''
    vf_stretches = [x[helpers.HOP_STRETCH]
                    for x in meta if x[helpers.IS_VF_CLOSENESS] == 1]
    stretches = [x[helpers.HOP_STRETCH] for x in meta]
    stretch_counter = collections.Counter([x[helpers.HOP_STRETCH]
                                           for x in meta])
    stretch_vf_counter = collections.Counter(vf_stretches)
    idx = 11
    for stretch in xrange(min(stretches), max(stretches) + 1):
        idx += 1
        stretched_trace_count = stretch_counter[stretch]
        vf_stretched_trace_count = stretch_vf_counter[stretch]
        stretched_vf_ratio = 0 if stretched_trace_count == 0 else vf_stretched_trace_count / float(stretched_trace_count)
        k = '%d.   %d' % (idx, stretch)
        res[k] = '%f%%[%d/%d]' % (100 * stretched_vf_ratio,
                                  vf_stretched_trace_count,
                                  stretched_trace_count)

    outstr = ''
    for key in sorted(res.iterkeys()):
        outstr += ';%s' % res[key]
        logger.info('%s: %s' % (key, res[key]))


def stretch_stat(meta, out_folder_path):
    results = []
    max_stretch = max([x[helpers.TRACE_LEN] - x[helpers.SH_LEN] for x in meta])

    for stretch in range(0, max_stretch + 1):
        metas = [x for x in meta if x[helpers.TRACE_LEN] - x[helpers.SH_LEN] == stretch]
        results.append([stretch, len(metas)])

    line_template = '{stretch};{count};{all_trace}\n'
    with open('{f}/stretch_stat'.format(f=out_folder_path), 'w') as f:
        # f.write('# Count how many route in every stretch group\n')
        f.write('STRETCH;TRACECOUNT;ALL\n')
        for result in results:
            f.write(line_template.format(stretch=result[0],
                                         count=result[1],
                                         all_trace=len(meta)))


# Segedfuggvent. Parameterben kap egy strukturat egy konkret mereshez,
# ahol minden elem egy STRETCH, IS_VF, IS_LP_SOFT triplet. Ez alapjan
# kiszamolja a stretchekhez tartozo darabszamokat:
# STRETCH TRACE_COUNT VF_COUNT LP_COUNT
# Opcionalisan megadhato a max stretch, addig fog szamolni. Ha elmarad
# akkor kiszamolja a datasetbol
def _stretch_summarize(dataset, max_stretch=-1):
    STRETCH, IS_VF, IS_LP_SOFT = range(3)
    result = []
    if max_stretch == -1:
        max_stretch = max([x[STRETCH] for x in dataset])

    logger.debug('Max stretch: %d' % max_stretch)

    for stretch in xrange(max_stretch + 1):
        ds = [x for x in dataset if x[STRETCH] == stretch]
        stretched_trace_count = len(ds)
        logger.debug('stretch: %3d -- trace: %d' % (stretch, stretched_trace_count))

        vf_count = sum([x[IS_VF] for x in ds])
        lp_soft_count = sum([x[IS_LP_SOFT] for x in ds])

        result.append([stretch, stretched_trace_count, vf_count, lp_soft_count])

    return result


def upwalk(upwalk_f, out_folder_path):
    data = helpers.load_from_json(upwalk_f)
    keys = sorted(list(set(list(data['RANDOM'].keys() + data['REAL'].keys()))))
    with open('{}/upwalk'.format(out_folder_path), 'w') as f:
        f.write('IDX;REAL;RANDOM\n')
        for k in keys:
            f.write('{};{};{}\n'.format(k, data['REAL'].get(k, 0),
                                        data['RANDOM'].get(k, 0)))

def eye_stat_basic(meta, out_folder_path):
    STRETCH, TRACE_COUNT, VF_COUNT, LP_COUNT = range(4)
    real_trace_dataset = []

    # elso lepesben a metabol elkulonithjuk a stretch, vf, lp tripleteket
    # a valos es a random mereseket kulon-kulon
    # A random meresek a random_trace_dataset-be kerulnek. A tomb minden eleme
    # egy random futtatas osszes tripletje, egymas utan. Vagyis a dataset annyi
    # elemu, ahany random futas lett szimulalva, es minden eleme, az adott indexu
    # futasban kinyert eredmenyek halmaza.
    for x in meta:
        real_row = [x[helpers.HOP_STRETCH],
                    x[helpers.IS_VF_CLOSENESS],
                    # a negativ ertekek csereje 0-ra
                    max(x[helpers.IS_LP_SOFT_CLOSENESS], 0)]
        real_trace_dataset.append(real_row)

    logger.debug('Real measurement count: %d' % len(real_trace_dataset))


    real_trace_result = _stretch_summarize(real_trace_dataset)
    max_stretch = max([x[STRETCH] for x in real_trace_result])

    template = '{stretch};{RTRCOUNT};{RVFCOUNT};{RLPCOUNT}\n'
    with open('%s/eye_stat_basic' % out_folder_path, 'w') as f:
        f.write('STRETCH;REAL_TR_COUNT;REAL_VF_COUNT;REAL_LP_COUNT\n')
        for x in xrange(0, max_stretch + 1):
            f.write(template.format(stretch=x,
                                    RTRCOUNT=real_trace_result[x][TRACE_COUNT],
                                    RVFCOUNT=real_trace_result[x][VF_COUNT],
                                    RLPCOUNT=real_trace_result[x][LP_COUNT],
            ))


def eye_stat(meta, out_folder_path):
    STRETCH, TRACE_COUNT, VF_COUNT, LP_COUNT = range(4)
    real_trace_dataset = []
    rnd_round = len(meta[0][helpers.RANDOM_GULYAS_WALK_ROUTES_STRETCH])
    random_trace_dataset = [[] for x in xrange(rnd_round)]
    logger.debug('Detected number of random rounds: %d' % rnd_round)

    # elso lepesben a metabol elkulonithjuk a stretch, vf, lp tripleteket
    # a valos es a random mereseket kulon-kulon
    # A random meresek a random_trace_dataset-be kerulnek. A tomb minden eleme
    # egy random futtatas osszes tripletje, egymas utan. Vagyis a dataset annyi
    # elemu, ahany random futas lett szimulalva, es minden eleme, az adott indexu
    # futasban kinyert eredmenyek halmaza.
    for x in meta:
        real_row = [x[helpers.HOP_STRETCH],
                    x[helpers.IS_VF_CLOSENESS],
                    # a negativ ertekek csereje 0-ra
                    max(x[helpers.IS_LP_SOFT_CLOSENESS], 0)]
        real_trace_dataset.append(real_row)

        for idx, rnd_stretch in enumerate(x[helpers.RANDOM_GULYAS_WALK_ROUTES_STRETCH]):
            random_trace_dataset[idx].append([
                rnd_stretch,
                x[helpers.RANDOM_GULYAS_WALK_ROUTES_VF_CLOSENESS][idx],
                # a negativ ertekek csereje 0-ra
                max(x[helpers.RANDOM_GULYAS_WALK_ROUTES_LP_SOFT_CLOSENESS][idx], 0)
            ])

    logger.debug('Real measurement count: %d' % len(real_trace_dataset))


    real_trace_result = _stretch_summarize(real_trace_dataset)
    max_stretch = max([x[STRETCH] for x in real_trace_result])
    rnd_vf_ratio = [[] for x in range(max_stretch + 1)]
    rnd_lp_ratio = [[] for x in range(max_stretch + 1)]
    rnd_trace_count = [[] for x in range(max_stretch + 1)]

    for rnd_measurement in random_trace_dataset:
        # a random utaknal kis esellyel, de lehetseges, hogy nincs
        # max stretchet elert random utvonal (noha torekedtunk ra)
        # hogy azonosak legyenek a dimenziok, ezert kikenyszeritjuk
        # hogy menjunk el max_stretch ertekig a szamolasnal
        rnd_summary = _stretch_summarize(rnd_measurement, max_stretch)
        for res in rnd_summary:
            vf_ratio = res[VF_COUNT] / float(res[TRACE_COUNT]) if res[TRACE_COUNT] else np.nan
            lp_ratio = res[LP_COUNT] / float(res[VF_COUNT]) if res[VF_COUNT] else np.nan
            rnd_trace_count[res[STRETCH]].append(res[TRACE_COUNT])
            rnd_vf_ratio[res[STRETCH]].append(vf_ratio)
            rnd_lp_ratio[res[STRETCH]].append(lp_ratio)

    template = '{stretch};{RTRCOUNT};{RVFCOUNT};{RLPCOUNT};{RNDVFMEAN};{RNDVF10};{RNDVF90};{RNDLPMEAN};{RNDLP10};{RNDLP90};{RNDTRCOUNTMEAN}\n'
    with open('%s/eye_stat' % out_folder_path, 'w') as f:
        f.write('STRETCH;REAL_TR_COUNT;REAL_VF_COUNT;REAL_LP_COUNT;RND_VF_MEAN;RND_VF_10;RND_VF_90;RND_LP_MEAN;RND_LP_10;RND_LP_90;RND_TRACE_COUNT_MEAN\n')
        for x in xrange(0, max_stretch + 1):
            f.write(template.format(stretch=x,
                                    RTRCOUNT=real_trace_result[x][TRACE_COUNT],
                                    RVFCOUNT=real_trace_result[x][VF_COUNT],
                                    RLPCOUNT=real_trace_result[x][LP_COUNT],
                                    RNDVFMEAN=np.nanmean(rnd_vf_ratio[x]),
                                    RNDVF10=np.nanpercentile(rnd_vf_ratio[x], 10),
                                    RNDVF90=np.nanpercentile(rnd_vf_ratio[x], 90),
                                    RNDLPMEAN=np.nanmean(rnd_lp_ratio[x]),
                                    RNDLP10=np.nanpercentile(rnd_lp_ratio[x], 10),
                                    RNDLP90=np.nanpercentile(rnd_lp_ratio[x], 90),
                                    RNDTRCOUNTMEAN=np.nanmean(rnd_trace_count[x])
            ))


def ba_stat(meta, ba_files, out_folder_path):
    max_stretch = 4
    vf_res = [[] for x in range(max_stretch + 1)]
    lp_res = [[] for x in range(max_stretch + 1)]
    for f_name in ba_files:
        with open(f_name) as f:
            data = json.load(f)
            
        for d in data:
            stretch, trace_count, is_vf_count, is_lp_count = d
            vf_res[stretch].append(is_vf_count / float(trace_count))
            lp_res[stretch].append(is_lp_count / float(is_vf_count))

    template = '{stretch};{BAVFMEAN};{BAVF10};{BAVF90};{BALPMEAN};{BALP10};{BALP90}\n'
    with open('%s/ba_eye_stat' % out_folder_path, 'w') as f:
        f.write('STRETCH;BA_VF_MEAN;BA_VF_10;BA_VF_90;BA_LP_MEAN;BA_LP_10;BA_LP_90\n')
        for stretch, vf, lp in zip(xrange(max_stretch + 1), vf_res, lp_res):
            f.write(template.format(stretch=stretch,
                                    BAVFMEAN=np.nanmean(vf),
                                    BAVF10=np.nanpercentile(vf, 10),
                                    BAVF90=np.nanpercentile(vf, 90),
                                    BALPMEAN=np.nanmean(lp),
                                    BALP10=np.nanpercentile(lp, 10),
                                    BALP90=np.nanpercentile(lp, 90)))


def degree_distribution_stat(g, out_folder_path):
    in_degrees = g.degree(mode=igraph.IN)
    out_degrees = g.degree(mode=igraph.OUT)
    all_degrees = g.degree(mode=igraph.ALL)

    in_degree_dist = Counter(in_degrees)
    out_degree_dist = Counter(out_degrees)
    all_degree_dist = Counter(all_degrees)

    template = '{degree};{count}\n'

    for fname, dist in (('in_degree_dist', in_degree_dist),
                        ('out_degree_dist', out_degree_dist),
                        ('all_degree_dist', all_degree_dist)):
        stat = zip(dist.iterkeys(), dist.itervalues())
        with open('{f}/{fname}'.format(f=out_folder_path, fname=fname), 'w') as f:
            f.write('DEGREE;COUNT\n')
            for x in stat:
                f.write(template.format(degree=x[0], count=x[1]))


def degree_dist_print(g, fname):
    fname = '%s_degree_dist.pdf' % fname
    degrees = [g.degree(x) for x in g.vs]
    degrees, bins = np.histogram(degrees, bins=max(degrees), density=True)
    # degrees = np.cumsum(hist_degree)

    xvalues = bins[:-1]

    ref_xvalues = np.arange(int(min(xvalues)), int(max(xvalues)), 1)
    ref_points = [x**-1.2 for x in ref_xvalues]
    ref_points2 = [x**-1.7 for x in ref_xvalues]

    fig, ax = plt.subplots()
    ax.plot(xvalues, degrees)
    ax.plot(ref_xvalues, ref_points)
    ax.plot(ref_xvalues, ref_points2)
    ax.set_xlabel('')
    ax.set_ylabel('Degree')
    ax.set_title('Node degree distribution')
    ax.set_yscale('log')
    ax.set_xscale('log')
    ax.set_ylim([min(degrees)-1, max(degrees)+1])
    # ax.set_xlim([1, 10000])
    ax.yaxis.grid(True, which='major')

    # plt.gca().invert_yaxis()

    logger.info(fname)
    pdf_file = PdfPages(fname)
    plt.savefig(pdf_file, format='pdf')
    pdf_file.close()

    plt.show()
    # igraph.plot(g.degree_distribution(), log="xy")


def stat_printer(statistic):
    trace_count = float(statistic.get('tc', -1))
    vf_degree_route_count = statistic.get('vf_degree', -1)
    vf_prelabeled_route_count = statistic.get('vf_prelabeled', -1)
    vf_closeness_route_count = statistic.get('vf_closeness', -1)
    random_walk_vf_closeness_route_count = statistic.get('random_walk_vf_closeness', -1)
    lp_soft_prelabeled_count = statistic.get('lp_soft_prelabeled', -1)
    lp_hard_prelabeled_count = statistic.get('lp_hard_prelabeled', -1)
    lp_soft_degree_count = statistic.get('lp_soft_degree', -1)
    lp_hard_degree_count = statistic.get('lp_hard_degree', -1)
    lp_soft_closeness_count = statistic.get('lp_soft_closeness', -1)
    lp_hard_closeness_count = statistic.get('lp_hard_closeness', -1)
    sh_pred = statistic.get('sh_pred', -1)
    ppvf_pred = statistic.get('ppvf_pred', -1)
    all_pred = statistic.get('all_pred', -1)
    combined_pred = statistic.get('smart_pred', -1)
    clustering_coeff = statistic.get('cc', -1.0)
    average_distance = statistic.get('ad', -1.0)

    rich_club_coeff = statistic.get('rc', -1.0)

    trace_avg_len = statistic.get('tl', -1)
    trace_max_len = statistic.get('tml', -1)
    max_trace_example = statistic.get('tml_sentence', '')
    trace_min_len = statistic.get('tsl', -1)
    min_trace_example = statistic.get('tsl_sentence', '')

    logger.info('Summary')
    logger.info('VF PRELABELED route count:..... %d [%5.1f%%]' % (vf_prelabeled_route_count, 100 * vf_prelabeled_route_count / trace_count))
    logger.info('VF OUT DEGREE route count:..... %d [%5.1f%%]' % (vf_degree_route_count, 100 * vf_degree_route_count / trace_count))
    logger.info('VF CLOSENESS route count:..... %d [%5.1f%%]' % (vf_closeness_route_count, 100 * vf_closeness_route_count / trace_count))
    logger.info('Random walk VF CLOSENESS route count:..... %d [%5.1f%%]' % (random_walk_vf_closeness_route_count, 100 * random_walk_vf_closeness_route_count / trace_count))
    logger.info('LP_HARD_PRE route count:... %d [%5.1f%%]' % (lp_hard_prelabeled_count, 100 * lp_hard_prelabeled_count / trace_count))
    logger.info('LP_SOFT_PRE route count:... %d [%5.1f%%]' % (lp_soft_prelabeled_count, 100 * lp_soft_prelabeled_count / trace_count))
    logger.info('LP_HARD_DEGREE route count:... %d [%5.1f%%]' % (lp_hard_degree_count, 100 * lp_hard_degree_count / trace_count))
    logger.info('LP_SOFT_DEGREE route count:... %d [%5.1f%%]' % (lp_soft_degree_count, 100 * lp_soft_degree_count / trace_count))
    logger.info('LP_HARD_CLOSENESS route count:... %d [%5.1f%%]' % (lp_hard_closeness_count, 100 * lp_hard_closeness_count / trace_count))
    logger.info('LP_SOFT_CLOSENESS route count:... %d [%5.1f%%]' % (lp_soft_closeness_count, 100 * lp_soft_closeness_count / trace_count))
    logger.info('SH prediciton:...... %d [%5.1f%%]' % (sh_pred, 100 * sh_pred / trace_count))
    logger.info('++VF prediction:.... %d [%5.1f%%]' % (ppvf_pred, 100 * ppvf_pred / trace_count))
    logger.info('ALL prediction:..... %d [%5.1f%%]' % (all_pred, 100 * all_pred / trace_count))
    logger.info('SH and ++VF:........ %d [%5.1f%%]' % (combined_pred, 100 * combined_pred / trace_count))
    logger.info('Rich club coeff:.... %f' % (rich_club_coeff))
    logger.info('====== Network stat ======')
    logger.info('Average distance: %f' % (average_distance))
    logger.info('Clustering coefficient: %f' % (clustering_coeff))
    logger.info('====== Trace stat ======')
    logger.info('Average length: %f' % (trace_avg_len))
    logger.info('Max trace length: %d [%s]' % (trace_max_len, max_trace_example))
    logger.info('Min trace length: %d [%s]' % (trace_min_len, min_trace_example))


def purify(g, meta, filters):

    results = dict()
    traceroutes = [x[helpers.TRACE] for x in meta]

    if 'cc' in filters:
        results['cc'] = g.transitivity_undirected(mode=igraph.TRANSITIVITY_ZERO)

    if 'ad' in filters:
        results['ad'] = g.average_path_length(directed=False, unconn=True)

    if 'nc' in filters:
        results['nc'] = g.vcount()

    if 'ec' in filters:
        results['ec'] = g.ecount()

    if 'rc' in filters:
        k = 20
        scores = g.degree()
        indices = range(g.vcount())
        indices.sort(key=scores.__getitem__)
        e_k = [x for x in g.es
               if g.degree(x.source) >= k and g.degree(x.target) >= 50]
        e_k2 = float(2 * len(e_k))
        n_k = float(len([x for x in g.vs if g.degree(x) >= k]))

        fi_k = e_k2 / (n_k * (n_k - 1))
        results['rc'] = fi_k

    # remove traces with unknown nodes
    before_caida = len(traceroutes)
    traceroutes = vft.trace_in_vertex_id(g, traceroutes)

    if 'tc' in filters:
        results['tc'] = len(traceroutes)

    if 'tl' in filters:
        results['tl'] = np.mean([len(x) for x in traceroutes])

    if 'tml' in filters:
        results['tml'] = max([len(x) for x in traceroutes])
        results['tml_sentence'] = vft.trace_in_vertex_name(g, [x for x in traceroutes if len(x) == results['tml']])[0]

    if 'tsl' in filters:
        results['tsl'] = min([len(x) for x in traceroutes])
        results['tsl_sentence'] = vft.trace_in_vertex_name(g, [x for x in traceroutes if len(x) == results['tsl']])[0]

    if 'rt' in filters:
        results['rt'] = before_caida - len(traceroutes)

    if 'vf_prelabeled' in filters:
        results['vf_prelabeled'] = len([x for x in meta if x[helpers.IS_VF_PRELABELED] == 1])

    if 'vf_degree' in filters:
        results['vf_degree'] = len([x for x in meta if x[helpers.IS_VF_DEGREE] == 1])

    if 'vf_closeness' in filters:
        results['vf_closeness'] = len([x for x in meta if x[helpers.IS_VF_CLOSENESS] == 1])

    if 'random_walk_vf_closeness' in filters:
        results['random_walk_vf_closeness'] = len([x for x in meta if x[helpers.RANDOM_WALK_VF_CLOSENESS_ROUTE] == 1])

    if 'lp_soft_prelabeled' in filters:
        results['lp_soft_prelabeled'] = len([x for x in meta if x[helpers.IS_LP_SOFT_PRELABELED] == 1])

    if 'lp_hard_prelabeled' in filters:
        results['lp_hard_prelabeled'] = len([x for x in meta if x[helpers.IS_LP_HARD_PRELABELED] == 1])

    if 'lp_soft_degree' in filters:
        results['lp_soft_degree'] = len([x for x in meta if x[helpers.IS_LP_SOFT_DEGREE] == 1])

    if 'lp_hard_degree' in filters:
        results['lp_hard_degree'] = len([x for x in meta if x[helpers.IS_LP_HARD_DEGREE] == 1])

    if 'lp_soft_closeness' in filters:
        results['lp_soft_closeness'] = len([x for x in meta if x[helpers.IS_LP_SOFT_CLOSENESS] == 1])

    if 'lp_hard_closeness' in filters:
        results['lp_hard_closeness'] = len([x for x in meta if x[helpers.IS_LP_HARD_CLOSENESS] == 1])

    if 'pred' in filters:
        # SH prediction
        sh_pred = len([x for x in meta if x[helpers.SH_LEN] == x[helpers.TRACE_LEN]])
        # only VF with 1 extra hop
        ppvf_pred = len([x for x in meta if x[helpers.TRACE_LEN] <= x[helpers.SH_LEN] + 1 and x[helpers.IS_VF_DEGREE] == 1])
        # SH or VF with one extra hop
        smart_pred = len([x for x in meta if x[helpers.SH_LEN] == x[helpers.TRACE_LEN] or (x[helpers.TRACE_LEN] <= x[helpers.SH_LEN] + 1 and x[helpers.IS_VF_DEGREE] == 1)])

        # Brute force prediction
        all_pred = len([x for x in meta if x[helpers.TRACE_LEN] <= x[helpers.SH_LEN] + 1])

        results['sh_pred'] = sh_pred
        results['ppvf_pred'] = ppvf_pred
        results['smart_pred'] = smart_pred
        results['all_pred'] = all_pred

    return results

if __name__ == '__main__':
    misc.logger_setup()
    main()


# # brain snippet
# import csv
# import collections
# STRETCH, COUNT, SUM = range(0, 3)
# maxid = 39
# maxstretch = 0
# res = []
# for idx in xrange(0, maxid + 1):
#     ds = collections.defaultdict(lambda: 'NA')
#     with open('%d_brain_stretch_stat.csv' % idx, 'rb') as f:
#         reader = csv.reader(f, delimiter=';')
#         line = 0
#         for row in reader:
#             line += 1
#             if line < 3: continue
#             if int(row[COUNT]) == 0: continue
#             ds[int(row[STRETCH])] = int(row[COUNT]) / float(row[SUM])
#             maxstretch = max(maxstretch, int(row[STRETCH]))

#     res.append(ds)

# with open('brain_stretch_stat.csv', 'w') as f:
#     f.write('# generated with statistics.py brain_snippet based on brain_stretch_stat_csv folder\n')
#     f.write('# route percentage in every stretch in every measurement\n')
#     f.write('STRETCH')
#     for i in xrange(0, maxid + 1):
#         f.write(';BRAIN%d' % i)
#     f.write('\n')
#     for i in xrange(0, maxstretch + 1):
#         f.write('%d' % i)
#         for x in xrange(0, maxid + 1):
#             f.write(';%s' % res[x][i])
#         f.write('\n')
