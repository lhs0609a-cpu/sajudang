"""
API 계층 테스트 — docs/02 §5

여기서 지키는 것
    · 문장 원문·뱅크 키·조건식이 응답에 새지 않는다
    · 계산할 수 없으면 지어내지 않고 거절한다
    · 브레이크가 실제로 막는다
    · 공감률은 100건 전에는 숫자를 주지 않는다
"""
from __future__ import annotations

import os
import tempfile

import pytest

os.environ.setdefault("STATEMENT_LOG_PATH",
                      os.path.join(tempfile.gettempdir(), "sajudang_test_log.jsonl"))

from fastapi.testclient import TestClient          # noqa: E402

import store                                       # noqa: E402
from main import app                               # noqa: E402

BIRTH = {"year": 1993, "month": 5, "day": 15, "hour": 10, "minute": 20,
         "hour_known": True, "sex": "F", "birth_city": "서울"}


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def chart_id(client):
    return client.post("/v1/chart", json=BIRTH).json()["chart_id"]


# ── /health ────────────────────────────────────────────────
def test_health(client):
    r = client.get("/health").json()
    assert r["ok"] is True
    assert r["tz_source"].startswith("tzdata"), "tzdata 없이 돌고 있습니다"


# ── /v1/chart ──────────────────────────────────────────────
def test_chart_returns_features(client):
    r = client.post("/v1/chart", json=BIRTH)
    assert r.status_code == 200
    f = r.json()["features"]
    assert [p["gz"] for p in f["pillars"]] == ["癸酉", "丁巳", "丙申", "癸巳"]


def test_chart_is_cached(client):
    client.post("/v1/chart", json=BIRTH)
    assert client.post("/v1/chart", json=BIRTH).json()["cached"] is True


def test_chart_rejects_hour_known_without_hour(client):
    bad = dict(BIRTH, hour=None, minute=None, hour_known=True)
    assert client.post("/v1/chart", json=bad).status_code == 422


def test_chart_rejects_out_of_range_year(client):
    assert client.post("/v1/chart", json=dict(BIRTH, year=1850)).status_code == 422


def test_chart_without_hour_returns_three_pillars(client):
    r = client.post("/v1/chart",
                    json=dict(BIRTH, hour=None, minute=None, hour_known=False))
    f = r.json()["features"]
    assert len(f["pillars"]) == 3
    assert f["correction"]["hour_used"] is False


# ── /v1/hook ───────────────────────────────────────────────
def test_hook_returns_segments(client, chart_id):
    r = client.post("/v1/hook", json={"chart_id": chart_id, "concern": "love",
                                      "axis4": "INFP", "lens_id": "pungun"})
    assert r.status_code == 200
    segs = r.json()["segments"]
    assert [s["stage"] for s in segs] == ["0", "1", "2", "2.5", "3"]
    assert all(s["statement_id"] for s in segs)


def test_hook_unknown_chart_id(client):
    r = client.post("/v1/hook", json={"chart_id": "nope", "concern": "love"})
    assert r.status_code == 404


def test_hook_response_carries_no_bank_internals(client, chart_id):
    """뱅크 표 이름·조건식이 응답에 새면 안 된다."""
    raw = client.post("/v1/hook",
                      json={"chart_id": chart_id, "concern": "love"}).text
    for leak in ("STAB", "IGNITE", "BLAME", "NAME2", "MYTH_TG", "IGKEY",
                 "priority", "condition"):
        assert leak not in raw, leak


# ── /v1/report ─────────────────────────────────────────────
def _mark_paid(session_id, tier, lens_id="pungun"):
    """이 세션이 값을 치른 것으로 기록한다. pay/confirm 이 쓰는 그 모양."""
    oid = "test-order-%s-%s-%s" % (session_id, tier, lens_id)
    store.set_json("order:" + oid, {
        "session_id": session_id, "chart_id": "x", "lens_id": lens_id,
        "tier": tier, "concern": "love", "amount": 1, "status": "paid",
        "payment_key": "t"})
    store.set_json("orders:" + session_id, [oid])


