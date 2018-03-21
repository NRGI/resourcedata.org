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
        years = [fname[-9:-5] for fname in bunch]
        dataset['year'].extend(years)
        print dataset['year']
        datasets[dataset['name']]=dataset

    return datasets
    #with open(os.path.join('dataset.json'), 'w') as f:
    #    json.dump(datasets, f)

if __name__=='__main__':
    combine_csv('test')
    combine_datasets('test-datasets')
