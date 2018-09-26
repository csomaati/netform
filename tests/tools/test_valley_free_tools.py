import igraph
import unittest
from mock import MagicMock
from tools import valley_free_tools as vf_tools
from tools.valley_free_tools import VFT as vft


class UnitTestWithGraph(unittest.TestCase):
    def setUp(self):
        sample_graph = igraph.Graph(directed=False)
        sample_graph.add_vertices(range(0, 8))
        # kicsit kavart, mert az iranyitatlan es iranyitott grafoknal
        # az edge.source es edge.target kicsit maskepp van kezelve
        # es par vft kod hasznalja. Azok megzavarasara van igy rendezve
        sample_graph.add_edges([[0, 5],
                                [1, 5],
                                [2, 6],
                                [6, 3],
                                [5, 6],
                                [4, 5],
                                [6, 4]])
        # Named nodes
        for x in sample_graph.vs:
            x['name'] = 'N{d}'.format(d=x.index)

        self.sample_graph = sample_graph

        self.prelabeled = {4: 2, 5: 1, 6: 1, 0: 0, 1: 0, 2: 0, 3: 0, 7: 10000}
        self.closenesses = {4: 2.1, 5: 1.1, 6: 1.1, 0: 0.1, 1: 0.1, 2: 0.1,
                            3: 0.1, 7: 10000.0}
        self.degrees = {4: 5, 5: 4, 6: 4, 0: 1, 1: 1, 2: 1, 3: 1, 7: 10000}

        def degree_side_effect(g, n):
            return self.degrees[n]

        def prelabeled_side_effect(g, n):
            return self.prelabeled[n]

        def closeness_side_effect(g, n):
            return self.closenesses[n]

        vft.rank_prelabeled = MagicMock(side_effect=prelabeled_side_effect)
        vft.rank_degree = MagicMock(side_effect=degree_side_effect)
        vft.rank_closeness = MagicMock(side_effect=closeness_side_effect)

        vft.EDGE_DIR_METHOD = {
            vft.CLOSENESS: vft.rank_closeness,
            vft.PRELABELED: vft.rank_prelabeled,
            vft.DEGREE: vft.rank_degree
        }


class TestPresumtions(unittest.TestCase):

    def setUp(self):
        sample_graph = igraph.Graph(directed=False)
        sample_graph.add_vertices(range(0, 7))
        sample_graph.add_edges([[0, 1],
                                [1, 2]])
        # Named nodes
        for x in sample_graph.vs:
            x['name'] = 'N{d}'.format(d=x.index)

        self.sample_graph = sample_graph

    def test_closeness_of_middle_node_is_higher(self):
        c0 = self.sample_graph.closeness(0, mode=igraph.ALL)
        c1 = self.sample_graph.closeness(1, mode=igraph.ALL)
        c2 = self.sample_graph.closeness(2, mode=igraph.ALL)

        self.assertNotAlmostEqual(c0, c1)
        self.assertNotAlmostEqual(c1, c2)
        self.assertAlmostEqual(c0, c2)

        self.assertGreater(c1, c0)
        self.assertGreater(c1, c2)


