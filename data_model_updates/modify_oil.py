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

rows = 10
start = 0

org = "4f68d003-ac7f-4d63-b677-6a8db02d54ef"

# staging
if True:
    BASE_URL='https://staging.resourcedata.org/'
    org = 'noclibraryfinalprelaunch'
if False:
    BASE_URL='https://resourcedata.org/'
    org = "8445b050-db86-4cac-92eb-1e233d178993"

params = {
    'fq': "owner_org:%s" % org,
    'sort': 'name asc',
    'rows': 0,
}


resp = session.get(BASE_URL + "api/action/package_search", params = params,
                   headers =headers).json()


total = resp['result']['count']
params['rows'] = rows


while start < total:
    params['start'] = start
    packages = session.get(BASE_URL + "api/action/package_search", params = params,
                           headers =headers).json()['result']['results']
    
    for package in packages:

        patch = {'id': package['id'],
                 'package_type': 'record',
                 'topic': ["State-owned enterprises"],
                 }
        
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
