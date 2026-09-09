"""10,000 synthetic decisions on the current UI, not a conversion prediction.

Probabilities are unmeasured assumptions inherited from conversion_sim.py.
Removed name/personality screens are excluded. Each hook response is a separate
transition; the following 0.55/0.70/0.82 rate means the final summary CTA only.
No request is sent to a payment gateway or production analytics.
"""
import argparse
import json
import random
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

STEPS = [
    ('concern', '첫 버튼 → 고민 선택', (.35,.55,.72)),
    ('birth', '고민 선택 → 생년월일 입력', (.78,.87,.93)),
    ('hour', '생년월일 입력 → 출생 시간', (.62,.75,.85)),
    ('chart', '출생 시간 → 계산 결과', (.82,.90,.95)),
    ('hook', '계산 결과 → 첫 해석', (.86,.92,.96)),
    *[(f'answer_{i}', f'무료 해석 {i}번째 응답', (.86,.93,.97)) for i in range(1,6)],
    ('free', '다섯 응답 → 무료 요약', (.55,.70,.82)),
    ('price', '무료 요약 → 추가 해석·가격', (.30,.45,.60)),
    ('checkout', '상품 선택 → 결제창', (.18,.30,.44)),
    ('approved', '결제창 → 승인', (.55,.70,.82)),
]
CASES = ('보수적 가정','중간 가정','낙관적 가정')

def simulate(n, sales_ready, seed=20260909):
    rng=random.Random(seed)
    draws=[[rng.random() for _ in STEPS] for _ in range(n)]
    cases=[]
    for case_index,name in enumerate(CASES):
        counts=[0]*len(STEPS)
        for person in draws:
            for i,(_,_,rates) in enumerate(STEPS):
                if person[i]>=rates[case_index]:break
                counts[i]+=1
        expected=float(n);rows=[]
        for i,(key,label,rates) in enumerate(STEPS):
            expected*=rates[case_index]
            blocked=not sales_ready and key in ('checkout','approved')
            rows.append(dict(key=key,label=label,assumed_pass_rate=rates[case_index],
                simulated_if_ready=counts[i],expected_if_ready=round(expected,2),
                simulated_current=0 if blocked else counts[i]))
        cases.append(dict(name=name,rows=rows))
    return dict(visitors_per_case=n,seed=seed,sales_ready=sales_ready,
        warning='Behavior rates are assumptions, not measured estimates or confidence bounds. Independent transitions omit channel/device/returning-user differences.',cases=cases)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args()
    with urllib.request.urlopen('https://sajudang-three.vercel.app/api/sales-status',timeout=30) as response:
        status=json.load(response)
    result=simulate(10000,status.get('ready') is True)
    result.update(observed_sales_status=status,checked_at=datetime.now(timezone.utc).isoformat())
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({c['name']:{r['key']:dict(current=r['simulated_current'],if_ready=r['simulated_if_ready'],expected_if_ready=r['expected_if_ready']) for r in c['rows'] if r['key'] in ('free','price','checkout','approved')} for c in result['cases']},ensure_ascii=False))

if __name__=='__main__':main()
