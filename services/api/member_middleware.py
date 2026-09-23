"""A member-owned purchase session requires the member's authenticated token."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from fastapi import HTTPException
import member_accounts as accounts
import store


class MemberSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self,request,call_next):
        if request.method=='OPTIONS' or request.url.path.startswith('/v1/account/'):
            return await call_next(request)
        sid=request.query_params.get('session_id')
        session_ids=[sid]
        body={}
        if request.method in ('POST','PUT','DELETE','PATCH') and 'application/json' in request.headers.get('content-type',''):
            try:body=await request.json()
            except Exception:body={}
            if isinstance(body,dict):
                session_ids.append(body.get('session_id'))
                sid=body.get('session_id') or sid
        owners=set()
        for candidate in session_ids:
            if isinstance(candidate,str) and accounts.owner(candidate):owners.add(accounts.owner(candidate))
            if isinstance(candidate,str):
                for oid in store.get_json('orders:'+candidate) or []:
                    order=store.get_json('order:'+oid) or {}
                    bound=store.get_json('member-order:'+oid) or order.get('member_id') or accounts.owner(order.get('session_id'))
                    if bound:owners.add(bound)
        if request.url.path=='/v1/pay/restore' and isinstance(body,dict):
            order=store.get_json('order:'+str(body.get('order_id',''))) or {}
            bound=store.get_json('member-order:'+str(body.get('order_id',''))) or order.get('member_id') or accounts.owner(order.get('session_id'))
            if bound:owners.add(bound)
        if owners:
            try:
                account=accounts.authenticate(request.headers.get('authorization'))
                if owners!={account['id']}:raise HTTPException(403,'다른 회원의 구매 내역에는 접근할 수 없습니다.')
                if request.url.path=='/v1/pay/restore' and accounts.owner(sid)!=account['id']:
                    raise HTTPException(403,'회원 구매는 로그인한 보관함에서 복원해 주세요.')
            except HTTPException as exc:return JSONResponse({'detail':exc.detail},status_code=exc.status_code)
        return await call_next(request)
