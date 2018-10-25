import requests
import os
import json


ENDPOINT = "https://staging.eiti.org/api/v2.0/"


session = requests.Session()
cache = {}

class UnexpectedResponse(Exception): pass

def _single_request(url=None, obj_type=None, obj_id=None, **kwargs):
    """ polymorphic request

    If we have a full url, use that.
    If we have a object type and id, construct and use those.

    :param url: absolute url, optional
    :param obj_type: organization/gfs/etc, optional
    :param obj_id: object id, optional
    kwargs -- to be passed in as parameters to the request.
    :returns: object dict
    """

    if not url:
        url = os.path.join(ENDPOINT, obj_type, obj_id)

    if url in cache:
        return cache[url]

    r = session.get(url, params=kwargs)
    r.raise_for_status()

    try:
        cache[url] = r.json()['data'][0]
        return dict(cache[url])
    except Exception as msg:
        raise UnexpectedResponse(msg)

def _collection_request(url=None, obj_type=None, **kwargs):
    """ polymorphic request

    If we have a full url, use that.
    If we have a object type and id, construct and use those.

    :param url: absolute url, optional
    :param obj_type: organization/gfs/etc, optional
    kwargs -- to be passed in as parameters to the request.
    :returns: list of object dicts
    """

    if not url:
        url = os.path.join(ENDPOINT, obj_type)

    r = session.get(url, params=kwargs)
    r.raise_for_status()

    try:
        return r.json()
    except Exception as msg:
        raise UnexpectedResponse(msg)

def _cache(collection):
    for elt in collection:
        cache[elt['self']] = elt

def _slurp(obj_type, **kwargs):
    items = _collection_request(obj_type=obj_type, **kwargs)
    ret = items['data']
    while 'next' in items:
        items = _collection_request(url=items['next']['href'])
        ret.extend(items['data'])

    _cache(ret)
    return dict([(r['self'],r) for r in ret])

def countries():
    return _slurp('implementing_country')

def country(url=None, cid=None):
    return _single_request(url=url, obj_type='implementing_country', obj_id=cid)

def gfs_codes():
    return _slurp('gfs_code')

def gfs_code(url=None, cid=None):
    return _single_request(url=url, obj_type='gfs_code', obj_id=cid)

def organisation(url=None, oid=None):
    return _single_request(url=url, obj_type='organisation', obj_id=oid)

def organisation_forCountry(country_id):
    return _slurp('organisation', **{'filter[country]':country_id})

def revenue(url=None, rid=None):
    return _single_request(url=url, obj_type='revenue', obj_id=rid)

def summary_data(url=None, sid=None):
    return _single_request(url=url, obj_type='summary_data', obj_id=sid)

def all_summary_data():
    return _slurp('summary_data')

def all_summary_data_obj():
    return [SummaryData(s) for s in _slurp('summary_data')]

def pp(item):
    print json.dumps(item, indent=2)


class LinkedObj(object):
#    _wraps = { 'field_name': function_to_resolve  }
    _wraps = {}

    def __init__(self, data_dict):
        self.data_dict = data_dict

    def __getattr__(self, att):
        if att in self.data_dict:
            return self._wrap(att)
        raise AttributeError

    def _wrap(self, att):
        """for reference values, return the linked object instead of the
            reference

        """
        val = self.data_dict[att]
        if att in self._wraps:
            func = self._wraps[att]
            if type(val) == type([]):
                ret = [func(ref) for ref in val]
                setattr(self, att, ret)
                return ret
            elif type(val) == type({}):
                ret = dict([(k,func(v)) for k,v in val.items()])
                setattr (self, att, ret)
                return ret
            return func(val)
        return val

    def __repr__(self):
        return json.dumps(self.data_dict)

    # dict interface
    def __contains__(self, att):
        return att in self.data_dict
    def __getitem__(self, att):
        try:
            return getattr(self,att)
        except AttributeError:
            return KeyError
    def get(self, att, default=None):
        try:
            return getattr(self, att)
        except AttributeError:
            return default
    def keys(self):
        return self.data_dict.keys()
    def items(self):
        return self.data_dict.items()
    def values(self):
        return self.data_dict.values()



class Revenue(LinkedObj): pass
class Organisation(LinkedObj): pass
class GfsCode(LinkedObj): pass
class SummaryData(LinkedObj): pass
class Country(LinkedObj): pass

def asObj(func, cls):
    def wrapped(*args, **kwargs):
        return cls(func(*args, **kwargs))
    return wrapped

revenue_obj = asObj(revenue, Revenue)
organisation_obj = asObj(organisation, Organisation)
gfs_obj = asObj(gfs_code, GfsCode)
country_obj = asObj(country, Country)
summary_data_obj = asObj(summary_data, SummaryData)

def summary_data_obj_fromId(sid):
    return SummaryData(summary_data(sid=sid))

SummaryData._wraps = {
    'revenue_government': revenue_obj,
    'revenue_company': revenue_obj,
    'country': country_obj,
}

Revenue._wraps = {
    'organisation': organisation_obj,
    'gfs': gfs_obj,
}

Organisation._wraps = {
    'country': country_obj,
    'summary_data': summary_data_obj_fromId
}

Country._wraps = {
    'summary_data': summary_data_obj,
}
