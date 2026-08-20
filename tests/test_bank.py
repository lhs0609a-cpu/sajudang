"""
문장엔진 테스트 — 훅 5단 · 가드 · 릴레이 · 리포트.

여기서 지키는 규칙 (CLAUDE.md 절대 규칙)
    · 뱅크 원문·조건식은 응답에 넣지 않는다
    · 공감률은 실응답 100건 전에는 내보내지 않는다
    · 2.5단은 불일치가 있을 때만 넣는다
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


def test_hook_without_axis4_drops_the_gap_stage(f):
    stages = [s["stage"] for s in bank.build_hook(f, "love")]
    assert "2.5" not in stages
    assert len(stages) == 4


def test_hook_with_matching_axis4_drops_the_gap_stage(f):
    """어긋난 데가 없으면 2.5단을 아예 넣지 않는다 (빈 칸을 만들지 않는다)."""
    same = bank.axis_string(f)
    stages = [s["stage"] for s in bank.build_hook(f, "love", same)]
    assert "2.5" not in stages


def test_hook_works_for_every_concern(f):
    for c in CONCERNS:
        segs = bank.build_hook(f, c)
        assert len(segs) == 4
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
    assert ids[3].startswith("gap:")
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
    assert len(segs) == 4


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
