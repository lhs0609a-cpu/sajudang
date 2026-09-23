import uuid
import pytest
from fastapi.testclient import TestClient
from main import app
import store

BIRTH={'year':1993,'month':5,'day':15,'hour':10,'minute':20,'hour_known':True,'sex':'F','birth_city':'서울'}
PASSWORD='test-password-235!'

def create(client):
    sid=str(uuid.uuid4());name='qa_'+uuid.uuid4().hex[:14]
    response=client.post('/v1/account/signup',json={'username':name,'password':PASSWORD,'session_id':sid,'consent':True})
    assert response.status_code==200,response.text
    data=response.json()
    return data,{'Authorization':'Bearer '+data['access_token']}

def test_account_lifecycle_private_library_and_recovery():
    c=TestClient(app);a,h=create(c);other,oh=create(c)
    sid=a['user']['session_id']
    assert c.get('/v1/account/me',headers=h).json()['user']==a['user']
    assert c.get('/v1/account/library').status_code==401
    assert c.post('/v1/account/login',json={'username':a['user']['username'],'password':'wrong-password'}).status_code==401
    for token,status in [({},401),(oh,403),(h,200)]:
        assert c.get('/v1/pay/history',params={'session_id':sid},headers=token).status_code==status
    assert c.post('/v1/relay/consume',params={'session_id':sid},json={'session_id':str(uuid.uuid4())}).status_code==401
    saved=c.post('/v1/account/save',headers=h,json={'birth':BIRTH,'lens_id':'jeokhyeol','concern':'love','axis4':'INFP','name':'검증','tier':'all'})
    assert saved.status_code==200,saved.text
    rid=saved.json()['id']
    rows=c.get('/v1/account/library',headers=h).json()['readings'];assert len(rows)==1 and rows[0]['tier']=='free'
    assert c.get('/v1/account/reading/'+rid,headers=oh).status_code==404
    assert c.get('/v1/account/download/'+rid,headers=oh).status_code==404
    html=c.get('/v1/account/download/'+rid,headers=h)
    assert html.status_code==200 and 'INFP' in html.text and 'window.print()' in html.text
    second=c.post('/v1/account/login',json={'username':a['user']['username'],'password':PASSWORD}).json()
    assert second['user']['session_id']==sid
    second_h={'Authorization':'Bearer '+second['access_token']}
    assert len(c.get('/v1/account/library',headers=second_h).json()['readings'])==1
    recovered=c.post('/v1/account/recover',json={'username':a['user']['username'],'password':'replacement-235!','recovery_code':a['recovery_code']})
    assert recovered.status_code==200
    assert c.get('/v1/account/me',headers=h).status_code==401
    assert c.get('/v1/account/me',headers=second_h).status_code==401
    rh={'Authorization':'Bearer '+recovered.json()['access_token']}
    assert c.post('/v1/account/delete',headers=rh,json={'password':'replacement-235!','confirm':False}).json()['done'] is False
    assert len(c.get('/v1/account/library',headers=rh).json()['readings'])==1
    assert c.post('/v1/account/delete',headers=rh,json={'password':'replacement-235!','confirm':True}).json()['done'] is True
    assert c.get('/v1/account/me',headers=rh).status_code==401
    assert c.get('/v1/pay/history',params={'session_id':sid}).status_code==401

