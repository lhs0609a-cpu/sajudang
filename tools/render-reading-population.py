"""Render the measured before/after audit and twenty inspectable examples."""
import json
from html import escape
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/reading-10000'


def read(label,name):
    return json.loads((OUT/label/f'{name}.json').read_text('utf-8'))


def main():
    before,after=read('baseline','audit'),read('final','audit')
    old={r['sample']:r for r in read('baseline','examples')}
    new=read('final','examples')
    assert read('baseline','population')==read('final','population')
    metrics=[('서로 다른 출생 정보',before['distinct_inputs'],after['distinct_inputs']),
             ('전체 풀이',before['totals']['reports'],after['totals']['reports']),
             ('추가 무료 풀이',before['totals']['free_reports'],after['totals']['free_reports']),
             ('지정 전문 표현 노출',sum(n for _,n in before['hard_terms']),sum(n for _,n in after['hard_terms'])),
             ('200자 넘는 문단',before['totals'].get('long_paragraphs',0),after['totals'].get('long_paragraphs',0)),
             ('생성·일관성 오류',len(before['errors']),len(after['errors']))]
    table=''.join(f'<tr><th>{escape(label)}</th><td>{a:,}</td><td>{b:,}</td></tr>' for label,a,b in metrics)
    cards=[]; options=[]
    for row in new[:20]:
        lens=row['lens']; name=row['report']['lens']['name']; options.append(f'<option value="{lens}">{escape(name)}</option>')
        columns=[]
        for label,example in [('수정 전',old[row['sample']]),('수정 후',row)]:
            cuts=[c for c in example['report']['cuts'] if c['id'] in ('spine_depth','spine_scene')]
            body=''.join(f'<h3>{escape(c.get("reader_title",c["title"]))}</h3>{c["reader_html"]}' for c in cuts)
            columns.append(f'<section><h2>{label}</h2>{body}</section>')
        cards.append(f'<article data-lens="{lens}"><h2>{escape(name)}</h2><p>가상 표본 {row["sample"]+1} · 동일한 출생 정보와 선택 답변 비교</p><div class="columns">'+''.join(columns)+'</div></article>')
    page='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>1만 건 사주 풀이 개선 검증</title>
