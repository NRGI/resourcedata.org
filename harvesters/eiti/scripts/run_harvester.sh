#!/bin/sh -e

mkdir ./out
# incremental
python ./eiti.py

#full
#python ./extract_summary.py
#python ./eiti_import.py
