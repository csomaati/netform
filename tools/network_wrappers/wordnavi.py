import json
import igraph
import dateutil.parser


def get_traceroutes(db_json_path):
    with open(db_json_path) as f:
        db = json.load(f, encoding='utf-8')
    game_logs = db['GameLogs']

    traceroutes = []
    timer = []

    for userid in game_logs:
        userchain = []
        for gameid in game_logs[userid]:
            game = game_logs[userid][gameid]
            if game['wordlength'] != 3: continue
            if game['language'] != 'EN': continue
#            if game['time_in_sec'] > 1000: continue
            chain = game['chain'].split(' ')
            s, t = game['sourceWord'], game['targetWord']
            if chain[-1] != t: continue
            if len(set(chain)) != len(chain): continue
            timer.append(game['time_in_sec'])
            # if game['time_in_sec'] > 26: continue
            chain = [x.lower() for x in chain]
            ts = int(dateutil.parser.parse(game['date']).strftime('%s'))
            userchain.append((chain, ts, game['time_in_sec'], game['date'], len(chain)))

        userchain = sorted(userchain, key=lambda x: x[1])
        userchain = userchain[50:]
        userchain = [x for x in userchain if x[2] <= 26.1]
        # for x in userchain:
        #     print "%4d:%4d!!%4.2f -- %s" % (x[4], x[2], (x[2]/float(x[4])), x[3])
        # print '----'
        userchain = [x[0] for x in userchain]
        traceroutes.extend(userchain)

#    print sum(timer)/len(timer)
#    print timer
    return traceroutes


def load_topology(graph_path):
    return igraph.load(graph_path)
