# -*- coding: utf-8 -*-
"""
엿보기 — 물음은 보이고 **답은 서버에 남는가.**

★ 손님이 시킨 것 (2026-09-04)

  "자리 하나든 스무 사람 전부든 누르면 다음에는 각 캐릭터들이 나와서
  «당신에게 가장 중요한 건 ~~» 블러 처리하고 … 너무나 궁금해서 결제
  안 하고는 미칠 정도로."

★ 블러는 **가림이지 잠금이 아닙니다**

  이 집의 절대 규칙 — 「잠긴 컷은 본문이 아예 안 내려옵니다. 블러로
  가린 게 아니라 서버가 안 줍니다」 (docs/02 §7). 글을 내려보내고 CSS
  로 흐리면 개발자도구에서 그대로 읽힙니다. 값을 치른 사람과 안 치른
  사람이 같은 것을 받는 셈입니다.

  그래서 **앞머리만 진짜로 보내고 뒤는 서버에 남깁니다.** 화면은 그
  길이만큼 칸을 그립니다 — 벗겨도 나올 게 없습니다.

  이 검사가 그 자리를 지킵니다. 언젠가 「블러 처리하면 되잖아」 로
  되돌아가려는 날, 여기서 걸립니다.
"""
import re
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine.calendar import build_chart          # noqa: E402
from engine.features import build_features       # noqa: E402
from engine.peek import build_peek, _plain       # noqa: E402
from engine.report import build_report           # noqa: E402

LENSES = ["pungun", "baegun", "cheongam", "sigye"]


@pytest.fixture(scope="module")
def f():
    return build_features(
        build_chart(1993, 11, 25, 15, 55, "M", city="서울"),
        as_of=date.today())


def _body(rep) -> str:
    return " ".join(re.sub(r"<[^>]+>", "", c["html"]) for c in rep["cuts"])


# ── 답이 새지 않는가 ──────────────────────────────────────
def test_no_paid_sentence_reaches_the_peek(f):
    """
    유료 본문의 **한 문장도** 엿보기에 섞이면 안 된다.
    앞머리는 맛보기에서 온 짧은 조각이라 문장이 아니다.
    """
    rows = build_peek(f, "t", ["pungun"], "work", "INTJ")
    blob = " ".join((r["head"] or "") for r in rows)
    paid = _body(build_report(f, "t", "pungun", "one", "work", "INTJ"))
    leaked = [s.strip() for s in re.split(r"[.!?]", paid)
              if len(s.strip()) >= 22 and s.strip() in blob]
    assert not leaked, "유료 문장이 엿보기에 섞였소: %s" % leaked[:2]


def test_the_hidden_part_is_a_number_not_a_string(f):
    """가린 것은 **길이**다. 글자를 보내면 그건 블러지 잠금이 아니다."""
    for r in build_peek(f, "t", ["pungun"], "work", "INTJ"):
        assert isinstance(r["mask"], int) and r["mask"] > 0
        assert "answer" not in r and "body" not in r and "html" not in r


def test_the_head_is_much_shorter_than_the_cut(f):
    """앞머리가 컷의 절반을 넘으면 그건 엿보기가 아니라 본문이다."""
    for r in build_peek(f, "t", ["pungun"], "work", "INTJ"):
        assert len(r["head"]) < r["chars"] * 0.5, r["ask"]


# ── 궁금해질 만한가 ──────────────────────────────────────
def test_many_people_ask_different_things(f):
    """
    ★ 스무 사람을 산 사람에게 네 명이 「지금은 庚申 대운이오」 를
      나란히 말하면, 궁금해지기는커녕 «다 같은 것» 으로 보인다.
      관점 컷(lc_)이 그 사람을 산 까닭 그 자체이니 그것부터 낸다.
    """
    rows = build_peek(f, "t", LENSES, "work", "INTJ", limit=4)
    asks = [r["ask"] for r in rows]
    assert len(set(asks)) == len(asks), "여럿이 같은 것을 묻소: %s" % asks
    heads = [r["head"] for r in rows]
    assert len(set(heads)) == len(heads), "앞머리가 겹치오"


def test_one_lens_gets_that_lens_only(f):
    rows = build_peek(f, "t", ["pungun"], "work", "INTJ")
    assert rows and {r["lens_id"] for r in rows} == {"pungun"}


def test_the_source_is_not_hidden(f):
    """
    ★ 가리는 것은 **답**이지 근거가 아니다. 무엇을 보고 한 말인지는
      값을 치르기 전에도 보여 준다 — 그게 이 집의 자리다.
    """
    for r in build_peek(f, "t", ["pungun"], "work", "INTJ"):
        assert (r["source"] or "").strip(), r["ask"]


def test_glosses_do_not_eat_the_head(f):
    """
    앞머리 열여덟 자를 용어 풀이가 다 먹으면 궁금할 까닭이 없다.
    맛보기는 잘려 오므로 **닫는 괄호가 없는** 풀이도 걷어야 한다.
    """
    assert _plain("대운 (십 년마다 바뀌는 큰 마디") == "대운"
    assert "(" not in _plain("지금은 庚申 대운 (십 년마다 읽는 것) 이오.")


