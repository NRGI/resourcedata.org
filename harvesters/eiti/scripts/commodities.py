#!/usr/bin/env python

commodities = [
    u'Coal, volume',
    u'Condensate, volume',
    u'Copper, volume',
    u'Crude oil production revenues in kind',
    u'Gas production revenues in kind',
    u'Gas, volume',
    u'Gold, volume',
    u'NGL, volume',
    u'Oil, volume',
    u'Total revenue received?',
    u'Exports - all sectors',
    u'Exports - extractive industries',
    u'Government revenue - all sectors',
    u'Government revenue - extractive industries',
    u'Gross Domestic Product - all sectors',
    u'Gross Domestic Product - extractive industries (Gross Value Added)',
]


c_map = dict([(v, "commodity_%d" % ix) for ix,v in enumerate(commodities)])

def truncate_date(s):
    return  "%sT00:00:00+0000" % s.split('T')[0]

c_header1 = []
c_header2 = []

for ix, v in enumerate(commodities):
    c_header1.append('commodity_%d_value'% ix)
    c_header1.append('commodity_%d_units'% ix)
    c_header2.append('"%s"' % v)
    c_header2.append("unit")

header_1 = (
    'created',
    'changed',
    'country',
    'iso3',
    'year',) + tuple(c_header1) + ('source', )

header_2 = ("","", "","","") + tuple(c_header2) + ('',)


def filter_commodity(data):
    reports =  [d for d in data if 'country' in d and d['country'].get('reports', None)]

    seen = set()
    lines = [header_1, header_2]
    for d in reports:
        reports = d['country'].get('reports', None)
        source = d.get('report_file', '')
        if reports:
            for label, values in reports.items():
                country_year = (d['country']['label'], label)
                if country_year in seen:
                    continue
                seen.add(country_year)
                items = {}
                for rpt in values:
                    c = rpt.get('commodity', None)
                    if c_map.get(c, None):
                        items[c_map[c]] = {
                            'value': rpt.get('value', ''),
                            'unit': rpt.get('unit', '')
                            }
                c_line = []
                for ix, v in enumerate(commodities):
                    elt = "commodity_%d" % ix
                    c_line.append(items.get(elt, {}).get('value',''))
                    c_line.append(items.get(elt, {}).get('unit',''))

                line = (truncate_date(d['created']),
                        truncate_date(d['changed']),
                        d['country']['label'],
                        d['country']['iso3'],
                        label) + tuple(c_line) + \
                        (source,)


                lines.append(line)

    return lines
