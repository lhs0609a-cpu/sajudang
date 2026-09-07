# -*- coding: utf-8 -*-
"""
릴레이가 **물으신 자리를 보는 사람**을 부르는가.

★ 손님이 짚은 것 (2026-09-07)

  "캐릭터도 그 캐릭 전문성에 맞게끔 상담해야하고 이거 계속 문제야
   무조건 고쳐."

★ 무엇이 어긋났나

  재보니 삼거리 노파(방향 담당·priority 95)가 **여섯 고민 전부에서
  1순위 최다**였습니다. 돈을 물어도 사랑을 물어도 몸을 물어도 노파가
  먼저 섰습니다. 까닭은 둘이었습니다 —

  ① 고민 게이트 규칙이 얇았습니다. 사람은 화경 하나, 사랑은 월하
     하나뿐이라, 그 조건이 안 걸리면 담당이 **후보에조차** 없었습니다.
     (없는 사람은 재순위로 못 올립니다.)
  ② 고민 가중치가 0.2라 우선순위 격차(95 대 70)를 못 이겼습니다.

  게이트 규칙 열다섯을 더하고 가중치를 0.45로 올렸습니다.
  자세한 셈은 `engine/relay.py` 의 DEFAULT_CONCERN_W 머리말에 있습니다.

★ 그래도 잠그지는 않습니다
  고민으로 문을 닫으면 스무 명이 여섯 통으로 갈라져 릴레이의 뜻이
  죽습니다. 가중만 겁니다 — 그래서 문턱을 100%로 두지 않습니다.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import relay                                  # noqa: E402
from engine.calendar import build_chart                   # noqa: E402
from engine.features import build_features                # noqa: E402

CONCERNS = ("money", "work", "love", "people", "dir", "health")

# 그 고민을 실제로 보는 사람 — seed/lenses.json 의 `concerns` 가 정합니다.
_raw = json.loads((ROOT / "seed" / "lenses.json").read_text("utf-8"))
_lenses = _raw["lenses"] if isinstance(_raw, dict) and "lenses" in _raw else _raw
_lenses = _lenses if isinstance(_lenses, list) else list(_lenses.values())
COVERS = {l["id"]: set(l.get("concerns") or []) for l in _lenses}


@pytest.fixture(scope="module")
def people():
    random.seed(11)
    out = []
    while len(out) < 150:
        y = random.randint(1965, 2005)
        m, d = random.randint(1, 12), random.randint(1, 28)
        h, mi = random.randint(0, 23), random.randint(0, 59)
        sx = random.choice("MF")
        try:
            out.append(build_features(
                build_chart(y, m, d, h, mi, sx, hour_known=True, city="서울")))
        except Exception:
            pass
    return out


def _ranked(f, concern):
    return [x["lens_id"]
            for x in relay.rerank(relay.evaluate(f, concern=concern),
                                  None, concern)]


def test_every_concern_has_more_than_one_gated_rule():
    """
    ★ 담당이 후보에 못 들면 재순위로는 못 올립니다.
      한 규칙에만 매달리면 그 조건이 안 걸리는 사람에게 담당이 사라집니다.
    """
    got = {}
    for r in relay.rules():
        gate = r.get("when_concern")
        if not gate:
            continue
        if gate in COVERS.get(r["lens_id"], ()):
            got.setdefault(gate, set()).add(r["lens_id"])
    for c in CONCERNS:
        assert len(got.get(c, ())) >= 2, (
            "%s 를 물었을 때 세울 수 있는 담당이 %s 뿐이오"
            % (c, sorted(got.get(c, ())) or "없음"))


@pytest.mark.parametrize("concern", CONCERNS)
def test_the_asked_seat_is_usually_first(concern, people):
    """물으신 자리를 보는 사람이 1순위로 선다 — 늘은 아니고, 대체로."""
    hit = sum(1 for f in people
              if (r := _ranked(f, concern)) and concern in COVERS.get(r[0], ()))
    rate = hit / len(people)
    assert rate >= 0.60, "%s · 담당이 1순위인 비율 %.0f%%" % (concern, 100 * rate)


@pytest.mark.parametrize("concern", CONCERNS)
def test_the_asked_seat_is_almost_always_in_the_top_three(concern, people):
    hit = sum(1 for f in people
              if any(concern in COVERS.get(i, ())
                     for i in _ranked(f, concern)[:3]))
    rate = hit / len(people)
    assert rate >= 0.70, "%s · 담당이 상위 3에 드는 비율 %.0f%%" % (
        concern, 100 * rate)


@pytest.mark.parametrize("concern", CONCERNS)
def test_the_most_common_first_pick_belongs_to_the_asked_seat(concern, people):
    """
    ★ 이 검사가 손님이 짚은 그 자리입니다.
      전에는 여섯 칸 **전부** 삼거리 노파(방향 담당)가 1순위 최다였습니다.
    """
    import collections
    cnt = collections.Counter()
    for f in people:
        r = _ranked(f, concern)
        if r:
            cnt[r[0]] += 1
    top = cnt.most_common(1)[0][0]
    assert concern in COVERS.get(top, ()), (
        "%s 를 물었는데 1순위 최다가 %s — 그 자리를 안 보는 사람이오"
        % (concern, top))


def test_no_concern_locks_the_relay_to_a_single_face(people):
    """
    가중만 겁니다 — 잠그면 스무 명이 여섯 통으로 갈라집니다.
    한 고민에서도 1순위가 여럿 나와야 합니다.
    """
    import collections
    for concern in CONCERNS:
        cnt = collections.Counter()
        for f in people:
            r = _ranked(f, concern)
            if r:
                cnt[r[0]] += 1
        assert len(cnt) >= 5, "%s · 1순위가 %d명뿐이오" % (concern, len(cnt))
        top_share = cnt.most_common(1)[0][1] / sum(cnt.values())
        assert top_share <= 0.70, "%s · 한 사람이 1순위를 %.0f%% 가져가오" % (
            concern, 100 * top_share)


def test_gated_rules_point_at_a_lens_that_actually_covers_it():
    """
    ★ 「돈을 물었으니 장사꾼」 은 근거가 아니라 장사입니다.
      게이트를 달았으면 그 사람이 실제로 그 자리를 봐야 합니다.
      — 다만 곁들이로 세우는 규칙은 있을 수 있어, 하나도 없으면 잡습니다.
    """
    for c in CONCERNS:
        gated = [r for r in relay.rules() if r.get("when_concern") == c]
        assert gated, "%s 에 게이트 규칙이 없소" % c
        covering = [r for r in gated if c in COVERS.get(r["lens_id"], ())]
        assert covering, "%s 게이트 규칙이 전부 남의 담당이오" % c


def test_gated_reasons_hide_the_rule():
    """근거는 보이되 규칙은 감춘다 — 연산자·문턱값이 새면 안 됩니다."""
    import re
    bad = re.compile(r"[<>≤≥]=?|\bin\b|==")
    for r in relay.rules():
        reason = r.get("reason") or ""
        assert not bad.search(reason), "%s 의 근거에 규칙이 샜소: %s" % (
            r["id"], reason)
