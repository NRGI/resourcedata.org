import os
import re
import json
import requests
import unicodedata

API_ENDPOINT = "https://eiti.org/api/v1.0/"

filesAlreadyWrittenTo = set([])
datasets = {}
tracking = []
allyears = set()
allthecountries = set()
allthecountries_list = []
allthecountries_iso = set()
allthecountries_iso_list = []

# 'caches'
organisations = {}
gfs = {}
revenues = {}

general_notes = """
    The data is published using the Summary Data Template, Version 1.1 as of 05 March 2015.

According to the EITI Standard 5.3.b: "Summary data from each EITI Report should be submitted electronically to the International Secretariat according to the standardised reporting format provided by the International Secretariat" This template should be completed in full and submitted by email by the national secretariat to the International EITI Secretariat following the publication of the report. The data will be used to populate the global EITI data repository, available on the international EITI website.

NB: The data available on ResourceData is republished from the EITI API and covers one section of the Summary Data, Part 3 which is comprised of data on government revenues per revenue stream and company.

Notes for consideration:

Disclaimer: The EITI Secretariat advice that users consult the original reports for detailed information. Where figures are not available in US dollars, the annual average exchange rate is used. Any questions regarding the data collection and Summary Data methodology can be directed to the EITI Secretariat: data@eiti.org or by visiting [eiti.org/summary-data](http://eiti.org/summary-data)
        """


def writeCsv(name, company_or_govt, data):
    filename = name + '-' + company_or_govt + '.csv';
    mode = 'a'
    
    if not (filename in filesAlreadyWrittenTo):
        print 'first time - Setting header'
        #Split files https://github.com/NRGI/resourcedata.org/issues/13
        if company_or_govt == 'company':
            data.insert(0, 'created,changed,country,iso3,year,start_date,end_date,company_name,gfs_code,gfs_description,name_of_revenue_stream,currency_code,currency_rate,value_reported,value_reported_as_USD,reporting_url')
        else:
            data.insert(0, 'created,changed,country,iso3,year,start_date,end_date,government_agency_name,gfs_code,gfs_description,name_of_revenue_stream,currency_code,currency_rate,value_reported,value_reported_as_USD,reporting_url')
        filesAlreadyWrittenTo.add(filename)
        mode = 'w'
        
    with open('./out/' + company_or_govt + '/' + filename, mode) as f:
        for l in data:
            f.write(l.encode('utf-8') + '\n')


def write(meta, data, company_or_govt):
    countryName = meta['country']['label']
    sanitizedCountryName = sanitizeCountryName(countryName)
    writeCsv(sanitizedCountryName, company_or_govt, data)

    dataset_title = "EITI Summary data table for %s" % countryName
    dataset_name = "eiti-summary-data-table-for-%s" % sanitizedCountryName
    
    resource_title_company = "Company payments - %s" % countryName
    resource_title_government = "Revenues received by government agencies - %s" % countryName

    if not (dataset_name in tracking):
        dataset = {
            "title": dataset_title,
            "name": dataset_name,
            "year": [meta['label'][-4:]],
            "notes": general_notes,
            "owner_org": 'eiti',
            "country_iso3": meta['country']['iso3'],
            "country": [countryName],
            "license_id": "cc-by",
            "maintainer": "Anders Pedersen",
            "maintainer_email": "apedersen@resourcegovernance.org",
            "category": "Accountability and Transparency",
            "filename_company": './out/company/%s-company.csv' % sanitizedCountryName,
            "filename_government": './out/government/%s-government.csv' % sanitizedCountryName,
            "resource_title_company": resource_title_company,
            "resource_title_government": resource_title_government
        }
        datasets[dataset_name] = dataset
        tracking.append(dataset_name)
        allyears.add(dataset['year'][0])
    else:
        yearsofar = datasets[dataset_name]['year']
        ysf = set(yearsofar)
        theyear = meta['label'][-4:]
        ysf.add(theyear)
        allyears.add(theyear)
        yearsofar = list(ysf)
        yearsofar.sort()
        datasets[dataset_name]['year'] = yearsofar

def sanitizeCountryName(countryName):
    normalizedCountryName = unicodedata.normalize('NFKD', countryName.lower())
    asciiCountryName = normalizedCountryName.encode('ascii', 'ignore')
    return re.sub('[^a-z]', '-', asciiCountryName)

def getSummaryData():
    page = 1
    done = False
    data = []

    while (done is False):
        d = requests.get(API_ENDPOINT + 'summary_data?page=%s' % page).json()['data']
        if len(d) == 0:
            done = True
        data.extend(d)
        page += 1
    return data


