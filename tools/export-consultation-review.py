"""Export actual rendered examples for reviewing the expanded reading."""
from datetime import date
from html import escape
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'services/api'))
from engine.calendar import build_chart
from engine.features import build_features
from engine.report import build_report, _plain
from engine.editorial import ROLES
from engine.lens import public

out = ROOT / 'output' / 'consultation-depth'
out.mkdir(parents=True, exist_ok=True)
features = build_features(build_chart(1993, 11, 25, 15, 55, 'M', city='서울'),
                          as_of=date(2026, 9, 21))
free = build_report(features, 'review-sample', 'pungun', 'free', 'work')
sections = []
stats = []
for cid in ROLES:
    paid = build_report(features, 'review-sample', cid, 'all', 'work')
    method = next(c for c in paid['cuts'] if 'consultation-method' in c['html'])
    stats.append({'character': cid, 'name': public(cid)['name'], 'chapter_chars': len(_plain(method['html']))})
    sections.append('<details><summary>%s · %s</summary><p class="source">%s</p>%s</details>' % (
        escape(public(cid)['name']), escape(method['title']), method['source'], method['html']))
free_html = ''.join('<article><h2>%s</h2>%s<p class="source">%s</p></article>' % (
    escape(c['title']), c['html'], c['source']) for c in free['cuts'] if c['id'] != 'chart')
practice = free['practice']
html = '''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>무료 풀이와 스무 명의 상담 · 구현 검토본</title><style>
*{box-sizing:border-box}body{margin:0;background:#161b19;color:#e9e5d9;font:17px/1.95 system-ui,sans-serif;word-break:keep-all;overflow-wrap:anywhere}
main{max-width:800px;margin:auto;padding:40px 24px}h1{font-size:32px;line-height:1.5}h2{font-size:25px}h3{font-size:21px}h4{font-size:17px;color:#d5be84;margin-bottom:6px}
p{margin:14px 0 24px}article,details{padding:28px 0;border-bottom:1px solid #3d443e}summary{cursor:pointer;color:#d5be84;font-size:21px}.source,.note{font-size:13px;color:#acb4a8}
mark{background:#d5be842a;color:#edd8a4}a{color:#d5be84}.free-depth-essay,.consultation-method{padding-top:20px;margin-top:24px;border-top:1px solid #3d443e}li{padding:8px 0}.gl{font-size:13px;color:#a9b2a7}
</style><main><p class="source">구현 검토본 · 실제 리포트 생성 결과 · 예시 생년월일 1993.11.25 15:55 / 남 / 서울 · 기준일 2026.09.21 · 고민: 일</p>
<h1>나를 이해하는 무료 풀이에서<br>선택에 써먹는 깊은 상담까지</h1>
<p>앞부분은 풍운도령의 무료 풀이입니다. 아래 스무 명의 이름을 누르면 각 인물의 실제 해석 한 장과 새로 추가한 판단 기준·실행 문장·반례를 읽을 수 있습니다. 검토용 예시이며 실제 서비스의 결제 화면은 아닙니다.</p>
<a href="#characters">스무 명의 상담 비교하기 ↓</a>'''
html += free_html
html += '<article><h2>오늘의 행동</h2><h3>%s</h3><p>%s</p><ol>%s</ol></article>' % (
    escape(practice['title']), escape(practice['action']), ''.join('<li>%s</li>' % escape(s) for s in practice['steps']))
html += '<h2 id="characters">스무 명이 각각 짚는 기준</h2>' + ''.join(sections) + '</main></html>'
(out / 'reading-preview.html').write_text(html, encoding='utf-8')
metrics = {'free_chars': sum(len(_plain(c['html'])) for c in free['cuts']),
           'action_chars': len(practice['action']) + sum(map(len, practice['steps'])), 'characters': stats}
(out / 'verification.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding='utf-8')
assert html.count('consultation-method"') == 20
assert all(s['chapter_chars'] > 500 for s in stats)
print(json.dumps(metrics, ensure_ascii=False))
