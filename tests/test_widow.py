# -*- coding: utf-8 -*-
"""
과부 줄(widow) 이 없는가.

★ 과부 줄이 무엇인가

  문단 **마지막** 줄에 조각만 홀로 남는 것이다.

      왜 그리 말했는지까지 적어 드리오. 맞힌다고는
      안 하오.

  글이 틀린 것도 버그도 아닌데, 읽는 사람에게는 덜 만든 것처럼
  보인다. 첫 화면에서 그러면 그 인상이 끝까지 간다. 가운데 정렬이면
  더 티가 난다. (첫 줄이 떨어지면 고아 줄/orphan 이라 부른다.)

★ 어떻게 재는가

  화면 폭도 글자 크기도 정해져 있으니 한 줄에 몇 자가 들어가는지
  셀 수 있다. tools/widow.py 가 그 계산을 들고 있다.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import widow  # noqa: E402


def _bad():
    out = []
    for rel, line, kind, text in widow.harvest():
        px = widow.SIZE.get(kind, 16.0)
        box = widow.GATE_WIDTH if kind == "promise" else widow.WIDTH
        lines = widow.wrap(text, px, box)
        if len(lines) < 2:
            continue
        tail = sum(widow.width_of(c) for c in lines[-1])
        if tail <= widow.WIDOW:
            out.append("%s:%d  …%s" % (rel, line, lines[-1]))
    return out


def test_no_widow_lines():
    bad = _bad()
    assert not bad, "마지막 줄에 조각만 남는 자리:\n  " + "\n  ".join(bad)


def test_css_asks_the_browser_to_avoid_them():
    """손으로 못 잡는 자리는 브라우저가 피하게 둔다."""
    css = (ROOT / "apps" / "web" / "styles" / "overrides.css").read_text(
        encoding="utf-8")
    assert "text-wrap: pretty" in css, "pretty 가 없다"
    for cls in (".sm", ".say", ".nar"):
        assert cls in css.split("text-wrap: pretty")[0].rsplit("{", 1)[0][-400:], \
            "%s 에 안 걸려 있다" % cls
