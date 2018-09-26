import os
import igraph as i
import itertools
from .. import progressbar1
from .. import helpers

OFF_AIR_TRESHOLD = 0  # int(sys.argv[1])
DISCONNECTION_TRESHOLD = 0

(OF_AIRLINE, OF_AIRLINE_ID, OF_DEP_AIRPORT, OF_DEP_AIRPORT_ID,
 OF_ARR_AIRPORT, OF_ARR_AIRPORT_ID, OF_IS_CODSHARE,
 OF_STOPS, OF_EQUIPMENT) = range(0, 9)

(OF_AIRPORT_ID, OF_AIRPORT_NAME, OF_AIRPORT_CITY, OF_AIRPORT_COUNTRY,
 OF_AIRPORT_IATA, OF_AIRPORT_ICAO, OF_AIRPORT_LAT, OF_AIRPORT_LANG,
 OF_AIRPORT_ALT, OF_AIRPORT_TIMEZONE_OFFSET, OF_AIRPORT_DST,
 OF_AIRPORT_TIMEZONE) = range(0, 12)


def parse_r2r_itineraries(itineraries):
    sub_routes_all = list()
    for itinerarie in itineraries:
        hops = itinerarie['legs'][0]['hops']
        price = int(itinerarie['legs'][0]['indicativePrice']['price'])
        sCodes, tCodes = list(), list()
        # get all airport hop by hop
        for hop in hops:
            sCodes.append(hop['sCode'])
            tCodes.append(hop['tCode'])

        # all airport included twice (as an S airport and a T airport)
        # except segment's start and destination airport
        # so sCodes[1:] the same as tCode[:-1]
        # create a hop string
        hop_string = sCodes[:]
        hop_string.append(tCodes[-1])

        sub_routes_all.append((price, hop_string))

    # get the cheapest mode to travel through this segment
    ordered_itineraries = sorted(sub_routes_all, key=lambda x: x[0])

    lowest_price = ordered_itineraries[0][0]
    cheapest_hops = list(itertools.takewhile(lambda x: x[0] == lowest_price,
                                             ordered_itineraries))

    # remove prices
    cheapest_hops = [x[1] for x in cheapest_hops]

    # ALL routes instead of cheapest
    all_hops = [x[1] for x in sub_routes_all]

    # return cheapest_hops
    return all_hops


def parse_r2r_route_segments(segment_section):
    segment_routes_all = [list()]
    off_air = 0

    for segment in segment_section:

        if segment['kind'] != 'flight':
            # if this is off air segment
            # calculate distance spent not in the air
            off_air += segment['distance']

            # if off air exceed a treshold
            # drop this route
            if off_air > OFF_AIR_TRESHOLD:
                # print 'Spent too much on ground (%s)' % off_air
                return []
            continue
        # on air
        segment_routes_now = parse_r2r_itineraries(segment['itineraries'])
        # reset off_air counter
        off_air = 0
        # combine all possible flight routes from B to C with previous
        # results (actually with routes from Source to B)
        segment_routes_all = [head + tail for head in segment_routes_all
                              for tail in segment_routes_now]

    # convert lists to tuples
#    print "A good route, nice"
    return [tuple(x) for x in segment_routes_all]


def parse_r2r_routes(route_section):
    routes_all = list()
    for route in route_section:
        routes_now = parse_r2r_route_segments(route['segments'])
        if len(routes_now) > 0:
            price = route['indicativePrice']['price']
            # price = 0
            # price = route['duration']
            routes_all.append((price, routes_now))

    if len(routes_all) < 1: return []

    # get the cheapest route
    ordered_routes = sorted(routes_all, key=lambda x: x[0])
    lowest_price = ordered_routes[0][0]
    cheapest_routes = list(itertools.takewhile(lambda x: x[0] == lowest_price,
                                               ordered_routes))

    # remove prices
    cheapest_routes = [y for x in cheapest_routes for y in x[1]]
    return cheapest_routes


