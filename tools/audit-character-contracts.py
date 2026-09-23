import json,re,sys
from pathlib import Path
from datetime import date
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'services/api'))
from engine import lens,voice
from engine.calendar import build_chart
from engine.features import build_features
from engine.report import build_report,_plain
out=ROOT/'output/character-consistency';out.mkdir(parents=True,exist_ok=True)
rows=[];words=set()
for source in [p for folder in ('app','components','lib') for p in (ROOT/'apps/web'/folder).rglob('*.tsx')]:
    words.update(re.findall(r'[가-힣0-9]+(?:시오|오|소|요)',source.read_text(encoding='utf-8')))
for known in (True,False):
 f=build_features(build_chart(1993,11,25,15 if known else None,55,'F',known,'서울'),as_of=date(2026,9,22))
 for l in lens.released():
  for incoming in ['money','work','love','people','dir','health']:
   r=build_report(f,'contract-audit',l['id'],'one' if l.get('price') else 'free',incoming)
   text=' '.join([r['opening'],r['closing'],r['practice']['action'],*r['practice']['steps'],*[c['source']+' '+c['html'] for c in r['cuts']]])
   words.update(re.findall(r'[가-힣0-9]+(?:시오|오|소|요)',text))
   rows.append({'character':l['id'],'name':l['name'],'hour_known':known,'incoming':incoming,'effective':r['concern'],'voice':lens.view(l['id'])['voice'],'address':lens.you_of(l['id'],'','F'),'opening':_plain(r['opening']),'action':r['practice']['action'],'source':_plain(r['cuts'][0]['source'])})
parity=[[w,t,ask,voice._word(w,t,ask)] for w in sorted(words) for t in voice.VOICES for ask in [False,True]]
(out/'voice-parity.json').write_text(json.dumps(parity,ensure_ascii=False),encoding='utf-8')
(out/'character-matrix.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'matrix':len(rows),'words':len(words),'parity_cases':len(parity)},ensure_ascii=False))
