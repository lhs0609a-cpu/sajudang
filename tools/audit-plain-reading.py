"""Audit the reading edition across every character and free/paid reports."""
import json
import re
import sys
from datetime import date
from html import escape
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'services/api'))
from engine.calendar import build_chart
from engine.features import build_features
from engine.report import build_report
from engine.plain_reading import WORDS
from engine.terms import used_here


class Visible(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.text = []
    def handle_starttag(self, tag, attrs):
        if tag == 'details': self.depth += 1
        if tag in ('p','h3','h4','li','br'): self.text.append('\n')
    def handle_endtag(self, tag):
        if tag == 'details': self.depth -= 1
    def handle_data(self, data):
        if not self.depth: self.text.append(data)


def visible(html):
    parser = Visible(); parser.feed(html)
    return ''.join(parser.text)


def metric(html):
    text = visible(html)
    jargon = sum(1 for word in WORDS for m in re.finditer(re.escape(word), text)
                 if used_here(text, word, m.start(), m.end()))
    paragraphs = [x.strip() for x in text.split('\n') if x.strip()]
    return {'characters':len(text), 'jargon':jargon,
            'long_paragraphs':sum(len(x)>200 for x in paragraphs)}


def main():
    out = ROOT/'output/plain-reading'
    out.mkdir(parents=True, exist_ok=True)
    profiles = json.loads((ROOT/'apps/web/lib/character-profiles.json').read_text('utf-8'))
    rows, examples = [], []
    samples = [(1993,11,25,None,None,'F',False), (1985,5,4,14,0,'M',True), (2001,2,28,8,0,'F',True)]
    for lid, profile in profiles.items():
        concern = (profile['concerns'] or ['work'])[0]
        for idx, args in enumerate(samples):
            f = build_features(build_chart(*args), as_of=date(2026,9,29))
            for tier in ('free','one'):
                report = build_report(f, 'plain-audit', lid, tier, concern, axis4='ENTJ')
                before = ''.join(c['html'] for c in report['cuts'] if c['id'] != 'chart')
                after = ''.join(c['reader_html'] for c in report['cuts'] if c['id'] != 'chart')
                rows.append({'lens':lid,'sample':idx,'tier':tier,'before':metric(before),'after':metric(after)})
                if idx == 0 and tier == 'free':
                    c = next((c for c in report['cuts'] if c['id']=='spine_scene'), next(c for c in report['cuts'] if c['id']=='spine'))
                    examples.append(f'<article><h2>{escape(report["lens"]["name"])}</h2><div class="columns"><section><h3>원문</h3>{c["html"]}</section><section><h3>기본 읽기 화면</h3>{c["reader_html"]}</section></div></article>')
    totals = {side:{k:sum(r[side][k] for r in rows) for k in ('characters','jargon','long_paragraphs')}
              for side in ('before','after')}
    result = {'reports':len(rows),'characters':len(profiles),'totals':totals,'rows':rows}
    (out/'audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), 'utf-8')
    (out/'review.html').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>20명 쉬운 해석 검토</title><style>body{background:#17241e;color:#eadfc9;font:16px/1.9 sans-serif;margin:30px auto;padding:20px;max-width:1300px}h1,h2,h3{color:#dbc58b}.columns{display:grid;grid-template-columns:1fr 1fr;gap:28px}article{border-top:1px solid #66745e;padding:20px 0}section{min-width:0}details{border:1px solid #71826c;padding:15px}summary{cursor:pointer}.gl{font-size:12px;color:#a5b29c}@media(max-width:700px){.columns{display:block}}</style><h1>20명 전체 · 쉬운 해석 검토</h1><p>3개 명식 표본 × 무료·유료 × 20명. 계산 원문과 기본 읽기 화면을 비교합니다. 실제 구매 만족도나 결제율을 측정한 자료는 아닙니다.</p>'+''.join(examples)+'</html>', 'utf-8')
    print(json.dumps({'reports':len(rows),'totals':totals},ensure_ascii=False))


if __name__ == '__main__': main()
