import sys
sys.path.append("..")

# import copy
import re
import igraph
import logging
import itertools
from tools import helpers, misc
import tools.progressbar1 as progressbar1
import csv
import xml.dom.minidom
from collections import Counter

misc.logger_setup()
logger = logging.getLogger('compnet.metabolic_logger')
# np.set_printoptions(precision=2)

PATHWAYS, COMMONNAME, INPATHWAY, REACTIONLIST, SUBPATHWAYS = range(0, 5)
REACTION, ECNUMBER, LEFT, RIGHT, OBJECTID, DIRECTION = range(0, 6)
NAME, REACTIONLIST, FRAMEID, SUBPATHWAYS, REACTIONLAYOUT, NAMES = range(0, 6)
# NAME MAP
NAME, COMMONNAME, FRAMEID, NAMES, SYNONYMS = range(0, 5)


def template2(text, map_words):
    for i, j in map_words.iteritems():
        text_o = text
        text = text.replace(i, j)
        if text_o != text:
            print '%s to %s' % (i, j)
    return text


def template(str, vars):
    rep = dict((re.escape(k), v) for k, v in vars.iteritems())
    pattern = re.compile("|".join(rep.keys()))
    str = pattern.sub(lambda m: rep[re.escape(m.group(0))], str)
    return str


def reaction_layout_split(path):
    reactionpairs = path[REACTIONLIST][2:-2].split('" "')
    rpl = '|'.join([re.escape(x) for x in reactionpairs]) 
    results = re.split(rpl+'|LEFT-PRIMARIES|DIRECTION|RIGHT-PRIMARIES', path[REACTIONLAYOUT])
    results = [x for x in results if len(x) > 0]
    results = zip(*[iter(results)]*3)
    return results


def is_valid_path(path):
    hops = zip(path, path[1:])
    for hop in hops:
        if len(set(hop[0][1]) & set(hop[1][0])) == 0:
            return False
    return True


def path_shuffle(path):
    valid_paths = []
    for mask in itertools.product(range(2), repeat=len(path)):
        path_candidate = path[:]
        for (idx, state) in enumerate(mask):
            if state == 0: continue
            A = path_candidate[idx]
            path_candidate[idx] = [A[1], A[0]]

        if is_valid_path(path_candidate):
            valid_paths.append(path_candidate)

    return valid_paths

# == FILES == #
all_reaction_file = 'all_reactions.csv'
# pathways_file = 'pathways.csv'
pathways_file = 'pathway_query.tsv'
compound_name_file = 'compound_name_map.tsv'
protein_name_file = 'protein_name_map.tsv'
reaction_layout_xml = 'reaction_layout.xml'

reactions = helpers.import_csv_file_as_list(all_reaction_file, ';')
reactions = reactions[1:]         # remove header
for reaction in reactions:
    reaction[LEFT] = reaction[LEFT].split(' // ')
    reaction[RIGHT] = reaction[RIGHT].split(' // ')

reaction_map = {x[REACTION]: x for x in reactions}

all_edges = []
for reaction in reactions:
    left = reaction[LEFT]
    right = reaction[RIGHT]
    # direction = reaction[DIRECTION] if reaction[DIRECTION] else 'REVERSIBLE'
    # if 'RIGHT-TO-LEFT' in direction:
    #     left, right = right, left
    edges = list(itertools.product(left, right))
    # if 'REVERSIBLE' in direction:
    #     edges = list(itertools.product(right, left))
    all_edges.extend(edges)

reaction_edges = (dict(source=s, target=t)
                       for s, t in all_edges)
reaction_graph = igraph.Graph.DictList(edges=reaction_edges, vertices=None, directed=False)
reaction_graph.simplify()


compound_name_db = helpers.import_csv_file_as_list(compound_name_file, '\t')
for compound in compound_name_db:
    compound[NAMES] = compound[NAMES][2:-2].split('" "')
    compound[SYNONYMS] = compound[SYNONYMS][2:-2].split('" "')

protein_name_db = helpers.import_csv_file_as_list(protein_name_file, '\t')
for protein in protein_name_db:
    protein[NAMES] = protein[NAMES][2:-2].split('" "')
    protein[SYNONYMS] = protein[SYNONYMS][2:-2].split('" "')

