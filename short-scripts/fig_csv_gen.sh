#!/bin/bash

NETFORM_PATH="/mnt/ADAT/netform"

STAT_BUILDER="${NETFORM_PATH}/valley_free/scripts/statistics.py"
UPWALK_BUILDER="${NETFORM_PATH}/valley_free/scripts/trace_lp_choose_analyzer.py"

FIGA="${NETFORM_PATH}/papers/nature_2016/paper/figs/fig1stretch"
FIGBC="${NETFORM_PATH}/papers/nature_2016/paper/figs/fig2eyefigs"
FIGD="${NETFORM_PATH}/papers/nature_2016/paper/figs/figsyntetic"
FIGE="${NETFORM_PATH}/papers/nature_2016/paper/figs/upwalk"
FIGF="${NETFORM_PATH}/papers/nature_2016/paper/figs/load"
TMPDIR="/tmp/stats"

AIR_BASEDIR="${NETFORM_PATH}/valley_free/data/airport"
AIR_TOPO="${AIR_BASEDIR}/converted/topo_original_and_trace_cheapest_r2r_with_closeness.gml"
AIR_TRACEROUTES="${AIR_BASEDIR}/filtered/loop_ex_topo_original_and_trace_cheapest_trace_cheapest_r2r"
AIR_META_FULL="${AIR_BASEDIR}/results/loop_ex_topo_original_and_trace_cheapest_r2r_with_closeness_with_lp_soft_with_random_gulyas_walk_10_round_meta.json"
AIR_DS_STATS="${AIR_BASEDIR}/DS/results/result_topo_original_and_trace_cheapest_r2r_with_closeness_*_DS_meta.json"

INTERNET_BASEDIR="${NETFORM_PATH}/valley_free/data/internet"
INTERNET_TOPO="$INTERNET_BASEDIR/converted/topo_trace_filtered_dnszones_rank_with_closeness.gml"
INTERNET_TRACEROUTES="$INTERNET_BASEDIR/filtered/loop_ex_topo_trace_filtered_dnszones_rank"
INTERNET_META_FULL="$INTERNET_BASEDIR/results/loop_ex_topo_trace_filtered_dnszones_rank_with_closeness_with_lp_soft_with_random_gulyas_10_round_meta_SHORT_RANDOM_15000.json"
INTERNET_BA_STATS="${INTERNET_BASEDIR}/BA/results/result_topo_trace_filtered_dnszones_rank_with_closeness_*_BA_meta.json"

BRAINID=37
BRAIN_BASEDIR="${NETFORM_PATH}/valley_free/data/brain"
BRAIN_TOPO="$BRAIN_BASEDIR/converted/brain_str_map_gt_user_SQ8t7_${BRAINID}.gml"
BRAIN_TRACEROUTES="$BRAIN_BASEDIR/filtered/loop_ex_topo_SQ8t7_${BRAINID}"
BRAIN_META_FULL="$BRAIN_BASEDIR/results/loop_ex_topo_SQ8t7_${BRAINID}_with_closeness_with_lp_soft_with_random_gulyas_walk_10_round_meta.json"
BRAIN_DS_STATS="$BRAIN_BASEDIR/DS/results/result_brain_str_map_gt_user_SQ8t7_${BRAINID}_*_DS_meta.json"

WIKI_BASEDIR="${NETFORM_PATH}/valley_free/data/wiki"
WIKI_TOPO="${WIKI_BASEDIR}/converted/topo_original_with_closeness.gml"
WIKI_TRACEROUTES="$WIKI_BASEDIR/filtered/loop_ex_topo_original_trace_all"
WIKI_META_FULL="$WIKI_BASEDIR/results/loop_ex_topo_original_trace_all_with_closeness_with_lp_soft_with_random_gulyas_walk_10_round_meta.json"

WORDNAVI_BASEDIR="${NETFORM_PATH}/valley_free/data/wordnavi"
WORDNAVI_TOPO="${WORDNAVI_BASEDIR}/converted/word_grap3_with_closeness.gml"
WORDNAVI_TRACEROUTES="${WORDNAVI_BASEDIR}/filtered/loop_ex_topo_3_with_closeness_3_EN_26s_after50games"
WORDNAVI_META_FULL="${WORDNAVI_BASEDIR}/results/loop_ex_topo_3_with_closeness_3_EN_26s_after50games_with_random_gulyas_walk_10_round_meta.json"
WORDNAVI_DS_STATS="${WORDNAVI_BASEDIR}/DS/results/DS_word_graph_3_with_closeness_5000_*"