def test_existing_purchase_signup_paid_archive_and_refund():
    c=TestClient(app);sid=str(uuid.uuid4());oid='test_'+uuid.uuid4().hex
    store.set_json('order:'+oid,{'order_id':oid,'session_id':sid,'status':'paid','tier':'one','lens_id':'jeokhyeol','amount':9900})
    store.set_json('orders:'+sid,[oid])
    a=c.post('/v1/account/signup',json={'username':'qa_'+uuid.uuid4().hex[:14],'password':PASSWORD,'session_id':sid,'consent':True}).json()
    h={'Authorization':'Bearer '+a['access_token']}
    assert a['user']['session_id']==sid
    assert not store.get_json('order:'+oid).get('opened_at')
    alias=str(uuid.uuid4());store.set_json('orders:'+alias,[oid])
    assert c.get('/v1/pay/history',params={'session_id':alias}).status_code==401
    r=c.post('/v1/account/save',headers=h,json={'birth':BIRTH,'lens_id':'jeokhyeol','concern':'love','axis4':'ENTJ','tier':'all'})
    assert r.status_code==200,r.text
    rid=r.json()['id'];path='/v1/account/reading/'+rid
    paid=c.get(path,headers=h).json()['report'];assert paid['tier']=='one'
    c.post('/v1/account/save',headers=h,json={'birth':BIRTH,'lens_id':'jeokhyeol','concern':'love','axis4':'ENTJ','tier':'free'})
    assert c.get(path,headers=h).json()['report']['tier']=='one'
    assert c.post('/v1/pay/restore',json={'order_id':oid,'session_id':str(uuid.uuid4())}).status_code==401
    order=store.get_json('order:'+oid);order['status']='refunded';store.set_json('order:'+oid,order)
    free=c.get(path,headers=h).json()['report'];assert free['tier']=='free' and len(free['cuts'])<len(paid['cuts'])
    assert c.post('/v1/account/save',headers=h,json={'birth':BIRTH,'lens_id':'jeokhyeol','concern':'wrong','tier':'all'}).status_code==422
    c.post('/v1/account/logout',headers=h)
    assert c.get('/v1/account/me',headers=h).status_code==401


def test_saved_reading_keeps_the_focused_situation_without_storing_raw_topic():
    c=TestClient(app);account,headers=create(c)
    saved=c.post('/v1/account/save',headers=headers,json={
        'birth':BIRTH,'lens_id':'pungun','concern':'love','tier':'free',
        'topic':{'choice':'married','choice2':'trust','choice3':'marry'}})
    assert saved.status_code==200,saved.text
    reading=c.get('/v1/account/reading/'+saved.json()['id'],headers=headers).json()
    focused=next(cut for cut in reading['report']['cuts'] if cut['id']=='topic_ask')
    assert all(word in focused['html'] for word in ('부부 관계','믿음·거짓말 문제','결혼 생활이 맞을지'))
    assert 'topic' not in reading and 'topic' not in str({k:v for k,v in reading.items() if k!='report'})
    c.post('/v1/account/delete',headers=headers,json={'password':PASSWORD,'confirm':True})


def paid_order(sid,lens_id='jeokhyeol',tier='one'):
    """값을 먼저 치른 브라우저 하나. 이 집은 선결제가 먼저입니다."""
    oid='test_'+uuid.uuid4().hex
    store.set_json('order:'+oid,{'order_id':oid,'session_id':sid,'status':'paid','tier':tier,'lens_id':lens_id,'amount':9900})
    store.set_json('orders:'+sid,[oid])
    return oid


def opens(client,headers,sid,lens_id='jeokhyeol'):
    """치른 값이 실제로 열리는가 — 자격은 서버가 봅니다."""
    from routers.report import entitled_tier
    chart=client.post('/v1/chart',json=BIRTH).json()
    report=client.post('/v1/report',headers=headers,json={'chart_id':chart['chart_id'],'lens_id':lens_id,
        'concern':'love','tier':'one','session_id':sid}).json()
    return entitled_tier(sid,lens_id),report['tier']


