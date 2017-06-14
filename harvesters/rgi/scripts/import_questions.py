import unicodecsv as csv
import json

questions = []

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
        elif row[0] == "INDICATOR":
            currentIndicator = row[3]
        elif row[0] in ("QUESTION", "NON_SCORING"):
            lawOrPractice = row[1]
            ref = row[2]
            elName = row[3]
            qName = row[4]
            questions.append([ref, currentComponent, qName, currentSubComponent, currentIndicator, lawOrPractice, elName])

questions = sorted(questions, key=lambda k: int(k[0])) 
            
with open("questions_out.csv", "wb") as outfile:
    csvwriter = csv.writer(outfile)
    csvwriter.writerow(["Q", "Component", "Question", "Subcomponent", "Indicator", "LawOrPractice", "Element name"])
    
    for question in questions:
        csvwriter.writerow(question)
        
with open("questions_for_schema.json", "wb") as outfile:
    jdata = {}
    jdata['choices'] = []
    
    for question in questions:
        jdata['choices'].append({"value": question[0], "label": str(question[0]) + ": " + question[2]})
        
    outfile.write(json.dumps(jdata));