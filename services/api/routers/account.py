"""Authenticated personal library. Reports are rendered on the server, not uploaded."""
import hashlib
import json
import time
from html import escape
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import member_accounts as accounts
import store
from schemas.api import ChartRequest, ReportRequest, Concern, Tier

router=APIRouter(prefix='/v1/account',tags=['account'])


class Credentials(BaseModel):
    username:str=Field(min_length=4,max_length=32)
    password:str=Field(min_length=10,max_length=128)
    # 값을 먼저 치르고 들어온 브라우저. 가입만이 아니라 **로그인·복구에도**
    # 받습니다 — 이 집은 선결제가 먼저라, 잇는 자리가 가입에만 있으면
    # 이미 계정이 있는 손님이 치른 값을 잃습니다.
    session_id:str=Field(default='',max_length=128)


class Signup(Credentials):
    consent:bool


class Recovery(Credentials):
    recovery_code:str=Field(min_length=20,max_length=100)


class SaveReading(BaseModel):
    birth:ChartRequest
    lens_id:str=Field(max_length=30)
    concern:Concern
    axis4:str|None=Field(default=None,max_length=4)
    name:str=Field(default='',max_length=20,pattern=r'^[^<>]*$')
    tier:Tier='free'
    topic:dict|None=None


def auth(header):return accounts.authenticate(header)
def rows(account):return store.get_json('member-library:'+account['id']) or []
def key(account,rid):return 'member-reading:'+account['id']+':'+rid


@router.post('/signup')
def signup(req:Signup):
    if not req.consent:raise HTTPException(422,'회원 정보와 사주 보관 동의를 확인해 주세요.')
    account,token,recovery=accounts.register(req.username,req.password,req.session_id)
    return {'user':accounts.public(account),'access_token':token,'recovery_code':recovery}


@router.post('/login')
def login(req:Credentials):
    account,token=accounts.login(req.username,req.password,req.session_id)
    return {'user':accounts.public(account),'access_token':token}


@router.post('/recover')
def recover(req:Recovery):
    account,token,recovery=accounts.recover(req.username,req.recovery_code,req.password,req.session_id)
    return {'user':accounts.public(account),'access_token':token,'recovery_code':recovery}


@router.get('/me')
def me(authorization:str|None=Header(default=None)):
    return {'user':accounts.public(auth(authorization))}


@router.post('/logout')
def logout(authorization:str|None=Header(default=None)):
    token=(authorization or '').removeprefix('Bearer ')
    if token:store.delete('member-token:'+accounts.digest(token))
    return {'ok':True}


@router.post('/save')
def save(req:SaveReading,authorization:str|None=Header(default=None)):
    account=auth(authorization)
    from routers.chart import post_chart
    from routers.report import post_report
    from engine.mbti_reading import valid
    if req.axis4 and not valid(req.axis4):raise HTTPException(422,'MBTI를 다시 선택해 주세요.')
    chart=post_chart(req.birth)
    request=ReportRequest(chart_id=chart.chart_id,lens_id=req.lens_id,concern=req.concern,
                          axis4=req.axis4,name=req.name,tier=req.tier,session_id=account['session_id'],
                          extras={'topic':req.topic} if req.topic else None)
    report=post_report(request).model_dump()
    rid=hashlib.sha256('|'.join([chart.chart_id,req.lens_id,report['concern'],req.axis4 or '']).encode()).hexdigest()[:24]
    compare_profile={key:chart.features[key] for key in (
        'flow','top_ten_god','strength','strong_el','weak_el')}
    record={'id':rid,'chart_id':chart.chart_id,'birth':req.birth.model_dump(),'name':req.name,
            'lens_id':req.lens_id,'lens_name':report['lens']['name'],'concern':report['concern'],
            'axis4':req.axis4,'tier':report['tier'],'saved_at':time.time(),
            'compare_profile':compare_profile,'report':report}
    try:
        with store.payment_lease('library:'+account['id']):
            index=rows(account)
            if rid not in index and len(index)>=300:raise HTTPException(409,'보관함이 가득 찼습니다. 필요 없는 풀이를 삭제해 주세요.')
            previous=store.get_json(key(account,rid))
            rank={'free':0,'sub':1,'one':2,'all':3}
            # Reading a free preview must not replace an already saved paid report.
            if not previous or rank.get(report['tier'],0)>=rank.get(previous['tier'],0):
                store.set_json(key(account,rid),record)
            store.set_json('member-library:'+account['id'],[rid]+[i for i in index if i!=rid])
    except store.LeaseBusy:raise HTTPException(409,'다른 풀이를 보관 중입니다. 잠시 후 다시 저장해 주세요.')
    return {'ok':True,'id':rid}


@router.get('/library')
def library(authorization:str|None=Header(default=None)):
    account=auth(authorization)
    from routers.report import entitled_tier
    records=[]
    for rid in rows(account):
        record=store.get_json(key(account,rid))
        if record:
            item={k:v for k,v in record.items() if k not in {'report','compare_profile'}}
            item['entitlement']=entitled_tier(account['session_id'],record['lens_id'])
            records.append(item)
    orders=[];seen=set()
    # 값을 치른 난수와 계정의 난수는 다를 수 있습니다 — 선결제하고
    # 나중에 로그인한 손님이오. 묶인 난수를 다 봅니다.
    for sid in accounts.sessions(account['session_id']):
        for oid in store.get_json('orders:'+sid) or []:
            if oid in seen:continue
            seen.add(oid)
            order=store.get_json('order:'+oid)
            if order and order.get('status') in ('paid','refunded','partial_refunded'):
                orders.append({k:order.get(k) for k in ('order_id','tier','lens_id','chart_id','amount','status','paid_at','expires_at')})
    return {'user':accounts.public(account),'readings':records,'orders':orders}


