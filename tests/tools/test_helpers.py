import unittest
import igraph
from tools import helpers
import logging

logging.basicConfig(level=logging.INFO)


class HelperTest(unittest.TestCase):

    def test_dfs_mark_if_node_not_exits(self):
        sample_graph = igraph.Graph(directed=False)
        sample_graph.add_vertices(range(0, 6))
        sample_graph.add_edges([[0, 1],
                                [0, 2],
                                [1, 3],
                                [2, 4],
                                [3, 5],
                                [4, 5]])
        for node in sample_graph.vs:
            node['traces'] = dict()
        all_path = helpers.dfs_mark(sample_graph, 0, 9999, 10)
        self.assertEqual(len(all_path), 0)

        for node in sample_graph.vs:
            node['traces'] = dict()
        # source node can not be found in the graph. Igraph error
        all_path = helpers.dfs_mark(sample_graph, 9999, 5, 10)
        self.assertEqual(len(all_path), 0)

    def test_dfs_mark_found_all_path_undirected(self):
        sample_graph = igraph.Graph(directed=False)
        sample_graph.add_vertices(range(0, 6))
        sample_graph.add_edges([[0, 1],
                                [0, 2],
                                [1, 3],
                                [2, 4],
                                [3, 5],
                                [4, 5]])

        for node in sample_graph.vs:
            node['traces'] = dict()
        all_path = helpers.dfs_mark(sample_graph, 0, 5, 10)
        self.assertEqual(len(all_path), 2)
        self.assertIn((0, 1, 3, 5), all_path)
        self.assertIn((0, 2, 4, 5), all_path)

    def test_dfs_mark_found_hop_limited_paths_undirected(self):
        sample_graph = igraph.Graph(directed=False)
        sample_graph.add_vertices(range(0, 6))
        sample_graph.add_edges([[0, 1],
                                [0, 4],
                                [0, 5],
                                [1, 5],
                                [1, 2],
                                [2, 5],
                                [2, 3],
                                [3, 5],
                                [3, 4],
                                [4, 5]])
        for node in sample_graph.vs:
            node['traces'] = dict()
        all_path = helpers.dfs_mark(sample_graph, 0, 5, 1)
        self.assertIsNone(all_path)

        for node in sample_graph.vs:
            node['traces'] = dict()
        all_path = helpers.dfs_mark(sample_graph, 0, 5, 2)
        self.assertEqual(len(all_path), 1)
        self.assertIn((0, 5), all_path)

        for node in sample_graph.vs:
            node['traces'] = dict()
        all_path = helpers.dfs_mark(sample_graph, 0, 5, 3)
        self.assertEqual(len(all_path), 3)
        self.assertIn((0, 5), all_path)
        self.assertIn((0, 1, 5), all_path)
        self.assertIn((0, 4, 5), all_path)

    def test_dfs_mark_found_hop_limited_paths_long_undirected(self):
        sample_graph = igraph.Graph(directed=False)
        sample_graph.add_vertices(range(0, 5))
        sample_graph.add_edges([[0, 1],
                                [0, 4],
                                [0, 3],
                                [1, 4],
                                [1, 2],
                                [2, 4],
                                [2, 3],
                                [3, 4]])

        for node in sample_graph.vs:
            node['traces'] = dict()
        all_path = helpers.dfs_mark(sample_graph, 0, 4, 5)
        self.assertEqual(len(all_path), 7)
        self.assertIn((0, 4), all_path)
        self.assertIn((0, 3, 2, 1, 4), all_path)
        self.assertIn((0, 1, 2, 3, 4), all_path)
        self.assertIn((0, 3, 2, 4), all_path)
        self.assertIn((0, 3, 4), all_path)

    def random_walk_route_test_graph(self):
        g = igraph.Graph(directed=False)
        g.add_vertices(range(0, 6))
        g.add_edges([[0, 1],
                     [0, 2],
                     [1, 3],
                     [1, 4],
                     [3, 5],
                     [4, 5],
                     [2, 5]])
        for vertex in g.vs:
            vertex['name'] = 'N{}'.format(vertex.index)
        return g

    def test_random_route_walk_too_short_criteria(self):
        g = self.random_walk_route_test_graph()
        res = helpers.random_route_walk(g, 'N0', 'N5', 0)
        self.assertEqual(len(res), 0)
        res = helpers.random_route_walk(g, 'N0', 'N5', 1)
        self.assertEqual(len(res), 0)
        res = helpers.random_route_walk(g, 'N0', 'N5', 2)
        self.assertEqual(len(res), 0)

    def test_random_route_walk_node_is_not_exists(self):
        g = self.random_walk_route_test_graph()
        self.assertRaises(IndexError,
                          helpers.random_route_walk,
                          g, 'N0', 'N66', 100)
        self.assertRaises(IndexError,
                          helpers.random_route_walk,
                          g, 'N0', 'N66', 0)
        self.assertRaises(IndexError,
                          helpers.random_route_walk,
                          g, 'N0', 'N66', 1)

    def test_random_route_walk_only_one_route(self):
        g = self.random_walk_route_test_graph()
        g.delete_vertices(['N3', 'N4'])
        for probe in xrange(0, 1000):
            routes = helpers.random_route_walk(g, 'N0', 'N5', 3, named=True)
            self.assertEqual(len(routes), 3)
            self.assertEqual(routes, ['N0', 'N2', 'N5'])

    def test_random_route_walk_two_paralell_routes(self):
        g = self.random_walk_route_test_graph()
        g.delete_vertices(['N3'])
        first_route = 0
        second_route = 0
        anomaly = 0
        for probe in xrange(0, 10000):
            routes = helpers.random_route_walk(g, 'N0', 'N5', 4, named=True)
            route_statement = len(routes) == 4 or len(routes) == 3
            self.assertTrue(route_statement)
            if routes == ['N0', 'N1', 'N4', 'N5']:
                first_route += 1
            elif routes == ['N0', 'N2', 'N5']:
                second_route += 1
            else:
                anomaly += 1
        self.assertEqual(anomaly, 0)
        self.assertTrue(abs(first_route / 10000.0 - 0.50) < 0.1)
        self.assertTrue(abs(second_route / 10000.0 - 0.50) < 0.1)

    def test_random_route_walk_covered_routes(self):
        g = self.random_walk_route_test_graph()
        first_route = 0
        second_route = 0
        third_route = 0
        anomaly = 0
        for probe in xrange(0, 10000):
            route = helpers.random_route_walk(g, 'N0', 'N5', 4, named=True)
            route_statement = len(route) == 4 or len(route) == 3
            self.assertTrue(route_statement)
            if route == ['N0', 'N1', 'N4', 'N5']:
                first_route += 1
            elif route == ['N0', 'N2', 'N5']:
                second_route += 1
            elif route == ['N0', 'N1', 'N3', 'N5']:
                third_route += 1
            else:
                anomaly += 1
        self.assertEqual(anomaly, 0)
        self.assertTrue(abs(first_route / 10000.0 - 0.25) < 0.1)
        self.assertTrue(abs(second_route / 10000.0 - 0.50) < 0.1)
        self.assertTrue(abs(third_route / 10000.0 - 0.25) < 0.1)

    def test_random_route_walk_two_paralell_and_one_dead_end(self):
        g = self.random_walk_route_test_graph()
        g.add_vertices(2)
        g.vs[6]['name'] = 'N6'
        g.vs[7]['name'] = 'N7'
        g.add_edges([[6, 7], [1, 6]])
        g.delete_vertices(['N3', ])
        first_route = 0
        second_route = 0
        anomaly = 0
        for probe in xrange(0, 10000):
            routes = helpers.random_route_walk(g, 'N0', 'N5', 1000, named=True)
            route_statement = len(routes) == 4 or len(routes) == 3
            self.assertTrue(route_statement)
            if routes == ['N0', 'N1', 'N4', 'N5']:
                first_route += 1
            elif routes == ['N0', 'N2', 'N5']:
                second_route += 1
            else:
                anomaly += 1
        self.assertEqual(anomaly, 0)
        self.assertTrue(abs(first_route / 10000.0 - 0.50) < 0.1)
        self.assertTrue(abs(second_route / 10000.0 - 0.50) < 0.1)

    def test_random_route_walk_keep_limits(self):
        g = self.random_walk_route_test_graph()
        for probe in xrange(0, 1000):
            route = helpers.random_route_walk(g, 'N0', 'N5', 3, named=True)
            self.assertEqual(len(route), 3)
            self.assertEqual(route, ['N0', 'N2', 'N5'])

    def test_random_route_walk_no_loops(self):
        g = self.random_walk_route_test_graph()
        for probe in xrange(0, 1000):
            route = helpers.random_route_walk(g, 'N0', 'N5', 100, named=True)
            self.assertEqual(len(route), len(set(route)))

    def test_random_route_walk_loop(self):
        g = self.random_walk_route_test_graph()
        g.delete_edges([(g.vs.find('N0').index, g.vs.find('N2').index),
                        (g.vs.find('N2').index, g.vs.find('N5').index),
                        (g.vs.find('N4').index, g.vs.find('N5').index),
                        (g.vs.find('N1').index, g.vs.find('N4').index)])
        g.add_edges([['N3', 'N2'], ['N2', 'N4'], ['N4', 'N3']])
        for probe in xrange(0, 1000):
            route = helpers.random_route_walk(g, 'N0', 'N5', 100, named=True)
            self.assertEqual(len(route), len(set(route)))
            self.assertEqual(len(route), 4)
            self.assertEqual(route, ['N0', 'N1', 'N3', 'N5'])

    def test_random_route_walk_merged_routes(self):
        # A visszalepesekkel tiltolistara kerult node nem zavar be
        # Nem zavarhat, hiszen melysegi kereses tortenik, de azert vizsgaljuk
        # meg
        g = self.random_walk_route_test_graph()
        g.delete_edges([(g.vs.find('N0').index, g.vs.find('N2').index), ])
        g.add_vertex(name='N6')
        g.add_edge('N5', 'N6')
        for probe in xrange(0, 1000):
            route = helpers.random_route_walk(g, 'N0', 'N2', 100, named=True)
            self.assertEqual(len(route), len(set(route)))
            self.assertEqual(len(route), 5)
            self.assertIn(route, [['N0', 'N1', 'N3', 'N5', 'N2'],
                                  ['N0', 'N1', 'N4', 'N5', 'N2']])

    def test_random_route_walk_weighted_edges(self):
        g = self.random_walk_route_test_graph()
        weights = [2, 1000, 1, 1000, 100, 1, 0]
        g.es['w'] = weights
        for probe in xrange(0, 1000):
            route = helpers.random_route_walk(g, 'N0', 'N5', 500,
                                              named=True, weight_field='w')
            self.assertEqual(len(route), len(set(route)))
            self.assertEqual(len(route), 4)
            self.assertEqual(route, ['N0', 'N1', 'N3', 'N5'])

    def test_random_route_walk_visited_nodes_are_correct(self):
        g = self.random_walk_route_test_graph()
        g.add_edges([['N4', 'N3'], ])
        weights = [2, 1000, 1, 0, 5, 1000, 0, 1]
        g.es['w'] = weights
        for prob in xrange(0, 1000):
            route = helpers.random_route_walk(g, 'N0', 'N5', 500,
                                              named=True, weight_field='w')
            self.assertEqual(len(route), len(set(route)))
            self.assertTrue(4 <= len(route) <= 5)
            self.assertIn(route, [['N0', 'N1', 'N3', 'N5'],
                                  ['N0', 'N1', 'N4', 'N3', 'N5']])

    def test_random_route_walk_double_step_back(self):
        g = self.random_walk_route_test_graph()
        g.add_edges([['N4', 'N3'], ])
        weights = [1, 1, 3, 10, 1000, 1000, 2, 0]
        g.es['w'] = weights
        g.delete_edges([(g.vs.find('N5').index, g.vs.find('N4').index),
                        (g.vs.find('N5').index, g.vs.find('N3').index)])
        for prob in xrange(0, 1000):
            route = helpers.random_route_walk(g, 'N0', 'N3', 10,
                                              named=True, weight_field='w')
            self.assertEqual(len(route), len(set(route)))
            self.assertEqual(len(route), 3)
            self.assertEqual(route, ['N0', 'N1', 'N3'])
if __name__ == '__main__':
    unittest.main()