def test_report_tier_gating(client, chart_id):
    """티어가 오르면 더 열린다 — **값을 치렀을 때** 얘기다."""
    _mark_paid("t-gate-paid", "all")
    free = client.post("/v1/report", json={
        "chart_id": chart_id, "lens_id": "pungun", "tier": "free",
        "concern": "love"}).json()
    all_ = client.post("/v1/report", json={
        "chart_id": chart_id, "lens_id": "pungun", "tier": "all",
        "session_id": "t-gate-paid", "concern": "love"}).json()
    assert free["locked"] and not all_["locked"]
    assert len(all_["cuts"]) > len(free["cuts"])


def test_report_without_paying_stays_free(client, chart_id):
    """
    ★ 여기가 비어 있었습니다.

      리포트 본체가 클라이언트가 보낸 tier 를 그대로 믿어서, 값을 한 푼도
      안 치른 요청에 tier="one" 을 실으면 19컷 8,339자가 그대로 나갔습니다.
      화면은 그 값을 localStorage 에서 읽어 보냅니다 — 브라우저에서 한
      글자만 고치면 스무 캐릭터가 전부 열렸습니다.
    """
    free = client.post("/v1/report", json={
        "chart_id": chart_id, "lens_id": "pungun", "tier": "free",
        "concern": "love"}).json()
    for tier in ("one", "all", "sub"):
        got = client.post("/v1/report", json={
            "chart_id": chart_id, "lens_id": "pungun", "tier": tier,
            "session_id": "t-never-paid", "concern": "love"}).json()
        # 거절이 아니라 **낮춰서** 냅니다. 무료 구간은 보여야 합니다.
        assert got["tier"] == "free", tier
        assert len(got["cuts"]) == len(free["cuts"]), tier
        assert got["locked"], tier
        for c in got["locked"]:
            assert not c.get("html"), (tier, c["id"])


def test_report_without_session_stays_free(client, chart_id):
    """열쇠를 아예 안 보내도 마찬가지."""
    got = client.post("/v1/report", json={
        "chart_id": chart_id, "lens_id": "pungun", "tier": "all",
        "concern": "love"}).json()
    assert got["tier"] == "free"


def test_one_tier_opens_only_the_lens_that_was_paid(client, chart_id):
    """
    「이 자리 하나」는 그 캐릭터 값입니다. 4,900원짜리를 치르고
    19,900원짜리를 열 수는 없습니다.
    """
    _mark_paid("t-one-lens", "one", lens_id="paeseon")
    mine = client.post("/v1/report", json={
        "chart_id": chart_id, "lens_id": "paeseon", "tier": "one",
        "session_id": "t-one-lens", "concern": "love"}).json()
    other = client.post("/v1/report", json={
        "chart_id": chart_id, "lens_id": "pungun", "tier": "one",
        "session_id": "t-one-lens", "concern": "love"}).json()
    assert mine["tier"] == "one"
    assert other["tier"] == "free"


def test_all_tier_opens_every_lens(client, chart_id):
    """'여덟 글자 전부' 는 캐릭터를 안 가립니다."""
    _mark_paid("t-all-any", "all", lens_id="paeseon")
    for lens in ("paeseon", "pungun", "nopa"):
        got = client.post("/v1/report", json={
            "chart_id": chart_id, "lens_id": lens, "tier": "all",
            "session_id": "t-all-any", "concern": "love"}).json()
        assert got["tier"] == "all", lens


def test_unpaid_order_does_not_open_anything(client, chart_id):
    """주문만 만들고 승인 안 한 건은 자격이 아니다."""
    oid = "test-order-pending"
    store.set_json("order:" + oid, {
        "session_id": "t-pending", "lens_id": "pungun", "tier": "all",
        "status": "pending"})
    store.set_json("orders:t-pending", [oid])
    got = client.post("/v1/report", json={
        "chart_id": chart_id, "lens_id": "pungun", "tier": "all",
        "session_id": "t-pending", "concern": "love"}).json()
    assert got["tier"] == "free"