class TestValleyFreeToolEdgeDirection(UnitTestWithGraph):

    def test_edge_dir_closeness_with_id(self):
        dir_u = vft.edge_dir(self.sample_graph, (5, 4), vfmode=vft.CLOSENESS)
        dir_d = vft.edge_dir(self.sample_graph, (6, 2), vfmode=vft.CLOSENESS)
        dir_p = vft.edge_dir(self.sample_graph, (5, 6), vfmode=vft.CLOSENESS)

        self.assertEqual(dir_u, vf_tools.LinkDir.U)
        self.assertEqual(dir_d, vf_tools.LinkDir.D)
        self.assertEqual(dir_p, vf_tools.LinkDir.P)

    def test_edge_dir_closeness_with_name(self):
        dir_u = vft.edge_dir(self.sample_graph, ('N5', 'N4'),
                             vfmode=vft.CLOSENESS)
        dir_d = vft.edge_dir(self.sample_graph, ('N6', 'N2'),
                             vfmode=vft.CLOSENESS)
        dir_p = vft.edge_dir(self.sample_graph, ('N5', 'N6'),
                             vfmode=vft.CLOSENESS)

        self.assertEqual(dir_u, vf_tools.LinkDir.U)
        self.assertEqual(dir_d, vf_tools.LinkDir.D)
        self.assertEqual(dir_p, vf_tools.LinkDir.P)

    def test_edge_dir_rank_with_id(self):
        dir_u = vft.edge_dir(self.sample_graph, (5, 4), vfmode=vft.DEGREE)
        dir_d = vft.edge_dir(self.sample_graph, (6, 2), vfmode=vft.DEGREE)
        dir_p = vft.edge_dir(self.sample_graph, (5, 6), vfmode=vft.DEGREE)

        self.assertEqual(dir_u, vf_tools.LinkDir.U)
        self.assertEqual(dir_d, vf_tools.LinkDir.D)
        self.assertEqual(dir_p, vf_tools.LinkDir.P)

    def test_edge_dir_rank_with_name(self):
        dir_u = vft.edge_dir(self.sample_graph, ('N5', 'N4'),
                             vfmode=vft.DEGREE)
        dir_d = vft.edge_dir(self.sample_graph, ('N6', 'N2'),
                             vfmode=vft.DEGREE)
        dir_p = vft.edge_dir(self.sample_graph, ('N5', 'N6'),
                             vfmode=vft.DEGREE)

        self.assertEqual(dir_u, vf_tools.LinkDir.U)
        self.assertEqual(dir_d, vf_tools.LinkDir.D)
        self.assertEqual(dir_p, vf_tools.LinkDir.P)

    def test_edge_dir_prelabeled_with_id(self):
        dir_u = vft.edge_dir(self.sample_graph, (5, 4), vfmode=vft.PRELABELED)
        dir_d = vft.edge_dir(self.sample_graph, (6, 2), vfmode=vft.PRELABELED)
        dir_p = vft.edge_dir(self.sample_graph, (5, 6), vfmode=vft.PRELABELED)

        self.assertEqual(dir_u, vf_tools.LinkDir.U)
        self.assertEqual(dir_d, vf_tools.LinkDir.D)
        self.assertEqual(dir_p, vf_tools.LinkDir.P)

    def test_edge_dir_prelabeled_with_name(self):
        dir_u = vft.edge_dir(self.sample_graph, ('N5', 'N4'),
                             vfmode=vft.PRELABELED)
        dir_d = vft.edge_dir(self.sample_graph, ('N6', 'N2'),
                             vfmode=vft.PRELABELED)
        dir_p = vft.edge_dir(self.sample_graph, ('N5', 'N6'),
                             vfmode=vft.PRELABELED)

        self.assertEqual(dir_u, vf_tools.LinkDir.U)
        self.assertEqual(dir_d, vf_tools.LinkDir.D)
        self.assertEqual(dir_p, vf_tools.LinkDir.P)

    def test_edge_dir_error(self):
        up = self.sample_graph.es[self.sample_graph.get_eid(4, 5)]
        error_msg = "igraph's edge type is not supported"
        with self.assertRaises(AttributeError, msg=error_msg):
            vft.edge_dir(self.sample_graph, up, vfmode=vft.PRELABELED)
        with self.assertRaises(AttributeError, msg=error_msg):
            vft.edge_dir(self.sample_graph, up, vfmode=vft.CLOSENESS)
        with self.assertRaises(AttributeError, msg=error_msg):
            vft.edge_dir(self.sample_graph, up, vfmode=vft.DEGREE)


