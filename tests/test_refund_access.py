from datetime import datetime, timedelta, timezone
import pytest
from fastapi import HTTPException
import store, payments
from routers import pay, report, subscription


@pytest.fixture(autouse=True)
def clear():
    store.clear_all()


def order(oid='o',tier='all',status='paid'):
    row={'session_id':'s','tier':tier,'status':status,'amount':9900,'payment_key':'test-only'}
    store.set_json('order:'+oid,row)
    store.set_json('orders:s',[oid])
    return row


def test_omnibus_access_records_opening_and_blocks_refund(monkeypatch):
    order()
    report._mark_opened('s','all')
    assert store.get_json('order:o')['opened_at']
    monkeypatch.setattr(payments,'cancel',lambda *a:pytest.fail('opened order cannot auto refund'))
    with pytest.raises(HTTPException) as e:
        pay.refund(pay.RefundRequest(session_id='s',order_id='o',reason='test',opened=False))
    assert e.value.status_code==409


def test_refunded_order_cannot_release_paid_content():
    order(status='refunded')
    with pytest.raises(HTTPException) as e:report._mark_opened('s','all')
    assert e.value.status_code==402


def test_refunding_current_subscription_removes_card_and_access(monkeypatch):
    order(tier='sub')
    subscription._save({'session_id':'s','user_key':subscription._user_key('s'),
        'status':'active','period_end':(datetime.now(timezone.utc)+timedelta(days=15)).isoformat(),
        'orders':['o'],'billing_key':'encrypted-test-only'})
    monkeypatch.setattr(payments,'cancel',lambda *a:None)
    assert pay.refund(pay.RefundRequest(session_id='s',order_id='o',reason='test'))['ok']
    assert not subscription.active(subscription._load('s'))
    assert subscription._load('s')['billing_key']==''
    assert report.entitled_tier('s','pungun')=='free'


def test_refunded_old_period_does_not_remove_new_paid_period():
    row=order(tier='sub',status='refunded')
    subscription._save({'session_id':'s','user_key':subscription._user_key('s'),
        'status':'active','orders':['o','newer'],'billing_key':'encrypted-test-only'})
    pay._stop_refunded_subscription(row,'o')
    assert subscription._load('s')['billing_key']=='encrypted-test-only'
