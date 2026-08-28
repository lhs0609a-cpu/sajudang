"""
문장엔진 테스트 — 훅 5단 · 가드 · 릴레이 · 리포트.

여기서 지키는 규칙 (CLAUDE.md 절대 규칙)
    · 뱅크 원문·조건식은 응답에 넣지 않는다
    · 공감률은 실응답 100건 전에는 내보내지 않고, 낼 때는 하한으로 낸다
    · 2.5단은 넉 자를 적었으면 넣는다 — 겹친 자리를 먼저 말한다
      (전에는 불일치가 있을 때만 넣었고, 그래서 넷이 다 맞는 6%에게
       아무 말도 하지 않았습니다)
    · 릴레이 규칙은 스무 명 전원에게 있고, 근거에 문턱을 쓰지 않는다
    · 브레이크는 설정으로 끌 수 없다
"""
from __future__ import annotations

import pytest

from engine import bank, guard, lens as lens_mod, relay as relay_engine
from engine.calendar import build_chart
from engine.features import build_features
from engine.report import build_report

CONCERNS = ["money", "work", "love", "people", "dir", "health"]


@pytest.fixture(scope="module")
def f():
    return build_features(build_chart(1993, 5, 15, 10, 20, "F"))


@pytest.fixture(scope="module")
def f_no_hour():
    return build_features(
        build_chart(1986, 6, 21, None, None, "F", hour_known=False))


# ══════════════════════════════════════════════════════════
# 훅 5단
# ══════════════════════════════════════════════════════════
def test_hook_has_all_stages(f):
    segs = bank.build_hook(f, "love", "INFP")
    assert [s["stage"] for s in segs] == ["0", "1", "2", "2.5", "3"]


def test_hook_without_axis4_still_gets_a_25_stage(f):
    """
    ★ 규칙이 바뀐 자리입니다.
      전에는 넉 자를 안 적으면 2.5단을 통째로 뺐습니다. 재보니 그게
      **16.4%** 였고, 하필 훅에서 유일하게 손님이 낸 것과 여덟 글자를
      맞붙이는 자리였습니다 — 가장 "나에 대한 말" 처럼 읽히는 대목이
      조건부였던 것입니다.

      넉 자가 없어도 손님이 낸 것이 하나 더 있습니다: **고민**.
      물은 자리와 글자가 센 자리를 나란히 놓습니다.
    """
    segs = bank.build_hook(f, "love")
    stages = [s["stage"] for s in segs]
    assert stages == ["0", "1", "2", "2.5", "3"]
    seg = next(s for s in segs if s["stage"] == "2.5")
    assert seg["statement_id"].startswith("cax:")
    assert seg["source"], "대체 단에도 근거가 붙어야 합니다"


def test_hook_with_matching_axis4_still_speaks(f):
    """
    넉 자가 다 겹쳐도 2.5단을 넣는다.

    ★ 규칙이 바뀐 자리입니다.
      전에는 어긋난 데가 없으면 단을 통째로 뺐습니다. 그런데 이진 축
      넷이 다 맞을 확률은 잘해야 6%라, 그 규칙은 **가장 드문 사람에게
      침묵**하는 것이었습니다. 지금은 겹친 자리를 말합니다.
    """
    same = bank.axis_string(f)
    segs = bank.build_hook(f, "love", same)
    seg = next(s for s in segs if s["stage"] == "2.5")
    assert "겹" in seg["html"]
    assert seg["statement_id"] == "axis:4:%s:-:%s" % (same, f.strength)


def test_deep_reading_only_for_three_or_more_gaps(f):
    """
    깊은 해석은 셋 이상 어긋난 사람에게만.

    ★ 전에는 94%가 이 해석을 받았습니다. 넷 중 하나만 어긋나도
      "오래 눌러온 것입니다" 라고 단정하던 자리입니다.
    """
    same = bank.axis_string(f)
    flip = {"E": "I", "I": "E", "S": "N", "N": "S",
            "T": "F", "F": "T", "J": "P", "P": "J"}

    def axis4_with(n_gaps):
        return "".join(flip[c] if i < n_gaps else c
                       for i, c in enumerate(same))

    for n in range(5):
        cmp = bank.axis_compare(f, axis4_with(n))
        assert len(cmp["gaps"]) == n
        assert cmp["deep"] is (n >= bank.GAP_DEEP_AT)
        html = bank.axis_block(cmp)
        deep_lines = [g["w"] for g in cmp["gaps"]]
        for w in deep_lines:
            assert (w in html) is cmp["deep"]