def test_report_unknown_lens(client, chart_id):
    r = client.post("/v1/report", json={
        "chart_id": chart_id, "lens_id": "없는캐릭터", "tier": "free",
        "concern": "love"})
    assert r.status_code == 404


# ── /v1/relay ──────────────────────────────────────────────
def test_relay_recommends_and_blocks(client, chart_id):
    store.clear_all()
    cid = client.post("/v1/chart", json=BIRTH).json()["chart_id"]
    body = {"chart_id": cid, "session_id": "t-block", "read": ["pungun"]}

    first = client.post("/v1/relay", json=body).json()
    assert first["blocked"] is False
    assert 1 <= len(first["recommend"]) <= 3

    limit = first["breaks"]["per_session_relay"]
    for _ in range(limit):
        client.post("/v1/relay/consume", params={"session_id": "t-block"})

    after = client.post("/v1/relay", json=body).json()
    assert after["blocked"] is True
    assert after["recommend"] == []
    assert after["block_reason"]


def test_relay_response_carries_no_condition(client, chart_id):
    raw = client.post("/v1/relay", json={"chart_id": chart_id,
                                         "session_id": "t-leak"}).text
    assert '"condition"' not in raw
    assert '"op"' not in raw


# ── /v1/feedback · /v1/agreement ───────────────────────────
def test_feedback_records(client, chart_id):
    r = client.post("/v1/feedback", json={
        "statement_id": "stab:love:목", "chart_id": chart_id,
        "answer": 1, "stage": "0", "concern": "love"})
    assert r.status_code == 200 and r.json()["ok"] is True


def test_agreement_hidden_below_threshold(client, chart_id):
    r = client.get("/v1/agreement", params={"statement_id": "seed:none"}).json()
    assert r["shown"] is False
    assert "rate" not in r
    assert r["min_responses"] >= 100


def test_feedback_rejects_bad_answer(client, chart_id):
    r = client.post("/v1/feedback", json={
        "statement_id": "x", "chart_id": chart_id, "answer": 7})
    assert r.status_code == 422


# ── /v1/daily ──────────────────────────────────────────────
def test_daily(client, chart_id):
    r = client.get("/v1/daily", params={"chart_id": chart_id}).json()
    assert len(r["gz"]) == 2
    assert 12 <= r["score"] <= 96
    assert r["text"]


# ── 가드 미들웨어 ───────────────────────────────────────────
def test_guard_middleware_catches_a_leaking_route(client):
    """새 라우터가 enforce 를 빠뜨려도 미들웨어가 잡는다."""
    from fastapi import APIRouter

    r = APIRouter()

    @r.get("/_test/leak")
    def leak() -> dict:
        return {"text": "적중률 92% 입니다"}

    app.include_router(r)
    try:
        got = client.get("/_test/leak").json()
        assert "적중률 92%" not in got["text"]
    finally:
        app.router.routes = [
            x for x in app.router.routes
            if getattr(x, "path", None) != "/_test/leak"]


# ══════════════════════════════════════════════════════════
# 잠긴 컷의 첫 줄 — 맛보기가 본문이 되지 않는가
# ══════════════════════════════════════════════════════════
#
# ★ 여기가 무방비였습니다.
#   페이월이 자리표시 문자열(`가가가가 가가가가가 가가가`)을 그리다가
#   서버가 진짜 첫 줄을 내려보내게 바뀌었는데, **얼마나 주는지를
#   아무도 안 세고 있었습니다.** 맛보기는 값을 치를지 정하게 하는
#   것이지 값을 안 치르고도 되게 하는 것이 아닙니다.
def _locked(client, chart_id, lens_id="pungun"):
    r = client.post("/v1/report", json={
        "chart_id": chart_id, "lens_id": lens_id, "tier": "free",
        "concern": "love"}).json()
    assert r["locked"], "무료로 보면 잠긴 자리가 있어야 합니다"
    return r["locked"]


def test_locked_cut_never_carries_the_body(client, chart_id):
    """본문은 여전히 안 내려간다. 블러로 가린 게 아니라 서버가 안 준다."""
    for l in _locked(client, chart_id):
        assert "html" not in l, l


