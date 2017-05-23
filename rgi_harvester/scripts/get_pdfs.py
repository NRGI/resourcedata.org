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

question_categories = {}
with open('./questions.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        question_categories[row['Q'].zfill(3)] = row['Component']

with open('./assessments.csv', 'r') as f:
    assessments = [l.strip().replace('"','').replace('"','') for l in f.readlines()]

datasets = {}


def urlify(s):
    return s.lower().replace(' ', '-').replace(':', '')

for assessment in assessments:
    #Used for skipping/testing
    #if "CIV" not in assessment:
    #    continue
    r = requests.get(API_ENDPOINT + assessment)
    docs = r.json()

    print '%s has %s pdfs' % (assessment, len([d for d in docs if d['mime_type'] == "application/pdf"]))

    for d in docs:
        if (d['mime_type'] == 'application/pdf'):
            category = ''
            questions = []

            try:
                category = question_categories[d['answers'][0][-3:]]
                questions = [q[-3:] for q in d['answers']]
            except:
                continue

            assessment_type_abbr = assessment[-2:]
            if assessment_type_abbr == "HY":
                assessment_type = "Oil and Gas"
            elif assessment_type_abbr == "MI":
                assessment_type = "Mining"
            else:
                assessment_type = "Unknown"

            datasets[urlify(d['title'])] = {
                'title': d['title'] + " (" + assessment_type + ", " + iso3[assessment[0:3]] + ", " + assessment[4:8] + ")",
                'name': urlify(d['title']),
                'owner_org': 'rgi',
                'license_id': 'cc-by',
                'assessment_type': assessment_type,
                'maintainer': 'Natural Resource Governance Institute',
                'maintainer_email': 'index@resourcegovernance.org',
                'version': '2017 Resource Governance Index',
                'country': iso3[assessment[0:3]],
                'country_iso3': assessment[0:3],
                'year': assessment[4:8],
                'url': API_ENDPOINT + assessment,
                'category': category,
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

with open('./datasets2.json', 'w') as f:
    json.dump(datasets, f, indent=4, separators=(',', ': '))