def test_gap_interpretation_never_asserts_the_past():
    """
    지난 일을 확인 없이 단정하지 않는다 (CLAUDE.md 절대 규칙 2).

    ★ "드러나는 기질을 오래 눌러온 것입니다" 가 그 위반이었습니다.
    """
    for pair, g in bank.bank()["GAP"].items():
        w = g["w"]
        assert ("수 있습니다" in w or "수 있소" in w), (pair, w)
        assert "것입니다." not in w, (pair, w)


def test_hook_works_for_every_concern(f):
    for c in CONCERNS:
        segs = bank.build_hook(f, c)
        assert len(segs) == 5
        assert all(s["html"] for s in segs)


def test_hook_rejects_unknown_concern(f):
    with pytest.raises(bank.BankError):
        bank.build_hook(f, "money2")


def test_statement_ids_are_stable_and_keyed(f):
    segs = bank.build_hook(f, "love", "INFP")
    ids = [s["statement_id"] for s in segs]
    assert ids[0].startswith("stab:")
    assert ids[1].startswith("myth:")
    assert ids[2].startswith("seq:")
    assert ids[3].startswith("axis:")
    assert ids[4].startswith("name:")
    # 같은 입력이면 같은 id
    assert [s["statement_id"] for s in bank.build_hook(f, "love", "INFP")] == ids


def test_hook_never_ships_an_agreement_number(f):
    """
    공감률은 실응답 100건 전에는 화면에 못 띄운다.
    참조 구현체는 해시로 만든 예시 숫자를 뿌리는데, 그건 옮겨오지 않았다.
    """
    for s in bank.build_hook(f, "love", "INFP"):
        assert "%" not in s["html"]
        assert "명이" not in s["html"] and "명 중" not in s["html"]


def test_hook_escapes_user_name(f):
    segs = bank.build_hook(f, "love", name="<script>x</script>")
    assert "<script>" not in segs[0]["html"]
    assert "&lt;script&gt;" in segs[0]["html"]


def test_you_word_follows_the_lens(f):
    assert "자네" in bank.build_hook(f, "love", you=lens_mod.you_word("nopa"))[1]["html"]
    assert "아저씨" in bank.build_hook(f, "love", you=lens_mod.you_word("dongja"))[1]["html"]


def test_hook_works_without_hour(f_no_hour):
    segs = bank.build_hook(f_no_hour, "work")
    assert len(segs) == 5


def test_saju_axis_is_four_letters(f):
    a = bank.axis_string(f)
    assert len(a) == 4
    assert a[0] in "EI" and a[1] in "SN" and a[2] in "TF" and a[3] in "JP"


def test_gap_list_empty_for_bad_axis4(f):
    assert bank.gap_list(f, None) == []
    assert bank.gap_list(f, "INF") == []


def test_josa():
    assert bank.josa("나무", "이", "가") == "나무가"
    assert bank.josa("불", "이", "가") == "불이"
    assert bank.josa("흙", "은", "는") == "흙은"
    assert bank.josa("쇠", "은", "는") == "쇠는"


# ══════════════════════════════════════════════════════════
# 가드
# ══════════════════════════════════════════════════════════
@pytest.mark.parametrize("bad", [
    "이 시기에 반드시 옵니다",
    "그 사람과는 이혼합니다",
    "우울증이 올 수 있소",
    "적중률 92% 입니다",
    "3월까지 기다리시오",
    "수술 날을 잡아드리리다",
    "주식은 지금 사시오",
])
def test_guard_blocks(bad):
    ok, hits = guard.check(bad)
    assert not ok and hits