<style>body{background:#122019;color:#e6ebdf;font:16px/1.85 system-ui,sans-serif;max-width:1400px;margin:auto;padding:24px}h1,h2,h3,summary{color:#e4cb93}h1{font-size:30px}h3{font-size:18px}p{max-width:70ch}table{border-collapse:collapse;width:100%;max-width:800px}th,td{padding:12px;border-bottom:1px solid #5a6e53;text-align:left}td{font-variant-numeric:tabular-nums}.columns{display:grid;grid-template-columns:1fr 1fr;gap:32px}section{background:#1b2a20;padding:24px;min-width:0;overflow-wrap:anywhere;border-radius:12px}article{margin-top:40px}details{border:1px solid #506448;padding:14px;margin:18px 0}summary{cursor:pointer}select{padding:14px;background:#f1ebda;color:#15241b;min-width:240px;font:inherit}.reader-break{display:block;content:"";margin-top:12px}.gl{font-size:12px;color:#b7c7ac}article[hidden]{display:none}@media(max-width:800px){.columns{grid-template-columns:1fr}body{padding:16px}}</style>
<h1>1만 건 사주 풀이 · 수정 전후 검증</h1><p>실제 고객 정보가 아닌 서로 다른 가상 출생 정보 10,000건입니다. 20명 캐릭터에 500건씩 배분했습니다. 1만 건 각각을 20명 모두에게 돌린 검사는 아닙니다.</p>
<p>2026-09-29 기준, 동일한 표본과 답변을 수정 전후에 비교했습니다. 모든 글을 사람이 읽었다는 뜻이나, 사주가 사람을 정확히 맞힌다는 검증은 아닙니다. 결제율도 이 검사로 증명되지 않습니다.</p>
<table><thead><tr><th>측정 항목</th><th>수정 전</th><th>수정 후</th></tr></thead><tbody>'''+table+'''</tbody></table>
<p>전문 표현과 문단 길이는 펼치지 않은 계산 근거·표를 제외한 본문에서 측정했습니다. 지정한 단어 목록 밖의 어려운 표현이나 모든 독자의 이해도를 측정한 것은 아닙니다.</p>
<label for="lens">캐릭터별 실제 출력 비교 </label><select id="lens"><option value="all">20명 전체</option>'''+''.join(options)+'''</select>'''+''.join(cards)+'''
<script>document.getElementById('lens').addEventListener('change',e=>document.querySelectorAll('article').forEach(a=>a.hidden=e.target.value!=='all'&&a.dataset.lens!==e.target.value));</script></html>'''
    (OUT/'수정전후.html').write_text(page,'utf-8')
    rows='\n'.join(f'| {label} | {a:,} | {b:,} |' for label,a,b in metrics)
    report=f'''# 1만 건 풀이 개선 검증

같은 가상 출생 정보 10,000건을 수정 전후에 각각 실행했다. 실제 고객 데이터는 사용하지 않았다. 1920~2008년생, 성별·시간 유무·고민·선택 답변이 다른 표본이다. 캐릭터별 500건씩이며, 10,000 × 20명의 전체 조합 검사가 아니다.

| 측정 항목 | 수정 전 | 수정 후 |
|---|---:|---:|
{rows}

태어난 시간 미입력은 {after['totals']['unknown_hour']:,}건, 선택 답변 입력은 {after['totals']['answered']:,}건이다. 수정 후에는 입력 표시와 답변 반영도 {after['totals'].get('basis_checks',0):,}건 확인했다. 데이터·오류·소요 시간·표본은 baseline/ 및 final/에서 확인할 수 있다.

## 바뀐 설명

- 20명 공통 핵심 풀이를 다시 작성했다. 글자 수가 같은 특징은 함께 설명하고, 성격 하나로 단정하지 않는다.
- 도움이 되는 조건, 부담이 되는 조건, 실제 고민에서 확인할 행동을 분리했다. 5개 특징 묶음 × 7개 고민의 구체적 예시를 작성했다.
- 풍운도령의 올해 해석을 유지하고, 나머지 19명도 직접 고른 답과 올해 글자의 해석을 구분한다. 답이 없으면 실제 경험을 지어내지 않는다.
- 반영한 생년월일·시각 유무·현재 시기·직접 선택한 상황을 표시한다. 세부 근거는 펼쳐 볼 수 있다.
- 일반어 ‘지지 않다’를 사주 용어로 오역하던 문제를 고쳤다. 남아 있던 복합 전문용어와 제목을 쉬운 표현으로 바꿨다.
- 계산된 강약을 실제 체력으로 표현하던 비교 안내를 수정했다. 글자의 부재가 능력의 부재를 뜻하지 않는다는 설명을 추가했다.
- 결제 미리보기를 실제 풀이의 제한된 문장으로 개선했다. 무료와 추가 구매의 차이를 설명하며, 결제 전 가격·포함 내용·조건 확인 흐름을 유지했다.

## 신뢰와 결제 설계

권위는 확인할 수 있는 입력과 계산 근거로 제시한다. 가짜 전문가 경력, 후기, 구매자 수, 제한 시간, 적중률을 추가하지 않았다. 가상 표본 1만 건 검사는 실제 고객 1만 명의 만족도 검증이 아니다.

[GOV.UK의 명료한 문장 원칙](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/writing-guidelines/clear-language/)과 [Baymard의 상품 정보 연구](https://baymard.com/research/product-page)를 설계에 참고했다. 이 자료가 본 서비스의 결제율을 보장하지는 않는다.

실제 효과는 기존 익명 계측의 inline_offer_view → inline_offer_click → price_view → pay_start → pay_done에서 평가한다. 새 근거 설명 펼치기는 reading_expand의 stage 6으로 기록하며, 이름·생년월일·선택 답변은 계측에 보내지 않는다. 유입 조건과 기간을 맞춰 비교해야 하고, 아직 결제 효과는 측정되지 않았다.

## 검토 파일

- 수정전후.html: 20명 비교, 캐릭터 선택 필터, 펼쳐 보는 원문 근거.
- baseline/audit.json, final/audit.json: 자동 검사 결과. 단어 목록 밖의 어려움이나 인간의 이해도를 증명하지 않는다.
- baseline/population.json, final/population.json: 동일한 가상 출생 표본.
- tests.log: 전체 회귀검사 기록.
'''
    (OUT/'검증결과.md').write_text(report,'utf-8')
    print(json.dumps({'metrics':metrics,'files':['수정전후.html','검증결과.md']},ensure_ascii=False))


if __name__=='__main__': main()
