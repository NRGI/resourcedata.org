#!/bin/sh

mkdir ./out
python ./extract_summary.py
python ./eiti_import.py
