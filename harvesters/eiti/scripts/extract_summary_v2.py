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

import logging
log = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


import eiti_api_v2 as api

MULTITHREAD=0

general_notes = """
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
        data.insert(0, 'created,changed,country,iso3,year,start_date,end_date,company_name,gfs_code,gfs_description,name_of_revenue_stream,currency_code,currency_rate,value_reported,value_reported_as_USD,reporting_url,commodities,company_identification'.split(','))
    else:
        data.insert(0, 'created,changed,country,iso3,year,start_date,end_date,government_agency_name,gfs_code,gfs_description,name_of_revenue_stream,currency_code,currency_rate,value_reported,value_reported_as_USD,reporting_url'.split(','))

    with open(path, mode) as f:
        writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        try:
            writer.writerows(data)
        except Exception as msg:
            print(msg)
            print(type(data))
            print(len(data))
            print(data)


def dataset_name_fromCountry(countryName):
    return "eiti-summary-data-table-for-%s" % sanitizeCountryName(countryName)


def write(meta, data, company_or_govt):
    countryName = meta['country']['label']
    year = meta['label'][-4:]
    sanitizedCountryName = sanitizeCountryName(countryName)

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
            'topic': ["Open data", "Revenue sharing", "Global initiatives"],
            'last_updated': meta.changed,
            'created': meta.created,
            "maintainer": "Tommy Morrison",
            "maintainer_email": "tmorrison@resourcegovernance.org",
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
    api.gfs_codes() # grab all, store in cache
    api.countries() # grab all, store in cache
    return api.all_summary_data_obj()

def formatGfsCode(orig):
    for i, c in enumerate(orig):
        if not c.isdigit():
            return orig[0:i] + "-" + orig[i:]
    return orig

def _formatName(s):
    return s.encode('utf-8').replace('"', '').replace("\n", "; ").strip()

def getLineForRevenue(summary, revenue, company_or_govt):
    countryn = summary.country.label
    ciso3 = summary.country.iso3
    # api returns spurious timestamps in the date created/changed.
    created = summary.created
    changed = summary.changed
    year = summary.label[-4:]

    # If the org or gfs is missing, and the revenue is not 0, then we will
    # continue with the missing data. The values in the CSV will be blank
    # for those items.

    org = revenue.organisation
    if not org:
        # some of the linked data
        # (e.g. https://eiti.org/api/v2.0/revenue/479968) has a bare org.
        if revenue.revenue == 0:
            log.info("getLineForRevenue: org is null: %s", revenue.self)
            return

    gfs = revenue.gfs
    if not gfs:
        if revenue.revenue == 0:
            log.info("getLineForRevenue: gfs is null: %s", revenue.self)
            return

    gfscode = formatGfsCode(gfs.get('code',''))
    gfsdesc = _formatName(gfs.get('label',''))
    start_date = summary.year_start
    end_date = summary.year_end

    entity_name = _formatName(org.get('label',''))

    valreported = revenue.get('original_revenue', '')
    valreportedusd = revenue.revenue
    stream_name = revenue.label
    currency_code = revenue.currency

    currency_rate = ''
    try:
        currency_rate = d['country']['metadata'][year]['currency_rate']
    except: pass

    company_extras = tuple()
    if company_or_govt == 'company':
        company_extras = (",".join(org.get('commodities',None) or []).encode('utf-8'),
                          (org.get('identification', '') or '').replace("\n", ",").encode('utf-8'))


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
        gfsdesc,
        _formatName(stream_name),
        currency_code,
        currency_rate,
        valreported,
        valreportedusd,
        org.get('self', '')
        ) + company_extras


def gatherCountry(summary):
    out_government = []
    out_company = []

    country = summary.country.label
    year = summary.label[-4:]

    if not ('revenue_company' in summary or 'revenue_government' in summary):
        log.info("gatherCountry: %s %s - No revenue_company or revenue_government", country, year)
        return

    sanitizedCountryName = sanitizeCountryName(country)
    log.info("gatherCountry: %s %s", sanitizedCountryName, year)
    filename = "%s-%s-%s.csv" % (sanitizedCountryName, "government", year)
    path = os.path.join('./out', "government" , filename)

    if os.path.exists(path):
        print("%s %s exists: continuing" %(sanitizedCountryName, year))
        return

    # precache these
    try:
        org_list = api.organisation_forSummary(summary.id)
    except requests.exceptions.HTTPError:
        # some summaries don't have this info, if this doesn't work, it's probably
        # going to be empty anyway
        log.error("gatherCountry: Exception getting org_list for: %s", summary.id)
    try:
        revenue_list = api.revenue_forSummary(summary.id)
    except requests.exceptions.HTTPError:
        log.error("gatherCountry: Exception getting revenue_list for: %s", summary.id)

    #Split files https://github.com/NRGI/resourcedata.org/issues/13
    revgovt = summary.revenue_government or []
    revcompany = summary.revenue_company or []

    for revenue in revgovt:
        if not revenue: continue
        try:
            record = getLineForRevenue(summary, revenue, 'government')
            if record:
                out_government.append(record)
            #print out_government[-1]
        except KeyboardInterrupt:
            raise
        except (ssl.SSLError, requests.exceptions.SSLError) as msg:
            continue
        except KeyError:
            continue
        except Exception as msg:
            log.error("gatherCountry: Exception in government: %s", msg)
            raise
            continue

    for revenue in revcompany:
        if not revenue: continue
        try:
            record = getLineForRevenue(summary, revenue, 'company')
            if record:
                out_company.append(record)
            #print out_company[-1]
        except KeyboardInterrupt:
            raise
        except (ssl.SSLError, requests.exceptions.SSLError) as msg:
            continue
        except KeyError:
            continue
        except Exception as msg:
            log.error("gatherCountry: Exception in company: %s", msg)
            raise
            continue

    #Split files https://github.com/NRGI/resourcedata.org/issues/13
    write(summary, out_government, 'government')
    write(summary, out_company, 'company')


def gatherCountry_asJson(json_dict):
    data_dict = json.loads(json_dict)
    return gatherCountry(api.SummaryData(data_dict))

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

    allthecountries = set()
    allthecountries_list = []
    allthecountries_iso = set()
    allthecountries_iso_list = []

    for d in sorted(sum_data, key=lambda d: d['label']):
        country = d['country']['label']

        allthecountries.add(country)
        allthecountries_iso.add(d['country']['iso3'])

    if MULTITHREAD:
        p = multiprocessing.Pool(MULTITHREAD)
        p.map(gatherCountry_asJson, [s.to_json() for s in sum_data])
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
            "category": ["Precept 2: Accountability and Transparency"],
            'topic': ["Open data", "Revenue sharing", "Global initiatives"],
            "filename": './out/all_unique.csv',
            "filename_company": './out/all_unique_company.csv',
            "filename_government": './out/all_unique_government.csv',
            "resource_title_company": "Company payments",
            "resource_title_government": "Revenues received by government agencies"
        }
        json.dump(list(datasets.values()), f)

    return 0

if __name__=='__main__':
    if len(sys.argv) > 1:
        setup_directories()
        api.gfs_codes()
        summary = api.summary_data_obj_fromId(sys.argv[1])
        gatherCountry(summary)
        sys.exit(0)
    else:
        sys.exit(main())
