"""
감정 곡선과 깊이 자리 — 값이 아깝지 않은가

★ 손님이 물은 것 (2026-09-07)

  "비싼 캐릭터들은 더 심층적으로 다각도로 분석해서 설계해놨어?
   그 돈이 전혀 아깝지 않고 인생에 도움이 되어야 해. 희망도 주고
   위로도 주고 웃기기도 하고 울리기도 하고."

★ 재보니 아니었습니다

  19,900원짜리 29컷 12,582자가 **전부 진단**이었습니다. 앞을 보는
  자리는 「이번 주 한 가지」 하나(255자)뿐이고, 유일하게 따뜻한
  「누가 돕는가」는 236자로 가장 짧고 스물두 번째에 묻혀 있었습니다.
  그리고 19,900원이 9,900원보다 주는 것은 **같은 꼴의 진단문 일곱**
  이었습니다 — 「더 길다」이지 「더 깊다」가 아닙니다.

★ 그래서 이 파일이 지키는 것

      ① 감정 곡선의 **자리**   위로는 아픈 말 뒤, 희망은 처방 앞
      ② 값이 여는 **종류**     비싼 자리에만 있는 컷이 있는가
      ③ 위로가 **셈에서** 나오는가  빈말이면 이 집 것이 아닙니다
      ④ 스무 사람의 **온도**가 다른가
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import lens as lens_mod                      # noqa: E402
from engine import report as report_mod                  # noqa: E402
from engine.calendar import build_chart                  # noqa: E402
from engine.features import build_features               # noqa: E402
from engine.report import build_report                   # noqa: E402

TAG = re.compile(r"<[^>]+>")


def _f(spec=(1993, 11, 25, 15, 55, "M")):
    return build_features(build_chart(*spec), as_of=date(2026, 9, 7))


def _ids(rep):
    return [c["id"] for c in rep["cuts"]]


# ══════════════════════════════════════════════════════════
# ① 감정 곡선 — 자리가 뜻입니다
# ══════════════════════════════════════════════════════════
@pytest.mark.parametrize("lens", [l for l in lens_mod.released()],
                         ids=lambda l: l["id"])
def test_comfort_comes_right_after_the_hardest_line(lens):
    """
    ★ 위로는 **가장 아픈 말 바로 뒤**입니다.

      아프게 해 놓고 그대로 다음 진단으로 넘어가면 그건 상담이 아니라
      진단서입니다. 캐릭터마다 `why` 를 맨 앞에 두기도 하므로
      (lens.view.lead) 자리는 사람마다 다르지만, **붙어 있어야** 합니다.
    """
    tier = "one" if lens.get("price") else "free"
    rep = build_report(_f(), "t", lens["id"], tier, "work", "INFP")
    ids = _ids(rep)
    assert "why" in ids and "solace" in ids, lens["id"]
    assert ids.index("solace") == ids.index("why") + 1, (lens["id"], ids[:8])


def test_the_ending_is_hope_then_prescription_then_close():
    """
    ★ 끝 세 자리를 고정합니다 — 희망 → 처방 → 마감.

      「이걸 하시오」 앞에 「그대가 이미 쥔 것은 이것이오」 가 서야
      처방이 숙제가 아니라 쓸 수 있는 힘이 됩니다.
    """
    for lens in lens_mod.released():
        if not lens.get("price"):
            continue          # 청동자는 브레이크라 유료 컷이 없소
        rep = build_report(_f(), "t", lens["id"], "one", "money", "INFP")
        ids = _ids(rep)
        assert ids[-1] == "closing_cut", (lens["id"], ids[-3:])
        assert ids[-2] == "week", (lens["id"], ids[-3:])
        assert ids[-3] == "hope", (lens["id"], ids[-3:])


# ══════════════════════════════════════════════════════════
# ② 값이 여는 것이 **종류**인가
# ══════════════════════════════════════════════════════════
def test_the_dear_seat_opens_a_kind_the_cheap_one_never_has():
    """
    ★ 이 검사가 이 파일의 값어치 자리입니다.

      전에는 19,900원이 9,900원보다 **관점 컷 일곱**을 더 줬는데
      그 일곱도 같은 꼴의 진단문이었습니다. 두 배 값의 근거가
      분량뿐이면 그건 값이 아니라 눈금입니다.
    """
    f = _f()
    rich = _ids(build_report(f, "t", "pungun", "one", "work", "INFP"))
    poor = _ids(build_report(f, "t", "jeokhyeol", "one", "work", "INFP"))
    for cid in ("hindsight", "counter"):
        assert cid in rich, cid
        assert cid not in poor, cid


def test_the_middle_rung_gets_hindsight_but_not_the_counter():
    """15,900원은 「지나온 자리」까지, 19,900원만 「내가 틀렸다면」."""
    f = _f()
    mid = _ids(build_report(f, "t", "baegun", "one", "work", "INFP"))
    assert "hindsight" in mid
    assert "counter" not in mid


def test_looking_back_never_invents_an_event():
    """
    ★ 지나온 칸을 짚되 **무슨 일이 있었다고는 말하지 않습니다.**
      사건을 지어내면 그건 점이 아니라 소설입니다.
    """
    banned = ("있었소", "겪었소", "잃었소", "만났소", "헤어졌", "그만두었")
    for spec in ((1993, 11, 25, 15, 55, "M"), (1978, 3, 3, 21, 40, "F")):
        rep = build_report(_f(spec), "t", "pungun", "one", "love", "INFP")
        for c in rep["cuts"]:
            if c["id"] != "hindsight":
                continue
            body = TAG.sub("", c["html"])
            # 「무슨 일이 있었는지는 내가 모르오」 는 남깁니다 — 부정문입니다.
            body = body.replace("무슨 일이 있었는지는 내가 모르오", "")
            body = body.replace("무슨 일이 있었다고는 말하지 않소", "")
            for w in banned:
                assert w not in body, (spec, w, body[:80])


# ══════════════════════════════════════════════════════════
# ③ 위로가 셈에서 나오는가
# ══════════════════════════════════════════════════════════
def test_comfort_is_counted_not_soothed():
    """
    ★ "괜찮아요, 다 잘될 거예요" 는 이 집이 하지 않는 말입니다.
      아무것도 금지하지 않아 어떤 관찰에서도 살아남습니다.

      위로에도 **센 것**이 들어 있어야 합니다 — 없는 기운, 희소도.
    """
    for spec in ((1993, 11, 25, 15, 55, "M"), (2001, 7, 19, 8, 5, "F")):
        rep = build_report(_f(spec), "t", "pungun", "one", "work", "INFP")
        cut = next(c for c in rep["cuts"] if c["id"] == "solace")
        body = TAG.sub("", cut["html"])
        assert "여덟 글자에서" in body, body[:60]
        assert "배치" in body, body[:60]
        # 근거 줄이 이치와 출처를 달고 있어야 합니다.
        assert "—" in (cut["source"] or ""), cut["source"]
        assert "〔" in (cut["source"] or ""), cut["source"]


def test_hope_never_promises():
    """
    ★ 희망은 **가진 것**으로 씁니다. 「좋아질 것이오」는 검증 불가능한
      주장이고 시점 확정 금지에 걸립니다 (docs/11).
    """
    banned = ("잘될 것이", "좋아질 것이", "성공하", "부자가", "반드시")
    for lens in lens_mod.released():
        if not lens.get("price"):
            continue
        rep = build_report(_f(), "t", lens["id"], "one", "money", "INFP")
        cut = next(c for c in rep["cuts"] if c["id"] == "hope")
        body = TAG.sub("", cut["html"])
        # ★ 이 집이 스스로 「잘될 것이라는 말은 안 하오」 라 적은 줄은
        #   뺍니다. 어미는 말투 층이 갈므로(안 하오/안 합니다/안 해요)
        #   **안 바뀌는 앞부분**으로만 잡습니다.
        body = body.replace("잘될 것이라는 말은 안", "")
        for w in banned:
            assert w not in body, (lens["id"], w, body[:80])


# ══════════════════════════════════════════════════════════
# ④ 스무 사람의 온도가 다른가
# ══════════════════════════════════════════════════════════
def test_twenty_people_comfort_differently():
    """
    ★ 스무 사람이 **같은 위로**를 하면 그건 위로가 아니라 안내문입니다.
      삼거리 노파는 웃기고 연담은 울려야 합니다. 본문은 셈에서 나오니
      한 벌로 두고, 온도만 곁말로 스물을 갈랐습니다 (flavor.SIDE).
    """
    f = _f()
    tails = {}
    for lens in lens_mod.released():
        tier = "one" if lens.get("price") else "free"
        rep = build_report(f, "t", lens["id"], tier, "work", "INFP")
        cut = next(c for c in rep["cuts"] if c["id"] == "solace")
        side = re.findall(r'<p class="side">(.*?)</p>', cut["html"], re.S)
        assert side, "%s 가 제 온도로 위로하지 않소" % lens["id"]
        tails[lens["id"]] = TAG.sub("", side[-1]).strip()
    assert len(set(tails.values())) == len(tails), \
        "같은 말로 위로하는 캐릭터가 있소"


def test_the_two_new_cuts_pass_the_guard():
    """금지어 필터를 지납니다 — 병·수명·이혼 단정·투자 시점."""
    from engine import guard
    f = _f()
    for lens in ("pungun", "yakcho", "yeondam"):
        rep = build_report(f, "t", lens, "one", "health", "INFP")
        for c in rep["cuts"]:
            if c["id"] in ("solace", "hope", "hindsight", "counter"):
                assert guard.enforce(c["html"], {"cut": c["id"]}) == c["html"]


def test_the_rungs_are_ordered_by_price():
    """값이 오르는데 여는 층이 줄면 사다리가 아닙니다."""
    seen = -1
    for threshold, _cid in report_mod.PRICE_RUNGS:
        assert threshold >= seen, report_mod.PRICE_RUNGS
        seen = threshold
