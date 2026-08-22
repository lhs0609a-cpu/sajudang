"""
결제 배선 — 실거래 없이 증명할 수 있는 것만 증명한다.

★ 여기서 **증명 못 하는 것**
    실제 카드 승인. PG 키가 없습니다. 토스 테스트 키를 넣고
    한 건 긁어 봐야 끝납니다. docs/17 §7 에 절차가 있습니다.

★ 여기서 증명하는 것
    · 키가 없으면 결제를 거절한다 (성공한 척하지 않는다)
    · 금액을 클라이언트가 못 정한다
    · 하루 2건 브레이크가 결제 경로 양쪽(prepare·confirm)에서 걸린다
    · 승인 전에는 티어가 안 열린다
    · 같은 주문을 두 번 승인해도 두 번 안 긁는다
    · 시크릿 키가 응답에 안 실린다
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("STORE_PATH", str(tmp_path / "s.sqlite"))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    for m in [k for k in list(sys.modules)
              if k in ("store", "payments", "db", "main", "analytics")
              or k.startswith("routers")]:
        sys.modules.pop(m, None)
    from fastapi.testclient import TestClient
    import main
    return TestClient(main.app)


def _chart(app) -> str:
    r = app.post("/v1/chart", json={
        "year": 1993, "month": 5, "day": 15, "hour": 10, "minute": 20,
        "hour_known": True, "sex": "F", "birth_city": "서울",
    })
    assert r.status_code == 200, r.text
    return r.json()["chart_id"]


def _prepare(app, sid="sess-pay-0001", tier="all"):
    return app.post("/v1/pay/prepare", json={
        "session_id": sid, "chart_id": _chart(app),
        "lens_id": "yeondam", "tier": tier, "concern": "love",
    })


# ══════════════════════════════════════════════════════════
# 키가 없으면 — 성공한 척하지 않는다
# ══════════════════════════════════════════════════════════
def test_config_reports_disabled_without_keys(app):
    cfg = app.get("/v1/pay/config").json()
    assert cfg["enabled"] is False
    assert cfg["client_key"] is None


def test_secret_key_is_never_in_a_response(app, monkeypatch):
    import payments
    monkeypatch.setattr(payments, "TOSS_SECRET_KEY", "test_sk_DO_NOT_LEAK")
    monkeypatch.setattr(payments, "TOSS_CLIENT_KEY", "test_ck_public")
    monkeypatch.setattr(payments, "ENABLED", True)
    body = app.get("/v1/pay/config").text + _prepare(app).text
    assert "DO_NOT_LEAK" not in body
    assert "test_ck_public" in body        # 공개 키는 나가도 된다


def test_confirm_is_refused_without_keys(app):
    o = _prepare(app).json()
    r = app.post("/v1/pay/confirm", json={
        "session_id": "sess-pay-0001", "order_id": o["order_id"],
        "payment_key": "가짜열쇠",
    })
    assert r.status_code == 503, r.text


def test_tier_stays_locked_when_payment_fails(app):
    """승인 못 했으면 잠긴 컷의 본문이 나가면 안 된다."""
    chart_id = _chart(app)
    r = app.post("/v1/report", json={
        "chart_id": chart_id, "lens_id": "yeondam",
        "tier": "free", "concern": "love",
    }).json()
    locked = {c["id"] for c in r["locked"]}
    assert "daeun_now" in locked and "yongsin" in locked
    for c in r["locked"]:
        assert "html" not in c or not c.get("html")


# ══════════════════════════════════════════════════════════
# 금액 — 서버가 정한다
# ══════════════════════════════════════════════════════════
def test_amount_comes_from_the_server(app):
    import payments
    for tier, want in payments.TIER_PRICE.items():
        o = _prepare(app, tier=tier).json()
        assert o["amount"] == want, tier


def test_client_cannot_set_the_amount(app):
    """요청에 amount 를 실어 보내도 서버가 무시한다."""
    r = app.post("/v1/pay/prepare", json={
        "session_id": "sess-pay-0002", "chart_id": _chart(app),
        "lens_id": "yeondam", "tier": "all", "concern": "love",
        "amount": 10, "price": 10,
    })
    assert r.status_code == 200
    assert r.json()["amount"] == 19900


def test_unknown_tier_is_refused(app):
    r = app.post("/v1/pay/prepare", json={
        "session_id": "sess-pay-0003", "chart_id": _chart(app),
        "lens_id": "yeondam", "tier": "공짜", "concern": "love",
    })
    assert r.status_code >= 400


# ══════════════════════════════════════════════════════════
# ★ 브레이크 — 하루 2건
# ══════════════════════════════════════════════════════════
def test_daily_purchase_break_holds(app, monkeypatch):
    """
    매출 최적화를 이유로 이걸 풀지 마세요. (CLAUDE.md 절대 규칙 4)
    """
    import payments
    from engine.relay import BREAKS
    limit = BREAKS()["per_day_purchase"]
    assert limit <= 2

    # 승인은 PG 를 타지 않게 갈아 끼운다 — 브레이크만 본다
    monkeypatch.setattr(payments, "ENABLED", True)
    monkeypatch.setattr(payments, "confirm", lambda pk, oid, amt:
                        payments.PaymentResult(True, oid, amt, "tid_" + oid,
                                               "DONE", {}))
    sid = "sess-break-01"
    done = 0
    for _ in range(limit + 2):
        o = _prepare(app, sid=sid).json()
        if "order_id" not in o:
            break
        r = app.post("/v1/pay/confirm", json={
            "session_id": sid, "order_id": o["order_id"],
            "payment_key": "pk_test"})
        if r.status_code == 429:
            break
        assert r.status_code == 200, r.text
        done += 1
    assert done == limit, "하루 %d건이어야 하는데 %d건 통과했습니다" % (limit, done)

    # 상한을 넘긴 뒤에는 주문 자체가 막힌다
    assert _prepare(app, sid=sid).status_code == 429


def test_break_cannot_be_loosened_by_the_seed_file(app):
    """시드를 고쳐 브레이크를 느슨하게 만들 수 없어야 한다."""
    import json
    import engine.relay as relay
    original = relay._rules_file

    def loose():
        d = json.loads(json.dumps(original()))
        d["breaks"]["per_day_purchase"] = 999
        d["breaks"]["per_session_relay"] = 999
        d["breaks"]["reunion_cooldown_days"] = 0
        return d

    relay._rules_file = loose
    try:
        b = relay.BREAKS()
        assert b["per_day_purchase"] <= 2
        assert b["per_session_relay"] <= 2
        assert b["reunion_cooldown_days"] >= 7
    finally:
        relay._rules_file = original


# ══════════════════════════════════════════════════════════
# 승인
# ══════════════════════════════════════════════════════════
def test_confirm_unlocks_and_is_idempotent(app, monkeypatch):
    import payments
    calls = []

    def fake(pk, oid, amt):
        calls.append((pk, oid, amt))
        return payments.PaymentResult(True, oid, amt, "tid_1", "DONE", {})

    monkeypatch.setattr(payments, "ENABLED", True)
    monkeypatch.setattr(payments, "confirm", fake)

    sid = "sess-once-01"
    o = _prepare(app, sid=sid).json()
    first = app.post("/v1/pay/confirm", json={
        "session_id": sid, "order_id": o["order_id"], "payment_key": "pk"})
    assert first.status_code == 200, first.text
    assert set(payments.TIER_UNLOCKS["all"]) <= set(first.json()["unlocked"])

    # 같은 주문을 또 승인해도 PG 를 두 번 긁지 않는다
    again = app.post("/v1/pay/confirm", json={
        "session_id": sid, "order_id": o["order_id"], "payment_key": "pk"})
    assert again.status_code == 200
    assert again.json().get("already") is True
    assert len(calls) == 1, "PG 를 %d번 긁었습니다" % len(calls)


def test_confirm_sends_the_server_amount_not_the_clients(app, monkeypatch):
    import payments
    seen = {}
    monkeypatch.setattr(payments, "ENABLED", True)
    monkeypatch.setattr(payments, "confirm", lambda pk, oid, amt:
                        (seen.update(amount=amt),
                         payments.PaymentResult(True, oid, amt, "t", "DONE", {}))[1])
    sid = "sess-amt-01"
    o = _prepare(app, sid=sid, tier="one").json()
    app.post("/v1/pay/confirm", json={
        "session_id": sid, "order_id": o["order_id"],
        "payment_key": "pk", "amount": 1})
    assert seen["amount"] == payments.TIER_PRICE["one"]


def test_unknown_order_is_refused(app):
    r = app.post("/v1/pay/confirm", json={
        "session_id": "sess-x", "order_id": "sjd_없는주문",
        "payment_key": "pk"})
    assert r.status_code == 404


# ══════════════════════════════════════════════════════════
# 화면 쪽 — 결제창이 실제로 붙었는가
# ══════════════════════════════════════════════════════════
WEB = ROOT / "apps" / "web"


def test_frontend_uses_the_real_sdk_not_a_prompt():
    """
    예전에는 window.prompt 로 paymentKey 를 사람에게 물어봤습니다.
    그건 붙다 만 자리표시였습니다.
    """
    page = (WEB / "app" / "pay" / "page.tsx").read_text(encoding="utf-8")
    assert "window.prompt" not in page
    assert "openCheckout(" in page

    toss = (WEB / "lib" / "toss.ts").read_text(encoding="utf-8")
    assert "js.tosspayments.com" in toss
    assert "requestPayment" in toss


def test_frontend_never_sends_personal_data_to_the_pg():
    """customerKey 에 이름·생년월일을 넣으면 PG 로 넘어갑니다."""
    page = (WEB / "app" / "pay" / "page.tsx").read_text(encoding="utf-8")
    block = page[page.index("openCheckout({"):]
    block = block[:block.index("});")]
    assert "customerKey: s.sessionId" in block
    for banned in ["s.name", "s.year", "s.month", "s.day", "s.city"]:
        assert banned not in block, banned


def test_return_from_checkout_is_handled():
    """결제창은 페이지를 통째로 떠났다 옵니다. 돌아온 자리가 있어야 합니다."""
    page = (WEB / "app" / "pay" / "page.tsx").read_text(encoding="utf-8")
    assert 'params.get("toss")' in page
    assert 'params.get("paymentKey")' in page
    assert "payConfirm(" in page


# ══════════════════════════════════════════════════════════
# 키 두 짝이 맞는가 — 손님이 카드를 긁기 **전에** 걸러야 한다
#
# 위젯 키(gck/gsk)를 넣어도 결제창은 멀쩡히 뜹니다. 막히는 곳은 승인이고,
# 그때는 이미 긁은 뒤입니다. 그래서 뜰 때 봅니다.
# ══════════════════════════════════════════════════════════
def test_matching_api_keys_pass():
    import payments
    assert payments.check_keys("live_ck_aaa", "live_sk_bbb") is None
    assert payments.check_keys("test_ck_aaa", "test_sk_bbb") is None


def test_widget_keys_are_refused_while_frontend_uses_payment_window():
    """프론트가 payment() 를 쓰는 동안 gck/gsk 를 받으면 안 된다."""
    import payments
    why = payments.check_keys("live_gck_aaa", "live_gsk_bbb")
    assert why and "결제위젯" in why


def test_live_and_test_keys_cannot_be_mixed():
    import payments
    assert payments.check_keys("test_ck_aaa", "live_sk_bbb")
    assert payments.check_keys("live_ck_aaa", "test_sk_bbb")


def test_swapped_keys_are_caught():
    """클라이언트 자리에 시크릿을 넣는 사고가 제일 흔하다."""
    import payments
    why = payments.check_keys("live_sk_bbb", "live_ck_aaa")
    assert why and "바뀌었" in why


def test_client_key_alone_is_not_enough():
    import payments
    assert payments.check_keys("live_ck_aaa", "")
    assert payments.check_keys("", "live_sk_bbb")


def test_reason_never_carries_the_key_itself():
    """까닭은 로그와 /health 로 나갑니다. 키가 실리면 안 됩니다."""
    import payments
    for c, k in [("live_gck_SECRETISH", "live_gsk_SECRETISH"),
                 ("live_sk_SECRETISH", "live_ck_SECRETISH"),
                 ("무엇", "live_sk_SECRETISH"),
                 ("live_ck_SECRETISH", "무엇")]:
        why = payments.check_keys(c, k) or ""
        assert "SECRETISH" not in why, why


def test_health_says_why_payments_are_off(app):
    h = app.get("/health").json()
    assert h["payments"] is False
    assert h["payments_live"] is False
    assert "TOSS_SECRET_KEY" in h["payments_reason"]
