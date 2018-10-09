import os
import re
import json
import requests
import unicodedata
import sys
import multiprocessing
import ssl
import combine

import csv

API_ENDPOINT = "https://eiti.org/api/v1.0/"

# Number of threads, 0 to disable
MULTITHREAD = 0

# Use HTTP keepalive
session = requests.Session()

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


def writeCsv(name, company_or_govt, year, data):
    filename = "%s-%s-%s.csv" % (name, company_or_govt, year)
    mode = 'wb'

    path = os.path.join('./out', company_or_govt , filename)

    #Split files https://github.com/NRGI/resourcedata.org/issues/13
    if company_or_govt == 'company':
        data.insert(0, 'created,changed,country,iso3,year,start_date,end_date,company_name,gfs_code,gfs_description,name_of_revenue_stream,currency_code,currency_rate,value_reported,value_reported_as_USD,reporting_url,commodities'.split(','))
    else:
        data.insert(0, 'created,changed,country,iso3,year,start_date,end_date,government_agency_name,gfs_code,gfs_description,name_of_revenue_stream,currency_code,currency_rate,value_reported,value_reported_as_USD,reporting_url'.split(','))

    with open(path, mode) as f:
        writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        try:
            writer.writerows(data)
        except Exception as msg:
            print msg
            print type(data)
            print len(data)
            print data


def dataset_name_fromCountry(countryName):
    return "eiti-summary-data-table-for-%s" % sanitizeCountryName(countryName)


def write(meta, data, company_or_govt):
    countryName = meta['country']['label']
    year = meta['label'][-4:]
    sanitizedCountryName = sanitizeCountryName(countryName)

    if not len(data):
        print "empty data for %s %s, %s" % (sanitizedCountryName, year, company_or_govt)
        return
    writeCsv(sanitizedCountryName, company_or_govt, year, data)

    dataset_title = "EITI Summary data table for %s" % countryName
    dataset_name = dataset_name_fromCountry(countryName)

    resource_title_company = "Company payments - %s" % countryName
    resource_title_government = "Revenues received by government agencies - %s" % countryName

    path = '%s-%s.json' %(sanitizedCountryName, year)
    with open(os.path.join('./out/datasets', path), 'w') as f:
        dataset = {
            "title": dataset_title,
            "name": dataset_name,
            "year": [meta['label'][-4:]],
            "notes": general_notes,
            "owner_org": 'eiti',
            "country_iso3": [meta['country']['iso3']],
            "country": [countryName],
            "license_id": "cc-by",
            "maintainer": "Anders Pedersen",
            "maintainer_email": "apedersen@resourcegovernance.org",
            "category": ["Precept 2: Accountability and Transparency"],
            "filename_company": './out/company/%s-company.csv' % sanitizedCountryName,
            "filename_government": './out/government/%s-government.csv' % sanitizedCountryName,
            "resource_title_company": resource_title_company,
            "resource_title_government": resource_title_government
        }
        json.dump(dataset, f)
    return

def sanitizeCountryName(countryName):
    normalizedCountryName = unicodedata.normalize('NFKD', countryName.lower())
    asciiCountryName = normalizedCountryName.encode('ascii', 'ignore')
    return re.sub('[^a-z]', '-', asciiCountryName)

def getSummaryData():
    page = 1
    data = []

    while True:
        print("Getting summary page %s"% page)
        d = session.get(API_ENDPOINT + 'summary_data?page=%s' % page).json()['data']
        if len(d) == 0:
            break
        data.extend(d)
        page += 1

    return data


