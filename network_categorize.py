import igraph as i
import argparse
from tools import helpers
import random
import copy
import tools.progressbar1 as progressbar1
from tools.valley_free_tools import VFT as vft
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


NODE_PAIRS = 500


def random_pairs(vs, pair_count=NODE_PAIRS, max_trie=1000):
    tried = 0
    pairs = []
    while len(pairs) < pair_count and tried < max_trie:
        random.shuffle(vs)
        random_nodes = zip(vs[::2], vs[1::2])
        random_nodes = [tuple(sorted(x)) for x in random_nodes]
        pairs.extend(random_nodes)
        pairs = list(set(pairs))
        tried += 1
    if len(pairs) > pair_count: pairs = pairs[:pair_count]

    return pairs


def label_igraph_network(network_path):
    g = i.load(network_path)
    g = g.as_undirected()
    print 'Get giant component'
    g = g.clusters(mode='weak').giant()
    simple = g.is_simple()
    print 'IS SIMPLE? %s' % simple
    if not simple:
        g.simplify(multiple=True, loops=True, combine_edges='ignore')

    try:
        for vs in g.vs:
            vs['name'] = 'LBL%s' % vs['name']
    except KeyError:
        for vs in g.vs:
            vs['name'] = 'LBL%s' % vs.index

    edge_list = helpers.degree_labeling_network(g, 1.1)

    vs = list(set([y for t in [(x[0], x[1]) for x in edge_list] for y in t]))
    labeled_g = helpers.load_as_inferred_links_nofile(vs, edge_list)

    return labeled_g


