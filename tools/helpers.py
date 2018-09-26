import tools.valley_free_tools as vf_tools
from tools.valley_free_tools import VFT as vft
from tools.misc import deprecated
from operator import itemgetter
import igraph as i
import progressbar1
import subprocess
import logging
import string
import random
import json
import csv
import os
import io
import re

# META HEADER
(TRACE,  # Melyik tracre vonatkoznak az adatok
 TRACE_LEN,  # milyen hosszu a trace hop szamban
 SH_LEN,  # milyen hosszu a vegpontok kozotti legrovidebb ut hopp szamban
 SH_VF_LEN,  # A legrovidebb VF utvonal hossza a ket vegpont kozott
 IS_VF_PRELABELED,  # Adott trace prelabeled VF tulajdonsaggal rendelkezik-e
 HOP_STRETCH,  # Mekkora a nyulas hoppokban merve
 PERC_STRETCH,  # Mekkora a nyulas a SH pathoz kepest float ertekkent
 IN_VF_PRED,  # Sikerult-e josolni a vf predikcioval
 IS_VF_CLOSENESS,  # closeness metrikaval vf-e
 IS_VF_DEGREE,  #
 IS_LP_SOFT_PRELABELED,  # local preferenced first hopp metrika igaz-e
 IS_LP_HARD_PRELABELED,  # local preferenced all hopp metrika igaz-e
 IS_LP_SOFT_CLOSENESS,  # local preferenced first hopp metrika igaz-e
 IS_LP_HARD_CLOSENESS,  # local preferenced all hopp metrika igaz-e
 IS_LP_SOFT_DEGREE,  # local preferenced first hopp metrika igaz-e
 IS_LP_HARD_DEGREE,  # local preferenced all hopp metrika igaz-e
 ALL_PATH_COUNT,  # hany utvonal lehet a vegpontok kozott a stretchig
 SAME_LONG_PATH_COUNT,  # az elozo szambol mennyi volt azonos hosszu a traceszel
 SHORTER_PATH_COUNT,  # osszes lehetseges utbol mennyi volt rovidebb mint ez a trace
 ALL_PATH_VF_COUNT,  # hany vf utvonal van az ALL_PATH utak kozott
 SAME_LONG_PATH_VF_COUNT,  # az azonos hosszu osszes utbol mennyi vf
 SHORTER_PATH_VF_COUNT,  # a shortest all pathok kozul mennyi vf
 RANDOM_WALK_RUN_COUNT,  # hanyszor futtattuk le a random wealking algoritmust
 RANDOM_WALK_VF_CLOSENESS_ROUTE,  # hanyszor kaptunk a futasokbol VF utvonalat
 RANDOM_WALK_VF_DEGREE_ROUTE,
 RANDOM_WALK_VF_PRELABELED_ROUTE,
 RANDOM_NONVF_WALK_RUN_COUNT,
 RANDOM_NONVF_WALK_VF_CLOSENESS_ROUTE,
 RANDOM_NONVF_WALK_VF_CLOSENESS_ROUTE_LEN,  # a talalt utak hosszainak listaja
 RANDOM_NONVF_WALK_VF_DEGREE_ROUTE,
 RANDOM_NONVF_WALK_VF_DEGREE_ROUTE_LEN,  # a talalt utak hosszainak listaja
 RANDOM_NONVF_WALK_VF_PRELABELED_ROUTE,
 RANDOM_NONVF_WALK_VF_PRELABELED_ROUTE_LEN,  # a talalt utak hosszainak listaja
 RANDOM_NONVF_WALK_LP_SOFT_CLOSENESS_ROUTE,
 RANDOM_NONVF_WALK_LP_SOFT_DEGREE_ROUTE,
 RANDOM_NONVF_WALK_LP_SOFT_PRELABELED_ROUTE,
 RANDOM_NONVF_WALK_LP_HARD_CLOSENESS_ROUTE,
 RANDOM_NONVF_WALK_LP_HARD_DEGREE_ROUTE,
 RANDOM_NONVF_WALK_LP_HARD_PRELABELED_ROUTE,
 RANDOM_WALK_LP_SOFT_CLOSENESS_ROUTE,
 RANDOM_WALK_LP_SOFT_DEGREE_ROUTE,
 RANDOM_WALK_LP_SOFT_PRELABELED_ROUTE,
 RANDOM_WALK_LP_HARD_CLOSENESS_ROUTE,
 RANDOM_WALK_LP_HARD_DEGREE_ROUTE,
 RANDOM_WALK_LP_HARD_PRELABELED_ROUTE,
 RANDOM_GULYAS_WALK_ROUTES_STRETCH,
 RANDOM_GULYAS_WALK_ROUTES_VF_PRELABELED,
 RANDOM_GULYAS_WALK_ROUTES_VF_DEGREE,
 RANDOM_GULYAS_WALK_ROUTES_VF_CLOSENESS,
 RANDOM_GULYAS_WALK_ROUTES_LP_SOFT_PRELABELED,
 RANDOM_GULYAS_WALK_ROUTES_LP_HARD_PRELABELED,
 RANDOM_GULYAS_WALK_ROUTES_LP_SOFT_DEGREE,
 RANDOM_GULYAS_WALK_ROUTES_LP_HARD_DEGREE,
 RANDOM_GULYAS_WALK_ROUTES_LP_SOFT_CLOSENESS,
 RANDOM_GULYAS_WALK_ROUTES_LP_HARD_CLOSENESS,
 RANDOM_GULYAS_WALK_ROUTES_RQ_STRETCH
 ) = [str(x) for x in range(0, 56)]