class TestValleyFreeToolTraceMethods(UnitTestWithGraph):

    def test_edgelist_to_string(self):
        edges = [[0, 5], [5, 4], [4, 6], [6, 5], [5, 6], [6, 2]]  # UUDPPD
        trace = vft.edgelist_to_string(self.sample_graph, edges)
        self.assertEqual(trace, 'UUDPPD')

    def test_trace_to_string(self):
        trace = [0, 5, 4, 6, 5, 1, 5, 6, 4, 6, 2]
        trace_str = vft.trace_to_string(self.sample_graph, trace)
        self.assertEqual(trace_str, 'UUDPDUPUDD')

    def test_is_valley_free_true(self):
        simple_vf = [0, 5, 4, 6, 2]  # UUDD - vf
        middle_peer_vf = [0, 5, 6, 2]  # UPD - vf
        just_down = [4, 6, 3]  # DD - vf
        just_up = [1, 5, 4]  # UU - vf
        start_peer = [5, 6, 3]  # PD - vf
        just_peer = [5, 6]  # P - vf

        self.assertTrue(vft.is_valley_free(self.sample_graph, simple_vf))
        self.assertTrue(vft.is_valley_free(self.sample_graph, middle_peer_vf))
        self.assertTrue(vft.is_valley_free(self.sample_graph, just_down))
        self.assertTrue(vft.is_valley_free(self.sample_graph, just_up))
        self.assertTrue(vft.is_valley_free(self.sample_graph, start_peer))
        self.assertTrue(vft.is_valley_free(self.sample_graph, just_peer))

    def test_is_valley_free_false(self):
        peerup = [0, 5, 6, 4]  # DPU
        peerpeer = [0, 5, 6, 5, 1]  # UPPD
        downpeer = [4, 6, 5, 0]  # DPD
        downup = [4, 5, 4]  # DU

        self.assertFalse(vft.is_valley_free(self.sample_graph, peerup))
        self.assertFalse(vft.is_valley_free(self.sample_graph, peerpeer))
        self.assertFalse(vft.is_valley_free(self.sample_graph, downpeer))
        self.assertFalse(vft.is_valley_free(self.sample_graph, downup))

    def test_trace_exists(self):
        real_trace = [0, 5, 4, 6, 5, 1]
        nonreal_trace = [0, 5, 2, 6]

        self.assertTrue(vft.trace_exists(self.sample_graph, real_trace))
        self.assertFalse(vft.trace_exists(self.sample_graph, nonreal_trace))

    def test_route_exists(self):
        s_ok, t_ok = 0, 2
        s_nok, t_nok = 0, 7

        self.assertTrue(vft.route_exists(self.sample_graph, s_ok, t_ok))
        self.assertFalse(vft.route_exists(self.sample_graph, s_nok, t_nok))


class TestExtendedGraph(UnitTestWithGraph):

    def test_convert_to_vf(self):
        vfg = vft.convert_to_vf(self.sample_graph)
        self.assertEqual(vfg.ecount(), 22)
        self.assertEqual(vfg.vcount(), 16)

        real_traces = [['N0', 'N5', 'EN5', 'EN1'],
                       ['N1', 'N5', 'N4', 'EN4', 'EN6', 'EN3'],  # SELF hop
                       ['N5', 'EN6', 'EN2']]  # PEER edge
        fake_traces = [['EN4', 'EN6', 'EN6', 'EN5', 'EN4'],  # DPU
                       ['N5', 'EN6', 'N5'],  # PP
                       ['EN4', 'EN6', 'N5'],  # DP
                       ['N0', 'N5', 'EN5', 'EN4']]  # if CP and PC edge
                                                    # not handled properly

        self.assertFalse(all([vft.trace_exists(vfg, x) for x in fake_traces]))
        self.assertTrue(all([vft.trace_exists(vfg, x) for x in real_traces]))

    def test_vf_route_converter(self):
        N = self.sample_graph.vcount()
        route_vf = [0, 5, 4, 12, 14, 10]
        route_orig = [0, 5, 4, 6, 2]
        self.assertEqual(vft.vf_route_converter(route_vf, N), route_orig)


