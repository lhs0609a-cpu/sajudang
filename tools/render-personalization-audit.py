"""Human-reviewable before/after evidence, including limits of string diversity."""
from html import escape
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/personalization-audit'
spec=importlib.util.spec_from_file_location('controlled_audit',ROOT/'tools/audit-reading-personalization.py')
a=importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
from engine.chart_synthesis import analyze
from engine.lens import public

before=json.loads((OUT/'before/summary.json').read_text('utf-8'))
after=json.loads((OUT/'final/summary.json').read_text('utf-8'))
cases=json.loads((OUT/'before/collisions.json').read_text('utf-8'))
labels={'spine_depth':'핵심 설명','spine_scene':'상황과 올해','why':'반복의 조건','lack':'부족한 글자','daeun_now':'현재 10년 운'}

lines=['# 사주 개인화 검증 및 개선','',
       '기존의 전체 보고서 1만 개가 다르다는 결과만으로 깊은 개인화를 입증할 수 없었다. 이번에는 캐릭터별 고민과 선택 답변 5개를 고정하고, 출생 정보만 바꿔 수정 전후 1만 건씩 실행했다. 가상 표본이며 실제 고객 데이터는 사용하지 않았다.','',
       '캐릭터별 500건 × 20명이다. 서로 다른 출생 정보라도 같은 사주 구조나 해석 규칙에 해당할 수 있다. 모든 문장이 달라야 좋은 해석이라는 기준을 적용하지 않았다.','',
       '숫자·한자·공백을 제거한 기본 본문 전체가 같은지를 비교했다. 사주표·접힌 근거·표는 제외했다. 아래는 각 항목의 서로 다른 본문 수이며, 의미의 정확성·적중률·고객 만족도 점수가 아니다.','',
       '| 캐릭터 | 핵심 설명 | 상황과 올해 | 반복의 조건 | 부족한 글자 | 현재 10년 운 |','|---|---:|---:|---:|---:|---:|']
rows=[]
for lens in a.a.IDS:
    name=public(lens)['name']
    values=[f"{before['characters'][lens][k]['unique']} → {after['characters'][lens][k]['unique']}" for k in labels]
    lines.append('| '+' | '.join([name]+values)+' |')
    rows.append('<tr><th>'+escape(name)+'</th>'+''.join('<td>'+escape(v)+'</td>' for v in values)+'</tr>')
lines+=['','## 어떤 계산이 설명을 바꾸는가','',
        '- 태어난 계절의 도움, 날의 아래 글자가 주는 도움, 전체 강약을 함께 설명한다.',
        '- 역할 하나의 최다 개수에 의존하던 설명을 두 역할 묶음의 관계와 동률 표시로 보완했다.',
        '- 달의 윗글자와 날의 아랫글자가 다른 생활 자리를 뜻한다는 전통적 해석을 구분했다.',
        '- 강약과 올해 역할을 함께 보고, 도움 확보·작은 실행·범위 조정의 우선순위를 정한다.',
        '- 현재 10년 운과 올해 역할의 방향, 실제 글자의 맞섬·결합·반복 및 해당 위치를 계산한다.',
        '- 유료 설명은 무료 문단을 반복하는 대신 잘 통하는 조건과 부담 조건, 두 시기가 함께 닿는 자리를 추가로 비교한다.',
        '- 같은 입력은 같은 결과를 낸다. 이름·난수·생년월일의 해시로 문장을 다르게 만들지 않는다. 선택 답변은 사주 계산과 구분한다.','',
        '## 한계','',
        '여전히 규칙과 작성된 문장을 조합하는 해석 엔진이다. 문장이 구분된다는 사실이 그 사람의 실제 성격이나 사건을 맞혔다는 뜻은 아니다. 같은 해석을 받는 표본도 남아 있으며, 전체 명리 유파·모든 관계·정밀한 사건 시점을 다룬 것은 아니다. 행동의 우선순위는 몇 가지 명시적인 규칙을 공유한다.','',
        '기존에 핵심 본문이 같았던 서로 다른 사주 두 건을 캐릭터마다 한 쌍씩 저장했다. `개인화비교.html`에서 같은 두 사람에게 수정 후 어떤 설명이 나오는지 확인할 수 있다.','',
        '검사 실패를 숨기지 않기 위해 중간 로그도 보관했다. 최종 테스트·배포 결과는 문서 아래에 별도 기록한다.']

