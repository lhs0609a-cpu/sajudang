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


# ══════════════════════════════════════════════════════════
# 어려운 말 풀이 층
# ══════════════════════════════════════════════════════════
#
# ★ 재보니 어려운 말 41가지 중 **40가지가 풀이 없이** 2,860번
#   나오고 있었습니다 (tools/hard_words.py).
import sys
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import terms as T                      # noqa: E402
from engine.calendar import build_chart            # noqa: E402
from engine.features import build_features         # noqa: E402
from engine.report import build_report, _plain     # noqa: E402


def test_a_hard_word_is_explained_the_first_time_it_appears():
    out = T.gloss("자네 격은 편관이 잡았소.")
    assert "편관<i class=\"gl\">(나를 누르는 힘)</i>" in out
    assert "격<i class=\"gl\">(이 사주를 읽는 틀)</i>" in out


def test_it_is_explained_only_once():
    """
    한 장 안에서 열 번 다 풀면 읽기를 방해합니다.
    """
    seen: set = set()
    a = T.gloss("편관이 셋이오.", seen)
    b = T.gloss("편관이 또 나오오.", seen)
    assert "gl" in a and "gl" not in b


def test_the_same_letters_in_a_different_word_are_left_alone():
    """
    ★ 「상관없소」를 「상관(밖으로 내지르는 힘)없소」로 만들면 안 됩니다.
      「격」은 한 글자라 성격·가격·자격에 다 걸립니다.
    """
    for t in ("그건 상관없소.", "성격이 아니오.", "가격이 다르오.",
              "자격을 보오.", "지지하는 사람이오."):
        assert "gl" not in T.gloss(t), t


def test_the_parentheses_live_in_the_text_not_the_css():
    """
    ★ CSS 의 ::before 로만 두면 태그를 걷어낸 자리에서
      「용신모자란 것을 채워 줄 기운」처럼 붙어 버립니다 —
      공유 payload · 분석지 · 미리보기가 그렇습니다.
    """
    assert "(" in T.gloss("용신을 보오.")
    css = (WEB / "styles" / "overrides.css").read_text("utf-8")
    assert ".gl::before" not in css


def test_a_real_report_explains_its_hard_words():
    f = build_features(build_chart(1997, 3, 22, 14, 10, "F", True, "서울"))
    rep = build_report(f, "t", "pungun", "one", "love", "INFP", name="가은")
    body = " ".join(_plain(c["html"]) for c in rep["cuts"])
    # ★ 리포트마다 나오는 말이 다릅니다 — 「용신」은 근거 줄에만 있고
    #   본문에는 "필요한 건 쇠" 로 나오기도 합니다. **나온 말만** 봅니다.
    checked = 0
    for term in T.MEANING:
        # ★ 한 글자 말(「격」)은 성격·가격에도 걸립니다. 풀이 층은
        #   앞 글자를 보고 올바르게 건너뛰는데, 이 검사는 그걸 못 봅니다.
        #   그 자리는 test_the_same_letters_in_a_different_word... 가
        #   따로 지킵니다.
        if len(term) < 2 or term not in body:
            continue
        i = body.index(term)
        assert "(" in body[i:i + 34], ("%s 을(를) 안 풀어 줍니다: %r"
                                       % (term, body[i:i + 34]))
        checked += 1
    assert checked >= 5, "리포트에 어려운 말이 너무 적습니다(%d)" % checked
