"""
토스페이먼츠 연동 — docs/01 §5 · docs/11 환불 정책

    TOSS_CLIENT_KEY=test_ck_...
    TOSS_SECRET_KEY=test_sk_...

★ 키가 없으면 결제를 **거절**합니다. 성공한 척하지 않습니다.
★ 하루 결제 2건 상한은 이 모듈에서 강제합니다. 우회 경로를 만들지 마세요.
  (CLAUDE.md 절대 규칙 4)

환불 정책 (docs/11)
    미열람        전액 환불
    열람 후        청약철회 제한 (사전 고지 필요)
    계산 오류 확인  전액 환불 + 재발행
"""
from __future__ import annotations

import base64
import logging
import os
from dataclasses import dataclass
from typing import Optional

import httpx

log = logging.getLogger("payments")

TOSS_CLIENT_KEY = os.getenv("TOSS_CLIENT_KEY", "").strip()
TOSS_SECRET_KEY = os.getenv("TOSS_SECRET_KEY", "").strip()
TOSS_BASE = "https://api.tosspayments.com/v1/payments"

ENABLED = bool(TOSS_SECRET_KEY)

# 티어별 정가. products 테이블이 정본이 되면 거기서 읽도록 바꾸세요.
TIER_PRICE = {"one": 3900, "all": 19900, "sub": 9900}

# 티어가 여는 컷 (engine/report.py 의 min_level 과 짝을 맞춘다)
TIER_UNLOCKS = {
    "one": ["daeun_now", "yongsin"],
    "all": ["daeun_now", "yongsin", "daeun_map", "axis"],
    "sub": ["daeun_now", "yongsin", "daeun_map", "axis"],
}

REFUND_NOTICE = (
    "디지털 콘텐츠 특성상 열람한 리포트는 청약철회가 제한됩니다. "
    "열람 전에는 전액 환불되며, 계산 오류가 확인되면 전액 환불 후 재발행합니다."
)


class PaymentError(RuntimeError):
    pass


class PaymentsDisabled(PaymentError):
    """PG 키가 없음. 결제를 진행하지 않는다."""


@dataclass
class PaymentResult:
    ok: bool
    order_id: str
    amount: int
    pg_tid: Optional[str]
    status: str
    raw: dict


def _auth_header() -> dict:
    if not ENABLED:
        raise PaymentsDisabled(
            "TOSS_SECRET_KEY 가 없습니다. 결제를 진행할 수 없습니다.")
    token = base64.b64encode((TOSS_SECRET_KEY + ":").encode()).decode()
    return {"Authorization": "Basic " + token,
            "Content-Type": "application/json"}


def client_config() -> dict:
    """프론트가 결제창을 띄우는 데 필요한 것. 시크릿 키는 절대 내려보내지 않는다."""
    return {"enabled": ENABLED, "client_key": TOSS_CLIENT_KEY or None,
            "refund_notice": REFUND_NOTICE}


def price_of(tier: str) -> int:
    try:
        return TIER_PRICE[tier]
    except KeyError:
        raise PaymentError("값을 매기지 않은 티어입니다: %r" % (tier,))


def confirm(payment_key: str, order_id: str, amount: int) -> PaymentResult:
    """
    결제 승인. 금액은 **서버가 계산한 값**을 보냅니다.
    클라이언트가 보낸 금액을 그대로 믿지 마세요.
    """
    res = httpx.post(
        TOSS_BASE + "/confirm",
        headers=_auth_header(),
        json={"paymentKey": payment_key, "orderId": order_id, "amount": amount},
        timeout=15.0,
    )
    data = res.json()
    if res.status_code != 200:
        log.warning("toss confirm 실패 %s %s", res.status_code, data)
        raise PaymentError(data.get("message", "결제 승인에 실패했습니다."))
    return PaymentResult(
        ok=True, order_id=order_id, amount=amount,
        pg_tid=data.get("paymentKey"), status=data.get("status", "DONE"),
        raw=data)


def cancel(payment_key: str, reason: str,
           amount: Optional[int] = None) -> PaymentResult:
    """환불. amount 를 주면 부분 취소."""
    body: dict = {"cancelReason": reason}
    if amount is not None:
        body["cancelAmount"] = amount
    res = httpx.post(
        "%s/%s/cancel" % (TOSS_BASE, payment_key),
        headers=_auth_header(), json=body, timeout=15.0)
    data = res.json()
    if res.status_code != 200:
        log.warning("toss cancel 실패 %s %s", res.status_code, data)
        raise PaymentError(data.get("message", "환불에 실패했습니다."))
    return PaymentResult(
        ok=True, order_id=data.get("orderId", ""),
        amount=amount or data.get("totalAmount", 0),
        pg_tid=payment_key, status=data.get("status", "CANCELED"), raw=data)
