import unicodecsv as csv
import json

questions = []
cset = set()

print("The list of sub-components will be shown for cross-checking")

with open("questions_new_with_mapping.csv", "rb") as qfile:
    csvreader = csv.reader(qfile)
    currentComponent = None
    currentSubComponent = None
    currentIndicator = None
    for row in csvreader:
        if row[4] == "COMPONENT":
            currentComponent = row[2]
        elif row[4] == "SUB-COMPONENT":
            currentSubComponent = row[2]
            cset.add(row[2])
        elif row[4] == "INDICATOR":
            currentIndicator = row[2]
        elif row[4] in ("QUESTION", "NON-SCORING"):
            if (row[4] == "NON-SCORING"):
                scoring = "non-scoring"
            else:
                scoring = "scoring"
            if (row[5] == "Law_Q"):
                lp = "law"
            elif (row[5] == "Practice_Q"):
                lp = "practice"
            else:
                lp = "neither"
            ref = row[0]
            qLabel = row[1]
            elName = row[2]
            qName = row[3]
            questions.append([ref, currentComponent, qName, qLabel, currentSubComponent, currentIndicator, lp, elName, scoring])

questions = sorted(questions, key=lambda k: int(k[0])) 

for item in cset:
    print(item)
            
with open("questions_out.csv", "wb") as outfile:
    csvwriter = csv.writer(outfile)
    csvwriter.writerow(["Q", "Component", "Question", "QuestionLabel", "Subcomponent", "Indicator", "LawOrPractice", "Element name", "Scoring"])
    
    for question in questions:
        csvwriter.writerow(question)
        
with open("questions_for_schema.json", "wb") as outfile:
    jdata = {}
    jdata['choices'] = []
    
    for question in questions:
        jdata['choices'].append({"value": question[3], "label": question[3] + ": " + question[2]})
        
    outfile.write(json.dumps(jdata, sort_keys=True, indent=4,));
