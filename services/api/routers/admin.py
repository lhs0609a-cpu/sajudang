"""
GET /v1/admin/overview — 가게가 지금 어떤가.

★ 왜 따로 두나

  손님 화면과 주인 화면은 **다른 것**입니다. 전에는 주소 뒤에
  `?admin=1` 만 붙이면 레일이 열렸습니다. 그건 잠금이 아니라 **가림**
  입니다 — 아무나 붙일 수 있습니다. 매출과 이탈은 영업 정보라
  퍼널과 같은 열쇠 뒤에 둡니다.

★ 무엇을 내주나

    지금       오늘 들어온 사람 · 명식 세운 수 · 지금 도는 사람
    돈         치른 건수 · 매출 · 상품별 · 환불
    이탈       화면별 도달과 잃은 수 (퍼널)
    훅         단별 응답률 — 초반이 어디서 끊기는가
    집         소리·결제·곳간이 살아 있는가

★ 개인정보는 안 싣습니다

  생년월일·이름·chart_id 는 준식별자입니다 (CLAUDE.md). 여기서도
  **세기만** 하고 누구인지는 내려보내지 않습니다.
"""
from __future__ import annotations

import hmac
import os
import time
from collections import Counter
from datetime import date, datetime, timezone

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

import keyguard
from keyguard import require_admin as _guard

import adminauth
import analytics
import payments
import store

router = APIRouter(prefix="/v1/admin", tags=["admin"])

# 문지기는 keyguard 한 자리에 있습니다. 퍼널과 **같은 열쇠**를 씁니다 —
# 둘을 따로 두면 하나만 걸어 두고 다른 하나는 열린 채 배포됩니다.


def _sales() -> dict:
    """
    치른 주문을 셉니다.

    ★ 주문 하나가 여러 번 저장될 수 있어(준비 → 승인) 주문번호로
      한 번만 셉니다. 상태가 치른 것인지는 payments 가 정합니다 —
      여기서 다시 정하면 두 곳의 판단이 갈립니다.
    """
    today = date.today().isoformat()
    seen: dict[str, dict] = {}
    for k, v in store.scan("order:"):
        if isinstance(v, dict):
            seen[k] = v

    # ★ **우리 장부의 말**로 셉니다 (payments.ORDER_*).
    #   전에는 토스의 말(PAID_STATES = {"DONE"})과 견주고 있었습니다.
    #   두 어휘가 한 번도 안 겹쳐서 매출이 늘 0원이었습니다.
    paid = [o for o in seen.values()
            if o.get("status") in payments.ORDER_PAID]
    dead = [o for o in seen.values()
            if o.get("status") in payments.ORDER_DEAD]
    pending = [o for o in seen.values()
               if o.get("status") in payments.ORDER_PENDING]

    def _day(o: dict) -> str:
        t = o.get("paid_at") or o.get("created_at") or ""
        return str(t)[:10]

    by_tier = Counter(o.get("tier") or "?" for o in paid)
    by_lens = Counter(o.get("lens_id") or "?" for o in paid)
    amount = sum(int(o.get("amount") or 0) for o in paid)
    today_paid = [o for o in paid if _day(o) == today]

    return {
        "orders_all": len(seen),
        "paid": len(paid),
        "paid_today": len(today_paid),
        "refunded": len(dead),
        "refunded_amount": sum(int(o.get("amount") or 0) for o in dead),
        # 값을 매겨 놓고 안 치른 것. 결제창에서 물러선 사람입니다.
        "pending": len(pending),
        "pending_amount": sum(int(o.get("amount") or 0) for o in pending),
        "revenue": amount,
        "revenue_today": sum(int(o.get("amount") or 0) for o in today_paid),
        # 한 건에 평균 얼마인가. 치른 건이 없으면 안 냅니다 — 0으로
        # 나누지 않고, 없는 값을 0원으로 적지도 않습니다.
        "avg_order": (round(amount / len(paid)) if paid else None),
        # 값을 치른 사람이 몇 %인가 — 만든 주문 대비
        "close_rate": (round(100.0 * len(paid) / len(seen), 1)
                       if seen else None),
        "by_tier": dict(by_tier.most_common()),
        "by_lens": dict(by_lens.most_common(10)),
    }


