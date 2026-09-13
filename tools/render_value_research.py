"""Render the local research report without fetching third-party assets."""
from pathlib import Path
import html
import re

ROOT = Path(__file__).resolve().parents[1]
source = next((ROOT / 'docs').glob('42_*.md'))
out = ROOT / 'artifacts/value-research/research.html'


def inline(text):
    text = html.escape(text)
    text = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2">\1</a>', text)
    text = re.sub(r'\[\^(\d+)\]', r'<a href="#ref-\1"><sup>[\1]</sup></a>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    return re.sub(r'`([^`]+)`', r'<code>\1</code>', text)


blocks = []
table = False
for line in source.read_text('utf-8').splitlines():
    if not line.startswith('|') and table:
        blocks.append('</tbody></table></div>')
        table = False
    if not line.strip():
        continue
    if line.startswith('|'):
        if re.fullmatch(r'[| :\-]+', line):
            continue
        cells = line.strip('|').split('|')
        tag = 'td' if table else 'th'
        if not table:
            blocks.append('<div class="table"><table><tbody>')
            table = True
        blocks.append('<tr>' + ''.join(f'<{tag}>{inline(c.strip())}</{tag}>' for c in cells) + '</tr>')
    elif match := re.match(r'^(#{1,6}) (.+)', line):
        level = len(match[1])
        blocks.append(f'<h{level}>{inline(match[2])}</h{level}>')
    elif match := re.match(r'^\[\^(\d+)\]: (.+)', line):
        blocks.append(f'<p class="reference" id="ref-{match[1]}">[{match[1]}] {inline(match[2])}</p>')
    else:
        blocks.append('<p>' + inline(line) + '</p>')
if table:
    blocks.append('</tbody></table></div>')
out.write_text('''<!doctype html><html lang="ko"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>성신당 유료 가치 딥리서치</title><style>
body{max-width:900px;margin:auto;padding:40px 24px;color:#242522;background:#faf9f5;font:17px/1.9 system-ui}
h1{font-size:34px;line-height:1.4}h2{margin-top:56px;border-top:2px solid #b9a26b;padding-top:24px;font-size:25px}
h3{margin-top:30px;font-size:20px}a{color:#315b72}table{border-collapse:collapse;width:100%;font-size:14px}
td,th{padding:12px;border-bottom:1px solid #ccc;text-align:left;min-width:90px}.table{overflow:auto}
.reference{font-size:14px;overflow-wrap:anywhere}code{overflow-wrap:anywhere}.nav{padding:16px;background:#eeeade}
@media print{body{background:white;font-size:11pt;max-width:none;padding:0}h2{break-after:avoid}h3{break-after:avoid}.nav{display:none}a{color:inherit}tr{break-inside:avoid}}
</style><p class="nav"><a href="after/review.html">페이지·결과별 전체 평가표와 생성 본문 보기</a></p>'''
    + '\n'.join(blocks) + '</html>', 'utf-8')
print(out)
