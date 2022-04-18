#!/bin/bash

python3 -u gentx.py 5 | python3 -u node.py node1 1111 heavy_config1.txt > out1.txt &
pid1=$!

python3 -u gentx.py 5 | python3 -u node.py node2 2222 heavy_config2.txt > out2.txt &
pid2=$!

python3 -u gentx.py 5 | python3 -u node.py node3 3333 heavy_config3.txt > out3.txt &
pid3=$!

python3 -u gentx.py 5 | python3 -u node.py node4 4444 heavy_config4.txt > out4.txt &
pid4=$!

python3 -u gentx.py 5 | python3 -u node.py node5 5555 heavy_config5.txt > out5.txt &
pid5=$!

python3 -u gentx.py 5 | python3 -u node.py node6 6666 heavy_config6.txt > out6.txt &
pid6=$!

python3 -u gentx.py 5 | python3 -u node.py node7 7777 heavy_config7.txt > out7.txt &
pid7=$!

python3 -u gentx.py 5 | python3 -u node.py node8 8888 heavy_config8.txt > out8.txt &
pid8=$!

sleep 110

kill $pid1
kill $pid2
kill $pid3
echo "node123 are done"

sleep 100

kill $pid4
kill $pid5
kill $pid6
kill $pid7
kill $pid8

echo "Finished"

