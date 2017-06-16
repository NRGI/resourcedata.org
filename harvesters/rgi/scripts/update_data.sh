curl http://rgi.nrgi-assessment.org/api/public/assessments > assessment_list.json
jq '.[] | .assessment_ID' ./assessment_list.json > assessments.csv
