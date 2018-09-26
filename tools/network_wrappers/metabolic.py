import xml.dom.minidom
import itertools
import logging
import igraph
from tools import helpers
import copy

PATHWAYS, COMMONNAME, INPATHWAY, REACTIONLIST, SUBPATHWAYS = range(0, 5)
REACTION, ECNUMBER, LEFT, RIGHT, OBJECTID, DIRECTION = range(0, 6)
NAME, REACTIONLIST, FRAMEID, SUBPATHWAYS, REACTIONLAYOUT, NAMES = range(0, 6)
# NAME MAP
NAME, COMMONNAME, FRAMEID, NAMES, SYNONYMS = range(0, 5)
logger = logging.getLogger('netform.metabolic')


# Bad node list based on iJO1366_cofactors.txt
# from latter 'Fwd: Re: Fw: metabolikus halozat utvonalai'
# resolved by ecocyc.org at 2016.08.15
BAD_NODES = ['10-FORMYL-THF', 'DEMETHYLMENAQUINONE', 'CPD-12115', 'ACP', 'ADP',
             'ADENOSYL-HOMO-CYS', 'AMP', 'ATP', 'CARBON-DIOXIDE', 'CO-A',
             'DSBDOXI-MONOMER', 'DSBD-MONOMER', 'FAD', 'FADH2', 'FE+2', 'FE+3',
             'EG10628', 'FMN', 'FMNH2', 'Ox-Glutaredoxins',
             'Red-Glutaredoxins', 'PROTON', 'WATER', 'HYDROGEN-PEROXIDE',
             'LYS', 'REDUCED-MENAQUINONE', 'CPD-9728', 'NAD', 'NADH', 'NADP',
             'NADPH', 'AMMONIUM', 'OXYGEN-MOLECULE', 'Pi', 'PPI', 'P3I',
             'UBIQUINONE-8', 'CPD-9956', 'CPD-316', 'RIBOFLAVIN', 'SO3', 'THF',
             'OX-THIOREDOXIN-MONOMER', 'Red-Thioredoxin']


def clean_graph(g):
    reaction_graph = copy.deepcopy(g)
    # A biologusok altal kuldott csomopontok torlese
    bad_nodes_idx = []
    for bn in BAD_NODES:
        try:
            bad_nodes_idx.append([reaction_graph.vs.find(x).index for x in bn])
        except ValueError:
            pass

    reaction_graph.delete_vertices(bad_nodes_idx)
    return reaction_graph


def load_topology(all_reaction_file, reaction_layout_xml):
    # A letoltott reakciok beolvasasa a csv filebol. Ez alapjan lehet
    # grafot epiteni a reakciok kozotti kapcsolatokbol
    reactions = helpers.import_csv_file_as_list(all_reaction_file, ';')
    reactions = reactions[1:]         # remove header

    # a left es right tartalmazza rogton az elemek listajat
    # ne kelljen a stringgel bajlodni kesobb
    for reaction in reactions:
        reaction[LEFT] = reaction[LEFT].split(' // ')
        reaction[RIGHT] = reaction[RIGHT].split(' // ')

    # A reakciok alapjan itt epitjuk fel a reakcio grafot
    all_edges = []
    for reaction in reactions:
        left = reaction[LEFT]
        right = reaction[RIGHT]

        # **** Ha iranyitott grafot akarunk, akkor szamit,
        # **** hogy a reakcio melyik iranybol olvasando

        # direction = reaction[DIRECTION] if reaction[DIRECTION] else 'REVERSIBLE'
        # if 'RIGHT-TO-LEFT' in direction:
        #     left, right = right, left
        # if 'REVERSIBLE' in direction:
        #     edges = list(itertools.product(right, left))

        edges = list(itertools.product(left, right))
        all_edges.extend(edges)

    # A graf generalasa a korabban kilistazott elek alapjan
    reaction_edges = (dict(source=s, target=t) for s, t in all_edges)
    reaction_graph = igraph.Graph.DictList(edges=reaction_edges,
                                           vertices=None,
                                           # Ha iranyitott graf kell: True
                                           directed=False)
    reaction_graph.simplify()

    primaries = get_traceroutes(reaction_layout_xml, return_primaries=True)

    # Halmaz kepzes, hogy kivegyuk a duplikatumokat
    primaries = set(primaries)
    # Mik azok az elemek, akik benne vannak a reakcios grafban, de nem
    # primaries-ek a pathway-ek alapjan
    del_nodes = [x.index for x in reaction_graph.vs
                 if x['name'] not in primaries]
    log_msg = 'Delete {count} nodes from reaction graph with {vcount} nodes'
    log_msg.format(count=len(del_nodes), vcount=reaction_graph.vcount())
    logger.info(log_msg)

    # A 'felesleges' elemek torlese
    # reaction_graph.delete_vertices(del_nodes)

    reaction_graph = clean_graph(reaction_graph)

    # loopok es parhuzamos elek torlese
    reaction_graph.simplify()

    return reaction_graph