def visible_record(account,rid):
    record=store.get_json(key(account,rid))
    if not record:raise HTTPException(404,'보관한 풀이를 찾을 수 없습니다.')
    from routers.report import entitled_tier,post_report,_mark_opened
    allowed=entitled_tier(account['session_id'],record['lens_id'])
    # ★ 보관한 컷의 등급과 **지금 자격**이 다르면 다시 폅니다.
    #
    #   전에는 보관한 것이 무료판이면 그대로 냈습니다. 그런데 이 집은
    #   값을 먼저 치르고 나중에 가입하는 집이라, 가입하는 순간 보관되는
    #   것은 **무료판**입니다(`/save` 는 자격을 제 손으로 안 엽니다).
    #   그 뒤로 손님이 「보관한 풀이 다시 읽기」 를 누르면 치른 값이
    #   아니라 무료판이 나왔습니다 — 자격은 멀쩡한데 화면에서만
    #   사라진 것이오. 여는 것은 손님이 누른 자리니 여기서 폅니다.
    if allowed!=record['tier']:
        from routers.chart import post_chart
        chart=post_chart(ChartRequest(**record['birth']))
        record={**record,'report':post_report(ReportRequest(chart_id=chart.chart_id,lens_id=record['lens_id'],concern=record['concern'],
                   axis4=record['axis4'],name=record['name'],tier='all',session_id=account['session_id'])).model_dump()}
    elif record['tier']!='free':
        _mark_opened(account['session_id'],record['tier'],record['lens_id'])
    return record


@router.get('/reading/{rid}')
def reading(rid:str,authorization:str|None=Header(default=None)):
    return visible_record(auth(authorization),rid)


@router.delete('/reading/{rid}')
def remove_reading(rid:str,authorization:str|None=Header(default=None)):
    account=auth(authorization)
    try:
        with store.payment_lease('library:'+account['id']):
            store.delete(key(account,rid))
            store.set_json('member-library:'+account['id'],[i for i in rows(account) if i!=rid])
    except store.LeaseBusy:raise HTTPException(409,'저장 중입니다. 잠시 후 다시 삭제해 주세요.')
    return {'ok':True}


@router.get('/download/{rid}')
def download(rid:str,authorization:str|None=Header(default=None)):
    record=visible_record(auth(authorization),rid)
    from engine.report import _plain
    report=record['report']
    title=escape((record['name'] or '나')+'의 사주 · '+record['lens_name'])
    sections=''.join('<section><h2>'+escape(c['title'])+'</h2><p>'+escape(_plain(c['html']))+'</p><small>'+escape(_plain(c['source']))+'</small></section>' for c in report['cuts'])
    practice=report.get('practice') or {}
    for field in ('title','focus','mbti','scene','action','example','decision','trap','review'):
        if practice.get(field):sections+='<p>'+escape(practice[field])+'</p>'
    sections+='<ol>'+''.join('<li>'+escape(step)+'</li>' for step in practice.get('steps',[]))+'</ol>'
    body='<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>'+title+'</title><style>body{max-width:780px;margin:40px auto;padding:24px;font:18px/1.9 sans-serif;color:#222}section{margin:40px 0;border-top:1px solid #ccc}small{color:#555}p{white-space:pre-wrap}@media print{button{display:none}}</style><h1>'+title+'</h1><p>보관한 기본 풀이 · MBTI '+escape(record['axis4'] or '미선택')+'</p><button onclick="window.print()">인쇄 · PDF로 저장</button>'+sections+'</html>'
    return HTMLResponse(body,headers={'Content-Disposition':'attachment; filename="sajudang-reading.html"','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})


class DeleteAccount(BaseModel):
    password:str=Field(min_length=1,max_length=128)
    confirm:bool=False


@router.post('/delete')
def delete_account(req:DeleteAccount,authorization:str|None=Header(default=None)):
    account=auth(authorization);accounts.limit('delete',account['id'],5)
    if not accounts.password_matches(req.password,account['password']):raise HTTPException(401,'비밀번호를 확인해 주세요.')
    from routers.privacy import forget,ForgetRequest
    # 묶인 난수를 **다** 지웁니다. 하나만 지우면 탈퇴하고도 치른 기록이
    # 다른 난수 밑에 남습니다 — 지웠다고 말해 놓고 안 지운 것이오.
    result=None
    for sid in accounts.sessions(account['session_id']):
        one=forget(ForgetRequest(session_id=sid,confirm=req.confirm))
        if result is None:result=one
        else:
            for label,count in one['plan']['removes'].items():result['plan']['removes'][label]=result['plan']['removes'].get(label,0)+count
            result['plan']['keeps']['거래 기록']=result['plan']['keeps'].get('거래 기록',0)+one['plan']['keeps'].get('거래 기록',0)
    if req.confirm:
        import referrals
        referrals.forget(account)
        store.delete('member-sessions:'+account['id'])
        for rid in rows(account):store.delete(key(account,rid))
        store.delete('member-library:'+account['id'])
        store.delete('member-name:'+account['username'])
        store.delete('member:'+account['id'])
        # Keep the ownership tombstone: old purchase session IDs never become guest keys again.
    return result