def get_traceroutes(json_folder, json_preload_folder):
    print 'get traceroutes'
    discovered_routes = []

    r2r_saved_responses = [f for f in os.listdir(json_folder)
                           if os.path.isfile(os.path.join(json_folder, f))
                           and not f.startswith('.')]

    route_count = len(r2r_saved_responses)
    progress = progressbar1.AnimatedProgressBar(end=route_count, width=15)

    for response_path in r2r_saved_responses:
        # print "Json file %s" % response_path
        # load previously downloaded json response
        progress += 1
        progress.show_progress()
        try:
            if json_preload_folder is None:
                raise IOError('Preload folder is not specified')
            routes = helpers.load_from_json(os.path.join(json_preload_folder,
                                                         response_path))
            routes = [tuple(x) for x in routes]
        except IOError:
            r2r_response = helpers.load_from_json(os.path.join(json_folder,
                                                               response_path))

            # get all possible route from Rome2Rio response
            # a ROUTE is a tuple of IATA codes (airport hops)
            # all possible route is a list of ROUTE
            routes = parse_r2r_routes(r2r_response['routes'])

            # save discovered routes
            if json_preload_folder is not None:
                helpers.save_to_json(os.path.join(json_preload_folder,
                                                  response_path), routes)

        # save routes
        discovered_routes.extend(routes)

        # remove duplicated elements
        discovered_routes = list(set(discovered_routes))

    return discovered_routes


def import_openflights_routes(fpath):
    loaded = helpers.import_csv_file_as_list(fpath)
    for sublist in loaded:
        sublist[OF_STOPS] = int(sublist[OF_STOPS])
        sublist[OF_DEP_AIRPORT_ID] = int(sublist[OF_DEP_AIRPORT_ID]) if sublist[OF_DEP_AIRPORT_ID] != '\\N' else None
        sublist[OF_ARR_AIRPORT_ID] = int(sublist[OF_ARR_AIRPORT_ID]) if sublist[OF_ARR_AIRPORT_ID] != '\\N' else None
        sublist[OF_AIRLINE_ID] = int(sublist[OF_AIRLINE_ID]) if sublist[OF_AIRLINE_ID] != '\\N' else None
    return loaded


def load_topology(openfligths_routes_path):
    print 'load airnet'
    # load CSV file containing airport routes
    # downloaded from http://openflights.org/data.html
    of_airport_connection = import_openflights_routes(openfligths_routes_path)

    # select only direct routes
    of_direct_routes = [x for x in of_airport_connection
                        if x[OF_STOPS] == 0]

    # create a table like list array to
    # directly address columns by column id
    # instead just rows
    of_direct_routes_table = zip(*of_direct_routes)

    # openflight routes dataset is directed, so
    # there is a directed route between airport A
    # to airport B if there is a row in directed_route
    # table where dep_aiport == A and arr_airport == B
    of_connected_airports = zip(of_direct_routes_table[OF_DEP_AIRPORT],
                                of_direct_routes_table[OF_ARR_AIRPORT])

    # build igraph graph object, using airport direct routes as edges
    airnet_edges = (dict(source=s, target=t)
                    for s, t in of_connected_airports )
    airnet = i.Graph.DictList(edges=airnet_edges, vertices=None)

    # remove disconnected clusters
    airnet_clusters = airnet.clusters()
    disconnected_idx = [x for x, c in enumerate(airnet_clusters)
                        if len(c) < DISCONNECTION_TRESHOLD]
    disconnected_node_list = [airnet_clusters[x] for x in disconnected_idx]
    disconnected_node_idx = list(itertools.chain.from_iterable(disconnected_node_list))

    # get IATA code for disconnected airports
    # just to remove from possible destination airport list
    # disconnected_iata = airnet.vs[disconnected_node_idx]['name']

    # remove disconnected subgraphs from airport connection graph
    airnet.delete_vertices(disconnected_node_idx)

    airnet.simplify()

    return airnet
