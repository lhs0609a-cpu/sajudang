"""
결합 축의 추가 입력 — docs/07 §결합 축

여기서 지키는 것
    · 상대 사주는 **저장하지 않는다** (제3자 생년월일 · docs/11)
    · 관계축은 잘 되겠다/안 되겠다를 판정하지 않는다
    · 혈액형은 근거가 아니라고 **먼저** 말한다
    · 맥락축은 자유 입력을 받지 않는다 (개인정보·가드 우회 경로)
    · 얼굴 사진은 붙이지 않는다 (생체인식정보)
"""
from __future__ import annotations

import json
import re

import pytest

from engine import extras
from engine import pattern, guard, lens as lens_mod
from engine.calendar import build_chart
from engine.features import build_features
from engine.report import build_report

PARTNER = {"year": 1990, "month": 8, "day": 3, "hour": 14, "minute": 0,
           "sex": "M", "hour_known": True}
CONTEXT = {"situation": "job", "stance": "hold", "since_months": 8}

ALL_PAYLOADS = {
    "partner": PARTNER,
    "context": CONTEXT,
    "blood": {"type": "A"},
    "image": {"pick": "door"},
    "cards": {"picks": ["gil", "mun", "san"]},
}


@pytest.fixture(scope="module")
def f():
    return build_features(build_chart(1993, 5, 15, 10, 20, "F"))


@pytest.fixture(scope="module")
def f_no_hour():
    return build_features(
        build_chart(1986, 6, 21, None, None, "F", hour_known=False))


# ══════════════════════════════════════════════════════════
# 배선 — 열둘이 추가 입력 없이 돌던 자리
# ══════════════════════════════════════════════════════════
def test_only_the_photo_is_still_missing():
    """
    얼굴 사진 말고는 전부 붙었는가.

    ★ 전에는 스무 명 중 **열둘**이 추가 입력 없이 돌았습니다.
      그래서 캐릭터를 바꿔 또 사도 순서만 바뀐 같은 리포트였습니다.
    """
    missing = lens_mod.missing_inputs()
    assert {m["input"] for m in missing} == {"photo"}, missing


def test_photo_is_blocked_for_a_reason_not_forgotten():
    """
    얼굴 사진은 '아직 안 함' 이 아니라 '하면 안 됨' 입니다.
    생체인식정보라 저장이 금지돼 있습니다 (CLAUDE.md · docs/11).
    """
    assert "photo" not in extras.BUILDERS
    assert "photo" in lens_mod.BLOCKED_INPUTS
    assert "생체인식" in lens_mod.BLOCKED_INPUTS["photo"]


@pytest.mark.parametrize("lens_id", [l["id"] for l in lens_mod.all_lenses()])
def test_every_lens_either_needs_nothing_or_gets_asked(f, lens_id):
    """
    추가 입력이 필요한 캐릭터는 안 받았을 때 **물어볼 수 있어야** 한다.
    컷을 지어내지 않습니다.

    ★ 고민도 묻습니다 (2026-09-04).

      전에는 **캐릭터만** 물었습니다. 그래서 월하선녀는 돈을 물어도
      상대 사주를 묻고, 백운선사는 사랑을 물어도 아무것도 안 물었습니다.
      손님이 짚었습니다 — "연애 고민이면 누구랑인지 어떻게 만났는지
      그런 거 싹 해서…"

      캐릭터가 받는 것이 **먼저**요. 그것이 없을 때만 고민이 묻고,
      그것도 **짜임이 걸렸을 때만** 묻습니다 (engine/pattern.asks_for).
    """
    rep = build_report(f, "cid", lens_id, "all", "love", "INFP")
    need = lens_mod.required_input(lens_id)
    got = rep["needs_input"]
    if need in extras.BUILDERS:
        assert got == need, "그 사람이 받는 것을 안 묻소"
    elif got is not None:
        # 고민이 부른 물음. **빌더가 있는 것**만, 그리고 짜임이 걸렸을 때만.
        assert got in extras.BUILDERS, got
        assert got == pattern.asks_for(f, "love"), (
            "짜임이 안 불렀는데 묻고 있소: %s" % got)


