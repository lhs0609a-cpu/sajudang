from copy import deepcopy
from datetime import date
from fastapi.testclient import TestClient
from main import app
from engine import interpretation as ip, value_audit, page_evaluation, reading_evaluation
from engine.calendar import build_chart
from engine.features import build_features
import store


def test_missing_human_data_is_never_filled_with_internal_score():
    f=build_features(build_chart(1993,11,25,15,30,'F',city='서울'),as_of=date(2026,9,13))
    reading=ip.render(ip.build_plan(f,'work'),f,'all')
    scored=value_audit.score_reading(reading)
    assert scored['human_score'] is None
    broken=deepcopy(reading)
    broken.pop('practice')
    assert value_audit.score_reading(broken)['score']<scored['score']
    assert reading['practice']['source']=='traditional_hypothesis'


def test_every_route_including_shared_client_is_audited():
    rows=value_audit.page_inventory()
    assert sum(r['scope']=='route' for r in rows)==len(list((value_audit.ROOT/'apps/web/app').rglob('page.tsx')))
    assert {'s1','a7','c2','d0','d1'} <= {r['id'] for r in rows}
    assert all(r['human_score'] is None for r in rows)


def test_page_feedback_is_explicit_validated_and_private(monkeypatch):
    client=TestClient(app)
    recorded=[]
    monkeypatch.setattr(page_evaluation,'record',lambda *args:recorded.append(args))
    payload={'session_id':'page-evaluation-test','page_id':'c2','ease':7,'success':'yes'}
    assert client.post('/v1/page-evaluation',json={**payload,'name':'secret'}).status_code==422
    assert client.post('/v1/page-evaluation',json={**payload,'page_id':'/s/private-token'}).status_code==422
    assert client.post('/v1/page-evaluation',json={**payload,'ease':8}).status_code==422
    assert not recorded
    assert client.post('/v1/page-evaluation',json=payload).status_code==200
    assert recorded==[('page-evaluation-test','c2',7,'yes')]
    assert client.get('/v1/admin/value-audit').status_code in (401,403,503)


def test_page_score_uses_actual_answers_and_replaces_duplicate(monkeypatch):
    saved={}
    monkeypatch.setattr(store,'set_json',lambda key,row,ttl:saved.update({key:row}))
    monkeypatch.setattr(store,'scan',lambda prefix,limit:list(saved.items()))
    page_evaluation.record('private-session','c2',7,'yes')
    page_evaluation.record('private-session','c2',1,'no')
    result=page_evaluation.stats()
    assert result['samples']==1 and result['rows'][0]['ease_score_100']==0
    assert 'private-session' not in str(saved)


def test_result_evaluation_separates_concerns_scope_and_price(monkeypatch):
    saved={}
    monkeypatch.setattr(store,'set_json',lambda key,row,ttl:saved.update({key:row}))
    monkeypatch.setattr(store,'scan',lambda prefix,limit:list(saved.items()))
    answers={d:'partly' for d in reading_evaluation.DIMENSIONS}
    for concern in ('money','love'):
        reading_evaluation.record('session-private','chart-private','pungun',5,answers,True,
            dict(concern=concern,scope='book',result_key='a'*20,value_for_money=3))
    result=reading_evaluation.stats()
    assert len(result['results'])==2
    assert all(r['reader_score']==50 and r['value_mean_1_5']==3 for r in result['results'])
    assert 'chart-private' not in str(saved) and 'a'*20 not in str(saved)


def test_refunded_buyers_can_rate_value_without_regaining_access(monkeypatch):
    saved={'orders:value-refund':['value-order'],'order:value-order':{
        'session_id':'value-refund','status':'refunded','tier':'one','lens_id':'pungun'}}
    monkeypatch.setattr(store,'get_json',lambda key:saved.get(key))
    assert reading_evaluation.purchased('value-refund','pungun')
    assert not reading_evaluation.purchased('value-refund','hongmae')
    from routers.report import entitled_tier
    assert entitled_tier('value-refund','pungun')=='free'


def test_summary_keeps_consultation_but_share_never_includes_it():
    client=TestClient(app)
    chart=client.post('/v1/chart',json={'year':1993,'month':11,'day':25,'hour':15,'minute':30,
        'hour_known':True,'sex':'F','birth_city':'서울'}).json()['chart_id']
    req=dict(chart_id=chart,concern='work',lens_id='pungun')
    before=client.post('/v1/summary',json=req).json()['reading']
    question=next(q for q in before['consultation']['questions'] if q['id'].startswith('claim:'))
    extras={'consultation':{'concern':'work','answers':{question['id']:'no'}}}
    after=client.post('/v1/summary',json={**req,'extras':extras}).json()['reading']
    assert before['summary'][0]['id'] not in {r['id'] for r in after['summary']}
    shared=client.post('/v1/share',json={**req,'extras':extras}).json()
    opened=client.get(shared['path'].replace('/s/','/v1/share/')).json()
    assert 'consultation' not in str(opened) and 'practice' not in opened and 'reading' not in opened


def test_daily_and_hook_have_simple_main_text_with_separate_evidence():
    from engine import daily, bank
    f=build_features(build_chart(1993,11,25,15,30,'F',city='서울'),as_of=date(2026,9,13))
    a=daily.build_daily(f,date(2026,9,13),'money')
    b=daily.build_daily(f,date(2026,9,13),'love')
    assert a['plain']!=b['plain'] and a['score']==b['score']
    assert a['practice']['action']==a['plain'][2]
    for segment in bank.build_hook(f,'money'):
        assert '<details' in segment['html'] and segment['statement_id'].endswith(':copy3')
        assert '그럴 줄 알았소' not in segment['yes']
