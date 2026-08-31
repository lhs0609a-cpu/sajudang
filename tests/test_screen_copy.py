"""
화면이 손님이 아는 말로 쓰였는가.

★ 명식 화면이 이랬습니다:

      여덟 글자가 섰다.
      년주 · 월주 · 일주 · 시주
      庚 일간 · 신강(26) · 용신 불
      가장 강한 것 물 3 · 흐름 식상
      주도 십신 상관 · 대운 순행 · 대운수 4

  처음 온 사람은 하나도 못 알아봅니다. 이 집은 "근거 대는 집" 인데,
  근거를 **모르는 말로** 대면 그건 근거가 아니라 주문입니다.

★ 용어를 지우지는 않습니다. 옆에 뜻을 답니다. 명리 용어는 이 집의
  근거이자 신뢰의 재료라, 없애면 여느 점집과 같아집니다.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
CHART = WEB / "components" / "Chart.tsx"


def _customer_screens():
    """손님이 보는 화면만. 관리자 레일은 뺍니다."""
    return [p for p in list((WEB / "app").rglob("*.tsx")) +
            list((WEB / "components").rglob("*.tsx"))
            if p.name != "DevRail.tsx"]


def test_the_internal_score_never_reaches_the_customer():
    """
    ★ 「신강(26)」의 26은 **내부 척도**입니다. 신강약을 재는 우리 쪽
      점수인데 그게 화면에 그대로 나가고 있었습니다.
      근거는 보이되 규칙은 감춥니다 (CLAUDE.md).
    """
    bad = [str(p.relative_to(WEB)) for p in _customer_screens()
           if "strength_score" in p.read_text("utf-8")]
    assert not bad, ("손님 화면에 내부 점수가 나갑니다: %s" % bad)


def test_every_hard_word_is_explained_where_it_appears():
    """
    명식 화면에 나오는 말은 그 자리에서 풀어 줍니다.
    """
    src = CHART.read_text("utf-8")
    for word, gloss in [
        ("일간", "나 자신"),
        ("용신", "모자란 것을 채워"),
        ("대운", "십 년마다"),
        ("주도", "관계에 붙인"),
    ]:
        assert word in src, word
        assert gloss in src, ("%s 을(를) 안 풀어 줍니다" % word)


def test_the_pillars_say_what_they_look_at():
    """
    년주·월주·일주·시주가 한자 넉 줄로만 서 있었습니다.
    각 기둥이 무엇을 보는 자리인지 적습니다.
    """
    src = CHART.read_text("utf-8")
    for label, gloss in [("년주", "태어난 해"), ("월주", "태어난 달"),
                         ("일주", "태어난 날"), ("시주", "태어난 시각")]:
        assert gloss in src, ("%s 을(를) 안 풀어 줍니다" % label)


def test_the_ten_gods_are_all_glossed():
    """
    십신 열 가지가 이름만 나오고 뜻이 없었습니다. 「상관」이 무엇인지
    아는 손님은 거의 없습니다.
    """
    src = CHART.read_text("utf-8")
    for g in ("비견", "겁재", "식신", "상관", "편재", "정재",
              "편관", "정관", "편인", "정인"):
        assert g in src, ("십신 %s 이(가) 빠졌습니다" % g)


def test_the_eight_characters_are_explained_once():
    """
    ★ "여덟 글자가 섰다" 만 있고 그게 무슨 뜻인지 아무 데도 없었습니다.
      첫 화면에서 한 번은 말해 줘야 뒤가 읽힙니다.
    """
    entry = (WEB / "app" / "page.tsx").read_text("utf-8")
    assert "여덟 글자가 섰다" in entry
    assert "두 글자로 옮긴 것" in entry, "여덟 글자가 무엇인지 안 밝힙니다"
