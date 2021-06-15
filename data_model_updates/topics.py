#!/usr/bin/env python

import requests
import csv
import os
import collections
import itertools
BASE_URL = 'http://nrgi.staging.derilinx.com/'
API_KEY = os.environ.get('API_KEY')

headers = {'Authorization': API_KEY}
session = requests.Session()

topic_map = collections.defaultdict(list)

with open('question_map.csv', 'r') as f:
    reader = csv.reader(f)
    for line in reader:
        topic_map[line[0]].append(line[1])

rows = 10
start = 0

params = {
    'fq': "dataset_type:document owner_org:4d781324-aeb9-48e3-9898-2b8c6738a132",
    'sort': 'name asc',
    'rows': 0,
}

resp = session.get(BASE_URL + "api/action/package_search", params = params,
                   headers =headers).json()

total = resp['result']['count']
params['rows'] = rows


def _int(s):
    if isinstance(s, int):
        if s < 1900 or s > 2030:
            return ''
        return s
    try:
        intval = int(s.strip())
        if intval < 1900 or intval > 2030:
            return ''
        return str(intval)
    except:
        return ''

while start < total:
    params['start'] = start
    packages = session.get(BASE_URL + "api/action/package_search", params = params,
                           headers =headers).json()['result']['results']

    for package in packages:
        questions = package.get('question',[])
        topics = [topic_map.get(question,'') for question in questions]
        # topic_map is question -> [topic, topic]
        # flatten with itertools.chain, uniquify with set, and filter for blank with if.
        topic_list = list(s for s in set(itertools.chain(*topics)) if s)
        patch = { 'id': package['id'],
                  'rgi_edition_year': ['2017'],
                  'topic': topic_list
        }

        year = package.get('year','')
        if not year or year == 'N/A':
            patch['year'] = []
            
        if not isinstance(year, list):
            try:
                intval = int(year)
                if intval < 1900 or intval > 2030:
                    year = []
                else:
                    year = [str(intval)]
            except:
                if ';' in year:
                    year = [yr for yr in [_int(s) for s in year.split(';')] if yr]
                
            patch['year'] = year
        else:
            patch['year'] = [yr for yr in [_int(s) for s in year] if yr]
        
        
        print "updating %s" % package['name']
        r = session.post(BASE_URL + "api/action/package_patch", json = patch,
                              headers=headers)

        try:
            r.raise_for_status()
            #print r.json()
        except:
            import pdb; pdb.set_trace()
            print r.content

        
    start += rows

    #if start > 6400:
    #    break
