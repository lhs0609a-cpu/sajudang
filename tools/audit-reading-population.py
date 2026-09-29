"""Reproducible synthetic population audit; never uses customer birth data.

10,000 distinct birth inputs, balanced across 20 characters (500 each).
Each receives the full report, including free sections. An additional free
report is checked for one tenth of the population. This is NOT 200,000 reports
or a study of human comprehension, prediction accuracy, or conversion.
"""
import argparse
import hashlib
import json
import random
import re
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'services/api'))
from engine.calendar import build_chart
from engine.features import build_features
from engine.report import build_report
from engine.plain_reading import WORDS
from engine.terms import used_here
from engine.topic import ask_spec
from engine.character_consultation import enrich_spec

PROFILES = json.loads((ROOT/'apps/web/lib/character-profiles.json').read_text('utf-8'))
IDS = list(PROFILES)
HARD = ('투출','통변','격국','궁위','십성','월령','본기','중기','생극','형충',
        '재고','설기','비겁쟁재','관살','식상생재','재다신약','조후','신왕','관인상생',
        '발현','기제','변별','배속','작동 원리','판정 축','분기','자원 배분')
PATTERN = re.compile('|'.join(map(re.escape, sorted(set(WORDS)|set(HARD),key=len,reverse=True))))


class Visible(HTMLParser):
    def __init__(self):
        super().__init__(); self.hidden = 0; self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in ('details','table'): self.hidden += 1
        if not self.hidden and tag in ('p','h2','h3','h4','li','br','blockquote'): self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ('details','table'): self.hidden = max(0,self.hidden-1)
    def handle_data(self, data):
        if not self.hidden: self.parts.append(data)


def visible(value):
    p=Visible(); p.feed(value); return ''.join(p.parts)


def samples(n):
    rng=random.Random(20260929); result=[]; seen=set()
    while len(result)<n:
        day=date(1920,1,1)+timedelta(days=rng.randrange((date(2008,12,31)-date(1920,1,1)).days+1))
        known=rng.random()>=.2
        args=(day.year,day.month,day.day,rng.randrange(24) if known else None,0 if known else None,rng.choice('FM'),known)
        if args in seen: continue
        seen.add(args); result.append(args)
    return result


def batch(task):
    entries=task; counts=Counter(); hard=Counter(); long=Counter(); sentences=Counter(); errors=[]; rows=[]; examples=[]
    for index,args in entries:
        lid=IDS[index%20]; concerns=PROFILES[lid]['concerns'] or ['work']
        concern=concerns[(index//20)%len(concerns)]
        try:
            f=build_features(build_chart(*args),as_of=date(2026,9,29))
            spec=enrich_spec(ask_spec(concern),lid,concern)
            topic={'concern':concern}
            for slot in range(1,6):
                opts=spec.get('options' if slot==1 else f'options{slot}',[])
                if opts: topic['choice' if slot==1 else f'choice{slot}']=opts[(index//20+slot)%len(opts)]['id']
            extras={'topic':topic} if index%3 else None
            report=build_report(f,'population',lid,'all',concern,axis4=None,extras=extras)
            assert not report['extra_error'], report['extra_error']
            if report.get('reading_basis'):
                basis=report['reading_basis']
                assert ('시간은 제외' in basis['birth']) == (not f.hour_known)
                assert bool(basis['answers']) == bool(extras)
                counts['basis_checks']+=1
            body=[]; cut_hashes=[]
            for c in report['cuts']:
                if c['id']=='chart': continue
                value=visible(c['reader_html']); body.append(value)
                assert '사주의 아랫줄 글자 않' not in value
                normalized=re.sub(r'[0-9一-龥\s]+','',value)
                cut_hashes.append((c['id'],hashlib.sha256(normalized.encode()).hexdigest()))
                for m in PATTERN.finditer(value):
                    if m.start() and '가'<=value[m.start()-1]<='힣': continue
                    if used_here(value,m.group(),m.start(),m.end()): hard[m.group()]+=1
                for p in value.split('\n'):
                    if len(p)>200: counts['long_paragraphs']+=1; long[p]+=1
                for s in re.split(r'[.!?]\s+|\n',value):
                    if len(s)>90: counts['long_sentences']+=1; sentences[s]+=1
                counts['cuts']+=1
            rendered='\n'.join(body)
            counts['characters']+=len(rendered); counts['reports']+=1
            counts['unknown_hour']+=not args[-1]
            counts['answered']+=bool(extras)
            rows.append({'sample':index,'lens':lid,'concern':concern,'sex':args[5],
                         'strength':f.strength,'year_role':f.year_ten_god,'hour_known':args[-1],
                         'digest':hashlib.sha256(rendered.encode()).hexdigest(),'cuts':cut_hashes})
            if (index//20)%10==0:
                free=build_report(f,'population',lid,'free',concern,extras=extras)
                assert all('html' not in c and 'reader_html' not in c for c in free['locked'])
                counts['free_reports']+=1
            if index<40:
                examples.append({'sample':index,'lens':lid,'input':args,'report':report})
        except Exception as exc:
            errors.append({'sample':index,'lens':lid,'input':args,'error':repr(exc)})
    return dict(counts),dict(hard),long.most_common(20),sentences.most_common(20),errors,rows,examples


def main():
    p=argparse.ArgumentParser(); p.add_argument('--count',type=int,default=10000)
    p.add_argument('--workers',type=int,default=4); p.add_argument('--label',default='baseline')
    opts=p.parse_args(); out=ROOT/'output/reading-10000'/opts.label; out.mkdir(parents=True,exist_ok=True)
    population=samples(opts.count); start=time.monotonic()
    (out/'population.json').write_text(json.dumps(population),encoding='utf-8')
    totals=Counter(); hard=Counter(); long=Counter(); sentences=Counter(); errors=[]; rows=[]; examples=[]
    jobs=[list(enumerate(population))[i:i+50] for i in range(0,len(population),50)]
    with ProcessPoolExecutor(max_workers=opts.workers) as pool:
        for index,result in enumerate(pool.map(batch,jobs)):
            c,h,l,s,e,r,x=result; totals.update(c); hard.update(h); long.update(dict(l)); sentences.update(dict(s)); errors.extend(e); rows.extend(r); examples.extend(x)
            if (index+1)%20==0: print(f'{opts.label}: {(index+1)*50}/{opts.count}, errors={len(errors)}, seconds={time.monotonic()-start:.0f}',flush=True)
    per_lens={lid:sum(row['lens']==lid for row in rows) for lid in IDS}
    result={'synthetic':True,'as_of':'2026-09-29','seed':20260929,'distinct_inputs':len(population),
            'coverage':'one full character report per input, balanced across 20 characters; extra free report for every tenth input',
            'totals':dict(totals),'per_lens':per_lens,'hard_terms':hard.most_common(),
            'long_paragraph_examples':long.most_common(40),'long_sentence_examples':sentences.most_common(40),
            'errors':errors,'elapsed_seconds':round(time.monotonic()-start,1),
            'unique_report_texts':len({r['digest'] for r in rows})}
    for name,data in [('audit',result),('rows',rows),('examples',examples)]:
        (out/f'{name}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('long_paragraph_examples','long_sentence_examples')},ensure_ascii=False),flush=True)
    return bool(errors) or totals['reports']!=opts.count


if __name__=='__main__': sys.exit(main())
