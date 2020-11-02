#!/bin/bash
set -e

python3 evaluate_tracking.py --seqmap seqmaps/TEST.txt --track data/ --gt data/