def test_guard_passes_normal_sentences():
    ok, _ = guard.check("그대는 늘 이 순서요. 붙들고 놓지 못하고, 끊어낼 칼이 없다.")
    assert ok


def test_guard_enforce_falls_back_when_unfixable():
    out = guard.enforce("우울증이 옵니다")
    assert out == guard.SAFE_FALLBACK


def test_guard_scan_walks_nested():
    hits = guard.scan({"a": ["ok", {"b": "적중률 92%"}]})
    assert len(hits) == 1
    assert hits[0]["path"] == "$.a[1].b"


def test_every_hook_sentence_passes_guard(f):
    for c in CONCERNS:
        for s in bank.build_hook(f, c, "INFP"):
            ok, hits = guard.check(s["html"])
            assert ok, (c, s["statement_id"], hits)


# ══════════════════════════════════════════════════════════
# 릴레이
# ══════════════════════════════════════════════════════════
def test_relay_sorted_by_priority(f):
    out = relay_engine.evaluate(f)
    assert out == sorted(out, key=lambda x: -x["priority"])


def test_relay_excludes_read_and_skipped(f):
    first = relay_engine.evaluate(f)[0]["lens_id"]
    assert all(x["lens_id"] != first
               for x in relay_engine.evaluate(f, read=[first]))
    assert all(x["lens_id"] != first
               for x in relay_engine.evaluate(f, skipped=[first]))


def test_relay_returns_at_most_three(f):
    assert len(relay_engine.recommend(f)["recommend"]) <= relay_engine.TOP_N


def test_relay_blocks_at_session_limit(f):
    limit = relay_engine.BREAKS()["per_session_relay"]
    out = relay_engine.recommend(f, session_relay_count=limit)
    assert out["blocked"] is True
    assert out["recommend"] == []


def test_breaks_cannot_be_loosened_by_seed():
    """시드를 고쳐 브레이크를 풀 수 없어야 한다."""
    b = relay_engine.BREAKS()
    assert b["per_session_relay"] <= 2
    assert b["per_day_purchase"] <= 2
    assert b["reunion_cooldown_days"] >= 7
    assert b["visit_warn_at"] <= 3


def test_forced_safety_net_after_heavy_lens(f):
    """노파·연담 다음에는 무료 캐릭터(청동자)를 강제로 앞에 붙인다."""
    out = relay_engine.recommend(f, last_lens="nopa")
    assert out["forced"] == ["dongja"]
    assert all(x["lens_id"] != "dongja" for x in out["recommend"])


def test_relay_reason_is_filled_in(f):
    for x in relay_engine.evaluate(f):
        assert "{" not in x["reason"], x


def test_relay_rules_only_use_known_fields(f):
    # 모르는 필드를 쓰는 규칙이 있으면 여기서 터진다
    relay_engine.evaluate(f)


# ══════════════════════════════════════════════════════════
# 리포트
# ══════════════════════════════════════════════════════════
def test_report_locks_by_tier(f):
    free = build_report(f, "cid", "pungun", "free", "love", "INFP")
    all_ = build_report(f, "cid", "pungun", "all", "love", "INFP")
    assert free["locked"], "무료에는 잠긴 컷이 있어야 합니다"
    assert not all_["locked"]
    assert len(all_["cuts"]) > len(free["cuts"])


def test_locked_cuts_do_not_leak_their_body(f):
    free = build_report(f, "cid", "pungun", "free", "love")
    for l in free["locked"]:
        assert "html" not in l


def test_report_id_is_deterministic(f):
    a = build_report(f, "cid", "pungun", "all", "love")["report_id"]
    b = build_report(f, "cid", "pungun", "all", "love")["report_id"]
    assert a == b


def test_report_cuts_pass_guard(f):
    for tier in ("free", "one", "all"):
        for cut in build_report(f, "cid", "pungun", tier, "love", "INFP")["cuts"]:
            ok, hits = guard.check(cut["html"])
            assert ok, (tier, cut["id"], hits)


