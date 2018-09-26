import igraph as i


def get_traceroutes(adj_matrix_path):
    g = load_topology(adj_matrix_path)
    return create_traceroutes(g)


def load_topology(adj_matrix_path):
    foodweb = i.read(adj_matrix_path, format="adjacency")
    foodweb.vs['name'] = ['FW%d' % v.index for v in foodweb.vs]
    foodweb.simplify()
    return foodweb


def create_traceroutes(foodweb):
    print 'Create traceroutes from adj matrix'
    all_path = list()

    for v in foodweb.vs:
        shortest_paths = foodweb.get_all_shortest_paths(v)
        # shortest_paths = [x for x in shortest_paths if len(x) > 2]
        shortest_paths = [(foodweb.vs.find(y)['name'] for y in x)
                          for x in shortest_paths]
        # print shortest_paths
        all_path.extend(shortest_paths)

    all_path = list(set(all_path))

    return all_path