rename_map = dict()
for element in compound_name_db + protein_name_db:
    mapit = set(element[NAMES] + element[SYNONYMS])
    rename_map.update({x: element[FRAMEID] for x in mapit})


DOMTree = xml.dom.minidom.parse(reaction_layout_xml)
pathways_xml = DOMTree.documentElement.getElementsByTagName('Pathway')


# Keressuk meg a primarie elemeket, hogy torolhessuk a tobbit a reaction graphbol
primaries = []
for path in pathways_xml:
    pw_id = path.getAttribute('frameid')
    layouts = path.getElementsByTagName('reaction-layout')
    orderings = path.getElementsByTagName('reaction-ordering')
    subpws = path.getElementsByTagName('sub-pathways')

    if len(layouts) == 0 or len(orderings) == 0 or len(subpws) > 0:
        # logger.warn('No layout or ordering or has subpthw')
        continue

    for layout in layouts:
        left_primaries_xml = layout.getElementsByTagName('left-primaries')[0].childNodes
        right_primaries_xml = layout.getElementsByTagName('right-primaries')[0].childNodes
        for left_primarie in left_primaries_xml:
            if left_primarie.nodeType != left_primarie.ELEMENT_NODE: continue
            primaries.append(left_primarie.getAttribute('frameid'))

        for right_primarie in right_primaries_xml:
            if right_primarie.nodeType != right_primarie.ELEMENT_NODE: continue
            primaries.append(right_primarie.getAttribute('frameid'))

primaries = set(primaries)
del_nodes = [x.index for x in reaction_graph.vs if x['name'] not in primaries]
logger.info('Delete %d nodes from reaction graph with %d nodes' % (len(del_nodes),
                                                                   reaction_graph.vcount()))
# for node_idx in del_nodes:
#     node_name = reaction_graph.vs[node_idx]['name']
#     logger.debug('Delete: %s' % node_name)

reaction_graph.delete_vertices(del_nodes)
# raw_input()
inflations = []
for path in pathways_xml:
    pw_id = path.getAttribute('frameid')
    layouts = path.getElementsByTagName('reaction-layout')
    orderings = path.getElementsByTagName('reaction-ordering')
    subpws = path.getElementsByTagName('sub-pathways')

    if len(layouts) == 0 or len(orderings) == 0 or len(subpws) > 0:
        # logger.warn('No layout or ordering or has subpthw')
        continue

    logger.debug('PW: %s' % pw_id)
    edges = []
    reaction_map = dict()
    for layout in layouts:
        reaction_id = layout.getElementsByTagName('Reaction')[0].getAttribute('frameid')
        left = []
        right = []
        left_primaries_xml = layout.getElementsByTagName('left-primaries')[0].childNodes
        right_primaries_xml = layout.getElementsByTagName('right-primaries')[0].childNodes
        for left_primarie in left_primaries_xml:
            if left_primarie.nodeType != left_primarie.ELEMENT_NODE: continue
            left.append(left_primarie.getAttribute('frameid'))

        for right_primarie in right_primaries_xml:
            if right_primarie.nodeType != right_primarie.ELEMENT_NODE: continue
            right.append(right_primarie.getAttribute('frameid'))

        direction = layout.getElementsByTagName('direction')[0].childNodes[0].data

        if direction == 'R2L':
            left, right = right, left

        reaction_map[reaction_id] = {
            'LEFT': left,
            'RIGHT': right
        }
        prod_edges = list(itertools.product(left, right))
        edges.extend(prod_edges)
        # logger.debug('INNER: %s' % prod_edges)

    for ordering in orderings:
        reaction_id = ordering.getElementsByTagName('Reaction')[0].getAttribute('frameid')
        predecessor_id = ordering.getElementsByTagName('predecessor-reactions')[0].getElementsByTagName('Reaction')[0].getAttribute('frameid')
        ordering_edge = list(itertools.product(reaction_map[predecessor_id]['RIGHT'], reaction_map[reaction_id]['LEFT']))
        # logger.debug('ORDERING: %s' % ordering_edge)
        edges.extend(ordering_edge)

    pw_edges = (dict(source=s, target=t)
                for s, t in edges)
    pw_graph = igraph.Graph.DictList(edges=pw_edges, vertices=None, directed=True)
    pw_graph.simplify(multiple=False, loops=True)

    start_nodes = [x['name'] for x in pw_graph.vs if pw_graph.degree(x, mode=igraph.IN) == 0]
    end_nodes = [x['name'] for x in pw_graph.vs if pw_graph.degree(x, mode=igraph.OUT) == 0]

    # logger.debug('IN node: [b]{start}[/], OUT: [g]{out}[/]'.format(start=start_nodes,
    #                                                             out=end_nodes))

    if len(start_nodes) < 1 or len(end_nodes) < 1: continue

    s = start_nodes[0]
    t = end_nodes[0]

    shortest_path = reaction_graph.get_shortest_paths(reaction_graph.vs.find(s),
                                                      reaction_graph.vs.find(t))[0]
    pw_shortest = pw_graph.get_shortest_paths(pw_graph.vs.find(s),
                                              pw_graph.vs.find(t))[0]
    inflation = len(pw_shortest) - len(shortest_path)
    logger.debug('REACTION shortest: %s' % [reaction_graph.vs[x]['name'] for x in shortest_path])
    logger.debug('PW shortest: %s' % [pw_graph.vs[x]['name'] for x in pw_shortest])
    logger.debug('Inflation: %d' % inflation)
    inflations.append(inflation)

    # igraph.plot(pw_graph, vertex_label=pw_graph.vs['name'])
    # pw_graph.simplify()

    # raw_input()

