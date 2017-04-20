import os
import json
import requests


API_HOST = os.environ['API_HOST']
API_KEY = os.environ['API_KEY']


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
    print r.status_code, r.json()
    return org['name']


def update_org(org):
    print "UPDATING ORG " + org['name']
    r = api_post("organization_create", data=org)
    print r.status_code, r.json()
    return org['name']


def upsert_org(org):
    r = api_get("organization_show", data={'id': org['name']})
    print r
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
    print r.status_code, r.json()
    return data['name']


def update_dataset(data):
    print "UPDATING DATASET " + data['name']
    r = api_post("package_update", data=data)
    print r.status_code, r.json()
    return data['name']


def upsert_dataset(data):
    print "UPSERTING DATASET " + data['name']
    r = api_get("package_show", data={'id': data['name']})
    print r.status_code, r.json()
    jsondata = r.json()
    already_exists = jsondata.get("success")
    if already_exists:
        return update_dataset(data)
    else:
        return create_dataset(data)


def patch_dataset(data):
    package_dict = api_get('package_show', {'name_or_id': data.get('name')})

    package_dict = package_dict.json()['result']

    patched = dict(package_dict)
    patched.update(data)
    patched['id'] = package_dict['id']
    return update_dataset(patched)


def upload_resource(dataset_name, resource_path, resource_name):
    print "UPLOADING RESOURCE " + resource_path[5:] + " TO DATASET " + dataset_name

    r = requests.post('%s/api/action/resource_create' % (API_HOST),
                      data={
                          "package_id": dataset_name,
                          "type": "file.upload",
                          "url": resource_path,
                          "name": resource_name,
                          "format": "csv"
                      },
                      headers={"Authorization": API_KEY},
                      files={'upload':(resource_name + '.csv', file(resource_path))})
    print r.json()


datasets = {}

with open('./datasets.json', 'r') as f:
    datasets = json.load(f)

for d in datasets:
    print d

    d['url'] = "https://eiti.org/api/v1.0/summary_data"

    upsert_dataset(d)

    upload_resource(d['name'], d['filename'], d.get("country", "all"))
