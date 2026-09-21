"""Save real new reading samples and a standalone visual review of the entry work."""
from pathlib import Path
from datetime import date
import sys
import json
import re
from html import escape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'services' / 'api'))
from engine.calendar import build_chart
from engine.features import build_features
from engine.first_reading import build_first_reading, READINGS

OUT = ROOT / 'output' / 'a1-a7-research-20260921'
samples = []
for args, known in [((1993,7,14,5,20,'F'),True), ((1987,11,3,17,40,'M'),True), ((2000,2,19,None,None,'F'),False)]:
    feature = build_features(build_chart(*args,hour_known=known),as_of=date(2026,9,21))
    for concern in READINGS:
        rows = build_first_reading(feature,concern)
        samples.append({'birth':args,'hour_known':known,'concern':concern,'segments':rows,
                        'body_chars':sum(len(re.sub('<[^>]+>','',r['html'])) for r in rows)})
(OUT/'first-reading-v2-samples.json').write_text(json.dumps(samples,ensure_ascii=False,indent=2),encoding='utf-8')
labels = {'a1':'대문 · 첫 만남','a5':'지금의 고민','a3':'태어난 날','a4':'태어난 시간','a2':'별칭 · 선택','a4b':'성향 비교 · 선택','a6':'사주 준비','a7':'첫 해석'}
cards = ''.join(f'<article><h3>{step.upper()} <span>{label}</span></h3><a href="screens/390-{step}.png"><img src="screens/390-{step}.png" alt="{label} 실제 모바일 화면" loading="lazy"></a></article>' for step,label in labels.items())
concerns = {'money':'돈','work':'일','love':'사랑','people':'사람','dir':'방향','health':'몸·생활'}
readings = ''
for sample in samples[:6]:
    segments = sample['segments']
    readings += '<details><summary>'+concerns[sample['concern']]+' · 실제 생성된 첫 해석</summary>'
    for seg in segments:
        body = re.sub('<[^>]+>',' ',seg['html'])
        readings += '<h4>'+escape(seg['label'])+'</h4><p>'+escape(body)+'</p>'
    readings += '</details>'
assets = ''.join(f'<figure><img loading="lazy" src="../../apps/web/public/images/entry-v2/{key}.webp" alt="{label}"><figcaption>{label}</figcaption></figure>' for key,label in [('threshold','문을 열고'),('desk','내 이야기를 적고'),('night','나를 돌아보고'),('reading','도령과 마주 앉다')])
assets += ''.join(f'<figure><img loading="lazy" src="../../apps/web/public/images/concerns/{key}-v2.webp" alt="{label}"><figcaption>{label}</figcaption></figure>' for key,label in concerns.items())
page = '''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>성신당 · 새로 여는 첫 이야기</title>
<style>*{box-sizing:border-box}body{margin:0;background:#111b18;color:#eae4d1;font:15px/1.9 system-ui,'Malgun Gothic',sans-serif}main{max-width:1320px;margin:auto;padding:60px 30px 100px}header{max-width:840px;margin-bottom:55px}.eyebrow{color:#c9b283;font-size:11px;letter-spacing:.18em}h1{font:500 clamp(32px,4vw,54px)/1.4 Georgia,serif;letter-spacing:-.045em;margin:18px 0}h2{font-size:25px;font-weight:500;margin:55px 0 20px;color:#e2c999}header p{color:#b7c4b3}a{color:#edd5a2;text-underline-offset:4px}.links{display:flex;flex-wrap:wrap;gap:12px;margin:25px 0}.links a{border:1px solid #70836077;padding:10px 18px;border-radius:7px;text-decoration:none}.links a:first-child{background:#e1cda3;color:#1a291c}.facts{display:flex;flex-wrap:wrap;gap:10px;margin:25px 0}.facts span{padding:6px 12px;background:#283526;border-radius:5px;color:#d1d9bf}.screens{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:22px}article{min-width:0}h3{font-size:13px;color:#d7bd87}h3 span{font-weight:400;color:#b9c7af;margin-left:8px}article img{width:100%;border:1px solid #65745155;border-radius:10px;display:block}.assets{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:16px}figure{margin:0}figure img{width:100%;height:180px;object-fit:cover;border-radius:8px}figcaption{font-size:12px;color:#b3bfa8;padding:8px 0}details{border:1px solid #69795355;border-radius:9px;padding:17px 22px;margin:12px 0;background:#1b271e}summary{cursor:pointer;color:#dcc79e}details p{max-width:850px;color:#c7cfbc}h4{margin:25px 0 8px;color:#ead7b4}footer{margin-top:50px;color:#a3b198;font-size:12px}@media(max-width:850px){.screens{grid-template-columns:repeat(2,minmax(0,1fr))}.assets{grid-template-columns:repeat(2,minmax(0,1fr))}main{padding:30px 18px}}@media(max-width:430px){.screens{gap:12px}h3{font-size:11px}h3 span{display:block;margin:0}}</style>
<main><header><p class="eyebrow">SEONGSINDANG · ENTRY EXPERIENCE V2</p><h1>설명은 가볍게.<br>그대의 이야기는 깊게.</h1><p>a1–a7 대사·입력·첫 해석과 이미지 개편. 2026년 9월 21일 로컬 구현본.</p><div class="links"><a href="http://localhost:3038/?step=a1">직접 체험하기 ↗</a><a href="report.html">조사와 개선 전략</a><a href="screens/results.json">브라우저 검증 기록</a></div><div class="facts"><span>새 이미지 10장</span><span>6개 고민 · 18개 기본 해석 흐름</span><span>320 / 390 / 1366px 확인</span><span>관련 테스트 96개 통과</span></div><p>무료 해석에서 장면·이유·행동을 전하고 다음 질문으로 연결합니다. 수치와 상세 근거는 펼쳐 읽을 수 있습니다. 실제 사용자 결제 효과는 아직 측정하지 않았습니다.</p></header>
<h2>새로운 첫 만남</h2><div class="screens">'''+cards+'''</div><h2>같은 세계, 서로 다른 질문</h2><div class="assets">'''+assets+'''</div><h2>실제로 생성되는 여섯 고민의 대사</h2><p>1993-07-14 05:20, 여성, 기본 지역 기준의 합성 예시입니다. 입력과 계산 조건에 따라 다른 관점을 선택합니다.</p>'''+readings+'''<footer>이미지: 내장 image_gen 도구로 제작, 앱용 WebP로 최적화. <a href="image-prompts.json">장면 프롬프트</a> · <a href="concern-image-prompts.json">고민 이미지 프롬프트</a> · <a href="first-reading-v2-samples.json">18개 실제 생성 표본</a><br>페이지는 저장된 실제 화면 캡처입니다. 체험 링크는 이 컴퓨터의 로컬 서버가 실행 중일 때 동작합니다. 운영 배포는 하지 않았습니다.</footer></main></html>'''
(OUT/'index.html').write_text(page,encoding='utf-8')
for step in labels:
    assert (OUT/'screens'/f'390-{step}.png').is_file()
assert len(samples)==18
print('Saved visual review and 18 generated readings. Body text range:',min(s['body_chars'] for s in samples),max(s['body_chars'] for s in samples))
