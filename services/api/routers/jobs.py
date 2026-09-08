"""Authenticated scheduler endpoint; callers cannot supply cards, users or amounts."""
import hmac, os, time
from datetime import datetime,timezone
from fastapi import APIRouter,Header,HTTPException
import store
from routers import subscription

router=APIRouter(prefix='/v1/jobs',tags=['jobs'])

@router.post('/renew-subscriptions')
def renew_subscriptions(x_job_key:str|None=Header(default=None)):
    expected=os.getenv('RENEW_JOB_KEY','')
    if not expected or not x_job_key or not hmac.compare_digest(expected.encode(),x_job_key.encode()):
        raise HTTPException(status_code=403,detail='예약 작업 인증이 필요합니다.')
    result={'examined':0,'renewed':0,'failed':0,'retired':0,'more':False}
    started=time.monotonic()
    now=datetime.now(timezone.utc)
    try:
        with store.payment_lease('job:subscription-renewal'):
            for _,sub in store.scan('sub:'):
                if time.monotonic()-started>80:
                    result['more']=True
                    break
                if not sub:continue
                result['examined']+=1
                if subscription.due(sub,now):
                    got=subscription.renew(sub,now)
                    result['renewed' if got.get('ok') else 'failed']+=1
                elif sub.get('ending') and (subscription._at(sub.get('period_end')) or now)>now:
                    continue
                elif sub.get('ending') and sub.get('status')!='dead':
                    with store.payment_lease(sub['session_id']):
                        fresh=store.get_json('sub:'+sub['user_key'])
                        if (fresh and fresh.get('ending') and fresh.get('status')!='dead'
                                and (subscription._at(fresh.get('period_end')) or now)<=now):
                            subscription.retire(fresh);result['retired']+=1
            store.set_json('job:renewal-status',{'at':now.isoformat(),**result})
    except store.LeaseBusy:
        raise HTTPException(status_code=409,detail='이미 실행 중입니다.')
    return result
