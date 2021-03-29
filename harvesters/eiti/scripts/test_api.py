import eiti_api_v2 as api
import pytest


@pytest.mark.parametrize("code", ["1E", "11E", "111E","1112E2"])
def test_gfs_code(code):
    api.clear_cache()
    ret = api.gfs_code(cid=code)
    for field in ('self', 'label', 'id', 'parent'):
        assert field in ret
    assert ret['id'] == code

    api.clear_cache()
    
    ret_url = api.gfs_code(url=ret['self'])
    for k,v in ret.items():
        assert ret_url[k] == v

def test_gfs_codes():
    ret = api.gfs_codes()
    assert isinstance(ret, dict)

    for code in ret.values():
        for field in ('self', 'label', 'id', 'parent'):
            assert field in code

@pytest.mark.parametrize("code", ['AF', 'AM', 'AR'])
def test_country(code):
    api.clear_cache()
    ret = api.country(cid=code)
    for field in ('self', 'label', 'id', 'iso2', 'iso3', 'status', 'join_date', 'leave_date',
                      'local_website', 'latest_validation_date', 'validation_data', 'summary_data'):
        assert field in ret
    assert ret['id'] == code

    api.clear_cache()
    
    ret_url = api.country(url=ret['self'])
    for k,v in ret.items():
        assert ret_url[k] == v

def test_countries():
    ret = api.countries()
    assert isinstance(ret, dict)

    for country in ret.values():
        for field in ('self', 'label', 'id', 'iso2', 'iso3', 'status', 'join_date', 'leave_date',
                      'local_website', 'latest_validation_date', 'validation_data', 'summary_data'):
            assert field in country


@pytest.mark.parametrize("code", ['AF2009', 'AF2010', 'AF2011'])
def test_summary_data(code):
    api.clear_cache()
    ret = api.summary_data(sid=code)
    for field in ('self', 'label', 'id', 'links', 'revenue_company',
                  'revenue_government', 'sector_gas', 'sector_mining',
                  'year_end', 'year_start', 'report_file'):
        assert field in ret
    assert ret['id'] == code

    api.clear_cache()
    
    ret_url = api.summary_data(url=ret['self'])
    for k,v in ret.items():
        assert ret_url[k] == v

def xtest_all_summary_data():
    ret = api.all_summary_data()
    assert isinstance(ret, dict)

    for data in ret.values():
        for field in ('self', 'label', 'id', 'links', 'revenue_company',
                  'revenue_government', 'sector_gas', 'sector_mining',
                  'year_end', 'year_start', 'report_file'):
            assert field in data


def test_all_summary_data_obj():
    ret = api.all_summary_data_obj()
    assert isinstance(ret, list)

    for summary in ret[:3]:
        assert summary.country.label
        assert summary.country.iso3
        assert summary.created
        assert summary.changed
        assert summary.label[-4:]
        assert isinstance(summary.revenue_government, list)
        assert isinstance(summary.revenue_company, list)
    
    
@pytest.mark.parametrize("code", ['AF2009', 'AF2010', 'AF2011'])
def test_summary_object(code):
    summary = api.summary_data_obj_fromId(code)

    assert summary.country.label
    assert summary.country.iso3
    assert summary.created
    assert summary.changed
    assert summary.label[-4:]
    assert isinstance(summary.revenue_government, list)
    assert isinstance(summary.revenue_company, list)
    
