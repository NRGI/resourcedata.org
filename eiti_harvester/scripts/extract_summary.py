import os
import re
import json
import requests
import progressbar
import unicodedata

API_ENDPOINT = "https://eiti.org/api/v1.0/"

filesAlreadyWrittenTo = set([])
datasets = []

# 'caches'
organisations = {}
gfs = {}
revenues = {}


def writeCsv(name, data):
    mode = 'a'
    if not (name in filesAlreadyWrittenTo):
        data.insert(0, 'country,iso3,year,start_date,end_date,company_name,name_of_recieving_agency,government_or_company,gfs_code,gfs_description,name_of_revenue_stream,currency_code,currency_rate,value_reported,value_reported_as_USD,reporting_url')
        filesAlreadyWrittenTo.add(name)
        mode = 'w'
    with open('./out/' + name, mode) as f:
        for l in data:
            f.write(l.encode('utf-8') + '\n')


def write(meta, data):
    countryName = meta['country']['label']
    sanitizedCountryName = sanitizeCountryName(countryName)
    writeCsv(sanitizedCountryName + '.csv', data)

    dataset = {
        "title": "EITI Summary Data Table for %s" % countryName,
        "name": "eiti-summary-data-table-for-%s" % sanitizedCountryName,
        "notes": """
    The data is published using the Summary Data Template, Version 1.1 as of 05 March 2015.

According to the EITI Standard 5.3.b: "Summary data from each EITI Report should be submitted electronically to the International Secretariat according to the standardised reporting format provided by the International Secretariat" This template should be completed in full and submitted by email by the national secretariat to the International EITI Secretariat following the publication of the report. The data will be used to populate the global EITI data repository, available on the international EITI website.

NB: The data available on ResourceData is republished from the EITI API and covers one section of the Summary Data, Part 3 which is comprised of data on government revenues per revenue stream and company.

Notes for consideration:

Disclaimer: The EITI Secretariat advice that users consult the original reports for detailed information. Where figures are not available in US dollars, the annual average exchange rate is used. Any questions regarding the data collection and Summary Data methodology can be directed to the EITI Secretariat: data@eiti.org or by visiting [eiti.org/summary-data](http://eiti.org/summary-data)
        """,
        "owner_org": 'eiti',
        "country_iso3": meta['country']['iso3'],
        "country": countryName,
        "license_id": "cc-by",
        "maintainer": "Anders Pedersen",
        "maintainer_email": "apedersen@resourcegovernance.org",
        "category": "Accountability and Transparency",
        "filename": './out/%s.csv' % sanitizedCountryName
    }

    if not (dataset in datasets):
        datasets.append(dataset)

        with open('./datasets.json', 'w') as f:
            json.dump(datasets, f)


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

    gid = company['gfs_code_id']

    if gid not in gfs:
        j = requests.get(API_ENDPOINT + 'gfs_code/' + gid).json()
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

    return (
        countryn + ',' +  # country
        ciso3 + ',' +  # iso3
        year + ',"' +
        start_date + '","' +  # start year
        end_date + '","' +  # end year
        orglabel + '","' +  # org name
        rec_agency_name + '",' +  # rec agency
        company_or_govt + ',' +
        gfscode + ',"' +  # gfs code
        gfsdesc + '","' +  # gfs desc
        stream_name + '",' +  # stream name
        currency_code + ',' +
        currency_rate + ',' +
        valreported + ',' +  # value reported by company
        valreportedusd + ',' +  # value reported by company in usd
        companyurl  # company irl
    )


sum_data = getSummaryData()
total_len = len(sum_data)
i = 0
for d in sorted(sum_data, key=lambda d: d['label']):
    i += 1

    out = []

    country = d['country']['label']
    year = d['label'][-4:]

    if (d['revenue_company'] or d['revenue_government']):
        print "%s/%s  %s %s" % (i, total_len, country, year)

        revgovt = []
        revcompany = []

        if 'revenue_government' in d and not (d['revenue_government'] is None):
            revgovt.extend(d['revenue_government'])
        if 'revenue_company' in d and not (d['revenue_company'] is None):
            revcompany.extend(d['revenue_company'])

        for revenue in revgovt:
            try:
                out.append(getLineForRevenue(d, revenue, 'government'))
            except Exception:
                continue

        for revenue in revcompany:
            try:
                out.append(getLineForRevenue(d, revenue, 'company'))
            except Exception:
                continue
        write(d, out)
    else:
        print "%s/%s  %s %s - No revenue_company or revenue_government" % (i, total_len, country, year)

# now that that's all done, we'll aggregate them all into a 'total' dataset
os.system("cat ./out/* | awk '!seen[$0]++' > ./out/all_unique.csv")

with open('./datasets.json', 'r+') as f:
    datasets = json.load(f)
    f.seek(0)
    datasets.append({
        "title": "EITI Complete Summary Data Table",
        "name": "eiti-complete-summary-table",
        "owner_org": 'eiti',
        "license_id": "cc-by",
        "category": "Accountability and Transparency",
        "filename": './out/all_unique.csv'
    })
    json.dump(datasets, f)
    f.truncate()
