"""Voluntary task-level ratings. No URLs, names, birth data or text answers."""
from hashlib import sha256
from .screenscan import KO
import store

PREFIX='page-evaluation:'
ROUTES=('/', '/lobby','/report/[id]','/pay','/omnibus','/summary','/daily','/relay','/me','/legal','/s/[token]')
PAGE_IDS=set(KO)|{'route:'+r for r in ROUTES}|{'book','legal'}


def record(session_id,page_id,ease,success,version=1):
    key=sha256(f'{session_id}:{page_id}:{version}'.encode()).hexdigest()
    store.set_json(PREFIX+key,dict(page_id=page_id,ease=ease,success=success,version=version),ttl=90*86400)


def stats():
    rows=[r for _,r in store.scan(PREFIX,limit=5000) if r]
    groups={}
    for row in rows:
        key=f'{row["page_id"]}@{row["version"]}'
        item=groups.setdefault(key,dict(page_id=row['page_id'],version=row['version'],n=0,
            ease_sum=0,distribution={str(i):0 for i in range(1,8)},success={'yes':0,'partly':0,'no':0}))
        item['n']+=1;item['ease_sum']+=row['ease']
        item['distribution'][str(row['ease'])]+=1;item['success'][row['success']]+=1
    for item in groups.values():
        mean=item.pop('ease_sum')/item['n']
        item['ease_mean']=round(mean,2)
        item['ease_score_100']=round((mean-1)/6*100,1)
        item['sample_note']='소표본 · 탐색용' if item['n']<30 else '자발적 응답 · 전체 고객을 대표한다고 볼 수 없음'
    return dict(rows=list(groups.values()),samples=len(rows),limited=len(rows)>=5000,
        note='한국어 자체 번역 7점 과업 용이성 문항. 100점은 (평균−1)/6×100 환산값이며 만족도·돈값 점수가 아닙니다. 최근 90일의 브라우저별 최신 자발적 응답입니다.')