def test_the_concern_only_asks_when_a_pattern_calls_for_it():
    """
    ★ 「사랑을 골랐으니 상대 사주를 내시오」는 묻는 것이 아니라
      **받아 내는 것**입니다. 걸린 자리가 있어야 물을 까닭이 서고,
      손님도 왜 묻는지 압니다.
    """
    from engine.calendar import build_chart
    from engine.features import build_features
    from datetime import date as _d
    ff = build_features(build_chart(1993, 11, 25, 15, 55, "M", city="서울"),
                        as_of=_d.today())
    for concern in ("money", "work", "love", "people", "dir", "health"):
        want = pattern.asks_for(ff, concern)
        if want is None:
            continue
        # 물을 때는 **그 짜임이 실제로 걸려** 있어야 합니다.
        hit = [x for x in pattern.read(ff, concern, limit=99)
               if x.get("ask") == want]
        assert hit, (concern, want)
        assert want in extras.BUILDERS, want


@pytest.mark.parametrize("kind,payload", sorted(ALL_PAYLOADS.items()))
def test_each_extra_adds_a_cut(f, kind, payload):
    lens_id = next(l["id"] for l in lens_mod.all_lenses()
                   if l.get("input") == kind)
    rep = build_report(f, "cid", lens_id, "all", "love", "INFP",
                       {kind: payload})
    assert rep["needs_input"] is None
    ids = [c["id"] for c in rep["cuts"]]
    assert kind in ids, ids


@pytest.mark.parametrize("kind,payload", sorted(ALL_PAYLOADS.items()))
def test_every_extra_cut_passes_guard(f, f_no_hour, kind, payload):
    for feats in (f, f_no_hour):
        cut = extras.BUILDERS[kind](feats, payload)
        ok, hits = guard.check(cut["html"])
        assert ok, (kind, hits)


def test_extras_are_ignored_for_lenses_that_do_not_ask(f):
    """
    풍운도령에게 상대 사주를 밀어 넣어도 컷이 생기지 않는다.
    받을 사람이 정해져 있습니다.
    """
    rep = build_report(f, "cid", "pungun", "all", "love", "INFP",
                       {"partner": PARTNER})
    assert all(c["id"] != "partner" for c in rep["cuts"])


# ══════════════════════════════════════════════════════════
# 관계 — 상대 사주
# ══════════════════════════════════════════════════════════
def test_partner_never_judges_the_relationship(f):
    """
    잘 되겠다 / 안 되겠다 / 언제 / 기다려라 — 전부 금지 (docs/11).
    """
    cut = extras.partner_cut(f, PARTNER)
    for banned in ("잘 될", "안 될", "헤어지", "재회", "결혼합니다",
                   "기다리", "인연입니다", "천생연분"):
        assert banned not in cut["html"], banned


def test_partner_needs_a_full_birth_date(f):
    with pytest.raises(extras.ExtraInputError):
        extras.partner_cut(f, {"year": 1990})
    with pytest.raises(extras.ExtraInputError):
        extras.partner_cut(f, {})


def test_partner_works_without_the_partners_hour(f):
    """상대 시각을 모르는 경우가 더 흔합니다. 시주를 지어내지 않습니다."""
    cut = extras.partner_cut(f, {"year": 1990, "month": 8, "day": 3,
                                 "sex": "M", "hour_known": False})
    assert cut["html"]


def test_partner_is_deterministic(f):
    a = extras.partner_cut(f, PARTNER)
    b = extras.partner_cut(f, PARTNER)
    assert a["statement_id"] == b["statement_id"]
    assert a["html"] == b["html"]


# ══════════════════════════════════════════════════════════
# 맥락 — 고르는 값만 받는다
# ══════════════════════════════════════════════════════════
def test_context_rejects_free_text(f):
    """
    자유 입력을 받지 않는다.

    ★ 자유 입력은 개인정보가 섞여 들어오고, 가드가 못 보는 텍스트가
      리포트에 실릴 길을 냅니다. 고르는 값만 받습니다.
    """
    with pytest.raises(extras.ExtraInputError):
        extras.context_cut(f, {"situation": "회사에서 김부장이 저를",
                               "stance": "hold", "since_months": 3})
    with pytest.raises(extras.ExtraInputError):
        extras.context_cut(f, {"situation": "job", "stance": "아무거나",
                               "since_months": 3})


