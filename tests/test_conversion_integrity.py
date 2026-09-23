import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
from fastapi import HTTPException
import store
import activity
import referrals
import promotions
import payments


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    monkeypatch.setattr(store, '_redis', None)
    monkeypatch.setattr(store, '_db', None)
    monkeypatch.setattr(store, '_mem', {})
    for key in ('SALE_START','SALE_END','SALE_PERCENT'):
        monkeypatch.delenv(key, raising=False)


def account(key, created=0):
    row={'id':key,'session_id':'session-'+key,'created_at':created}
    store.set_json('member:'+key,row)
    store.set_json('member-owner:'+referrals.accounts.digest(row['session_id']),key)
    return row


def comparison_reading(member_id, flow, top, strength, strong, weak):
    rid='reading-'+member_id
    store.set_json('member-library:'+member_id,[rid])
    store.set_json('member-reading:'+member_id+':'+rid,{'compare_profile':{
        'flow':flow,'top_ten_god':top,'strength':strength,
        'strong_el':strong,'weak_el':weak}})


def test_presence_dedup_expiration_and_no_personal_data(monkeypatch):
    monkeypatch.setattr(activity.time,'time',lambda:1000)
    assert activity.snapshot('a'*32,'entry')['active_browsers']==1
    assert activity.snapshot('a'*32,'entry')['active_browsers']==1
    assert activity.snapshot('b'*32,'entry')['active_browsers']==2
    monkeypatch.setattr(activity.time,'time',lambda:1061)
    out=activity.snapshot('c'*32,'entry')
    assert out=={'active_browsers':1,'window_seconds':60,'purchases':[]}
    assert 'a'*32 not in str(store.get_json('public-presence:entry'))


def test_notices_only_live_paid_and_remove_refunds(monkeypatch):
    order={'status':'paid','amount':9900,'paid_at':datetime.now(timezone.utc).isoformat(),
           'session_id':'private', 'name':'private name'}
    store.set_json('order:private-order',order)
    monkeypatch.setattr(payments,'LIVE',False)
    activity.record_purchase('private-order',order)
    assert not activity.snapshot('a'*32,'entry')['purchases']
    monkeypatch.setattr(payments,'LIVE',True)
    activity.record_purchase('private-order',order)
    activity.record_purchase('private-order',order)
    out=activity.snapshot('a'*32,'entry')['purchases']
    assert len(out)==1 and 'private' not in str(out)
    order['status']='refunded';store.set_json('order:private-order',order)
    assert not activity.snapshot('a'*32,'entry')['purchases']


def test_fixed_discount_boundary_and_subscription_exclusion(monkeypatch):
    now=datetime.now(timezone.utc)
    monkeypatch.setenv('SALE_START',(now-timedelta(minutes=1)).isoformat())
    monkeypatch.setenv('SALE_END',(now+timedelta(minutes=1)).isoformat())
    monkeypatch.setenv('SALE_PERCENT','10')
    assert promotions.quote(9900,'one')['price']==8910
    assert promotions.quote(14900,'sub')['price']==14900
    assert promotions.current(now+timedelta(minutes=1)) is None
    assert promotions.current(now-timedelta(minutes=2)) is None


def test_campaign_configuration_is_explicit_and_safe(monkeypatch):
    example = (Path(__file__).parents[1] / '.env.example').read_text(encoding='utf-8')
    assert all(name in example for name in ('SALE_START', 'SALE_END', 'SALE_PERCENT'))
    monkeypatch.setenv('SALE_START', '2026-09-22T00:00:00')
    monkeypatch.setenv('SALE_END', '2026-09-23T00:00:00')
    monkeypatch.setenv('SALE_PERCENT', '10')
    assert promotions.current(datetime(2026, 9, 22, 1, tzinfo=timezone.utc)) is None
    monkeypatch.setenv('SALE_START', '2026-09-22T00:00:00+00:00')
    monkeypatch.setenv('SALE_END', '2026-09-23T00:00:00+00:00')
    monkeypatch.setenv('SALE_PERCENT', '51')
    assert promotions.current(datetime(2026, 9, 22, 1, tzinfo=timezone.utc)) is None


