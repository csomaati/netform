#!/bin/bash

##
## AS PATH-okat tartalmazo statisztikak letoltese a caida oldalaro
## A datum es kimeneti mappa parameterekkel valtoztathato
## Jelen beallitas a meresekhez hasznalt ertekeket tukrozi
##

DATE='2015.01'
FOLDERS='route-views.eqix route-views.isc route-views.jinx route-views.kixp route-views.linx route-views.nwax route-views.perth route-views.saopaulo route-views.sfmix route-views.sg route-views.soxrs route-views.sydney route-views.telxatl route-views.wide route-views3 route-views4 route-views6 .'
ROUTERS='00 01 03 04 05 06 07 10 11 12 13 14 15'
SUBFOLDERS='RIBS UPDATES'

# mkdir -p as_path
# cd as_path

# mkdir -p route_view
# cd route_view
# for i in $FOLDERS
# do
#     uri='ftp://archive.routeviews.org/'$i'/bgpdata/'$DATE'/'
#     wget -m $uri
# done
# cd ../

# mkdir ripe_ris
# cd ripe_ris
# for i in $ROUTERS
# do
#     mkdir -p 'rrc'$i
#     cd $i
#     uri='http://data.ris.ripe.net/rrc'$i'/'$DATE'/'
#     echo $uri
#     wget -m -np -e robots=off $uri
#     cd ../
# done
# cd ../

# cd ../

function dump {
    root_dir=$2
    i=$1
    rm -f $root_dir'/as_path/route_view/archive.routeviews.org/'$i'/bgpdata/'$DATE'/delme_as_path_summary.txt'
    echo 'Parse files in folder '$i
    for subf in $SUBFOLDERS
    do
        echo '  We are in '$subf
        cd $root_dir'/as_path/route_view/archive.routeviews.org/'$i'/bgpdata/'$DATE'/'$subf'/'
        for file in *.bz2
        do
            echo 'Parse '$file
            full_name=$(basename "$file")
            fname=${full_name%.*}
            bgpdump $file | grep 'ASPATH' | cut -d ' ' -f 2- | sort -b -d | uniq >> ../delme_as_path_summary.txt
        done
    done
    cd ../

    echo '  Now in '$(pwd)
    echo 'Before global uniq: '$(cat delme_as_path_summary.txt | wc -l)
    cat delme_as_path_summary.txt | sort -b -d | uniq > as_path_summary.txt
    # rm delme_as_path_summary.txt
    echo 'After global uniq:'$(cat as_path_summary.txt | wc -l)
}


# get as path from saved MRT formatted files
# allfile=$(find ./ -type f)

for i in $FOLDERS
do
    root_dir=$(pwd)
    dump $i $root_dir &
    sleep 2
done

# select only one rib/day/collector from the given days
DAYS='01 05 10 15 20 25 30'
for i in $FOLDERS
do
    for d in $DAYS
    do
        fname='rib.201501'$d'.1200.bz2'
        cp '/mnt/ADAT/measurements3/data/internet/raw/traceroutes/as_path/route_view/archive.routeviews.org/'$i'/bgpdata/'$DATE'/RIBS/'$fname ./$i'_'$fname
    done
done

for i in *.bz2
do
    echo 'parse '$i
    bgpdump $i | grep 'ASPATH' | cut -d ' ' -f 2- | sort -b -d | uniq >> ${i}_summary.txt &
done



# python code

file = ''

with open(fname, 'r') as f:
    as_set = set()
    for line in f:
        as_list = line.strip().split(' ')
        as_list = (x[0] for x in itertools.groupby(as_list))
        as_set.add(as_list)

    as_list = list(as_set)
    as_list = sorted(as_list)
    with open('%s.compressed' % fname, 'w') as k:
        for x in as_list
            k.write('%s\n' % x)
