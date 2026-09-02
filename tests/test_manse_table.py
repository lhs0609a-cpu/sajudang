# -*- coding: utf-8 -*-
"""
만세력처럼 보는 표가 실제 만세력과 맞는가.

★ 왜 이 표를 만들었나

  손님은 쓰던 만세력 앱과 대 본다. 우리 화면이 다른 모양이면 한 줄씩
  눈으로 옮겨 가며 견줘야 하고, 그러다 지친다. 만세력이 늘 그리는
  모양 그대로 두면 나란히 놓고 바로 견줄 수 있다.

★ 지장간을 보여 주는 까닭

  손님이 물었다 — "나무가 0개인데 왜 0.3이냐". 답이 지장간에 있다
  (亥 안에 甲). 말로만 하면 안 믿고, 표로 보이면 셀 수 있다.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine.constants import HIDDEN            # noqa: E402

CHART = ROOT / "apps" / "web" / "components" / "Chart.tsx"


def test_hidden_stems_match_the_engine():
    """
    ★ 화면의 지장간 표가 서버와 다르면 두 곳이 다른 말을 한다.

      셈은 서버가 하고 설명은 화면이 한다. 표가 갈리면 설명이 셈을
      틀린 것으로 만든다.
    """
    src = CHART.read_text(encoding="utf-8")
    i = src.index("const HIDDEN")
    block = src[i:src.index("};", i)]
    for ji, pairs in HIDDEN.items():
        want = [g for g, _ in pairs]
        m = re.search(r"%s:\s*\[([^\]]*)\]" % ji, block)
        assert m, "지지 %s 가 화면 표에 없다" % ji
        got = re.findall(r"[가-힣一-鿿]+", m.group(1))
        assert got == want, "%s — 화면 %s · 서버 %s" % (ji, got, want)


def test_columns_run_right_to_left():
    """만세력은 오른쪽부터 시·일·월·년이다. 순서를 바꾸면 다른 값처럼 보인다."""
    src = CHART.read_text(encoding="utf-8")
    i = src.index("export function ManseTable")
    body = src[i:i + 2500]
    assert ".reverse()" in body, "시·일·월·년 순서로 안 뒤집었다"


def test_it_says_where_the_hidden_number_came_from():
    src = CHART.read_text(encoding="utf-8")
    assert "지장간" in src, "숨은 글자를 안 밝힌다"
    assert "0.3" in src, "0.3 이 어디서 왔는지 안 잇는다"


def test_school_choices_are_told_to_everyone():
    """
    ★ 갈리는 사람에게만 말하면, 안 걸리는 사람은 자기가 안 걸리는 줄도
      모르고 다른 만세력과 대 본다. 누구에게나 밝히고, 안 걸리는
      사람에게는 **안 걸린다고** 말해 준다.
    """
    src = CHART.read_text(encoding="utf-8")
    assert "집마다 다름" in src, "어느 자리가 갈리는지 딱지를 안 단다"
    assert "안 걸리니" in src, "안 걸리는 사람에게 안심을 안 준다"
    assert "고른 것이 다른" in src, "틀린 게 아니라는 말을 안 한다"
