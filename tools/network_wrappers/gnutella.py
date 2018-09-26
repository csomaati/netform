import igraph as i


def load_topology(edge_list_path):
    foodweb = i.read(edge_list_path, format="edgelist")
    foodweb.vs['name'] = ['FW%d' % v.index for v in foodweb.vs]
    foodweb.simplify()
    return foodweb
