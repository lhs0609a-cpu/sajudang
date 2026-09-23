"""Deterministic current-engine audit; no traffic, payment, or analytics writes."""
import collections
import hashlib
import json
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'services/api'), str(ROOT)]
from tools.journey_sim import people
from engine.calendar import build_chart
from engine.features import build_features
from engine.first_reading import build_first_reading
from engine.report import build_report, _plain
from engine.editorial import ROLES
from engine.practice import build as practice


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    out = ROOT / 'output/funnel-10000'
    out.mkdir(parents=True, exist_ok=True)
    chars = list(ROLES)
    failures, metrics, samples = [], collections.Counter(), []
    signatures = {key: collections.Counter() for key in ['hook', 'free', 'paid', 'scene']}
    times = []
    started = time.perf_counter()
    for i, p in enumerate(people(count)):
        stage = 'chart'
        tick = time.perf_counter()
        try:
            f = build_features(build_chart(p['year'], p['month'], p['day'], p['hour'], p['minute'], p['sex'], p['hour_known'], p['city']), as_of=date(2026, 9, 22))
            assert len(f.pillars) == (4 if p['hour_known'] else 3)
            metrics['chart'] += 1
            stage = 'hook'
            hook = build_first_reading(f, p['concern'], p['axis4'], misses=0)
            assert len(hook) == 5
            assert all(s['html'] and s['yes'] and s['no'] and s['yes'] != s['no'] for s in hook)
            metrics['hook'] += 1
            lens = chars[i % len(chars)]
            stage = 'free'
            free = build_report(f, 'synthetic-audit', lens, 'free', p['concern'], p['axis4'])
            assert free['cuts'] and all(c['html'] for c in free['cuts'])
            if lens != 'dongja':
                assert not any('consultation-method' in c['html'] for c in free['cuts'])
                assert len([c for c in free['locked'] if c.get('teaser')]) >= 3
            assert len(practice(p['concern'])['steps']) == 3
            metrics['free'] += 1
            stage = 'paid'
            paid = build_report(f, 'synthetic-audit', lens, 'one', p['concern'], p['axis4'])
            assert paid['cuts'] and len(paid['cuts']) >= len(free['cuts'])
            metrics['paid'] += 1
            metrics['character:' + lens] += 1
            metrics['concern:' + p['concern']] += 1
            metrics['unknown_hour'] += not p['hour_known']
            for key, body in [('hook', ''.join(s['html'] for s in hook)), ('free', ''.join(c['html'] for c in free['cuts'])), ('paid', ''.join(c['html'] for c in paid['cuts'])), ('scene', ''.join(c['html'] for c in free['cuts'] if c['id'] == 'spine_scene'))]:
                if body:
                    signatures[key][hashlib.sha256(body.encode()).hexdigest()] += 1
            if i < 120:
                samples.append({'character': lens, 'concern': p['concern'], 'free_chars': sum(len(_plain(c['html'])) for c in free['cuts']), 'paid_chars': sum(len(_plain(c['html'])) for c in paid['cuts']), 'extra_input': paid.get('needs_input')})
        except Exception as e:
            failures.append({'index': i, 'stage': stage, 'error': type(e).__name__ + ': ' + str(e)[:180]})
        times.append((time.perf_counter()-tick)*1000)
        if (i+1) % 500 == 0:
            print(f'{i+1}/{count}: failures={len(failures)} elapsed={time.perf_counter()-started:.1f}s', flush=True)
    times.sort()
    result = {'population': count, 'as_of': '2026-09-22', 'kind': 'synthetic engine executions, not human reactions or successful payments', 'metrics': dict(metrics), 'failures': failures, 'latency_local_sequential_ms': {'p50': times[len(times)//2], 'p95': times[int(len(times)*.95)]}, 'elapsed_seconds': time.perf_counter()-started, 'distinctness': {k: {'unique': len(v), 'largest_share': max(v.values(), default=0)/max(1,sum(v.values()))} for k,v in signatures.items()}, 'samples': samples}
    (out/'engine-current.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['samples','failures']}, ensure_ascii=False))
    return bool(failures)

if __name__ == '__main__':
    sys.exit(main())