def test_context_covers_every_choice(f):
    """화면이 보여주는 선택지가 전부 컷을 만들 수 있어야 한다."""
    c = extras.choices()
    for sit in c["situation"]:
        for st in c["stance"]:
            cut = extras.context_cut(
                f, {"situation": sit["id"], "stance": st["id"],
                    "since_months": 7})
            ok, hits = guard.check(cut["html"])
            assert ok, (sit["id"], st["id"], hits)


def test_context_says_it_tires_you_not_that_it_fails(f):
    """
    '넘치는 기운을 더 쓰는' 경우에도 안 될 일이라 말하지 않는다.
    빨리 지친다고 말하고 쉬는 자리를 두라고 합니다.
    """
    T = extras.text()
    assert "안 될 일이라는 게 아니라" in T["SITUATION_FIT"]["과잉"]


# ══════════════════════════════════════════════════════════
# 검사 · 술수
# ══════════════════════════════════════════════════════════
def test_blood_says_it_is_not_evidence_first(f):
    """
    혈액형은 근거가 아니라고 **먼저** 말한다.
    재미 상품이라도 근거를 지어내지는 않습니다.
    """
    cut = extras.blood_cut(f, {"type": "A"})
    body = cut["html"]
    assert "근거가 아닙니다" in body
    assert body.index("근거가 아닙니다") < body.index("A형")
    # 표시광고법 — 검증 불가능한 주장 금지
    for banned in ("과학적", "통계", "적중률", "입증"):
        assert banned not in body, banned


@pytest.mark.parametrize("t", ["A", "B", "O", "AB"])
def test_every_blood_type_works(f, t):
    assert extras.blood_cut(f, {"type": t})["html"]


def test_blood_rejects_nonsense(f):
    with pytest.raises(extras.ExtraInputError):
        extras.blood_cut(f, {"type": "Z"})


def test_image_covers_every_choice(f):
    for im in extras.choices()["image"]:
        cut = extras.image_cut(f, {"pick": im["id"]})
        ok, _ = guard.check(cut["html"])
        assert ok, im["id"]


def test_cards_need_exactly_three(f):
    with pytest.raises(extras.ExtraInputError):
        extras.cards_cut(f, {"picks": ["gil", "mun"]})
    with pytest.raises(extras.ExtraInputError):
        extras.cards_cut(f, {"picks": ["gil", "mun", "san", "mul"]})
    with pytest.raises(extras.ExtraInputError):
        extras.cards_cut(f, {"picks": ["gil", "mun", "없는패"]})


def test_cards_say_the_draw_is_not_fixed(f):
    """패로 정해진 것을 읽지 않는다 — 글자는 안 바뀌고 패는 바뀝니다."""
    cut = extras.cards_cut(f, {"picks": ["gil", "mun", "san"]})
    assert "뽑을 때마다 바뀌" in cut["html"]


def test_choices_ship_no_sentences():
    """화면에는 id 와 라벨만. 문장 원문은 안 내려보냅니다 (docs/02 §7)."""
    import json
    raw = json.dumps(extras.choices(), ensure_ascii=False)
    T = extras.text()
    for v in T["SITUATION"].values():
        assert v["t"] not in raw
    for v in T["IMAGE"].values():
        assert v["t"] not in raw
    for v in T["CARD"].values():
        assert v["t"] not in raw


# ══════════════════════════════════════════════════════════
# 두 번째 결제 — 진짜 다른 상품인가
# ══════════════════════════════════════════════════════════
def test_extra_input_actually_changes_the_report(f):
    """
    ★ 이게 이 모듈이 생긴 이유입니다.
      추가 입력이 없으면 캐릭터를 바꿔도 리포트는 순서만 바뀝니다.
      여덟 글자는 하나뿐이니까요.
    """
    plain = build_report(f, "cid", "wolha", "all", "love", "INFP")
    withx = build_report(f, "cid", "wolha", "all", "love", "INFP",
                         {"partner": PARTNER})
    plain_html = "".join(c["html"] for c in plain["cuts"])
    with_html = "".join(c["html"] for c in withx["cuts"])
    assert len(with_html) > len(plain_html)
    assert plain["report_id"] == withx["report_id"], (
        "report_id 는 명식·캐릭터·티어·고민으로만 정합니다")


