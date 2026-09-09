"""Regressions for the September 9 audit; never contacts a payment provider."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from threading import Event
import pytest
from fastapi import HTTPException
import store, payments
from engine import calendar as cal
from routers import chart, pay, subscription, report
from schemas.api import ChartRequest

REQ = dict(year=1993,month=11,day=25,hour=9,minute=10,sex='F',hour_known=True,birth_city='서울')

@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    store.clear_all()
    monkeypatch.setattr(payments, 'cancel', lambda *a: None)
    yield
    store.clear_all()

def test_alternative_policy_does_not_contaminate_concurrent_chart(monkeypatch):
    original=cal.build_chart; entered=Event(); release=Event()
    def paused(*a,**kw):
        if kw.get('hour_basis')=='standard':
            entered.set(); assert release.wait(5)
        return original(*a,**kw)
    monkeypatch.setattr(cal,'build_chart',paused)
    baseline=original(1993,11,25,9,10,'F')
    with ThreadPoolExecutor(1) as pool:
        future=pool.submit(chart._divergence,ChartRequest(**REQ))
        try:
            assert entered.wait(5)
            during=original(1993,11,25,9,10,'F')
            assert [p.gz for p in baseline.pillars]==[p.gz for p in during.pillars]
            assert cal.HOUR_BASIS=='true_solar'
        finally:release.set()
        assert future.result()['cases']

def test_cache_refreshes_year_and_direct_reads_request_rebuild(monkeypatch):
    monkeypatch.setattr(chart,'today',lambda:date(2025,12,31))
    a=chart.post_chart(ChartRequest(**REQ))
    monkeypatch.setattr(chart,'today',lambda:date(2026,1,1))
    with pytest.raises(HTTPException) as e:chart.load_features(a.chart_id)
    assert e.value.headers['X-Chart-Rebuild']=='1'
    b=chart.post_chart(ChartRequest(**REQ))
    assert b.chart_id==a.chart_id and not b.cached
    assert b.features['age']==a.features['age']+1

@pytest.mark.parametrize('over',[{'year':2050},{'year':2020},{'birth_city':'뉴욕'}])
def test_unsupported_person_input_rejected(over):
    with pytest.raises(HTTPException) as e:chart.post_chart(ChartRequest(**{**REQ,**over}))
    assert e.value.status_code==400

def subscription_order():
    end=(datetime.now(timezone.utc)+timedelta(days=20)).isoformat()
    row=dict(session_id='old-browser',tier='sub',status='paid',amount=9900,payment_key='mock',expires_at=end)
    store.set_json('order:audit-order',row);store.set_json('orders:old-browser',['audit-order'])
    sub=dict(session_id='old-browser',user_key=subscription._user_key('old-browser'),orders=['audit-order'],
             status='live',period_end=end,billing_key='mock',ending=False)
    subscription._save(sub)
    return sub

def test_repeated_restore_then_refund_stops_current_owner():
    subscription_order()
    for owner in ['new-browser','third-browser']:
        assert subscription.restore(subscription.RestoreRequest(session_id=owner,order_id='audit-order'))['ok']
        assert store.get_json('order:audit-order')['session_id']==owner
    pay.refund(pay.RefundRequest(session_id='third-browser',order_id='audit-order',reason='test refund'))
    sub=subscription._load('third-browser')
    assert not subscription.active(sub) and not sub['billing_key']
    assert report.entitled_tier('third-browser','pungun')=='free'

def test_stale_scheduler_snapshot_cannot_charge_after_restore(monkeypatch):
    from copy import deepcopy
    stale=deepcopy(subscription_order())
    subscription.restore(subscription.RestoreRequest(session_id='new-browser',order_id='audit-order'))
    stale['period_end']=(datetime.now(timezone.utc)-timedelta(days=1)).isoformat()
    monkeypatch.setattr(payments,'charge_billing',lambda *a:pytest.fail('stale owner must not charge'))
    assert subscription.renew(stale)['already']

def test_verified_refund_reissues_once_and_cannot_refund_free_reissue(monkeypatch):
    calls=[];monkeypatch.setattr(payments,'cancel',lambda *a:calls.append(a))
    store.set_json('order:original',dict(session_id='buyer',tier='all',status='paid',amount=24900,
        payment_key='mock',opened_at='2026-09-01',calc_error_verified=True))
    store.set_json('orders:buyer',['original'])
    req=pay.RefundRequest(session_id='buyer',order_id='original',reason='calculation error',calc_error=True)
    first=pay.refund(req);second=pay.refund(req)
    assert first['reissue_order_id']==second['reissue_order_id'] and len(calls)==1
    assert report.entitled_tier('buyer','pungun')=='all'
    assert len(store.get_json('orders:buyer'))==2
    with pytest.raises(HTTPException) as e:
        pay.refund(pay.RefundRequest(session_id='buyer',order_id=first['reissue_order_id'],reason='again'))
    assert e.value.status_code==409

def test_evicted_chart_requests_rebuild_without_losing_payment():
    result=chart.post_chart(ChartRequest(**REQ));store.delete(store.k_chart(result.chart_id))
    store.set_json('order:paid',dict(session_id='buyer',tier='all',status='paid'))
    store.set_json('orders:buyer',['paid'])
    with pytest.raises(HTTPException) as e:chart.load_features(result.chart_id)
    assert e.value.status_code==404 and e.value.headers['X-Chart-Rebuild']=='1'
    assert report.entitled_tier('buyer','pungun')=='all'
    assert chart.post_chart(ChartRequest(**REQ)).chart_id==result.chart_id

def test_restored_permanent_purchase_index_survives_a_year(monkeypatch):
    store.set_json('order:forever',dict(session_id='old-browser',tier='all',status='paid'))
    pay.restore(pay.RestoreRequest(session_id='new-browser',order_id='forever'))
    now=store._now()
    monkeypatch.setattr(store,'_now',lambda:now+366*86400)
    assert report.entitled_tier('new-browser','pungun')=='all'


def test_product_discloses_exact_missing_inputs():
    from engine import lens, extras
    result = chart.post_chart(ChartRequest(**REQ))
    got = pay.get_tiers(pay.TiersRequest(chart_id=result.chart_id, lens_id='wolha', concern='love'))
    tiers = {t['id']: t for t in got['tiers']}
    expected = {lens.required_input(l['id']) for l in lens.released()} & set(extras.BUILDERS)
    assert expected <= set(tiers['all']['required_inputs'])
    assert set(tiers['all']['required_inputs']) <= set(extras.BUILDERS)
    assert tiers['all']['needs_extra_input'] == bool(tiers['all']['required_inputs'])
    assert set(tiers['one']['required_inputs']) <= set(tiers['all']['required_inputs'])
