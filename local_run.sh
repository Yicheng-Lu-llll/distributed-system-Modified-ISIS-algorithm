#!/bin/bash

python3 -u gentx.py 0.5 | python3 -u node.py node1 1234 local_config1.txt > out1.txt &
pid1=$!

python3 -u gentx.py 0.5 | python3 -u node.py node2 1235 local_config2.txt > out2.txt &
pid2=$!

python3 -u gentx.py 0.5 | python3 -u node.py node3 1236 local_config3.txt > out3.txt &
pid3=$!

sleep 100

kill $pid1
echo "Node1 failed"
#
sleep 100

kill $pid2
kill $pid3

echo "Finished"
