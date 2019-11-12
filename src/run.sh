#! /bin/bash
python2 parser.py ../tests/test"$1".go ../out/ir/out"$1".ir ../out/csv/out"$1".csv var_map"$1".pkl 