def test_report_without_hour_marks_three_pillars(f_no_hour):
    rep = build_report(f_no_hour, "cid", "pungun", "all", "work")
    chart_cut = next(c for c in rep["cuts"] if c["id"] == "chart")
    assert "세 기둥으로 계산" in chart_cut["html"]


# ══════════════════════════════════════════════════════════
# 릴레이 — 규칙 20개 · 재순위 · 문턱 감추기
# ══════════════════════════════════════════════════════════
def test_every_lens_has_a_rule():
    """
    스무 명 전원에게 조건이 있어야 한다.

    ★ 규칙이 없으면 그 캐릭터는 릴레이에 **한 번도** 안 나옵니다.
      전에 열 명이 그 상태였습니다. 스무 명을 만든 뜻이 없어집니다.
    """
    ruled = {r["lens_id"] for r in relay_engine.rules()}
    missing = sorted({l["id"] for l in lens_mod.all_lenses()} - ruled)
    assert not missing, "규칙이 없는 캐릭터: %s" % ", ".join(missing)


def test_no_rule_catches_everyone():
    """
    누구에게나 걸리는 규칙은 추천이 아니라 배경이다.

    ★ `always` 조건은 재순위에서 늘 꼴찌가 되어 그 캐릭터가 영영 안
      팔립니다. 근거를 못 찾은 사람에게는 규칙이 아니라 무료 캐릭터를
      세웁니다 (relay.FALLBACK_LENS).
    """
    for r in relay_engine.rules():
        assert r["condition"]["field"] != "always", r["id"]


def test_reason_never_leaks_the_threshold():
    """
    근거는 보이되 규칙은 감춘다.

    ★ 전에는 `근거 · 목 0.0 ≤ 1.0` 을 화면에 그대로 렌더했습니다.
      `목 0.0` 은 그 사람의 명식이라 보여도 되지만 `≤ 1.0` 은 우리
      분기표입니다. 문턱이 새면 규칙을 역산할 수 있습니다.
    """
    banned = ["<=", ">=", "!=", "==", "≤", "≥", " < ", " > "]
    for r in relay_engine.rules():
        for b in banned:
            assert b not in r["reason"], (r["id"], b, r["reason"])


def test_rendered_reason_is_clean(f, f_no_hour):
    banned = ["<=", ">=", "≤", "≥", "condition", "priority"]
    for feats in (f, f_no_hour):
        for it in relay_engine.evaluate(feats):
            for b in banned:
                assert b not in it["reason"], (it["rule_id"], b, it["reason"])


def test_recommend_hides_the_ranking_internals(f):
    out = relay_engine.recommend(f)
    for it in out["recommend"]:
        assert set(it) == set(relay_engine.PUBLIC_FIELDS)
        for k in ("rule_id", "priority", "reach", "score"):
            assert k not in it


def test_stored_reach_matches_the_rules():
    r"""
    저장된 도달률이 규칙과 어긋나면 재순위가 헛돈다.

    ★ 규칙을 고치면 이 테스트가 먼저 알려줍니다.
      그때 `.\dev.ps1 reach --write` 를 다시 돌리세요.
    """
    for r in relay_engine.rules():
        assert r.get("reach") is not None, (
            r"%s 에 도달률이 없습니다 — .\dev.ps1 reach --write" % r["id"])
        assert 0.0 <= r["reach"] <= 1.0, r["id"]


def test_rerank_beats_priority_only_at_spreading(f):
    """재순위가 실제로 순서를 바꾸는가 — 안 바뀌면 붙인 뜻이 없다."""
    plain = [x["lens_id"] for x in relay_engine.evaluate(f)]
    ranked = [x["lens_id"] for x in relay_engine.rerank(relay_engine.evaluate(f))]
    assert sorted(plain) == sorted(ranked), "목록의 내용은 그대로여야 합니다"
    assert plain != ranked, "재순위가 순서를 전혀 안 바꿉니다"


