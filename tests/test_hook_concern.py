# -*- coding: utf-8 -*-
"""
훅 다섯 단이 **고른 고민을 보는가.**

★ 손님이 짚은 것 (2026-09-05)

  "지금 사람에 대한 사주를 묻고 있는데 전부 답변이 다 똑같아,
   사랑도 돈도."

★ 무엇이 어긋났나

  앞의 셋은 갈리는데 **3단 「이름」이 안 갈렸습니다** — 어느 칸을
  골라도 「말은 했는데 안 한 일」 하나였습니다.

      넉 자를 적으면    갈래 [6, 6, 6, 1, 1]
      넉 자를 안 적으면  갈래 [6, 6, 6, 6, 1]

  하필 거기가 **끝**입니다. 기억은 마지막이 지배하는데(peak-end) 그
  마지막이 여섯 칸에서 하나였습니다. 앞에서 아무리 갈라도 손님에게
  남는 한 줄이 같으면 「다 똑같다」가 맞습니다.

★ 이름 자체는 안 바꿉니다

  `NAME2[모자란 오행][흐름]` 스물다섯은 **짜임의 이름**이라 고민이
  바꿀 것이 아닙니다. 바꾸는 것은 그 이름이 **물으신 자리에서 어떤
  얼굴로 나오는가** 입니다 (`NAME_AT[흐름][고민]` 서른 줄).

★ 2.5단은 갈리지 않아도 됩니다

  그 단이 보는 것은 고민이 아니라 **넉 자와 여덟 글자의 어긋남**
  입니다. 넉 자를 안 적은 사람에게는 고민으로 읽는 단이 대신 서니,
  그때는 다섯 단이 다 갈립니다.
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import guard                              # noqa: E402
from engine.bank import bank, build_hook              # noqa: E402
from engine.calendar import build_chart               # noqa: E402
from engine.features import build_features            # noqa: E402

CONCERNS = ("money", "work", "love", "people", "dir", "health")
NAME_STAGE = "3"          # 이름 — 훅의 끝


def _flat(h):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h or "")).strip()


@pytest.fixture(scope="module")
def people():
    return [build_features(build_chart(*b, city="서울"), as_of=date.today())
            for b in ((1993, 11, 25, 15, 55, "M"),
                      (1988, 3, 2, 7, 10, "F"),
                      (2001, 7, 19, 22, 40, "M"))]


def _by_concern(f, axis4):
    return {c: build_hook(f, c, axis4, name="", you="그대") for c in CONCERNS}


def test_이름_단이_고민마다_갈린다(people):
    """
    ★ 이게 이번에 어긋났던 자리입니다. 훅의 **끝**이라 손님에게 가장
      오래 남는 한 줄인데, 여섯 칸에서 하나였습니다.
    """
    for f in people:
        for axis4 in ("INTJ", None):
            segs = _by_concern(f, axis4)
            name = {}
            for c in CONCERNS:
                got = [s for s in segs[c] if s.get("stage") == NAME_STAGE]
                assert got, "이름 단이 없소"
                name[c] = _flat(got[0]["html"])
            assert len(set(name.values())) == len(CONCERNS), (
                "이름이 %d가지뿐이오 (넉 자 %s)"
                % (len(set(name.values())), axis4))


def test_넉_자를_안_적으면_다섯_단이_다_갈린다(people):
    for f in people:
        segs = _by_concern(f, None)
        n = len(segs["work"])
        for i in range(n):
            kinds = len({_flat(segs[c][i]["html"]) for c in CONCERNS})
            assert kinds == len(CONCERNS), "%d단이 %d가지요" % (i, kinds)


def test_고민이_훅의_절반_넘게_바꾼다(people):
    """
    한두 줄만 갈리고 나머지가 같으면 손님 눈에는 여전히 「다 똑같다」요.
    """
    for f in people:
        segs = _by_concern(f, "INTJ")
        n = len(segs["work"])
        tot = dif = 0
        for i in range(n):
            ln = len(_flat(segs["work"][i]["html"]))
            tot += ln
            if len({_flat(segs[c][i]["html"]) for c in CONCERNS}) > 1:
                dif += ln
        assert dif / tot >= 0.5, "고민이 바꾸는 몫이 %.0f%% 뿐이오" % (100 * dif / tot)


def test_이름_표가_흐름_다섯과_고민_여섯을_다_덮는다():
    """빈칸을 두지 않습니다 — 없으면 그 사람만 조용히 안 갈립니다."""
    at = bank().get("NAME_AT") or {}
    flows = set(bank()["NAME_FLOW"])
    assert set(at) == flows, "흐름이 빠졌소: %s" % (flows - set(at))
    for flow, row in at.items():
        assert set(row) == set(CONCERNS), (flow, set(CONCERNS) - set(row))
        for c, line in row.items():
            assert len(line) >= 20, (flow, c, line)


def test_새_말도_가드를_지난다(people):
    for f in people:
        for c in CONCERNS:
            for s in build_hook(f, c, None, name="", you="그대"):
                ok, hits = guard.check(_flat(s["html"]))
                assert ok, (c, hits)
