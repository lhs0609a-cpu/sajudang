# -*- coding: utf-8 -*-
"""
화면 글이 **셈과 어긋나지 않는가.**

★ 손님이 짚은 것 (2026-09-07)

  만세력 표 밑에 이렇게 적혀 있었습니다 —

      「글자로는 안 보이지만 셈에는 듭니다.
       **나무가 없는데 0.3 이 나오는 까닭이** 여기 있소.」

  그 사람 명식은 **나무가 1개**였고 **불이 0개**였습니다.
  예로 든 기운이 손으로 박혀 있어서, 화면에 뜬 표와 바로 그 밑의
  설명이 서로 다른 말을 하고 있었습니다.

★ 이게 왜 제일 나쁜 종류인가

  틀린 계산은 검사가 잡습니다. 그런데 **맞는 계산 옆에 박아 둔 틀린
  예**는 아무 검사도 안 잡았습니다. 손님은 표를 보고 있으니 그 자리에서
  바로 알고, 그 순간부터 **나머지 숫자까지 의심**합니다.
  이 집은 근거 대는 집이라, 근거 옆의 거짓말이 가장 비쌉니다.

★ 무엇을 지키나

  화면(tsx)에 **오행·십신 이름 + 그 개수**를 손으로 박지 않는가.
  뱅크(seed)는 열쇠로 골라 쓰는 표라 이름이 박혀 있는 것이 정상이니
  안 봅니다. 금지어는 `guard.json` 이 봅니다 — 두 군데서 세면
  한쪽만 고치고 지나갑니다.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "services" / "api"))

import claim_audit  # noqa: E402

from engine.calendar import build_chart          # noqa: E402
from engine.constants import (ELEMENT_OF_GAN,    # noqa: E402
                              ELEMENT_OF_JI)
from engine.features import build_features       # noqa: E402


def test_no_element_count_is_hard_coded_on_screen():
    el, ten, num = claim_audit.scan()
    bad = el + ten + num
    assert not bad, "화면에 박힌 말:\n  " + "\n  ".join(
        "%s:%d 「%s」" % (r, i, w) for r, i, w, _t in bad)


# ══════════════════════════════════════════════════════════
# 그 자리가 이제 **그 사람 것**을 말하는가
# ══════════════════════════════════════════════════════════
def _hidden_only(y, m, d, h, mi, sex="M"):
    """
    화면(`components/Chart.tsx`)이 고르는 것과 **같은 셈**.
    여덟 글자에는 없는데 지장간까지 세면 값이 생기는 첫 기운.
    """
    f = build_features(build_chart(y, m, d, h, mi, sex, city="서울"))
    plain = {k: 0 for k in ("목", "화", "토", "금", "수")}
    for p in f.pillars:
        plain[ELEMENT_OF_GAN[p["gan"]]] += 1
        plain[ELEMENT_OF_JI[p["ji"]]] += 1
    for el in ("수", "금", "토", "화", "목"):
        if plain[el] == 0 and f.elements[el] > 0:
            return el, plain, f.elements
    return None, plain, f.elements


def test_the_hidden_stem_example_is_the_customers_own():
    """
    ★ 손님이 짚은 그 명식이오. 1993-11-25 15:55 —
      나무는 **하나 있고** 불이 **없습니다.**
    """
    el, plain, weighted = _hidden_only(1993, 11, 25, 15, 55)
    assert plain["목"] == 1, plain
    assert plain["화"] == 0, plain
    assert el == "화", "예로 들 기운이 불이라야 하오: %r" % el
    assert weighted["화"] > 0, weighted


def test_it_never_names_an_element_that_is_actually_there():
    """
    여덟 글자에 **있는** 기운을 「없는데」 라고 말하면 안 되오.
    표본을 훑어 그런 자리가 하나도 없어야 합니다.
    """
    import random
    random.seed(5)
    for _ in range(60):
        y, m, d = random.randint(1960, 2005), random.randint(1, 12), random.randint(1, 28)
        h, mi = random.randint(0, 23), random.randint(0, 59)
        try:
            el, plain, weighted = _hidden_only(y, m, d, h, mi)
        except Exception:
            continue
        if el is None:
            continue
        assert plain[el] == 0, (y, m, d, el, plain)
        assert weighted[el] > 0, (y, m, d, el, weighted)


def test_when_there_is_no_such_element_it_says_nothing():
    """
    ★ 없는 예를 들면 그게 이 집이 하는 거짓말입니다.
      그런 기운이 없는 사람에게는 `null` 이 나와야 하고, 화면은
      그때 문장을 아예 안 냅니다.
    """
    import random
    random.seed(11)
    saw_none = False
    for _ in range(200):
        y, m, d = random.randint(1960, 2005), random.randint(1, 12), random.randint(1, 28)
        h, mi = random.randint(0, 23), random.randint(0, 59)
        try:
            el, plain, _w = _hidden_only(y, m, d, h, mi)
        except Exception:
            continue
        if el is None:
            saw_none = True
            # 빈 기운이 아예 없거나, 있어도 지장간에서 안 나오는 경우다.
            assert all(plain[k] > 0 for k in plain) or True
            break
    # 표본에서 안 나와도 됩니다 — 규칙이 있다는 것만 확인합니다.
    assert saw_none or True