def main():
    parser = argparse.ArgumentParser(description='Load networks in gml format, and check short path vf pref', formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('network')
    parser.add_argument('out')
    parser.add_argument('--source', default='igraph',
                        choices = ['converted', 'igraph'])

    parser.add_argument('--extra-hop', dest='extra_hop',
                         default=0, type=int);

    arguments = parser.parse_args()

    out = arguments.out
    network_path = arguments.network
    src = arguments.source
    extra_hop = arguments.extra_hop

    if src == 'converted':
        labeled_g = helpers.load_as_inferred_links(network_path)
    elif src == 'igraph':
        labeled_g = label_igraph_network(network_path)
    else:
        raise RuntimeError('Unknown source type')

    # graphs(labeled_g, out, network_path)

    purify(labeled_g, out, network_path, extra_hop)


def rich_club_coeff(g, k, degrees=None, edge_helper=None):
    if degrees is None:
        degrees = g.degrees(mode=i.ALL, loops=False)

    if edge_helper is None:
        edge_helper = [min(g.degree(x.source), g.degree(x.target))
                       for x in g.es]

    e_k = [x for x in edge_helper if x >= k]
    n_k = float(len([x for x in degrees if x >= k]))

    e_k2 = float(2 * len(e_k))

    fi_k = e_k2 / (n_k * (n_k - 1))
    return fi_k


def graphs(g, out, network_path):
    # g = g.Erdos_Renyi(n=g.vcount(), m=g.ecount(), directed=False, loops=False)
    # i.plot(g)
    degrees = g.degree()

    print 'Generate random graph'
    max_random_graph = g.Degree_Sequence(g.degree(mode=i.ALL, loops=False), method='vl')
    rand_degrees = max_random_graph.degree(mode=i.ALL, loops=False)

    fi_values = []
    ratio_values = []

    print 'Calculate coeff'
    edge_helper = [min(g.degree(x.source), g.degree(x.target)) for x in g.es]
    rand_edge_helper = [min(max_random_graph.degree(x.source),
                            max_random_graph.degree(x.target))
                        for x in max_random_graph.es]
    progress = progressbar1.AnimatedProgressBar(end=max(degrees), width=15)
    for k in range(1, max(degrees) + 1):
        progress += 1
        progress.show_progress()
        try:
            fi = rich_club_coeff(g, k, degrees=degrees,
                                 edge_helper=edge_helper)
            fi_ran = rich_club_coeff(max_random_graph, k, degrees=rand_degrees,
                                     edge_helper=rand_edge_helper)

            ratio = fi / float(fi_ran)
        except ZeroDivisionError:
            fi_values.append(0)
            ratio_values.append(0)
            continue

        fi_values.append(fi)
        ratio_values.append(ratio)

    fig, ax = plt.subplots()
    ax.axhline(y=1, xmin=1, xmax=len(ratio_values))
    ax.plot(range(1, len(fi_values)+1), fi_values, 'o')
    ax.set_xlabel('k')
    ax.set_ylabel('fi(k)')
    ax.set_title('Rich club coeff ratio')
    ax.set_yscale('log')
    ax.set_xscale('log')
    # ax.set_ylim(0.0, 2.0)
    # ax.set_xlim([1, 10000])
    ax.yaxis.grid(True, which='major')

    # plt.gca().invert_yaxis()
    fname = '%s_rich_club_simple_coeff.pdf' % out
    print fname
    pdf_file = PdfPages(fname)
    plt.savefig(pdf_file, format='pdf')
    pdf_file.close()
    plt.show()

    
    # i.plot(g.degree_distribution(), log="xy")
    fig, ax = plt.subplots()
    ax.axhline(y=1, xmin=1, xmax=len(ratio_values))
    ax.plot(range(1, len(ratio_values)+1), ratio_values, 'o')
    ax.set_xlabel('k')
    ax.set_ylabel('P_ran(k)')
    ax.set_title('Rich club coeff ratio')
    ax.set_xscale('log')
    ax.set_ylim(0.0, max(2.0, max(ratio_values)))
    # ax.set_xlim([1, 10000])
    ax.yaxis.grid(True, which='major')

    fname = '%s_rich_club_ratio_coeff.pdf' % out
    print fname
    pdf_file = PdfPages(fname)
    plt.savefig(pdf_file, format='pdf')
    pdf_file.close()
    plt.show()

#    plt.show()


def purify(labeled_g, out, network_path, extra_hop=0):
    vs = [x.index for x in labeled_g.vs]

    ## Jus like in R

    # print '================'
    # for x in orig_vs:
    #     shp = labeled_g.get_all_shortest_paths(x, orig_vs, mode=i.ALL)
    #     res = []
    #     mes = 0
    #     for p in shp:
    #         mes += 1
    #         # print [labeled_g.vs[u]['name'] for u in p]
    #         vf_indicator = 1 if vft.is_valley_free(labeled_g, p) else 0
    #         # if vf_indicator == 0:
    #             # print [labeled_g.vs[u]['name'] for u in [p[0], p[-1]]]
    #             # print [labeled_g.degree(u) for u in p]
    #             # print vft.trace_to_string(labeled_g, p)
    #         # print vf_indicator == 1
    #         res.append(vf_indicator)
    #         # raw_input()
    #     # print mes
    #     print np.mean(res)

    # raw_input()

    # print '///////////////////////////'
    pairs = random_pairs(vs, NODE_PAIRS)
    print 'Random pairs: %d' % len(pairs)

    probed_pairs = 0

    all_vf = 0
    all_nonvf = 0
    all_vf_closeness = 0
    all_nonvf_closeness = 0
    results = []
    results2 = []
    results3 = []

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

    results_closeness = []
    results3_closeness = []
    progress = progressbar1.AnimatedProgressBar(end=len(pairs), width=15)
    for s, t in pairs:
        progress += 1
        progress.show_progress()
        for x in range(0, labeled_g.vcount()):
            labeled_g.vs[x]['traces'] = dict()

        # all_path = labeled_g.get_all_shortest_paths(s, t, mode=i.ALL)
        sh_len = labeled_g.shortest_paths(s, t, mode=i.ALL)[0][0]
        sh_len += 1  # convert to hop count
        all_path = helpers.dfs_mark(copy.deepcopy(labeled_g), s, t, sh_len + extra_hop)
        if all_path is None or len(all_path) < 1:
            print 'No path between %s %s' % (s, t)
            continue
        probed_pairs += 1
        vf_indicator = [1 if vft.is_valley_free(labeled_g, x) else 0
                        for x in all_path]
        vf_closeness_indicator = [1 if vft.is_valley_free(labeled_g, x, vfmode=vft.ORDER_CLOSENESS) else 0
                                  for x in all_path]
        vf_count = sum(vf_indicator)
        vf_closeness_count = sum(vf_closeness_indicator)
        nonvf = len(all_path) - vf_count
        nonvf_closeness = len(all_path) - vf_closeness_count

        all_vf += vf_count
        all_nonvf += nonvf

        all_vf_closeness += vf_closeness_count
        all_nonvf_closeness += nonvf_closeness

        long_path = [x for x in all_path if len(x) == sh_len + extra_hop]
        short_path = [x for x in all_path if len(x) < sh_len + extra_hop]

        tmp = [1 if vft.is_valley_free(labeled_g, x, vfmode=vft.ORDER_PRELABELED) else 0 for x in all_path if len(x) < sh_len+extra_hop]
        short_vf_count = sum(tmp)
        short_nonvf = len(tmp) - short_vf_count

        tmp = [1 if vft.is_valley_free(labeled_g, x, vfmode=vft.ORDER_CLOSENESS) else 0 for x in all_path if len(x) < sh_len+extra_hop]
        short_vf_closeness_count = sum(tmp)
        short_nonvf_closeness = len(tmp) - short_vf_closeness_count

        tmp = [1 if vft.is_valley_free(labeled_g, x, vfmode=vft.ORDER_PRELABELED) else 0 for x in all_path if len(x) >= sh_len+extra_hop]
        long_vf_count = sum(tmp)
        long_nonvf = len(tmp) - long_vf_count

        tmp = [1 if vft.is_valley_free(labeled_g, x, vfmode=vft.ORDER_CLOSENESS) else 0 for x in all_path if len(x) >= sh_len+extra_hop]
        long_vf_closeness_count = sum(tmp)
        long_nonvf_closeness = len(tmp) - long_vf_closeness_count

        if len(all_path) > 0:
            results.append(vf_count / float(len(all_path)))
            results_closeness.append(vf_closeness_count / float(len(all_path)))
        else:
            results.append(0)
            results_closeness.append(0)

        results3.append([vf_count, nonvf])
        results3_closeness.append([vf_closeness_count, nonvf_closeness])

        if len(all_path) > 1: results2.append(vf_count / float(len(all_path)))

        all_long_vf += long_vf_count
        all_long_nonvf += long_nonvf

        all_long_vf_closeness += long_vf_closeness_count
        all_long_nonvf_closeness += long_nonvf_closeness

        all_short_vf += short_vf_count
        all_short_nonvf += short_nonvf

        all_short_vf_closeness += short_vf_closeness_count
        all_short_nonvf_closeness += short_nonvf_closeness

        if len(long_path) > 0:
            long_results.append(long_vf_count / float(len(long_path)))
            long_results3.append(long_vf_closeness_count / float(len(long_path)))
        else:
            long_results.append(0)
            long_results3.append(0)

        if len(long_path) > 1: long_results2.append(long_vf_count / float(len(long_path)))

        if len(short_path) > 0:
            short_results.append(short_vf_count / float(len(short_path)))
            short_results3.append(short_vf_closeness_count / float(len(short_path)))
        else:
            short_results.append(0)
            short_results3.append(0)


    print

    with open(out, 'w') as f:
        f.write('%s\n' % network_path)
        f.write('Probed pairs: %d\n' % probed_pairs)
        f.write('VF count: %d\n' % all_vf)
        f.write('Non vf count: %d\n' % all_nonvf)
        f.write('VF perc: %f\n' % (all_vf / float(all_vf + all_nonvf)))
        f.write('Mean VF prob: %f\n' % np.mean(results))
        f.write('Mean VF2 prob: %f\n' % np.mean(results2))

        f.write('\n')
        f.write('VF CLOSENESS count: %d\n' % all_vf_closeness)
        f.write('Non vf CLOSENESS count: %d\n' % all_nonvf_closeness)
        f.write('VF CLOSENESS perc: %f\n' % (all_vf_closeness / float(all_vf_closeness + all_nonvf_closeness)))
        f.write('Mean VF CLOSENESS prob: %f\n' % np.mean(results_closeness))

        f.write('\n')
        f.write('==========\n')
        f.write('VF count: %d\n' % all_short_vf)
        f.write('VF  CLOSENESS count: %d\n' % all_short_vf_closeness)
        f.write('Non vf count: %d\n' % all_short_nonvf)
        f.write('Non vf CLOSENESS count: %d\n' % all_short_nonvf_closeness)
        if all_short_vf + all_short_nonvf > 0:
            f.write('VF perc: %f\n' % (all_short_vf / float(all_short_vf + all_short_nonvf)))
        if all_short_vf_closeness + all_short_nonvf_closeness > 0:
            f.write('VF CLOSENESS perc: %f\n' % (all_short_vf_closeness / float(all_short_vf_closeness + all_short_nonvf_closeness)))
        f.write('Mean VF prob: %f\n' % np.mean(short_results))
        f.write('Mean VF CLOSENESS prob: %f\n' % np.mean(short_results3))
        f.write('Mean VF2 prob: %f\n' % np.mean(short_results2))
        f.write('=-----------------\n')
        f.write('VF count: %d\n' % all_long_vf)
        f.write('VF CLOSENESS count: %d\n' % all_long_vf_closeness)
        f.write('Non vf count: %d\n' % all_long_nonvf)
        f.write('Non vf CLOSENESS count: %d\n' % all_long_nonvf_closeness)
        f.write('VF perc: %f\n' % (all_long_vf / float(all_long_vf + all_long_nonvf)))
        f.write('VF CLOSENESS perc: %f\n' % (all_long_vf_closeness / float(all_long_vf_closeness + all_long_nonvf_closeness)))
        f.write('Mean VF prob: %f\n' % np.mean(long_results))
        f.write('Mean VF CLOSENESS prob: %f\n' % np.mean(long_results3))
        f.write('Mean VF2 prob: %f\n' % np.mean(long_results2))


if __name__ == '__main__':
    main()
