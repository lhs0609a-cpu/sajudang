"""
결제 — docs/01 §5 · docs/11

    GET  /v1/pay/config    결제창에 필요한 공개 정보 (시크릿 키 제외)
    POST /v1/pay/tiers     목패 셋 — 값과 **이 명식으로 실제 열리는 자리 수**
    POST /v1/pay/prepare   주문 생성. 금액은 서버가 정한다.
    POST /v1/pay/confirm   승인 → 인장 지급 · 잠금 해제
    POST /v1/pay/refund    환불 (열람 전 전액 / 계산 오류 전액)

★ 하루 결제 2건 상한을 여기서 강제합니다. (CLAUDE.md 절대 규칙 4)
★ 금액은 클라이언트가 보낸 값을 믿지 않고 서버가 티어에서 계산합니다.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

import payments
import store
from engine.relay import BREAKS
from schemas.api import Tier

log = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/pay", tags=["pay"])

DAY = 86400

# 「한 달 듣기」가 며칠인가.
#
# ★ 이 값을 「달마다」로 팔면서 **끝나지 않았습니다.**
#   빌링키도 자동결제도 없습니다. 9,900원을 한 번 받고 끝인데
#   entitled_tier 는 그 주문을 보고 **영원히** 스무 사람을 열어 줬습니다.
#   한 달치 값에 영구 이용권을 준 셈입니다.
#
# ★ 자동결제를 붙이지 않았습니다.
#   정기결제는 빌링키 발급·PG 심사·해지 화면이 따로 붙는 일입니다.
#   그전까지는 **한 번 치르고 서른 날**로 정직하게 팝니다 —
#   저절로 다시 빠져나가지 않습니다. 목패도 그렇게 적습니다.
SUB_DAYS = 30


def _user_key(session_id: str) -> str:
    return hashlib.sha256(session_id.encode()).hexdigest()[:16]


def _today() -> str:
    return date.today().isoformat()


def _purchases_today(session_id: str) -> int:
    return store.get_int(store.k_purchase_day(_user_key(session_id), _today()))


class PrepareRequest(BaseModel):
    session_id: str
    chart_id: str
    lens_id: str
    tier: Tier
    concern: str = "love"


class PrepareResponse(BaseModel):
    order_id: str
    amount: int
    tier: str
    client_key: Optional[str]
    enabled: bool
    refund_notice: str
    # ★ 같은 약속을 이 집의 말로. 결제 버튼 바로 위에 놓입니다.
    refund_say: str
    purchases_today: int
    per_day_limit: int


class ConfirmRequest(BaseModel):
    session_id: str
    order_id: str
    payment_key: str = Field(min_length=1)


class RefundRequest(BaseModel):
    order_id: str
    reason: str = Field(min_length=2, max_length=200)
    opened: bool = False          # 열람 후면 청약철회 제한
    calc_error: bool = False      # 계산 오류로 확인된 건은 항상 전액 환불


@router.get("/config")
def get_config() -> dict:
    return payments.client_config()


# ══════════════════════════════════════════════════════════
# 목패 셋 — 무엇을 얼마에 파는가
# ══════════════════════════════════════════════════════════
#
# ★ 화면이 값과 분량을 제 손으로 적고 있었습니다.
#   apps/web/lib/store.ts 의 TIERS 가 "평생운 18컷 · 25페이지" 라고
#   적어 두었는데, 실제로 나오는 것은 11~12컷 · 6탭이었습니다.
#   값도 마찬가지로 카드와 결제가 서로 달랐습니다.
#
#   이제 **서버가 세어서 내려보냅니다.** 화면은 받아 적기만 합니다.
#   리포트를 만드는 그 함수로 세므로 어긋날 수가 없습니다.
class TiersRequest(BaseModel):
    chart_id: str
    lens_id: str
    concern: str = "love"
    axis4: Optional[str] = None


# 목패 이름·설명은 payments.py 에 한 벌만 둡니다. 값 바로 옆에 있어야
# 이름만 고치고 값을 안 고치는 일이 안 생깁니다.
TIER_NAME = payments.TIER_NAME
TIER_NOTE = payments.TIER_NOTE

# 한 컷을 읽는 데 걸리는 시간. 한글 산문 기준으로 잡았습니다.
# 분량을 '컷' 이라는 우리 말로만 적으면 손님은 그게 얼마인지 모릅니다.
CHARS_PER_MINUTE = 550


def _plain_len(html: str) -> int:
    import re
    return len(re.sub(r"<[^>]+>", "", html or "").strip())


def _measure(rep: dict) -> tuple:
    """(컷 수, 글자 수). 서버가 셉니다 — 화면이 적지 않습니다."""
    return len(rep["cuts"]), sum(_plain_len(c["html"]) for c in rep["cuts"])


@router.post("/tiers")
def get_tiers(req: TiersRequest) -> dict:
    """
    이 사람이 티어마다 **실제로** 무엇을 받는가.

    부풀리지도 줄이지도 않습니다 — build_report 로 세어서 그대로 냅니다.

    ★ `all` · `sub` 은 이 캐릭터 몫만 세면 안 됩니다.
      그 둘은 **스무 사람을 전부** 엽니다. 한 사람 몫(18컷)만 적어 두면
      9,900원짜리 달삯과 견줄 때 같은 것으로 보입니다. 실제로 여는 것을
      세서 적습니다 — 스무 사람 합계입니다.
    """
    from engine import lens as lens_mod
    from engine.features import Features
    from engine.report import build_report
    from routers.chart import load_features

    f = Features(**load_features(req.chart_id))
    released = [l["id"] for l in lens_mod.released()]

    out = []
    for tier in ("one", "all", "sub"):
        try:
            price = payments.price_of(tier, req.lens_id)
        except payments.PaymentError:
            continue                      # 값 없는 캐릭터의 '이 자리 하나'

        rep = build_report(f, req.chart_id, req.lens_id, tier, req.concern,
                           req.axis4)
        cuts, chars = _measure(rep)
        lenses = 1
        # 열리는 자리의 이름. 목패에 적으면 손님이 무엇을 사는지 압니다.
        opens = [c["title"] for c in rep["locked"]]

        if tier in ("all", "sub"):
            # 스무 사람 전부를 실제로 세어 합칩니다.
            cuts = chars = 0
            for lid in released:
                r = build_report(f, req.chart_id, lid, tier, req.concern,
                                 req.axis4)
                c, ch = _measure(r)
                cuts += c
                chars += ch
            lenses = len(released)
            opens = []

        out.append({
            "id": tier,
            "name": TIER_NAME[tier],
            "price": price,
            # ★ 「달마다」가 아닙니다 — 빌링키도 자동결제도 없습니다.
            #   한 번 치르고 서른 날입니다. 저절로 다시 안 빠져나갑니다.
            "per_month": False,
            "days": SUB_DAYS if tier == "sub" else None,
            "forever": tier in ("one", "all"),
            "note": TIER_NOTE[tier],
            # ★ 센 것을 그대로. 사람마다 다릅니다.
            "cuts": cuts,
            "chars": chars,
            "minutes": max(1, round(chars / CHARS_PER_MINUTE)),
            "lenses": lenses,
            "locked": len(rep["locked"]) if tier == "one" else 0,
            "opens": opens,
        })
    return {"tiers": out, "lens_id": req.lens_id,
            "refund_notice": payments.REFUND_NOTICE,
            "refund_say": payments.REFUND_SAY}


@router.post("/prepare", response_model=PrepareResponse)
def prepare(req: PrepareRequest) -> PrepareResponse:
    limit = BREAKS()["per_day_purchase"]
    used = _purchases_today(req.session_id)
    if used >= limit:
        # 브레이크. 우회 파라미터를 만들지 마세요.
        raise HTTPException(
            status_code=429,
            detail="하루에 %d건까지만 받소. 내일 다시 오시오." % limit)

    # ★ 값은 캐릭터마다 다릅니다 — 카드에 보인 값이 그대로 청구됩니다.
    try:
        amount = payments.price_of(req.tier, req.lens_id)
    except payments.PaymentError as e:
        raise HTTPException(status_code=422, detail=str(e))
    order_id = "sjd_" + uuid.uuid4().hex[:20]
    store.set_json("order:" + order_id, {
        "session_id": req.session_id, "chart_id": req.chart_id,
        "lens_id": req.lens_id, "tier": req.tier, "concern": req.concern,
        "amount": amount, "status": "pending", "payment_key": None,
    }, ttl=DAY)

    cfg = payments.client_config()
    return PrepareResponse(
        order_id=order_id, amount=amount, tier=req.tier,
        client_key=cfg["client_key"], enabled=cfg["enabled"],
        refund_notice=cfg["refund_notice"],
        refund_say=payments.REFUND_SAY,
        purchases_today=used, per_day_limit=limit)


@router.post("/confirm")
def confirm(req: ConfirmRequest) -> dict:
    order = store.get_json("order:" + req.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="모르는 주문이오.")
    if order["status"] == "paid":
        return {"ok": True, "already": True, "unlocked": order.get("unlocked", [])}

    limit = BREAKS()["per_day_purchase"]
    if _purchases_today(req.session_id) >= limit:
        raise HTTPException(status_code=429,
                            detail="하루에 %d건까지만 받소." % limit)

    try:
        # 금액은 주문에 적힌 서버 계산값을 쓴다
        result = payments.confirm(req.payment_key, req.order_id, order["amount"])
    except payments.PaymentsDisabled as e:
        raise HTTPException(status_code=503, detail=str(e))
    except payments.PaymentError as e:
        raise HTTPException(status_code=402, detail=str(e))

    unlocked = payments.unlocks_for(order["tier"], order.get("lens_id"))

    # ★ 산 때와 끝나는 때를 적습니다.
    #
    #   전에는 주문을 `ttl=30*DAY` 로 저장했습니다. entitled_tier 가 그
    #   주문을 읽어 자격을 보는데, 서른 날이 지나면 주문이 사라지고
    #   자격이 조용히 free 로 떨어졌습니다 — **영구라고 판 것을 값을
    #   치른 사람이 잃었습니다.** 목패에는 "영구" 라 적혀 있었습니다.
    #
    #   이제 치른 주문은 **지우지 않습니다**(ttl 없음). 끝나는 때는
    #   기록으로 판정합니다 — 사라져서 끝나는 것이 아니라, 적힌 날에
    #   끝납니다. 그래야 무엇이 언제 끝나는지 손님에게 말할 수 있습니다.
    now = datetime.now(timezone.utc)
    ends = (now + timedelta(days=SUB_DAYS)) if order["tier"] == "sub" else None
    order.update(status="paid", payment_key=result.pg_tid, unlocked=unlocked,
                 paid_at=now.isoformat(),
                 expires_at=ends.isoformat() if ends else None)
    store.set_json("order:" + req.order_id, order)

    # 하루 결제 카운터 · 인장
    store.incr(store.k_purchase_day(_user_key(req.session_id), _today()), ttl=DAY)

    # 이 세션이 치른 주문 목록. 스무 사람 종합이 이걸 보고 자격을 봅니다.
    # 클라이언트가 보낸 tier 를 믿으면 요청 한 줄로 8만 자가 빠져나갑니다.
    okey = "orders:" + req.session_id
    orders = store.get_json(okey) or []
    if req.order_id not in orders:
        orders.append(req.order_id)
        store.set_json(okey, orders, ttl=365 * DAY)

    seals_key = "seals:" + _user_key(req.session_id)
    seals = store.get_json(seals_key) or []
    if order["lens_id"] not in seals:
        seals.append(order["lens_id"])
        store.set_json(seals_key, seals)

    # ★ 값을 치른 직후에 **무엇을 얻었는지**를 세어 함께 보냅니다.
    #
    #   완료 화면이 "붉은 끈이 풀렸다 / 이제 나머지를 보시오" 한 줄이었습니다.
    #   사람은 경험의 정점과 **끝**으로 전체를 기억합니다. 재구매·후기·추천이
    #   갈리는 자리인데 방금 무엇을 얻었는지가 화면에 없었습니다.
    #   화면이 제 손으로 세지 않게, 여기서 세어 내려보냅니다.
    got = _granted(order)

    return {"ok": True, "tier": order["tier"], "unlocked": unlocked,
            "seal": order["lens_id"], "refund_notice": payments.REFUND_NOTICE,
            "granted": got}


def _granted(order: dict) -> dict:
    """이 결제로 실제로 열린 것. 세어서 냅니다 — 부풀리지 않습니다."""
    from engine import lens as lens_mod
    from engine.features import Features
    from engine.report import build_report
    from routers.chart import load_features

    tier, lens_id = order["tier"], order.get("lens_id")
    try:
        f = Features(**load_features(order["chart_id"]))
    except Exception:
        # 명식 캐시가 지워졌으면 세지 않습니다. 지어내지 않습니다.
        return {"counted": False}

    ids = ([l["id"] for l in lens_mod.released()]
           if tier in ("all", "sub") else [lens_id])
    cuts = chars = 0
    for lid in ids:
        if not lid:
            continue
        try:
            r = build_report(f, order["chart_id"], lid, tier,
                             order.get("concern", "love"))
        except Exception:
            continue
        c, ch = _measure(r)
        cuts += c
        chars += ch
    return {
        "counted": True,
        "cuts": cuts,
        "chars": chars,
        "minutes": max(1, round(chars / CHARS_PER_MINUTE)),
        "lenses": len(ids),
        "tier_name": TIER_NAME.get(tier, tier),
    }


# ══════════════════════════════════════════════════════════
# 웹훅 — 결제 상태가 바뀌었다는 **알림**
# ══════════════════════════════════════════════════════════
#
# ★ 본문을 믿지 않습니다.
#   토스 웹훅에는 서명 헤더가 문서화돼 있지 않습니다. 그러면 본문만
#   보고는 그게 토스가 보낸 것인지 알 수 없습니다 — 주소만 알면 누구나
#   "이 주문 결제됐다" 고 POST 할 수 있습니다. 무료로 스무 사람을 여는
#   요청 한 줄이 됩니다.
#
#   그래서 웹훅은 **깨우는 종**으로만 씁니다. 무엇이 참인지는 우리가
#   시크릿 키로 토스에 되물어 정합니다(payments.lookup_by_order).
#   화면이 보낸 tier 를 안 믿는 것과 같은 이유입니다.
#
# ★ 무엇을 위해 붙였나
#   가상계좌 입금(DEPOSIT_CALLBACK)과 **PG 쪽에서 일어난 취소**를
#   우리가 알 길이 없었습니다. 토스 관리자 화면에서 취소해도 이쪽은
#   계속 열려 있었습니다.
#
# ★ 10초 안에 200 을 줘야 합니다. 안 주면 토스가 7번 다시 보냅니다
#   (1·4·16·64·256·1024·4096분). 그래서 못 알아들은 것도 200 입니다 —
#   재시도로 풀릴 문제가 아니면 다시 받아도 같습니다.
@router.post("/webhook")
async def webhook(request: Request) -> dict:
    try:
        body = await request.json()
    except Exception:
        return {"ok": True, "ignored": "본문을 읽지 못했소"}

    order_id = (body or {}).get("data", {}).get("orderId") or (body or {}).get("orderId")
    if not order_id:
        return {"ok": True, "ignored": "주문번호가 없소"}

    order = store.get_json("order:" + str(order_id))
    if not order:
        return {"ok": True, "ignored": "모르는 주문이오"}

    # ★ 여기가 요점입니다 — 본문이 아니라 토스에게 묻습니다.
    try:
        real = payments.lookup_by_order(str(order_id))
    except payments.PaymentError as e:
        log.warning("webhook lookup 실패 %s: %s", order_id, e)
        # 우리 쪽 사정이면 다시 받아 볼 값이 있습니다.
        raise HTTPException(status_code=503, detail="확인하지 못했소.")

    status = real.get("status")
    if status in payments.DEAD_STATES or (
            status == "PARTIAL_CANCELED" and not real.get("balanceAmount")):
        # 취소·만료 — 자격을 거둡니다. 기록은 남깁니다.
        order.update(status="canceled", unlocked=[], pg_status=status)
        store.set_json("order:" + str(order_id), order)
        return {"ok": True, "applied": "canceled"}

    if status in payments.PAID_STATES and order.get("status") != "paid":
        # 가상계좌 입금처럼 나중에 완결되는 건. 금액도 토스 것을 씁니다.
        now = datetime.now(timezone.utc)
        ends = (now + timedelta(days=SUB_DAYS)) if order["tier"] == "sub" else None
        order.update(
            status="paid", pg_status=status,
            payment_key=real.get("paymentKey") or order.get("payment_key"),
            amount=int(real.get("totalAmount") or order.get("amount") or 0),
            unlocked=payments.unlocks_for(order["tier"], order.get("lens_id")),
            paid_at=now.isoformat(),
            expires_at=ends.isoformat() if ends else None)
        store.set_json("order:" + str(order_id), order)

        okey = "orders:" + str(order.get("session_id") or "")
        orders = store.get_json(okey) or []
        if str(order_id) not in orders:
            orders.append(str(order_id))
            store.set_json(okey, orders, ttl=365 * DAY)
        return {"ok": True, "applied": "paid"}

    return {"ok": True, "applied": "none", "status": status}


# ══════════════════════════════════════════════════════════
# 자격 복구 — 산 것을 잃지 않게
# ══════════════════════════════════════════════════════════
#
# ★ 로그인이 없습니다. 자격이 localStorage 난수(session_id)에 매여
#   있어서, 손님이 브라우저 데이터를 지우거나 기기를 바꾸면 **치른 값을
#   통째로 잃었습니다.** 24,900원짜리를요. 되찾아 줄 길조차 없었습니다.
#
# ★ 주문번호는 결제 영수증과 승인 문자에 남습니다. 그걸로 되찾습니다.
#   그리고 여기서도 **토스에 되물어** 실제로 치러진 주문인지 봅니다 —
#   주문번호를 아무렇게나 넣어 보는 길을 막습니다.
class RestoreRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)
    order_id: str = Field(min_length=4, max_length=64)


@router.post("/restore")
def restore(req: RestoreRequest) -> dict:
    order = store.get_json("order:" + req.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="그런 주문번호가 없소.")

    if order.get("status") != "paid":
        # 치르지 않은 주문으로는 못 엽니다.
        try:
            real = payments.lookup_by_order(req.order_id)
        except payments.PaymentError:
            raise HTTPException(status_code=409, detail="아직 치러지지 않은 주문이오.")
        if real.get("status") not in payments.PAID_STATES:
            raise HTTPException(status_code=409, detail="아직 치러지지 않은 주문이오.")

    okey = "orders:" + req.session_id
    orders = store.get_json(okey) or []
    if req.order_id not in orders:
        orders.append(req.order_id)
        store.set_json(okey, orders, ttl=365 * DAY)

    # 인장도 같이 되돌려 줍니다.
    if order.get("lens_id"):
        skey = "seals:" + _user_key(req.session_id)
        seals = store.get_json(skey) or []
        if order["lens_id"] not in seals:
            seals.append(order["lens_id"])
            store.set_json(skey, seals, ttl=365 * DAY)

    return {"ok": True, "tier": order["tier"], "lens_id": order.get("lens_id"),
            "expires_at": order.get("expires_at"),
            "say": "찾았소. 치르신 자리를 되돌려 놓았소."}


@router.post("/refund")
def refund(req: RefundRequest) -> dict:
    order = store.get_json("order:" + req.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="모르는 주문이오.")
    if order["status"] != "paid":
        raise HTTPException(status_code=409, detail="결제된 주문이 아니오.")

    # docs/11 — 열람 후에는 청약철회 제한. 다만 계산 오류는 언제나 전액 환불.
    if req.opened and not req.calc_error:
        raise HTTPException(
            status_code=409,
            detail=("이미 열람하신 리포트는 청약철회가 제한됩니다. "
                    "계산이 틀린 것이 확인되면 전액 환불해 드립니다."))

    try:
        payments.cancel(order["payment_key"], req.reason)
    except payments.PaymentsDisabled as e:
        raise HTTPException(status_code=503, detail=str(e))
    except payments.PaymentError as e:
        raise HTTPException(status_code=402, detail=str(e))

    order.update(status="refunded", unlocked=[])
    # 환불된 주문도 지우지 않습니다 — 무엇을 돌려줬는지 남아야 합니다.
    store.set_json("order:" + req.order_id, order)
    return {"ok": True, "status": "refunded",
            "reissue": bool(req.calc_error)}


@router.get("/order/{order_id}")
def get_order(order_id: str) -> dict:
    order = store.get_json("order:" + order_id)
    if not order:
        raise HTTPException(status_code=404, detail="모르는 주문이오.")
    # 내부 키는 내려보내지 않는다
    return {k: v for k, v in order.items() if k != "payment_key"}
