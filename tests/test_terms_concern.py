# -*- coding: utf-8 -*-
"""
어려운 말 풀이가 **낱말을 쪼개지 않는가** · **물은 자리를 보는가.**

★ 손님이 짚은 것 (2026-09-07)

  "사랑에 대한건데 사랑에 대해서는 전혀 말하지 않아."

★ 무엇이 어긋났나

  ① 풀이가 **낱말 한가운데** 붙었습니다.
     화면에 이렇게 나갔습니다 —
        「상처를 덜 받으려 세운(그 해의 기운) 벽일 수 있소」
     그 단에 歲運 은 한 번도 안 나오는데 「이게 무슨 말인가 · 세운」
     상자까지 딸려 나갔습니다. 말뭉치의 「세운」은 **전부 세우다의
     활용형**이고, 歲運 은 근거 줄에서 갑자와 함께만 나옵니다.
     같은 꼴이 「내 편인데」 「꺾일지언정」 「대운수」 「천간합」
     「백호대살」 「정재격」에도 있었습니다.

  ② 풀이가 **고민을 안 봤습니다.**
     자평에서 배우자를 보는 글자는 남명이 재성, 여명이 관성입니다.
     그런데 사랑을 물은 사내에게 짝 보는 글자를
        재성 → "재물을 보는 자리" · 정재 → "달마다 들어오는 삯"
     으로 풀었습니다. 재보니 사랑 훅 1,321자에 사랑 낱말이 2.7회인데
     **돈 낱말이 4.9회**였고, 120명 중 103명(86%)에게 돈이 더 많았습니다.

★ 뜻을 감추지는 않습니다
  재성은 재물이면서 짝입니다. 물으신 쪽을 앞에 두고, 나머지는
  비유에서 함께 말합니다 (terms.PICTURE_AT).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import terms                              # noqa: E402
from engine.bank import blade_order, count_blade      # noqa: E402
from engine.calendar import build_chart               # noqa: E402
from engine.features import build_features            # noqa: E402


def _g(text, concern=None, sex=None):
    """풀이를 ⟪ ⟫ 로 바꿔 읽기 쉽게."""
    return re.sub(r'<i class="gl">\((.*?)\)</i>', r"⟪\1⟫",
                  terms.gloss(text, None, concern, sex))


# ══════════════════════════════════════════════════════════
# 1 · 낱말을 쪼개지 않는다
# ══════════════════════════════════════════════════════════
# (글, 풀이가 붙으면 안 되는 말)
SPLIT = [
    ("상처를 덜 받으려 세운 벽일 수 있소.", "세운"),
    ("스스로 세운 사람들이오.", "세운"),
    ("격을 세운 뒤라야 용신을 보오.", "세운"),
    ("명식을 세운다.", "세운"),
    ("철은 내 편인데 발밑이 비었소.", "편인"),
    ("내 편인지 겨루는 편인지가 늦게 밝혀지오.", "편인"),
    ("굽히는 법을 안 배운 글자라, 꺾일지언정 휘지 않소.", "일지"),
    ("대운수가 나이보다 크다는 뜻이오.", "대운"),
    ("일간이 乙과 묶이오(천간합).", "천간"),
    ("백호대살 白虎大殺", "백호"),
    ("정재격이오. 꾸준히 쌓아 서는 격이라.", "정재"),
    ("편재격이오.", "편재"),
    ("정관격이오.", "정관"),
    ("편관격이오.", "편관"),
    ("정인격이오.", "정인"),
    ("편인격이오.", "편인"),
    ("식신격이오.", "식신"),
    ("양인격이오.", "양인"),
]


@pytest.mark.parametrize("text,term", SPLIT)
def test_gloss_does_not_split_a_word(text, term):
    got = _g(text)
    assert "%s⟪" % term not in got, (
        "낱말 한가운데 풀이가 붙었습니다: %s" % got)


# 반대쪽 — 진짜 용어일 때는 **반드시** 풀어야 합니다.
KEEP = [
    ("세운이 그 판의 한 해요.", "세운"),
    ("대운 丙寅 · 세운 丙午", "세운"),
    ("편인이 둘이오.", "편인"),
    ("일지가 酉요.", "일지"),
    ("대운이 바뀌는 자리요.", "대운"),
    ("주도가 정재니 그 자리가 쌓는 데서 나오오.", "정재"),
    ("재성 하나 · 용신 불 · 대운 순행", "재성"),
]


@pytest.mark.parametrize("text,term", KEEP)
def test_gloss_still_explains_the_real_term(text, term):
    got = _g(text)
    assert "%s⟪" % term in got, "진짜 용어인데 안 풀었습니다: %s" % got


def test_every_only_particle_term_has_a_meaning():
    """조사 규칙을 건 말은 표에 있어야 합니다 — 없으면 조용히 안 풀립니다."""
    missing = [t for t in terms.ONLY_PARTICLE if t not in terms.MEANING]
    assert not missing, missing


# ══════════════════════════════════════════════════════════
# 2 · 물은 자리를 본다
# ══════════════════════════════════════════════════════════
def test_love_reads_the_spouse_star_as_a_partner_not_as_money():
    """남명 사랑에서 재성은 짝 보는 글자요 — 「쌓는 재물」이 아니오."""
    s = "재성이 하나요. 정재도 없소."
    money = _g(s, "money", "M")
    love = _g(s, "love", "M")
    assert "재물" in money and "짝" not in money
    assert "짝" in love, love
    assert "재성⟪짝을 보는 자리⟫" in love, love


def test_love_spouse_star_follows_the_sex():
    """여명은 관성이 짝이오. 남명의 관성은 짝이 아니오 — 규율이오."""
    s = "정관이 하나요."
    assert "짝" in _g(s, "love", "F")
    assert "짝" not in _g(s, "love", "M")


def test_picture_box_moves_with_the_gloss():
    """괄호와 비유가 **같은 층**이라야 합니다. 한쪽만 갈면 어긋납니다."""
    love = terms.picture_box({"정재"}, "love", "M")
    money = terms.picture_box({"정재"}, "money", "M")
    assert "짝" in love, love
    assert "짝" not in money, money


def test_meaning_at_only_overrides_terms_that_exist():
    for concern, by_sex in terms.MEANING_AT.items():
        for sex, table in by_sex.items():
            for t in table:
                assert t in terms.MEANING, "%s/%s 의 %r 이 표에 없소" % (
                    concern, sex, t)
    for concern, by_sex in terms.PICTURE_AT.items():
        for sex, table in by_sex.items():
            for t in table:
                assert t in terms.PICTURE, "%s/%s 의 %r 이 그림표에 없소" % (
                    concern, sex, t)


# ══════════════════════════════════════════════════════════
# 3 · 훅의 첫 줄도 물은 자리를 본다
# ══════════════════════════════════════════════════════════
def test_blade_order_leads_with_the_asked_seat():
    assert blade_order("love", "M")[:2] == ("정재", "편재")
    assert blade_order("love", "F")[:2] == ("정관", "편관")
    assert blade_order("work", "M")[:2] == ("정관", "편관")
    # 고민을 안 주면 정해 둔 차례 그대로.
    assert blade_order(None, "M") == blade_order("", "M")


def test_blade_order_keeps_all_ten_and_never_repeats():
    """앞자리만 옮깁니다 — 빼거나 겹치면 세는 값이 달라집니다."""
    for concern in (None, "love", "money", "work", "people", "dir", "health"):
        for sex in ("M", "F"):
            got = blade_order(concern, sex)
            assert len(got) == 10 and len(set(got)) == 10, (concern, sex, got)


def test_first_line_of_the_love_hook_talks_about_a_partner():
    """
    ★ 사랑을 물었는데 첫 문장이 「정재(쌓는 재물)도 없소」였습니다.
      물은 자리가 아니라 표 순서가 말하고 있었습니다.
    """
    f = build_features(build_chart(1988, 11, 2, 21, 40, "M", city="서울"))
    plain = lambda h: re.sub(r"<[^>]+>", "", h or "")
    love = plain(count_blade(f, "love"))
    money = plain(count_blade(f, "money"))
    assert "짝" in love, love
    assert "짝" not in money, money
    assert love != money
