#!/bin/bash

echo "!!!! Plot gen"

pushd /mnt/ADAT/netform/papers/nature_2016/paper/figs

for folder in fig1stretch fig2eyefigs fig3lpeyefigs fig3upwalk figsyntetic; do
    pushd $folder
    echo "#### Plot in $folder"
    Rscript plot.R
    popd
done

popd
