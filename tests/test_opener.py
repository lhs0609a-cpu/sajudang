# -*- coding: utf-8 -*-
"""
컷은 **사람으로 연다** — 사전으로 열지 않는다.

★ 2026-09-24. 손님이 짚었습니다 — 「사주가 추상적이다」.
  서른일곱 컷이 어떻게 여는지 전수로 재 보니 서른 컷이 용어·사전으로
  열고 있었습니다 —

      「관성 0개 · 재성 1개 · 식상 3개.」
      「년주는 할아버지·할머니 같은 윗세대를 뜻하오.」
      「지금은 庚申 대운이오.」

  손님은 컷을 열 때마다 사전을 먼저 읽고 나서야 제 얘기에 닿았고,
  그걸 서른 번 했습니다. 그래서 한 장 전체가 「사주 설명」으로 읽히고
  「내 얘기」로 안 읽혔습니다.
"""
from datetime import date
import json
import re
from pathlib import Path

import pytest

from engine import guard, opener as O, voice as V
from engine.calendar import build_chart
from engine.features import build_features
from engine.report import build_report

ROOT = Path(__file__).resolve().parents[1]
PLAIN = re.compile('<[^>]+>')
GLOSS = re.compile(r'\([^)]*\)')
TONES = (V.HAEYO, V.HAGE, V.HAPSYO, V.BANMAL)

# 사전으로 여는 꼴 — 용어가 주어로 맨 앞에 선 자리요.
JARGON = re.compile(
    r'^(년주|월주|일주|시주|일간|일지|월지|년지|시지|대운|세운|십신|'
    r'재성|관성|식상|비겁|인성|상관|식신|편재|정재|편관|정관|편인|정인|'
    r'비견|겁재|신살|길신|용신|공망|조후|오행|격은|격을|사주는|명식)')

# 사람으로 여는 꼴 — 그대가 주어이거나, 그 사람이 말을 거는 자리요.
PERSON = re.compile(
    r'^(그대|자네|당신|손님|나는|저는|내가|물으신|남들|누가|요새|적으신|'
    r'지나온|급한|만드는|큰판|한번|이번 주|오늘|여태|앞일)')

CELLS = [(cut, key, say)
         for cut, table in O.SAY.items() for key, say in table.items()]


def _plain(html):
    return GLOSS.sub('', PLAIN.sub(' ', html)).strip()


def _first(html):
    return re.split(r'(?<=[.?!])\s', _plain(html))[0].strip()


@pytest.fixture(scope='module')
def chart():
    return build_features(build_chart(1993, 11, 25, 15, 55, 'M', city='서울'),
                          as_of=date(2026, 9, 24))


# ── 표 ──────────────────────────────────────────────────
def test_사람_줄은_그대가_주어다():
    """★ 맨 앞 낱말만 보면 「몫이 갈릴 때 그대는…」 같은 바른 줄이 걸리오.
    보는 것은 **그대가 그 문장 안에 있는가**와 **사전으로 열지 않는가**요.
    """
    for cut, key, say in CELLS:
        assert '그대' in say or PERSON.match(say), (cut, key, say)
        assert not JARGON.match(say), (cut, key, say)


def test_사람_줄에_눈에_보이는_것이_있다():
    """뜬 말만으로는 그림이 안 그려지오."""
    air = ('기운이오.', '자리요.', '흐름이오.')
    for cut, key, say in CELLS:
        assert not say.rstrip().endswith(air), (cut, key)
        assert 12 < len(say) < 140, (cut, key, len(say))


def test_뱅크는_하오체_한_벌이다():
    stuck = []
    for cut, key, say in CELLS:
        for one in re.split(r'(?<=[.])\s*', say):
            one = one.strip()
            if not one:
                continue
            outs = {V.speak(one, t) for t in TONES}
            if len(outs) == 1 and outs.pop() == one:
                stuck.append((cut, key, one))
    assert not stuck, stuck[:5]


def test_이어지는_어미로_문장을_끝내지_않는다():
    bad = ('서요.', '데요.', '나요.', '거든요.', '니까요.')
    for cut, key, say in CELLS:
        for one in re.split(r'(?<=[.])\s*', say):
            assert not one.strip().endswith(bad), (cut, key, one)


def test_이미_사람으로_여는_컷에는_안_얹는다():
    """같은 말을 두 번 하면 손님은 둘 다 흘리오."""
    assert not (set(O.SAY) & O.SKIP)
    for cut in ('chart', 'portrait', 'closing_cut', 'week'):
        assert cut in O.SKIP


def test_금지어를_안_넘는다():
    for cut, key, say in CELLS:
        assert guard.check(say)[0], (cut, key)


# ── 한 장 ───────────────────────────────────────────────
@pytest.mark.parametrize('lens_id', ['pungun', 'wolha', 'haengsu', 'dongja'])
def test_한_장의_컷이_사전으로_안_연다(chart, lens_id):
    got = build_report(chart, 'x', lens_id, 'all', 'money', 'INTJ')
    bad = []
    for cut in got['cuts']:
        if cut['id'] == 'chart':      # 표요 — 셈의 근거라 표로 서야 하오
            continue
        first = _first(cut['html'])
        if JARGON.match(first):
            bad.append('%s: %s' % (cut['id'], first[:48]))
    assert not bad, bad


@pytest.mark.parametrize('concern', ['money', 'work', 'love', 'people',
                                     'dir', 'health'])
def test_사람_줄이_한_장에_같은_말을_두_번_안_한다(chart, concern):
    got = build_report(chart, 'x', 'pungun', 'all', concern, 'INTJ')
    said = [_plain(c['html']).split('.')[0]
            for c in got['cuts'] if c.get('opener')]
    assert len(said) == len(set(said)), said


def test_사람_줄이_실제로_붙는다(chart):
    got = build_report(chart, 'x', 'pungun', 'all', 'money', 'INTJ')
    opened = {c['id'] for c in got['cuts'] if c.get('opener')}
    assert len(opened) >= 12, opened
    assert not (opened & O.SKIP)


def test_사람이_바뀌면_사람_줄도_바뀐다():
    import random
    rnd = random.Random(5)
    seen = set()
    for _ in range(10):
        f = build_features(
            build_chart(rnd.randint(1960, 2006), rnd.randint(1, 12),
                        rnd.randint(1, 28), rnd.randint(0, 23),
                        rnd.randint(0, 59), rnd.choice(['M', 'F'])),
            as_of=date(2026, 9, 24))
        seen.add(O.line(f, 'spine_depth') + O.line(f, 'lack'))
    assert len(seen) >= 6, len(seen)


def test_표에_없으면_지어내지_않는다(chart):
    assert O.line(chart, '없는컷') == ''
    assert O.line(chart, 'chart') == ''
    assert O.line(chart, 'lc_pungun_root') == ''


# ── 관점 컷의 머리말 ────────────────────────────────────
def test_관점_컷도_사전으로_안_연다():
    """132개 가운데 열한 개가 용어 뜻풀이로 열고 있었소 (2026-09-24)."""
    rows = json.loads((ROOT / 'seed' / 'lens_cuts.json')
                      .read_text('utf-8'))['cuts']
    bad = []
    for lens_id, cuts in rows.items():
        for cut in cuts:
            first = _first(cut.get('lead') or '')
            if JARGON.match(first):
                bad.append('%s/%s: %s' % (lens_id, cut['id'], first[:44]))
    assert not bad, bad
