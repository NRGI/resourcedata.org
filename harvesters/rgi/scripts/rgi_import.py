#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import requests
import unicodedata
import re
import uuid
import os

import time

failed_states = []

API_HOST = os.environ['API_HOST']
API_KEY = os.environ['API_KEY']

max_conn_attempts = 2

def api_get(action, data={}):
    attempts = 0
    try:
        print "GET: " + API_HOST+"/api/action/"+action+" - attempt #" + str(attempts+1)
        req = requests.get(
                    API_HOST+"/api/action/"+action,
                    params=data,
                    verify=True,
                    headers={"Authorization": API_KEY})
        r = req.json()
        return r
    except Exception as e: #We can either have connection errors or json errors depending on the HTTP response
        if attempts == max_conn_attempts:
            print "Connection failure: " + str(e) + ", giving up after " + str(attempts) + " attempts"
            raise
        attempts += 1
        print "Connection failure: " + str(e) + ", backing off for 90 seconds"
        time.sleep(90)


def api_post(action, data={}):
    attempts = 0
    try:
        print "POST: " + API_HOST+"/api/action/"+action+" - attempt #" + str(attempts+1)
        req = requests.post(
                API_HOST+"/api/action/"+action,
                verify=True,
                json=data,
                headers={"Authorization": API_KEY, "Content-Type": "application/json"})
        r = req.json()
        return r
    except Exception as e: #We can either have connection errors or json errors depending on the HTTP response
        print "Connection failure: " + str(e) + ", backing off for 90 seconds"
        if attempts == max_conn_attempts:
            print "Connection failure: " + str(e) + ", giving up after " + str(attempts) + " attempts"
            raise
        attempts += 1
        print "Connection failure: " + str(e) + ", backing off for 90 seconds"
        time.sleep(90)

def create_org(org):
    print ("CREATING ORG " + org['name'])
    r = api_post("organization_create", data=org)
    print (r)
    return org['name']


def update_org(org):
    print ("UPDATING ORG " + org['name'])
    r = api_post("organization_create", data=org)
    print (r)
    return org['name']


def upsert_org(org):
    r = api_get("organization_show", data={'id': org['name']})
    print (r)
    already_exists = r.get("success")
    if not already_exists:
        return create_org(org)
    else:
        return update_org(org)


def create_dataset(data):
    print ("CREATING DATASET " + data['name'])
    r = api_post("package_create", data=data)
    print r
    if ('error' in r):
        failed_states.append(data)
    return r


def update_dataset(data):
    print ("UPDATING DATASET " + data['name'])
    r = api_post("package_update", data=data)
    if ('error' in r):
        failed_states.append(data)
    return r


def upsert_dataset(data):
    print ("UPSERTING DATASET " + data['name'])
    r = api_get("package_show", data={'id': data['name']})
    print(r)
    already_exists = False
    already_exists = r.get("success")
    if already_exists:
        updated = update_dataset(data)
        # Workaround https://github.com/ckan/ckan/issues/3560
        print updated
        v = api_get("resource_view_list", data={'id': updated['result']['resources'][0]['id']})
        if len(v['result']) == 0:
            format_for_view = updated['result']['resources'][0]['format'].lower()
            if format_for_view in ('pdf', 'xls', 'xlsx', 'jpeg', 'png', 'rtf', 'docx', 'doc', 'csv'):
                if format_for_view == 'pdf':
                    view_title = 'PDF'
                    view_type = 'pdf_view'
                elif format_for_view in ('xls', 'xlsx', 'rtf', 'docx', 'doc'):
                    view_title = 'Office'
                    view_type = 'officedocs_view'
                elif format_for_view in ('jpeg', 'png'):
                    view_title = 'Image'
                    view_type = 'image_view'
                elif format_for_view == 'csv':
                    if updated['result']['resources'][0]['datastore_active']:
                        view_title = 'Table'
                        view_type = 'datatables_view'
                    else:
                        return updated #Only do Table view if in datastore
                vn = api_post("resource_view_create", data={"resource_id": updated['result']['resources'][0]['id'], "title": view_title, "view_type": view_type})
        return updated
    else:
        return create_dataset(data)


def sanitize(name):
    #Thanks Vitamin for this
    normalizedName = unicodedata.normalize('NFKD', name.lower())
    asciiName = normalizedName.encode('ascii', 'ignore')
    newname = re.sub('[\W_]+', '-', asciiName)
    
    #CKAN names can't start with -
    while len(newname) > 0 and newname[0] == "-":
        newname = newname[1:len(newname)]
            
    #Truncate (leave room for rgi- at front). CKAN names are max. 100 chars
    if len(newname) > 96:
        newname = newname[len(newname)-96:len(newname)]
        
    return newname

def unicodeToNumbers(name):
    #Some names have no western characters left; make up something that will be repeatable
    finalstring = "u" #U for unicode!
    for char in name:
        finalstring += str(ord(char))
        
    if len(finalstring) > 96:
        finalstring = finalstring[len(finalstring)-96:len(finalstring)]
        
    return finalstring

qchoices = {}

url = requests.get("https://raw.githubusercontent.com/derilinx/ckanext-nrgi-published/master/ckanext/nrgi/schema.json")
schema = url.json()
for field in schema['dataset_fields']:
    if field['field_name'] == 'question':
        for item in field['choices']:
            qchoices[item['value']] = item['label']
        break

with open('./datasets2.json', 'r') as f:
    datasets = json.load(f)

badquestions = set()

unsanitisednamesset = set()
sanitisednamesset = set()
duplicates = []

print len(datasets)

startname = None
started = False

#upsert_org({'name': 'rgi', 'title': 'Resource Governance Index', 'image_url': 'http://resourcedata.org/nrgi-logo.png'})

for d in datasets:
    
    #print (datasets[d])
    print datasets[d]['name']
    
    if datasets[d]['name'] in unsanitisednamesset:
        print "Duplicate name! " +  datasets[d]['name']
    else:
        unsanitisednamesset.add(datasets[d]['name'])
    
    sname = sanitize(datasets[d]['name'])
    print sname
    
    if len(sname) < 2:
        sname = unicodeToNumbers(datasets[d]['name'])
    
    if len(sname) > 96:
        print "shortening"
        sname = sname[len(sname)-96:len(sname)]
        
    print sname
    
        
    datasets[d]['name'] = ("rgi-" + sname).lower()
    
    if datasets[d]['name'] in sanitisednamesset:
        print "Duplicate (clean) name! " +  datasets[d]['name']
        duplicates.append(d)
        print datasets[d]
    else:
        sanitisednamesset.add(datasets[d]['name'])
        
    if startname and not started:
        if datasets[d]['name'] != startname:
            print "Skipping"
            continue
        
    started = True

    qtext = "Question "
    qset = set()
    #Avoid duplicate question entries and throw out questions not in the schema.
    #Neither should happen as we catch these things in get_pdfs.py
    for question in datasets[d]['question']: #temp, already checked
        if question in qchoices:
            qset.add(question)
        else:
            badquestions.add(question)
            
    datasets[d]['question'] = list(qset)

    for question in datasets[d]['question']:
        qtext = qtext + qchoices[question] + ',\n'

    qtext = qtext[0:len(qtext)-2]
    datasets[d]['notes'] = qtext #Put question(s) as description
    upsert_dataset(datasets[d])
    
print "The following datasets failed:"
print failed_states

print "The following questions are invalid:"
print badquestions

print "Could not avoid the following duplicate names:"
print duplicates