LEVELS = [logging.ERROR,
          logging.WARNING,
          logging.INFO,
          logging.DEBUG]

logger = logging.getLogger('compnet.test.helpers')

def id_generator(size=6, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
    '''Creates a random ID in the given length using the given character set.
    With default settings creates a 6 character long alphanumeric string using
    uppercase characters'''
    return ''.join(random.choice(chars) for _ in range(size))


def import_csv_file_as_list(fpath, delimiter=','):
    '''Import the lines of a CSV file
    creating a new list element for all new line'''
    loaded = list()
    with io.open(fpath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            loaded.append(row)

    return loaded


def load_from_json(fpath):
    '''Just a wrapper to ease unicode json file loading'''
    # open for read with UTF-8 encoding
    with io.open(fpath, 'r', encoding='utf-8') as f:
        return json.loads(f.read())


def save_to_json_file(f, data):
    tmp = json.dumps(data, ensure_ascii=False, encoding='utf-8')
    f.write(unicode(tmp))


def save_to_json(fp, data, mode='w'):
    '''Just a wrapper to ease variable saving to a utf-8 coded file'''
    if callable(getattr(fp, "write", None)):
        save_to_json_file(fp, data)
    else:
        with io.open(fp, mode=mode, encoding='utf-8') as f:
            save_to_json_file(f, data)


def file_list(folder, pattern='.*'):
    """File listazas adott mappaban adott minta alapjan

    Kilistazza a parameterul kapott mappabol az osszes olyan filet, amely
    megfelel a parameterkent kapott mintanak.

    :param folder: Melyik mappaban kell a keresest vegezni
    :param pattern: Milyen mintara illeszkedo fileokat kell visszaadni
    :returns: egy lista, minden eleme egy filenev
    :rtype: list

    """
    return [f for f in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, f)) and
            re.match(pattern, f)]


def traceroutes_to_ranked_graph(traceroutes, directed=False):
    edges = []

    edges = [y for x in traceroutes for y in zip(x, x[1:])]
    edges = (dict(source=s, target=t) for s, t in edges)
    g = i.Graph.DictList(edges=edges, vertices=None, directed=directed)
    g.simplify(combine_edges="ignore")

    if directed:
        tmp = g.as_undirected()
        tmp.simplify()
    else:
        tmp = g.copy()

    for x in g.vs:
        x['rank'] = tmp.degree(x['name'])

    return g