def get_traceroutes(reaction_layout_xml, return_primaries=False):

    traceroutes = []
    primaries = []

    # Betoltjuk az xml file-t, amiben ott van, hogy a pathway, hogyan epul fel.
    # Ebben a fontos elemek a pathway azonositoja, a layout es az ordering.
    #  - Az azonositoval a biocyc-en lehet nezegetni, ok hogy jelenitik meg,
    #    milyen elemekbol epul fel, stb.
    #  - Az ordering megmondja, hogy melyik reakcio melyik utan kovetkezik es
    #    milyen iranyitassal. A reakciok az egyedi kodjaikkal vannak azonositva
    #  - A layout az egyes reakciokra vonatkozik, szinten a reakcio egyedi
    #    azonositojaval nevezi meg. A layout leirja, hogy a reakcio milyen
    #    iranyitasu es a ket oldalan mik a primarie anyag(ok). Ezekkel akarunk
    #    dolgozni, es eldobni a H2O, H+ es ilyesmi elemeket, amik valoszinuleg
    #    csak mellektermekek katalizatorok, ilyesmik (talan)
    #
    # Nem mindegy, ki van a reakcio jobb vagy baloldali primarie elemekent
    # megjelolve. Az otlet az, hogy az iranyitott reakcioparok egy grafot
    # adnak. A reakciokat feloldva azkon belul a konkret elemek kozotti
    # kolcsonhatast vehetjuk ki a left es right primaries mezokbol. Az elemek
    # lesznek a node-ok. Minden olyan node, amibe nem fut el, az egy kiindulo
    # elem. Minden olyan, amibol nem fut ki el, az a vegtermek. Lehet tobb
    # kiindulasi pont es valoszinuleg tobb vegtermek is. Lehetnek korok is,
    # ahol nincs egy ilyen elem sem. A kod nem fool-proof, vannak/lehetnek
    # benne hibak, kell meg vele szoszolni.
    DOMTree = xml.dom.minidom.parse(reaction_layout_xml)
    pathways_xml = DOMTree.documentElement.getElementsByTagName('Pathway')

    for path in pathways_xml:
        pw_id = path.getAttribute('frameid')
        layouts = path.getElementsByTagName('reaction-layout')
        orderings = path.getElementsByTagName('reaction-ordering')
        subpws = path.getElementsByTagName('sub-pathways')

        if len(layouts) == 0 or len(orderings) == 0 or len(subpws) > 0:
            logger.warn('No layout or ordering or has subpthw')
            continue

        # Ha gond van, akkor erre rakereshetunk a biocyc adatbazisban.
        logger.debug('PW: %s' % pw_id)
        edges = []
        reaction_map = dict()
        for layout in layouts:
            new_edges, new_reaction_map = _layout_edges(layout)
            reaction_map.update(new_reaction_map)
            edges.extend(new_edges)
            primaries.extend([y for x in new_edges for y in x])

        # Az ordering alapjan rendezzuk egymas utan a reakciokban a
        # vegtermekeket a pathway kovetkezo 'hopjan' a kezdotermekkel.
        # Altalaban a ketto megegyezik, tehat az egyik reakcio vegtermeke
        # egyben a kovetkezo inputja de vannak, amik tobb reakcio vegetermeket
        # hasznaljak fel, vagy tobb vegtermek van, es mashol hasznosulnak
        # (talan) Ha a vegtermek es az input azonos, ez a grafban egy self-loop
        # kepeben jelenik meg (B->B), de ez nem gond, az igraph ad egy
        # fuggvenyt ezek gyors eltavolitasara
        for ordering in orderings:
            new_edges = _ordering_edges(ordering, reaction_map)
            edges.extend(new_edges)

        # Graf gyartasa az elek alapjan
        pw_edges = (dict(source=s, target=t) for s, t in edges)
        pw_graph = igraph.Graph.DictList(edges=pw_edges,
                                         vertices=None,
                                         directed=True)

        # Self-loopok torlese
        pw_graph.simplify(multiple=False, loops=True)

        # Keressuk ki az osszes elemet, ami nem valami outputja volt
        start_nodes = [x['name'] for x in pw_graph.vs
                       if pw_graph.degree(x, mode=igraph.IN) == 0]

        # Es az osszeset, ami nem valami inputja
        end_nodes = [x['name'] for x in pw_graph.vs
                     if pw_graph.degree(x, mode=igraph.OUT) == 0]

        # Ha nincsenek kezdo- es vegpontok, akkor kor volt, vagy ilyesmi.
        # Egyelore nem erdekelnek minket
        if len(start_nodes) < 1 or len(end_nodes) < 1: continue

        # Osszes pontpar generalasa
        pointpairs = list(itertools.product(start_nodes, end_nodes))

        for s, t in pointpairs:
            # Es a legrovidebb utak a pathwayen keresztul.
            pw_shortests = pw_graph.get_all_shortest_paths(pw_graph.vs.find(s),
                                                           pw_graph.vs.find(t))

            if len(pw_shortests) == 0 or len(pw_shortests[0]) == 0:
                log_msg = 'No route between {s}-{t} in {pw}'
                log_msg.format(s=s, t=t, pw=pw_id)
                logger.warn(log_msg)
                continue

            pw_reactions_with_name = [tuple(pw_graph.vs[x]['name'] for x in y)
                                      for y in pw_shortests]
            logger.debug('PW shortest: {sh}'.format(sh=pw_reactions_with_name))

            traceroutes.extend(pw_reactions_with_name)

    ret = traceroutes
    if return_primaries:
        ret = primaries

    return ret


