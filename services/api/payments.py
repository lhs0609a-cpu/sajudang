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
#
# ★ 그런데 값이 **서로를 잡아먹고 있었습니다.**
#   `all` 이 19,900원이었는데 가장 비싼 캐릭터도 19,900원이었습니다.
#   풍운도령에서는 「이 자리 하나」와 「여덟 글자 전부」가 값도 컷 수도
#   똑같았습니다 — 같은 상품이 두 장 놓여 있던 것입니다.
#   그리고 `sub`(9,900원/월)이 `all` 과 여는 것이 글자 그대로 같아서,
#   첫 달만 보면 `all` 은 **두 배 값에 같은 것**이었습니다.
#
#   두 가지를 고쳤습니다.
#     ① `all` 을 가장 비싼 캐릭터보다 **위로** 올립니다. 그래야 세 목패에
#        순서가 생깁니다.  one(4,900~19,900) < all(24,900)
#     ② `all` 과 `sub` 의 차이를 **내용이 아니라 기간**으로 말합니다.
#        둘은 같은 것을 엽니다 — 하나는 한 번 치르고 영구, 하나는 달마다.
#        목패가 그렇게 적어야 합니다 (routers/pay.TIER_NOTE).
#
#   ★ ①은 값을 올리는 결정입니다. 되돌리려면 이 상수 하나만 고치면
#     됩니다. 다만 되돌릴 때는 `one` 의 최고가도 같이 내려야 합니다 —
#     tests/test_pay.py 의 지배 검사가 그걸 셉니다.
TIER_PRICE = {"all": 24900, "sub": 9900}
FLAT_TIERS = frozenset(TIER_PRICE)

# 티어가 여는 컷 (engine/report.py 의 min_level 과 짝을 맞춘다)
# ══════════════════════════════════════════════════════════
# 목패 이름 — ★ 한 벌만 둡니다
# ══════════════════════════════════════════════════════════
#
# ★ 이름이 두 곳에 있었습니다.
#   `routers/pay.py` 가 목패 이름을 들고 있었고, 페이월 화면
#   (`report/[id]` c4) 이 **제 손으로 다시 적고** 있었습니다.
#   `all` 을 "여덟 글자 전부" 에서 "스무 사람 전부" 로 고쳤을 때
#   화면 쪽은 안 따라와서, 같은 상품을 두 화면이 다른 이름으로
#   부르고 있었습니다. seed/meta.json 의 값·분량을 지운 것과 같은
#   이유입니다 — 두 벌이 되면 어긋납니다.
#
#   값(TIER_PRICE)과 나란히 여기 둡니다. 화면은 받아 적기만 합니다.
TIER_NAME = {"one": "이 자리 하나", "all": "스무 사람 전부",
             "sub": "한 달 듣기"}

# 목패는 **무엇이 다른지**를 말해야 합니다.
#   전에는 `all` 이 "여덟 글자 전부 — 대운 맵과 성향 대조까지" 였습니다.
#   그런데 `all` 을 치르면 실제로는 **스무 사람이 전부** 열립니다
#   (routers/report.entitled_tier 가 모든 캐릭터에 rank 2 를 줍니다).
#   가진 것을 안 적고 있었습니다.
#
#   그리고 `all` 과 `sub` 은 여는 것이 같습니다. 그러니 목패는 그 둘을
#   **내용이 아니라 기간**으로 갈라 말합니다. 안 그러면 손님이 같은 것을
#   두 값에 놓고 고르게 됩니다.
# ★ 목패는 **실제로 일어나는 일**을 적어야 합니다.
#   전에는 「달마다 듣기 · 언제든 그만둘 수 있소」였는데, 빌링키도
#   자동결제도 없습니다. 저절로 다시 빠져나가지 않으니 "그만둘" 것도
#   없습니다. 그런데 자격은 영원히 열려 있었습니다 — 한 달치 값에
#   영구 이용권이었습니다. 이제 서른 날이고, 그렇게 적습니다.
TIER_NOTE = {
    "one": "이 사람 하나를 끝까지 — 값이 오를수록 깊이 들어가오. 영구",
    "all": "스무 사람을 전부, 끝까지. 한 번 치르고 영구",
    "sub": "스무 사람을 넓게, 서른 날. 저절로 다시 빠져나가지 않소",
}

