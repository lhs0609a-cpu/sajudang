"""Reproducible, synthetic page/result audit. Never generates human ratings."""
import argparse
import csv
from datetime import datetime, timezone, date
from html import escape
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'services/api'))
from engine import value_audit as audit, reading_quality as quality, interpretation as ip, lens


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--baseline',type=Path)
    parser.add_argument('--publish-snapshot',action='store_true')
    parser.add_argument('--auxiliary',action='store_true')
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    dataset=quality.cases()
    pages=audit.page_inventory()
    results=[]
    excerpts=[]
    auxiliary=[]
    for index,case in enumerate(dataset['cases']):
        f=quality.features(case,dataset['as_of'])
        for concern in ip.content()['domains']:
            plan=ip.build_plan(f,concern)
            if args.auxiliary:
                from engine import bank, daily
                hook=bank.build_hook(f,concern)
                day=daily.build_daily(f,on=date.fromisoformat(dataset['as_of']),concern=concern)
                for kind,payload in (('hook',hook),('daily',day)):
                    auxiliary.append(audit.score_auxiliary(payload,kind,f'{case["id"]}:{concern}:{kind}',case['id'],concern))
                summary=ip.render(plan,f,'free')
                row=audit.score_reading(summary,f'{case["id"]}:{concern}:summary',concern,'pungun','free')
                row.update(case=case['id'],kind='summary',rubric='integrated-reading-v1')
                auxiliary.append(row)
            variants=[('pungun','all',True)]
            if index==0:
                variants += [(character['id'],tier,False) for character in lens.released() for tier in ('free','one','sub','all')]
            for lid,tier,comprehensive in variants:
                reading=ip.render(plan,f,tier,comprehensive=comprehensive,lens_id=lid)
                key=f'{case["id"]}:{concern}:{lid}:{tier}:{"book" if comprehensive else "focus"}'
                row=audit.score_reading(reading,key,concern,lid,tier)
                row['case']=case['id']
                row['scope']='book' if comprehensive else 'focus'
                results.append(row)
                if comprehensive:
                    excerpts.append({'id':key,'html': ''.join('<h3>'+escape(r['title'])+'</h3>'+r['html'] for r in reading['summary']+reading['sections'])})
    report={'rubric_version':audit.RUBRIC_VERSION,'reading_version':ip.VERSION,
        'at':datetime.now(timezone.utc).isoformat(),'as_of':dataset['as_of'],
        'source_fingerprint':audit.source_fingerprint(),'note':audit.NOTE,'human_score':None,
        'sources':audit.SOURCES,'pages':pages,'results':results,'auxiliary_results':auxiliary,
        'coverage':{'routes':sum(p['scope']=='route' for p in pages),'screens':sum(p['scope']=='screen' for p in pages),
            'birth_cases':len(dataset['cases']),'concerns':6,'character_cases':1,'characters':len(lens.released()),
            'tiers':4,'results':len(results),'note':'30개 합성 명식 × 6개 고민의 종합본 + 첫 명식의 20인 × 6개 고민 × 4등급. 모든 출생 입력의 전수 검사가 아닙니다.'}}
    report['summary']={kind:{'mean':round(sum(r['score'] for r in rows)/len(rows),1),
        'min':min(r['score'] for r in rows),'below_80':sum(r['score']<80 for r in rows),'count':len(rows)}
        for kind,rows in (('pages',pages),('results',results))}
    if args.baseline:
        before=json.loads((args.baseline/'audit.json').read_text('utf-8'))
        if before['rubric_version']!=report['rubric_version']:
            raise ValueError('Cannot compare different rubrics')
        report['before']=before['summary']
        for kind in ('pages','results'):
            old={r['id']:r['score'] for r in before[kind]}
            for row in report[kind]:
                row['before']=old.get(row['id'])
                row['delta']=row['score']-old[row['id']] if row['id'] in old else None
    (args.out/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    for kind in ('pages','results','auxiliary_results'):
        with (args.out/f'{kind}.csv').open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.writer(stream)
            writer.writerow(['id','title_or_case','score_internal','before','delta','human_score','low_checks','evidence'])
            for r in report[kind]:
                writer.writerow([r['id'],r.get('title',r.get('case')),r['score'],r.get('before'),r.get('delta'),'',
                    ' / '.join(c['name'] for c in r['checks'] if c['level']<2), ' / '.join(c['evidence'] for c in r['checks'])])
    with (args.out/'human-review.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.writer(stream)
        writer.writerow(['target_id','reviewer_code','task_success_yes_partly_no','ease_1_7','clarity_1_5',
            'personal_relevance_1_5','comfort_1_5','usefulness_1_5','actual_price_shown','value_for_price_1_5',
            'can_restate_in_own_words','can_find_evidence','most_generic_sentence','next_action','notes'])
        for r in pages+results+auxiliary:
            writer.writerow([r['id']]+['']*14)
    def table(rows):
        return '<table><thead><tr><th>대상</th><th>전</th><th>후</th><th>실제 사용자</th><th>부족한 항목</th></tr></thead><tbody>'+''.join(
            f'<tr><td>{escape(r["id"])} {escape(r.get("title",""))}</td><td>{r.get("before","—")}</td><td>{r["score"]}</td><td>미측정</td><td>'+escape(' / '.join(c['name'] for c in r['checks'] if c['level']<2) or '자동 항목 충족 · 독자 검토 별도')+'</td></tr>' for r in rows)+'</tbody></table>'
    html='<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>성신당 페이지·결과 평가</title><style>body{max-width:1160px;margin:auto;padding:28px;font:16px/1.8 system-ui;color:#222;background:#fff}table{border-collapse:collapse;width:100%;font-size:14px}th,td{border-bottom:1px solid #ccc;padding:12px;text-align:left;overflow-wrap:anywhere}h2{margin-top:48px}details{border-top:1px solid #ccc;padding:16px 0}summary{cursor:pointer}a{color:#215a80}@media print{details{break-inside:avoid}}</style><h1>성신당 페이지·결과 평가</h1><p>'+escape(audit.NOTE)+'</p><p>'+escape(report['coverage']['note'])+'</p><h2>페이지별 점수</h2>'+table(pages)+'<h2>결과별 점수</h2>'+table(results)+'<h2>실제 생성 본문 180건</h2>'+''.join('<details><summary>'+escape(e['id'])+'</summary>'+e['html']+'</details>' for e in excerpts)+'</html>'
    if auxiliary:
        html=html.replace('<h2>실제 생성 본문 180건</h2>','<h2>무료 대화·일진·분석지 결과별 검사</h2><p>보조 결과는 역할에 맞는 별도 기준을 사용합니다. 종합 결과와 점수를 직접 비교하지 않습니다.</p>'+table(auxiliary)+'<h2>실제 생성 본문 180건</h2>')
    (args.out/'review.html').write_text(html,'utf-8')
    if args.publish_snapshot:
        (ROOT/'seed/value_audit.json').write_text(json.dumps(report,ensure_ascii=False,separators=(',',':')),'utf-8')
    print(json.dumps(report['summary'],ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
