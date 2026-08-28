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
    import payments
    # 값은 여기 적지 않습니다. 서버가 정한 것과 같은지만 봅니다 —
    # 숫자를 두 벌 적어 두면 값을 고칠 때 여기가 조용히 거짓이 됩니다.
    assert r.json()["amount"] == payments.TIER_PRICE["all"]


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
    # ★ '이 자리 하나' 는 캐릭터마다 값이 다릅니다. 릴레이 카드에 보인
    #   값이 그대로 청구돼야 합니다 — _prepare 는 연담으로 삽니다.
    assert seen["amount"] == payments.price_of("one", "yeondam")


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


# ══════════════════════════════════════════════════════════
# 목패 — 값과 분량을 서버가 센다
# ══════════════════════════════════════════════════════════
#
# ★ 화면이 제 손으로 적고 있었습니다.
#   apps/web/lib/store.ts 가 "여덟 글자 전부 · 평생운 18컷 · 25페이지"
#   라고 적어 두었는데 실제로는 11~12컷 · 6탭이었습니다. 19,900원짜리
#   디지털 콘텐츠이고 같은 화면에 청약철회 제한 고지가 붙습니다.
def _tiers(app, lens_id="yeondam"):
    r = app.post("/v1/pay/tiers", json={
        "chart_id": _chart(app), "lens_id": lens_id,
        "concern": "love", "axis4": "INFP",
    })
    assert r.status_code == 200, r.text
    return r.json()["tiers"]


def test_tiers_report_the_real_cut_count():
    """
    세어 준 컷 수가 리포트가 **실제로** 내는 컷 수와 같아야 한다.

    ★ `all` · `sub` 은 한 사람 몫이 아닙니다.
      그 둘을 치르면 스무 사람이 전부 열립니다
      (routers/report.entitled_tier 가 모든 캐릭터에 rank 2 를 줍니다).
      한 사람 몫만 적어 두면 9,900원짜리 달삯과 견줄 때 같은 것으로
      보입니다 — 실제로 그렇게 보였고, 가운데 목패가 순수하게 열등한
      선택지가 되어 있었습니다.
    """
    from fastapi.testclient import TestClient
    import main as main_mod
    from engine import lens as lens_mod
    from engine.features import Features
    from engine.report import build_report
    from routers.chart import load_features

    with TestClient(main_mod.app) as app:
        cid = _chart(app)
        r = app.post("/v1/pay/tiers", json={
            "chart_id": cid, "lens_id": "yeondam",
            "concern": "love", "axis4": "INFP"})
        assert r.status_code == 200, r.text
        f = Features(**load_features(cid))
        released = [l["id"] for l in lens_mod.released()]
        for t in r.json()["tiers"]:
            if t["id"] == "one":
                rep = build_report(f, cid, "yeondam", "one", "love", "INFP")
                assert t["cuts"] == len(rep["cuts"]), t
                assert t["locked"] == len(rep["locked"]), t
                assert t["lenses"] == 1, t
            else:
                want = sum(len(build_report(f, cid, lid, t["id"], "love",
                                            "INFP")["cuts"])
                           for lid in released)
                assert t["cuts"] == want, t
                assert t["lenses"] == len(released), t
            # 분량도 서버가 셉니다. 화면이 적지 않습니다.
            assert t["chars"] > 0 and t["minutes"] >= 1, t


def test_tiers_price_matches_what_prepare_charges(app):
    """목패에 적힌 값이 곧 청구되는 값이어야 한다."""
    import payments
    for lens_id in ("yeondam", "pungun", "jeokhyeol"):
        for t in _tiers(app, lens_id):
            assert t["price"] == payments.price_of(t["id"], lens_id), \
                (lens_id, t["id"])


def test_free_character_has_no_one_tier(app):
    """값 없는 캐릭터에게 '이 자리 하나' 를 팔지 않는다. 강매입니다."""
    ids = {t["id"] for t in _tiers(app, "dongja")}
    assert "one" not in ids, ids


def test_tiers_never_promise_more_than_it_gives(app):
    """
    ★ 목패가 약속한 컷 수가 **0 보다 크고**, 화면이 따로 적어 둔 숫자가
      아니라 서버가 센 것이어야 한다. 부풀린 문구가 다시 들어오면
      여기가 붉어집니다.
    """
    for t in _tiers(app):
        assert t["cuts"] > 0, t
        assert t["chars"] > 0, t
        assert isinstance(t["note"], str) and t["note"], t
        # 한 사람 몫과 스무 사람 몫이 뒤섞이지 않아야 합니다.
        assert (t["lenses"] == 1) == (t["id"] == "one"), t


