import igraph as i
import collections

BACK_CLICK = '<'
(HASHEDIPADDRESS, TIMESTAMP, DURATIONINSEC, PATH, RATING) = range(0, 5)


def get_traceroutes(plain_text_path):
    all_path = []
    users = {}
    # alltime = []
    with open(plain_text_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith('#'): continue
            if len(line) < 1: continue

            struct = line.split('\t')
            # alltime.append(int(struct[DURATIONINSEC]))
            # if int(struct[DURATIONINSEC]) > 150: continue
            path = wiki_parse_path(struct[PATH])
            if len(path) == 1: continue
            try:
                userdata = users[struct[HASHEDIPADDRESS]]
            except KeyError:
                userdata = []
                users[struct[HASHEDIPADDRESS]] = userdata

            userdata.append([struct[TIMESTAMP], path,
                             int(struct[DURATIONINSEC])])

    # c = collections.Counter([len(x) for x in users.itervalues()])
    # keys = sorted([x for x in c])
    # for k in keys:
    #     print '%d: %d' % (k, c[k])

    for userid in users:
        userdata = users[userid]
        if len(userdata) > 1000: continue
        userdata = sorted(userdata, key=lambda x: x[0])
        userdata = userdata[30:]
        if len(userdata) == 0: continue
        userdata = [x[1] for x in userdata if (x[2] / float(len(x[1]))) <= 20]
        all_path.extend(userdata[10:])

    # print sum(alltime)
    # print sum(alltime)/float(len(alltime))

    return all_path


def load_topology(edge_list_file):
    edges = []
    with open(edge_list_file) as f:
        for line in f:
            line = line.strip()
            if line.startswith('#'): continue
            if len(line) < 1: continue

            edge = line.split('\t')
            edges.append(dict(source=edge[0],
                              target=edge[1]))
    wiki_net = i.Graph.DictList(edges=edges, vertices=None, directed=True)

    return wiki_net


def wiki_parse_path(path):
    steps = path.split(';')
    real_steps = []
    for step in steps:
        if step == BACK_CLICK:
            del real_steps[-1]
            continue
        real_steps.append(step)

    return real_steps
