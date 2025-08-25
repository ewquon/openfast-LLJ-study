#!/bin/bash
set -e

conditions='mon_veer_classC llj_classC'

for cond in $conditions; do
    cd $cond
    for fstfile in *.fst; do
        echo '================================================='
        echo $fstfile
        echo '================================================='

        prefix="${fstfile%.fst}"
        logfile="${prefix}.log"
        outfile="${prefix}.out"

        cd inflow
        turbsim ${prefix}.inp
        cd ..

        openfast $fstfile 2>&1 | tee $logfile

        #gzip $outfile
    done
    cd ..
done

