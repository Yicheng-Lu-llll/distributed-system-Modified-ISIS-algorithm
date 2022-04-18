# MP1 Design document
Kanya Mo and Zhenning Zhang

## How to use
See and modify `local_run.sh` and `heavy_run.sh` to reproduce the result and 
create your own testcase. The stdout which contains balance info will be stored to `out*.txt` where for node*,
and the stats will be collected under `/stats`. Then run `plot.py` to get the bandwidth and delay information.

## Protocol Design
We implement the modified version of ISIS algorithm in this mp. The basic procedure is the same as ISIS in slide, but for the unicast part we use multicast so that we do not need to concern too much about the status of message. We just need to seperate them into seen and unseen two parts. It may consume more bandwidth, but we think it will accelerate the algorithm.

## Failures Handling
We implement the basic handling mentioned in the MP document.
We assume no failure would happen at the initial stage. During the 
other time, when a failed process is detected by the message sender, a 
failure message will be reported so that the main worker will not 
wait for the failed process. 