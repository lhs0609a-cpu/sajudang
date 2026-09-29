"""Controlled personalization audit. No customers, payments or prediction claims."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from datetime import date
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('population_audit', ROOT/'tools/audit-reading-population.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
FOCUS = ['spine_depth', 'spine_scene', 'why', 'lack', 'daeun_now']

def normalize(s):
    # Do not give credit for changed dates, counts, Han characters, or spacing.
    return re.sub(r'[0-9一-龥\s]+', '', s)

def digest(s):
    return hashlib.sha256(s.encode()).hexdigest()

def make(index, args):
    lens = a.IDS[index % 20]
    concern = (a.PROFILES[lens]['concerns'] or ['work'])[0]
    f = a.build_features(a.build_chart(*args), as_of=date(2026, 9, 29))
    spec = a.enrich_spec(a.ask_spec(concern), lens, concern)
    topic = {'concern': concern}
    for slot in range(1, 6):
        opts = spec.get('options' if slot == 1 else f'options{slot}', [])
        if opts:
            topic['choice' if slot == 1 else f'choice{slot}'] = opts[0]['id']
    report = a.build_report(f, 'controlled', lens, 'all', concern, extras={'topic': topic})
    assert not report['extra_error'], report['extra_error']
    return f, report, lens, concern

def batch(entries):
    rows = []
    for index, args in entries:
        f, report, lens, concern = make(index, args)
        cuts = {c['id']: a.visible(c['reader_html']) for c in report['cuts'] if c['id'] != 'chart'}
        text = '\n'.join(cuts.values())
        rows.append({'sample': index, 'input': args, 'lens': lens, 'concern': concern,
                     'pillars': [p['gz'] for p in f.pillars], 'strength': f.strength,
                     'top': f.top_ten_god, 'year_role': f.year_ten_god,
                     'full': digest(text), 'normalized': digest(normalize(text)),
                     'cuts': {k: digest(normalize(v)) for k, v in cuts.items()}})
    return rows

def stats(values):
    c = Counter(values)
    n = sum(c.values())
    return {'n': n, 'unique': len(c), 'shared_readers': sum(v for v in c.values() if v > 1),
            'largest_group': max(c.values(), default=0),
            'equal_pair_rate': round(sum(v*(v-1) for v in c.values()) / (n*(n-1)), 6) if n > 1 else 0}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--label', required=True)
    p.add_argument('--count', type=int, default=10000)
    p.add_argument('--workers', type=int, default=4)
    opts = p.parse_args()
    out = ROOT/'output/personalization-audit'/opts.label
    out.mkdir(parents=True, exist_ok=True)
    population = json.loads((ROOT/'output/reading-10000/final/population.json').read_text('utf-8'))[:opts.count]
    start = time.monotonic()
    entries = list(enumerate(population))
    rows = []
    with ProcessPoolExecutor(max_workers=opts.workers) as pool:
        for i, chunk in enumerate(pool.map(batch, [entries[i:i+50] for i in range(0,len(entries),50)])):
            rows.extend(chunk)
            if (i+1) % 20 == 0:
                print(f'{opts.label}: {len(rows)}/{len(entries)} ({time.monotonic()-start:.0f}s)', flush=True)
    summary = {'commit': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
               'count': len(rows), 'as_of': '2026-09-29',
               'controls': 'Same character, concern and all five selected answers within each 500-person group; only birth inputs vary.',
               'normalization': 'Remove Arabic numbers, Han characters and whitespace; exclude chart, collapsed evidence and tables.',
               'full': stats(r['full'] for r in rows), 'normalized_full': stats(r['normalized'] for r in rows),
               'characters': {}, 'elapsed_seconds': round(time.monotonic()-start, 1)}
    examples = []
    for lens in a.IDS:
        group = [r for r in rows if r['lens'] == lens]
        summary['characters'][lens] = {key: stats(r['cuts'][key] for r in group if key in r['cuts']) for key in FOCUS}
        # A concrete collision: different actual pillars, same entire normalized core explanation.
        buckets = defaultdict(list)
        for r in group:
            buckets[r['cuts'].get('spine_depth')].append(r)
        for members in sorted(buckets.values(), key=len, reverse=True):
            pair = next(((members[0], other) for other in members[1:] if other['pillars'] != members[0]['pillars']), None)
            if pair:
                detail = []
                for r in pair:
                    _, report, _, _ = make(r['sample'], r['input'])
                    cut = next(c for c in report['cuts'] if c['id'] == 'spine_depth')
                    detail.append({**r, 'core_text': a.visible(cut['reader_html'])})
                examples.append({'lens': lens, 'shared_group': len(members), 'pair': detail})
                break
    for name, data in [('summary', summary), ('rows', rows), ('collisions', examples)]:
        (out/f'{name}.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False), flush=True)

if __name__ == '__main__':
    main()
