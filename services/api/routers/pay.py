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
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import payments
import store
from engine.relay import BREAKS
from schemas.api import Tier

router = APIRouter(prefix="/v1/pay", tags=["pay"])

DAY = 86400


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
            "per_month": tier == "sub",
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
    order.update(status="paid", payment_key=result.pg_tid, unlocked=unlocked)
    store.set_json("order:" + req.order_id, order, ttl=30 * DAY)

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
    store.set_json("order:" + req.order_id, order, ttl=30 * DAY)
    return {"ok": True, "status": "refunded",
            "reissue": bool(req.calc_error)}


@router.get("/order/{order_id}")
def get_order(order_id: str) -> dict:
    order = store.get_json("order:" + order_id)
    if not order:
        raise HTTPException(status_code=404, detail="모르는 주문이오.")
    # 내부 키는 내려보내지 않는다
    return {k: v for k, v in order.items() if k != "payment_key"}