def test_teaser_is_a_real_prefix_of_the_cut(client, chart_id):
    """
    맛보기는 **그 컷의 첫 줄**이어야 한다 — 지어낸 문장이면 안 된다.

    본문에 없는 말을 맛보기로 내면 그건 값을 치르기 전에 하는 약속인데,
    치른 뒤에 그 문장이 없습니다.
    """
    from engine.features import Features
    from engine.report import _plain, build_report
    from routers.chart import load_features

    f = Features(**load_features(chart_id))
    full = build_report(f, chart_id, "pungun", "all", "love")
    body = {c["id"]: _plain(c["html"]) for c in full["cuts"]}

    seen = 0
    for l in _locked(client, chart_id):
        if not l.get("teaser"):
            continue
        seen += 1
        head = l["teaser"].rstrip(" —")
        assert body[l["id"]].startswith(head), l["id"]
    assert seen, "맛보기가 한 줄도 안 나왔습니다"


def test_teaser_never_gives_away_the_cut(client, chart_id):
    """
    맛보기가 본문의 40%를 넘지 않는다.

    ★ 짧은 컷이 위험합니다. 100자짜리 컷에 44자를 주면 그건 맛보기가
      아니라 본문의 절반입니다. 한도가 두 개인 이유입니다 —
      글자 수(TEASER_MAX)와 **비율**(TEASER_SHARE).
    """
    from engine.report import TEASER_MAX, TEASER_SHARE

    for l in _locked(client, chart_id):
        if not l.get("teaser"):
            continue
        assert l["chars"] > 0, l
        assert len(l["teaser"]) <= TEASER_MAX + 8, l
        assert len(l["teaser"]) <= l["chars"] * TEASER_SHARE + 8, l


def test_teaser_does_not_break_mid_particle(client, chart_id):
    """
    조사에서 끊긴 채로 내보내지 않는다.

    "그대의 대운이" 에서 끊기면 문장이 잘린 게 아니라 망가진 것처럼
    보입니다. 맛보기가 성의 없어 보이면 값을 치를 마음이 사라집니다.
    """
    from engine.report import _BAD_TAIL

    for l in _locked(client, chart_id):
        t = (l.get("teaser") or "").rstrip(" —")
        if not t or t[-1] in ".!?…":
            continue
        assert t[-1] not in _BAD_TAIL, l["teaser"]


def test_locked_cut_names_the_tier_in_the_words_the_shop_uses(client, chart_id):
    """
    ★ 이름이 두 벌이면 어긋납니다.

      `all` 을 "여덟 글자 전부" 에서 "스무 사람 전부" 로 고쳤을 때
      목패는 따라왔는데 페이월은 옛 이름을 계속 불렀습니다. 같은 상품을
      두 화면이 다른 이름으로 부르고 있었던 것입니다.
      이제 이름은 payments.TIER_NAME 한 곳에 있고 서버가 실어 보냅니다.
    """
    import payments

    for l in _locked(client, chart_id):
        assert l["need_tier_name"] == payments.TIER_NAME[l["need_tier"]], l


# ══════════════════════════════════════════════════════════
# /v1/review — 받는 척만 하고 버리던 자리
# ══════════════════════════════════════════════════════════
@pytest.fixture
def review_log(tmp_path, monkeypatch):
    import repo
    p = tmp_path / "reviews.jsonl"
    monkeypatch.setattr(repo, "REVIEW_PATH", p)
    return p


def test_review_is_actually_stored(client, review_log):
    r = client.post("/v1/review", json={
        "lens_id": "pungun", "rating": 4, "body": "재미있게 읽었소."})
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True
    assert review_log.exists(), "후기가 저장되지 않았습니다"
    assert "재미있게" in review_log.read_text(encoding="utf-8")


def test_review_needs_a_star_or_a_word(client, review_log):
    r = client.post("/v1/review", json={"lens_id": "pungun", "body": "   "})
    assert r.status_code == 422


