import random
from tools import helpers, misc
import argparse
import tools.progressbar1 as progressbar1
import igraph as i
from tools.valley_free_tools import VFT as vft
import numpy as np
import copy
import logging

misc.logger_setup()
logger = logging.getLogger('compnet.sandbox')
logging.getLogger('compnet').setLevel(logging.INFO)


def main():

    parser = argparse.ArgumentParser(description='SANDBOX mode. Write something useful here', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('network')
    parser.add_argument('meta')
    parser.add_argument('out')
    parser.add_argument('--count', type=int, default=1000)

    arguments = parser.parse_args()

    g = helpers.load_network(arguments.network)
    meta = helpers.load_from_json(arguments.meta)
    out = arguments.out

    g.vs['closeness'] = g.closeness()

    k = [x for x in meta if x[helpers.SH_LEN] == x[helpers.TRACE_LEN]]
    random.shuffle(k)
    k = k[:100]
    for m in k:
        if m[helpers.SH_LEN] != m[helpers.TRACE_LEN]: continue
        trace = m[helpers.TRACE]
        o = [g.vs.find(x)['closeness'] for x in trace]
        print 'ORIGINAL TRACE: \n%s--%s: %s ' % (max(o), sum(o), o)

        l = []
        b = []

        s, t = trace[0], trace[-1]
        sh = g.get_all_shortest_paths(s, t)
        print 'SH paths:'
        for p in sh:
            tr = [g.vs[x]['closeness'] for x in p]
            print '%s--%s' % (max(tr), sum(tr))
            l.append(max(tr))
            b.append(sum(tr))

        print 'AVG:\n %s' % (sum(l) / float(len(l)))
        l_sorted = sorted(l, reverse=True)
        b_sorted = sorted(b, reverse=True)
        print 'SORTED MAX:'
        for x in l_sorted:
            if x == max(o): print '!!!'
            print x
        print 'SORTED SUM:'
        for x in b_sorted:
            if x == sum(o): print '!!!!'
            print x

        raw_input()

    exit(0)

    purify(g, meta, out, arguments.count)


def purify(g, meta, out, count=1000):
    results = list()
    results2 = list()
    results3 = list()
    all_vf = 0
    all_nonvf = 0
    all_vf_closeness = 0
    all_nonvf_closeness = 0

    short_results = list()
    short_results2 = list()
    short_results3 = list()
    all_short_vf = 0
    all_short_nonvf = 0
    all_short_vf_closeness = 0
    all_short_nonvf_closeness = 0

    long_results = list()
    long_results2 = list()
    long_results3 = list()
    all_long_vf = 0
    all_long_nonvf = 0
    all_long_vf_closeness = 0
    all_long_nonvf_closeness = 0

    # remove traces with already calculated all_path
    logger.warn('[r]ONLY NOT FILLED PATHS[/]')
    meta = [x for x in meta if not helpers.ALL_PATH_COUNT in x]

    # traces with a maximum stretch
    logger.warn('[r]!!!ONLY WITH LOW STRETCH[/]')
    meta = [x for x in meta if x[helpers.STRETCH] < 4]

    # shorter meta records
    logger.warn('[r]!!!ONLY SHORT TRACES[/]')
    meta = [x for x in meta if len(x[helpers.TRACE]) < 5]

    meta_map = {tuple(x[helpers.TRACE]): x for x in meta}

    # traceroutes = [x for x in meta if x[TRACE_LEN] == x[SH_LEN]]
    logger.info('All trace count: %d' % len(meta))
    tr_count = min(len(meta), count)
    meta = random.sample(meta, tr_count)
    logger.info('Chosen trace count: %d' % len(meta))

    real_vf = [x for x in meta if x[helpers.IS_VF] == 1]
    real_nonvf = [x for x in meta if x[helpers.IS_VF] == 0]

    real_vf_closeness = [x for x in meta if x[helpers.IS_VF_CLOSENESS] == 1]
    real_nonvf_closeness = [x for x in meta if x[helpers.IS_VF_CLOSENESS] == 0]

    logger.info('Real vf: %f[%d]' % ((len(real_vf)/float(len(meta)), len(real_vf))))
    logger.info('Real nonvf: %f[%d]' % ((len(real_nonvf)/float(len(meta)), len(real_nonvf))))

    logger.info('Real vf closeness: %f[%d]' % ((len(real_vf_closeness)/float(len(meta)), len(real_vf_closeness))))
    logger.info('Real nonvf closeness: %f[%d]' % ((len(real_nonvf_closeness)/float(len(meta)), len(real_nonvf_closeness))))

    logger.info('Remove unknown traces. Trace count before: %d' % len(meta))
    traceroutes = [x[helpers.TRACE] for x in meta]
    traceroutes, ignored = vft.trace_clean(g, traceroutes)
    logger.info('Traceroutes after: %d. Ignored: %d' % (len(traceroutes), ignored))

    traceroutes = vft.trace_in_vertex_id(g, traceroutes)

    progress = progressbar1.AnimatedProgressBar(end=len(traceroutes), width=15)
    for trace in traceroutes:
        progress += 1
        progress.show_progress()

        for x in range(0, g.vcount()):
            g.vs[x]['traces'] = dict()

        s, t = trace[0], trace[-1]
        sh_path = g.get_all_shortest_paths(s, t, mode=i.OUT)
        all_path = helpers.dfs_mark(copy.deepcopy(g), s, t, len(trace))

        # if len(sh_path) != len(all_path):
        #     print len(sh_path)
        #     print len(all_path)
        #     print s, t

        # sanity check
        for x in all_path:
            if x[0] != s or x[-1] != t:
                logger.error('ALERT')
        if len(set([tuple(x) for x in all_path])) != len(all_path):
            logger.error('LENGTH ALERT')
            logger.error('%s' % len(all_path))
            logger.error('%s' % len(set([tuple(x) for x in all_path])))
            logger.error('%s' % sorted(all_path))

        long_path = [x for x in all_path if len(x) == len(trace)]
        short_path = [x for x in all_path if len(x) < len(trace)]

        named_trace = [g.vs[x]['name'] for x in trace]
        extra_meta = {
            helpers.ALL_PATH_COUNT: len(all_path),
            helpers.SAME_LONG_PATH_COUNT: len(long_path),
            helpers.SHORTER_PATH_COUNT: len(short_path)
        }
        meta_map[tuple(named_trace)].update(extra_meta)

        vf_count = sum([1 if vft.is_valley_free(g, x, vfmode=vft.PRELABELED) else 0 for x in all_path])
        nonvf = len(all_path) - vf_count

        vf_closeness_count = sum([1 if vft.is_valley_free(g, x, vfmode=vft.CLOSENESS) else 0 for x in all_path])
        nonvf_closeness = len(all_path) - vf_closeness_count

        tmp = [1 if vft.is_valley_free(g, x, vfmode=vft.PRELABELED) else 0 for x in short_path]
        short_vf_count = sum(tmp)
        short_nonvf = len(tmp) - short_vf_count

        tmp = [1 if vft.is_valley_free(g, x, vfmode=vft.CLOSENESS) else 0 for x in short_path]
        short_vf_closeness_count = sum(tmp)
        short_nonvf_closeness = len(tmp) - short_vf_closeness_count

        tmp = [1 if vft.is_valley_free(g, x, vfmode=vft.PRELABELED) else 0 for x in long_path]
        long_vf_count = sum(tmp)
        long_nonvf = len(tmp) - long_vf_count

        tmp = [1 if vft.is_valley_free(g, x, vfmode=vft.CLOSENESS) else 0 for x in long_path]
        long_vf_closeness_count = sum(tmp)
        long_nonvf_closeness = len(tmp) - long_vf_closeness_count

        extra_meta = {
            helpers.ALL_PATH_VF_COUNT: vf_closeness_count,
            helpers.SAME_LONG_PATH_VF_COUNT: long_vf_closeness_count,
            helpers.SHORTER_PATH_VF_COUNT: short_vf_closeness_count
        }
        meta_map[tuple(named_trace)].update(extra_meta)

        all_vf += vf_count
        all_nonvf += nonvf

        all_vf_closeness += vf_closeness_count
        all_nonvf_closeness += nonvf_closeness

        all_long_vf += long_vf_count
        all_long_nonvf += long_nonvf

        all_long_vf_closeness += long_vf_closeness_count
        all_long_nonvf_closeness += long_nonvf_closeness

        all_short_vf += short_vf_count
        all_short_nonvf += short_nonvf

        all_short_vf_closeness += short_vf_closeness_count
        all_short_nonvf_closeness += short_nonvf_closeness

        results.append(vf_count / float(len(all_path)))
        results3.append(vf_closeness_count / float(len(all_path)))
        if len(all_path) > 1: results2.append(vf_count / float(len(all_path)))

        long_results.append(long_vf_count / float(len(long_path)))
        long_results3.append(long_vf_closeness_count / float(len(long_path)))
        if len(long_path) > 1: long_results2.append(long_vf_count / float(len(long_path)))

        if len(short_path) > 0:
            short_results.append(short_vf_count / float(len(short_path)))
            short_results3.append(short_vf_closeness_count / float(len(short_path)))
        else:
            pass
            # short_results.append(0)
            # short_results3.append(0)
        if len(short_path) > 1: short_results2.append(short_vf_count / float(len(short_path)))

    # save mofified meta
    meta_mod = [x for x in meta_map.itervalues()]
    helpers.save_to_json(out, meta_mod)

    # print results
    print 'ALL'
    print 'VF count: %d' % all_vf
    print 'VF CLOSENESS count: %d' % all_vf_closeness
    print 'Non vf count: %d' % all_nonvf
    print 'Non vf CLOSENESS count: %d' % all_nonvf_closeness
    print 'VF perc: %f' % (all_vf/float(all_vf + all_nonvf))
    print 'VF CLOSENESS perc: %f' % (all_vf_closeness/float(all_vf_closeness + all_nonvf_closeness))
    print 'Mean VF prob: %f' % np.mean(results)
    print 'Mean VF CLOSENESS prob: %f' % np.mean(results3)
    print 'Mean VF2 prob: %f' % np.mean(results2)
    print '=========='
    print 'SHORT'
    print 'VF count: %d' % all_short_vf
    print 'VF  CLOSENESS count: %d' % all_short_vf_closeness
    print 'Non vf count: %d' % all_short_nonvf
    print 'Non vf CLOSENESS count: %d' % all_short_nonvf_closeness
    if all_short_vf + all_short_nonvf > 0:
        print 'VF perc: %f' % (all_short_vf/float(all_short_vf + all_short_nonvf))
    if all_short_vf_closeness + all_short_nonvf_closeness > 0:
        print 'VF CLOSENESS perc: %f' % (all_short_vf_closeness/float(all_short_vf_closeness + all_short_nonvf_closeness))
    print 'Mean VF prob: %f' % np.mean(short_results)
    print 'Mean VF CLOSENESS prob: %f' % np.mean(short_results3)
    print 'Mean VF2 prob: %f' % np.mean(short_results2)
    print '=-----------------'
    print 'LONG'
    print 'VF count: %d' % all_long_vf
    print 'VF CLOSENESS count: %d' % all_long_vf_closeness
    print 'Non vf count: %d' % all_long_nonvf
    print 'Non vf CLOSENESS count: %d' % all_long_nonvf_closeness
    print 'VF perc: %f' % (all_long_vf/float(all_long_vf + all_long_nonvf))
    print 'VF CLOSENESS perc: %f' % (all_long_vf_closeness/float(all_long_vf_closeness + all_long_nonvf_closeness))
    print 'Mean VF prob: %f' % np.mean(long_results)
    print 'Mean VF CLOSENESS prob: %f' % np.mean(long_results3)
    print 'Mean VF2 prob: %f' % np.mean(long_results2)

if __name__ == '__main__':
    main()



# def a(meta):
#  print '                 VF           NONVF          CLOSENESS'
#  for i in range(0, 18):
#   tmp = [x for x in meta if x[TRACE_LEN] == x[SH_LEN]+i]
#   if len(tmp) < 1: continue
#   vf = len([x for x in tmp if x[IS_VF] == 1])
#   vfcloseness = len([x for x in tmp if x[IS_VF_CLOSENESS] == 1])
#   nonvf = len([x for x in tmp if x[IS_VF] == 0])
#   # if i > 1:
#   #     k = [x[0] for x in tmp if x[IS_VF] == 1]
#   #     return k
#   allt = float(len(tmp))
#   print '%2d -- %5d[%6.2f%%]\t%5d[%6.2f%%]\t%5d[%6.2f%%]' % (i, vf, 100*(vf/allt), nonvf, 100*(nonvf/allt), vfcloseness, 100*(vfcloseness/allt))



# def vf(arr):
#     for i in range(0, len(arr)-2):
#         a, b, c = arr[i:i+3]
#         if (a>b and b==c) or (a>b and b<c) or (a==b and b==c) or (a==b and b<c): return False
#     return True


# import igraph as i
# import argparse
# from tools import helpers
# import random
# import copy
# import tools.progressbar1 as progressbar1
# from tools.valley_free_tools import VFT as vft
# import numpy as np
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_pdf import PdfPages

# # g_r_c = helpers.load_as_inferred_links('/mnt/ADAT/measurements3/data/airport/converted/topo_trace_rank_route_cheapest')
# g_r_c = i.load('/mnt/ADAT/measurements3/data/misc_networks/word_cooc.gml')
# degree_key = {x.index:g_r_c.degree(x.index) for x in g_r_c.vs}
# closeness_key = {x.index:g_r_c.closeness(x.index) for x in g_r_c.vs}
# max_random_graph = g_r_c.Degree_Sequence(g_r_c.degree(mode=i.ALL, loops=False), method='vl')
# rand_degree_key = {x.index:max_random_graph.degree(x.index) for x in max_random_graph.vs}
# rand_closeness_key = {x.index:max_random_graph.closeness(x.index) for x in max_random_graph.vs}


# def rich_club_coeff(g, k, ranks):
#     e_k = [x for x in g.es if ranks[x.source] >= k and ranks[x.target] >= k]
#     n_k = len([x for x in ranks.itervalues() if x >= k])

#     e_k2 = 2 * len(e_k)

#     if e_k2 < 1: return 0
#     if n_k < 2: raise RuntimeError('Never ever, previous if reached sooner')

#     fi_k = e_k2 / float(n_k * (n_k - 1))
#     return fi_k

# ratio_values = []
# steps = np.arange(min(closeness_key.itervalues()), max(closeness_key.itervalues())+1, 0.01)
# for k in steps:
#     fi = rich_club_coeff(g_r_c, k, closeness_key)
#     fi_ran = rich_club_coeff(max_random_graph, k, rand_closeness_key)
#     if fi_ran == 0: ratio = 0.0
#     else: ratio = fi/float(fi_ran)
#     ratio_values.append(ratio)

# # i.plot(g.degree_distribution(), log="xy")
# fig, ax = plt.subplots()
# ax.axhline(y=1, xmin=1, xmax=len(ratio_values))
# ax.plot(steps, ratio_values, 'o')
# ax.set_xlabel('k')
# ax.set_ylabel('P_ran(k)')
# ax.set_title('Rich club coeff ratio')
# ax.set_xscale('log')
# ax.set_yscale('log')
# # ax.set_ylim(0.0, max(2.0, max(ratio_values)))
# # ax.set_xlim([1, 10000])
# ax.yaxis.grid(True, which='major')

# plt.show()