def test_선결제한_값은_어느_길로_들어와도_사라지지_않는다():
    """★ 손님이 못 박은 자리 — 「결제 후 로그인이니까 절대 회원가입하고
    그 결제했던 내용이 사라지면 안 돼」. 네 갈래를 다 대 봅니다."""
    c=TestClient(app)

    # ① 치르고 → 가입
    first=str(uuid.uuid4());paid_order(first)
    a=c.post('/v1/account/signup',json={'username':'qa_'+uuid.uuid4().hex[:14],'password':PASSWORD,'session_id':first,'consent':True}).json()
    ah={'Authorization':'Bearer '+a['access_token']};sid=a['user']['session_id']
    assert opens(c,ah,sid)==('one','one')
    # 가입할 때 보관되는 것은 **무료판**입니다 — 잇는 일이 값을 제 손으로
    # 열지 않습니다. 그래도 「보관한 풀이 다시 읽기」 는 치른 값이라야 하오.
    linked=c.post('/v1/account/save',headers=ah,json={'birth':BIRTH,'lens_id':'jeokhyeol','concern':'love','tier':'free'})
    assert linked.status_code==200,linked.text
    again=c.get('/v1/account/reading/'+linked.json()['id'],headers=ah)
    assert again.status_code==200 and again.json()['report']['tier']=='one',again.text

    # ② 치르고 → **기존 계정으로 로그인**. 가입 경로를 안 지나는 길이오.
    second=str(uuid.uuid4());paid_order(second,'pungun')
    back=c.post('/v1/account/login',json={'username':a['user']['username'],'password':PASSWORD,'session_id':second})
    assert back.status_code==200,back.text
    bh={'Authorization':'Bearer '+back.json()['access_token']}
    assert opens(c,bh,sid,'pungun')==('one','one')
    assert opens(c,bh,sid)==('one','one')   # ①도 그대로 있소
    got={o['order_id'] for o in c.get('/v1/account/library',headers=bh).json()['orders']}
    assert len(got)==2

    # ③ 승인이 도는 중에 로그인한 사람. 주문이 **뒤에** 서도 열려야 하오.
    late=str(uuid.uuid4())
    assert c.post('/v1/account/login',json={'username':a['user']['username'],'password':PASSWORD,'session_id':late}).status_code==200
    paid_order(late,'wolha')
    assert opens(c,bh,sid,'wolha')==('one','one')

    # ④ randomUUID 가 없는 브라우저의 난수. 자에 안 맞는다고 버리면 안 되오.
    odd='s'+uuid.uuid4().hex[:11]+'kq3x7z'
    paid_order(odd,'sigye')
    other=c.post('/v1/account/signup',json={'username':'qa_'+uuid.uuid4().hex[:14],'password':PASSWORD,'session_id':odd,'consent':True})
    assert other.status_code==200,other.text
    oh={'Authorization':'Bearer '+other.json()['access_token']}
    assert opens(c,oh,other.json()['user']['session_id'],'sigye')==('one','one')

    # 자격을 세는 자리는 **전부** 같은 묶음을 봐야 하오. 한 군데만
    # 난수 하나를 보면 그 화면에서만 구매가 사라집니다 — `_mark_opened`
    # 가 실제로 그랬습니다(entitled_tier 는 통과, 본문은 402).
    hist=c.get('/v1/pay/history',params={'session_id':sid},headers=bh)
    assert hist.status_code==200 and len(hist.json()['orders'])>=3,hist.text
    one=[o for o in hist.json()['orders'] if o['lens_id']=='pungun'][0]['order_id']
    assert c.get('/v1/pay/order/'+one,params={'session_id':sid},headers=bh).status_code==200
    trip=c.get('/v1/journey',params={'session_id':sid},headers=bh)
    assert trip.status_code==200,trip.text

    # 남의 구매는 안 따라옵니다.
    assert opens(c,oh,other.json()['user']['session_id'],'pungun')==('free','free')
    stolen=c.post('/v1/account/login',json={'username':other.json()['user']['username'],'password':PASSWORD,'session_id':second})
    assert stolen.status_code==409,stolen.text

    # 탈퇴하면 묶인 난수가 **다** 지워집니다.
    assert c.post('/v1/account/delete',headers=bh,json={'password':PASSWORD,'confirm':True}).json()['done'] is True
    for gone in (first,second,late):
        assert not store.get_json('orders:'+gone)
