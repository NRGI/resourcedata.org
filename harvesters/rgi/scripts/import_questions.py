import unicodecsv as csv

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
        elif row[0] == "QUESTION":
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