def test_complement_prefers_what_the_last_one_muted():
    """앞 캐릭터가 뒤로 민 자리를 앞세우는 캐릭터가 점수를 더 받는가."""
    muted = set(lens_mod.view("nopa")["mute"])
    scorer = [l["id"] for l in lens_mod.all_lenses()
              if muted & set(lens_mod.view(l["id"])["focus"] or ())]
    assert scorer, "노파가 뒤로 민 자리를 보는 캐릭터가 하나도 없습니다"
    for lid in scorer:
        assert lens_mod.complement("nopa", lid) > 0
    assert lens_mod.complement("nopa", "nopa") == 0.0
    assert lens_mod.complement(None, "pungun") == 0.0


def test_fallback_is_free_and_appears_when_nothing_matches(f, monkeypatch):
    """근거를 못 찾았을 때 값을 받는 캐릭터를 권하면 그건 강매다."""
    assert lens_mod.get(relay_engine.FALLBACK_LENS)["price"] in (0, None)
    monkeypatch.setattr(relay_engine, "evaluate", lambda *a, **k: [])
    out = relay_engine.recommend(f)
    assert len(out["recommend"]) == 1
    assert out["recommend"][0]["lens_id"] == relay_engine.FALLBACK_LENS


# ══════════════════════════════════════════════════════════
# 공감률 — 점추정 대신 하한
# ══════════════════════════════════════════════════════════
def test_wilson_lower_is_below_the_point_estimate():
    import repo
    for hit, total in [(52, 100), (520, 1000), (900, 1000), (100, 100)]:
        lo = repo.wilson_lower(hit, total)
        assert lo < hit / total, (hit, total)
        assert 0.0 <= lo <= 1.0


def test_wilson_never_claims_a_hundred_percent():
    """
    100/100 을 '100%' 라 말하지 않는다.

    ★ 백 명이 다 그렇다고 했다고 해서 다음 사람도 그렇다는 뜻은
      아닙니다. 하한은 96.3% 쯤을 돌려줍니다.
    """
    import repo
    assert repo.wilson_lower(100, 100) < 1.0
    assert repo.wilson_lower(100, 100) > 0.9


def test_small_samples_are_punished_more():
    """52/100 과 520/1000 은 같은 52% 지만 확신의 크기가 다르다."""
    import repo
    small = repo.wilson_lower(52, 100)
    big = repo.wilson_lower(520, 1000)
    assert small < big
    assert big < 0.52


def test_wilson_handles_the_empty_case():
    import repo
    assert repo.wilson_lower(0, 0) == 0.0
    assert repo.wilson_lower(0, 10) == 0.0


# ══════════════════════════════════════════════════════════
# 추가 입력 — 결합 축
# ══════════════════════════════════════════════════════════
def test_every_lens_declares_its_extra_input():
    """
    docs/07 §결합 축이 정한 추가 입력이 시드에 적혀 있는가.

    ★ 문서에만 있으면 잊힙니다. 실제로 잊혀서 12명이 추가 입력 없이
      돌고 있었고, 그래서 두 번째 결제가 순서만 바뀐 같은 리포트였습니다.
    """
    by_group = {}
    for l in lens_mod.all_lenses():
        assert "input" in l, l["id"]
        by_group.setdefault(l["group"], set()).add(l["input"])
    # 추가 입력이 없는 것이 설계인 축
    assert by_group["정통"] == {None}
    assert by_group["정서"] == {None}
    # 나머지는 전부 무언가를 받아야 한다
    for g in ("검사", "술수", "관계", "맥락"):
        assert None not in by_group[g], g


def test_missing_inputs_are_counted_not_forgotten():
    """
    아직 안 붙인 추가 입력을 코드가 센다. 이 숫자가 늘면 알려준다.
    """
    missing = lens_mod.missing_inputs()
    ids = {m["lens_id"] for m in missing}
    # 못 붙이는 것은 이유가 적혀 있어야 한다
    for m in missing:
        assert m["reason"], m
    # 얼굴 사진은 생체인식정보라 저장이 금지돼 있다 — 이건 '아직' 이 아니다
    photo = [m for m in missing if m["input"] == "photo"]
    for m in photo:
        assert "생체인식" in m["reason"], m
    assert ids <= {l["id"] for l in lens_mod.all_lenses()}