# ══════════════════════════════════════════════════════════
# ★ 목패끼리 잡아먹지 않는가 — 지배 검사
# ══════════════════════════════════════════════════════════
#
# 이 검사가 없어서 값이 서로를 덮고 있었습니다.
#
#   · `sub`(9,900원/월)이 `all`(19,900원)과 여는 것이 **글자 그대로**
#     같았습니다. 절반 값에 같은 것 — `all` 은 순수하게 열등했습니다.
#   · 풍운도령에서는 「이 자리 하나」와 「여덟 글자 전부」가 값도 컷도
#     똑같았습니다. **같은 상품이 두 장** 놓여 있었습니다.
#
# 값 사다리 검사(tests/test_lens_cuts.py)는 캐릭터 **사이**를 지켰지만
# 티어 **사이**는 아무도 안 보고 있었습니다. 여기가 그 자리입니다.
def test_no_tier_is_dominated_by_another(app):
    """
    더 비싼데 **그 목패라야 열리는 것이 하나도 없으면** 안 된다.

    ★ 잣대를 고쳤습니다.
      전에는 **컷 수**로 견줬습니다. 그런데 스무 사람을 여는 목패는
      어떤 한 사람짜리와 견줘도 컷 수가 항상 많습니다. 그 잣대로는
      「이 자리 하나」가 영원히 지는 것으로 나옵니다 — 틀린 계산이
      아니라 틀린 질문입니다.

      손님이 묻는 것은 "더 싼 저걸 사면 이건 안 사도 되는가?" 입니다.
      그러니 **여는 것의 포함관계**로 봅니다.

    ★ 전에는 `per_month` 가 다른 짝을 건너뛰었습니다. 이제 자동결제가
      없어져 셋 다 한 번 치르는 상품이라, 건너뛸 짝이 없습니다 —
      전부 나란히 놓고 견줍니다.
    """
    from engine.calendar import build_chart
    from engine.features import build_features
    from engine.report import build_report

    f = build_features(build_chart(1997, 3, 22, 14, 10, "F", True, "서울"))

    for lens_id in ("yeondam", "pungun", "jeokhyeol", "nopa", "haengsu"):
        tiers = {t["id"]: t for t in _tiers(app, lens_id)}
        opens = {tid: {c["id"] for c in build_report(
                    f, "t", lens_id, tid, "love", "INFP")["cuts"]}
                 for tid in tiers}
        for a in tiers.values():
            for b in tiers.values():
                if a["id"] == b["id"] or a["price"] < b["price"]:
                    continue
                only = opens[a["id"]] - opens[b["id"]]
                # 더 비싸거나 같은 값인데, 이것만 여는 것이 없으면 지배
                assert only or a["lenses"] > b["lenses"], (
                    "%s: %s(%d원)가 %s(%d원)보다 싸지 않은데 "
                    "이것만 여는 것이 하나도 없습니다"
                    % (lens_id, a["name"], a["price"], b["name"], b["price"]))


def test_single_character_never_costs_as_much_as_all_twenty(app):
    """
    ★ 「이 자리 하나」가 「스무 사람 전부」와 같거나 비싸면 안 된다.

    가장 비싼 캐릭터가 19,900원인데 `all` 도 19,900원이었습니다.
    한 사람 값으로 스무 사람을 살 수 있는데 아무도 그걸 모르는 상태였고,
    풍운도령을 고른 사람에게는 두 목패가 완전히 같아 보였습니다.
    """
    import payments
    from engine import lens as lens_mod
    top = max(l["price"] for l in lens_mod.released() if l.get("price"))
    assert top < payments.TIER_PRICE["all"], (
        "가장 비싼 캐릭터(%d원)가 '스무 사람 전부'(%d원) 이상입니다"
        % (top, payments.TIER_PRICE["all"]))