panels=[]; evidence=[]
for case in cases:
    cards=[]; pair_data=[]
    for old in case['pair']:
        f,report,_,_=a.make(old['sample'],old['input'])
        new=next(c for c in report['cuts'] if c['id']=='spine_depth')
        current=a.a.visible(new['reader_html'])
        pair_data.append({'input':old['input'],'pillars':old['pillars'],'before':old['core_text'],'after':current,'reasoning':analyze(f)})
        inp=old['input']; birth=f'{inp[0]}-{inp[1]:02}-{inp[2]:02} '+(f'{inp[3]:02}:00' if inp[-1] else '시간 미상')+' '+inp[5]
        cards.append('<article><h3>'+escape(birth)+'</h3><p class="basis">'+escape(' · '.join(old['pillars']))+'</p><details><summary>수정 전 · 두 사주에 같았던 핵심 설명</summary><pre>'+escape(old['core_text'])+'</pre></details><h4>수정 후</h4><pre>'+escape(current)+'</pre></article>')
    assert a.normalize(pair_data[0]['before'])==a.normalize(pair_data[1]['before'])
    changed=a.normalize(pair_data[0]['after'])!=a.normalize(pair_data[1]['after'])
    evidence.append({'lens':case['lens'],'old_core_identical':True,'new_core_different':changed,'pair':pair_data})
    panels.append('<section class="pair" data-lens="'+case['lens']+'"><h2>'+escape(public(case['lens'])['name'])+'</h2><p>기존 동일 핵심 설명 표본 중 두 건. 수정 후 핵심 설명 '+('구분됨' if changed else '같음')+'.</p><div class="cards">'+''.join(cards)+'</div></section>')
lines+=['',f"기존 동일 설명 사례 20쌍 중 수정 후 구분된 사례: {sum(x['new_core_different'] for x in evidence)}/20. 이것은 위에서 선정한 사례의 재검사이며 전체 적중률이 아니다."]
options=''.join('<option value="'+lid+'">'+escape(public(lid)['name'])+'</option>' for lid in a.a.IDS)
page='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>사주 개인화 수정 전후 검증</title>
<style>body{font-family:system-ui,"Malgun Gothic",sans-serif;background:#f5f3ee;color:#202a27;margin:0}main{max-width:1280px;margin:auto;padding:32px 24px}h1{font-size:32px}p{line-height:1.8}.note{background:#e5ece6;padding:20px;border-radius:12px}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;background:white}td,th{padding:12px;text-align:left;border-bottom:1px solid #ddd;white-space:nowrap}select{font-size:18px;padding:12px;width:100%;max-width:400px}.cards{display:grid;grid-template-columns:1fr 1fr;gap:20px}article{background:white;padding:24px;border:1px solid #d9ded5;border-radius:14px}pre{white-space:pre-wrap;font:inherit;line-height:1.9;overflow-wrap:anywhere}.basis{color:#50654e}summary{cursor:pointer;color:#755b2c;padding:12px 0}h4{margin-bottom:0}.pair[hidden]{display:none}@media(max-width:760px){.cards{grid-template-columns:1fr}main{padding:18px}}</style>
<main><h1>같은 대표 특징, 서로 다른 사주</h1><p class="note">캐릭터·고민·답변을 고정하고 출생 정보만 바꾼 가상 표본 1만 건의 수정 전후 비교입니다. 숫자와 한자를 빼고 본문을 비교했습니다. 문장의 다양성이 실제 성격·사건의 적중률을 뜻하지는 않습니다.</p><h2>항목별 서로 다른 본문 수 · 각 500건</h2><div class="scroll"><table><thead><tr><th>캐릭터</th>'''+''.join('<th>'+v+'</th>' for v in labels.values())+'''</tr></thead><tbody>'''+''.join(rows)+'''</tbody></table></div><h2>기존에 같은 설명을 받았던 두 사주 비교</h2><label for="lens">캐릭터 선택</label><br><select id="lens">'''+options+'''</select>'''+''.join(panels)+'''<script>const select=document.getElementById('lens');function show(){document.querySelectorAll('.pair').forEach(p=>p.hidden=p.dataset.lens!==select.value)}select.addEventListener('change',show);show()</script></main></html>'''
(OUT/'개인화비교.html').write_text(page,encoding='utf-8')
(OUT/'검증결과.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
(OUT/'same-chart-cases.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'cases':len(evidence),'changed':sum(x['new_core_different'] for x in evidence),'files':['개인화비교.html','검증결과.md']},ensure_ascii=False))