# ── 화면이 진짜로 안 받는가 ──────────────────────────────
def test_the_screen_never_draws_a_blurred_body():
    """
    화면이 `filter: blur` 로 본문을 가리면 그 아래 글이 DOM 에 있다는
    뜻이다. 여기서는 애초에 글이 없고 **칸만** 있어야 한다.
    """
    css = (WEB / "styles" / "overrides.css").read_text(encoding="utf-8")
    i = css.index(".peek .pkmask")
    block = css[i:i + 400]
    assert "blur(" not in block, "가린 자리에 블러를 걸었소 — 벗겨지오"
    assert "color: transparent" in block


def test_the_client_type_carries_no_answer():
    src = (WEB / "lib" / "api.ts").read_text(encoding="utf-8")
    i = src.index("payPeek")
    block = src[i:i + 700]
    assert "mask: number" in block
    for bad in ("answer", "body:", "html:"):
        assert bad not in block, "엿보기 응답에 %s 가 있소" % bad


# ── 손님한테 하는 말인가 ─────────────────────────────────
#
# ★ 손님이 짚은 것 (2026-09-04)
#
#   "이 부분은 당신한테 하는 말이어야지, 뭔 말이야 이게."
#
#   엿보기 넉 줄이 이랬습니다 —
#
#       풍운도령 「뿌리가 있는가」     나는 뿌리부터 보오. 뿌리가 있
#       백운선사 「덥고 마른가…」      나는 십신을 세지 않소.
#       청암거사 「격을 잡는다」       순서가 있소. 격을 먼저 잡고 그
#       시계장이 「지금 어느 눈금인가」 나는 때를 보는 사람입니다.
#
#   넉 줄 전부 **화자가 자기 소개**를 하고 있고, 손님 얘기는 한 줄도
#   없었습니다. 값을 치를지 정하는 자리에서 스무 사람이 돌아가며 제
#   보는 법을 설명한 셈입니다.
#
#   까닭은 둘이었습니다 —
#     ① 물음이 컷 **제목**이었습니다. 제목은 그 캐릭터가 제 보는 법에
#        붙인 이름이라(「격을 잡는다」) 손님에게 하는 물음이 아닙니다.
#     ② 앞머리가 **맛보기**에서 왔습니다. 맛보기는 컷의 앞 40%인데
#        관점 컷은 거기가 통째로 여는 말(화자 얘기)입니다.

SELF_TALK = re.compile(r"^(나는|내가|나도|저는|제가)\b")


def _you_of(lid):
    from engine.lens import you_of
    return you_of(lid, "", "M")


def test_the_peek_speaks_to_the_customer_not_about_the_speaker(f):
    """앞머리가 화자의 자기 소개로 시작하면 안 된다."""
    bad = [(r["lens_name"], r["head"])
           for r in build_peek(f, "t", LENSES, "work", "INTJ", limit=6)
           if SELF_TALK.match(r["head"])]
    assert not bad, "엿보기가 제 얘기를 하오: %s" % bad


def test_every_question_is_asked_of_the_customer(f):
    """
    ★ 물음은 **손님을 부르는 말**을 달고 나가야 합니다. 「격을 잡는다」는
      목차지 물음이 아닙니다.
    """
    for lid in LENSES:
        you = _you_of(lid)
        for r in build_peek(f, "t", [lid], "work", "INTJ", limit=6):
            assert you in r["ask"], (
                "%s 의 물음에 손님이 없소: 「%s」" % (r["lens_name"], r["ask"]))


def test_the_question_and_the_answer_call_the_customer_the_same_thing(f):
    """물음은 「그대」인데 답은 「자네」면 한 상자에 부르는 사람이 둘이다."""
    for lid in LENSES:
        you = _you_of(lid)
        for r in build_peek(f, "t", [lid], "work", "INTJ", limit=6):
            for other in ("그대", "자네", "당신", "그쪽"):
                if other == you:
                    continue
                assert other not in r["ask"], (
                    "%s 가 「%s」라 부르오: %s" % (lid, other, r["ask"]))


def test_a_particle_never_breaks_away_from_its_word(f):
    """
    ★ `<b>상관</b>이` 를 「상관 이」로 내보내면 손님 눈에는 오탈자입니다.
      태그는 블록만 띄우고 인라인은 붙입니다.
    """
    bad = [r["head"] for r in build_peek(f, "t", LENSES, "work", "INTJ")
           if re.search(r"[가-힣一-龥A-Za-z0-9]\s+[은는이가을를의로]\b", r["head"])]
    assert not bad, "조사가 낱말에서 떨어졌소: %s" % bad


def test_the_source_line_calls_the_customer_by_name_too(f):
    """
    ★ 근거의 이치는 「관성은 나를 누르는 자리라」 로 쓰여 있었습니다.
      명리에서 그 「나」는 일간, 곧 **손님**입니다. 그런데 화면에서는
      캐릭터가 말하는 상자 안이라 **제 얘기**로 읽혔습니다.
    """
    from engine.why import AXIS, GROUP, RULE, TEN_GOD
    for table in (TEN_GOD, GROUP, RULE, AXIS):
        for key, val in table.items():
            line = val[0] if isinstance(val, tuple) else val
            assert not re.search(r"(^|[^가-힣])(나를|나와|나에게|내가|내 편)", line), (
                "근거의 이치가 제 얘기를 하오 — %s: %s" % (key, line))