def test_review_rejects_an_unknown_lens(client, review_log):
    r = client.post("/v1/review", json={"lens_id": "없는사람", "rating": 5})
    assert r.status_code == 404


def test_review_is_verified_only_when_the_order_was_paid(client, review_log):
    """
    '결제 확인됨' 은 **치른 주문**이 정한다. 화면이 하는 말이 아니다.
    (표시광고법 · docs/11)
    """
    unpaid = client.post("/v1/review", json={
        "lens_id": "pungun", "rating": 5, "session_id": "rv-unpaid",
        "body": "좋소"}).json()
    assert unpaid["verified"] is False

    _mark_paid("rv-paid", "one", "pungun")
    paid = client.post("/v1/review", json={
        "lens_id": "pungun", "rating": 5, "session_id": "rv-paid",
        "body": "좋소"}).json()
    assert paid["verified"] is True


def test_review_scrubs_contact_details(client, review_log):
    """
    ★ 자유 입력이라 손님이 무심코 적습니다. 보관할 이유가 없습니다.
    """
    client.post("/v1/review", json={
        "lens_id": "pungun", "rating": 5,
        "body": "연락 주시오 010-1234-5678 me@example.com"})
    saved = review_log.read_text(encoding="utf-8")
    assert "1234-5678" not in saved
    assert "example.com" not in saved
    assert "[번호]" in saved and "[메일]" in saved


def test_review_that_trips_the_guard_is_kept_but_hidden(client, review_log):
    """
    지우지는 않습니다 — 손님이 실제로 한 말이라 우리 쪽에서는 읽어야
    합니다. 다만 화면에는 안 나갑니다. 그 사실을 손님에게도 말합니다.
    """
    r = client.post("/v1/review", json={
        "lens_id": "pungun", "rating": 1,
        "body": "적중률 99% 라더니 아니었소"}).json()
    assert r["ok"] is True
    assert r["visible"] is False
    assert r["say"]
    assert "적중률" in review_log.read_text(encoding="utf-8")


def test_review_stats_count_what_was_left(client, review_log):
    import repo

    for n in (5, 3):
        client.post("/v1/review", json={"lens_id": "yeondam", "rating": n})
    st = repo.review_stats("yeondam")
    assert st["count"] == 2
    assert st["average"] == 4.0


# ══════════════════════════════════════════════════════════
# /v1/daily — 부정만 하고 정의를 안 주던 수
# ══════════════════════════════════════════════════════════
def test_daily_score_shows_its_arithmetic(client, chart_id):
    """
    ★ 화면이 "적중률이 아니라 배치 점수요" 라고만 적고 있었습니다.
      아닌 것만 말하고 무엇인지는 안 말하면, 손님에게 76은 아무 뜻도
      없는 수입니다. 여기는 근거 대는 집이니 셈법을 펴 보입니다.

      **더한 것이 그대로 점수여야 합니다.** 안 그러면 펴 보인 셈법이
      거짓말이 됩니다.
    """
    r = client.get("/v1/daily", params={"chart_id": chart_id}).json()
    assert r["score_says"]
    assert r["score_why"], "셈법이 비어 있습니다"
    assert sum(w["v"] for w in r["score_why"]) == r["score"]
    for w in r["score_why"]:
        assert w["k"] and w["t"], w
        # 근거 줄에 연산자·문턱값을 쓰지 않습니다 (CLAUDE.md)
        assert "<=" not in w["t"] and "≤" not in w["t"], w


# ══════════════════════════════════════════════════════════
# 훅이 응답에 따라 방향을 트는가
# ══════════════════════════════════════════════════════════
#
# ★ 여기가 비어 있었습니다.
#   손님의 응답이 즉답 한 줄만 바꾸고, 다음 단의 본문은 응답과 무관하게
#   똑같이 나왔습니다. 세 번 "아니오" 를 눌러도 도령이 한 번도 방향을
#   안 틀었습니다 — 그 순간 손님은 이게 녹음이라는 걸 압니다.
def _hook(client, chart_id, misses=0):
    r = client.post("/v1/hook", json={
        "chart_id": chart_id, "concern": "love", "axis4": "INFP",
        "misses": misses})
    assert r.status_code == 200, r.text
    return {s["stage"]: s for s in r.json()["segments"]}