# Syntetic folders
SYN_DIR="${NETFORM_PATH}/papers/nature_2016/paper/figs/syntetic"

SYN_INTERNET_DIR="${SYN_DIR}/syntetic_internet_NODE_CHANGE_RND_SAMPLE_topo_trace_filtered_dnszones_rank_with_closeness_0.10_0_5000"
SYN_WIKI_DIR="${SYN_DIR}/syntetic_wiki_NODE_CHANGE_RND_SAMPLE_topo_original_with_closeness_0.0010000_0_5000"
SYN_AIR_DIR="${SYN_DIR}/syntetic_airport_NODE_CHANGE_RND_SAMPLE_topo_original_and_trace_cheapest_r2r_with_closeness_0.250_0_5002"
SYN_BRAIN_DIR="${SYN_DIR}/syntetic_brain_NODE_CHANGE_RND_SAMPLE_brain_str_map_gt_user_SQ8t7_37_0.509_0_5002"
SYN_WORDNAVI_DIR="${SYN_DIR}/syntetic_wordnavi_NODE_CHANGE_NONRND_SAMPLE_word_grap3_with_closeness_0.098_0_5002"
#syntetic_wiki_LP_topo_original_with_closeness_0.01_0_5000"

function calc {
    TYPE=${1}
    pushd $TMPDIR

    tmpupwalk=$(mktemp)
    python $UPWALK_BUILDER $TOPO $META_FULL $tmpupwalk -vv --progressbar upwalker

    PARAMS="--stretch-stat --eye-stat --upwalk $tmpupwalk"
    if [ -n ${DS_STATS+x} ]; then
        PARAMS=$PARAMS" --ba-stat $DS_STATS"
    fi
    
    python $STAT_BUILDER $TOPO $META_FULL ./ $PARAMS

    mv stretch_stat ${FIGA}/${TYPE}_stretch_stat.csv
    mv eye_stat ${FIGBC}/${TYPE}_eye_stat.csv
    mv upwalk ${FIGE}/${TYPE}_upwalk_stat.csv

    if [ -f ba_eye_stat ]; then
        mv ba_eye_stat $FIGBC/${TYPE}_DS_eye_stat.csv
    fi

    rm $tmpupwalk

    popd    
}

