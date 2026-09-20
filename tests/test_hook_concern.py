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


def _sents(t):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s*", t) if s.strip()]


def test_고민이_훅의_절반_넘게_바꾼다(people):
    """
    ★ 이 검사가 **약해서 손님이 먼저 짚었습니다** (2026-09-19).

      손님이 말했습니다 — 「지금 훅이 너무 다 똑같아. 일이랑 사랑이랑
      다 똑같아.」 그런데 이 검사는 통과하고 있었습니다.

      까닭은 세는 단위였습니다. 여기서 세던 것은 「이 마디가 갈리는가」
      였고, 한 글자만 달라도 그 마디 **전체**가 갈린 몫으로 들어갔습니다.
      다섯 마디가 다 한 줄씩 갈리니 100%가 나왔습니다.

      실제로 글자로 재 보니 훅 10만 7천 자 가운데 **6만 2천 자(58%)**
      가 여섯 고민에 글자 그대로 같았습니다.

      손님이 읽는 것은 마디가 아니라 **글자**입니다. 그러니 글자를
      셉니다. 자세한 표는 `tools/hook_concern.py` 가 찍습니다.

    ★ 0%를 노리지 않습니다. 이 집의 뼈대(「세어 보시오」 「여태 그래
      왔소」)와 명식에서 나온 값(일간 · 계절 · 대운 나이)은 고민이
      바꿀 자리가 아닙니다.
    """
    for f in people:
        for axis4 in ("INTJ", None):
            segs = _by_concern(f, axis4)
            same = tot = 0
            for i in range(len(segs["work"])):
                ss = [_sents(_flat(segs[c][i]["html"])) for c in CONCERNS]
                for s in ss[0]:
                    tot += len(s)
                    if all(s in o for o in ss[1:]):
                        same += len(s)
            assert same / tot <= 0.5, (
                "훅의 %.0f%% 가 여섯 고민에 글자 그대로 같소 (넉 자 %s)"
                % (100 * same / tot, axis4))


def test_손님이_누르는_자리도_갈린다(people):
    """
    ★ 묻는 말이 90.4% 고정이었습니다 (2026-09-19).

      「이 말은 어떻소?」 「이제 알겠소?」 — 무엇을 물었든 같았습니다.
      이 줄은 손님이 **그렇소/아니오를 누르기 직전**에 읽는 한 마디라,
      여기가 고정이면 앞에서 아무리 갈라도 누르는 순간 되돌아갑니다.
    """
    for f in people:
        segs = _by_concern(f, "INTJ")
        for fld in ("question", "yes", "no"):
            same = tot = 0
            for i in range(len(segs["work"])):
                vals = [_flat(segs[c][i].get(fld)) for c in CONCERNS]
                tot += len(vals[0])
                if len(set(vals)) == 1:
                    same += len(vals[0])
            assert same / tot <= 0.25, (
                "%s 의 %.0f%% 가 여섯 고민에 같소" % (fld, 100 * same / tot))


def test_순서_상자_세_칸이_다_고민을_본다(people):
    """
    ★ 손님이 짚은 바로 그 자리입니다 (2026-09-19).

      2단 순서 상자는 훅에서 **가장 크게 보이는** 것입니다 — 굵은
      세 칸 목록이오. 그런데 첫 칸만 `IGNITE[십신][고민]` 이고
      둘째는 `FLOW[흐름]`, 셋째는 `RESULT[모자란 오행]` 이라 무엇을
      물었든 같았습니다.

          일   :  일 벌임    → 붙들기 → 멈추지 못함
          사랑 :  다 걸어 봄 → 붙들기 → 멈추지 못함     ← 2/3 같음

      가장 크게 보이는 자리가 3분의 2 같으면, 본문이 아무리 갈려도
      손님 눈에는 같은 화면입니다.
    """
    for f in people:
        segs = _by_concern(f, "INTJ")
        boxes = {}
        for c in CONCERNS:
            html = [s for s in segs[c] if s.get("stage") == "2"][0]["html"]
            after = html[html.index('<div class="seq">'):]
            boxes[c] = re.findall(r"<span>(.*?)</span>", after)[:3]
            assert len(boxes[c]) == 3, boxes[c]
        for i in range(3):
            got = {boxes[c][i] for c in CONCERNS}
            assert len(got) >= 5, (
                "순서 %d째 칸이 %d가지뿐이오: %s" % (i + 1, len(got), got))


def test_순서_상자와_그_아래_줄이_어긋나지_않는다(people):
    """
    ★ 상자를 고민축으로 가른 날 같이 생긴 자리입니다.

      `HOOK_AT["2"]` 가 순서 세 칸을 **다시 읊고** 있었습니다. 상자가
      고정이던 때는 그게 번역이었지만, 상자가 고민마다 갈리고 나니
      같은 자리를 두 번 말하면서 서로 다른 말을 했습니다 — 상자는
      「일 벌임 · 못 넘기기 · 못 쉼」 인데 그 줄은 「맡고 → 쏟고 →
      못 끝냄」 이었습니다.
    """
    from engine import topic as topic_mod
    for c in CONCERNS:
        line = topic_mod.hook_line(c, "2")
        assert "→" not in line, (
            "2단 줄이 순서를 다시 읊고 있소 — 상자와 어긋나오: %s" % line)


def test_표가_빈칸_없이_찼다():
    """빈칸을 두면 **그 사람만 조용히 안 갈립니다.**"""
    B = bank()
    flows = set(B["NAME_FLOW"])
    els = set(B["RESULT"])
    for name, keys in (("FLOW_AT", flows), ("RESULT_AT", els)):
        tbl = B.get(name) or {}
        assert set(tbl) == keys, (name, keys - set(tbl))
        for k, row in tbl.items():
            assert set(row) == set(CONCERNS), (name, k, set(CONCERNS) - set(row))
            ks = [v["k"] for v in row.values()]
            assert len(set(ks)) == len(ks), (
                "%s[%s] 의 상자 이름이 겹치오: %s" % (name, k, ks))
    for name in ("BLADE_LIVED", "MYTH_LIVED", "AXIS_LIVED",
                 "NAME_NOT", "CAX_LIVED"):
        tbl = B.get(name) or {}
        assert set(tbl) == set(CONCERNS), (name, set(CONCERNS) - set(tbl))
        assert len(set(tbl.values())) == len(CONCERNS), "%s 가 겹치오" % name
    blame = B.get("BLAME_AT") or {}
    assert set(blame) == set(CONCERNS)
    for c, row in blame.items():
        assert set(row) == flows, (c, flows - set(row))
    post = B.get("NAME_POST_AT") or {}
    assert set(post) == set(CONCERNS)
    for c, row in post.items():
        assert set(row) == set(B["NAME_POST"]), (c, set(row))
    relief = B.get("SEQ_RELIEF_AT") or {}
    assert set(relief) == set(B["SEQ_RELIEF"])
    for k, row in relief.items():
        assert set(row) == set(CONCERNS), (k, set(CONCERNS) - set(row))
    flat = [v for row in relief.values() for v in row.values()]
    assert len(set(flat)) == len(flat), "2단 위로 줄이 겹치오"


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
