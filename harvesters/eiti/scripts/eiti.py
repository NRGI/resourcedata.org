#!/usr/bin/env python

#
# Script to only crawl the EITI data that has been reported changed.
#
# Relies heavily on the existing scripts to do the detail work
#

import time
import requests
import json
import os

import eiti_import
import extract_summary

session = requests.Session()
MOST_RECENT_CHANGE = None

def parseIsoTs(ts):
    return time.strptime(ts.split('T')[0], '%Y-%m-%d')

def hoist_country(summary):
    return summary['label'][:-6]

def hoist_year(summary):
    return summary['label'][-4:]

def update_recent(dt):
    global MOST_RECENT_CHANGE

    if not MOST_RECENT_CHANGE:
        MOST_RECENT_CHANGE = dt

    MOST_RECENT_CHANGE = max(dt, MOST_RECENT_CHANGE)

def pr_safe(s):
    return extract_summary.sanitizeCountryName(s)

def checkForUpdates(summary):
    """ Checks the metadata and the years to see if we need to harvest

    :param summary: entry,
    :returns: True if we need to harvest, False if not
    """

    country = hoist_country(summary)
    year = summary['label'][-4:]
    # note that
    summary_modified = parseIsoTs(summary['changed'])

    update_recent(summary_modified)

    dataset_name = extract_summary.dataset_name_fromCountry(country)

    dataset = eiti_import.get_dataset(dataset_name)
    if not dataset:
        print "New country spotted: %s" % (pr_safe(country))
        return True

    # check if there's any point in checking this...
    if not (summary.get('revenue_government',None)
            or summary.get('revenue_company',None)):
        print "No company or government data, skipping %s, %s" % (pr_safe(country), year)
        return False

    # check changed, year
    if not (year in dataset['year']):
        print "New year spotted for %s, %s" %(pr_safe(country), year)
        return True

    dataset_modified = parseIsoTs(dataset['metadata_modified'])

    if summary_modified >= dataset_modified:
        print "Summary data has been updated for %s, %s: on %s, existing %s" %(
            pr_safe(country), year,
            time.strftime('%Y-%m-%d', summary_modified),
            time.strftime('%Y-%m-%d', dataset_modified))
        return True

    print "No change for %s, %s last updated %s" % (
        pr_safe(country), year, time.strftime('%Y-%m-%d', summary_modified))
    return False


def fileName_fromUrl(country, url):
    if 'company' in url:
        return './out/company/%s-company.csv' % extract_summary.sanitizeCountryName(country)
    else:
        return './out/government/%s-government.csv' % extract_summary.sanitizeCountryName(country)

def gather_csvs(country):
    dataset_name = extract_summary.dataset_name_fromCountry(country)
    dataset = eiti_import.get_dataset(dataset_name)
    for resource in dataset['resources']:
        url = resource['url']
        if not url:
            continue
        print "Getting %s" % url
        resp = session.get(url)
        with open(fileName_fromUrl(country, url), 'wb') as f:
            print "Writing %s" % fileName_fromUrl(country, url)
            f.write(resp.content)

def update_complete_dataset(filtered_summaries):
    dataset = eiti_import.get_dataset('eiti-complete-summary-table')
    dataset.update({
        "filename": './out/all_unique.csv',
        "filename_company": './out/all_unique_company.csv',
        "filename_government": './out/all_unique_government.csv',
        "resource_title_company": "Company payments",
        "resource_title_government": "Revenues received by government agencies",

    })


    for summary in filtered_summaries:
        year = summary['label'][-4:]

        if not year in dataset['year']:
            dataset['year'].append(year)

    dataset['year'].sort()
    dataset['country'] = []
    dataset['country_iso3'] = []

    return dataset


def main():
    update_all = os.environ.get('UPDATE_ALL', None)
    use_cached_summaries = os.environ.get('USE_CACHED_SUMMARIES', None)

    extract_summary.setup_directories()

    if use_cached_summaries:
        print('Loading cached summaries from ./out/summaries.json')
        with open('./out/summaries.json') as f:
            summaries = json.load(f)
    else:
        # SummaryData returns a list of datasets, each one a country/year pair
        summaries = extract_summary.getSummaryData()
        # Cache summaries on disk
        extract_summary.store_summaries(summaries)

    if update_all:
        for summary in summaries:
            extract_summary.gatherCountry(summary)
        filtered_summaries = summaries
    else:
        # Check which countries to update
        countries_to_update = set([hoist_country(s) for s in summaries if checkForUpdates(s)])

        print "Most recent upstream change: %s" % time.strftime('%Y-%m-%d', MOST_RECENT_CHANGE)

        if len(countries_to_update):
            print "There are %d countries that need updating" % len(countries_to_update)
            print "\n".join(countries_to_update)
        else:
            print "There are no changes to report"
            return

        # Grab all the data for each country that needs updated.
        filtered_summaries = [s for s in summaries if hoist_country(s) in countries_to_update]


        unchanged_countries = set([hoist_country(s) for s in summaries
                                   if hoist_country(s) not in countries_to_update])

        for country in unchanged_countries:
            gather_csvs(country)

        for summary in filtered_summaries:
            extract_summary.gatherCountry(summary)

    #combine the files, pop in the eiti combined dataset table
    datasets = extract_summary.combine_files()
    datasets['eiti-complete-summary-table'] = update_complete_dataset(filtered_summaries)

    with open('./datasets.json', 'w') as f:
        json.dump(datasets.values(), f)

    # delegate to the old import script for those items we want to update
    eiti_import.main()

if __name__=='__main__':
    main()