# ★ `sub` 이 `all` 과 **글자 그대로 같은 목록**이었습니다.
#   그래서 9,900원/월이 24,900원을 통째로 덮었고, 그것만이 아니라
#   「이 자리 하나」까지 덮었습니다 — 스무 명 중 **열여섯 명**에서
#   더 싼 달삯이 더 많이 줬습니다. 풍운도령은 19,900원에 22컷 한 사람,
#   달삯은 9,900원에 374컷 스무 사람이었습니다.
#
#   셋을 **다른 축**으로 갈라 세웁니다.
#     one   깊이 — 그 사람 하나를, 값이 여는 층까지 (report.PRICE_RUNGS)
#     sub   넓이 — 스무 사람을, **기본 층만**. 달마다.
#     all   둘 다 — 스무 사람을 끝까지. 한 번 치르고 영구.
#
#   이제 값을 치를 이유가 셋 다 다릅니다. 달삯을 아무리 오래 내도
#   대운 맵과 성향 대조는 안 열립니다 — 그건 깊이를 산 사람의 몫입니다.
TIER_UNLOCKS = {
    "one": ["daeun_now", "yongsin"],
    "all": ["daeun_now", "yongsin", "daeun_map", "axis"],
    "sub": ["daeun_now", "yongsin"],
}


def unlocks_for(tier: str, lens_id: Optional[str] = None) -> list:
    """
    이 결제가 실제로 연 컷.

    ★ 「이 자리 하나」는 캐릭터 값으로 받으므로 **값이 층을 엽니다.**
      표를 여기 또 적지 않고 engine/report.PRICE_RUNGS 를 그대로 봅니다 —
      값이 두 벌이 되면 어긋납니다. 화면이 보는 것과 청구가 보는 것은
      한 표라야 합니다.
    """
    base = list(TIER_UNLOCKS.get(tier, []))
    if tier != "one" or not lens_id:
        return base
    from engine import report as report_mod
    for cid in sorted(report_mod.rungs_at(price_of(tier, lens_id))):
        if cid not in base:
            base.append(cid)
    return base

REFUND_NOTICE = (
    "디지털 콘텐츠 특성상 열람한 리포트는 청약철회가 제한됩니다. "
    "열람 전에는 전액 환불되며, 계산 오류가 확인되면 전액 환불 후 재발행합니다."
)

# ★ 같은 약속을 이 집의 말로 한 번 더 합니다.
#
#   위 고지는 법이 요구하는 문장이라 결제 화면 아래 잔글씨로 갑니다.
#   그런데 그 안에 **점집이 하지 않는 약속**이 하나 들어 있습니다 —
#   "계산 오류가 확인되면 전액 환불 후 재발행".
#   이 집의 포지션을 값으로 증명하는 문장인데 회색 글씨에 묻혀
#   아무도 안 읽고 있었습니다. 결제 버튼 **바로 위**에 이걸 놓습니다.
#
#   무엇을 보증하고 무엇을 보증하지 않는지가 한 문장에 다 들어갑니다.
REFUND_SAY = (
    "셈이 틀렸다면 값을 돌려드리고 다시 세워 드리오. "
    "맞혔는지는 못 따지오만, 셈이 틀린 건 내 잘못이오."
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


def lookup_by_order(order_id: str) -> dict:
    """
    이 주문이 토스 쪽에서 **실제로** 어떤 상태인가.

        GET /v1/payments/orders/{orderId}

    ★ 웹훅 본문을 믿지 않기 위한 자리입니다.
      토스 웹훅에는 서명 헤더가 문서화돼 있지 않습니다. 그러면 본문만
      보고는 그게 토스가 보낸 것인지 알 수 없습니다 — 주소만 알면
      누구나 "이 주문 결제됐다" 고 POST 할 수 있습니다.

      그래서 웹훅은 **알림으로만** 씁니다. 무엇이 참인지는 우리가
      시크릿 키로 토스에 되물어 정합니다. 이 집에서 클라이언트가 보낸
      tier 를 안 믿는 것과 같은 이유입니다.

    돌려주는 것: 토스 응답 그대로(dict). 못 물으면 PaymentError.
    """
    if not ENABLED:
        raise PaymentsDisabled(DISABLED_REASON or "결제가 꺼져 있습니다.")
    res = httpx.get(
        "%s/orders/%s" % (TOSS_BASE, order_id),
        headers=_auth_header(), timeout=10.0)
    data = res.json() if res.content else {}
    if res.status_code >= 400:
        log.warning("toss lookup 실패 %s %s", res.status_code, data)
        raise PaymentError(data.get("message") or "결제를 확인하지 못했습니다.")
    return data


# 토스가 알려 주는 결제 상태 (docs.tosspayments.com/reference)
#   READY · IN_PROGRESS · WAITING_FOR_DEPOSIT · DONE
#   CANCELED · PARTIAL_CANCELED · ABORTED · EXPIRED
PAID_STATES = {"DONE"}
DEAD_STATES = {"CANCELED", "ABORTED", "EXPIRED"}


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