def test_hook_turns_the_axis_after_two_misses(client, chart_id):
    from engine import bank

    before = _hook(client, chart_id, 0)["2"]
    after = _hook(client, chart_id, bank.TURN_AT)["2"]

    assert before["html"] != after["html"], "방향을 안 틀었습니다"
    assert "십신으로 짚던 것을 접고" in after["html"]
    # 튼 단은 다른 문장으로 집계돼야 합니다 — 어긋난 축을 버리는 신호입니다
    assert after["statement_id"] != before["statement_id"]
    assert "@turn" in after["statement_id"]
    # 근거도 바뀐 축을 말해야 합니다. 십신을 접었다면서 근거에 십신이
    # 그대로 있으면 손님이 바로 알아봅니다.
    assert "생 ·" in after["source"]


def test_hook_does_not_turn_before_the_threshold(client, chart_id):
    from engine import bank

    plain = _hook(client, chart_id, 0)["2"]
    one = _hook(client, chart_id, bank.TURN_AT - 1)["2"]
    assert one["html"] == plain["html"], "한 번 아니오에 방향을 틀면 성급합니다"


def test_turned_hook_does_not_poison_the_cache(client, chart_id):
    """
    ★ 캐시 열쇠에 misses 가 없으면 방향을 튼 훅이 안 튼 훅을 덮어씁니다.
      다음 손님이 **남의 응답으로 고쳐진 훅**을 받습니다.
    """
    from engine import bank

    _hook(client, chart_id, bank.TURN_AT)
    assert "@turn" not in _hook(client, chart_id, 0)["2"]["statement_id"]


# ══════════════════════════════════════════════════════════
# 「글쎄올시다」 — 이분법이 공감률을 오염시키던 자리
# ══════════════════════════════════════════════════════════
def test_neutral_answer_is_counted_as_exposure_not_agreement(client, chart_id,
                                                             tmp_path,
                                                             monkeypatch):
    """
    답을 미룬 사람은 **노출로만** 셉니다.

    ★ 그렇소·아니오 둘뿐이라 애매한 사람이 거짓 '그렇소' 를 눌렀습니다.
      그 표가 공감률의 분자로 들어갑니다. 미룬 것은 분모에서도 뺍니다.
    """
    import repo

    monkeypatch.setattr(repo, "LOG_PATH", tmp_path / "log.jsonl")
    sid = "stab:love:목"

    client.post("/v1/feedback", json={
        "statement_id": sid, "chart_id": chart_id, "answer": 1})
    client.post("/v1/feedback", json={          # 글쎄올시다 — answer 없음
        "statement_id": sid, "chart_id": chart_id})

    hit, total, shown = repo._counts(sid)
    assert shown == 2, "노출은 둘 다 세야 합니다"
    assert total == 1, "미룬 답이 공감률 분모에 들어갔습니다"
    assert hit == 1


def test_agreement_reports_exposure_even_below_the_threshold(client, chart_id,
                                                             tmp_path,
                                                             monkeypatch):
    """
    ★ 공감률이 비어 있는 동안 그 자리가 **그냥 비어** 있었습니다.
      사회적 증거가 0인 채로 결제 갈림길까지 갑니다. 숫자를 지어내지
      않고 낼 수 있는 것이 노출 수입니다 — 정확도 주장이 아닙니다.
    """
    import repo

    monkeypatch.setattr(repo, "LOG_PATH", tmp_path / "log.jsonl")
    sid = "seen:only"
    for _ in range(3):
        client.post("/v1/feedback", json={
            "statement_id": sid, "chart_id": chart_id, "answer": 1})

    r = client.get("/v1/agreement", params={"statement_id": sid}).json()
    assert r["shown"] is False, "100건 전에는 공감률을 주지 않습니다"
    assert "rate" not in r
    assert r["seen"] == 3