def _trouble() -> dict:
    """
    지금 결제가 막히고 있는가.

    ★ 주인이 가장 먼저 묻는 것은 「지금 뭐 터진 거 없소?」 입니다.
      그런데 화면에는 매출과 이탈만 있었고, **막힌 자리**를 볼 데가
      없었습니다. 세 가지를 함께 냅니다 —

        문   PG 키가 걸려 있는가. 없으면 결제를 아예 거절합니다.
        건   물린 주문 · 값만 매기고 안 치른 주문
        수   손님 화면에서 결제가 깨진 횟수 (pay_fail)

    ★ 여기서도 누구인지는 안 내려보냅니다. 주문번호는 우리가 만든
      값이라 준식별자가 아니지만, 세션·명식은 싣지 않습니다.
    """
    seen: dict[str, dict] = {}
    for k, v in store.scan("order:"):
        if isinstance(v, dict):
            seen[k] = v

    now = datetime.now(timezone.utc)
    stale = []
    for key, o in seen.items():
        if o.get("status") not in payments.ORDER_PENDING:
            continue
        made = o.get("created_at")
        age_min = None
        if made:
            try:
                age_min = int((now - datetime.fromisoformat(made))
                              .total_seconds() // 60)
            except ValueError:
                age_min = None
        stale.append({
            "order_id": key.split("order:", 1)[-1],
            "amount": int(o.get("amount") or 0),
            "tier": o.get("tier"),
            "lens_id": o.get("lens_id"),
            "age_min": age_min,
        })
    # 오래 묵은 것부터. 나이를 모르는 건 뒤로 보냅니다.
    stale.sort(key=lambda r: (r["age_min"] is None, -(r["age_min"] or 0)))

    dead = [{"order_id": k.split("order:", 1)[-1],
             "amount": int(o.get("amount") or 0),
             "tier": o.get("tier"),
             "pg_status": o.get("pg_status")}
            for k, o in seen.items()
            if o.get("status") in payments.ORDER_DEAD]

    try:
        fails = analytics.count("pay_fail")
        starts = analytics.count("pay_start")
    except Exception:                          # noqa: BLE001
        fails = starts = None

    # 문이 열려 있는가. 키가 없으면 결제는 503 으로 거절합니다 —
    # 그건 고장이 아니라 **일부러 닫은 것**이라 그렇게 적습니다.
    if not payments.ENABLED:
        gate = "PG 키가 없어 결제를 안 받고 있소 (일부러 닫은 것이오)"
    elif not payments.LIVE:
        gate = "시험 키로 열려 있소. 실거래는 안 되오"
    else:
        gate = "실거래 키로 열려 있소"

    return {
        "gate": gate,
        "enabled": payments.ENABLED,
        "live": payments.LIVE,
        "pay_start": starts,
        "pay_fail": fails,
        "fail_rate": (round(100.0 * fails / starts, 1)
                      if starts else None),
        "stale_pending": stale[:10],
        "stale_pending_all": len(stale),
        "canceled": dead[:10],
        "canceled_all": len(dead),
    }


def _live() -> dict:
    """지금 도는 사람. 세션 열쇠를 세는 것이라 누구인지는 모릅니다."""
    now = time.time()
    rows = store.scan("sess:") + store.scan("relay:")
    fresh = 0
    for _, v in rows:
        if isinstance(v, dict):
            t = v.get("at") or v.get("ts")
            if isinstance(t, (int, float)) and now - t < 900:
                fresh += 1
    return {"sessions_seen": len(rows), "active_15m": fresh}


@router.get("/overview")
def overview(x_funnel_key: str | None = Header(default=None),
             x_admin_token: str | None = Header(default=None)) -> dict:
    _guard(x_funnel_key, x_admin_token)
    import voice

    try:
        fn = analytics.funnel()
    except Exception:                          # noqa: BLE001
        fn = {}

    return {
        "at": datetime.now().isoformat(timespec="seconds"),
        "sales": _sales(),
        "trouble": _trouble(),
        "live": _live(),
        "funnel": fn,
        "house": {
            "store": store.stats(),
            "payments": payments.ENABLED,
            "payments_live": payments.LIVE,
            "voice": voice.enabled(),
            "voice_cached": (len(list(voice.CACHE.glob("*.mp3")))
                             if voice.CACHE.is_dir() else 0),
        },
    }


@router.get("/screens")
def screens(x_funnel_key: str | None = Header(default=None),
            x_admin_token: str | None = Header(default=None)) -> dict:
    """
    화면마다 **연출 점수** — 다음 화가 보고 싶어지는가.

    ★ 손님이 시킨 것 (2026-09-02)

      "관리자 페이지에서는 페이지마다 매력도를 측정해서, 실제 내용이
      팩트를 때리고 다음 화로 넘어갈 수밖에 없게 설계했는지, 내용은
      충실한지, 쉬운지를 지표로 각 페이지마다 다 점수로 표시해줘.
      뭐가 부족한지도 나타내고. 항상 연동해서 점수 보여줘."

    ★ 지어낸 점수가 아닙니다

      **실제로 나가는 글**을 그 자리에서 재서 냅니다 — 엔진이 짓는
      화면은 표본 하나를 진짜로 돌리고, 코드에 박힌 화면은 그 글을
      그대로 읽습니다. 그러니 문장을 고치면 이 숫자가 바로 움직입니다.

    ★ 캐시를 안 겁니다

      고치고 새로 고쳤는데 옛 점수가 나오면 도구를 안 믿게 됩니다.
      스무 화면 재는 데 1초가 안 걸립니다.
    """
    _guard(x_funnel_key, x_admin_token)
    from engine import screenscan

    # 코드를 고치면 바로 다시 읽어야 합니다. lru_cache 를 비웁니다.
    screenscan._screens.cache_clear()
    rows = screenscan.scan_all()
    return {
        "at": datetime.now().isoformat(timespec="seconds"),
        "summary": screenscan.summary(rows),
        "screens": rows,
    }


@router.get("/ping")
def ping(x_funnel_key: str | None = Header(default=None),
         x_admin_token: str | None = Header(default=None)) -> dict:
    """열쇠가 맞는지만 봅니다 — 화면이 문을 열기 전에 묻는 자리."""
    _guard(x_funnel_key, x_admin_token)
    return {"ok": True}


# ══════════════════════════════════════════════════════════
# 주인 문 — 아이디와 비밀번호
# ══════════════════════════════════════════════════════════
#
# ★ 비밀번호는 **여기 한 번**만 오갑니다.
#   맞으면 쪽지(토큰)를 드리고, 그 뒤로는 쪽지만 오갑니다.
#   비밀번호는 서버에도 저장소에도 로그에도 남지 않습니다.
class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=1, max_length=200)


