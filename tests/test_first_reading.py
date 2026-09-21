from datetime import date
from dataclasses import replace
import re

import pytest
from engine import guard
from engine.calendar import build_chart
from engine.features import build_features
from engine.first_reading import build_first_reading, READINGS


@pytest.fixture(scope='module')
def chart():
    return build_features(build_chart(1993, 7, 14, None, None, 'F', hour_known=False), as_of=date(2026, 9, 21))


@pytest.mark.parametrize('concern', READINGS)
@pytest.mark.parametrize('axis', [None, 'INFP', 'ESTJ'])
def test_short_complete_reading_and_scope(chart, concern, axis):
    rows = build_first_reading(chart, concern, axis)
    assert [r['stage'] for r in rows] == ['0', '1', '2', '2.5', '3']
    assert all(guard.check(r['html'])[0] for r in rows)
    assert all(len(re.sub('<[^>]+>', '', r['html'])) < 310 for r in rows)
    assert all('맞지 않는 해석' in r['no'] for r in rows)
    assert '세 기둥' in rows[0]['source']
    assert not any('여덟' in r['html'] + r['source'] or '8글자' in r['html'] for r in rows)
    assert 'first-reading-action' in rows[2]['html']
    assert '다음 무료 풀이' in rows[-1]['html']
    assert rows == build_first_reading(chart, concern, axis)


def test_concern_changes_scene_action_and_question(chart):
    readings = [build_first_reading(chart, c) for c in READINGS]
    for index in (0, 1, 2, 4):
        assert len({rows[index]['html'] for rows in readings}) == 6


def test_features_change_the_reading_and_counts_are_real(chart):
    low = replace(chart, gwan=0, sik=3)
    high = replace(chart, gwan=3, sik=0)
    assert build_first_reading(low, 'work')[0]['html'] != build_first_reading(high, 'work')[0]['html']
    assert '3' in build_first_reading(high, 'work')[0]['source']


def test_rejection_changes_only_unread_parts_and_ids(chart):
    before = build_first_reading(chart, 'love')
    after = build_first_reading(chart, 'love', misses=2)
    assert before[:2] == after[:2]
    assert before[2]['html'] != after[2]['html']
    assert before[2]['statement_id'] != after[2]['statement_id']
    assert '앞선 두 응답' in after[2]['source']


def test_alias_and_axis_are_escaped_and_do_not_change_calculation(chart):
    before = chart.to_dict()
    rows = build_first_reading(chart, 'love', 'INFP', name='<img src=x onerror=alert(1)>')
    assert '<img' not in rows[0]['html']
    assert '&lt;img' in rows[0]['html']
    assert 'INFP' in rows[3]['html']
    assert chart.to_dict() == before