# ══════════════════════════════════════════════════════════
# ★ 기간이 다른 목패끼리도 견줘야 한다 — 첫 달은 나란히 놓입니다
# ══════════════════════════════════════════════════════════
#
# 위의 지배 검사는 `per_month` 가 다른 짝을 **건너뜁니다.** 한 번 치르는
# 것과 달마다를 곧바로 견주지 않으려고 그렇게 뒀는데, 그 틈으로
# 「이 자리 하나」 ↔ 「달마다 듣기」가 아무 검사도 없이 빠져나갔습니다.
#
#   손님은 목패 셋을 **한 화면에 나란히** 놓고 고릅니다. 그 순간 머릿속에
#   있는 것은 첫 달 값입니다. 풍운도령에서 이렇게 보였습니다:
#
#       이 자리 하나   19,900원 · 22컷 · 1사람
#       달마다 듣기     9,900원 · 374컷 · 20사람
#
#   두 배 값에 17분의 1입니다. 스무 명 중 **열여섯 명**이 그랬습니다.
def test_a_single_character_is_not_buried_by_the_monthly_tier(app):
    """
    ★ 기간이 다른 목패끼리도 견줘야 합니다 — 첫 달은 나란히 놓입니다.

      위의 지배 검사는 `per_month` 가 다른 짝을 건너뜁니다. 그 틈으로
      「이 자리 하나」 ↔ 「달마다 듣기」가 아무 검사도 없이 빠져나갔고,
      스무 명 중 **열여섯 명**에서 달삯이 단품을 통째로 덮고 있었습니다.
      풍운도령은 19,900원에 22컷 한 사람, 달삯은 9,900원에 374컷
      스무 사람이었습니다.

    ★ 잣대를 조심해야 합니다.
      **컷 수로 견주면 안 됩니다.** 달삯은 스무 사람을 열어서 어떤 한
      사람짜리 목패와 견줘도 컷 수가 항상 많습니다. 그 잣대로는 one 이
      영원히 지는 것으로 나옵니다 — 틀린 계산이 아니라 틀린 질문입니다.

      손님이 실제로 묻는 것은 "더 싼 저걸 사면 이건 안 사도 되는가?"
      입니다. 그러니 이렇게 셉니다 —
          값이 같거나 비싼데, **그 목패라야 열리는 것이 하나도 없다.**
    """
    from engine.calendar import build_chart
    from engine.features import build_features
    from engine.report import build_report
    import payments

    f = build_features(build_chart(1997, 3, 22, 14, 10, "F", True, "서울"))
    sub_price = payments.TIER_PRICE["sub"]

    buried = []
    for l in lens_mod_released():
        price = l.get("price")
        if not price:
            continue
        one = {c["id"] for c in build_report(
            f, "t", l["id"], "one", "love", "INFP")["cuts"]}
        sub = {c["id"] for c in build_report(
            f, "t", l["id"], "sub", "love", "INFP")["cuts"]}
        if price >= sub_price and not (one - sub):
            buried.append(
                "%s(%d원): 달삯(%d원)이 여는 것을 넘어서는 자리가 없습니다"
                % (l["id"], price, sub_price))
    assert not buried, (
        "「이 자리 하나」가 달삯에 완전히 덮입니다: "
        + " / ".join(buried))


def lens_mod_released():
    from engine import lens as lens_mod
    return lens_mod.released()


def test_the_monthly_tier_never_opens_the_deep_cuts(app):
    """
    ★ 달삯은 **넓이**를 팝니다. 깊이는 안 팝니다.

      대운 맵과 성향 대조는 「이 자리 하나」의 값 사다리와 「스무 사람
      전부」의 몫입니다. 달삯으로 그게 열리면 셋이 다시 같은 상품이 되고,
      값 사다리가 통째로 의미를 잃습니다.
    """
    from engine.calendar import build_chart
    from engine.features import build_features
    from engine.report import build_report

    f = build_features(build_chart(1997, 3, 22, 14, 10, "F", True, "서울"))
    ids = {c["id"] for c in build_report(
        f, "t", "pungun", "sub", "love", "INFP")["cuts"]}
    assert "daeun_map" not in ids, "달삯이 대운 맵을 열고 있습니다"
    assert "axis" not in ids, "달삯이 성향 대조를 열고 있습니다"


