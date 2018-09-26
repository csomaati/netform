#!/bin/bash

function skipnlines {
    echo "Called with $1 AND $2"
    fname=$1
    linenum=$2
    tmpfile=$(mktemp)
    tail -n +$((linenum + 1))  $fname > $tmpfile
    mv $tmpfile $fname
}


CORE_LIMIT=0
NODE_CHANGE_MODE="False"
RANDOM_SAMPLE="False"
MODE=""
SYNTETIC_ROUTING_EXTRAS=""

PRE_WORDNAVI_GRAPH="/mnt/ADAT/netform/valley_free/data/wordnavi/converted/word_grap3_with_closeness.gml"
#PRE_WORDNAVI_META="/mnt/ADAT/netform/valley_free/data/wordnavi/results/loop_ex_topo_3_with_closeness_3_EN_26s_after50games_with_random_gulyas_walk_10_round_meta.json"
PRE_WORDNAVI_META="/mnt/ADAT/netform/valley_free/data/wordnavi/results/loop_ex_topo_3_with_closeness_3_EN_26s_after50games_2017-01-09_with_random_gulyas_walk_10_round_meta.json"

PRE_AIRPORT_GRAPH="/mnt/ADAT/netform/valley_free/data/airport/converted/topo_original_and_trace_cheapest_r2r_with_closeness.gml"
PRE_AIRPORT_META="/mnt/ADAT/netform/valley_free/data/airport/results/loop_ex_topo_original_and_trace_cheapest_r2r_with_closeness_with_lp_soft_with_random_gulyas_walk_10_round_meta.json"

PRE_BRAIN_GRAPH="/mnt/ADAT/netform/valley_free/data/brain/converted/brain_str_map_gt_user_SQ8t7_37.gml"
PRE_BRAIN_META="/mnt/ADAT/netform/valley_free/data/brain/results/loop_ex_topo_SQ8t7_37_with_closeness_with_lp_soft_with_random_gulyas_walk_10_round_meta.json"

PRE_INTERNET_GRAPH="/mnt/ADAT/netform/valley_free/data/internet/converted/topo_trace_filtered_dnszones_rank_with_closeness.gml"
PRE_INTERNET_META="/mnt/ADAT/netform/valley_free/data/internet/results/loop_ex_topo_trace_filtered_dnszones_rank_with_closeness_with_lp_soft_with_random_gulyas_10_round_meta_SHORT_RANDOM_15000.json"

PRE_WIKI_GRAPH="/mnt/ADAT/netform/valley_free/data/wiki/converted/topo_original_with_closeness.gml"
PRE_WIKI_META="/mnt/ADAT/netform/valley_free/data/wiki/results/loop_ex_topo_original_trace_all_with_closeness_with_lp_soft_with_random_gulyas_walk_10_round_meta.json"

function graph_path_extract {
    GRAPH_FULL="$1"
    GRAPH=$(basename $GRAPH_FULL)
    GRAPH_EXT="${GRAPH##*.}"
    GRAPH_NAME="${GRAPH%.*}"   
}

function preload {
    PRELOAD_TYPE=$1
    if [ "$PRELOAD_TYPE" == "wordnavi" ]
    then
        graph_path_extract $PRE_WORDNAVI_GRAPH
        META=$PRE_WORDNAVI_META
    elif [ "$PRELOAD_TYPE" == "airport" ]
    then
        graph_path_extract $PRE_AIRPORT_GRAPH
        META=$PRE_AIRPORT_META
    elif [ "$PRELOAD_TYPE" == "brain" ]
    then
        graph_path_extract $PRE_BRAIN_GRAPH
        META=$PRE_BRAIN_META
    elif [ "$PRELOAD_TYPE" == "internet" ]
    then
        graph_path_extract $PRE_INTERNET_GRAPH
        META=$PRE_INTERNET_META
    elif [ "$PRELOAD_TYPE" == "wiki" ]
    then
        graph_path_extract $PRE_WIKI_GRAPH
        META=$PRE_WIKI_META
    else
        echo "***** Unknown preload type: '$exit'"
        exit -1
    fi       
}


while [[ $# -gt 0 ]]
do
    key="$1"

    case $key in
        -g|--graph)
            graph_path_extract $2
            shift 2 # past argument
            ;;
        -ce|--closeness-error)
            CLOSENESS_ERROR="$2"
            shift 2 # past argument
            ;;
        --trace-count)
            TRACE_COUNT="$2"
            shift 2
            ;;
        --core-limit)
            CORE_LIMIT="$2"
            shift 2
            ;;
        --meta)
            META="$2"
            shift 2
            ;;
        --type)
            TYPE="$2"
            shift 2
            ;;
        --node-change-mode)
            NODE_CHANGE_MODE="True"
            shift 1
            ;;
        --random-sample)
            RANDOM_SAMPLE="True"
            shift 1
            ;;
        --preload)
            shift 1
            preload $TYPE
            ;;
        *)
            # unknown option
            shift
            ;;
    esac
done
if [ "$NODE_CHANGE_MODE" == "True" ]
then
    MODE=$MODE"_NODE_CHANGE"
    SYNTETIC_ROUTING_EXTRAS=$SYNTETIC_ROUTING_EXTRAS" --toggle-node-error-mode"
else
    MODE=$MODE"_EDGE_CHANGE"
fi

if [ "$RANDOM_SAMPLE" == "True" ]
then
    MODE=$MODE"_RND_SAMPLE_"
    SYNTETIC_ROUTING_EXTRAS=$SYNTETIC_ROUTING_EXTRAS" --random-sample"
else
    MODE=$MODE"_NONRND_SAMPLE_"
fi

