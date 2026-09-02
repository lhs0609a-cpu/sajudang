# -*- coding: utf-8 -*-
"""
화면이 내는 기운 수가 **손님이 센 것**과 맞는가.

★ 왜 지키나

  손님이 물었다 — "나 물 3개, 금 3개인데 왜 물 4개라고 하지?"

  세어 보니 엔진이 맞았다 (癸酉 癸亥 庚戌 壬午 → 물 4 · 금 2). 그런데
  화면은 「가장 적은 건 나무 0.3」 이라고 냈다. 손님은 여덟 글자를
  **직접 센다.** 세어 보면 나무는 0개인데 화면은 0.3 이라 한다.
  그러면 「이거 진짜 사주 맞나」 가 된다.

  0.3 은 지지 속 숨은 글자(지장간)까지 넣어 무게를 매긴 값이다.
  명리의 정식 셈이지만 **그 말을 안 하면 그냥 틀린 수**다.

  그래서 순서를 뒤집었다 — 셀 수 있는 수를 먼저, 무게를 매긴 수를
  까닭과 함께 그 다음에.
"""
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine.calendar import build_chart          # noqa: E402
from engine.constants import ELEMENT_OF_GAN, ELEMENT_OF_JI   # noqa: E402
from engine.features import build_features       # noqa: E402

CHART = ROOT / "apps" / "web" / "components" / "Chart.tsx"


def _plain(pillars):
    n = Counter()
    for p in pillars:
        n[ELEMENT_OF_GAN[p["gan"]]] += 1
        n[ELEMENT_OF_JI[p["ji"]]] += 1
    return n


def test_the_reported_case_is_right():
    """손님이 물어본 그 명식 — 물 4 · 금 2 가 맞다."""
    f = build_features(build_chart(1993, 11, 25, 13, 0, "M", True))
    plain = _plain([p if isinstance(p, dict) else p.__dict__
                    for p in f.pillars])
    assert plain["수"] == 4, plain
    assert plain["금"] == 2, plain
    # 무게를 매긴 값은 다르다 — 그래서 둘 다 보여 줘야 한다
    assert f.elements["금"] > plain["금"], "지장간이 안 들어갔다"
    assert f.elements["목"] > 0 and plain["목"] == 0, \
        "글자로는 없는데 무게로는 있는 자리 — 이게 설명이 필요한 까닭"


def test_screen_shows_a_countable_number_first():
    """손님이 직접 셀 수 있는 수를 먼저 낸다."""
    src = CHART.read_text(encoding="utf-8")
    assert "countPlain" in src, "글자 그대로 세는 자리가 없다"
    assert "여덟 글자로 세면" in src, "셀 수 있는 수를 안 낸다"
    i = src.index("여덟 글자로 세면")
    j = src.index("숨은 글자", i)
    assert i < j, "무게를 매긴 수가 먼저 나온다"


def test_screen_explains_the_hidden_stems():
    """0.3 이 어디서 왔는지 말하지 않으면 그냥 틀린 수다."""
    src = CHART.read_text(encoding="utf-8")
    for word in ("지장간", "숨은 글자", "무게"):
        assert word in src, "%s 를 안 밝힌다" % word


def test_client_table_matches_the_engine():
    """화면이 든 표가 서버와 다르면 두 곳이 다른 말을 한다."""
    src = CHART.read_text(encoding="utf-8")
    for gan, el in ELEMENT_OF_GAN.items():
        assert re.search(r"%s:\s*\"%s\"" % (gan, el), src), \
            "천간 %s 가 화면 표에 없거나 다르다" % gan
    for ji, el in ELEMENT_OF_JI.items():
        assert re.search(r"%s:\s*\"%s\"" % (ji, el), src), \
            "지지 %s 가 화면 표에 없거나 다르다" % ji
