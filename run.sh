#!/bin/bash
set -e

#python3 evaluate_tracking.py --seqmap seqmaps/test.txt --track data/ --gt data/
python3 evaluate_tracking.py --seqmap seqmaps/test2.txt --track data/ --gt data/
