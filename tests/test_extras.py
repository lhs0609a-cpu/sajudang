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

import pytest

from engine import extras, guard, lens as lens_mod
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
    """
    rep = build_report(f, "cid", lens_id, "all", "love", "INFP")
    need = lens_mod.required_input(lens_id)
    if need in extras.BUILDERS:
        assert rep["needs_input"] == need
    else:
        assert rep["needs_input"] is None


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
