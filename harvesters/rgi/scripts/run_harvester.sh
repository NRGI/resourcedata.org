#!/bin/sh

curl http://rgi.nrgi-assessment.org/api/public/assessments > assessment_list.json
jq '.[] | .assessment_ID' ./assessment_list.json > assessments.csv
python ./get_pdfs.py
python ./rgi_import.py