def _ordering_edges(ordering, reaction_map):
    reaction_tag = ordering.getElementsByTagName('Reaction')[0]
    reaction_id = reaction_tag.getAttribute('frameid')
    predecessor_tag = ordering.getElementsByTagName('predecessor-reactions')[0]
    pre_reaction_tag = predecessor_tag.getElementsByTagName('Reaction')[0]
    predecessor_id = pre_reaction_tag.getAttribute('frameid')
    # Minden kezdo elem jobb oldalat minden kovetkezo reakcio bal oldalaval
    # osszekotunk elso kozelitesben, mert 'lattunk' utat.
    predecessor_output = reaction_map[predecessor_id]['RIGHT']
    reaction_input = reaction_map[reaction_id]['LEFT']
    ordering_edges = list(itertools.product(predecessor_output,
                                            reaction_input))
    logger.debug('ORDERING EDGES: {e}'.format(e=ordering_edges))
    return ordering_edges


def _layout_edges(layout):
    reaction_map = dict()
    left, right = [], []

    reaction_tag = layout.getElementsByTagName('Reaction')[0]
    reaction_id = reaction_tag.getAttribute('frameid')
    left_primaries_tag = layout.getElementsByTagName('left-primaries')[0]
    left_primaries_xml = left_primaries_tag.childNodes
    right_primaries_tag = layout.getElementsByTagName('right-primaries')[0]
    right_primaries_xml = right_primaries_tag.childNodes

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
        logger.warn('Unknown direction {d} in {r_id}'.format(d=direction,
                                                             r_id=reaction_id))

    reaction_map[reaction_id] = {
        'LEFT': left,
        'RIGHT': right
    }

    prod_edges = list(itertools.product(left, right))
    logger.debug('INNER EDGES in {reaction}: {e}'.format(reaction=reaction_id,
                                                         e=prod_edges))
    return prod_edges, reaction_map
