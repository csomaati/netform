#!/usr/bin/evn python
# -*- coding: utf-8 -*-

# A program celja konverzios lehetoseg nyujtani a kulonbozo forrasokbol
# rendelkezesre allo, halozati strukturara vagy azokon vegzett utvonalvalasztasi
# meresekre vonatkozo adatoknak. Ezen felul elvegzi a halozat eleinek
# CUSTOMER es PEER cimkezeset is a kivalasztott algoritmussal.
#
# A kesobbi meresek megkonnyitese vegett minden meresi gyujtemenyen el kell vegezni
# a konverziot, hogy a kesobbiekben a forrasoktol fuggetlen, egyseges formaban
# alljon rendelkezesre minden halozat es minden utvonalvalasztasi meres.
# Ezzel eklerulheto a kod duplikalas, es a halozatok kulonbozosegebol
# fakado hibak tovabbgyuruzese, ami akar elronthatna az eredmenyek
# osszehasonlithatosagat.
#
# A program lehetoseget biztosit kulonbozo tipusu el cimkezesekre es
# lehetoseg van a halozati topologiak es a halozati mersek fuggetlen vagy
# futasido csonkentese vegett akar egyideju futtatasara is.

from tools.network_wrappers import (internet, foodweb, airport, text, wiki,
                                    metabolic, gnutella, wordnavi)
from tools import helpers, misc
import argparse_general
from enum import Enum
import argparse
import logging
import sys
import igraph


class Networks(Enum):
    foodweb = 0,
    airport = 1,
    internet = 2,
    weibo = 3,
    text = 4,
    wiki = 5,
    metabolic = 6,
    gnutella = 7,
    wordnavi = 8


misc.logger_setup()
logger = logging.getLogger('compnet.converter')
logging.getLogger('compnet').setLevel(logging.INFO)

formatter = argparse.ArgumentDefaultsHelpFormatter
parser = argparse.ArgumentParser(
    description=('Convert different '
                 'network sources '
                 'to quickly parsable '
                 'and humanly readable format.'),
    parents=[argparse_general.commonParser, ],
    **argparse_general.commonParams)

parser.add_argument(
    '--type', '-t', default='foodweb', choices=[x.name for x in Networks])

parser.add_argument(
    '--convert',
    default='network,traceroutes',
    # type=lambda x: sorted(x.split(',')),
    choices=[
        'network', 'traceroutes', 'topology', 'labeling', 'network,traceroutes'
    ],
    help=('Possible values: '
          '{network|traceroutes|topology|labeling|', 'network,traceroutes}\n',
          'network - convert network using caida labeling\n',
          'traceroutes - save traceroutes to the stdrd format\n',
          'topology - save network to gml format using '
          'method selected with topo-source\n',
          'labeling - relabel with ranking method a graph ',
          'created with caida labeling'))

parser.add_argument(
    '--json-traces',
    dest='json_traces',
    help=('Point to the file where traceroutes '
          'should be saved (consider as a traceroutes_output) '
          'or should be read by '
          'network converter (consider as network_input)'))
parser.add_argument('--traceroutes', '-ti', dest='traceroutes_input')
parser.add_argument('--topology', '-topo', dest='topology')
parser.add_argument(
    '--topo-source',
    dest='topo_source',
    default='inferred',
    choices=['inferred', 'graph', 'traceroutes'],
    help=('mark if topology contains traceroutes or a network'))

parser.add_argument('--network-output', '-no', dest='network_output')
parser.add_argument(
    '--network-cliques',
    dest='network_cliques',
    help=('Point to the file which contains '
          '(in its firs line) the node names(!) '
          'for clique nodes'))
parser.add_argument(
    '--caida-folder',
    dest='caida_folder',
    help=('Point to the folder where '
          'edge labeling caida perl script located'))

# parser.add_argument('--peer-treshold', dest='peer_treshold', default=1.0,
#                     type=float,
#                     help=('Add the percentage value relative to max degree '
#                           'from which nodes with higher degree '
#                           'need to be connected with peer link'))

# parser.add_argument('--vfmode',
#                     default='prelabeled', choices=['prelabeled','closeness'],
#                     dest='vfmode')

