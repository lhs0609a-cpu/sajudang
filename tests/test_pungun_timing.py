from datetime import date
from dataclasses import replace

import pytest

from engine.calendar import build_chart
from engine.features import build_features
from engine.pungun_timing import build
from engine.report import build_report


@pytest.fixture(scope='module')
def f():
    return build_features(build_chart(1993, 11, 25, None, None, 'F', hour_known=False),
                          as_of=date(2026, 9, 29))


def test_delivered_reading_replaces_generic_scene_and_mbti(f):
    reports = [build_report(f, 'timing', 'pungun', 'free', 'people', axis4=axis)
               for axis in ('ENTJ', 'ISFP', None)]
    readings = [next(c for c in r['cuts'] if c['id'] == 'spine_scene') for r in reports]
    assert len({c['html'] for c in readings}) == 1
    for c in readings:
        assert '왜 하필 지금' in c['title']
        assert 'mbti-reading' not in c['html']
        assert '괜찮다고 답한 뒤' not in c['html']
        assert '오늘 바로 꺼낼 수 있는 말' not in c['html']
        assert '그 장면부터 대 보시오' not in c['html']
        assert 'op-you' not in c['html']
        for value in (f.year_gz, str(f.year_num), f.day_gan, f.strength, f.daeun[f.daeun_now]['gz']):
            assert value in c['html']


def test_unknown_hour_is_not_invented(f):
    html = build(f, 'people')
    assert '출생시가 없어 시주는 제외' in html
    assert '시주 ' not in html
    assert '여덟 자' not in html


def test_before_first_daeun_does_not_describe_first_as_current(f):
    html = build(replace(f, daeun_started=False), 'work')
    assert '첫 대운에 아직 들어가지 않았소' in html
    assert '현재 대운은' not in html


def test_year_and_chart_changes_change_analysis(f):
    later = build_features(build_chart(1993, 11, 25, None, None, 'F', hour_known=False),
                           as_of=date(2027, 9, 29))
    other = build_features(build_chart(1985, 5, 4, 14, 0, 'M'), as_of=date(2026, 9, 29))
    assert build(f, 'people') != build(later, 'people')
    assert build(f, 'people') != build(other, 'people')
    assert str(later.year_num) in build(later, 'people')
    assert '출생시가 없어' not in build(other, 'people')


def test_contacts_are_calculated_not_assumed(f):
    # 子 annual branch opposes 午, joins 丑, repeats 子; 寅 has none of these.
    sample = replace(f, year_gz='甲子', pillars=[
        {'label':label, 'gan':'甲', 'ji':ji, 'gz':'甲'+ji}
        for label, ji in [('년주','午'), ('월주','丑'), ('일주','子'), ('시주','寅')]])
    html = build(sample, 'people')
    assert '년주 午와 올해 子는 충 관계' in html
    assert '월주 丑와 올해 子는 육합 관계' in html
    assert '일주의 子가 올해 지지와 같소' in html
    assert '시주 寅와 올해' not in html
