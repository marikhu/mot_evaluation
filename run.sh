#!/bin/bash
set -e

# MOT16-11
#python3 evaluate_tracking.py --seqmap seqmaps/test.txt --track data/ --gt data/

# TUD-Campus -- updated gt.txt to contain 1,1,1 instead of 1,-1,-1,-1 as
# it seems mot_evaluation supports only 2D
#python3 evaluate_tracking.py --seqmap seqmaps/test2.txt --track data/ --gt data/

# TEST -- Testing minimal contents of gt.txt and res.txt
python3 evaluate_tracking.py --seqmap seqmaps/test3.txt --track data/ --gt data/