def getLineForRevenue(d, company, company_or_govt):
    countryn = d['country']['label']
    ciso3 = d['country']['iso3']
    created = d['created']
    changed = d['changed']

    gid = company['gfs_code_id']
    if gid not in gfs:
        j = requests.get(API_ENDPOINT + 'gfs_code/' + gid).json()
        temp_gfs_code = j['data'][0]['code']
        for i, c in enumerate(temp_gfs_code):
            if not c.isdigit():
                j['data'][0]['code'] = j['data'][0]['code'][0:i] + "-" + j['data'][0]['code'][i:]
                break
        gfs[gid] = j['data'][0]
    
    cid = company['organisation_id']
    companyurl = API_ENDPOINT + 'organisation/' + cid
    if cid not in organisations:
        j = requests.get(companyurl).json()
        organisations[cid] = j['data'][0]

    rid = company['id']
    revurl = API_ENDPOINT + 'revenue/' + rid
    if rid not in revenues:
        j = requests.get(revurl).json()
        revenues[rid] = j['data'][0]

    gfscode = gfs[gid]['code']
    gfsdesc = gfs[gid]['label']
    start_date = d['year_start']
    end_date = d['year_end']

    if company_or_govt == 'company':
        orglabel = organisations[cid]['label']
        rec_agency_name = ''
    else:
        orglabel = ''
        rec_agency_name = organisations[cid]['label']

    valreported = company['original_revenue']

    valreportedusd = company['revenue']

    stream_name = revenues[rid]['label']

    currency_code = company['original_currency']

    currency_rate = d['country']['metadata'][year]['currency_rate']

    #Split files https://github.com/NRGI/resourcedata.org/issues/13
    returnstring = (
        created + ',' + 
        changed + ',' + 
        countryn + ',' +  # country
        ciso3 + ',' + # iso3
        year + ',"' +
        start_date + '","' + # start year
        end_date + '","'# end year
    )
    
    if company_or_govt == 'company':
        returnstring += orglabel.replace('"', '').replace("\n", "; ").strip() + '",'# org name
    else:
        returnstring += rec_agency_name.replace('"', '').replace("\n", "; ").strip() + '",' # rec agency
        
    return (
        returnstring +
        gfscode + ',"' +  # gfs code
        gfsdesc.replace('"', '').replace("\n", "; ").strip() + '","' +  # gfs desc
        stream_name.replace('"', '').replace("\n", "; ").strip() + '",' +  # stream name
        currency_code + ',' +
        currency_rate + ',' +
        valreported + ',' +  # value reported by company
        valreportedusd + ',' +  # value reported by company in usd
        companyurl  # company irl
    )

# Ensure output folders exist
os.system("mkdir -p ./out/company")
os.system("mkdir -p ./out/government")

sum_data = getSummaryData()
total_len = len(sum_data)
i = 0
for d in sorted(sum_data, key=lambda d: d['label']):
    i += 1

    out_government = []
    out_company = []

    country = d['country']['label']
    
    allthecountries.add(country)
    allthecountries_iso.add(d['country']['iso3'])
    
    year = d['label'][-4:]

    if (d['revenue_company'] or d['revenue_government']):
        print "%s/%s  %s %s" % (i, total_len, country, year)

        #Split files https://github.com/NRGI/resourcedata.org/issues/13
        revgovt = []
        revcompany = []

        if 'revenue_government' in d and not (d['revenue_government'] is None):
            revgovt.extend(d['revenue_government'])
        if 'revenue_company' in d and not (d['revenue_company'] is None):
            revcompany.extend(d['revenue_company'])

        for revenue in revgovt:
            try:
                out_government.append(getLineForRevenue(d, revenue, 'government'))
            except Exception:
                continue

        for revenue in revcompany:
            try:
                out_company.append(getLineForRevenue(d, revenue, 'company'))
            except Exception:
                continue
            
        #Split files https://github.com/NRGI/resourcedata.org/issues/13
        write(d, out_government, 'government')
        write(d, out_company, 'company')
    else:
        print "%s/%s  %s %s - No revenue_company or revenue_government" % (i, total_len, country, year)

# now that that's all done, we'll aggregate them all into a 'total' dataset
os.system("cat ./out/company/* | awk '!seen[$0]++' > ./out/all_unique_company.csv")
os.system("cat ./out/government/* | awk '!seen[$0]++' > ./out/all_unique_government.csv")

with open('./datasets.json', 'w') as f:
    alltheyears = list(allyears)
    alltheyears.sort()
    allthecountries_list = list(allthecountries)
    allthecountries_list.sort()
    allthecountries_iso_list = list(allthecountries_iso)
    allthecountries_iso_list.sort()
    
    datasets['eiti-complete-summary-table'] = {
        "title": "EITI Complete Summary Data Table",
        "name": "eiti-complete-summary-table",
        "notes": general_notes,
        "year": alltheyears,
        "country": allthecountries_list,
        "country_iso3": allthecountries_iso_list,
        "owner_org": 'eiti',
        "license_id": "cc-by",
        "category": "Accountability and Transparency",
        "filename": './out/all_unique.csv',
        "filename_company": './out/all_unique_company.csv',
        "filename_government": './out/all_unique_government.csv',
        "resource_title_company": "Company payments",
        "resource_title_government": "Revenues received by government agencies"
    }
    json.dump(datasets.values(), f)