class TestTraceConverting(UnitTestWithGraph):

    def test_trace_clean(self):
        traceroutes = [['N0', 'N5', 'N4', 'N6'],
                       ['NFAKE', 'N4', 'N5'],
                       ['N5', 'N5', 'N4', 'N5'],
                       ['N5', 'N2', 'N4']]

        cleaned_traces, ignored = vft.trace_clean(self.sample_graph,
                                                  traceroutes)
        self.assertEqual(len(cleaned_traces), 3)
        self.assertEqual(ignored, 1)
        self.assertIn(['N0', 'N5', 'N4', 'N6'], cleaned_traces)
        self.assertIn(['N5', 'N5', 'N4', 'N5'], cleaned_traces)
        self.assertIn(['N5', 'N2', 'N4'], cleaned_traces)

    def test_trace_conversion(self):
        traceroutes = [['N0', 'N5', 'N4', 'N6'],
                       ['N5', 'N5', 'N4', 'N5'],
                       ['N5', 'N2', 'N4']]
        traceroutes_check = [[0, 5, 4, 6],
                             [5, 5, 4, 5],
                             [5, 2, 4]]
        trace_id = vft.trace_in_vertex_id(self.sample_graph, traceroutes)
        self.assertEqual(traceroutes_check, trace_id)
        trace_back = vft.trace_in_vertex_name(self.sample_graph, trace_id)
        self.assertEqual(traceroutes, trace_back)

    def test_trace_conversion_error(self):
        fake_trace = [['FAKE', 'FAKE1'], ]
        fake_trace_id = [[2, 4, 55], ]
        with self.assertRaises(ValueError):
            _ = vft.trace_in_vertex_id(self.sample_graph, fake_trace)

        with self.assertRaises(IndexError):
            _ = vft.trace_in_vertex_name(self.sample_graph, fake_trace_id)


class TestVFSearch(UnitTestWithGraph):

    def test_shortest_vf_route(self):
        s, t = 0, 1  # shortest vf: N0 - N5 - N1
        shortest_vf = [0, 5, 1]
        sh = vft.get_shortest_vf_route(self.sample_graph, s, t)
        self.assertEqual(sh, shortest_vf)

        s, t = 0, 2
        shortest_vf = [0, 5, 6, 2]
        sh = vft.get_shortest_vf_route(self.sample_graph, s, t)
        self.assertEqual(sh, shortest_vf)

    def test_all_shortest_vf_route(self):
        self.sample_graph.add_vertex('N8')
        self.sample_graph.add_edges([['N8', 'N5'], ['N6', 'N8']])
        self.prelabeled[8] = self.prelabeled[4]
        self.sample_graph.delete_edges([self.sample_graph.get_eid(5, 6), ])

        s, t = 0, 2
        shortest_vf1 = [0, 5, 4, 6, 2]
        shortest_vf2 = [0, 5, 8, 6, 2]
        sh = vft.get_shortest_vf_route(self.sample_graph, s, t, _all=True)
        self.assertEqual(len(sh), 2)
        self.assertIn(shortest_vf1, sh)
        self.assertIn(shortest_vf2, sh)


