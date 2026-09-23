import pytest
from fastapi.testclient import TestClient
from main import app
from engine.features import Features
from engine.mbti_reading import build,TYPES,TOPIC
from engine import guard

@pytest.fixture(scope='module')
def chart():
    return TestClient(app).post('/v1/chart',json={'year':1987,'month':8,'day':19,'hour_known':False,'sex':'M','birth_city':'서울'}).json()

@pytest.mark.parametrize('code',TYPES)
@pytest.mark.parametrize('concern',TOPIC)
def test_every_type_and_concern_has_specific_content(chart,code,concern):
    result=build(Features(**chart['features']),code,concern)
    assert code in result['html'] and len(result['html'])>750
    assert result['html'].count('<h3>')==6
    assert guard.check(result['html'])[0]

def test_all_types_have_different_actions_and_no_type_is_invented(chart):
    f=Features(**chart['features'])
    assert len({build(f,code,'love')['action'] for code in TYPES})==16
    assert build(f,None,'love') is None
    assert build(f,'XXXX','love') is None

def test_report_action_and_free_reading_change_with_mbti(chart):
    c=TestClient(app);results=[]
    for code in ('INFP','ESTJ',None):
        response=c.post('/v1/report',json={'chart_id':chart['chart_id'],'lens_id':'jeokhyeol','concern':'love','axis4':code,'tier':'free'})
        assert response.status_code==200,response.text
        results.append(response.json())
    assert results[0]['practice']['steps']!=results[1]['practice']['steps']
    assert 'mbti' not in results[2]['practice']
    for result in results[:2]:
        assert any('mbti-reading' in cut['html'] for cut in result['cuts'])
        assert result['practice']['mbti']