@router.get("/gate")
def gate() -> dict:
    """
    문이 어떤 꼴인가.

    # 문 없음: 화면이 로그인 칸을 그릴지 열쇠 칸을 그릴지 정하려면
    #          들어오기 **전에** 물어봐야 합니다. 걸렸는지 아닌지만
    #          답하고 아이디도 열쇠도 안 흘립니다.
    """
    return {
        "login": adminauth.configured(),
        "key": bool(keyguard.FUNNEL_KEY),
    }


@router.post("/login")
def login(req: LoginRequest) -> dict:
    try:
        token = adminauth.login(req.email, req.password)
    except adminauth.AuthError as e:
        # ★ 401 로 냅니다. 무엇이 틀렸는지는 안 알려 줍니다 —
        #   아이디가 있는지 없는지부터 캐내는 자리가 됩니다.
        raise HTTPException(401, str(e))
    return {"token": token, "email": adminauth.ADMIN_EMAIL}


@router.post("/logout")
def logout(x_admin_token: str | None = Header(default=None)) -> dict:
    adminauth.logout(x_admin_token)
    return {"ok": True}


@router.get("/me")
def me(x_admin_token: str | None = Header(default=None)) -> dict:
    """쪽지가 아직 살아 있는가. 화면이 새로 뜰 때 물어봅니다."""
    sess = adminauth.session_of(x_admin_token)
    if not sess:
        raise HTTPException(401, "쪽지가 삭았소. 다시 들어오시오.")
    return {"email": sess.get("email")}