ROOT="/mnt/ADAT/netform/papers/nature_2016/paper/figs/syntetic"
MEASID="syntetic_${TYPE}${MODE}${GRAPH_NAME}_${CLOSENESS_ERROR}_${CORE_LIMIT}_${TRACE_COUNT}"
BASEPATH=$ROOT/$MEASID
TMP_SYNTETIC="${BASEPATH}/syntetic_${GRAPH_NAME}.json"
TMP_SYNTETIC_TRACES="${BASEPATH}/syntetic_traces_${GRAPH_NAME}.json"
TMP_SYNTETIC_FILTERED="${BASEPATH}/syntetic_traces_filtered_${GRAPH_NAME}.json"
TMP_SYNTETIC_META="${BASEPATH}/syntetic_traces_meta_${GRAPH_NAME}.json"
COMPARE_MEASUREMENTS_FOLDER="${BASEPATH}/compare"
echo "------------------ CONFIG ------------------"
echo "|"
echo "| TYPE:    $TYPE"
echo "|"
echo "| NODE CHANGE MODE: $NODE_CHANGE_MODE"
echo "| RANDOM SAMPLE   : $RANDOM_SAMPLE"
echo "| CLOSENESS ERROR : $CLOSENESS_ERROR"
echo "| CORE LIMIT      : $CORE_LIMIT"
echo "| TRACE_COUNT     : $TRACE_COUNT"
echo "|"
echo "| Files:"
echo "| GRAPH      : $GRAPH_NAME"
echo "| METADATA   : $META"
echo "| SYNT FOLDER: $MEASID"
echo "---------------------------------------------"

# CLOSENESS_ERROR=$6 # 0.002
# USED_TRACE_COUNT=$7 # 4000

# python graph_test_generator.py $GRAPH_FULL $TRACE_FULL --trace-count $TRACE_COUNT --network-type $GRAPH_TYPE --node-count $GRAPH_NODE_COUNT
# python trace_meta_builder.py $GRAPH_FULL $TRACE_FULL $META_FULL --with-closeness --with-lp-soft -vv --progressbar
# python random_gulyas_walk.py $GRAPH_FULL $META_FULL $RND_META --try-per-trace 10 --with-closeness --with-lp-soft --progressbar -vv




echo "#### Create $BASEPATH root folder for current measurement"
mkdir ${BASEPATH}

echo "#### Syntetic routing"
python syntetic_routing.py  $GRAPH_FULL $META $TMP_SYNTETIC $TMP_SYNTETIC_TRACES -vv -tc $TRACE_COUNT --closeness-error $CLOSENESS_ERROR --progressbar --core-limit-percentile $CORE_LIMIT  $SYNTETIC_ROUTING_EXTRAS

echo '#### Syntetic route stats'
python statistics.py $GRAPH_FULL $META $BASEPATH/ --load2d $TMP_SYNTETIC -vv

cd $BASEPATH
PLOT_NAME="${MEASID}.pdf"
echo "#### create plot at $PLOT_NAME"
Rscript /mnt/ADAT/netform/papers/nature_2016/paper/figs/syntetic_routing.R $PLOT_NAME $BASEPATH/base_list.csv $BASEPATH/tr_list.csv $BASEPATH/sh_list.csv $BASEPATH/sr_list.csv
## evince $PLOT_NAME &

cd -

echo "#### Filter syntetic traces"
python filter.py $GRAPH_FULL $TMP_SYNTETIC_TRACES --filter loop+ex $TMP_SYNTETIC_FILTERED
echo "#### Meta builder on syntetic routes"
python trace_meta_builder.py $GRAPH_FULL $TMP_SYNTETIC_FILTERED $TMP_SYNTETIC_META --with-closeness --with-lp-soft --progressbar
echo "#### Stats on syntetic routes"
python statistics.py ${GRAPH_FULL} ${TMP_SYNTETIC_META} ${BASEPATH} --stats --stretch-stat --eye-stat-basic -vv

echo "#### Stats on original routes for comparement"
mkdir ${COMPARE_MEASUREMENTS_FOLDER}
python statistics.py ${GRAPH_FULL} ${META} ${COMPARE_MEASUREMENTS_FOLDER} --stats --stretch-stat --eye-stat-basic -vv

echo "#### Compare syntetic vs original route numbers"
cp ${BASEPATH}/eye_stat_basic ${BASEPATH}/header_good_eye_stat_basic
cp ${BASEPATH}/stretch_stat ${BASEPATH}/header_good_stretch_stat

skipnlines "${BASEPATH}/stretch_stat" 1
skipnlines "${BASEPATH}/eye_stat_basic" 1
skipnlines "${COMPARE_MEASUREMENTS_FOLDER}/stretch_stat" 1
skipnlines "${COMPARE_MEASUREMENTS_FOLDER}/eye_stat_basic" 1

sed -i '1iX;ALL;PART;DONTCATE' ${BASEPATH}/eye_stat_basic
sed -i '1iX;ALL;PART;DONTCATE' ${COMPARE_MEASUREMENTS_FOLDER}/eye_stat_basic

sed -i '1iX;PART;ALL' ${BASEPATH}/stretch_stat
sed -i '1iX;PART;ALL' ${COMPARE_MEASUREMENTS_FOLDER}/stretch_stat

Rscript R/compare.r ${BASEPATH}/stretch_stat $COMPARE_MEASUREMENTS_FOLDER/stretch_stat ${BASEPATH}/compare_stretch_stat.pdf "syntetic" "original" logscale
Rscript R/compare.r ${BASEPATH}/eye_stat_basic $COMPARE_MEASUREMENTS_FOLDER/eye_stat_basic ${BASEPATH}/compare_eye_stat_basic.pdf "syntetic" "original" normal
