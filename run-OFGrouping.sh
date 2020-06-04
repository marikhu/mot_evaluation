#!/bin/bash
set -e

# OFGrouping - 19Nov19
#python3 evaluate_tracking.py --seqmap seqmaps/OFGrouping-19Nov19.txt --track data/ --gt data/

# OFGrouping - 04Jun20
python3 evaluate_tracking.py --seqmap seqmaps/OFGrouping-04Jun20.txt --track data/ --gt data/

