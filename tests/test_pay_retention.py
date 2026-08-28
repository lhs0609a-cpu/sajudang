"""
PHASE 5 — 결제 · 리텐션 테스트.

여기서 지키는 것
    · PG 키가 없으면 결제를 거절한다 (성공한 척하지 않는다)
    · 금액은 서버가 정한다 (클라이언트 값을 믿지 않는다)
    · 하루 결제 2건 상한
    · 열람 후 청약철회 제한 / 계산 오류는 전액 환불
    · 알림은 하루 1건, 겹치면 우선순위 높은 것 하나만
    · 회고 루프는 쌓인 응답이 없으면 만들지 않는다
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

import payments
import store
from engine import retention, solar_terms as st
from engine.calendar import build_chart
from engine.features import build_features
from main import app

BIRTH = {"year": 1993, "month": 5, "day": 15, "hour": 10, "minute": 20,
         "hour_known": True, "sex": "F", "birth_city": "서울"}


@pytest.fixture()
def client():
    store.clear_all()
    return TestClient(app)


@pytest.fixture(scope="module")
def features():
    return build_features(build_chart(1993, 5, 15, 10, 20, "F")).to_dict()


# ══════════════════════════════════════════════════════════
# 결제
# ══════════════════════════════════════════════════════════
def test_price_comes_from_the_server(client):
    r = client.post("/v1/pay/prepare", json={
        "session_id": "p1", "chart_id": "c", "lens_id": "pungun", "tier": "all"})
    assert r.status_code == 200
    assert r.json()["amount"] == payments.TIER_PRICE["all"]


def test_prepare_reports_the_refund_notice(client):
    r = client.post("/v1/pay/prepare", json={
        "session_id": "p2", "chart_id": "c", "lens_id": "pungun", "tier": "one"}).json()
    assert "청약철회" in r["refund_notice"]


def test_secret_key_never_leaves_the_server(client):
    """
    ★ 나가면 안 되는 것은 시크릿 **값**입니다.

    본문에 'secret' 이라는 글자가 있는지만 보면 안 됩니다. 키가 안 꽂힌
    환경에서 까닭 문장이 "TOSS_SECRET_KEY 가 없습니다" 라고 **이름**을
    부르는데(payments.check_keys), 그 이름에 걸려 붉게 뜹니다.
    이름은 나가도 됩니다 — 무엇을 꽂아야 하는지 알려주는 말입니다.
    """
    res = client.get("/v1/pay/config")
    data = res.json()

    assert "client_key" in data
    # 시크릿을 담는 자리 자체가 없어야 합니다.
    assert [k for k in data if "secret" in k.lower()] == []
    # 값이 꽂힌 환경이면 그 값이 본문에 없어야 합니다.
    if payments.TOSS_SECRET_KEY:
        assert payments.TOSS_SECRET_KEY not in res.text


@pytest.mark.skipif(payments.ENABLED, reason="PG 키가 설정된 환경")
def test_confirm_refuses_without_pg_key(client):
    order = client.post("/v1/pay/prepare", json={
        "session_id": "p3", "chart_id": "c", "lens_id": "pungun",
        "tier": "one"}).json()
    r = client.post("/v1/pay/confirm", json={
        "session_id": "p3", "order_id": order["order_id"],
        "payment_key": "fake"})
    # 성공한 척하지 않는다
    assert r.status_code == 503
    assert "TOSS_SECRET_KEY" in r.json()["detail"]


def test_daily_purchase_limit_blocks_prepare(client):
    from engine.relay import BREAKS
    from routers.pay import _today, _user_key

    limit = BREAKS()["per_day_purchase"]
    key = store.k_purchase_day(_user_key("p4"), _today())
    for _ in range(limit):
        store.incr(key, ttl=86400)

    r = client.post("/v1/pay/prepare", json={
        "session_id": "p4", "chart_id": "c", "lens_id": "pungun", "tier": "all"})
    assert r.status_code == 429


def test_refund_blocked_after_opening(client):
    order = client.post("/v1/pay/prepare", json={
        "session_id": "p5", "chart_id": "c", "lens_id": "pungun",
        "tier": "one"}).json()
    o = store.get_json("order:" + order["order_id"])
    o.update(status="paid", payment_key="pk_test")
    store.set_json("order:" + order["order_id"], o)

    r = client.post("/v1/pay/refund", json={
        "order_id": order["order_id"], "reason": "그냥", "opened": True})
    assert r.status_code == 409
    assert "청약철회" in r.json()["detail"]


def test_unknown_order_is_404(client):
    r = client.post("/v1/pay/confirm", json={
        "session_id": "x", "order_id": "nope", "payment_key": "k"})
    assert r.status_code == 404


def test_tier_unlocks_match_report_cuts():
    """결제로 열리는 컷 이름이 리포트의 컷 id 와 맞아야 한다."""
    from engine.report import _all_cuts
    f = build_features(build_chart(1993, 5, 15, 10, 20, "F"))
    cuts, _err = _all_cuts(f, "love", "그대", "INFP")
    ids = {c["id"] for c in cuts}
    for tier, unlocks in payments.TIER_UNLOCKS.items():
        assert set(unlocks) <= ids, (tier, set(unlocks) - ids)


# ══════════════════════════════════════════════════════════
# 리텐션
# ══════════════════════════════════════════════════════════
def test_only_one_notification_per_day(features):
    plan = retention.plan_for(features, date(1993, 5, 15), date(2026, 5, 15))
    assert plan is not None
    assert isinstance(plan["kind"], str)          # 하나만 나온다
    assert "dropped" in plan                       # 나머지는 버려진 목록으로


def test_priority_wins_when_triggers_collide(features):
    """겹치면 우선순위가 높은 하나만 나간다."""
    plan = retention.plan_for(features, date(1993, 5, 15), date(2026, 5, 15))
    assert plan["kind"] == "birthday"


def test_lookback_beats_everything(features):
    plan = retention.plan_for(
        features, date(1993, 5, 15), date(2026, 5, 15),
        lookback_statement={"statement_id": "stab:love:목", "shown_at": "2025-11-01"})
    assert plan["kind"] == "lookback"


def test_no_lookback_without_data(features):
    """쌓인 응답이 없으면 회고를 만들지 않는다."""
    plan = retention.plan_for(features, date(1993, 1, 2), date(2026, 3, 3))
    assert plan is None or plan["kind"] != "lookback"


# ── 일진은 매일 밀어내지 않는다 ────────────────────────────
#
# ★ 전에는 일진이 **매일** 잡혔습니다. 1년에 352건입니다.
#   그걸 다 밀어내면 손님이 그날로 알림을 끕니다. 그리고 일진은 같은 날
#   다수에게 같은 글자가 가는 자리라 캡처를 나란히 놓기 가장 쉽습니다
#   (docs/18 §4 — 반복이 위험한 진짜 이유는 반복이 들통나는 것).
#   앱을 열면 언제든 볼 수 있습니다. **미는 것만** 줄였습니다.
def test_daily_is_not_pushed_every_day(features):
    """아무 날에나 일진 알림이 나가면 안 된다."""
    from datetime import timedelta
    days = [date(2026, 3, 1) + timedelta(days=i) for i in range(60)]
    daily = [d for d in days
             if (retention.plan_for(features, date(1993, 1, 2), d) or {})
             .get("kind") == "daily"]
    assert daily, "그 사람에게 걸리는 날은 있어야 한다"
    assert len(daily) < len(days) / 2, (
        "예순 날 중 %d일이나 밀어냅니다 — 그건 매일과 다르지 않습니다"
        % len(daily))


def test_daily_push_says_why_it_hit(features):
    """미는 날이면 **왜 오늘인지**가 붙어야 한다."""
    from datetime import timedelta
    for i in range(60):
        on = date(2026, 3, 1) + timedelta(days=i)
        plan = retention.plan_for(features, date(1993, 1, 2), on)
        if plan and plan["kind"] == "daily":
            assert plan["payload"]["why"] in ("chung", "hap", "fill")
            assert features["day_ji"] in plan["payload"]["text"] \
                or plan["payload"]["why"] == "fill"
            return
    raise AssertionError("예순 날 안에 걸리는 날이 하나도 없습니다")


def test_ipchun_triggers_year(features):
    ipchun = (st.ipchun_utc(2026) + retention.KST_OFFSET).date()
    plan = retention.plan_for(features, date(1993, 12, 31), ipchun)
    assert plan["kind"] == "year"


def test_jeolip_triggers_month(features):
    # 입춘·생일이 아닌 절입일을 하나 고른다
    days = retention.jeolip_days(2026)
    target = next(d for d, name in days if name not in ("입춘",))
    plan = retention.plan_for(features, date(1993, 12, 31), target)
    assert plan["kind"] in ("month", "year", "turning")


def test_daily_is_the_floor(features):
    """아무 트리거도 없는 날엔 일진이 나간다."""
    plan = retention.plan_for(features, date(1993, 12, 31), date(2026, 3, 12))
    assert plan["kind"] == "daily"
    assert len(plan["payload"]["gz"]) == 2


def test_every_kind_has_a_priority():
    for kind in ("daily", "month", "year", "birthday", "turning",
                 "lookback", "new_lens"):
        assert kind in retention.PRIORITY


# ══════════════════════════════════════════════════════════
# 「이번 주 한 가지」 회수 — 이 집이 스스로 만든 복귀 고리
# ══════════════════════════════════════════════════════════
#
# ★ 무료 구간이 이미 "다음에 오시거든 **했는지만** 말해 주시오" 라고
#   약속해 놓고, 다시 묻는 자리가 없었습니다. 약속해 놓고 안 물으면
#   그 문장은 처방이 아니라 덕담이 됩니다.
def _task(given):
    return {"given_on": given, "statement_id": "week:금:여름:甲"}


def test_the_weekly_task_is_collected_after_a_week(features):
    given = date(2026, 3, 10)
    plan = retention.plan_for(
        features, date(1993, 5, 15),
        given + timedelta(days=retention.WEEK_CHECK_DAYS),
        week_task=_task(given))
    assert plan is not None
    assert plan["kind"] == "week_check"
    assert plan["payload"]["given_on"] == given.isoformat()


def test_the_weekly_task_is_asked_once_not_every_day(features):
    """
    ★ 매일 물으면 그건 회수가 아니라 잔소리입니다. 일진을 매일 밀지
      않는 것과 같은 이유입니다 — 다 밀면 그날로 알림이 꺼집니다.
    """
    given = date(2026, 3, 10)
    hits = [d for d in range(1, 21)
            if (retention.plan_for(features, date(1993, 1, 2),
                                   given + timedelta(days=d),
                                   week_task=_task(given)) or {}
                ).get("kind") == "week_check"]
    assert hits == [retention.WEEK_CHECK_DAYS], hits


def test_the_weekly_task_does_not_outrank_the_rarer_things(features):
    """
    드문 것이 먼저입니다. 대운은 십 년에 한 번이고, 이건 리포트마다
    한 번입니다. 드물어야 열립니다.
    """
    P = retention.PRIORITY
    assert P["week_check"] < P["lookback"]
    assert P["week_check"] < P["turning"]
    assert P["week_check"] < P["birthday"]
    # 다만 일진보다는 위입니다 — 우리가 먼저 한 약속입니다.
    assert P["week_check"] > P["daily"]
