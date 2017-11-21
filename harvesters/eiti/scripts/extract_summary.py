import os
import re
import json
import requests
import unicodedata
import unicodecsv as csv

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

#From Python 3.5, https://stackoverflow.com/questions/5595425/what-is-the-best-way-to-compare-floats-for-almost-equality-in-python#33024979
def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

def write(meta, data, company_or_govt_or_combined):
    countryName = meta['country']['label']
    sanitizedCountryName = sanitizeCountryName(countryName)
    writeCsv(sanitizedCountryName, company_or_govt_or_combined, data)

    dataset_title = "EITI Summary data table for %s" % countryName
    dataset_name = "eiti-summary-data-table-for-%s" % sanitizedCountryName
    
    resource_title_company = "Company payments - %s" % countryName
    resource_title_government = "Revenues received by government agencies - %s" % countryName
    resource_title_combined = "Matched transactions - %s" % countryName

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
            "category": ["Precept 2: Accountability and Transparency"],
            "filename_company": './out/company/%s-company.csv' % sanitizedCountryName,
            "filename_government": './out/government/%s-government.csv' % sanitizedCountryName,
            "filename_combined": './out/government/%s-government.csv' % sanitizedCountryName,
            "resource_title_company": resource_title_company,
            "resource_title_government": resource_title_government,
            "resource_title_combined": resource_title_combined
        }
        datasets[dataset_name] = dataset
        tracking.append(dataset_name)
        allyears.add(dataset['year'][0])
    else:
        yearsofar = datasets[dataset_name]['year']
        ysf = set(yearsofar)
        myyear = meta['label'][-4:]
        ysf.add(myyear)
        allyears.add(myyear)
        yearsofar = list(ysf)
        yearsofar.sort()
        datasets[dataset_name]['year'] = yearsofar

def sanitizeCountryName(countryName):
    normalizedCountryName = unicodedata.normalize('NFKD', countryName.lower())
    asciiCountryName = normalizedCountryName.encode('ascii', 'ignore')
    return re.sub('[^a-z]', '-', asciiCountryName)