def inferred_links_to_ranked_graph(inferred_links):
    """CAIDA labeling strukturabol graf cimkezese rangokkal

    A CAIDA labeling algoritmus altal generalt strukturanak megfelelo listabol
    keszit felcimkezett grafot. Az elek alapjan elkesziti az iranyitatlan grafot,
    amely minden nodejat olyan ranggal lat el, hogy
     * minden provider nagyobb ranggal rendelkezik mint a customerei
     * minden peer kapcsolattal osszekotott node azonos ranggal rendelkezik

    A kiszamolt rangokat a csomopont 'rank' attributumaban tarolja. A kapott graf
    nem iranyitott, nincsenek benne self loopok, nincsenek duplikalt elek. Ha
    a parameterben atadott listaban duplikalt elek szerepelnek, azokat eltavolitja.

    :param inferred_links: CAIDA labeling formatumu elek es cimkeik
    :returns: felcimkezett iranyitatlan graf
    :rtype: igraph.Graph

    """
    P, C, TYPE = (0, 1, 2)  # in CAIDA links are stored in P2C format

    def is_leaf(g, node):
        return g.degree(node, mode=i.IN) == 0

    def is_peer_relation(g, s, t):
        st = t in g.neighbors(s, mode=i.IN)
        ts = s in g.neighbors(t, mode=i.IN)
        return st and ts

    def check_for_possible_peer_clicks(g, s, visited=None):
        if visited is None: visited = []
        if s in visited: return visited
        visited.append(s)
        neighbors = g.neighbors(s, mode=i.IN)
        # Mark all neighbors with edges directed to s because in some
        # way, all of them will be discovered after this point
        g.vs[s]['marked'] = True
        for nodeid in neighbors:
            g.vs[nodeid]['marked'] = True

        if not neighbors: return []
        
        neighbor_is_peer = [is_peer_relation(g, s, neighbor) for neighbor in neighbors]
        if not all(neighbor_is_peer):
            # Why marking all neighbors befre was a good ide:
            # non of the neighbors need to check again because they are customers or peers and
            # - customer neighbors don't need to be checked from peer click searching methods
            # - peer neighbors has a neighbor (current node) which has at least one customer
            return []

        # check if all neighbors has only peer neighbors withoute customers
        unchecked_neighbors = [node for node in neighbors if node not in visited]
        reachable_peers = [check_for_possible_peer_clicks(g, neighbor, visited) for neighbor in unchecked_neighbors]

        # there was a peer with customers, so it returned with and empty list
        if not all(reachable_peers):
            return []                

        # neighbors.append(s)
        # return set(neighbors)
        return visited

    def get_peer_clicks(g):
        clicks = []
        for node in g.vs:
            if node['marked']: continue
            click = check_for_possible_peer_clicks(g, node.index)
            if not click: continue
            click_named = [g.vs[x]['name'] for x in click]
            clicks.append(click_named)

        for node in g.vs:
            node['marked'] = False
        return clicks

    edges = []

    for e in inferred_links:
        if e[C] == e[P]: continue  # self loop
        if e[TYPE] == vf_tools.LinkType.PEER.value:
            edges.append((e[P], e[C]))
            edges.append((e[C], e[P]))
        elif e[TYPE] == vf_tools.LinkType.C2P.value:
            edges.append((e[C], e[P]))

    edges = list(set(edges))
    edges = [dict(source=e[0], target=e[1]) for e in edges]

    inferred_net = i.Graph.DictList(edges=edges,
                                    vertices=None,
                                    directed=True)

    for x in inferred_net.vs:
        x['rank'] = 1

    tmp_net = i.Graph.DictList(edges=edges,
                                vertices=None,
                                directed=True)
    for x in tmp_net.vs:
        x['rank'] = 1
        x['marked'] = False

    leaves = [x['name'] for x in tmp_net.vs if is_leaf(tmp_net, x)]
    peer_clicks = get_peer_clicks(tmp_net)

    while len(leaves) > 0 or len(peer_clicks) > 0:
        for leaf in leaves:
            leaf_rank = tmp_net.vs.find(leaf)['rank']
            inferred_net.vs.find(leaf)['rank'] = leaf_rank
            neighbors = tmp_net.neighbors(leaf, mode=i.OUT)
            for n in neighbors:
                node = tmp_net.vs[n]
                node['rank'] = max(node['rank'], leaf_rank + 1)

                
        for peer_click in peer_clicks:
            max_rank = max([tmp_net.vs.find(x)['rank'] for x in peer_click])
            for peer_name in peer_click:
                node = tmp_net.vs.find(peer_name)
                node['rank'] = max_rank
                inferred_net.vs.find(peer_name)['rank'] = max_rank
                
                for neighbor in tmp_net.neighbors(node, mode=i.OUT):
                    neighbor_node = tmp_net.vs[neighbor]
                    neighbor_node['rank'] = max(neighbor_node['rank'], max_rank + 1)

        tmp_net.delete_vertices(leaves + [node for peer_click in peer_clicks for node in peer_click])
        leaves = [x['name'] for x in tmp_net.vs if is_leaf(tmp_net, x)]
        peer_clicks = get_peer_clicks(tmp_net)

    inferred_net.to_undirected()
    inferred_net.simplify()

    return inferred_net


