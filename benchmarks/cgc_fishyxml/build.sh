#!/bin/bash -ex
cd cgc_programs
pip3 install xlsxwriter pycrypto
bash ./build_fuzzbench.sh
cp build_afl1/challenges/FISHYXML/FISHYXML $OUT/
cp -r /opt/seeds $OUT/