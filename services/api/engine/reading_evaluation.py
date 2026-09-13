"""Opt-in reader feedback. No birth data, chart ID, name, motives or free text stored."""
from hashlib import sha256
from datetime import datetime, timezone
import store

DIMENSIONS = ('clarity', 'recognition', 'comfort', 'usefulness')
VALUES = {'yes': 2, 'partly': 1, 'no': 0}
PREFIX = 'reading-evaluation:'


def purchased(session_id, lens_id):
    # Include refunds: excluding disappointed purchasers would bias value ratings.
    # This verifies a past transaction; it never grants reading access.
    for order_id in store.get_json('orders:'+session_id) or []:
        order=store.get_json('order:'+order_id) or {}
        if order.get('session_id')!=session_id or order.get('status') not in ('paid','refunded'):
            continue
        if order.get('tier') in ('all','sub') or order.get('lens_id')==lens_id:
            return True
    return False


def record(session_id, chart_id, lens_id, version, answers, verified, meta=None):
    # Updates replace the same browser/chart/character/version response.
    meta=meta or {}
    result_key=sha256(meta.get('result_key','legacy').encode()).hexdigest()[:20]
    key = sha256(f'{session_id}|{chart_id}|{lens_id}|{version}|{meta.get("concern")}|{meta.get("scope")}|{result_key}'.encode()).hexdigest()
    row={'lens_id': lens_id, 'version': version, 'answers': answers,
        'verified_payment': verified, 'at': datetime.now(timezone.utc).isoformat()}
    if meta:
        row.update(concern=meta['concern'],scope=meta['scope'],result_key=result_key,
            value_for_money=meta.get('value_for_money') if verified else None)
    store.set_json(PREFIX + key,row,ttl=90*86400)


def stats():
    rows = [row for _, row in store.scan(PREFIX, limit=5000) if row]
    editions = {}
    for row in rows:
        key = str(row['version'])
        item = editions.setdefault(key, {'samples':0, 'paid_samples':0,
            'dimensions': {d:{v:0 for v in VALUES} for d in DIMENSIONS}})
        item['samples'] += 1
        item['paid_samples'] += int(row['verified_payment'])
        for d, value in row['answers'].items():
            item['dimensions'][d][value] += 1
    groups={}
    for row in rows:
        key=':'.join(str(row.get(k,'legacy')) for k in ('version','scope','concern','lens_id','result_key'))
        group=groups.setdefault(key,{'id':key,'version':row['version'],'lens_id':row['lens_id'],
            'scope':row.get('scope'),'concern':row.get('concern'),'n':0,'sum':0,'paid_n':0,'value_n':0,'value_sum':0})
        group['n']+=1
        group['sum']+=sum(VALUES[row['answers'][d]] for d in DIMENSIONS)/8*100
        group['paid_n']+=int(row['verified_payment'])
        if row.get('value_for_money') is not None:
            group['value_n']+=1;group['value_sum']+=row['value_for_money']
    for group in groups.values():
        group['reader_score']=round(group.pop('sum')/group['n'],1)
        value_sum=group.pop('value_sum')
        group['value_mean_1_5']=round(value_sum/group['value_n'],2) if group['value_n'] else None
        group['sample_note']='자발적 응답 · 개인별 결과의 소표본이며 전체 사용자 예측 점수 아님'
    return {'editions': editions, 'results':list(groups.values()), 'samples': len(rows), 'limited': len(rows) >= 5000,
        'note': '최근 90일의 자발적 응답입니다. 같은 브라우저·명식·캐릭터·버전의 응답은 갱신됩니다. 정확도나 결제 전환율이 아닙니다.'}