class TestLPFunctions(UnitTestWithGraph):
    def test_all_shortest_lp_route(self):
        self.sample_graph.add_vertices(['N8', 'N9'])
        self.sample_graph.add_edges([['N8', 'N5'], ['N2', 'N8'],
                                     ['N9', 'N5'], ['N2', 'N9']])
        self.prelabeled[8] = 0.5
        self.prelabeled[9] = 0.5

        s, t = 1, 2
        shortest_lp = [1, 5, 8, 2]
        shortest_lp2 = [1, 5, 9, 2]
        sh = vft.get_shortest_vf_route(self.sample_graph,
                                       s, t, _all=True, mode='lp')
        self.assertEqual(len(sh), 2)
        self.assertIn(shortest_lp, sh)
        self.assertIn(shortest_lp2, sh)

    def test_lp_choose_customer_cone(self):
        self.sample_graph.add_vertices(['N8', 'N9'])
        self.prelabeled[8] = self.prelabeled[7]
        self.prelabeled[9] = self.prelabeled[7] * 2
        self.closenesses[8] = self.closenesses[7]
        self.closenesses[9] = self.closenesses[7] * 2
        
        self.sample_graph.add_edges([['N4', 'N7'],
                                     ['N9', 'N7'],
                                     ['N8', 'N7'],
                                     ['N3', 'N8'],
                                     ['N9', 'N3']
        ])
        s = self.sample_graph.vs.find('N7').index
        t = self.sample_graph.vs.find('N3').index
        
        sh = vft.get_shortest_vf_route(self.sample_graph,
                                       s, t, _all=True, mode='lp')
        self.assertEqual(len(sh), 1)
        self.assertEqual(sh[0], [7, 4, 6, 3])

    def test_lp_choose_peer_if_no_customer_cone(self):
        self.sample_graph.add_vertices(['N8', 'N9'])
        self.prelabeled[8] = self.prelabeled[7]
        self.prelabeled[9] = self.prelabeled[7] * 2
        self.closenesses[8] = self.closenesses[7]
        self.closenesses[9] = self.closenesses[7] * 2
        
        self.sample_graph.add_edges([['N9', 'N7'],
                                     ['N8', 'N7'],
                                     ['N6', 'N8'],
                                     ['N9', 'N3']
        ])
        s = self.sample_graph.vs.find('N7').index
        t = self.sample_graph.vs.find('N3').index
        sh = vft.get_shortest_vf_route(self.sample_graph,
                                       s, t, _all=True, mode='lp')
        self.assertEqual(len(sh), 1)
        self.assertEqual(sh[0], [7, 8, 6, 3])

    def test_soft_lp_check(self):
        self.sample_graph.add_vertices(['N8', ])
        self.prelabeled[8] = 0.5
        self.closenesses[8] = 0.5
        self.sample_graph.add_edges([['N5', 'N7'],
                                     ['N3', 'N7'],
                                     ['N8', 'N5'],
                                     ['N6', 'N8'],
                                     ['N7', 'N4']
        ])

        lp_hard_routes = [['N0', 'N5', 'N6', 'N2'],
                          ['N5', 'N6'],
                          ['N4', 'N6', 'N2'],
                          ['N7', 'N4', 'N6', 'N3']
        ]
        # Az egyetlen kulonbseg a soft es hard lp kozott
        # csak akkor johet elo, mikor U ellel kezdunk, es
        # a kov. hopnal lehet fel vagy le/peer elen menni
        # A soft ekkor mehet tovabb fel, a hard csak peer/le
        # elet valaszthat.
        lp_soft_routes = [['N0', 'N5', 'N4', 'N6', 'N2'],
                          ['N1', 'N5', 'N6', 'N8']
        ]
        non_lp = [['N5', 'N4', 'N6'],
                  ['N5', 'N6', 'N8'],
                  ['N5', 'N4', 'N6', 'N2']
        ]

        vf_g = vft.convert_to_vf(self.sample_graph, vfmode=vft.CLOSENESS)

        for trace in lp_hard_routes:
            is_lp_hard = vft.is_local_preferenced(self.sample_graph, trace, vf_g=vf_g,
                                                  first_edge=False, vfmode=vft.CLOSENESS)
            is_lp_soft = vft.is_local_preferenced(self.sample_graph, trace, vf_g=vf_g,
                                                  first_edge=True, vfmode=vft.CLOSENESS)

            self.assertTrue(is_lp_hard)
            self.assertTrue(is_lp_soft)
        
        for trace in lp_soft_routes:
            is_lp_hard = vft.is_local_preferenced(self.sample_graph, trace, vf_g=vf_g,
                                                  first_edge=False, vfmode=vft.CLOSENESS)
            is_lp_soft = vft.is_local_preferenced(self.sample_graph, trace, vf_g=vf_g,
                                                  first_edge=True, vfmode=vft.CLOSENESS)

            self.assertFalse(is_lp_hard)
            self.assertTrue(is_lp_soft)

        for trace in non_lp:
            is_lp_hard = vft.is_local_preferenced(self.sample_graph, trace, vf_g=vf_g,
                                                  first_edge=False, vfmode=vft.CLOSENESS)
            is_lp_soft = vft.is_local_preferenced(self.sample_graph, trace, vf_g=vf_g,
                                                  first_edge=True, vfmode=vft.CLOSENESS)

            self.assertFalse(is_lp_hard)
            self.assertFalse(is_lp_soft)


if __name__ == '__main__':
    unittest.main()
