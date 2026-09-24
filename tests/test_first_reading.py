# -*- coding: utf-8 -*-
"""첫 해석 v3 — 가름 · 반증 · 고른 답이 닿는가."""
from datetime import date
from dataclasses import replace
import re

import pytest

from engine import guard, first_reading as fr
from engine.calendar import build_chart
from engine.features import build_features
from engine.first_reading import CELL, FACTS, RANK, WRONG, build_first_reading

CONCERNS = [c for c in RANK if c != 'real_estate']
PLAIN = re.compile('<[^>]+>')


def _plain(html):
    return PLAIN.sub('', html)


@pytest.fixture(scope='module')
def chart():
    """시각 미상 — 시주를 안 세우는 사람으로 잡습니다."""
    return build_features(build_chart(1993, 7, 14, None, None, 'F',
                                      hour_known=False),
                          as_of=date(2026, 9, 21))


@pytest.fixture(scope='module')
def timed():
    return build_features(build_chart(1993, 11, 25, 15, 55, 'M', city='서울'),
                          as_of=date(2026, 9, 21))


# ── 꼴 ──────────────────────────────────────────────────
@pytest.mark.parametrize('concern', RANK)
@pytest.mark.parametrize('axis', [None, 'INFP', 'ESTJ'])
def test_다섯_마디가_서고_금지어를_안_넘는다(chart, concern, axis):
    rows = build_first_reading(chart, concern, axis)
    assert [r['stage'] for r in rows] == ['0', '1', '2', '2.5', '3']
    assert all(guard.check(r['html'])[0] for r in rows)
    assert all(guard.check(r['source'])[0] for r in rows)
    assert all(len(_plain(r['html'])) < 470 for r in rows)
    assert all(r['label'] and r['question'] for r in rows)
    assert all('맞지 않' in r['no'] for r in rows)
    # 같은 입력이면 같은 답이오. 무작위가 섞이면 캐시가 거짓말을 하오.
    assert rows == build_first_reading(chart, concern, axis)


def test_시각을_모르면_기둥을_지어내지_않는다(chart):
    rows = build_first_reading(chart, 'money')
    assert '세 기둥' in rows[0]['source']
    joined = ''.join(r['html'] + r['source'] for r in rows)
    assert '여덟' not in joined and '8글자' not in joined


def test_시각을_알면_네_기둥으로_센다(timed):
    assert '네 기둥' in build_first_reading(timed, 'money')[0]['source']


# ── 가름 ────────────────────────────────────────────────
def test_판정은_무엇_하나를_지운다():
    """「A가 아니오. B요.」 — 아무것도 안 지우는 말은 바넘이오."""
    for (concern, key), cell in CELL.items():
        assert cell['no'].endswith('아니오.'), (concern, key)
        assert '?' not in cell['no'] + cell['yes'], (concern, key)
        assert '<b>' in cell['yes'], (concern, key)


def test_모든_마디에_반증_조건과_확인_기준이_선다(chart):
    rows = build_first_reading(chart, 'work')
    assert '틀리는 자리' in rows[1]['html']
    assert '맞았는지 재는 법' in rows[2]['html']
    # 시키는 일은 **한 컷에 하나**요.
    assert rows[2]['html'].count('first-reading-action') == 1


@pytest.mark.parametrize('concern', CONCERNS)
def test_판정에_센_값이_함께_선다(chart, concern):
    rows = build_first_reading(chart, concern)
    body = _plain(rows[0]['html'])
    assert re.search(r'\d', body), body
    assert re.search(r'\d', _plain(rows[1]['html']))


def test_고민이_바뀌면_판정도_바뀐다(chart):
    """여섯 고민이 글자 그대로 같으면 그건 고민을 안 본 것이오."""
    heads = {c: _plain(build_first_reading(chart, c)[0]['html'])
             for c in CONCERNS}
    assert len(set(heads.values())) == len(CONCERNS)
    acts = {c: _plain(build_first_reading(chart, c)[2]['html'])
            for c in CONCERNS}
    assert len(set(acts.values())) == len(CONCERNS)


@pytest.mark.parametrize('concern', CONCERNS)
def test_사람이_바뀌면_판정이_바뀐다(chart, timed, concern):
    """여덟 글자가 다른데 같은 글이 나가면 그건 명식을 안 본 것이오."""
    assert (_plain(build_first_reading(chart, concern)[0]['html'])
            != _plain(build_first_reading(timed, concern)[0]['html']))


# ── 고른 답이 닿는가 ────────────────────────────────────
def test_고른_답이_첫_해석에_닿는다(timed):
    """v2 는 이 인자가 아예 없었소 — 다섯을 묻고 한 개도 안 봤소."""
    rows = build_first_reading(timed, 'money',
                               topic={'choice': 'pay', 'choice2': 'people',
                                      'choice3': 'keep'})
    head = _plain(rows[0]['html'])
    assert '월급' in head and '사람에게' in head
    assert '번 돈을 지키는 방법' in _plain(rows[-1]['html'])


def test_고른_답이_판정_차례를_바꾼다():
    """같은 사주라도 무엇이 샌다 했는지에 따라 먼저 보는 자리가 다르오.

    ★ 걸린 짜임이 하나뿐인 사람은 안 바뀌오 — 그게 맞소. 없는 것을
      끌어다 쓰지 않으니까. 그래서 **사람을 여럿 놓고** 봅니다.
    """
    import random
    random.seed(3)
    moved = 0
    for _ in range(40):
        f = build_features(
            build_chart(random.randint(1965, 2006), random.randint(1, 12),
                        random.randint(1, 28), random.randint(0, 23),
                        random.randint(0, 59), random.choice(['M', 'F'])),
            as_of=date(2026, 9, 21))
        keys = {fr._candidates(f, 'money',
                               {'choice': 'pay', 'choice2': leak})[0]
                for leak in ('people', 'spread', 'stay')}
        moved += len(keys) > 1
    assert moved >= 5, moved


