"""Export observed aggregates and explicitly hypothetical 10k behavior scenarios."""
import json
import random
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/funnel-10000'
STEPS = [
    ('고민 선택으로 이동', .35,.55,.72,.62),
    ('고민 선택 완료', .78,.87,.93,.91),
    ('생년월일 입력 완료', .62,.75,.85,.82),
    ('시간 입력·모름 선택', .82,.90,.95,.94),
    ('선택 성향 화면 통과', .82,.92,.98,.96),
    ('계산·첫 풀이 도달', .86,.92,.96,.95),
    *[(f'첫 풀이 {i}번째 응답',.86,.93,.97,.95) for i in range(1,6)],
    ('무료 상세 도달', .55,.70,.82,.78),
    ('추가 해석·가격 확인', .30,.45,.60,.54),
    ('상품 선택·결제창 진입', .18,.30,.44,.36),
    ('결제 승인', .55,.70,.82,.75),
]
LABELS = ['보수 가정','중간 가정','낙관 가정','개선 목표 가정']


def main():
    rng = random.Random(20260922)
    draws = [[rng.random() for _ in STEPS] for _ in range(10000)]
    scenarios = []
    for case, label in enumerate(LABELS,1):
        counts = [0]*len(STEPS)
        for person in draws:
            for i, row in enumerate(STEPS):
                if person[i] >= row[case]: break
                counts[i] += 1
        prev = 10000
        rows = []
        expected = 10000.
        for i, row in enumerate(STEPS):
            expected *= row[case]
            rows.append(dict(stage=row[0], assumed_rate=row[case], reached=counts[i], lost=prev-counts[i], expected=round(expected,2)))
            prev = counts[i]
        scenarios.append(dict(label=label,rows=rows,synthetic_buyers=counts[-1]))
    observed = json.loads((OUT/'observed-funnel.json').read_text(encoding='utf-16'))
    engine = json.loads((OUT/'engine-current.json').read_text(encoding='utf-8'))
    artifact = dict(generated_at=datetime.now(timezone.utc).isoformat(),visitors=10000,seed=20260922,warning='All transition probabilities are uncalibrated assumptions. Goal scenario is a target, not measured uplift or a forecast. Synthetic people are independent and do not model human emotion.', scenarios=scenarios, observed=observed, engine=engine)
    (OUT/'simulation.json').write_text(json.dumps(artifact,ensure_ascii=False,indent=2),encoding='utf-8')
    rows='\n'.join(f"| {s['label']} | {s['synthetic_buyers']} | {s['synthetic_buyers']/100:.2f}% |" for s in scenarios)
    stages='\n'.join(f"| {r['stage']} | {r['assumed_rate']*100:.0f}% | {r['reached']} | {r['lost']} |" for r in scenarios[1]['rows'])
    report=f'''# 1만 건 이용 흐름 점검 · 2026-09-22

## 숫자의 의미

**실제 1만 명의 행동을 관찰한 결과가 아니다.** 풀이 엔진은 1만 개 입력으로 실행했고, 행동 시뮬레이션은 공개된 가정 확률로 별도 실행했다. 감동·구매 의향·실제 전환 개선은 자동 검사로 측정할 수 없다. PG에 실결제는 발생시키지 않았다. 동시 1만 접속 부하 시험도 아니다.

운영 최근 30일 순차 유입 코호트: **첫 화면 {observed['sessions']}개 브라우저 → 고민 선택 8 → 생일 입력 화면 5 → 계산 완료 4 → 무료 상세 2 → 상품 화면 2 → 서버 승인 0**. 7일 관찰이 끝난 브라우저는 13개. 실사용자만인지 보장할 수 없고, 과거 QA·운영 방문이 섞였을 수 있다. 표본이 작고 11개는 유입 분류도 없으므로 예측 모델 학습이나 개선 효과 추정에 쓰지 않았다. 이 숫자는 전체 매출 집계가 아니라 정해진 진입 경로의 승인 수다.

## 가정에 따른 1만 명 중 결제 도달

| 경우 | 가상 승인 수 | 가상 전환율 |
|---|---:|---:|
{rows}

범위는 신뢰구간이 아니다. 개선 목표는 현재 중간 가정과 같은 난수 표본에 더 높은 통과 확률을 넣은 목표치이며, 수정으로 그 확률이 달성됐다는 증거가 아니다. 기존 모델에서 빠졌던 선택 성향 화면도 추가했다. 첫 해석에 부정 응답해 구매 안내가 줄어드는 흐름, 유입 채널·가격·재방문·동의/건너뛰기 차이는 각 단계 통과율에 뭉뚱그려져 있어 별도 예측하지 않는다.

### 중간 가정의 이탈 위치

| 단계 | 가정 통과율 | 남은 가상 사용자 | 직전 단계 이탈 |
|---|---:|---:|---:|
{stages}

이 모형은 기본 신규 진입 경로를 단순화한 것이다. 추가한 ‘20자리 보기’ 직접 탐색과 구매 후 재방문 경로의 비중·전환 확률은 아직 측정되지 않아 위 결제 수에 별도 반영하지 않았다. 전체 제품의 예측치로 읽으면 안 된다.

## 직접 실행한 엔진 검사

- 20명 캐릭터 × 500개 입력 = {engine['population']:,}건. 6개 고민, 시간 미상 {engine['metrics']['unknown_hour']:,}건 포함.
- 명식·5단 첫 해석·무료 본문·한 명 유료 본문 각 1만 번 생성. 빈 본문, 응답 분기 누락, 시주 개수, 무료에 유료 상담 본문 유출, 3단 행동 누락을 검사. 오류 **{len(engine['failures'])}건**.
- 로컬 순차 실행 p50 {engine['latency_local_sequential_ms']['p50']:.1f}ms, p95 {engine['latency_local_sequential_ms']['p95']:.1f}ms. 네트워크와 브라우저를 포함한 사용자 대기시간이 아니다.
- 첫 해석 본문은 {engine['distinctness']['hook']['unique']}종, 가장 많이 반복된 본문은 {engine['distinctness']['hook']['largest_share']*100:.2f}%. 무료/유료 전체 문자열이 모두 달라도 명식 등의 차이만으로 달라질 수 있으므로 ‘감동 100%’로 해석하지 않는다.
- 생년·도시·성향 분포는 합성 표본이다. 일부 추가 정보가 필요한 캐릭터는 미입력 기본 해석을 검사했다. 보호자 동의, 모든 기기/PG 수단, 정기 결제 주기, 모든 추가 입력 조합을 1만 회 검증한 것은 아니다.

## 단계별 설계와 구현

| 단계 | 관찰한 문제 / 설계 | 이번 반영 | 확인할 지표 |
|---|---|---|---|
| 첫 화면 | 시작 전 얻을 것과 비용 우려 | 카드 등록 없이 시작 표시, 읽고 남는 것 FAQ | a1→a5 |
| 고민 선택 | 제목과 실제 풀이의 연결 | 선택 고민을 미리보기 정렬에도 일관되게 적용 | a5→a3, 불일치 응답 |
| 생년월일 | 성별 미선택 시 버튼이 왜 막히는지 모름 | 입력 완료 후 성별 안내 표시 | a3→a4 |
| 출생시간·성향 | 모르는 정보에서 포기할 위험 | 기존 모름·건너뛰기 경로 유지·실브라우저 재검사 | a4/a4b→계산 완료 |
| 첫 해석 | 다섯 응답이 모두 같은 대꾸, 조언의 예외 부족 | 단계별 5쌍 대꾸, 6개 고민별 적용 예외 | 단계별 응답률·아니오·건너뛰기 |
| 무료 상세 | 돈 질문 뒤 절기 설명이 먼저 나오는 불일치 | 고민에 맞는 본문 우선, 중간 3곳 실노출·클릭 측정 | 중간 위치별 노출 후 클릭 |
| 상품 선택 | 눌렀던 질문 소실, 다른 인물이 주의 분산 | 선택 질문·장 제목 유지, 다른 인물 접기, 긴 목차 접기 | 상품 화면→결제창 |
| 결제 | 승인 전 ‘돈은 건너갔다’ 단정 | 실제 승인 확인 중으로 수정, 기존 같은 주문 재시도 유지 | 서버 승인·결제 실패 |
| 구매 후 | 긴 글보다 실행할 가치 필요 | 기존 캐릭터별 판단 기준·실제로 꺼낼 말·수정할 경우 유지 | 열람·실천 저장·재방문·환불 |
| 처음부터 둘러보기·재방문 | 스무 자리 이동을 위해 입력 단계를 다시 거침, 무료 상태가 구매 열람 요청까지 제한 | 전 화면 20자리 고정 버튼, 저장된 명식 유지, 서버 구매 권한으로 다시 열기 | 20자리 직접 진입·재열람 |

20자리 버튼은 첫 화면·입력·무료 풀이·결제·결과에 계속 표시된다. 아무 정보 없이도 인물 20명의 소개를 둘러볼 수 있다. 해석을 열 때만 필요한 입력을 받고, 저장된 명식이 있으면 바로 해석으로 간다. 구매하지 않은 인물은 서버가 무료 범위만 반환하며, 구매 권한을 브라우저가 만들지 않는다. 바로가기 경로에서 발생한 승인도 기기별 전환 집계에 반영한다. 순차 이동 표는 실제로 거치지 않은 단계를 도달했다고 채우지 않는다.

## 다음 실사용 검증

신규 사용자 20명을 모바일 중심으로 모집해 동의받은 과업 테스트를 권한다. 감동을 유도하는 질문 대신 ‘기억나는 한 문장’, ‘내 상황과 다른 부분’, ‘구매하면 무엇이 추가되는지’, ‘가격을 보기 전 기대한 답’을 묻는다. 숫자나 점수를 만들어 기록하지 말고 실제 답과 원인을 남긴다. 익명 계측은 질문 원문·생일·고민 내용 없이 화면/숫자 위치만 저장한다.

실제 전환 개선 여부는 신규 유입 코호트의 7일 서버 승인으로 판단하고, 충분한 표본이 쌓이기 전에는 개선 달성을 선언하지 않는다. 구매율과 함께 아니오 응답·오류·환불·재방문을 본다. 배포 전후 채널 차이가 크면 단순 비교하지 않고 무작위 실험으로 검증한다.

재현: `tools/audit-funnel-10000.py 10000`, `tools/export-funnel-audit.py`. 원시 합성 결과는 `engine-current.json`, 행동 모델은 `simulation.json`, 운영 익명 집계는 `observed-funnel.json`에 보관했다.
'''
    (OUT/'검증결과와-전환설계.md').write_text(report,encoding='utf-8')
    payload=json.dumps({'scenarios':scenarios,'steps':[s[0] for s in STEPS]},ensure_ascii=False)
    html='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>성신당 · 1만 명 전환 가정 실험</title><style>body{background:#111712;color:#ece8dc;font:16px/1.7 system-ui;margin:0;padding:32px;max-width:1100px;margin:auto}h1{font-size:32px}b,strong{color:#dfc48a}select,input{font:inherit}table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #354136;padding:12px;text-align:left}input{width:110px}aside{padding:20px;border:1px solid #887957;border-radius:16px;margin:24px 0}.scroll{overflow:auto}.metric{font-size:40px}small{color:#b7c0b1}a{color:#dfc48a}</style><h1>1만 명, 어느 단계에서 멈출까</h1><p>운영 실측: 첫 화면 16개 브라우저 · 순차 상품 화면 2개 · 해당 코호트 서버 승인 0건.</p><aside><b>아래는 예측이나 실측이 아닌 가정 실험입니다.</b><br>각 통과율을 바꾸면 결과가 얼마나 달라지는지 살펴보세요. 감동·실제 결제율·개선 효과를 측정한 수치가 아닙니다.</aside><label>가정 선택 <select id="case"></select></label><p>계산상 승인 기대 인원 <strong class="metric" id="total"></strong><br><small>10,000 × 각 단계 통과율의 곱. 저장된 난수 시뮬레이션 승인 수와는 조금 다릅니다.</small></p><div class="scroll"><table><thead><tr><th>단계</th><th>가정 통과율 %</th><th>남은 기대 인원</th><th>예상 이탈</th></tr></thead><tbody id="rows"></tbody></table></div><p><a href="검증결과와-전환설계.md">전체 검사 결과와 단계별 설계</a> · <a href="simulation.json">가정·실행 원본 JSON</a></p><script>const data=PAYLOAD;const choice=document.querySelector('#case');data.scenarios.forEach((s,i)=>choice.add(new Option(s.label,i)));choice.value=1;function render(){document.querySelector('#rows').innerHTML=data.scenarios[+choice.value].rows.map((r,i)=>`<tr><td>${r.stage}</td><td><input aria-label="${r.stage} 통과율" type="number" min="0" max="100" step="1" value="${Math.round(r.assumed_rate*100)}"></td><td class="remain"></td><td class="lost"></td></tr>`).join('');document.querySelectorAll('input').forEach(x=>x.oninput=calculate);calculate()}function calculate(){let n=10000;document.querySelectorAll('tbody tr').forEach(row=>{const old=n;const v=Number(row.querySelector('input').value);n*=Math.max(0,Math.min(100,Number.isFinite(v)?v:0))/100;row.querySelector('.remain').textContent=Math.round(n).toLocaleString();row.querySelector('.lost').textContent=Math.round(old-n).toLocaleString()});document.querySelector('#total').textContent=n.toFixed(1)+'명 ('+(n/100).toFixed(2)+'%)'}choice.onchange=render;render();</script></html>'''.replace('PAYLOAD',payload)
    (OUT/'전환-가정-실험.html').write_text(html,encoding='utf-8')
    print(json.dumps({s['label']:s['synthetic_buyers'] for s in scenarios},ensure_ascii=False))

if __name__ == '__main__': main()
