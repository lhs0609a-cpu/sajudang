# -*- coding: utf-8 -*-
"""
값값 점수 — **치른 값이 아깝지 않은가.**

★ 손님이 시킨 것 (2026-09-07)

  "실제 그 돈 써도 돈값한다, 진짜 감동이다, 이거 돈 써도 하나도
   안 아깝다, 오히려 돈 번 느낌이다 들 정도 퀄리티인지 종합점수
   파악해서 관리자페이지에 실시간 연동해놓고, 100점만점으로."

★ 이 검사가 지키는 것

  점수 자체가 아닙니다 — 점수는 오르내려야 합니다. 지키는 것은
  **점수가 거짓말을 안 하는가** 입니다.

    · 여섯 축이 다 서는가 (하나가 조용히 빠지면 총점이 부풀어 오릅니다)
    · 무게 합이 100인가
    · 잰 값이 실제 글에서 나오는가 (표본을 못 지으면 0점이라고 말하는가)
    · 등급 문턱이 겹치거나 비지 않는가

★ 왜 최저점을 안 거는가

  「70점 아래면 실패」로 두면 점수를 올리려고 **문장을 지우게** 됩니다.
  뜬 말을 줄이려고 명리 용어를 빼면 근거가 사라집니다. 이 점수는
  관문이 아니라 **거울**입니다. 관문은 engine-check 가 봅니다.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import worth  # noqa: E402

AXES = ("own", "ground", "sting", "worth", "read", "pull")


@pytest.fixture(scope="module")
def got():
    worth.clear()
    return worth.score()


def test_the_weights_add_up_to_a_hundred():
    """무게 합이 100이라야 총점이 100점 만점이오."""
    assert sum(worth.WEIGHT.values()) == 100, worth.WEIGHT


def test_every_axis_has_a_name_and_a_question():
    """이름과 «무엇을 보는가» 가 없으면 주인이 못 고칩니다."""
    for k in AXES:
        assert k in worth.WEIGHT, k
        assert worth.NAMES.get(k), k
        assert worth.ASK.get(k), k


def test_all_six_axes_stand(got):
    """
    ★ 하나가 조용히 빠지면 총점이 **부풀어 오릅니다.**
      축이 죽어도 나머지로 평균이 나므로 화면에는 멀쩡해 보입니다.
    """
    keys = [a["key"] for a in got["axes"]]
    assert keys == list(AXES), keys
    for a in got["axes"]:
        assert 0 <= a["score"] <= 100, a
        assert a["weight"] == worth.WEIGHT[a["key"]]


def test_the_total_is_the_weighted_average(got):
    want = sum(a["score"] * a["weight"] for a in got["axes"]) / 100
    assert abs(got["total"] - round(want)) <= 1, (got["total"], want)
    assert 0 <= got["total"] <= 100


def test_the_grade_matches_the_score(got):
    """등급이 점수와 어긋나면 주인이 숫자를 안 믿습니다."""
    for cut, grade, _say in worth.GRADE:
        if got["total"] >= cut:
            assert got["grade"] == grade, (got["total"], got["grade"])
            break


def test_grade_bands_cover_every_score():
    """문턱이 겹치거나 비면 어떤 점수는 등급이 없습니다."""
    cuts = [c for c, _g, _s in worth.GRADE]
    assert cuts == sorted(cuts, reverse=True), cuts
    assert cuts[-1] == 0, "0점에도 할 말이 있어야 하오"
    assert len(set(cuts)) == len(cuts), "문턱이 겹치오"
    for n in (0, 1, 54, 55, 69, 70, 79, 80, 89, 90, 100):
        assert any(n >= c for c in cuts), n


def test_it_measures_real_text_not_a_guess(got):
    """
    ★ 지어낸 점수가 아닙니다 — 표본을 **진짜로 돌려** 셉니다.
      그래서 잰 값(퍼센트·상관)이 각 축에 함께 실려야 합니다.
    """
    for a in got["axes"]:
        assert a.get("parts") or a.get("why"), (
            "%s 축이 무엇을 재서 그 점수인지 말하지 않소" % a["name"])


def test_it_says_which_two_to_fix_first(got):
    """가장 약한 둘을 짚어 줘야 주인이 어디부터 볼지 압니다."""
    assert len(got["weakest"]) == 2
    lows = sorted(a["score"] for a in got["axes"])[:2]
    assert sorted(w["score"] for w in got["weakest"]) == lows


def test_clearing_makes_it_measure_again():
    """
    고치고 새로 고쳤는데 옛 점수가 나오면 도구를 안 믿게 됩니다.
    """
    worth.clear()
    a = worth.score()
    b = worth.score()
    assert a["total"] == b["total"], "같은 글인데 점수가 흔들리오"


def test_the_admin_route_exists():
    """관리자 화면이 부를 자리가 실제로 있는가."""
    import routers.admin as adm
    paths = {r.path for r in adm.router.routes}
    assert "/v1/admin/worth" in paths, sorted(paths)
