import unicodecsv as csv
import json

questions = []
cset = set()

print("The list of sub-components (categories in CKAN) will be shown for cross-checking")

with open("questions_new.csv", "rb") as qfile:
    csvreader = csv.reader(qfile)
    currentComponent = None
    currentSubComponent = None
    currentIndicator = None
    for row in csvreader:
        if row[0] == "COMPONENT":
            currentComponent = row[3]
        elif row[0] == "SUB-COMPONENT":
            currentSubComponent = row[3]
            cset.add(row[3])
        elif row[0] == "INDICATOR":
            currentIndicator = row[3]
        elif row[0] in ("QUESTION", "NON_SCORING"):
            if (row[0] == "NON_SCORING"):
                scoring = "non-scoring"
            else:
                scoring = "scoring"
            if (row[1] == "Law_Q"):
                lp = "law"
            elif (row[1] == "Practice_Q"):
                lp = "practice"
            else:
                lp = "neither"
            ref = row[2]
            elName = row[3]
            qName = row[4]
            questions.append([ref, currentComponent, qName, currentSubComponent, currentIndicator, lp, elName, scoring])

questions = sorted(questions, key=lambda k: int(k[0])) 

for item in cset:
    print(item)
            
with open("questions_out.csv", "wb") as outfile:
    csvwriter = csv.writer(outfile)
    csvwriter.writerow(["Q", "Component", "Question", "Subcomponent", "Indicator", "LawOrPractice", "Element name", "Scoring"])
    
    for question in questions:
        csvwriter.writerow(question)
        
with open("questions_for_schema.json", "wb") as outfile:
    jdata = {}
    jdata['choices'] = []
    
    for question in questions:
        q_as_str = "%03d" % int(question[0])
        jdata['choices'].append({"value": q_as_str, "label": q_as_str + ": " + question[2]})
        
    outfile.write(json.dumps(jdata, sort_keys=True, indent=4,));