@deprecated
def inferred_links_to_ranked_graph_old(inferred_links):
    """CAIDA labeling strukturabol graf cimkezese rangokkal

    A CAIDA labeling algoritmus altal generalt strukturanak megfelelo listabol
    keszit felcimkezett grafot. Az elek alapjan elkesziti az iranyitatlan grafot,
    amely minden nodejat olyan ranggal lat el, hogy
     * minden provider nagyobb ranggal rendelkezik mint a customerei
     * minden peer kapcsolattal osszekotott node azonos ranggal rendelkezik

    A kiszamolt rangokat a csomopont 'rank' attributumaban tarolja. A kapott graf
    nem iranyitott, nincsenek benne self loopok, nincsenek duplikalt elek. Ha
    a parameterben atadott listaban duplikalt elek szerepelnek, azokat eltavolitja.

    :param inferred_links: CAIDA labeling formatumu elek es cimkeik
    :returns: felcimkezett iranyitatlan graf
    :rtype: igraph.Graph

    """
    P, C, TYPE = (0, 1, 2)  # in CAIDA links are stored in P2C format

    def is_leaf(g, node):
        return g.degree(node, mode=i.IN) == 0

    def only_finished_peer_children(g, node):
        # print node
        children = list(g.bfsiter(node, mode=i.IN))
        if len(children) < 2: return False
        children = [x.index for x in children]
        for child in children:
            reachable = [x.index for x in g.bfsiter(child, mode=i.IN)]
            # print reachable
            if node not in reachable: return False

        return True

    edges = []

    for e in inferred_links:
        if e[C] == e[P]: continue  # self loop
        if e[TYPE] == vf_tools.LinkType.PEER.value:
            edges.append((e[P], e[C]))
            edges.append((e[C], e[P]))
        elif e[TYPE] == vf_tools.LinkType.C2P.value:
            edges.append((e[C], e[P]))

    edges = list(set(edges))
    edges = [dict(source=e[0], target=e[1]) for e in edges]

    inferred_net = i.Graph.DictList(edges=edges,
                                    vertices=None,
                                    directed=True)

    logger.debug('Empty inferred graph created')
    for x in inferred_net.vs:
        x['rank'] = 1

    tmp_net = i.Graph.DictList(edges=edges,
                                vertices=None,
                                directed=True)

    logger.debug('First leaves...')
    leaves = [x['name'] for x in tmp_net.vs if is_leaf(tmp_net, x)]
    logger.debug('First peers...')
    peers = []
    progressbar = progressbar1.AnimatedProgressBar(end=tmp_net.vcount(), width=15)
    for x in tmp_net.vs:
        progressbar += 1
        progressbar.show_progress()
        if only_finished_peer_children(tmp_net, x.index):
            peers.append(x['name'])
    # peers = [x['name'] for x in tmp_net.vs if only_finished_peer_children(tmp_net, x.index)]

    progress = progressbar1.AnimatedProgressBar(end=tmp_net.vcount(), width=15)

    while len(leaves) > 0 or len(peers) > 0:
        logger.debug('Leaves...')
        for leaf in leaves:
            leaf_rank = inferred_net.vs.find(name=leaf)['rank']
            neighbors = tmp_net.neighbors(leaf, mode=i.OUT)
            for n in neighbors:
                node_name = tmp_net.vs[n]['name']
                node = inferred_net.vs.find(name=node_name)
                node['rank'] = max(node['rank'], leaf_rank + 1)
                # inferred_net.vs.find(name=node_name)['rank'] += leaf_rank
                # print 'Increment %s rank from %s to %s because of %s(%s)' % (node_name, before_rank, inferred_net.vs.find(name=node_name)['rank'], leaf, leaf_rank)

        # print 'PEERS: %s' % peers
        logger.debug('Peers...')
        for peer in peers:
            peer_chain = list(tmp_net.bfsiter(tmp_net.vs.find(name=peer), mode=i.IN))
            parents = [tmp_net.neighbors(x, mode=i.OUT) for x in peer_chain]
            parents = [tmp_net.vs[x]['name'] for y in parents for x in y]
            peer_chain = [x['name'] for x in peer_chain]
            # print 'peer chain: %s ' % peer_chain
            max_rank = max([inferred_net.vs.find(name=x)['rank'] for x in peer_chain])
            # print 'max rank: %s' % max_rank

            for x in parents:
                inferred_net.vs.find(name=x)['rank'] += max_rank
                # print 'increment rank %s to %s with %s' % (x, inferred_net.vs.find(name=x)['rank'], max_rank)

            for x in peer_chain:
                inferred_net.vs.find(name=x)['rank'] = max_rank
                # print 'New rank for %s is %s' % (x, inferred_net.vs.find(name=x)['rank'])
                if x == peer: continue
                # print 'remove: %s' % x
                peers.remove(x)

        tmp_net.delete_vertices(leaves + peers)
        progress += len(leaves) + len(peers)
        progress.show_progress()

        leaves = [x['name'] for x in tmp_net.vs if is_leaf(tmp_net, x)]
        peers = [x['name'] for x in tmp_net.vs if only_finished_peer_children(tmp_net, x.index)]

    inferred_net.to_undirected()
    inferred_net.simplify()

    return inferred_net


