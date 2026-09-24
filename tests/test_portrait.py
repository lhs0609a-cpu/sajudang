# -*- coding: utf-8 -*-
"""어떤 사람인가 — 사람을 그리는 자리가 실제로 사람을 그리는가."""
from datetime import date
import random
import re

import pytest

from engine import guard, lens as lens_mod, voice as V
from engine import portrait as P
from engine.calendar import build_chart
from engine.features import build_features

PLAIN = re.compile('<[^>]+>')
TONES = (V.HAEYO, V.HAGE, V.HAPSYO, V.BANMAL)
CELLS = [(facet, key, say)
         for facet, table in P.TABLES.items() for key, say in table.items()]


def _plain(html):
    return PLAIN.sub('', html)


def _person(seed):
    rnd = random.Random(seed)
    return build_features(
        build_chart(rnd.randint(1960, 2006), rnd.randint(1, 12),
                    rnd.randint(1, 28), rnd.randint(0, 23), rnd.randint(0, 59),
                    rnd.choice(['M', 'F'])),
        as_of=date(2026, 9, 24))


@pytest.fixture(scope='module')
def chart():
    return build_features(build_chart(1993, 11, 25, 15, 55, 'M', city='서울'),
                          as_of=date(2026, 9, 24))


@pytest.fixture(scope='module')
def nohour():
    return build_features(build_chart(1993, 7, 14, None, None, 'F',
                                      hour_known=False),
                          as_of=date(2026, 9, 21))


# ── 표 ──────────────────────────────────────────────────
def test_표에_빈칸이_없다():
    from engine.editorial import ROLES
    assert set(P.VIEW) == set(ROLES), set(P.VIEW) ^ set(ROLES)
    for lens_id, order in P.VIEW.items():
        assert len(order) == len(set(order)), lens_id
        for facet in order:
            assert facet in P.TABLES and facet in P.HEAD, (lens_id, facet)
    for facet in P.TABLES:
        assert facet in P.HEAD and facet in P.AXIS_OF, facet
    from engine import why as why_mod
    for facet, axis in P.AXIS_OF.items():
        assert axis in why_mod.AXIS, facet


def test_스무_명이_서로_다른_차례로_본다():
    """줄이 같으면 그 둘은 같은 사람이오."""
    seen = {}
    for lens_id, order in P.VIEW.items():
        row = tuple(order)
        assert row not in seen, (lens_id, seen.get(row))
        seen[row] = lens_id


def test_여는_줄이_스무_명_다_다르다():
    leads = {lens_id: P._lead(lens_id) for lens_id in P.VIEW}
    assert len(set(leads.values())) == len(P.VIEW)


# ── 글 ──────────────────────────────────────────────────
def test_단정문이지_조건문이_아니다():
    """「…수 있소」 는 아무것도 안 지우는 말이오. 사람을 그리는 자리요.

    ★ 따옴표 **안**의 물음표는 봅니다 — 그건 남이 그대에게 하는 말이오.
    """
    for facet, key, say in CELLS:
        assert not say.rstrip().endswith('?'), (facet, key)
        assert '수 있소' not in say, (facet, key)
        assert '일 것이오' not in say, (facet, key)
        assert '일지도' not in say, (facet, key)


def test_면마다_눈에_보이는_것을_댄다():
    """「자리」 「마음」 만으로 된 줄은 그림이 안 그려지오."""
    # ★ **물건 · 자리 · 한 일**만 넣소. 「자리」 「마음」 같은 아무 데나
    #   붙는 말을 넣으면 그날로 이 자가 거울이 되오 (CLAUDE.md).
    things = ('회의', '카드', '밥값', '약속', '단톡', '책상', '달력', '잠',
              '연락', '모임', '자료', '숫자', '날짜', '일정', '첫 줄', '실수',
              '액자', '오타', '술자리', '장바구니', '배달비', '답장', '첫 삽',
              '강의', '십 년', '문', '얘기', '방', '집', '야근', '회식',
              '견적', '현관', '지하철', '목록', '연락처', '이모티콘')
    for facet, key, say in CELLS:
        assert any(t in say for t in things), (facet, key, say)


def test_뱅크는_하오체_한_벌이다():
    """다섯 말투를 걸어도 안 바뀌는 줄은 원문이 하오체가 아니라는 뜻이오."""
    stuck = []
    for facet, key, say in CELLS + [('CLOSING', '-', P.CLOSING)]:
        for one in re.split(r'(?<=[.])\s*', _plain(say)):
            one = one.strip()
            if not one:
                continue
            outs = {V.speak(one, t) for t in TONES}
            if len(outs) == 1 and outs.pop() == one:
                stuck.append((facet, key, one))
    assert not stuck, stuck[:5]


