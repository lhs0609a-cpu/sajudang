"""
접어 둔 말이 분량에서 빠지는가 — 그리고 브레이크는 안 접혔는가.

★ 2026-09-03. 손님이 말했습니다 —

      "전체적으로 글자가 너무 많아. 글 길이도 연출점수에 포함시켜서
       가독성을 극대화시켜. 전체 설계 다시해. 가독성이 너무 안좋아."

  분량 축(pace)은 이미 있었는데 **상한이 스무 배 헐거웠습니다** —
  「읽는 자리 1200초(20분)」 였고 점수는 그 두 배에서야 0 이 되니,
  스물여덟 화면이 **전부 100점**이었습니다. 본문이 18분인데도요.
  다 잘하고 있다고 말하는 자는 없는 것보다 나쁩니다.

★ 지우는 게 아니라 접습니다

  적는 자리의 글에는 이 집이 파는 것이 들어 있습니다 — 왜 묻는지,
  안 적으면 어찌 되는지. 지우면 팩폭·울림이 같이 죽습니다.
  그래서 `<Fold>` 로 접고, 자가 **분량에서만** 뺍니다.

★ 브레이크는 접지 않습니다

  「나가도 붙잡지 않소」 「값은 보이는 그대로 청구되오」 「하루 2번」
  같은 것은 풀이가 아니라 **약속**입니다. 접으면 안 본 것과 같아지고,
  그건 브레이크를 푸는 것입니다 (CLAUDE.md 절대 규칙 4).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import dramaturgy as D                     # noqa: E402
from engine import screenscan as S                     # noqa: E402

FOLD = re.compile(r"<Fold\b.*?</Fold>", re.S)


def test_접힌_글은_읽는_시간에서_빠진다():
    """
    ★ 자가 바뀌었습니다 (2026-09-04).

      손님이 정했습니다 — "페이지가 길면 괜찮은데 한 화면에 글자 꽉
      채우면 안 돼." 그래서 **총 분량에 매기던 점수를 걷어냈습니다.**
      길이는 죄가 아닙니다. 읽기속도는 이제 「가장 큰 상자가 한 화면을
      넘는가」를 봅니다 (dramaturgy.FILL_*).

      접힌 글은 여전히 빠집니다 — 다만 점수가 아니라 **읽는 시간**
      에서요. 그 수는 주인 자리에 그대로 뜹니다. 접힌 글의 강조도
      안 셉니다 (screenscan.MARK 는 FOLD 를 먼저 걷어냅니다).
    """
    html = "<p>" + ("가" * 600) + "</p>"
    full = D.score("t", "재보기", html, "input")
    half = D.score("t", "재보기", html, "input", folded=300)
    assert half["secs"] < full["secs"], "접어도 읽는 시간이 그대로요"
    # 다른 축은 그대로 — 접힌 글도 편 사람은 읽습니다
    for k in ("bite", "heart", "figure", "clear"):
        assert half[k] == full[k], "%s 가 접기로 움직이오" % k


def test_분량_상한이_실제로_문다():
    """
    ★ 상한이 헐거우면 축이 있으나 마나입니다. 한 상자에 900자를
      **안 끊고** 쏟았는데 만점이 나오면 안 됩니다 — 그 하나로
      화면이 한 번 반 넘게 찹니다.
    """
    long_input = "<p>" + ("가" * 900) + "</p>"
    got = D.score("t", "재보기", long_input, "input")
    assert got["pace"] < 70, "한 상자에 900자인데 %d점이오" % got["pace"]


def test_자가_접힌_글을_갈라_센다():
    """소스에서 <Fold> 를 알아보고 그 글자 수를 따로 들고 와야 합니다."""
    S._screens.cache_clear()
    pairs = S._screens()
    folded = {sid: v[4] for sid, v in pairs.items() if len(v) > 4 and v[4]}
    assert folded, "접은 자리를 하나도 못 셌소 — FOLD 를 못 읽는 것이오"
    S._screens.cache_clear()


def test_브레이크는_접히지_않았다():
    """
    ★ 접는 것은 **풀이**뿐입니다. 약속과 만류는 화면에 그대로 있어야
      합니다 — 접으면 안 본 것과 같고, 그건 브레이크를 푸는 것입니다.
    """
    keep = [
        "나가도 붙잡지 않소",          # 페이월 — 만류
        "1원도 없소",                  # 결제 — 표시가 = 청구가
        "하루에 2번",                  # 하루 결제 2건
    ]
    src = "".join((WEB / "app" / p).read_text(encoding="utf-8")
                  for p in ("page.tsx", "pay/page.tsx",
                            "report/[id]/page.tsx"))
    folded = " ".join(m.group(0) for m in FOLD.finditer(src))
    for k in keep:
        assert k in src, "약속이 사라졌소: %s" % k
        assert k not in folded, "약속을 접었소: %s" % k