def test_목록에_없는_답은_안_싣는다(timed):
    rows = build_first_reading(timed, 'money', topic={'choice': '없는것'})
    assert '없는것' not in _plain(rows[0]['html'])


# ── 두 번 「아니오」 ─────────────────────────────────────
def test_두_번_아니오면_판정을_뒤집는다(timed):
    before = build_first_reading(timed, 'love')
    after = build_first_reading(timed, 'love', misses=2)
    assert before[0]['statement_id'] != after[0]['statement_id']
    # 포기 문구로 바꾸던 자리요. 둘째 **후보**가 서야 하오.
    assert before[0]['statement_id'].split(':')[2] \
        != after[0]['statement_id'].split(':')[2]
    assert '다른 글자로' in after[0]['html']
    assert '둘째' in after[0]['source']
    assert all(k in CELL for k in
               [(('love'), after[0]['statement_id'].split(':')[2])])


# ── 표가 빈칸 없이 찼는가 ───────────────────────────────
def test_표에_빈칸이_없다():
    from engine import topic as topic_mod, why as why_mod
    for concern, keys in RANK.items():
        for key in keys:
            assert (concern, key) in CELL, (concern, key)
        for base in ('base_weak', 'base_strong'):
            assert (concern, base) in CELL, (concern, base)
    for (concern, key), cell in CELL.items():
        assert key in FACTS and key in WRONG and key in fr.AXIS_OF, key
        for fact in FACTS[key]:
            assert fact in topic_mod._FACTS, fact
        assert fr.AXIS_OF[key] in why_mod.AXIS, key
        assert all(cell[field] for field in
                   ('no', 'yes', 'why', 'act', 'check', 'next'))
    for concern in RANK:
        assert concern in fr.GUARD_LINE


def test_차례표가_짜임_이름을_지어내지_않는다():
    from engine import pattern
    known = {p['key'] for p in pattern.all_patterns()}
    for concern, keys in RANK.items():
        for key in keys:
            assert key in known, (concern, key)
            at = next(p['at'] for p in pattern.all_patterns()
                      if p['key'] == key)
            assert concern in at, (concern, key)


def test_짜임_이름은_값을_치른_자리의_몫이다():
    """무료 가름에 「군겁쟁재」 같은 이름을 펴지 않소."""
    from engine import pattern
    # 「도화」 「역마」 처럼 두 글자로 쓰이는 신살 이름은 이 집의 보통
    # 말이오. 막는 것은 **펴 놓고 읊는 격국 이름**이오.
    names = {n for n in (p['name'].split('(')[0].strip()
                         for p in pattern.all_patterns())
             if len(n) >= 3 and ' ' not in n}
    written = ' '.join(v for cell in CELL.values() for v in cell.values())
    for name in names:
        assert name not in written, name
    # 값을 치른 자리의 글을 **그 짜임에서** 그대로 옮기지도 않소.
    # (「…을 보는 글자가 겉에 안…」 처럼 이 집이 두루 쓰는 말투는
    #  베낀 것이 아니오. 그래서 같은 열쇠끼리만 댑니다.)
    says = {p['key']: PLAIN.sub('', p['say'])
            for p in pattern.all_patterns() if isinstance(p['say'], str)}
    for (concern, key), cell in CELL.items():
        body = says.get(key, '')
        mine = ' '.join(cell.values())
        for i in range(0, max(0, len(body) - 20)):
            assert body[i:i + 20] not in mine, (concern, key, body[i:i + 20])


# ── 안전 ────────────────────────────────────────────────
def test_이름과_넉_자는_그려지지_않고_셈도_안_바뀐다(chart):
    before = chart.to_dict()
    rows = build_first_reading(chart, 'love', 'INFP',
                               name='<img src=x onerror=alert(1)>')
    assert '<img' not in rows[0]['html'] and '&lt;img' in rows[0]['html']
    assert 'INFP' in rows[3]['html']
    assert chart.to_dict() == before


def test_모르는_고민은_지어내지_않고_거절한다(chart):
    from engine.bank import BankError
    with pytest.raises(BankError):
        build_first_reading(chart, '없는고민')


def test_짜임이_안_걸려도_얼굴로_가른다(chart):
    """조건이 안 맞으면 짜임을 안 내오. 그때도 판정은 서야 하오."""
    rows = build_first_reading(chart, 'real_estate')
    assert rows[0]['statement_id'].split(':')[2].startswith('base_')
    assert '전문가' in _plain(rows[1]['html'])


def test_쏠림_한_판정이_절반을_넘지_않는다():
    """스물한 벌짜리 글 세 벌로 돌던 자리요. 이제는 갈려야 하오."""
    import random
    random.seed(11)
    for concern in CONCERNS:
        seen = {}
        for _ in range(60):
            f = build_features(
                build_chart(random.randint(1965, 2006), random.randint(1, 12),
                            random.randint(1, 28), random.randint(0, 23),
                            random.randint(0, 59), random.choice(['M', 'F'])),
                as_of=date(2026, 9, 21))
            key = fr._candidates(f, concern, None)[0]
            seen[key] = seen.get(key, 0) + 1
        assert len(seen) >= 4, (concern, seen)
        assert max(seen.values()) <= 30, (concern, seen)
