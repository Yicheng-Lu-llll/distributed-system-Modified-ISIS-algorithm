#!/bin/bash

cd "$(dirname $0)"

for i in {1..7}
do  
    j=$(expr ${i} + 1)
    for k in {${j}..8}
    do
        echo "diff out${i}.txt out${k}.txt"
        diff out${i}.txt out${k}.txt
        echo
    done
done