def getSummaryData():
    offline = True
    page = 1
    done = False
    data = []
    if (offline):
        with open ("rawdata.json", "rb") as jsonfile:
            data = json.loads(jsonfile.read())
    else:
        while (done is False):
            d = requests.get(API_ENDPOINT + 'summary_data?page=%s' % page).json()['data']
            if len(d) == 0:
                done = True
            data.extend(d)
            page += 1
        #with open ("rawdata.json", "wb") as jsonfile:
        #    jsonfile.write(json.dumps(data))
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
        try:
            j = requests.get(companyurl).json()
            organisations[cid] = j['data'][0]
        except:
            print "Error: " + companyurl + " failed"
            organisations[cid] = {}
            organisations[cid]['label'] = 'Unknown'

    rid = company['id']
    revurl = API_ENDPOINT + 'revenue/' + rid
    if rid not in revenues:
        try:
            j = requests.get(revurl).json()
            revenues[rid] = j['data'][0]
        except:
            print "Error: " + revurl + " failed"
            revenues[rid] = {}
            revenues[rid]['label'] = 'Unknown'
            

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

    #Weird bug in API that we probably shouldn't completely ignore; may not happen in online version
    if valreported == '0' or valreportedusd == '0' or valreported == None or valreportedusd == None:
         valreported = '0'
         valreportedusd = '0'

    stream_name = revenues[rid]['label']

    currency_code = company['original_currency']

    if type(d['country']['metadata']) == dict:
        currency_rate = d['country']['metadata'][year]['currency_rate']
    else:
        print "Error: Metadata is missing,can't get currency rate"
        currency_rate = "Unknown"

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

    disaggregated = {}

    if type(d['country']['metadata']) == dict:
        for theyear, report in dict.items(d['country']['metadata']):
            if report['disaggregated']['revenue_stream'] == "1" and report['disaggregated']['company'] == "1":
                disaggregated[theyear] = True
            #elif report['disaggregated']['revenue_stream'] == "1":
            #    print "Error: rev stream is disag but company not"
            #    exit()
            #elif report['disaggregated']['company'] == "1":
            #    print "Error: company is disag but rev stream not"
            #    exit()
            else:
                disaggregated[theyear] = False
    else:
        print "Error: Metadata is missing, assuming not disaggregated"
        for y in range(1990, 2020):
            disaggregated[str(y)] = False

    if (d['revenue_company'] or d['revenue_government']):
        print "%s/%s  %s %s" % (i, total_len, country, year)

        #Split files https://github.com/NRGI/resourcedata.org/issues/13
        revgovt = []
        revcompany = []

        if 'revenue_government' in d and not (d['revenue_government'] is None):
            revgovt = d['revenue_government']
        if 'revenue_company' in d and not (d['revenue_company'] is None):
            revcompany = d['revenue_company']

        for revenue in revgovt:
            out_government.append(getLineForRevenue(d, revenue, 'government'))

        for revenue in revcompany:
            out_company.append(getLineForRevenue(d, revenue, 'company'))
        
        #Split files https://github.com/NRGI/resourcedata.org/issues/13
        write(d, out_government, 'government')
        write(d, out_company, 'company')
        
        #Join up where possible
        #https://github.com/NRGI/resourcedata.org/issues/13
        #May seem crazy to read them back in etc. after splitting and writing out, but we
        #can only do it for some files/rows, so this seem's smart enough for now
        matched = 0
        to_match = len(out_company)
        
        #Regenerate the country name so we know what file to read in
        countryName = d['country']['label']
        sanitizedCountryName = sanitizeCountryName(countryName)
        
        comp_rows = []
        gmt_rows = []
        totalled_government_rows = []
        totalled_government_rows_indexed = {}
        matches = []

        #Read in company payments
        with open('./out/company/' + sanitizedCountryName + '-company.csv', 'rb') as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                comp_rows.append(row)

        #Read in government receipts
        with open('./out/government/' + sanitizedCountryName + '-government.csv', 'rb') as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                gmt_rows.append(row)

        def dosum(srows):
            total = 0
            for srow in srows:
                total += float(srow['value_reported'])
            return total

        #Generate government receipt -totals-
        for row in gmt_rows:
            #print "Row has year " + row['year']
            not_found = True
            if disaggregated[row['year']]:
                #Group related stuff together - this would probably be a great place to use dataframes (pandas) #TODO
                if row['year'] not in totalled_government_rows_indexed:
                    totalled_government_rows_indexed[row['year']] = {}
                if row['gfs_code'] not in totalled_government_rows_indexed[row['year']]:
                    totalled_government_rows_indexed[row['year']][row['gfs_code']] = {}
                if row['name_of_revenue_stream'].lower() not in totalled_government_rows_indexed[row['year']][row['gfs_code']]:
                    totalled_government_rows_indexed[row['year']][row['gfs_code']][row['name_of_revenue_stream'].lower()] = {}
                    #We're going to track these three. Everything else should be equal. We could add some checks for that later.
                    totalled_government_rows_indexed[row['year']][row['gfs_code']][row['name_of_revenue_stream'].lower()]['local_total'] = []
                    totalled_government_rows_indexed[row['year']][row['gfs_code']][row['name_of_revenue_stream'].lower()]['us_total'] = []
                totalled_government_rows_indexed[row['year']][row['gfs_code']][row['name_of_revenue_stream'].lower()]['local_total'].append(float(row['value_reported']))
                totalled_government_rows_indexed[row['year']][row['gfs_code']][row['name_of_revenue_stream'].lower()]['us_total'].append(float(row['value_reported_as_USD']))
                #Copy of data for later
                totalled_government_rows_indexed[row['year']][row['gfs_code']][row['name_of_revenue_stream'].lower()]['orig_row'] = row
                
        #Now convert back to simple rows
        for year_in in totalled_government_rows_indexed:
            for gfs_code_in in totalled_government_rows_indexed[year_in]:
                for rev_str_in in totalled_government_rows_indexed[year_in][gfs_code_in]:
                    newrow = totalled_government_rows_indexed[year_in][gfs_code_in][rev_str_in]['orig_row'].copy()
                    newrow['value_reported'] = sum(totalled_government_rows_indexed[year_in][gfs_code_in][rev_str_in]['local_total'])
                    newrow['value_reported_as_USD'] = sum(totalled_government_rows_indexed[year_in][gfs_code_in][rev_str_in]['us_total'])
                    totalled_government_rows.append(newrow)
                    
        #For each g'ment sum, look for companies paying in
        for row in totalled_government_rows:
            not_found = True
            #No income, no payments
            if row['value_reported'] == 0:
                continue
            search_gfs = row['gfs_code']
            search_st = row['name_of_revenue_stream'].lower()
            search_amount = float(row['value_reported'])
            search_year = row['year']
            print "Looking for gfs: " + search_gfs + " / str: " + search_st + " / amount: " + str(row['value_reported']) + " / year: " + search_year
            ind_matches = []
            #Look for matching rows in companies; store for summing
            for grow in comp_rows:
                if search_gfs == grow['gfs_code'] and search_st == grow['name_of_revenue_stream'].lower() and search_year == grow['year']:
                    not_found = False
                    print "Found a matching company payment, accumulating..."
                    ind_matches.append(grow.copy())
                    del grow #Prevent reuse
            #Check sum for equality with government sum
            if isclose(dosum(ind_matches), search_amount):
                print "The total company payments match the total government receipts"
                #Now we have diff. info for each company, so keep them as sep. rows and add in the government columns without duplicating columns
                for match in ind_matches:
                    nc = match.copy()
                    nc.update(row) #Merge in government info (same for every row and mostly overlapping info)
                    matches.append(nc)
                    matched += 1
            else:
                print "Error: sum should be: " + str(search_amount) + " but sum is: " + str(dosum(ind_matches))
            if not_found:
                print "Error: despite disaggregated info, there are no company contributions for the government receipt"
        print "Matched " + str(matched) + " of " + str(to_match) + " company rows to government receipts"
        
        #Write out results
        #write(d, matches, 'combined')
    
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
        "category": ["Precept 2: Accountability and Transparency"],
        "filename": './out/all_unique.csv',
        "filename_company": './out/all_unique_company.csv',
        "filename_government": './out/all_unique_government.csv',
        "resource_title_company": "Company payments",
        "resource_title_government": "Revenues received by government agencies"
    }
    json.dump(datasets.values(), f)