function syntetic_gen {
    TYPE=${1}

    pushd $TMPDIR

    META_FULL="${SYN_DIR}/syntetic_traces_meta_*"

    PARAMS="--stretch-stat --eye-stat-basic"
    python $STAT_BUILDER $TOPO $META_FULL ./ $PARAMS

    mv stretch_stat $FIGD/${TYPE}_stretch_stat.csv
    mv eye_stat_basic $FIGD/${TYPE}_eye_stat.csv
    cp ${SYN_DIR}/*.pdf ${FIGF}/${TYPE}_load.pdf

    popd
}

function network_stats_table {
    echo "#### Network stats"    
    echo "         ---- Airport"
    air_stats=$(python $STAT_BUILDER -vv $AIR_TOPO $AIR_META_FULL /dev/null --stats 2>&1)
    air_names=$(echo $air_stats | grep -oE "[0-9]{,2}\. [A-Za-z \.]+: [0-9]\.?[0-9]*" | cut -f1 -d":")
    air_values=($(echo $air_stats | grep -oE "[0-9]{,2}\. [A-Za-z \.]+: [0-9]\.?[0-9]*" | cut -f2 -d":"))

    echo "         ---- Internet"
    internet_stats=$(python $STAT_BUILDER -vv $INTERNET_TOPO $INTERNET_META_FULL /dev/null --stats 2>&1)
    internet_names=$(echo $internet_stats | grep -oE "[0-9]{,2}\. [A-Za-z \.]+: [0-9]\.?[0-9]*" | cut -f1 -d":")
    internet_values=($(echo $internet_stats | grep -oE "[0-9]{,2}\. [A-Za-z \.]+: [0-9]\.?[0-9]*" | cut -f2 -d":"))

    echo "         ---- Wiki"
    wiki_stats=$(python $STAT_BUILDER -vv $WIKI_TOPO $WIKI_META_FULL  /dev/null --stats 2>&1)
    wiki_names=$(echo $wiki_stats | grep -oE "[0-9]{,2}\. [A-Za-z \.]+: [0-9]\.?[0-9]*" | cut -f1 -d":")
    wiki_values=($(echo $wiki_stats | grep -oE "[0-9]{,2}\. [A-Za-z \.]+: [0-9]\.?[0-9]*" | cut -f2 -d":"))

    echo "         ---- Wordnavi"
    wordnavi_stats=$(python $STAT_BUILDER -vv $WORDNAVI_TOPO $WORDNAVI_META_FULL /dev/null --stats 2>&1)
    wordnavi_names=$(echo $wordnavi_stats | grep -oE "[0-9]{,2}\. [A-Za-z \.]+: [0-9]\.?[0-9]*" | cut -f1 -d":")
    wordnavi_values=($(echo $wordnavi_stats | grep -oE "[0-9]{,2}\. [A-Za-z \.]+: [0-9]\.?[0-9]*" | cut -f2 -d":"))

    echo "         ---- Brain"
    tmpfile=$(mktemp)
    for BRAINID in {0..3}; do
        echo "    @@@@ ${BRAINID} brain table calc"
        TOPO="${BRAIN_BASEDIR}/converted/brain_str_map_gt_user_SQ8t7_${BRAINID}.gml"
        META_FULL="${BRAIN_BASEDIR}/results/loop_ex_topo_SQ8t7_${BRAINID}_with_closeness_with_lp_soft_with_random_gulyas_walk_10_round_meta.json"
        brain_stats=$(python $STAT_BUILDER -vv $TOPO $META_FULL /dev/null --stats 2>&1)
        brain_names=$(echo $brain_stats | grep -oE "[0-9]{,2}\. [A-Za-z \.]+: [0-9]\.?[0-9]*" | cut -f1 -d":")
        brain_values=$(echo $brain_stats | grep -oE "[0-9]{,2}\. [A-Za-z \.]+: [0-9]\.?[0-9]*" | cut -f2 -d":" | tr '\n' ' '| sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' | tr -s '[[:space:]]')
        echo $brain_values >> $tmpfile
    done
    tmpr=$(mktemp)
    tmpres=$(mktemp)
    cat > $tmpr <<EOF
d <- read.csv('$tmpfile', sep=' ', header=FALSE)
avg <- colMeans(d)
avg[7] <- sum(d\$V7)
avg
lapply(avg, write, "$tmpres", append=TRUE, ncolumns=length(avg))
EOF
    Rscript $tmpr 1>/dev/null
    brain_values=($(cat $tmpres | tr '\n' ' '))
    rm $tmpr $tmpres $tmpfile

    i=0
    printf "%20s | %15s | %15s | %15s | %15s\n" "Network" "Airport" "Internet" "Brain" "Wiki"
    while read -r name; do
        printf "%-20s | %15.2f | %15.2f | %15.2f | %15.2f\n" "$name" "${air_values[$i]}" "${internet_values[$i]}" "${brain_values[$i]}" "${wiki_values[$i]}"
        i=$(($i + 1))
    done <<< "$air_names"
}

function network_csv_gen {
    network_airport_csv_gen
    network_internet_csv_gen
    network_brain_csv_gen
    network_wiki_csv_gen

    syntetic_airport_csv_gen
}

function network_airport_csv_gen {
    echo "#### Airport"
    TOPO=$AIR_TOPO
    TRACEROUTES=$AIR_TRACEROUTES
    META_FULL=$AIR_META_FULL
    DS_STATS=$AIR_DS_STATS
    calc airport
}

function network_wordnavi_csv_gen {
    echo "#### Wordnavi"
    TOPO=$WORDNAVI_TOPO
    TRACEROUTES=$WORDNAVI_TRACEROUTES
    META_FULL=$WORDNAVI_META_FULL
    DS_STATS=$WORDNAVI_DS_STATS
    calc wordnavi
}

function network_internet_csv_gen {
    echo "#### Internet"
    TOPO=$INTERNET_TOPO
    TRACEROUTES=$INTERNET_TRACEROUTES
    META_FULL=$INTERNET_META_FULL
    DS_STATS=$INTERNET_BA_STATS
    calc internet
}

function network_brain_csv_gen {
    echo "#### Brain"
    # BRAIN SNIPPET
    TOPO=$BRAIN_TOPO
    TRACEROUTES=$BRAIN_TRACEROUTES
    META_FULL=$BRAIN_META_FULL
    calc brain
    pushd $TMPDIR
    # brain stretch stat needs a different calculation method
    for BRAINID in {0..39}; do
        echo "    @@@@ ${BRAINID} brain stretch calc"
        TOPO="${BRAIN_BASEDIR}/converted/brain_str_map_gt_user_SQ8t7_${BRAINID}.gml"
        META_FULL="${BRAIN_BASEDIR}/results/loop_ex_topo_SQ8t7_${BRAINID}_with_closeness_with_lp_soft_with_random_gulyas_walk_10_round_meta.json"


        # FIG: A
        python ${STAT_BUILDER} ${TOPO} ${META_FULL} ./ --stretch-stat
        mv stretch_stat ${BRAINID}_brain_stretch_stat.csv
    done
    
    tmppy=$(mktemp)
    cat > tmppy <<EOF
import csv
import collections
STRETCH, COUNT, SUM = range(0, 3)
maxid = 39
maxstretch = 0
res = []
for idx in xrange(0, maxid + 1):
    ds = collections.defaultdict(lambda: 'NA')
    with open('%d_brain_stretch_stat.csv' % idx, 'rb') as f:
        reader = csv.reader(f, delimiter=';')
        line = 0
        for row in reader:
            line += 1
            if line < 3: continue
            if int(row[COUNT]) == 0: continue
            ds[int(row[STRETCH])] = int(row[COUNT]) / float(row[SUM])
            maxstretch = max(maxstretch, int(row[STRETCH]))

    res.append(ds)

with open('brain_stretch_stat.csv', 'w') as f:
    f.write('# generated with statistics.py brain_snippet based on brain_stretch_stat_csv folder\n')
    f.write('# route percentage in every stretch in every measurement\n')
    f.write('STRETCH')
    for i in xrange(0, maxid + 1):
        f.write(';BRAIN%d' % i)
    f.write('\n')
    for i in xrange(0, maxstretch + 1):
        f.write('%d' % i)
        for x in xrange(0, maxid + 1):
            f.write(';%s' % res[x][i])
        f.write('\n')
EOF

    python tmppy
    mv brain_stretch_stat.csv ${FIGA}/
    rm *_brain_stretch_stat.csv
    rm tmppy
    popd    
}


function network_wiki_csv_gen {
    echo "#### Wiki"
    TOPO=$WIKI_TOPO
    TRACEROUTES=$WIKI_TRACEROUTES
    META_FULL=$WIKI_META_FULL
    calc wiki
}

function syn_csv_gen {
    echo "@@@ Syntetic route stats"
    echo "   ### Airport"
    TOPO=$AIR_TOPO
    SYN_DIR=$SYN_AIR_DIR
    syntetic_gen airport

    echo "   ### Internet"
    TOPO=$INTERNET_TOPO
    SYN_DIR=$SYN_INTERNET_DIR
    syntetic_gen internet

    echo "   ### Brain"
    TOPO=$BRAIN_TOPO
    SYN_DIR=$SYN_BRAIN_DIR
    syntetic_gen brain

    echo "   ### Wiki" 
    TOPO=$WIKI_TOPO
    SYN_DIR=$SYN_WIKI_DIR
    syntetic_gen wiki

    echo "   ### Wordnavi"
    TOPO=$WORDNAVI_TOPO
    SYN_DIR=$SYN_WORDNAVI_DIR
    syntetic_gen wordnavi
}


# echo "!!!! Table stats"
network_stats_table

echo "!!!! CSV gen"
network_csv_gen
syn_csv_gen