@deprecated
def load_as_inferred_links_nofile(vs, edges):
    g = i.Graph(directed=True)
    g.add_vertices(vs)

    edge_type = list()
    t_edge = list()
    for e in edges:
        ltype = vf_tools.LinkType(e[2])
        s, t = e[1], e[0]  # in CAIDA links are stored in P2C format
        t_edge.append((s, t))
        edge_type.append(ltype)

    g.add_edges(t_edge)
    g.es[vf_tools.VFT.TYPE] = edge_type

    return g


@deprecated
def load_as_inferred_links(path, graph=True):
    vertices = list()
    edges = list()
    with open(path, 'r') as f:
        reader = csv.reader(f, delimiter='|')
        for row in reader:
            if row[0].startswith('#'): continue
            if row[0] == row[1]: continue
            vertices.append('%s' % row[0])
            vertices.append('%s' % row[1])
            edges.append(['%s' % row[0], '%s' % row[1], int(row[2])])

    vs = list(set(vertices))

    if graph:
        return load_as_inferred_links_nofile(vs, edges)
    else:
        return vs, edges


@deprecated
def degree_labeling_traceroutes(traceroutes, peer_treshold=1.0, vfmode=None):
    edges = set([e for x in traceroutes for e in zip(x, x[1:])])  # | set([e for x in traceroutes for e in zip(x, x[2:])])
    nodes = set([n for x in traceroutes for n in x])
    g = i.Graph()
    g.add_vertices(list(nodes))
    g.add_edges(edges)
    g.simplify(combine_edges="ignore")

    return degree_labeling_network(g, peer_treshold, vfmode)


@deprecated
def degree_labeling_network(network, peer_treshold=1.0, vfmode=None):
    if vfmode is None: vfmode = vft.PRELABELED

    if vfmode == vft.PRELABELED:
        max_degree = network.maxdegree()
        rank = network.degree
    elif vfmode == vft.CLOSENESS:
        max_degree = float('inf')
        rank = network.closeness
    else:
        raise RuntimeError('Unhandled mode')

    degree_lb = max_degree * peer_treshold   # degree lower bound
    labeled_edges = list()
    for e in network.es:
        s, t = e.source, e.target
        name_s, name_t = [network.vs[x]['name'] for x in [s, t]]
        rank_s, rank_t = [rank(x) for x in [s, t]]

        # peer edge
        if ((rank_s >= degree_lb and rank_t >= degree_lb)   # top nodes
            or (rank_s == rank_t)):                               # same rank
            labeled_edges.append([name_s, name_t, vf_tools.LinkType.PEER.value])

        # C2P edge
        elif rank_s > rank_t:
            labeled_edges.append([name_s, name_t, vf_tools.LinkType.C2P.value])
        elif rank_s < rank_t:
            labeled_edges.append([name_t, name_s, vf_tools.LinkType.C2P.value])
    return labeled_edges