parser.add_argument(
    'logfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)

arguments = parser.parse_args()

if arguments.logfile is not sys.stdout:
    sys.stdout = arguments.logfile

arguments.verbose = min(len(helpers.LEVELS), arguments.verbose)
logging.getLogger('compnet').setLevel(helpers.LEVELS[arguments.verbose])

arguments.convert = arguments.convert.split(',')
arguments.type = Networks[arguments.type]

# pre check
if 'network' in arguments.convert and arguments.caida_folder is None:
    logger.error(
        'Pleas add caida folder argument if network converson selected')
    exit()

if ('network' in arguments.convert and
    (arguments.json_traces is None or arguments.network_output is None)):
    logger.error(('Network descriptor as an input file or the name',
                  ' for the output file is not defined'))
    exit()

if ('traceroutes' in arguments.convert and
    (arguments.traceroutes_input is None or arguments.json_traces is None)):
    logger.error(('Traceroutes\' descriptor as an input file '
                  'or the name for the output file is not defined'))
    exit()

if 'topology' in arguments.convert and arguments.topology is None:
    logger.error('Pleas add topology location if topology converson selected')
    exit()

# if arguments.vfmode == 'closeness':
#     vfmode = vft.CLOSENESS
# elif arguments.vfmode == 'prelabeled':
#     vfmode = vft.PRELABELED
# else:
#     raise RuntimeError('Unhandled mode')

logger.info('Pre check passed')

if "traceroutes" in arguments.convert:
    logger.info('Read traceroutes')
    # read traceroutes with required function
    # and save the traceroutes' list in json format
    if arguments.type == Networks.internet:
        traceroutes = internet.get_traceroutes(arguments.traceroutes_input)
    elif arguments.type == Networks.airport:
        traceroutes = airport.get_traceroutes(arguments.traceroutes_input,
                                              None)
    elif arguments.type == Networks.foodweb:
        traceroutes = foodweb.get_traceroutes(arguments.traceroutes_input)
    elif arguments.type == Networks.weibo:
        pass
    elif arguments.type == Networks.text:
        traceroutes = text.get_traceroutes(arguments.traceroutes_input)
    elif arguments.type == Networks.wiki:
        traceroutes = wiki.get_traceroutes(arguments.traceroutes_input)
    elif arguments.type == Networks.metabolic:
        traceroutes = metabolic.get_traceroutes(arguments.traceroutes_input)
    elif arguments.type == Networks.wordnavi:
        traceroutes = wordnavi.get_traceroutes(arguments.traceroutes_input)
    else:
        raise RuntimeError('Unknown network type')
    msg = 'Save traceroutes to {trace}'.format(trace=arguments.json_traces)
    logger.info(msg)
    helpers.save_to_json(arguments.json_traces, traceroutes)

if "network" in arguments.convert:
    # label network with caida labeling tool
    # first load previously converted traceroutes
    traceroutes = helpers.load_from_json(arguments.json_traces)
    logger.info('Trace count: {c}'.format(c=len(traceroutes)))
    # to increase accuracy
    if arguments.type == Networks.airport:
        traceroutes.extend([[y for y in reversed(x)] for x in traceroutes])

    # convert with caida labeling tools
    logger.info('Caida labeling the graph')
    edge_list = helpers.caida_labeling(arguments.caida_folder, traceroutes,
                                       arguments.network_cliques)

    # save to given output file using caida output format
    logger.info('Save to file %s' % arguments.network_output)
    with open(arguments.network_output, 'w') as f:
        for e in edge_list:
            f.write('%s|%s|%s\n' % (e[0], e[1], e[2]))

    # print_network_statistics(edge_list)

if "topology" in arguments.convert:

    if arguments.topo_source == 'inferred':
        logger.info('Loading inferred graph')
        vs, edges = helpers.load_as_inferred_links(
            arguments.topology, graph=False)
        logger.info('Reranking graph')
        topo = helpers.inferred_links_to_ranked_graph(edges)
        # edge_list = helpers.degree_labeling_network(topo,
        #                                             arguments.peer_treshold,
        #                                             vfmode=vfmode)
    if arguments.topo_source == 'graph':
        if arguments.type == Networks.internet:
            topo = internet.load_topology(arguments.topology)
        elif arguments.type == Networks.airport:
            topo = airport.load_topology(arguments.topology)
        elif arguments.type == Networks.foodweb:
            topo = foodweb.load_topology(arguments.topology)
        elif arguments.type == Networks.weibo:
            pass
        elif arguments.type == Networks.text:
            topo = text.load_topology(arguments.topology)
        elif arguments.type == Networks.wiki:
            topo = wiki.load_topology(arguments.topology)
        elif arguments.type == Networks.metabolic:
            topo = metabolic.load_topology(arguments.topology,
                                           arguments.traceroutes_input)
            topo = metabolic.clean_graph(topo)
        elif arguments.type == Networks.gnutella:
            topo = gnutella.load_topology(arguments.topology)
        elif arguments.type == Networks.wordnavi:
            topo = wordnavi.load_topology(arguments.topology)
        else:
            RuntimeError('Unknown network type')

        topo = topo.simplify(combine_edges="ignore")

        for x in topo.vs:
            x['rank'] = topo.degree(x, mode=igraph.ALL)

    if arguments.topo_source == 'traceroutes':
        traceroutes = helpers.load_from_json(arguments.json_traces)
        directed = False

        if arguments.type in [Networks.wiki, ]:
            directed = True

        topo = helpers.traceroutes_to_ranked_graph(
            traceroutes, directed=directed)
        # edge_list = helpers.degree_labeling_traceroutes(traceroutes,
        #                                                 arguments.peer_treshold,
        #                                                 vfmode=vfmode)

        if arguments.type in [Networks.metabolic, ]:
            topo = metabolic.clean_graph(topo)

    topo = topo.simplify(combine_edges="ignore")
    topo.write(arguments.network_output, format='gml')

    # edge_list = [(e.source, e.target, vft.edge_type(topo, e).value) for e in topo.es]

    # # save to given output file using caida output format
    # # with open(arguments.network_output, 'w') as f:
    # #     for e in edge_list:
    # #         f.write('%s|%s|%s\n' % (e[0], e[1], e[2]))

    # print_network_statistics(edge_list)

if "labeling" in arguments.convert:
    vs, edges = helpers.load_as_inferred_links(arguments.topology, graph=False)
    converted_topo = helpers.inferred_links_to_ranked_graph(edges)

    converted_topo.write(arguments.network_output, format='gml')

    # edge_list = [(e.source, e.target, vft.edge_type(converted_topo, e).value)
    #              for e in converted_topo.es]

    # print_network_statistics(edge_list)