def test_different_partners_give_different_reports(f):
    a = extras.partner_cut(f, PARTNER)
    b = extras.partner_cut(f, {"year": 1985, "month": 2, "day": 20,
                               "hour": 6, "minute": 30, "sex": "M",
                               "hour_known": True})
    assert a["html"] != b["html"]


# ══════════════════════════════════════════════════════════
# 만남 — 누구랑, 어떻게 만났는가
# ══════════════════════════════════════════════════════════
#
# ★ 손님이 짚은 것 (2026-09-04)
#
#   "연애 고민이면 누구랑 고민인지 어떻게 만났는지 그런 거 싹 해서…"
#
#   재 보니 그걸 받는 칸이 아예 없었습니다. `partner` 는 상대의
#   생년월일만 받고, `context` 의 여덟 칸에는 만난 결이 없었습니다.
#
# ★ 맞히지 않고 **맞대 봅니다**
#
#   여덟 글자로 만난 경위를 뽑을 수는 없습니다. 다만 짝을 보는
#   글자가 어느 궁에 앉았는지는 이미 셈이 끝나 있어, 적으신 결과
#   겹치는지 어긋나는지는 볼 수 있습니다 — 넉 자를 대 보는 것과
#   같은 구조입니다.

MEET = {"who": "now", "how": "work"}


def test_만난_결은_정해진_칸으로만_받는다(f):
    """
    자유 입력은 개인정보가 섞이고 가드를 우회합니다 (CLAUDE.md).
    표에 없는 열쇠는 **터뜨립니다** — 빈칸을 두지 않습니다.
    """
    extras.meet_cut(f, MEET)          # 표에 있는 것은 서고
    for bad in ({"who": "그냥 아는 사람", "how": "work"},
                {"who": "now", "how": "소개팅 앱"},
                {"who": "now"}, {"how": "work"}, {}):
        with pytest.raises(extras.ExtraInputError):
            extras.meet_cut(f, bad)


def test_재회는_판정하지_않는다(f):
    """
    ★ 재회 상품은 **재회 가능/불가 판정 · 시점 확정 · 기다림 종용**이
      금지입니다 (CLAUDE.md 절대 규칙 3 · docs/11).

      「헤어진 사람」을 골라도 다시 될지 안 될지를 말하지 않습니다.
      그대 자리만 봅니다.
    """
    cut = extras.meet_cut(f, {"who": "past", "how": "again"})
    body = re.sub(r"<[^>]+>", "", cut["html"])
    assert "말하지 않" in body, "재회를 판정하지 않는다고 말해야 하오"
    for bad in ("다시 만나", "돌아오", "기다리", "재회할", "이어질 것"):
        assert bad not in body, "재회를 점쳤소: %s" % bad
    ok, hits = guard.check(body)
    assert ok, hits


def test_적은_것과_글자를_맞대_본다(f):
    """
    겹치면 겹친다고, 어긋나면 어긋난다고 말해야 합니다. 무엇을 골라도
    같은 말이 나오면 그건 대 본 것이 아니라 **적어 둔 것**입니다.
    """
    got = {how: extras.meet_cut(f, {"who": "now", "how": how})["html"]
           for how in ("long", "work", "intro", "chance", "far", "again")}
    assert len(set(got.values())) >= 2, "무엇을 골라도 같은 말이 나오오"
    # 근거 줄에 **짝 글자가 앉은 자리**가 적혀 있어야 합니다
    src = extras.meet_cut(f, MEET)["source"]
    assert "적은 결" in src, src


def test_상대의_이름도_생년월일도_안_받는다():
    """
    ★ 여기서 받는 것은 **그대와 그 자리의 결**뿐입니다. 상대의
      생년월일은 `partner` 가 따로 받고 그것도 저장하지 않습니다.
    """
    ch = extras.choices()
    assert "meet_who" in ch and "meet_how" in ch
    flat = json.dumps(ch, ensure_ascii=False)
    for bad in ("year", "생년", "이름", "연락"):
        assert bad not in flat, bad


def test_만난_결도_저장하지_않는다고_적혀_있다(f):
    body = re.sub(r"<[^>]+>", "", extras.meet_cut(f, MEET)["html"])
    assert "남기지 않" in body or "버리오" in body