def caida_labeling(caida_folder, traceroutes, clique_file=None):
    if clique_file is not None:
        with open(clique_file, 'r') as f:
            first_line = f.readline().strip()
            cliques = first_line.split(' ')[3:]

    cwd = os.getcwd()
    os.chdir(caida_folder)
    traceroutes = sorted(traceroutes)
    # create an id for all nodes
    nodes = sorted(list(set([node for traceroute in traceroutes for node in traceroute])))
    ids = range(0, len(nodes))
    node_to_id = dict(zip(nodes, ids))
    id_to_node = dict(zip(ids, nodes))
    
    #convert traceroutes with node names to traceroutes with node ids
    mapped_traceroutes = [tuple([node_to_id[node] for node in traceroute]) for traceroute in traceroutes]

    #convert clique names to node ids
    if clique_file: cliques = [str(node_to_id[node]) for node in cliques]

    #save mapped traceroutes to a temporary file in a caida labeling compatible format
    tmp_mapped_trace_file = id_generator(size=8)
    with open(tmp_mapped_trace_file, 'w') as f:
        for traceroute in mapped_traceroutes:
            trace_str = [str(x) for x in traceroute]
            f.write('%s\n' % ('|'.join(trace_str), ))            
    
    caida_parameters = ['perl', 'asrank.pl']
    if clique_file is not None: caida_parameters.extend(['--clique', '%s' % " ".join(cliques)])
    caida_parameters.append(tmp_mapped_trace_file)
    caida_parameters.append('rels')
    print 'Call %s' % (' '.join(caida_parameters), )
    labeled_edges_str = subprocess.check_output(caida_parameters)
    labeled_edges = [edge_str.strip().split('|') for edge_str in labeled_edges_str.strip().split('\n') if not edge_str.strip().startswith('#')]
    # convert traceroute id's to id names
    labeled_edges = [[id_to_node[int(e[0])], id_to_node[int(e[1])], e[2]] for e in labeled_edges]
    labeled_edges = sorted(labeled_edges, key=lambda x: ''.join(x))

    # remove temporary file
    os.remove(tmp_mapped_trace_file)

    # change back to working directory
    os.chdir(cwd)
    return labeled_edges


def dfs_mark(gi, s, t, max_node_count, distance_map=None, debug=False):
    """Deep first search in given graph

    This function tries to save partial results to speed up current search
    or next tries.

    :param gi: original labeled graph
    :param s: source node
    :param t: target node
    :param max_node_count: how much node enabled in returned paths
    :returns: all possible traces from #s to #t
    :rtype: @list

    """
    # if gi.vs[s]['name'] == 'AS1213':  # 'AS3257':
    #     debug = True
    # else:

    if debug: print 'From %s->%s at %d' % (s, t, max_node_count)
    if max_node_count <= 0: return None # BUG if true??

    if s == t:
        return [(s, ), ]

    try:
        gi.vs[s]
        gi.vs[t]
    except IndexError:
        return []

    if max_node_count == 1: return None  # s already a hop, so 0 step remained

    # if distance_map is None and max_node_count > 3:
    #     distance_map = [x[0] + 1 for x in gi.shortest_paths(target=t)]

    discovered = gi.vs[s]['traces']
    keys = sorted(discovered.iterkeys())
    if debug: print 'Already discovered keys: %s' % keys
    if len(keys) > 0 and max(keys) >= max_node_count:  # discovered to t
        if debug: print 'Discovered t %s-%s' % (s, t)
        paths = [y for x in range(0, max_node_count + 1)
                 if discovered[x] is not None
                 for y in discovered[x]]
        if debug: print 'Returned path: %s' % paths
        return paths

    paths = list()
    neighbors = [x for x in gi.neighbors(s, mode=i.OUT)]
    # < mert a mostani node is beleszamolodik a max_node_count-ba, igy
    # a szomszedtol 1 lepessel kevesebbol kell eljutni a celig
    if distance_map is not None:
        neighbors = [x for x in neighbors if distance_map[x] < max_node_count]
    if debug: print neighbors
    for next_hop in neighbors:

        routes = dfs_mark(gi,
                          next_hop, t,
                          max_node_count - 1,
                          distance_map,
                          debug)
        # if next_hop == 15269:
            # print 'Check %s->%s through' % (s, t)
            # raw_input()
        if routes is not None:
            routes = [(s, ) + x for x in routes if s not in x]
            if debug: print 'New routes from %s-%s' % (next_hop, t)
            if debug: print '\t', routes
            paths.extend(routes)

    paths = list(set(paths))

    for path in paths:
        k = len(path)
        if k not in discovered or discovered[k] is None:
            discovered[k] = list()

        if discovered[k] is not None and path not in discovered[k]:
            if debug: print '%s not in %s' % (path, discovered[k])
            # if debug and k == 3: raw_input()
            discovered[k].append(path)

    for k in range(0, max_node_count + 1):
        if k not in discovered:
            discovered[k] = None

    if debug: print 'Return path: %s' % paths
    return paths


