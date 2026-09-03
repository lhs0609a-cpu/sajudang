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
from datetime import date, datetime

from fastapi import APIRouter, Header, HTTPException
from keyguard import require_key as _guard

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

    paid = [o for o in seen.values()
            if o.get("status") in payments.PAID_STATES]
    dead = [o for o in seen.values()
            if o.get("status") in getattr(payments, "DEAD_STATES", set())]

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
        "revenue": amount,
        "revenue_today": sum(int(o.get("amount") or 0) for o in today_paid),
        # 값을 치른 사람이 몇 %인가 — 만든 주문 대비
        "close_rate": (round(100.0 * len(paid) / len(seen), 1)
                       if seen else None),
        "by_tier": dict(by_tier.most_common()),
        "by_lens": dict(by_lens.most_common(10)),
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
def overview(x_funnel_key: str | None = Header(default=None)) -> dict:
    _guard(x_funnel_key)
    import voice

    try:
        fn = analytics.funnel()
    except Exception:                          # noqa: BLE001
        fn = {}

    return {
        "at": datetime.now().isoformat(timespec="seconds"),
        "sales": _sales(),
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
def screens(x_funnel_key: str | None = Header(default=None)) -> dict:
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
    _guard(x_funnel_key)
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
def ping(x_funnel_key: str | None = Header(default=None)) -> dict:
    """열쇠가 맞는지만 봅니다 — 화면이 문을 열기 전에 묻는 자리."""
    _guard(x_funnel_key)
    return {"ok": True}
