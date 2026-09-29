import json
import re
from pathlib import Path
from datetime import date

import pytest

from engine.plain_reading import html, text, WORDS
from engine.terms import MEANING
from engine.calendar import build_chart
from engine.features import build_features
from engine.report import build_report

PROFILES = json.loads((Path(__file__).resolve().parents[1]/'apps/web/lib/character-profiles.json').read_text('utf-8'))


def test_html_attributes_numbers_quotes_and_calculations_are_preserved():
    raw = '<p data-test="상관">상관 2개 · 2026년</p><q>상관없소</q><table><tr><td>甲 2.3</td></tr></table><details class="reading-calculation"><summary>계산</summary><p>상관 2개</p></details>'
    result = html(raw)
    assert 'data-test="상관"' in result
    assert '표현과 변화 성향에 해당하는 글자 2개' in result
    assert '<q>상관없소</q>' in result
    assert '<td>甲 2.3</td>' in result
    assert '<p>상관 2개</p></details>' in result
    assert re.findall(r'\d+(?:\.\d+)?', raw) == re.findall(r'\d+(?:\.\d+)?', result)


def test_ordinary_korean_words_are_not_treated_as_saju_terms():
    assert text('상관없소. 세운 계획을 끝까지 지지하오.') == '상관없소. 세운 계획을 끝까지 지지하오.'
    for value in ['받아들일지 정하시오.', '어떻게 만들지 보시오.', '내세운 기준이오.', '무엇을 맡길지 정하시오.']:
        assert text(value) == value


def test_removed_glosses_always_have_a_plain_replacement():
    assert set(MEANING) <= set(WORDS)


def test_love_readings_keep_the_relationship_context():
    assert '꾸준한 관계' in text('정재가 보이오.', 'love', 'M')
    assert '안정된 관계' in text('정관이 보이오.', 'love', 'F')
    assert '돈 관리' in text('정재가 보이오.', 'money', 'M')


def test_person_names_and_all_twenty_authored_introductions():
    from engine.easy_specialists import INTRO
    assert html('<p>정인님, 올해를 보겠소.</p>', name='정인') == '<p>정인님, 올해를 보겠소.</p>'
    assert set(INTRO) == set(PROFILES)
    assert len(set(INTRO.values())) == 20
    source=(Path(__file__).resolve().parents[1]/'apps/web/components/CheckoutReveal.tsx').read_text('utf-8')
    assert set(re.findall(r'^  ([a-z]+):\{hook:', source, re.M)) == set(PROFILES)


@pytest.fixture(scope='module')
def f():
    return build_features(build_chart(1993,11,25,None,None,'F',hour_known=False),as_of=date(2026,9,29))


@pytest.mark.parametrize('lens', PROFILES)
@pytest.mark.parametrize('tier', ['free','one'])
def test_every_specialist_delivers_readable_content_without_changing_evidence(f,lens,tier):
    result = build_report(f,'readable',lens,tier,(PROFILES[lens]['concerns'] or ['work'])[0],axis4='ENTJ')
    for cut in result['cuts']:
        assert cut['reader_html']
        assert cut['reader_title']
        reading = cut['reader_html'].split('<details')[0]
        assert 'class="gl"' not in reading or cut['id']=='chart'
        # Prose edits may remove parenthetical glossary numbers, but never invent numbers.
        original = set(re.findall(r'\d+(?:\.\d+)?', cut['html']))
        presented = set(re.findall(r'\d+(?:\.\d+)?', cut['reader_html']))
        assert presented <= original | {'10', str(f.year_num)}
    assert all('reader_html' not in cut for cut in result['locked'])


def test_pungun_explains_the_year_before_exposing_technical_terms(f):
    cut=next(c for c in build_report(f,'plain','pungun','free','work')['cuts'] if c['id']=='spine_scene')
    visible=cut['reader_html'].split('<details')[0]
    assert '상관' not in visible and '억부법' not in visible
    assert '2026' in visible
    assert '내 생각을 말하고 일하는 방식을 바꾸는 일' in visible
    assert 'reading-calculation' in cut['reader_html']
