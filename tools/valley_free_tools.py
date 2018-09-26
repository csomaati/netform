import re
import misc
import copy
import logging
import itertools
import igraph
from enum import Enum

misc.logger_setup()
logger = logging.getLogger('compnet.valley_free_tools')


class LinkDir(Enum):
    D = 0
    P = 1
    U = 2


class LinkType(Enum):
    C2P = -1
    PEER = 0


class VFT(object):

    # A route is valley free if it contains
    # 0 or more UP edges,
    # 0 or 1 Peer edge and
    # 0 or more Down edges. This is a strict sequence
    re_valley_free = re.compile('^U*P{0,1}D*$')
    TYPE = 'ltype'

    PRELABELED = 0
    CLOSENESS = 1
    DEGREE = 2

    @classmethod
    def rank_closeness(cls, graph, node):
        node = cls.node_to_nodeid(graph, node)
        try:
            closeness = graph.vs[node]['closeness']
            if closeness is None: raise KeyError
            return closeness
        except KeyError:
            logger.debug('Calculate closeness for %s' % node)
            closeness = graph.closeness(node, mode=igrap.OUT)
            graph.vs[node]['closeness'] = closeness
            return closeness

    @classmethod
    def rank_prelabeled(cls, graph, node):
        node = cls.node_to_nodeid(graph, node)
        return graph.vs[node]['closeness']

    @classmethod
    def rank_degree(cls, graph, node):
        node = cls.node_to_nodeid(graph, node)
        return graph.degree(node, mode=igraph.OUT)

    @classmethod
    def graph_dir_check(cls, g):
        if g.is_directed():
            logger.warn('VF graph creation based on directed graph is in test phase')

    @classmethod
    def node_to_nodeid(cls, graph, node):
        if isinstance(node, int):
            n = node
        elif isinstance(node, basestring) or isinstance(node, unicode):
            n = graph.vs.find(node).index
        elif isinstance(node, igraph.Vertex):
            n = node.index
        else:
            raise RuntimeError('Can not convert %s types to node id' % type(node))
        
        return n

    @classmethod
    def edge_dir(cls, graph, edge, vfmode=None):
        if vfmode is None:
            vfmode = cls.PRELABELED

        rank = cls.EDGE_DIR_METHOD[vfmode]

        if isinstance(edge, igraph.Edge):
            raise AttributeError("igraph's edge type is not supported")
            logger.warn(('Be cautios. Use edge.source and edge.target ',
                         'to check the correct order, if you used ',
                         'Graph.get_eid. It can change them if the link ',
                         'is directed'))
            edge = [edge.source, edge.target]

        s = cls.node_to_nodeid(graph, edge[0])
        t = cls.node_to_nodeid(graph, edge[1])

        eid = graph.get_eid(s, t, directed=True, error=False)
        if eid == -1:
            raise RuntimeError('No edge between %s[%s] and %s[%s]' % (s, graph.vs[s]['name'], t, graph.vs[t]['name']))

        s_rank = rank(graph, s)
        t_rank = rank(graph, t)

        # logger.debug('Original: %s->%s, by eid: %s->%s' % (s, t,
        #                                                   graph.es[eid].source,
        #                                                   graph.es[eid].target))

        # logmsg = 'rank({s}): {rs}, rank({t}): {rt}'
        # logger.debug(logmsg.format(s=s, t=t, rs=s_rank, rt=t_rank))

        if s_rank == t_rank: return LinkDir.P
        if s_rank < t_rank: return LinkDir.U
        if s_rank > t_rank: return LinkDir.D

        raise RuntimeError('Unhandled link direction')

    @classmethod
    def node_rank(cls, g, node, vfmode=None):
        if vfmode is None:
            vfmode = cls.PRELABELED

        rank = cls.EDGE_DIR_METHOD[vfmode]
        r = rank(g, node)
        return r

    @classmethod
    def edgelist_to_string(cls, graph, edge_list, vfmode=None):
        edge_string = [VFT.edge_dir(graph, e, vfmode).name for e in edge_list]
        return ''.join(edge_string)

    @classmethod
    def trace_to_string(cls, graph, trace, vfmode=None):
        elist = zip(trace, trace[1:])
        return VFT.edgelist_to_string(graph, elist, vfmode)

    @classmethod
    def is_valley_free(cls, graph, trace, vfmode=None):
        route_string = VFT.trace_to_string(graph, trace, vfmode)
        if len(route_string) < 1:
            raise ValueError('At least one edge required')
        is_vf = VFT.re_valley_free.match(route_string)
        if is_vf: return True
        else: return False

    @classmethod
    def trace_exists(cls, g, t):
        t = [cls.node_to_nodeid(g, x) for x in t]
        edges = zip(t, t[1:])
        connected = [g.are_connected(x[0], x[1]) for x in edges]
        if all(connected): return True
        else: return False

    @classmethod
    def route_exists(cls, g, s, t):
        s = cls.node_to_nodeid(g, s)
        t = cls.node_to_nodeid(g, t)
        sh_path_length = g.shortest_paths(s, t)[0][0]
        return sh_path_length < float('inf')

    @classmethod
    def is_local_preferenced(cls, g, trace,
                             vf_g=None, first_edge=True, vfmode=None):
        if vf_g is None: vf_g = VFT.convert_to_vf(g, vfmode)

        # trace = [cls.node_to_nodeid(g, x) for x in trace]

        # if only first edge matters:
        #   - get the shortest LP (SHLP) from s. If the type of the first edge
        #     in SHLP is the same as in trace: trace is LP

        t = trace[-1]
        edges = zip(trace, trace[1:])

        if len(edges) == 0: return True

        if first_edge: edges = [edges[0], ]
        logger.debug('lp check edges: %s' % edges)
        for e in edges:
            s = e[0]
            e_dir = VFT.edge_dir(g, e, vfmode)
            lp_route = VFT.get_shortest_vf_route(g, s, t,
                                                 mode='lp',
                                                 vf_g=vf_g, vfmode=vfmode)
            if len(lp_route) < 1:
                print
                print 'CHECK ME AT VALLEY_FREE_TOOLS'
                print 'S: %s' % s
                print 'T: %s' % t
                print trace
                print edges
                print lp_route
                return False  # direct link
            lp_dir = VFT.edge_dir(g, (lp_route[0], lp_route[1]), vfmode)

            if lp_dir != e_dir:  # LP affects only next hop decision
                return False

        return True

    @classmethod
    def label_graph_edges(cls, network, vfmode=None):
        g = copy.deepcopy(network)
        for edge in g.es:
            e_dir = VFT.edge_dir(g, [edge.source, edge.target], vfmode)
            # logger.debug('E dir %s -> %s is [b]%s[/]' % (edge.source,
            #                                              edge.target,
            #                                              e_dir))
            edge['dir'] = e_dir

        return g

    @classmethod
    def convert_to_vf(cls, network, vfmode=None, labeled_graph=None):
        cls.graph_dir_check(network)

        if labeled_graph is None:
            labeled_graph = cls.label_graph_edges(network, vfmode)
        
        N = labeled_graph.vcount()
        g = igraph.Graph(directed=True)
        g.add_vertices(range(0, 2 * N))

        cp_e = [x for x in labeled_graph.es if x['dir'] == LinkDir.U]
        pc_e = [x for x in labeled_graph.es if x['dir'] == LinkDir.D]

        # fw_e = [x for x in labeled_graph.es if x['dir'] != LinkDir.P]
        peer_e = [x for x in labeled_graph.es if x['dir'] == LinkDir.P]

        # fw_e = network.es.select(**{VFT.TYPE: LinkType.C2P})
        # peer_e = network.es.select(**{VFT.TYPE: LinkType.P2P})

        # **** Az iranyitott grafok eseten fontos megvizsgalni
        #      hogy az itt generalt elek szerinti bejaras valoban
        #      engedelyezett-e a valos grafban is. Ezert minden el
        #      letrehozasa elott tortenik egy feltetel vizsgalat
        #      hogy az adott iranyban valoban letezik-e el a valos halozatban
        #      is. Ha nem, akkor azok az utvonalak, amelyek az adott elet
        #      hasznalnak, nem valos bejarasai lennenek az eredeti grafnak.
        #      Iranyitatlan graf eseten a directed=True (default value)
        #      figyelmen kivul van hagyva az igraphnal.

        cp_edges = [(x.source, x.target) for x in cp_e
                    if labeled_graph.get_eid(x.source, x.target, error=False) != -1]
        pc_edges = [(x.target, x.source) for x in pc_e
                    if labeled_graph.get_eid(x.target, x.source, error=False) != -1]
        fwd_edges = cp_edges + pc_edges
        # fwd_edges = [(x.source, x.target) for x in fw_e]

        # fwd_over = [(x.source, x.target + N) for x in fw_e]

        cp_edges = [(x.target + N, x.source + N) for x in cp_e
                    if labeled_graph.get_eid(x.target, x.source, error=False) != -1]
        pc_edges = [(x.source + N, x.target + N) for x in pc_e
                    if labeled_graph.get_eid(x.source, x.target, error=False) != -1]
        bw_edges = cp_edges + pc_edges
        # bw_edges = [(x.target + N, x.source + N) for x in fw_e]

        peer_e_1 = [(x.source, x.target + N) for x in peer_e
                    if labeled_graph.get_eid(x.source, x.target, error=False) != -1]
        peer_e_2 = [(x.target, x.source + N) for x in peer_e
                    if labeled_graph.get_eid(x.target, x.source, error=False) != -1]
        self_conn = [(x, x + N) for x in range(0, N)]

        self_conn_weight = 0
        customer_conn_weight = 1
        peer_conn_weight = len(bw_edges) + 1  # customer edge count+1
        # a route with all customer edge is better than a route with one peer
        provider_conn_weight = peer_conn_weight + len(bw_edges) + 1
        # a valid VF route with one p2p connection and with all customer
        # connection is better in LP point of view than a route with one
        # provider edge

        offset = g.ecount()
        g.add_edges(self_conn)
        g.es[offset:g.ecount()]['LPweight'] = self_conn_weight
        g.es[offset:g.ecount()]['VFweight'] = 0

        offset = g.ecount()
        g.add_edges(bw_edges)
        g.es[offset:g.ecount()]['LPweight'] = customer_conn_weight
        g.es[offset:g.ecount()]['VFweight'] = 1

        offset = g.ecount()
        g.add_edges(peer_e_1)
        g.add_edges(peer_e_2)
        g.es[offset:g.ecount()]['LPweight'] = peer_conn_weight
        g.es[offset:g.ecount()]['VFweight'] = 1

        offset = g.ecount()
        g.add_edges(fwd_edges)
        # g.add_edges(fwd_over)
        g.es[offset:g.ecount()]['LPweight'] = provider_conn_weight
        g.es[offset:g.ecount()]['VFweight'] = 1

        g['all_lpweight'] = sum([x['LPweight'] for x in g.es])
        g['all_vfweight'] = sum([x['VFweight'] for x in g.es])

        for x in g.vs:
            old_idx = x.index % N
            name = network.vs[old_idx]['name']
            if x.index >= N: name = 'E{name}'.format(name=name)
            x['name'] = name

        return g

    @classmethod
    def get_valley_triplets(cls, g, trace, vfmode=None):
        trace = [cls.node_to_nodeid(g, x) for x in trace]
        trace_rank = [cls.node_rank(g, x, vfmode) for x in trace]
        logger.debug('Trace rank: %s' % trace_rank)
        valley_triplets = []
        for idx, a, b, c in zip(range(0, len(trace)), trace_rank, trace_rank[1:], trace_rank[2:]):
            logger.debug('Triplet: %f %f %f' % (a, b, c))
            DU = (a > b and b < c)
            DP = (a > b and b == c) 
            PU = (a == b and b < c)
            PP = (a == b and b == c)
            logger.debug('DU: %s, DP: %s, PU: %s, PP: %s' % (DU, DP, PU, PP))
            if DU or DP or PU or PP:
                valley_triplets.append((trace[idx],
                                        trace[idx + 1],
                                        trace[idx + 2]))

        return valley_triplets
                        
                

    @classmethod
    def vf_route_converter(cls, vf_route, N):
        orig_id_route = [x % N for x in vf_route]
        converted_route = [x for x, v in itertools.groupby(orig_id_route)]
        return converted_route

    @classmethod
    def trace_clean(cls, network, traceroutes):
        good_traceroutes = []
        ignored = 0
        for traceroute in traceroutes:
            try:
                [network.vs.find(x) for x in traceroute]
            except ValueError:  # no such vertex error. Ignore this traceroute
                # print 'No such trace %s' % traceroute
                ignored += 1
                continue
            good_traceroutes.append(traceroute)
        logger.warn('Ignored: %d/%d[%f]' % (ignored, len(traceroutes),
                                            ignored / float(len(traceroutes))))
        return (good_traceroutes, ignored)

    @classmethod
    def trace_in_vertex_id(cls, network, traceroutes):
        mapped_traceroutes = list()
        for traceroute in traceroutes:
            converted_trace = [cls.node_to_nodeid(network, x) for x in traceroute]
            mapped_traceroutes.append(converted_trace)
        return mapped_traceroutes

    @classmethod
    def trace_in_vertex_name(cls, network, traceroutes):
        mapped_traceroutes = list()
        for traceroute in traceroutes:
            converted_trace = [network.vs[x]['name'] for x in traceroute]
            mapped_traceroutes.append(converted_trace)

        return mapped_traceroutes

    @classmethod
    def get_shortest_vf_route(cls, original_network, s, t,
                              mode='vf', vf_g=None, _all=False, vfmode=None):

        if vf_g is None:
            vf_g = VFT.convert_to_vf(original_network, vfmode=vfmode)

        if mode == 'vf': weights = 'VFweight'
        elif mode == 'lp': weights = 'LPweight'
        else: raise ValueError('Unknown mode %s. Use "vf" or "lp"' % mode)

        s = cls.node_to_nodeid(original_network, s)
        t = cls.node_to_nodeid(original_network, t)

        N = original_network.vcount()
        candidates = vf_g.get_all_shortest_paths(s, t + N, mode=igraph.OUT,
                                                 weights=weights)

        candidates = [VFT.vf_route_converter(x, N) for x in candidates]
        # candidates = sorted(candidates, key=len)

        # there is no vf route between them
        if len(candidates) == 0: return []

        if not _all: candidates = candidates[0]

        return candidates


VFT.EDGE_DIR_METHOD = {
    VFT.CLOSENESS: VFT.rank_closeness,
    VFT.PRELABELED: VFT.rank_prelabeled,
    VFT.DEGREE: VFT.rank_degree
}
