import igraph


def get_traceroutes(path):
    traceroutes = []
    with open(path) as f:
        for line in f:
            hops = line.strip().split(' ')
            hops = tuple(['AS%s' % x for x in hops])
            traceroutes.append(hops)

    traceroutes = list(set(traceroutes))
    return traceroutes


def load_topology(path):
    raise NotImplementedError('Not implemented yet')