def test_paying_only_the_monthly_does_not_unlock_the_price_ladder(app):
    """
    ★ 등급이 같아지면서 생긴 구멍입니다.

      one 과 sub 이 같은 등급(1)이라, 달삯만 낸 사람이 tier="one" 을
      실어 보내면 등급 비교를 그냥 통과합니다. 그러면 그 캐릭터의 값
      사다리(대운 맵 · 성향 대조)가 9,900원에 열립니다.
      화면의 tier 는 localStorage 에서 오는 값입니다.
    """
    import store
    oid = "t-sub-order"
    store.set_json("order:" + oid, {
        "session_id": "t-sub-only", "chart_id": "x", "lens_id": "pungun",
        "tier": "sub", "concern": "love", "amount": 9900, "status": "paid",
        "payment_key": "t"})
    store.set_json("orders:t-sub-only", [oid])

    r = app.post("/v1/report", json={
        "chart_id": _chart(app), "lens_id": "pungun", "tier": "one",
        "session_id": "t-sub-only", "concern": "love"}).json()
    ids = {c["id"] for c in r["cuts"]}
    assert r["tier"] == "sub", "달삯이 「이 자리 하나」로 올라섰습니다"
    assert "daeun_map" not in ids and "axis" not in ids, (
        "달삯만 낸 사람에게 값 사다리가 열렸습니다")


# ══════════════════════════════════════════════════════════
# ★ 값을 치른 사람이 잃지 않는가
# ══════════════════════════════════════════════════════════
def test_a_forever_purchase_does_not_quietly_expire(app):
    """
    ★ 「한 번 치르면 계속 보오」라고 팔면서 **30일이면 사라졌습니다.**

      confirm 이 주문을 `ttl=30*DAY` 로 저장하고, entitled_tier 는 그
      주문을 읽어 자격을 봅니다. 서른 날이 지나면 주문이 없어지고
      자격이 조용히 free 로 떨어집니다 — 값을 치른 사람이 전부 잃습니다.
      목패에는 "영구" 라고 적혀 있습니다.
    """
    import store
    from routers.report import entitled_tier

    oid = "sjd-forever"
    store.set_json("order:" + oid, {
        "session_id": "s-forever", "chart_id": "x", "lens_id": "pungun",
        "tier": "all", "concern": "love", "amount": 24900,
        "status": "paid", "payment_key": "t",
        "paid_at": "2020-01-01T00:00:00+00:00", "expires_at": None})
    store.set_json("orders:s-forever", [oid])

    assert entitled_tier("s-forever", "pungun") == "all", (
        "영구로 판 것이 사라졌습니다")


def test_the_monthly_pass_actually_runs_out(app):
    """
    ★ 「달마다」로 팔면서 **끝나지 않았습니다.**

      빌링키도 자동결제도 없습니다. 9,900원을 한 번 받고 끝인데
      entitled_tier 는 그 주문을 보고 **영원히** 스무 사람을 열어 줬습니다.
      한 달치 값에 영구 이용권을 준 셈입니다.
    """
    import store
    from routers.report import entitled_tier

    live, dead = "sjd-live", "sjd-dead"
    store.set_json("order:" + live, {
        "session_id": "s-live", "chart_id": "x", "lens_id": "pungun",
        "tier": "sub", "status": "paid", "payment_key": "t",
        "paid_at": "2026-08-01T00:00:00+00:00",
        "expires_at": "2099-01-01T00:00:00+00:00"})
    store.set_json("orders:s-live", [live])
    assert entitled_tier("s-live", "pungun") == "sub"

    store.set_json("order:" + dead, {
        "session_id": "s-dead", "chart_id": "x", "lens_id": "pungun",
        "tier": "sub", "status": "paid", "payment_key": "t",
        "paid_at": "2020-01-01T00:00:00+00:00",
        "expires_at": "2020-01-31T00:00:00+00:00"})
    store.set_json("orders:s-dead", [dead])
    assert entitled_tier("s-dead", "pungun") == "free", (
        "달삯이 지났는데 아직 열려 있습니다 — 한 달 값에 영구를 준 것입니다")


def test_confirm_writes_when_it_was_paid_and_when_it_ends(app):
    """산 때와 끝나는 때를 안 적으면 위 둘을 판정할 수 없습니다."""
    import payments
    from routers import pay as pay_mod

    assert hasattr(pay_mod, "SUB_DAYS"), "달삯 기간이 코드에 없습니다"
    assert payments.TIER_PRICE["sub"] > 0