def test_이어지는_어미로_문장을_끝내지_않는다():
    """「…해서요」 「…인데요」 로 끝내면 해요체에서 「…해서예요」 가 나오오.

    ★ 갈아 낀 **결과**를 자로 재려 들면 「먼저 서네」 같은 바른 말까지
      걸리오. 원인은 원문에 있소 — 이어 주는 어미로 문장을 닫은 자리요.
    """
    bad = ('서요.', '데요.', '나요.', '거든요.', '니까요.')
    wrong = []
    for facet, key, say in CELLS + [('CLOSING', '-', P.CLOSING)]:
        for one in re.split(r'(?<=[.])\s*', _plain(say)):
            one = one.strip()
            if any(one.endswith(tail) for tail in bad):
                wrong.append((facet, key, one))
    assert not wrong, wrong


def test_금지어를_안_넘는다(chart):
    for lens_id in P.VIEW:
        cut = P.build(chart, lens_id, 6)
        assert cut and guard.check(cut['html'])[0], lens_id
        assert guard.check(cut['source'])[0], lens_id


# ── 사람 ────────────────────────────────────────────────
def test_스무_명이_같은_사람을_그린다(chart):
    """캐릭터가 바뀐다고 그대가 다른 사람이 되면 그건 소설이오."""
    said = {}
    for lens_id in P.VIEW:
        for row in P.rows(chart, lens_id, 6):
            if row['facet'] in said:
                assert said[row['facet']] == row['say'], row['facet']
            said[row['facet']] = row['say']
    assert len(said) >= 8


def test_캐릭터마다_먼저_보는_면이_다르다(chart):
    heads = {lens_id: P.rows(chart, lens_id, 6)[0]['facet'] for lens_id in P.VIEW}
    assert len(set(heads.values())) >= 6, heads


@pytest.mark.parametrize('lens_id', sorted(P.VIEW))
def test_여섯_면이_다_서고_근거에_센_값이_있다(chart, lens_id):
    got = P.rows(chart, lens_id, 6)
    assert len(got) == len(P.VIEW[lens_id])
    for row in got:
        assert row['head'] and row['say'] and row['ground']
    cut = P.build(chart, lens_id, 6)
    assert re.search(r'\d', cut['source']), cut['source']
    assert len(_plain(cut['html'])) > 300


def test_사람이_바뀌면_그림이_바뀐다():
    drawn = {_plain(P.build(_person(i), 'pungun', 5)['html']) for i in range(12)}
    assert len(drawn) >= 8, len(drawn)


def test_시각을_모르면_기둥을_지어내지_않는다(nohour):
    cut = P.build(nohour, 'pungun', 6)
    assert '세 기둥' in cut['source']
    assert '여덟' not in cut['source']


def test_아닌_줄은_빼라고_적는다(chart):
    assert '다 맞는 글은' in P.build(chart, 'pungun', 3)['html']


def test_이름과_호칭이_그려지지_않고_셈도_안_바뀐다(chart):
    before = chart.to_dict()
    cut = P.build(chart, 'pungun', 3, you='<img src=x>')
    assert '<img' not in cut['html']
    assert chart.to_dict() == before


# ── 자리 ────────────────────────────────────────────────
def test_훅에서_사람을_맨_먼저_그린다(chart):
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    made = client.post('/v1/chart', json={
        'year': 1993, 'month': 11, 'day': 25, 'hour': 15, 'minute': 55,
        'hour_known': True, 'sex': 'M', 'birth_city': '서울'}).json()
    got = client.post('/v1/hook', json={
        'chart_id': made['chart_id'], 'concern': 'money', 'lens_id': 'pungun'})
    assert got.status_code == 200, got.text
    segments = got.json()['segments']
    assert segments[0]['stage'] == 'portrait', [s['stage'] for s in segments]
    assert segments[0]['label'] == P.TITLE


def test_풀이에서_명식_바로_뒤에_선다(chart):
    from engine.report import build_report
    for lens_id in ('pungun', 'wolha', 'dongja'):
        got = build_report(chart, 'x', lens_id, 'all', 'money', 'INTJ')
        ids = [c['id'] for c in got['cuts']]
        assert ids[:2] == ['chart', 'portrait'], (lens_id, ids[:4])


def test_값을_치르기_전에도_보인다(chart):
    """알아봐 준 적 없는 집에 값을 치를 까닭이 없소."""
    from engine.report import build_report
    free = build_report(chart, 'x', 'pungun', 'free', 'money', 'INTJ')
    assert 'portrait' in {c['id'] for c in free['cuts']}
    assert 'portrait' not in {c['id'] for c in (free.get('locked') or [])}
