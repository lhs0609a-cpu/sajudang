"""Versioned, reproducible assignment. No birth data, pricing discrimination or forced purchase."""
from datetime import datetime, timedelta, timezone
import math

ID = 1
WINDOW_DAYS = 7

def variant(sid: str) -> int:
    h = 2166136261
    for byte in ('entry-value-v1:' + sid).encode():
        h = ((h ^ byte) * 16777619) & 0xffffffff
    return h % 2

def wilson(successes, total):
    if not total:
        return [None, None]
    z = 1.96
    p = successes / total
    d = 1 + z*z/total
    mid = (p + z*z/(2*total))/d
    radius = z*math.sqrt(p*(1-p)/total + z*z/(4*total*total))/d
    return [max(0, mid-radius), min(1, mid+radius)]

def summary(events, orders, now=None):
    now = now or datetime.now(timezone.utc)
    seen = {}
    for e in events:
        if e.get('name') != 'experiment_exposed' or e.get('n') != ID:
            continue
        try:
            at = datetime.fromisoformat(e['at'].replace('Z', '+00:00'))
            if at.tzinfo is None:
                at = at.replace(tzinfo=timezone.utc)
        except (ValueError, KeyError, TypeError):
            continue
        if at <= now:
            seen[e['sid']] = min(at, seen.get(e['sid'], at))
    groups = []
    for arm in (0, 1):
        cohort = {sid:at for sid,at in seen.items() if variant(sid)==arm and
                  now-timedelta(days=30)<=at<=now-timedelta(days=WINDOW_DAYS)}
        buyers, gross, refunds = set(), 0, 0
        for order in orders:
            sid = order.get('analytics_sid')
            if sid not in cohort or order.get('renewal'):
                continue
            try:
                paid = datetime.fromisoformat(order['paid_at'].replace('Z','+00:00'))
                if paid.tzinfo is None:
                    paid = paid.replace(tzinfo=timezone.utc)
            except (KeyError, TypeError, ValueError):
                continue
            if not cohort[sid]<=paid<=cohort[sid]+timedelta(days=WINDOW_DAYS):
                continue
            if order.get('status') not in ('paid','canceled','refunded'):
                continue
            buyers.add(sid)
            amount = int(order.get('amount') or 0)
            gross += amount
            if order.get('status') in ('canceled','refunded'):
                refunds += amount
        n = len(cohort)
        groups.append({'variant':arm,'mature_visitors':n,'buyers':len(buyers),
            'conversion':len(buyers)/n if n else None,'ci95':wilson(len(buyers),n),
            'gross':gross,'refunds':refunds,'net':gross-refunds,
            'net_per_visitor':(gross-refunds)/n if n else None})
    performance = []
    for metric, threshold in [('web_lcp',2500),('web_inp',200),('web_cls',100)]:
        values = {}
        for e in events:
            if e.get('name') != metric or e.get('ms') is None:
                continue
            try:
                at = datetime.fromisoformat(e['at'].replace('Z','+00:00'))
                if at.tzinfo is None: at=at.replace(tzinfo=timezone.utc)
                v=int(e['ms'])
            except (ValueError, KeyError, TypeError): continue
            if now-timedelta(days=30)<=at<=now and 0<=v<=120000:
                values[e['sid']]=max(v,values.get(e['sid'],0))
        ordered=sorted(values.values())
        p75=ordered[max(0,math.ceil(.75*len(ordered))-1)] if ordered else None
        performance.append({'metric':metric,'browsers':len(ordered),'p75':p75,
                            'good_threshold':threshold,'unit':'score×1000' if metric=='web_cls' else 'ms'})
    assigned = [sum(variant(sid)==arm for sid in seen) for arm in (0,1)]
    total=sum(assigned)
    srm=sum((n-total/2)**2/(total/2) for n in assigned) if total else 0
    # Fixed-horizon decision: do not select a winner from daily peeking.
    return {'id':ID,'name':'첫 화면 무료 가치 설명','window_days':WINDOW_DAYS,
        'unit':'anonymous_browser','groups':groups,
        'immature':sum(at>now-timedelta(days=WINDOW_DAYS) for at in seen.values()),
        'target_per_arm':5301,'decision':'not_evaluated','performance':performance,
        'assignment':assigned,'sample_ratio_warning':total>=100 and srm>10.828,
        'note':'각 군 5,301명과 7일 관찰 후 검토합니다. 자동으로 승자를 정하지 않습니다.'}
