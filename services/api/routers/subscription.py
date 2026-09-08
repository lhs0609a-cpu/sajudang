"""
한 달 듣기 — 자동결제 · docs/11 §5

    POST /v1/pay/sub/prepare    카드 등록 전. customerKey 를 받아 간다
    POST /v1/pay/sub/register   등록 끝 → 빌링키 발급 + 첫 달 청구
    GET  /v1/pay/sub            지금 구독이 어떤 상태인가
    POST /v1/pay/sub/cancel     그만두기 (기간 끝까지는 본다)
    POST /v1/pay/sub/resume     그만두기를 무르기 (기간 안에서만)
    POST /v1/pay/sub/restore    기기를 바꿨을 때 되찾기

★ 왜 파일을 따로 두는가
  `routers/pay.py` 는 **한 번 치르는 값**의 자리입니다. 구독은 손님이
  없는 자리에서 우리가 카드를 긁는 일이라, 지키는 것이 다릅니다 —
  카드 열쇠·갱신·해지·연체. 섞어 두면 「한 번 치르기」를 고치다 달삯이
  같이 흔들립니다.

★ 절대 규칙
  1. 빌링키는 **어떤 응답에도** 실리지 않습니다. 카드 뒷자리만 냅니다.
  2. 금액은 서버가 정합니다 (`payments.TIER_PRICE["sub"]`).
  3. 자동갱신은 **하루 결제 2건 브레이크에 안 셉니다** — 손님이 누른
     것이 아닙니다. 처음 등록만 셉니다.
  4. 그만둔 사람에게 다시 안 긁습니다. 기간이 끝나면 열쇠를 버립니다.
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import payments
import store
from engine.relay import BREAKS

log = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/pay/sub", tags=["pay"])

DAY = 86400

# 한 주기가 며칠인가. 「달마다」라 말하고 서른 날로 셉니다 —
# 달의 길이가 28~31일이라, 날로 세야 손님과 우리가 같은 날을 봅니다.
PERIOD_DAYS = 30

# 갱신에 실패해도 바로 끊지 않습니다. 카드 한도·유효기간은 사흘이면
# 손님이 고칩니다. 그동안 자격은 열어 둡니다 — 값을 치르던 사람입니다.
GRACE_DAYS = 3

# 이만큼 실패하면 그만 긁습니다. 계속 긁으면 카드사가 우리를 막습니다.
MAX_FAILS = 4


def _user_key(session_id: str) -> str:
    return hashlib.sha256(session_id.encode()).hexdigest()[:16]


def _k(session_id: str) -> str:
    return "sub:" + _user_key(session_id)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _at(iso: Optional[str]) -> Optional[datetime]:
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso)
    except ValueError:
        return None


def _customer_key(session_id: str) -> str:
    """
    토스에 보내는 손님 열쇠.

    ★ 세션 아이디를 그대로 보내지 않습니다. 그건 우리 쪽 자격의
      열쇠라, 밖으로 나가면 안 됩니다. 해시를 씁니다 — 같은 브라우저면
      늘 같은 값이 나와야 카드가 겹쳐 등록되지 않습니다.
    """
    return "sjd_" + hashlib.sha256(
        ("customer:" + session_id).encode()).hexdigest()[:24]


def _load(session_id: str) -> Optional[dict]:
    return store.get_json(_k(session_id))


def _save(sub: dict) -> None:
    store.set_json("sub:" + sub["user_key"], sub, ttl=730 * DAY)


def active(sub: Optional[dict]) -> bool:
    """지금 볼 수 있는가. **끊긴 것과 그만둔 것은 다릅니다** —
    그만둔 사람도 이미 치른 달까지는 봅니다."""
    if not sub or sub.get("status") == "dead":
        return False
    ends = _at(sub.get("period_end"))
    if not ends:
        return False
    return ends + timedelta(days=GRACE_DAYS if sub.get("fails") else 0) > _now()


# ══════════════════════════════════════════════════════════
# 화면에 내려보내는 꼴 — ★ 빌링키는 여기 못 옵니다
# ══════════════════════════════════════════════════════════
def _view(sub: Optional[dict]) -> dict:
    problem = payments.subscriptions_problem()
    if not sub:
        return {"has": False, "active": False,
                "price": payments.TIER_PRICE["sub"],
                "enabled": problem is None, "reason": problem}
    ends = _at(sub.get("period_end"))
    return {
        "has": True,
        "active": active(sub),
        "status": sub.get("status"),
        "price": sub.get("amount", payments.TIER_PRICE["sub"]),
        # 카드 뒷자리만. 카드 번호도 빌링키도 아닙니다.
        "card": sub.get("card_last4"),
        "card_name": sub.get("card_name"),
        "period_end": sub.get("period_end"),
        "next_charge": None if sub.get("ending") else sub.get("period_end"),
        # 그만두기를 눌렀는가. 눌렀어도 기간 끝까지는 봅니다.
        "ending": bool(sub.get("ending")),
        "months": sub.get("months", 1),
        "fails": sub.get("fails", 0),
        "last_error": sub.get("last_error"),
        "days_left": max(0, (ends - _now()).days) if ends else 0,
        "enabled": problem is None, "reason": problem,
    }


def _terms(price: int, when: datetime) -> list:
    """등록 버튼 위에 놓이는 고지. 네 가지를 다 말합니다."""
    return [t.format(price=format(price, ","),
                     next="%d월 %d일" % (when.month, when.day))
            for t in payments.SUB_TERMS]


# ══════════════════════════════════════════════════════════
# ① 카드 등록 전 — 손님 열쇠를 받아 간다
# ══════════════════════════════════════════════════════════
class PrepareRequest(BaseModel):
    session_id: str


@router.post("/prepare")
def prepare(req: PrepareRequest) -> dict:
    problem = payments.subscriptions_problem()
    if problem:
        raise HTTPException(status_code=503, detail=problem)

    sub = _load(req.session_id)
    if active(sub) and not (sub or {}).get("ending"):
        raise HTTPException(
            status_code=409,
            detail="이미 달마다 듣고 계시오. 두 번 걸 것 없소.")

    # 처음 등록은 **손님이 누른 결제**입니다. 브레이크에 셉니다.
    limit = BREAKS()["per_day_purchase"]
    used = store.get_int(store.k_purchase_day(
        _user_key(req.session_id), _now().date().isoformat()))
    if used >= limit:
        raise HTTPException(
            status_code=429,
            detail="하루에 %d건까지만 받소. 내일 다시 오시오." % limit)

    price = payments.TIER_PRICE["sub"]
    cfg = payments.client_config()
    return {
        "customer_key": _customer_key(req.session_id),
        "client_key": cfg["client_key"],
        "enabled": cfg["enabled"],
        "amount": price,
        "order_name": payments.TIER_NAME["sub"],
        "terms": _terms(price, _now() + timedelta(days=PERIOD_DAYS)),
        "say": payments.SUB_SAY,
        "refund_notice": payments.REFUND_NOTICE,
        "purchases_today": used, "per_day_limit": limit,
    }


# ══════════════════════════════════════════════════════════
# ② 등록 끝 — 빌링키를 받고 첫 달을 긁는다
# ══════════════════════════════════════════════════════════
class RegisterRequest(BaseModel):
    analytics_sid: Optional[str] = Field(default=None, pattern=r"^[A-Za-z0-9_-]{16,64}$")
    session_id: str
    customer_key: str
    auth_key: str
    chart_id: Optional[str] = None
    concern: str = "love"


@router.post("/register")
def register(req: RegisterRequest) -> dict:
    try:
        with store.payment_lease(req.session_id) as check:
            existing = _load(req.session_id)
            if active(existing):
                return {"ok": True, "already": True, "order_id": (existing.get("orders") or [""])[-1],
                        "sub": _view(existing), "say": "이미 이용 중인 구독이에요."}
            return _register_locked(req, check)
    except store.LeaseBusy as e:
        raise HTTPException(status_code=409, detail=str(e))


def _register_locked(req: RegisterRequest, check) -> dict:
    problem = payments.subscriptions_problem()
    if problem:
        raise HTTPException(status_code=503, detail=problem)

    # ★ 손님 열쇠는 **우리가 만든 것**이라야 합니다. 화면이 보낸 값을
    #   그대로 쓰면, 남의 열쇠를 실어 보내 남의 카드로 긁는 길이 열립니다.
    want = _customer_key(req.session_id)
    if req.customer_key != want:
        raise HTTPException(status_code=400, detail="손님 열쇠가 맞지 않소.")

    limit = BREAKS()["per_day_purchase"]
    daykey = store.k_purchase_day(_user_key(req.session_id),
                                  _now().date().isoformat())
    if store.get_int(daykey) >= limit:
        raise HTTPException(status_code=429,
                            detail="하루에 %d건까지만 받소." % limit)

    try:
        issued = payments.issue_billing_key(req.auth_key, req.customer_key)
    except payments.PaymentsDisabled as e:
        raise HTTPException(status_code=503, detail=str(e))
    except payments.PaymentError as e:
        raise HTTPException(status_code=402, detail=str(e))

    billing_key = issued["billingKey"]
    card = issued.get("card") or {}
    amount = payments.TIER_PRICE["sub"]
    order_id = "sjd_sub_" + uuid.uuid4().hex[:16]

    # ★ 카드를 등록했다고 값이 치러진 것이 아닙니다. 여기서 긁습니다.
    #   이 자리가 빠지면 카드만 잡아 두고 자격을 여는 꼴이 됩니다.
    try:
        result = payments.charge_billing(
            billing_key, req.customer_key, amount, order_id,
            payments.TIER_NAME["sub"])
    except payments.PaymentError as e:
        # 열쇠는 발급됐지만 첫 달을 못 긁었습니다. 자격을 열지 않고,
        # 열쇠도 저장하지 않습니다 — 안 긁힌 카드를 들고 있을 이유가 없습니다.
        raise HTTPException(status_code=402, detail=str(e))

    now = _now()
    ends = now + timedelta(days=PERIOD_DAYS)
    sub = {
        "user_key": _user_key(req.session_id),
        "session_id": req.session_id,
        "customer_key": req.customer_key,
        # ★ 봉해서 저장합니다. 이 값은 여기서만 삽니다.
        "billing_key": payments.seal(billing_key),
        "card_last4": card.get("number", "")[-4:] or None,
        "card_name": card.get("cardCompany") or card.get("issuerCode"),
        "amount": amount,
        "status": "live",
        "ending": False,
        "started_at": now.isoformat(),
        "period_end": ends.isoformat(),
        "months": 1,
        "fails": 0,
        "last_error": None,
        "chart_id": req.chart_id,
        "concern": req.concern,
        "orders": [order_id],
    }
    check()
    sub["analytics_sid"] = req.analytics_sid
    _save(sub)
    _write_order(sub, order_id, result.pg_tid, now, ends, first=True)
    store.increment_once("purchase-counted:" + order_id, daykey, DAY)
    if req.analytics_sid:
        import analytics
        analytics.record([{ "name": "payment_approved", "screen": "d3", "sid": req.analytics_sid, "n": amount }], server=True)

    return {"ok": True, "order_id": order_id,
            "sub": _view(sub),
            "say": "카드를 걸어 두었소. 오늘부터 서른 날, 그리고 그 뒤로도."}


def _write_order(sub: dict, order_id: str, pg_tid: Optional[str],
                 now: datetime, ends: datetime, first: bool) -> None:
    """
    청구 한 번 = 주문 한 건.

    ★ 갱신마다 주문을 새로 적습니다. 하나를 늘려 쓰면 「무엇을 언제
      얼마에 치렀는가」가 사라져 영수증도 환불도 못 냅니다. 자격을
      보는 자리(routers/report._paid_orders)도 이 주문을 봅니다.
    """
    store.set_json("order:" + order_id, {
        "session_id": sub["session_id"], "chart_id": sub.get("chart_id"),
        "lens_id": None, "tier": "sub", "concern": sub.get("concern", "love"),
        "amount": sub["amount"], "status": "paid", "payment_key": pg_tid,
        "created_at": now.isoformat(), "paid_at": now.isoformat(),
        "expires_at": ends.isoformat(),
        "unlocked": payments.unlocks_for("sub"),
        # 몇 번째 달인가. 주인 화면이 첫 달과 갱신을 갈라 봅니다.
        "renewal": not first,
    })
    okey = "orders:" + sub["session_id"]
    orders = store.get_json(okey) or []
    if order_id not in orders:
        orders.append(order_id)
        store.set_json(okey, orders, ttl=730 * DAY)


# ══════════════════════════════════════════════════════════
# ③ 지금 어떤 상태인가
# ══════════════════════════════════════════════════════════
@router.get("")
def status(session_id: str) -> dict:
    return _view(_load(session_id))


# ══════════════════════════════════════════════════════════
# ④ 그만두기 — 시작한 길만큼 쉬워야 합니다 (docs/11 §5)
# ══════════════════════════════════════════════════════════
class SessionRequest(BaseModel):
    session_id: str


@router.post("/cancel")
def cancel(req: SessionRequest) -> dict:
    sub = _load(req.session_id)
    if not sub or sub.get("status") == "dead":
        raise HTTPException(status_code=404, detail="걸어 두신 카드가 없소.")
    if sub.get("ending"):
        return {"ok": True, "already": True, "sub": _view(sub)}

    # ★ 자격을 지금 뺏지 않습니다. 이미 치른 달은 끝까지 봅니다.
    #   여기서 끊으면 「남은 날을 빼앗는 해지」가 됩니다.
    sub["ending"] = True
    sub["ended_at"] = _now().isoformat()
    _save(sub)
    ends = _at(sub.get("period_end"))
    return {
        "ok": True, "sub": _view(sub),
        "say": ("그리 하겠소. 더 안 빠져나가오. "
                + ("치르신 달은 %d월 %d일까지 그대로 보시오."
                   % (ends.month, ends.day) if ends else "")),
    }


@router.post("/resume")
def resume(req: SessionRequest) -> dict:
    """그만두기를 무르기. **기간이 살아 있을 때만**입니다 —
    끝난 뒤에는 카드를 다시 걸어야 합니다(열쇠를 버렸으므로)."""
    sub = _load(req.session_id)
    if not sub or not sub.get("ending") or not active(sub):
        raise HTTPException(status_code=409,
                            detail="무를 것이 없소. 다시 걸어 주시오.")
    sub["ending"] = False
    sub.pop("ended_at", None)
    _save(sub)
    return {"ok": True, "sub": _view(sub), "say": "이어 가겠소."}


class RestoreRequest(BaseModel):
    session_id: str
    order_id: str


@router.post("/restore")
def restore(req: RestoreRequest) -> dict:
    """
    기기를 바꿨을 때.

    ★ 로그인이 없습니다. 자격이 이 브라우저의 난수(session_id)에 매여
      있어서, 데이터를 지우면 치른 값을 잃습니다. 「한 번 치르기」는
      주문번호로 되찾는데(pay.restore), 구독은 그것만으로 모자랍니다 —
      **다음 달 청구가 옛 브라우저로 가서** 돈은 나가는데 새 기기에서는
      안 열립니다. 그래서 구독 레코드의 주인까지 함께 옮깁니다.

    ★ 손님 열쇠(customer_key)는 **안 바꿉니다.** 토스에 등록된 카드가
      그 열쇠에 매여 있어서, 바꾸면 다음 청구가 통째로 실패합니다.
    """
    order = store.get_json("order:" + req.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="그런 주문번호가 없소.")
    if order.get("tier") != "sub":
        raise HTTPException(status_code=409,
                            detail="달삯 주문이 아니오. 「내 첩」의 되찾기를 쓰시오.")
    if order.get("status") != "paid":
        raise HTTPException(status_code=409, detail="아직 치러지지 않은 주문이오.")

    old_session = order.get("session_id")
    sub = store.get_json("sub:" + _user_key(old_session)) if old_session else None
    if not sub:
        raise HTTPException(status_code=404, detail="걸어 두신 카드를 못 찾았소.")

    # 옛 자리를 비우고 새 자리로 옮깁니다. 두 자리에 남겨 두면 갱신이
    # 두 번 돕니다 — 한 달에 두 번 빠져나갑니다.
    if old_session != req.session_id:
        store.delete("sub:" + _user_key(old_session))
    sub["session_id"] = req.session_id
    sub["user_key"] = _user_key(req.session_id)
    _save(sub)

    # 치른 주문들도 새 세션에 붙여 줍니다 — 자격은 주문이 정합니다.
    okey = "orders:" + req.session_id
    orders = store.get_json(okey) or []
    for oid in sub.get("orders", []):
        if oid not in orders:
            orders.append(oid)
    store.set_json(okey, orders, ttl=730 * DAY)

    return {"ok": True, "sub": _view(sub),
            "say": "찾았소. 다음 달부터는 이 자리로 오오."}


# ══════════════════════════════════════════════════════════
# 갱신 — 손님이 없는 자리에서 도는 것
# ══════════════════════════════════════════════════════════
#
# ★ 요청 안에서 긁지 않습니다.
#   리포트를 여는 길에 카드를 긁으면, 손님이 안 오면 안 걷히고
#   (그건 구독이 아닙니다) 오면 화면이 결제 응답만큼 멈춥니다.
#   `scripts/renew.py` 가 밖에서 돕니다.
def due(sub: dict, now: Optional[datetime] = None) -> bool:
    """오늘 긁을 때가 되었는가."""
    now = now or _now()
    if sub.get("status") == "dead" or sub.get("ending"):
        return False
    if sub.get("fails", 0) >= MAX_FAILS:
        return False
    ends = _at(sub.get("period_end"))
    return bool(ends and ends <= now)


def renew(sub: dict, now: Optional[datetime] = None) -> dict:
    """
    한 건 긁는다. 돌려주는 것: {"ok": bool, "reason": str|None}

    ★ 실패해도 바로 안 끊습니다. 사흘은 열어 두고 다시 겁니다
      (GRACE_DAYS). 네 번 실패하면 그만 긁고 **끊습니다** — 계속
      긁으면 카드사가 우리를 막습니다.
    """
    now = now or _now()
    try:
        key = payments.unseal(sub["billing_key"])
    except payments.PaymentError as e:
        sub.update(status="dead", last_error=str(e))
        _save(sub)
        return {"ok": False, "reason": str(e)}

    order_id = "sjd_sub_" + uuid.uuid4().hex[:16]
    try:
        result = payments.charge_billing(
            key, sub["customer_key"], sub["amount"], order_id,
            payments.TIER_NAME["sub"])
    except payments.PaymentError as e:
        fails = sub.get("fails", 0) + 1
        sub.update(fails=fails, last_error=str(e),
                   last_try=now.isoformat())
        if fails >= MAX_FAILS:
            sub.update(status="dead", billing_key="")
        _save(sub)
        return {"ok": False, "reason": str(e), "fails": fails}

    # ★ 다음 기간은 **끝난 날부터** 셉니다. 오늘부터 세면 갱신이
    #   늦어질 때마다 손님이 하루씩 손해 봅니다.
    base = _at(sub.get("period_end")) or now
    ends = max(base, now - timedelta(days=GRACE_DAYS)) \
        + timedelta(days=PERIOD_DAYS)
    sub.update(period_end=ends.isoformat(), months=sub.get("months", 1) + 1,
               fails=0, last_error=None)
    sub.setdefault("orders", []).append(order_id)
    _save(sub)
    _write_order(sub, order_id, result.pg_tid, now, ends, first=False)
    return {"ok": True, "order_id": order_id, "period_end": ends.isoformat()}


def retire(sub: dict) -> None:
    """
    끝난 구독의 **카드 열쇠를 버립니다.**

    ★ 그만둔 사람의 카드를 계속 들고 있을 까닭이 없습니다. 들고 있으면
      언젠가 실수로 긁힙니다. 기록(몇 달 들었는가)은 남기고 열쇠만
      버립니다.
    """
    sub.update(status="dead", billing_key="", retired_at=_now().isoformat())
    _save(sub)