def test_invitation_self_repeat_existing_member_and_expiry():
    host=account('host');code=referrals.invite(host)
    assert referrals.invite(host)==code
    with pytest.raises(HTTPException):referrals.claim(host,code)
    with pytest.raises(HTTPException):referrals.claim(account('existing'),code)
    friend=account('friend',time.time()+1)
    credit=referrals.claim(friend,code)
    assert credit['percent']==5 and referrals.status(host)['status']=='ready'
    assert referrals.claim(friend,code)['expires_at']==credit['expires_at']
    assert referrals.quote(9900,'one',friend['session_id'])['price']==9405
    assert referrals.quote(14900,'sub',friend['session_id'])['price']==14900
    row=store.get_json('referral-credit:friend');row['expires_at']=0;store.set_json('referral-credit:friend',row)
    referrals.claim(friend,code)
    assert referrals.status(friend)['status']=='expired'
    assert referrals.quote(9900,'one',friend['session_id'])['price']==9900


def test_credit_one_order_retry_and_no_stacking(monkeypatch):
    host=account('host');friend=account('friend',time.time()+1)
    referrals.claim(friend,referrals.invite(host))
    sid=friend['session_id'];q=referrals.quote(9900,'one',sid)
    referrals.reserve(sid,'first',q)
    # No recovery during the small interval between reservation and order write.
    assert referrals.quote(9900,'one',sid)['price']==9900
    with pytest.raises(HTTPException):referrals.reserve(sid,'second',q)
    order={'session_id':sid,'chart_id':'chart','lens_id':'jeokhyeol','tier':'one','amount':q['price'],'price_quote':q,'status':'pending'}
    store.set_json('order:first',order)
    assert referrals.pending(sid,'chart','jeokhyeol','one')[0]=='first'
    assert referrals.pending(sid,'different','jeokhyeol','one') is None
    order['status']='paid';store.set_json('order:first',order);referrals.settle('first',order)
    assert referrals.status(friend)['status']=='used'
    assert referrals.quote(9900,'one',sid)['price']==9900
    now=datetime.now(timezone.utc)
    monkeypatch.setenv('SALE_START',(now-timedelta(minutes=1)).isoformat())
    monkeypatch.setenv('SALE_END',(now+timedelta(days=1)).isoformat())
    monkeypatch.setenv('SALE_PERCENT','10')
    assert referrals.quote(9900,'one',host['session_id'])['price']==8910
    assert 'referral' not in referrals.quote(9900,'one',host['session_id'])


@pytest.mark.parametrize(('relation','label'),[
    ('lover','연인'),('family','가족'),('relative','친지'),
    ('friend','친구'),('coworker','동료'),('other','소중한 사람'),
])
def test_any_relationship_opens_a_private_two_person_comparison(relation,label):
    host=account('host');friend=account('friend',time.time()+1)
    comparison_reading('host','식상','식신','신강','화','수')
    code=referrals.invite(host)
    referrals.claim(friend,code,relation)
    waiting=referrals.comparisons(friend)
    assert waiting==[{'id':waiting[0]['id'],'relation':relation,'relation_label':label,'status':'waiting'}]
    comparison_reading('friend','관성','정관','신약','수','화')
    mine=referrals.comparisons(friend)[0]
    theirs=referrals.comparisons(host)[0]
    assert mine['status']==theirs['status']=='ready'
    assert mine['relation_label']==theirs['relation_label']==label
    assert all(mine.get(key) for key in ('shared','difference','watch','action'))
    for result in (mine,theirs):
        assert not {'owner','invited','account_id','birth','name'} & result.keys()
        assert 'host' not in str(result.values())
    referrals.forget(host)
    assert referrals.comparisons(friend)==[]


def test_comparison_rejects_an_unknown_relationship():
    host=account('host');friend=account('friend',time.time()+1)
    with pytest.raises(HTTPException) as error:
        referrals.claim(friend,referrals.invite(host),'customer')
    assert error.value.status_code==422
