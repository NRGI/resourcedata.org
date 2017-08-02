# -*- coding: utf-8 -*-
import os
import json
import requests
import urllib
import filecmp

failed_states = []

API_HOST = os.environ['API_HOST']
API_KEY = os.environ['API_KEY']

#See https://github.com/NRGI/resourcedata.org/issues/25
#For now this is just mapping to what's in the schema (link below), but we may need to change the schema to be ISO conformant
ckan_names = {
    u'Democratic Republic of Congo': u'Congo, the Democratic Republic of the',
    u'Kyrgyz Republic': u'Kyrgyzstan',
    u'Republic of the Congo': u'Congo, the Democratic Republic of the',
    u'Tanzania': u'Tanzania, United Republic of',
    u'United States of America': u'United States'
}

def mapcountry(countryname):
    if countryname in (u'Democratic Republic of Congo', u'Kyrgyz Republic', u'Republic of the Congo', u'Tanzania', u'United States of America'):
        return ckan_names[countryname]
    else:
        return countryname

def api_get(action, data={}):
    print API_HOST + "/api/action/"+action
    return requests.get(
        API_HOST+"/api/action/"+action,
        params=data,
        verify=True,
        headers={"Authorization": API_KEY})


def api_post(action, data={}):
    return requests.post(
        API_HOST+"/api/action/"+action,
        verify=True,
        json=data,
        headers={"Authorization": API_KEY, "Content-Type": "application/json"})


def create_org(org):
    print "CREATING ORG " + org['name']
    r = api_post("organization_create", data=org)
    print r
    return org['name']


def update_org(org):
    print "UPDATING ORG " + org['name']
    r = api_post("organization_create", data=org)
    print r
    return org['name']


def upsert_org(org):
    r = api_get("organization_show", data={'id': org['name']})
    jsondata = r.json()
    print jsondata
    already_exists = jsondata.get("success")
    if not already_exists:
        return create_org(org)
    else:
        return update_org(org)


def create_dataset(data):
    print "CREATING DATASET " + data['name']
    r = api_post("package_create", data=data)
    jsonified = r.json()
    print "CREATE DATASET RESULT:"
    print jsonified
    if ('error' in jsonified):
        failed_states.append(data['country'])
    return True, jsonified


def update_dataset(data, existing):
    need_to_update = False
    #Test each key of data vs what's in existing; any differences, do update
    for key in data.keys():
        #print key
        #print data[key]
        #if key in existing: print existing[key]
        #else: print 'NONE'
        #owner_org gets returned as uuid, we have name... just don't bother; other things don't make it into CKAN, assume other things are new and should be added
        if key not in ("owner_org", "filename_government", "resource_title_government", "resource_title_company", "filename_company") and (key not in existing or data[key] != existing[key]):
            need_to_update = True
            break
    
    if need_to_update:
        print "DATASET " + data['name'] + " NEEDS UPDATE, UPDATING"
        #Patch so that we don't lose resources
        data['id'] = existing['id'] #Patch needs ID
        #TEMPORARY! Do delete resources to prevent empty resources by doing package_update
        r = api_post("package_update", data=data).json() #instead of package_patch
        print "PATCH DATASET RESULT:"
        print r
        if ('error' in r):
            failed_states.append(data['country'])
        return False, r.get("result")
    else:
        print "DATASET " + data['name'] + " UNCHANGED"
        return False, existing


def upsert_dataset(data):
    print "UPSERTING DATASET " + data['name']
    r = api_get("package_show", data={'id': data['name']})
    jsondata = r.json()
    already_exists = jsondata.get("success")
    if already_exists:
        print "DATA FROM CKAN (EXISTING):"
        print jsondata['result']
        return update_dataset(data, jsondata['result'])
    else:
        return create_dataset(data)


def create_resource(dataset_name, resource_path, resource_name):
    line_count = 0
    with open('./datasets.json', 'r') as testf:
        for line in testf:
            line_count += 1
            if line_count > 2:
                break
    if line_count == 2:
        print "NOT UPLOADING RESOURCE (EMPTY)"
        return
        
    #Nice filename - workaround needed for one country
    friendly_resource_name = resource_name.replace(u'ô', 'o')
    
    print "UPLOADING RESOURCE (NEW) " + resource_path[5:] + " TO DATASET " + dataset_name

    r = requests.post('%s/api/action/resource_create' % (API_HOST),
                      data={
                          "package_id": dataset_name,
                          "type": "file.upload",
                          "name": resource_name,
                          "format": "csv"
                      },
                      headers={"Authorization": API_KEY},
                      files={'upload':(friendly_resource_name + '.csv', file(resource_path))})
    
    print "CREATE RESOURCE RESULT:"
    print r.json()
    
def update_resource(resource_id, resource_path, resource_name):
    #Nice filename - workaround needed for one country
    friendly_resource_name = resource_name.replace(u'ô', 'o')
    
    print "UPLOADING RESOURCE (UPDATE) " + resource_path[5:] + " TO RESOURCE " + resource_id

    r = requests.post('%s/api/action/resource_update' % (API_HOST),
                      data={
                          "id": resource_id,
                          "type": "file.upload",
                          "name": resource_name,
                          "format": "csv"
                      },
                      headers={"Authorization": API_KEY},
                      files={'upload':(friendly_resource_name + '.csv', file(resource_path))})
    
    print "UPDATE RESOURCE RESULT:"
    print r.json()


def compare(remote_file, local_file):
    urllib.urlretrieve(remote_file, "temp.csv")
    return filecmp.cmp("temp.csv", local_file)

upsert_org({u'image_display_url': u'https://eiti.org/sites/all/themes/eiti/logo.svg', u'name': u'eiti', u'title': u'EITI'})

datasets = {}

with open('./datasets.json', 'r') as f:
    datasets = json.load(f)

for d in datasets:
    print "DATA FROM DOWNLOAD:"
    print d

    d['url'] = "https://eiti.org/api/v1.0/summary_data"
    if ('country' in d):
        #Switch to facet friendly names in https://github.com/derilinx/ckanext-nrgi-published/blob/master/ckanext/nrgi/schema.json
        count = 0
        for country in d['country']:
            print country
            print d['country'][count]
            print mapcountry(country)
            d['country'][count] = mapcountry(country)
            count += 1

    new_dataset, dataset = upsert_dataset(d)
    
    if not new_dataset:
        company_done = False
        government_done = False
        for resource in dataset['resources']:
            print resource
            if resource['name'] == d["resource_title_company"]:
                company_done = True
                equal = compare(resource['url'], d['filename_company'])
                if equal:
                    print "RESOURCE UNCHANGED, NOT UPLOADING RESOURCE"
                else:
                    update_resource(resource['id'], d['filename_company'], d["resource_title_company"])
            elif resource['name'] == d["resource_title_government"]:
                government_done = True
                equal = compare(resource['url'], d['filename_government'])
                if equal:
                    print "RESOURCE UNCHANGED, NOT UPLOADING RESOURCE"
                else:
                    update_resource(resource['id'], d['filename_government'], d["resource_title_government"])
        if not company_done:
            create_resource(d['name'], d['filename_company'], d["resource_title_company"])
        if not government_done:
            create_resource(d['name'], d['filename_government'], d["resource_title_government"])
    else:
        create_resource(d['name'], d['filename_company'], d["resource_title_company"])
        create_resource(d['name'], d['filename_government'], d["resource_title_government"])
    
print "The following or some of the following countries caused the dataset creation to fail:"
print failed_states
