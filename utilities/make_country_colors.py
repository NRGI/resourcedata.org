import numpy as np
import matplotlib.pyplot as plt
import requests

qchoices = []

url = requests.get("https://raw.githubusercontent.com/derilinx/ckanext-nrgi-published/master/ckanext/nrgi/schema.json")
schema = url.json()

for field in schema['dataset_fields']:
    if field['field_name'] == 'country':
        for item in field['choices']:
            qchoices.append(item['value'])
        break

ccolors = {}

cmap = plt.get_cmap('spectral')
rawcols = cmap(np.linspace(0, 1, len(qchoices)))

i = 0
for col in rawcols:
    ccolors[qchoices[i]] = "rgba(" + str(int(round(rawcols[i][0]*255.0,0))) + "," + str(int(round(rawcols[i][1]*255.0,0))) + "," + str(int(round(rawcols[i][2]*255.0,0))) + ",1.0)"
    i += 1

print ccolors
