#!/bin/bash -ex
cd cgc_programs
pip3 install xlsxwriter pycrypto
bash ./build_fuzzbench.sh
cp build_afl1/challenges/Network_Queuing_Simulator/Network_Queuing_Simulator $OUT/
cp -r /opt/seeds $OUT/