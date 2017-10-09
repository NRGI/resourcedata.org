import unicodecsv as csv
import json

questions = []
cset = set()
allprecepts = set()

with open("questions_new_with_mapping_and_precepts.csv", "rb") as qfile:
    csvreader = csv.reader(qfile)
    currentComponent = None
    currentSubComponent = None
    currentIndicator = None
    for row in csvreader:
        if row[7] == "COMPONENT":
            currentComponent = row[5]
        elif row[7] == "SUB-COMPONENT":
            currentSubComponent = row[5]
            cset.add(row[5])
        elif row[7] == "INDICATOR":
            currentIndicator = row[5]
        elif row[7] in ("QUESTION", "NON-SCORING"):
            precepts = []
            if (row[7] == "NON-SCORING"):
                scoring = "non-scoring"
            else:
                scoring = "scoring"
            if (row[8] == "Law_Q"):
                lp = "law"
            elif (row[8] == "Practice_Q"):
                lp = "practice"
            else:
                lp = "neither"
            ref = row[3]
            qLabel = row[4]
            elName = row[5]
            qName = row[6]
            for text in row[0:3]:
                if text.strip() != "NA":
                    theprecept = text.strip()
                    parts = theprecept.split(":")
                    theprecept = parts[0].strip() + ": " + parts[1].strip()
                    precepts.append(theprecept)
                    allprecepts.add(theprecept)
            preceptsjson = json.dumps(precepts)
            questions.append([ref, currentComponent, qName, qLabel, currentSubComponent, currentIndicator, lp, elName, scoring, preceptsjson])

questions = sorted(questions, key=lambda k: int(k[0])) 

print("The list of sub-components will be shown for cross-checking")
for item in cset:
    print(item)
    
print("The list of precepts (categories) will be shown for cross-checking")
for item in sorted(allprecepts):
    print(item)
            
with open("questions_out.csv", "wb") as outfile:
    csvwriter = csv.writer(outfile)
    csvwriter.writerow(["Q", "Component", "Question", "QuestionLabel", "Subcomponent", "Indicator", "LawOrPractice", "Element name", "Scoring", "Precepts"])
    
    for question in questions:
        csvwriter.writerow(question)
        
with open("questions_for_schema.json", "wb") as outfile:
    jdata = {}
    jdata['choices'] = []
    
    for question in questions:
        jdata['choices'].append({"value": question[3], "label": question[3] + ": " + question[2]})
        
    outfile.write(json.dumps(jdata, sort_keys=True, indent=4,));
    