cnt = Counter(inflations)
import numpy as np
import matplotlib.pyplot as plt
print cnt
labels, values = zip(*cnt.items())
indexes = np.arange(len(labels))
width = 1

plt.bar(indexes, values, width)
plt.xticks(indexes + width * 0.5, labels)
plt.show()
raw_input()
rasd()


# pathways = helpers.import_csv_file_as_list(pathways_file, ';')
# pathways = pathways[1:]         # remove header
# pathways = [x for x in pathways if len(x[SUBPATHWAYS]) == 0]
# with open(pathways_file, 'r') as f:
#     content = f.read()
#     modified = template(content, rename_map)
#     with open('/tmp/pw_tmp.csv', 'w') as out:
#         out.write(modified)


pathways = helpers.import_csv_file_as_list(pathways_file, '\t')
# pathways = helpers.import_csv_file_as_list("pw_tmp.csv", '\t')
pathways = [x for x in pathways if len(x[REACTIONLIST]) > 0 and len(x[SUBPATHWAYS]) == 0]

for pidx, pathway in enumerate(pathways):
    print '%d/%d' % (pidx, len(pathways))
    for idx, element in enumerate(pathway):
        pathway[idx] = template(element, rename_map)

# igraph.plot(reaction_graph.clusters().giant())

reaction_graph.save('reaction_graph.gml', format='gml')