def dfs_simple(gi, s, t, max_node_count, path_string):
    """Deep first search in given graph

    :param gi: original labeled graph
    :param s: source node
    :param t: target node
    :param max_node_count: how much node enabled in #path_string
    :param path_string: route to given #s
    :returns: all possible traces from #s to #t
    :rtype: @list

    """
    if max_node_count <= 0: return  # BUG if true??

    if s == t:
        return [(s, ), ]

    if max_node_count == 1: return  # s already a hop, so no step remained

    paths = list()
    neighbors = [x for x in gi.neighbors(s, mode=i.OUT)
                 if x not in path_string]
    for next_hop in neighbors:
        routes = dfs_simple(gi,
                            next_hop, t,
                            max_node_count - 1, path_string + (s, ))
        if routes is not None:
            routes = [(s, ) + x for x in routes if s not in x]
            paths.extend(routes)

    return paths


def load_network(network_path):
    try:
        return i.load(network_path)
    except IOError:
        return load_as_inferred_links(network_path)


def random_route_walk(g, s, t, limit, named=False, weight_field=None):
    try:
        s = vft.node_to_nodeid(g, s)
        t = vft.node_to_nodeid(g, t)

        # check if s and t are valid inidecies
        _, _ = g.vs[s], g.vs[t]
    except (ValueError, IndexError):
        raise IndexError('Vertex index out of range or not exists')

    # some special case
    if limit <= 0:
        # print 'HOP COUNT: %d' % hop_count
        return []
    if s == t: return [s, ]
    # # if s != t then length must be larger than 1
    # # but only in hop count mode
    if weight_field is None and limit == 1:
        # print 'S: %s, T: %s, HC: %d' % (s, t, hop_count)
        return []

    shortest_route = g.shortest_paths(s, t, weights=weight_field, mode=i.OUT)
    shortest_route = shortest_route[0][0]

    logger.debug('Shortes: %f, Limit: %f' % (shortest_route, limit))

    if weight_field is None:
        # in hop count mode convert hop count to node count
        shortest_route += 1

    if limit < shortest_route:
        # print 'TOO SHORT %d' % (hop_count)
        return []

    def edge_weight(s, t):
        eid = g.get_eid(s, t)
        if weight_field is None:
            # +1 ha nincs suly, mert az igraph azt mondja meg,
            # s-bol hany hopp t
            w = 1
        else:
            w = g.es[eid][weight_field]
        return w

    path = [s, ]
    weights = [0, ]
    visited_node_list = [[], ]
    actual_node = s

    # In hop count mode decrement, becase s already added to the path
    if weight_field is None: limit -= 1

    while limit > 0 and actual_node != t:
        logger.debug('Limit remained: %d' % limit)
        logger.debug('Current node: %s' % actual_node)
        visited_nodes = visited_node_list[-1]
        last_weight = weights[-1]
        logger.debug('Visited nodes: %s' % visited_nodes)
        neighbors = [x for x in g.neighbors(actual_node, mode=i.OUT)
                     if x not in visited_nodes and x not in path]

        neighbor_distances = [edge_weight(actual_node, x) for x in neighbors]
        next_hop_distances = [x[0] for x in g.shortest_paths(neighbors, t,
                                                             weights=weight_field,
                                                             mode=i.OUT)]
        distances = [x[0] + x[1] for x in zip(neighbor_distances,
                                              next_hop_distances)]

        candidates = filter(lambda x: x[1] <= limit,
                            zip(neighbors, distances))

        if len(candidates) == 0:
            limit += last_weight
            path.pop()
            visited_node_list.pop()
            weights.pop()
            actual_node = path[-1]
            continue

        logger.debug('Valid candidates: %s' % candidates)

        next_hop = random.choice(candidates)[0]
        logger.debug('Chosen one: %s' % next_hop)
        visited_nodes.append(next_hop)
        path.append(next_hop)
        visited_node_list.append([])
        last_weight = edge_weight(actual_node, next_hop)
        weights.append(last_weight)

        limit -= last_weight
        actual_node = next_hop

    if named:
        path = [g.vs[x]['name'] for x in path]

    logger.debug('random path between {s} and {t}: {p}'.format(s=s,
                                                               t=t,
                                                               p=path))
    return path


