# -*- coding: utf-8 -*-


import csv
import json
import requests

API_ENDPOINT = "http://rgi.nrgi-assessment.org/api/public/documents/"

assessments = []

iso3 = {
    "ABW":u"Aruba", "AFG":u"Afghanistan", "AGO":u"Angola", "AIA":u"Anguilla", "ALA":u"Åland Islands", "ALB":u"Albania", "AND":u"Andorra", "ANT":u"Netherlands Antilles", "ARE":u"United Arab Emirates", "ARG":u"Argentina", "ARM":u"Armenia", "ASM":u"American Samoa", "ATA":u"Antarctica", "ATF":u"French Southern Territories", "ATG":u"Antigua and Barbuda", "AUS":u"Australia", "AUT":u"Austria", "AZE":u"Azerbaijan", "BDI":u"Burundi", "BEL":u"Belgium", "BEN":u"Benin", "BFA":u"Burkina Faso", "BGD":u"Bangladesh", "BGR":u"Bulgaria", "BHR":u"Bahrain", "BHS":u"Bahamas", "BIH":u"Bosnia and Herzegovina", "BLM":u"Saint Barthélemy", "BLR":u"Belarus", "BLZ":u"Belize", "BMU":u"Bermuda", "BOL":u"Bolivia, Plurinational State of", "BRA":u"Brazil", "BRB":u"Barbados", "BRN":u"Brunei Darussalam", "BTN":u"Bhutan", "BVT":u"Bouvet Island", "BWA":u"Botswana", "CAF":u"Central African Republic", "CAN":u"Canada", "CCK":u"Cocos (Keeling) Islands", "CHE":u"Switzerland", "CHL":u"Chile", "CHN":u"China", "CIV":u"Côte d'Ivoire", "CMR":u"Cameroon", "COD":u"Congo, the Democratic Republic of the", "COG":u"Congo", "COK":u"Cook Islands", "COL":u"Colombia", "COM":u"Comoros", "CPV":u"Cape Verde", "CRI":u"Costa Rica", "CUB":u"Cuba", "CXR":u"Christmas Island", "CYM":u"Cayman Islands", "CYP":u"Cyprus", "CZE":u"Czech Republic", "DEU":u"Germany", "DJI":u"Djibouti", "DMA":u"Dominica", "DNK":u"Denmark", "DOM":u"Dominican Republic", "DZA":u"Algeria", "ECU":u"Ecuador", "EGY":u"Egypt", "ERI":u"Eritrea", "ESH":u"Western Sahara", "ESP":u"Spain", "EST":u"Estonia", "ETH":u"Ethiopia", "FIN":u"Finland", "FJI":u"Fiji", "FLK":u"Falkland Islands (Malvinas)", "FRA":u"France", "FRO":u"Faroe Islands", "FSM":u"Micronesia, Federated States of", "GAB":u"Gabon", "GBR":u"United Kingdom", "GEO":u"Georgia", "GGY":u"Guernsey", "GHA":u"Ghana", "GIB":u"Gibraltar", "GIN":u"Guinea", "GLP":u"Guadeloupe", "GMB":u"Gambia", "GNB":u"Guinea-Bissau", "GNQ":u"Equatorial Guinea", "GRC":u"Greece", "GRD":u"Grenada", "GRL":u"Greenland", "GTM":u"Guatemala", "GUF":u"French Guiana", "GUM":u"Guam", "GUY":u"Guyana", "HKG":u"Hong Kong", "HMD":u"Heard Island and McDonald Islands", "HND":u"Honduras", "HRV":u"Croatia", "HTI":u"Haiti", "HUN":u"Hungary", "IDN":u"Indonesia", "IMN":u"Isle of Man", "IND":u"India", "IOT":u"British Indian Ocean Territory", "IRL":u"Ireland", "IRN":u"Iran, Islamic Republic of", "IRQ":u"Iraq", "ISL":u"Iceland", "ISR":u"Israel", "ITA":u"Italy", "JAM":u"Jamaica", "JEY":u"Jersey", "JOR":u"Jordan", "JPN":u"Japan", "KAZ":u"Kazakhstan", "KEN":u"Kenya", "KGZ":u"Kyrgyzstan", "KHM":u"Cambodia", "KIR":u"Kiribati", "KNA":u"Saint Kitts and Nevis", "KOR":u"Korea, Republic of", "KWT":u"Kuwait", "LAO":u"Lao People's Democratic Republic", "LBN":u"Lebanon", "LBR":u"Liberia", "LBY":u"Libyan Arab Jamahiriya", "LCA":u"Saint Lucia", "LIE":u"Liechtenstein", "LKA":u"Sri Lanka", "LSO":u"Lesotho", "LTU":u"Lithuania", "LUX":u"Luxembourg", "LVA":u"Latvia", "MAC":u"Macao", "MAF":u"Saint Martin (French part)", "MAR":u"Morocco", "MCO":u"Monaco", "MDA":u"Moldova, Republic of", "MDG":u"Madagascar", "MDV":u"Maldives", "MEX":u"Mexico", "MHL":u"Marshall Islands", "MKD":u"Macedonia, the former Yugoslav Republic of", "MLI":u"Mali", "MLT":u"Malta", "MMR":u"Myanmar", "MNE":u"Montenegro", "MNG":u"Mongolia", "MNP":u"Northern Mariana Islands", "MOZ":u"Mozambique", "MRT":u"Mauritania", "MSR":u"Montserrat", "MTQ":u"Martinique", "MUS":u"Mauritius", "MWI":u"Malawi", "MYS":u"Malaysia", "MYT":u"Mayotte", "NAM":u"Namibia", "NCL":u"New Caledonia", "NER":u"Niger", "NFK":u"Norfolk Island", "NGA":u"Nigeria", "NIC":u"Nicaragua", "NIU":u"Niue", "NLD":u"Netherlands", "NOR":u"Norway", "NPL":u"Nepal", "NRU":u"Nauru", "NZL":u"New Zealand", "OMN":u"Oman", "PAK":u"Pakistan", "PAN":u"Panama", "PCN":u"Pitcairn", "PER":u"Peru", "PHL":u"Philippines", "PLW":u"Palau", "PNG":u"Papua New Guinea", "POL":u"Poland", "PRI":u"Puerto Rico", "PRK":u"Korea, Democratic People's Republic of", "PRT":u"Portugal", "PRY":u"Paraguay", "PSE":u"Palestinian Territory, Occupied", "PYF":u"French Polynesia", "QAT":u"Qatar", "REU":u"Réunion", "ROU":u"Romania", "RUS":u"Russian Federation", "RWA":u"Rwanda", "SAU":u"Saudi Arabia", "SDN":u"Sudan", "SEN":u"Senegal", "SGP":u"Singapore", "SGS":u"South Georgia and the South Sandwich Islands", "SHN":u"Saint Helena, Ascension and Tristan da Cunha", "SJM":u"Svalbard and Jan Mayen", "SLB":u"Solomon Islands", "SLE":u"Sierra Leone", "SLV":u"El Salvador", "SMR":u"San Marino", "SOM":u"Somalia", "SPM":u"Saint Pierre and Miquelon", "SRB":u"Serbia", "STP":u"Sao Tome and Principe", "SUR":u"Suriname", "SVK":u"Slovakia", "SVN":u"Slovenia", "SWE":u"Sweden", "SWZ":u"Swaziland", "SYC":u"Seychelles", "SYR":u"Syrian Arab Republic", "TCA":u"Turks and Caicos Islands", "TCD":u"Chad", "TGO":u"Togo", "THA":u"Thailand", "TJK":u"Tajikistan", "TKL":u"Tokelau", "TKM":u"Turkmenistan", "TLS":u"Timor-Leste", "TON":u"Tonga", "TTO":u"Trinidad and Tobago", "TUN":u"Tunisia", "TUR":u"Turkey", "TUV":u"Tuvalu", "TWN":u"Taiwan, Province of China", "TZA":u"Tanzania, United Republic of", "UGA":u"Uganda", "UKR":u"Ukraine", "UMI":u"United States Minor Outlying Islands", "URY":u"Uruguay", "USA":u"United States", "UZB":u"Uzbekistan", "VAT":u"Holy See (Vatican City State)", "VCT":u"Saint Vincent and the Grenadines", "VEN":u"Venezuela, Bolivarian Republic of", "VGB":u"Virgin Islands, British", "VIR":u"Virgin Islands, U.S.", "VNM":u"Viet Nam", "VUT":u"Vanuatu", "WLF":u"Wallis and Futuna", "WSM":u"Samoa", "YEM":u"Yemen", "ZAF":u"South Africa", "ZMB":u"Zambia", "ZWE":u"Zimbabwe",
"SSD":u"South Sudan"
}

