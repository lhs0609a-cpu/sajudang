# -*- coding: utf-8 -*-
"""
장부가 가게와 같은 말을 하는가.

★ 무슨 일이 있었나 (2026-09-03)

  주문에 적는 상태는 **우리 말**입니다 — `pending` → `paid` →
  `canceled` (`routers/pay.py`). 그런데 주인 화면의 매출 셈이
  **토스의 말**과 견주고 있었습니다:

      paid = [o for o in orders if o["status"] in payments.PAID_STATES]
      #                                          └ {"DONE"}

  두 어휘는 한 번도 겹치지 않습니다. 그래서 19,900원짜리를 치러도
  주인 화면에는 이렇게 떴습니다 —

      총 매출 0원 · 치른 건 0 · 환불 0 · 주문→결제 0.0%

  가게는 도는데 장부가 비어 있는 것입니다. 실거래를 시작하면
  **매출이 없다고 오판**하게 되는 자리라, 여기서 잠급니다.

★ 이름을 갈랐습니다

      PAID_STATES / DEAD_STATES     토스가 알려 주는 상태
      ORDER_PAID / ORDER_DEAD / ORDER_PENDING   우리 장부의 상태

  장부를 세는 곳은 `ORDER_*` 만 봅니다.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

import payments                       # noqa: E402
import store                          # noqa: E402
from routers import admin             # noqa: E402


def _seed():
    """치른 것 하나 · 안 치른 것 하나 · 물린 것 하나."""
    store.set_json("order:t_paid", {
        "amount": 19900, "status": "paid", "tier": "one",
        "lens_id": "pungun", "paid_at": "2026-09-03T10:00:00",
    })
    store.set_json("order:t_pend", {
        "amount": 4900, "status": "pending", "tier": "one",
        "lens_id": "jeokhyeol", "created_at": "2026-09-03T09:00:00+00:00",
    })
    store.set_json("order:t_dead", {
        "amount": 8900, "status": "canceled", "tier": "one",
        "lens_id": "yakcho", "pg_status": "CANCELED",
    })


def _clean():
    for k in ("order:t_paid", "order:t_pend", "order:t_dead"):
        try:
            store.delete(k)
        except AttributeError:
            store.set_json(k, None)


def test_two_vocabularies_do_not_overlap():
    """섞이면 안 되는 두 어휘. 겹치면 어느 쪽이든 오판합니다."""
    ours = payments.ORDER_PAID | payments.ORDER_DEAD | payments.ORDER_PENDING
    theirs = payments.PAID_STATES | payments.DEAD_STATES
    assert not (ours & theirs), "장부의 말과 PG 의 말이 겹치오: %s" % (ours & theirs)


def test_paid_order_shows_up_in_revenue():
    _seed()
    try:
        s = admin._sales()
        assert s["paid"] >= 1, "치른 주문이 안 세어지오"
        assert s["revenue"] >= 19900, "매출이 0원이오 — 상태 어휘가 갈렸소"
        assert s["refunded"] >= 1, "물린 주문이 안 세어지오"
        assert s["pending"] >= 1, "안 치른 주문이 안 세어지오"
        assert s["close_rate"] is not None
    finally:
        _clean()


def test_avg_order_is_none_when_nothing_paid():
    """
    치른 건이 없을 때 평균을 0원으로 적지 않는다. 없는 값은 없다고
    말합니다 — 이 집이 시주를 열두 시로 채우지 않는 것과 같은 이유.
    """
    s = admin._sales()
    if s["paid"] == 0:
        assert s["avg_order"] is None


def test_trouble_reports_the_gate_and_stale_orders():
    _seed()
    try:
        t = admin._trouble()
        assert t["gate"], "결제 문이 어떤 상태인지 안 적히오"
        assert t["stale_pending_all"] >= 1
        assert t["canceled_all"] >= 1
        row = [r for r in t["stale_pending"] if r["order_id"] == "t_pend"]
        assert row, "안 치른 주문이 목록에 없소"
        assert row[0]["age_min"] is not None, "만든 때를 못 읽었소"
    finally:
        _clean()


def test_trouble_carries_no_personal_columns():
    """
    ★ 계측·주인 화면에 개인정보를 싣지 않습니다 (CLAUDE.md).
      세션·명식은 준식별자입니다.
    """
    _seed()
    try:
        t = admin._trouble()
        blob = repr(t)
        for bad in ("session_id", "chart_id", "sid=", "birth"):
            assert bad not in blob, "주인 화면에 %s 가 실렸소" % bad
    finally:
        _clean()