def random_nonvf_route(g, s, t, hop_count,
                       path=None, vfmode=None):
    if path is None:
        try:
            if isinstance(s, str):
                s = g.vs.find(s).index
            if isinstance(t, str):
                t = g.vs.find(t).index

            # check if s and t are valid inidecies
            _, _ = g.vs[s], g.vs[t]
        except (ValueError, IndexError):
            raise IndexError('Vertex index out of range or not exists')

        # some special case
        if hop_count < 1:
            # print 'HOP COUNT: %d' % hop_count
            return (False, [])

        if s == t: return (True, [s, ])
        # if s != t then length must be larger than 1
        if hop_count == 1:
            # print 'S: %s, T: %s, HC: %d' % (s, t, hop_count)
            return (False, [])

        shortest_route = g.shortest_paths(s, t, mode=i.OUT)[0][0] + 1
        if hop_count < shortest_route:
            # print 'TOO SHORT %d' % (hop_count)
            return (False, [])

        path = [s, ]
        hop_count -= 1
        if vfmode is None: vfmode = vft.CLOSENESS

    if s == t:
        return (vft.is_valley_free(g, path, vfmode=vfmode), path)

    logger.debug('Hop count remained: %d' % hop_count)
    logger.debug('Current node: %s' % s)
    neighbors = [x for x in g.neighbors(s, mode=i.OUT) if x not in path]
    distances = [x[0] for x in g.shortest_paths(neighbors, t, mode=i.OUT)]
    candidates = filter(lambda x: x[1] + 1 <= hop_count,  # +, mert az igraph
                                                          # azt mondja meg,
                                                          # s-bol hany hopp t
                        zip(neighbors, distances))

    weights = [-1 if not vft.is_valley_free(g, path + [x[0], ], vfmode=vfmode)
               else vft.edge_dir(g, [s, x[0]], vfmode=vfmode).value
               for x in candidates]
    # create a list where every columnt is neighbors, distances, weights
    # respectevly
    candidates = zip(*(zip(*candidates) + [weights, ]))
    # sort by weights
    candidates = sorted(candidates, key=itemgetter(2))

    if len(candidates) == 0:
        return (False, [])

    logger.debug('Valid candidates: %s' % candidates)
    first_route = (False, [])  # by default there was no route to T
    for next_hop in candidates:
        logger.debug('Chosen one: %s' % next_hop[0])
        isvf, r = random_nonvf_route(g, next_hop[0], t,
                                     hop_count - 1,
                                     path + [next_hop[0], ], vfmode)
        if len(r) == 0: continue
        if not isvf:
            # we are done, we found a nonVF route
            return (isvf, r)
        # our first guess a vf route. save it for later use (e.g. there is no
        # nonVF rotue) but lets try again with another candidate
        if len(first_route[1]) == 0:  # first save
            first_route = (isvf, r)

    return first_route

    # logger.debug('random path between {s} and {t}: {p}'.format(s=s,
    #                                                            t=t,
    #                                                            p=path))
    # return path

# for edge in ranked_g.es:
#     s, t = edge.source, edge.target
#     name_s, name_t = ranked_g.vs[s]['name'], ranked_g.vs[t]['name']
#     tp = vf_tools.LinkType.C2P
#     if ranked_g.vs[s]['rank'] == ranked_g.vs[t]['rank']:
#         tp = vf_tools.LinkType.PEER
#     elif ranked_g.vs[s]['rank'] > ranked_g.vs[t]['rank']:
#         s, t = t, s
#         name_s, name_t = name_t, name_s

#     inferred_e = inferred_g.get_eid(name_s, name_t, directed=False)
#     ty = inferred_g.es[inferred_e][vf_tools.VFT.TYPE]
#     if ty != tp:
#         print 'AJAJ'
#         print s, t
#         print name_s, name_t
#         print tp
#         print ty