complete_metadata = {}
question_subcomponents = {}
question_lp = {}
question_scoring = {}
question_label = {}
question_precepts = {}
#Read output of import_questions.py
with open('./questions_out.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        question_subcomponents[row['QuestionLabel']] = row['Subcomponent']
        question_lp[row['QuestionLabel']] = row['LawOrPractice']
        question_scoring[row['QuestionLabel']] = row['Scoring']
        #Store this one this way to do the mapping RC API -> new question refs
        question_label[row['Q'].zfill(3)] = row['QuestionLabel']
        question_precepts[row['QuestionLabel']] = json.loads(row['Precepts'])
        
print question_precepts

with open('./assessments.csv', 'r') as f:
    assessments = [l.strip().replace('"','').replace('"','') for l in f.readlines()]

datasets = {}
all_removals = set()
pdfs = 0
dropped_pdfs = 0
duplicates = []

def urlify(s):
    return s.lower().replace(' ', '-').replace(':', '')

for assessment in assessments:
    complete_metadata[assessment] = []
    #Used for skipping/testing
    #if "CIV" not in assessment:
    #    continue
    r = requests.get(API_ENDPOINT + assessment)
    docs = r.json()

    print '%s has %s pdfs' % (assessment, len([d for d in docs if d['mime_type'] == "application/pdf"]))

    for d in docs:
        #Used for analysing what's in the data, should normally be commented out
        #print d.get('title', "EMPTY") + "\t" + d.get('type', "EMPTY") + "\t" + d.get('year', "EMPTY") + "\t" + d.get('publisher', "EMPTY") + "\t" + d['editors'][0]['first_name'] + " " + d['editors'][0]['last_name'] + "\t" + d['authors'][0]['first_name'] + " " + d['authors'][0]['last_name'] 
        #continue
        complete_metadata[assessment].append(d)
        if (d['mime_type'] == 'application/pdf'):
            pdfs += 1
            subcomponent = ''
            questions = []

            law_practice_question = set()
            scoring_question = set()
            #We now already detect a missing question here but we want to highlight it below; keep it around with the RC ref
            questions_raw = [question_label.get(l, l) for l in [q[-3:] for q in d['answers']]]
            questions = set(questions_raw)
            removals = []
            for question in questions:
                if question not in question_label.values():
                    print "Warning, question " + question + " not in list of valid questions"
                    all_removals.add(question)
                    removals.append(question)
            for removal in removals:
                questions.remove(removal)
            if len(questions) == 0:
                print "Warning, PDF not associated with any valid questions, dropping"
                dropped_pdfs += 1
                continue
            questions = list(questions)
            subcomponent = question_subcomponents[questions[0]]
            categories = []
            for question in questions:
                #Neither is an OK flag for us in the question list but doesn't fit the CKAN model so well
                if question_lp[question] != "neither":
                    law_practice_question.add(question_lp[question])
                scoring_question.add(question_scoring[question])
                categories.extend(question_precepts[question])
                
            categories = list(set(categories)) #Take unique values

            assessment_type_abbr = assessment[-2:]
            if assessment_type_abbr == "HY":
                assessment_type = "Oil and Gas"
            elif assessment_type_abbr == "MI":
                assessment_type = "Mining"
            else:
                assessment_type = "Unknown"
                
            law_practice_question = list(law_practice_question)
            year = d.get('year')
            if year:
                year = [year,]
            else:
                year = []
            
            new_dataset = {
                'type': 'document',
                'document_type': d.get('type', "Unknown").strip().title().replace("_", " "),
                'publisher': d.get('publisher', "Unknown").strip(),
                'editor': d['editors'][0]['first_name'] + " " + d['editors'][0]['last_name'].strip(),
                'author': d['authors'][0]['first_name'] + " " + d['authors'][0]['last_name'].strip(),
                'title': d['title'] + " (" + assessment_type + ", " + iso3[assessment[0:3]] + ", " + assessment[4:8] + ")",
                'name': urlify(d['title']),
                'owner_org': 'rgi',
                'license_id': 'cc-by',
                'assessment_type': assessment_type,
                'maintainer': 'Natural Resource Governance Institute',
                'maintainer_email': 'index@resourcegovernance.org',
                'version': '2017 Resource Governance Index',
                'country': [iso3[assessment[0:3]],],
                'country_iso3': [assessment[0:3],],
                'assessment_year': [assessment[4:8],],
                'year': year,
                'url': d.get('source', API_ENDPOINT + assessment),
                'subcomponent': subcomponent,
                'category': categories,
                'law_practice_question': law_practice_question,
                'scoring_question': list(scoring_question),
                'question': questions,
                'extras': [
                    {'key': 'spatial_text', 'value': iso3[assessment[0:3]]},
                    {'key': 'spatial_uri', 'value': 'http://publications.europa.eu/resource/authority/country/' + assessment[0:3]}
                ],
                'resources': [
                    {
                        'name': d['title'],
                        'url': d['s3_url'],
                        'license': 'https://creativecommons.org/licenses/by/4.0/',
                        'answers': d['answers'],
                        'questions': d['questions'],
                        'assessments': d['assessments']
                    }
                ]
            }
            
            if urlify(d['title']) in datasets:
                print "Warning, dataset already exists..."
                print "This:"
                print new_dataset
                print "That:"
                print datasets[urlify(d['title'])]
                duplicates.append(new_dataset['resources'][0]['url'] + "," + datasets[urlify(d['title'])]['resources'][0]['url'])
            else:
                datasets[urlify(d['title'])] = new_dataset
            
print "The following questions are invalid:"
all_removals_list = list(all_removals)
all_removals_list.sort(key=lambda x: int(x))
print all_removals_list
print "This led to " + str(dropped_pdfs) + " PDFs being dropped out of a total of " + str(pdfs) + " PDFs"
print "There were " + str(len(duplicates)) + " duplicates:"
for duplicate in duplicates:
    print duplicate
print "Writing out " + str(len(datasets)) + " datasets for CKAN"

with open('./datasets2.json', 'w') as f:
    json.dump(datasets, f, indent=4, separators=(',', ': '))

#Optional feature!   
#with open('./complete.json', 'w') as f:
#    json.dump(complete_metadata, f, indent=4)