def getLineForRevenue(d, company, company_or_govt):
    countryn = d['country']['label']
    ciso3 = d['country']['iso3']
    # api returns spurious timestamps in the date created/changed.
    created = "%sT00:00:00+0000" % d['created'].split('T')[0]
    changed = "%sT00:00:00+0000" % d['changed'].split('T')[0]
    year = d['label'][-4:]

    gid = company['gfs_code_id']
    if gid not in gfs:
        j = session.get(API_ENDPOINT + 'gfs_code/' + gid).json()
        temp_gfs_code = j['data'][0]['code']
        for i, c in enumerate(temp_gfs_code):
            if not c.isdigit():
                j['data'][0]['code'] = j['data'][0]['code'][0:i] + "-" + j['data'][0]['code'][i:]
                break
        gfs[gid] = j['data'][0]

    cid = company['organisation_id']
    companyurl = API_ENDPOINT + 'organisation/' + cid
    if cid not in organisations:
        j = session.get(companyurl).json()
        organisations[cid] = j['data'][0]

    rid = company['id']
    revurl = API_ENDPOINT + 'revenue/' + rid
    if rid not in revenues:
        j = session.get(revurl).json()
        revenues[rid] = j['data'][0]

    gfscode = gfs[gid]['code']
    gfsdesc = gfs[gid]['label']
    start_date = d['year_start']
    end_date = d['year_end']

    if company_or_govt == 'company':
        orglabel = organisations[cid]['label'].encode('utf-8')
        rec_agency_name = ''
    else:
        orglabel = ''
        rec_agency_name = organisations[cid]['label'].encode('utf-8')

    valreported = company['original_revenue'] or ''

    valreportedusd = company['revenue'] or ''

    stream_name = revenues[rid]['label']

    currency_code = company['original_currency']

    currency_rate = ''
    try:
        currency_rate = d['country']['metadata'][year]['currency_rate']
    except: pass

    entity_name = ''
    if company_or_govt == 'company':
        entity_name = orglabel.replace('"', '').replace("\n", "; ").strip()
        commodities = (",".join(organisations[cid].get('commodities',None) or []),)
    else:
        entity_name = rec_agency_name.replace('"', '').replace("\n", "; ").strip()
        commodities = tuple()


    #Split files https://github.com/NRGI/resourcedata.org/issues/13
    return (
        created,
        changed,
        countryn.encode('utf-8'),
        ciso3,
        year,
        start_date,
        end_date,
        entity_name,
        gfscode,
        gfsdesc.replace('"', '').replace("\n", "; ").strip().encode('utf-8'),
        stream_name.replace('"', '').replace("\n", "; ").strip().encode('utf-8'),
        currency_code,
        currency_rate,
        valreported,
        valreportedusd,
        companyurl,
        ) + commodities


def gatherCountry(d):
    out_government = []
    out_company = []

    country = d['country']['label']

    year = d['label'][-4:]

    if (d['revenue_company'] or d['revenue_government']):

        sanitizedCountryName = sanitizeCountryName(country)
        print "%s %s" % (sanitizedCountryName, year)
        filename = "%s-%s-%s.csv" % (sanitizedCountryName, "government", year)
        path = os.path.join('./out', "government" , filename)

        if os.path.exists(path):
            print "%s %s exists: continuing" %(sanitizedCountryName, year)
            return


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
                #print out_government[-1]
            except KeyboardInterrupt:
                raise
            except (ssl.SSLError, requests.exceptions.SSLError) as msg:
                continue
            except KeyError:
                continue
            except Exception as msg:
                print msg
                raise
                continue

        for revenue in revcompany:
            try:
                out_company.append(getLineForRevenue(d, revenue, 'company'))
                #print out_company[-1]
            except KeyboardInterrupt:
                raise
            except (ssl.SSLError, requests.exceptions.SSLError) as msg:
                continue
            except KeyError:
                continue
            except Exception as msg:
                print msg
                raise
                continue

        #Split files https://github.com/NRGI/resourcedata.org/issues/13
        write(d, out_government, 'government')
        write(d, out_company, 'company')
    else:
        print "%s %s - No revenue_company or revenue_government" % (country, year)

def setup_directories():
    # Ensure output folders exist
    os.system("mkdir -p ./out/company")
    os.system("mkdir -p ./out/government")
    os.system("mkdir -p ./out/datasets")

def combine_files():
    combine.combine_csv('./out/company')
    combine.combine_csv('./out/government')
    datasets = combine.combine_datasets('./out/datasets')

    # now that that's all done, we'll aggregate them all into a 'total' dataset
    os.system("cat ./out/company/*company.csv | awk '!seen[$0]++' > ./out/all_unique_company.csv")
    os.system("cat ./out/government/*government.csv | awk '!seen[$0]++' > ./out/all_unique_government.csv")

    return datasets

def main():
    setup_directories()

    sum_data = [d for d in getSummaryData() if d.get('country', None)]

    total_len = len(sum_data)
    i = 0

    if MULTITHREAD:
        p = multiprocessing.Pool(MULTITHREAD)
        p.map(gatherCountry, sum_data)
    else:
        for d in sorted(sum_data, key=lambda d: d['label']):
            gatherCountry(d)

    datasets = combine_files()

    year_set = set()
    for d in datasets.values():
        year_set.update(d['year'])

    with open('./datasets.json', 'w') as f:
        alltheyears = list(year_set)
        alltheyears.sort()

        datasets['eiti-complete-summary-table'] = {
            "title": "EITI Complete Summary Data Table",
            "name": "eiti-complete-summary-table",
            "notes": general_notes,
            "year": alltheyears,
            "country": [],
            "country_iso3": [],
            "owner_org": 'eiti',
            "license_id": "cc-by",
            "category": ["Precept 2: Accountability and Transparency"],
            "filename": './out/all_unique.csv',
            "filename_company": './out/all_unique_company.csv',
            "filename_government": './out/all_unique_government.csv',
            "resource_title_company": "Company payments",
            "resource_title_government": "Revenues received by government agencies"
        }
        json.dump(datasets.values(), f)

    return 0

if __name__=='__main__':
    sys.exit(main())
