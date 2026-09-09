import pytest
import re
from engine.calendar import build_chart
from engine.features import build_features
from engine.lens_cuts import _counted
from engine.report import build_report
from engine.bank import build_hook
from engine.reading_facts import visible_elements

@pytest.mark.parametrize('known', [True, False])
def test_display_counts_do_not_round_hidden_stem_weights_into_characters(known):
    f = build_features(build_chart(1993,11,25,15 if known else None,0,'F',hour_known=known))
    counts = visible_elements(f)
    assert sum(counts.values()) == (8 if known else 6)
    assert counts['화'] == 0 and f.elements['화'] > 0
    line = _counted(f, ['weak_el'])
    assert ('나무가 0' if known else '불이 0') in line
    assert ('여덟 자' if known else '여섯 자') in line

def test_report_and_hook_use_known_pillars_and_actual_category_counts():
    f = build_features(build_chart(1993,11,25,None,0,'F',hour_known=False))
    report = build_report(f,'reading-scope-regression','pungun','free','money')
    rows = report['cuts'] + report['locked']
    assert all('여덟 글자' not in row.get('html','') for row in rows)
    assert all('여덟 자' not in (row.get('source') or '') for row in rows)
    place = next(c for c in report['cuts'] if c['id']=='place')
    assert f.sik == 3
    assert '식상이 3개라' in re.sub(r'<[^>]+>', '', place['html'])
    rarity = next(c for c in report['cuts'] if c['id']=='rarity')
    assert '겉글자' in rarity['html'] and '숨은 기운' in rarity['html']
    assert all('여덟 글자' not in s['html'] for s in build_hook(f,'money'))
