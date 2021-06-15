#!/usr/bin/env python

import os
import itertools
import json

def combine_csv(path):
    files = sorted([f for f in os.listdir(path)
                    if f.endswith('.csv') and f[-9] == '-'])
    for name, bunch in itertools.groupby(files, lambda x: x[:-9]):
        with open(os.path.join(path, '%s.csv' % name), 'w') as combined:
            with open(os.path.join(path, bunch.next()), 'r') as source:
                combined.write(source.read())
            for source_path in bunch:
                with open(os.path.join(path, source_path), 'r') as source:
                    next(source)
                    for l in source:
                        combined.write(l)

def combine_datasets(path):
    files = sorted([f for f in os.listdir(path) if f.endswith('.json')])
    datasets = {}
    for name, bunch in itertools.groupby(files, lambda x: x[:-10]):
        with open(os.path.join(path, bunch.next()), 'r') as f:
            dataset = json.load(f)
        for fname in bunch:
            with open(os.path.join(path, fname), 'r') as f:
                additional_dataset = json.load(f)
                dataset['year'].extend(additional_dataset['year'])
                dataset['created'] = min(dataset['created'], additional_dataset['created'])
                dataset['last_updated'] = max(dataset['last_updated'], additional_dataset['last_updated'])
                
        print dataset['year']
        dataset['created'] = dataset['created'].split('T')[0]
        dataset['last_updated'] = dataset['last_updated'].split('T')[0]
        datasets[dataset['name']]=dataset


    return datasets
    #with open(os.path.join('dataset.json'), 'w') as f:
    #    json.dump(datasets, f)

if __name__=='__main__':
    combine_csv('test')
    combine_datasets('test-datasets')
