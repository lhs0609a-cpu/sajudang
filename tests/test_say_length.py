"""
말풍선 하나가 한 마디를 넘지 않는가.

★ 2026-09-03. 손님이 a5 에서 멈췄습니다. 도령의 말이 **열세 줄짜리
  말풍선 하나**였습니다.

      "지금 전반적으로 말이 너무 길어, 적당하면서도 임팩트있게,
       그리고 대화형식으로 글이 띄어져야할거아냐 자연스럽게"

  재보니 마흔둘 중 스물넷이 문턱을 넘었고, 평균이 209자였습니다.

★ 고친 자리는 **글이 아니라 화면**이었습니다.

  글은 이미 마디로 쓰여 있었습니다 — `<br />` 로 끊어 두었죠. 화면이
  그걸 무시하고 한 상자에 부었을 뿐입니다. `Narration.Say` 가 마디마다
  말풍선을 내게 하고, 그래도 긴 스무 자리에 `<br />` 를 한 번씩 더
  넣었습니다. **글자는 한 자도 안 지웠습니다** — 연출 점수가 그 글로
  매겨져 있어서, 지우면 점수가 아니라 화면이 상합니다.

  결과: 말풍선 42 → 119개 · 평균 209 → 59자 · 가장 긴 것 1,160 → 119자.

★ 대화는 주고받는 것입니다. 한 사람이 열세 줄을 이어 말하면 그건
  대화가 아니라 연설이고, 손님은 읽는 게 아니라 훑습니다.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from say_length import MAX_CHARS, MAX_SENT, scan   # noqa: E402


def test_말풍선_하나가_한_마디를_넘지_않는다():
    rows = scan()
    assert rows, "말풍선을 하나도 못 찾았소 — 자가 고장 났소"
    bad = [r for r in rows
           if r["chars"] > MAX_CHARS or r["sent"] > MAX_SENT]
    assert not bad, (
        "한 번에 쏟는 말풍선 %d개 (문턱 %d자 · %d문장)\n  %s\n"
        "  <br /> 로 마디를 끊으시오 — 글은 안 지워도 되오."
        % (len(bad), MAX_CHARS, MAX_SENT,
           "\n  ".join("%s %s:%d#%d %d자 %d문장  %s"
                       % (r["screen"], r["file"].split("/")[-1], r["line"],
                          r["beat"], r["chars"], r["sent"], r["text"][:40])
                       for r in sorted(bad, key=lambda r: -r["chars"])[:12])))


def test_말이_한_상자에_안_담긴다():
    """
    ★ 마디를 끊어 두어도 화면이 한 상자에 부으면 헛일입니다.
      `Say` 가 <br /> 에서 갈라 말풍선을 따로 내는지 봅니다.
    """
    src = (ROOT / "apps" / "web" / "components"
           / "Narration.tsx").read_text(encoding="utf-8")
    assert "function beats(" in src, "Say 가 마디를 안 가르오"
    assert 'className={"say" + (i ? " cont" : "")}' in src, \
        "이어 말하는 마디에 표가 없소"
    # 얼굴은 첫 마디에만 — 마디마다 붙이면 스무 명이 번갈아 말하는 꼴
    assert "i === 0 && l && (" in src, "얼굴이 마디마다 붙소"


def test_평균이_대사_길이에_머문다():
    """
    ★ 문턱만 지키고 평균이 문턱에 붙어 있으면 화면은 여전히 빽빽합니다.
      웹툰 말풍선은 두세 줄입니다 — 평균은 그 언저리에 있어야 하오.
    """
    rows = scan()
    avg = sum(r["chars"] for r in rows) / len(rows)
    assert avg < 90, "말풍선 평균이 %d자요 — 여전히 빽빽하오" % round(avg)
