from collections import Counter
import xml.dom.minidom
import itertools
import logging
import igraph
import csv
import io

import sys
sys.path.append("..")
from tools import helpers, misc

misc.logger_setup()
logger = logging.getLogger('compnet.metabolic_logger')


def import_csv_file_as_list(fpath, delimiter=','):
    '''Import the lines of a CSV file
    creating a new list element for all new line'''
    loaded = list()
    with io.open(fpath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            loaded.append(row)

    return loaded

PATHWAYS, COMMONNAME, INPATHWAY, REACTIONLIST, SUBPATHWAYS = range(0, 5)
REACTION, ECNUMBER, LEFT, RIGHT, OBJECTID, DIRECTION = range(0, 6)
NAME, REACTIONLIST, FRAMEID, SUBPATHWAYS, REACTIONLAYOUT, NAMES = range(0, 6)
# NAME MAP
NAME, COMMONNAME, FRAMEID, NAMES, SYNONYMS = range(0, 5)

# == FILES == #
all_reaction_file = 'all_reactions.csv'
reaction_layout_xml = 'reaction_layout.xml'

inflations = []
traces = []
# A letoltott reakciok beolvasasa a csv filebol. Ez alapjan lehet
# grafot epiteni a reakciok kozotti kapcsolatokbol
reactions = import_csv_file_as_list(all_reaction_file, ';')
reactions = reactions[1:]         # remove header

# a left es right tartalmazza rogton az elemek listajat
# ne kelljen a stringgel bajlodni kesobb
for reaction in reactions:
    reaction[LEFT] = reaction[LEFT].split(' // ')
    reaction[RIGHT] = reaction[RIGHT].split(' // ')

# A reakcioknak tobb neve is lehet, de van egy egyedi roviditese is
# Vannak olyan tablazataik a biocyc-eseknek, amikben keverik a szininimakat
# a reaction_map minden gyakori nevhez megadja az egyedi roviditest
reaction_map = {x[REACTION]: x for x in reactions}

# A reakciok alapjan itt epitjuk fel a reakcio grafot
all_edges = []
for reaction in reactions:
    left = reaction[LEFT]
    right = reaction[RIGHT]

    # **** Ha iranyitott grafot akarunk, akkor szamit, hogy a reakcio melyik
    # **** iranybol olvasando

    # direction = reaction[DIRECTION] if reaction[DIRECTION] else 'REVERSIBLE'
    # if 'RIGHT-TO-LEFT' in direction:
    #     left, right = right, left
    # if 'REVERSIBLE' in direction:
    #     edges = list(itertools.product(right, left))

    edges = list(itertools.product(left, right))
    all_edges.extend(edges)

# A graf generalasa a korabban kilistazott elek alapjan
reaction_edges = (dict(source=s, target=t)
                       for s, t in all_edges)
reaction_graph = igraph.Graph.DictList(edges=reaction_edges,
                                       vertices=None,
                                       # Ha iranyitott graf kell, akkor True
                                       directed=False)
reaction_graph.simplify()


# Betoltjuk az xml file-t, amiben ott van, hogy a pathway, hogyan epul fel.
# Ebben a fontos elemek a pathway azonositoya, a layout es az ordering.
#  - Az azonositoval a biocyc-en lehet nezegetni, ok hogy jelenitik meg, milyen
#    elemekbol epul fel, stb.
#  - Az ordering megmondja, hogy melyik reakcio melyik utan kovetkezik es milyen
#    iranyitassal. A reakciok az egyedi kodjaikkal vannak azonositva
#  - A layout az egyes reakciokra vonatkozik, szinten a reakcio egyedi
#    azonositojaval nevezi meg. A layout leirja, hogy a reakcio milyen iranyitasu
#    es a ket oldalan mik a primarie anyag(ok). Ezekkel akarunk dolgozni, es
#    eldobni a H2O, H+ es ilyesmi elemeket, amik valoszinuleg csak mellektermekek
#    katalizatorok, ilyesmik (talan)
DOMTree = xml.dom.minidom.parse(reaction_layout_xml)
pathways_xml = DOMTree.documentElement.getElementsByTagName('Pathway')

# Mivel a reakciokbol epitett grafban nem volt jelolve, hogy mi primarie es mi
# nem, ezert a pathwaybol epitkezunk amig nincs jobb. Megkeressuk, hogy kik a
# primarie elemek, es akik nem azok, azokat toroljuk a reakciokbol epitett
# grafbol
primaries = []
for path in pathways_xml:
    # a fontosabb tag-ek
    pw_id = path.getAttribute('frameid')
    layouts = path.getElementsByTagName('reaction-layout')
    orderings = path.getElementsByTagName('reaction-ordering')
    subpws = path.getElementsByTagName('sub-pathways')

    # Ha nincs layout vagy ordering, akkor nem tudunk vele mit kezdeni
    # lehet csak egy josolt pathway. Ha van subphwy, akkor meg superpathway,
    # amivel most nem kezdunk semmit, mert azokat ossze kellene mergelni
    # a gyerekeivel, ami future work
    if len(layouts) == 0 or len(orderings) == 0 or len(subpws) > 0:
        # logger.warn('No layout or ordering or has subpthw')
        continue

    # Left es Right primariek kinyerese. Most csak az elemek listaja erdekel,
    # az iranyitas nem fontos. A lista kell, hogy kitorljuk a listaban nem
    # szereploket a masik grafbol
    for layout in layouts:
        # childeNodes a vegen, mert lehet compound, enzime, rns, stb. lsd xml file
        left_primaries_xml = layout.getElementsByTagName('left-primaries')[0].childNodes
        right_primaries_xml = layout.getElementsByTagName('right-primaries')[0].childNodes
        for left_primarie in left_primaries_xml:
            if left_primarie.nodeType != left_primarie.ELEMENT_NODE: continue
            primaries.append(left_primarie.getAttribute('frameid'))

        for right_primarie in right_primaries_xml:
            if right_primarie.nodeType != right_primarie.ELEMENT_NODE: continue
            primaries.append(right_primarie.getAttribute('frameid'))

# Halmaz kepzes, hogy kivegyuk a duplikatumokat
primaries = set(primaries)
# Mik azok az elemek, akik benne vannak a reakcios grafban, de nem priamriek
# a pathway-ek alapjan
del_nodes = [x.index for x in reaction_graph.vs if x['name'] not in primaries]
logger.info('Delete %d nodes from reaction graph with %d nodes' % (len(del_nodes),
                                                                   reaction_graph.vcount()))

# A 'felesleges' elemek torlese
reaction_graph.delete_vertices(del_nodes)

# Nem tul elegans megoldas, de a sietseg ilyen kodokat szul :)
# Ismet nekifutunk az xml filenak, es beolvassuk a pathwayeket
# Most mar figyelunk a reakciok kozti iranyokra, illetve a reakciokon beluli
# iranyitasokra is. Nem mindegy, ki van a reakcio jobb vagy baloldali primarie
# elemekent megjelolve. Az otlet az, hogy az iranyitott reakcioparok egy grafot
# adnak. A reakciokat feloldva azkon belul a konkret elemek kozotti
# kolcsonhatast vehetjuk ki a left es right primaries mezokbol. Az elemek
# lesznek a node-ok. Minden olyan node, amibe nem fut el, az egy kiindulo elem.
# Minden olyan, amibol nem fut ki el, az a vegtermek. Lehet tobb kiindulasi pont
# es valoszinuleg tobb vegtermek is. Lehetnek korok is, ahol nincs egy ilyen
# elem sem. A kod nem fool-proof, vannak/lehetnek benne hibak, kell meg
# vele szoszolni.
for path in pathways_xml:
    pw_id = path.getAttribute('frameid')
    layouts = path.getElementsByTagName('reaction-layout')
    orderings = path.getElementsByTagName('reaction-ordering')
    subpws = path.getElementsByTagName('sub-pathways')

    if len(layouts) == 0 or len(orderings) == 0 or len(subpws) > 0:
        # logger.warn('No layout or ordering or has subpthw')
        continue

    # Ha gond van, akkor erre rakereshetunk a biocyc adatbazisban.
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

        # Az irany adja meg, hogy meg kell-e cserelni az elemeket.
        # Az xml-ben bidirectional vagy reversible nem kerult a szemem ele,
        # valoszinuleg a pathwayen belul egyertelmu az iranyitottsaga, de
        # errol majd meg kell kerdezni egy expertet
        # TODO: ask an expert ;)
        direction = layout.getElementsByTagName('direction')[0].childNodes[0].data

        # Igrah balrol jobbra veszi az iranyt ellista eseten. Tehat ha megadunk
        # egy [A, B] elt egy iranyitott grafban, akkor kihuz egy A->B-t
        if direction == 'R2L':
            left, right = right, left

        if direction != 'R2L' and direction != 'L2R':
            logger.warn('Unknown direction {d}'.format(d=direction))

        reaction_map[reaction_id] = {
            'LEFT': left,
            'RIGHT': right
        }
        prod_edges = list(itertools.product(left, right))
        edges.extend(prod_edges)
        # logger.debug('INNER: %s' % prod_edges)

    # Az ordering alapjan rendezzuk egymas utan a reakciokban a vegtermekeket
    # a pathway kovetkezo 'hopjan' a kezdotermekkel. Altalaban a ketto
    # megegyezik, tehat az egyik reakcio vegtermeke egyben a kovetkezo inputja
    # de vannak, amik tobb reakcio vegetermeket hasznaljak fel, vagy tobb
    # vegtermek van, es mashol hasznosulnak (talan)
    # Ha a vegtermek es az input azonos, ez a grafban egy self-loop kepeben
    # jelenik meg (B->B), de ez nem gond, az igraph ad egy fuggvenyt ezek gyors
    # eltavolitasara
    for ordering in orderings:
        reaction_id = ordering.getElementsByTagName('Reaction')[0].getAttribute('frameid')
        predecessor_id = ordering.getElementsByTagName('predecessor-reactions')[0].getElementsByTagName('Reaction')[0].getAttribute('frameid')
        # Minden kezdo elem jobb oldalat minden kovetkezo reakcio bal oldalaval
        # osszekotunk elso kozelitesben, mert 'lattunk' utat.
        ordering_edge = list(itertools.product(reaction_map[predecessor_id]['RIGHT'], reaction_map[reaction_id]['LEFT']))
        # logger.debug('ORDERING: %s' % ordering_edge)
        edges.extend(ordering_edge)

    # Graf gyartasa az elek alapjan
    pw_edges = (dict(source=s, target=t)
                for s, t in edges)
    pw_graph = igraph.Graph.DictList(edges=pw_edges, vertices=None, directed=True)

    # Self-loopok torlese
    pw_graph.simplify(multiple=False, loops=True)

    # Keressuk ki az osszes elemet, ami nem valami outputja volt
    start_nodes = [x['name'] for x in pw_graph.vs if pw_graph.degree(x, mode=igraph.IN) == 0]
    # Es az osszeset, ami nem valami inputja
    end_nodes = [x['name'] for x in pw_graph.vs if pw_graph.degree(x, mode=igraph.OUT) == 0]

    # logger.debug('IN node: [b]{start}[/], OUT: [g]{out}[/]'.format(start=start_nodes,
    #                                                             out=end_nodes))

    # Ha nincsenek kezdo- es vegpontok, akkor kor volt, vagy ilyesmi. Egyelore
    # nem erdekelnek minket
    if len(start_nodes) < 1 or len(end_nodes) < 1: continue

    # Osszes pontpar generalasa
    pointpairs = list(itertools.product(start_nodes, end_nodes))
    # s = start_nodes[0]
    # t = end_nodes[0]

    for s, t in pointpairs:

        # Legrovidebb elerheto 'elmeleti' ut a reakciok kozott kapcsolatokon
        # keresztul
        # Mivel s es t a reakciok egyedi azonositoja, az igraph meg a grafon beluli
        # indexeket var - ami grafok kozott elterhet azonos nevu csomopontokra -
        # ezert a find segitsegevel megkeressuk a nevhez tartozo indexet.
        shortest_path = reaction_graph.get_shortest_paths(reaction_graph.vs.find(s),
                                                          reaction_graph.vs.find(t))[0]


        # Es a legrovidebb ut a pathwayen keresztul.
        pw_shortest = pw_graph.get_all_shortest_paths(pw_graph.vs.find(s),
                                                      pw_graph.vs.find(t))

        if len(pw_shortest) == 0 or len(pw_shortest[0]) == 0:
            logger.warn('No route between {s}-{t} in {pw}'.format(s=s,
                                                                  t=t,
                                                                  pw=pw_id))
            continue

        # A nyulas a ketto kulonbsege. Egyelore vannak negativak, el kell
        # gondolkozni miert, mert nem csak diszjunkt utakbol allo pathwayek miatt.
        inflation = len(pw_shortest[0]) - len(shortest_path)
        inflations.append(inflation)

        if inflation >= 0:
            traces.extend(pw_shortest)
        logger.debug('REACTION shortest: %s' % [reaction_graph.vs[x]['name'] for x in shortest_path])
        logger.debug('PW shortest: %s' % [pw_graph.vs[x]['name'] for x in pw_shortest])
        logger.debug('Inflation: %d' % inflation)

    # igraph.plot(pw_graph, vertex_label=pw_graph.vs['name'])
    # pw_graph.simplify()

    # raw_input()

# # save traceroutes
# helpers.save_to_json('ecoli_traceroutes_nonegativeinflation.json', traces)
# # save reaction network
# igraph.save(reaction_graph, 'reaction_undirected.gml')

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