for (idx, path) in enumerate(pathways):
    logger.debug('Current pathway: {pathway}'.format(pathway=path[PATHWAYS]))
    path_reactions = path[REACTIONLIST].split(' // ')
    try:
        resolved_path_reactions = [reaction_map[x][:] for x in path_reactions]
    except KeyError as e:
        # logger.warn('Wrong key in pathway {pathway} for reaction {reaction}'.format(pathway=path[PATHWAYS], reaction=e.args[0]))
        continue

    logger.debug('BEFORE: %s' % [[x[LEFT], x[RIGHT]] for x in resolved_path_reactions])

    nodes = ['+'.join(x) for r in resolved_path_reactions for x in [r[LEFT], r[RIGHT]]]
    logger.debug('Nodes: {nodes}'.format(nodes=nodes))

    edges = []
    for r in resolved_path_reactions:
        if r[DIRECTION] in ('RIGHT-TO-LEFT', 'PHYSIOL-RIGHT-TO-LEFT'):
            edges.append([r[RIGHT][0], r[LEFT][0]])
        elif r[DIRECTION] in ('LEFT-TO-RIGHT', 'IRREVERSIBLE-LEFT-TO-RIGHT', 'PHYSIOL-LEFT-TO-RIGHT'):
            edges.append([r[LEFT][0], r[RIGHT][0]])
        elif r[DIRECTION] == 'REVERSIBLE':
            edges.append([r[RIGHT][0], r[LEFT][0]])
            edges.append([r[LEFT][0], r[RIGHT][0]])
            logger.warn('REVERSIBLE')
        else:
            logger.debug('Unkown: %s' % r[DIRECTION])

    current_reaction_edges = (dict(source=s, target=t) for s, t in edges)
    current_reaction_graph = igraph.Graph.DictList(edges=current_reaction_edges, vertices=None, directed=True)
    igraph.plot(current_reaction_graph,
                vertex_label = current_reaction_graph.vs['name'],
                vertex_label_size = 13,
                margin=(150, 50, 150, 50))
    raw_input()

    # valid_paths = path_shuffle([[x[LEFT], x[RIGHT]] for x in resolved_path_reactions])
    # logger.debug('%s' % path[COMMONNAME])
    # logger.debug('AFTER: %s' % valid_paths)
    # logger.debug('LEN: %d' % len(valid_paths))

# import urllib2
# import xml.dom.minidom

# g_p = igraph.load('topo_original.gml')
# pr = [x['name'] for x in g_p.vs]
# g_all = igraph.load('topo_original_notjustprimaries.gml')

# all_c = [x['name'] for x in g_all.vs]
# map_c = {x:{'ECOCYC': x, 'PRIMARY': False} for x in all_c}

# for x in pr:
#     map_c[x]['PRIMARY'] = True

# for idx, x in enumerate(list(map_c.iterkeys())[211:]):
#     print '%d/%d' % (idx, len(map_c)-211)
#     print x
#     f = urllib2.urlopen('http://websvc.biocyc.org/getxml?ECOLI:{cmp}'.format(cmp=x))
#     xmldata = f.read()
#     f.close()

#     print xmldata
    
#     DOMTree = xml.dom.minidom.parseString(xmldata)
#     if len(DOMTree.getElementsByTagName('Error')) > 0:
#         continue
#     try:
#         comp = DOMTree.getElementsByTagName('Compound')[0]
#     except IndexError:
#         try:
#             comp = DOMTree.getElementsByTagName('Protein')[0]
#         except IndexError:
#             comp = DOMTree.getElementsByTagName('RNA')[0]
#     try:
#         common_name = comp.getElementsByTagName('common-name')[0].firstChild.nodeValue
#     except IndexError:
#         common_name = ''
#     synoms = comp.getElementsByTagName('synonym')
#     synonyms = []
#     for syn in synoms:
#         synonyms.append(syn.firstChild.nodeValue)

#     print '{}\t{}\t{}'.format(x, common_name, synonimes)
#     map_c[x]['common_name'] = common_name
#     map_c[x]['synonyms'] = '//'.join(synonyms)

#     del synonyms
#     del synoms
#     del common_name

# with open('out.csv', 'w') as f:
#     f.write('ECOCYC ID;COMMON NAME;SYNONYMS;IS PRIMARY\n')
#     for x in map_c.itervalues():
#         f.write('{ecocyc};{common_name};{syn};{p}\n'.format(ecocyc=x['ECOCYC'],
#                                                             common_name=x.get('common_name', ''),
#                                                             syn = x.get('synonyms', ''),
#                                                             p=x['PRIMARY']))


# black_list = set([x[REACTION] for x in reactions if len(x[DIRECTION]) == 0])

# wrong_list = []
# for path in pathways:
#     path_reactions = path[REACTIONLIST].split(' // ')
#     contains = len(set(path_reactions).intersection(black_list)) > 0
#     if contains: wrong_list.append(path)

# # ATTENTION ACHTUNG
# if len(wrong_list) > 0:
#     logger.warn("""Volt olyan pathway, ami tartalmazott olyan
#                  reakciot, amiknek a ket oldala kozott nem ismert
#                  a kapcsolat. A smart-table = jelet tesz kozejuk,
#                  az exportalt tablazatban viszont uresen hagyja.""")
