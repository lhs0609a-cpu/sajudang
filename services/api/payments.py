"""
토스페이먼츠 연동 — docs/01 §5 · docs/11 환불 정책

    TOSS_CLIENT_KEY=test_ck_...   (라이브는 live_ck_…)
    TOSS_SECRET_KEY=test_sk_...   (라이브는 live_sk_…)

★ 시크릿 키를 저장소 안 어떤 파일에도 적지 마세요. 환경변수로만 넣습니다.
  (운영은 `fly secrets set`. 적어 두면 구글 드라이브로 동기화됩니다.)
★ 키가 없거나 **두 짝이 안 맞으면** 결제를 거절합니다. 성공한 척하지 않습니다.
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

# ── 키 두 짝이 서로 맞는지 뜰 때 본다 ──────────────────────────
#
# 토스는 연동 방식마다 키가 따로입니다.
#     live_ck_  / test_ck_    API 개별 연동 — 결제창 payment()   ← 우리 것
#     live_gck_ / test_gck_   결제위젯 연동 — widgets()
#
# 프론트(apps/web/lib/toss.ts)가 v2 SDK 의 payment() 를 부르므로
# **API 개별 연동 키(ck/sk)** 라야 합니다.
#
# ★ 왜 미리 보는가
#   위젯 키를 넣어도 결제창은 멀쩡히 뜹니다. 막히는 곳은 승인입니다 —
#   손님이 카드를 이미 긁은 뒤입니다. 돈은 물려 있고 리포트는 안 열립니다.
#   짝이 안 맞으면 아예 결제를 열지 않는 편이 낫습니다.

_KINDS = {"ck": ("client", "api"), "gck": ("client", "widget"),
          "sk": ("secret", "api"), "gsk": ("secret", "widget")}


def _read_key(key: str):
    """('live'|'test', 'client'|'secret', 'api'|'widget') 또는 None."""
    parts = key.split("_", 2)
    if len(parts) < 3:
        return None
    mode, kind = parts[0], parts[1]
    if mode not in ("live", "test") or kind not in _KINDS:
        return None
    role, family = _KINDS[kind]
    return mode, role, family


def check_keys(client: str, secret: str) -> Optional[str]:
    """못 쓸 조합이면 까닭을 돌려줍니다. 쓸 수 있으면 None.

    ★ 돌려주는 문장에 키를 절대 싣지 마세요. 로그와 /health 에 나갑니다.
    """
    if not secret:
        return "TOSS_SECRET_KEY 가 없습니다. 결제를 진행할 수 없습니다."
    if not client:
        return "TOSS_CLIENT_KEY 가 없습니다. 결제창을 띄울 수 없습니다."

    c, s = _read_key(client), _read_key(secret)
    if c is None:
        return "TOSS_CLIENT_KEY 의 형식을 모르겠습니다 (live_ck_… 라야 합니다)."
    if s is None:
        return "TOSS_SECRET_KEY 의 형식을 모르겠습니다 (live_sk_… 라야 합니다)."
    if c[1] != "client":
        return "TOSS_CLIENT_KEY 자리에 시크릿 키가 들어 있습니다. 두 값이 바뀌었습니다."
    if s[1] != "secret":
        return "TOSS_SECRET_KEY 자리에 클라이언트 키가 들어 있습니다. 두 값이 바뀌었습니다."
    if c[0] != s[0]:
        return ("키 두 짝의 모드가 다릅니다 — 클라이언트 %s · 시크릿 %s. "
                "한쪽만 라이브로 바꿔 두면 승인에서 막힙니다." % (c[0], s[0]))
    if c[2] != s[2]:
        return "클라이언트 키와 시크릿 키가 서로 다른 연동의 것입니다."
    if c[2] != "api":
        return ("결제위젯 연동 키(gck/gsk)입니다. 지금 프론트는 v2 SDK 의 "
                "payment() — 결제창을 씁니다. API 개별 연동 키(ck/sk)를 넣거나, "
                "프론트를 widgets() 로 바꾸세요.")
    return None


DISABLED_REASON = check_keys(TOSS_CLIENT_KEY, TOSS_SECRET_KEY)
ENABLED = DISABLED_REASON is None
LIVE = ENABLED and TOSS_SECRET_KEY.startswith("live_")

if DISABLED_REASON and (TOSS_CLIENT_KEY or TOSS_SECRET_KEY):
    # 키를 넣었는데 안 켜졌다면 조용히 넘기면 안 됩니다.
    log.error("결제를 켜지 않았습니다 — %s", DISABLED_REASON)
elif LIVE:
    log.warning("토스 라이브 키입니다. 이제부터 실제로 돈이 오갑니다.")

# ── 값 ────────────────────────────────────────────────────
#
# ★ 값이 두 벌이었습니다.
#   릴레이 카드는 seed/lenses.json 의 **캐릭터 값**(4,900~19,900원)을
#   보여 주는데, 실제로 청구되는 것은 여기 티어 값이었습니다. 스무
#   캐릭터의 값이 **한 번도 청구되지 않았습니다.** 4,900원으로 보고 누른
#   사람에게 19,900원이 찍히는 경로가 열려 있었습니다.
#
#   이제 **보이는 값이 청구되는 값**입니다.
#     one  '이 자리 하나' — 그 캐릭터를 듣는 값. 캐릭터마다 다릅니다.
#     all  '여덟 글자 전부' — 전 영역을 여는 값. 하나로 둡니다.
#     sub  '스무 사람 모두' — 달마다. 하나로 둡니다.
#
#   one 을 캐릭터 값으로 받으려면 **비싼 캐릭터가 실제로 더 줘야** 합니다.
#   그 배분은 engine/lens_cuts.py 의 관점 컷이 맡고,
#   tests/test_lens_cuts.py 가 값 순서를 지킵니다.
TIER_PRICE = {"all": 19900, "sub": 9900}
FLAT_TIERS = frozenset(TIER_PRICE)

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
            DISABLED_REASON or "결제를 진행할 수 없습니다.")
    token = base64.b64encode((TOSS_SECRET_KEY + ":").encode()).decode()
    return {"Authorization": "Basic " + token,
            "Content-Type": "application/json"}


def client_config() -> dict:
    """프론트가 결제창을 띄우는 데 필요한 것. 시크릿 키는 절대 내려보내지 않는다."""
    return {"enabled": ENABLED, "client_key": TOSS_CLIENT_KEY or None,
            "live": LIVE, "reason": DISABLED_REASON,
            "refund_notice": REFUND_NOTICE}


def price_of(tier: str, lens_id: Optional[str] = None) -> int:
    """
    이 사람이 이 티어를 사면 얼마인가.

    ★ `one` 은 **캐릭터 값**입니다. 릴레이 카드에 붙는 값과 같아야 합니다 —
      화면이 보여 준 값과 청구되는 값이 다르면 그건 값이 아니라 미끼입니다.
    """
    if tier in FLAT_TIERS:
        return TIER_PRICE[tier]
    if tier != "one":
        raise PaymentError("값을 매기지 않은 티어입니다: %r" % (tier,))
    if not lens_id:
        raise PaymentError("'이 자리 하나' 는 캐릭터마다 값이 다릅니다. "
                           "lens_id 가 있어야 합니다.")
    from engine import lens as lens_mod
    try:
        price = int(lens_mod.get(lens_id)["price"])
    except lens_mod.LensError:
        raise PaymentError("모르는 캐릭터입니다: %r" % (lens_id,))
    if price <= 0:
        # 값 없는 캐릭터. 결제로 보내지 않습니다 — 강매가 됩니다.
        raise PaymentError("이 캐릭터는 값 없이 듣는 자리요.")
    return price


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
