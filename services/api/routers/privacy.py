"""
내 자료 — 열람과 삭제 (개인정보보호법 제35조·제36조 · SHIP OS §22).

    GET  /v1/me/data      내가 맡긴 것 전부 (열람 요구권)
    POST /v1/me/forget    지워 주시오 (정정·삭제 요구권)

★ 계정이 없어도 이 권리는 있습니다

  이 집은 로그인을 안 받습니다. 그렇다고 손님이 맡긴 것을 도로
  가져갈 길이 없어도 되는 것은 아닙니다. 자격의 열쇠(세션)를 쥔
  사람이 곧 그 자료의 임자입니다.

★ 무엇을 지우고 무엇을 남기는가

  지웁니다   세션에 매인 것 — 주문 목록 · 인장 · 발길 수 · 하루 셈
  남깁니다   **거래 기록 자체**. 전자상거래법 제6조가 대금결제 기록을
             5년 보관하라 합니다. 다만 그 기록에서 **세션을 떼어**
             더는 이 브라우저와 이어지지 않게 합니다.

  「다 지웠다」 고 말해 놓고 남기면 거짓말이고, 법이 남기라는 것을
  지우면 그것도 잘못입니다. 그래서 **무엇이 남는지 말하고** 지웁니다.

★ 도는 구독이 있으면 안 지웁니다

  지워 버리면 카드는 걸린 채로 남아 **돈은 나가는데 볼 자리가 없는**
  사람이 됩니다. 먼저 그만두게 하고, 그 다음에 지웁니다.

★ 명식 캐시는 손님 것이 아닙니다

  `chart:{id}` 의 열쇠는 생년월일시의 해시라, 같은 날 같은 시에 난
  사람이면 **여럿이 같은 칸**을 씁니다. 한 사람이 지운다고 지우면
  남의 것을 지우는 것입니다. 그 칸에는 이름도 세션도 없고 90일이면
  스스로 삭습니다.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

import store
import throttle

router = APIRouter(prefix="/v1/me", tags=["privacy"])

# 열람·삭제도 세션만 알면 되는 자리라 두드리는 횟수를 셉니다.
TRIES, WINDOW = 20, 3600


def _user_key(session_id: str) -> str:
    return hashlib.sha256(session_id.encode()).hexdigest()[:16]


def _limit(session_id: str, what: str) -> None:
    try:
        throttle.check(what, session_id, limit=TRIES, window=WINDOW,
                       say="너무 자주 청하셨소. 한 시간 뒤에 다시 해 보시오.")
    except throttle.TooMany as e:
        raise HTTPException(429, str(e))


def _gather(session_id: str) -> dict:
    uk = _user_key(session_id)
    oids = store.get_json("orders:" + session_id) or []
    orders = []
    for oid in oids:
        o = store.get_json("order:" + oid)
        if not isinstance(o, dict):
            continue
        # ★ 내부 열쇠는 본인에게도 안 내려보냅니다 — 카드 열쇠와
        #   승인 키는 그 사람 것이 아니라 **PG 와 우리 사이의 것**입니다.
        orders.append({k: v for k, v in o.items()
                       if k not in ("payment_key", "session_id",
                                    "analytics_sid", "billing_key")})
    sub = store.get_json("sub:" + uk) or {}
    return {
        "orders": orders,
        "seals": store.get_json("seals:" + uk) or [],
        "subscription": {k: v for k, v in sub.items()
                         if k in ("status", "period_end", "amount",
                                  "card_last4", "started_at", "ending")},
        "visits": store.get_int("visit:" + uk),
    }


@router.get("/data")
def my_data(session_id: str = Query(min_length=8, max_length=64)) -> dict:
    """
    내가 맡긴 것 전부 (제35조 열람 요구권).

    ★ 생년월일시는 여기 없습니다. 이 집은 그것을 **세션에 매어
      저장하지 않습니다** — 명식 캐시의 열쇠는 생년월일시의 해시라
      누구 것인지 모릅니다. 원본은 손님 브라우저에만 있습니다.
    """
    _limit(session_id, "export")
    got = _gather(session_id)
    return {
        "at": datetime.now(timezone.utc).isoformat(),
        **got,
        "say": ("이 집이 그대에 대해 들고 있는 것은 이것이 전부요. "
                "생년월일시는 여기 없소 — 그건 그대 브라우저에만 있고, "
                "셈할 때만 받아 쓰고 버리오."),
    }


class ForgetRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)
    confirm: bool = False


@router.post("/forget")
def forget(req: ForgetRequest) -> dict:
    """
    지워 주시오 (제36조 정정·삭제 요구권).

    ★ `confirm=false` 면 **무엇이 지워지고 무엇이 남는지만** 말하고
      아무것도 안 지웁니다. 되돌릴 수 없는 일이라 한 번 보여 줍니다
      (§6-6 위험 행동은 확인 단계를 둔다).
    """
    _limit(req.session_id, "forget")
    uk = _user_key(req.session_id)
    got = _gather(req.session_id)

    sub = store.get_json("sub:" + uk) or {}
    if sub.get("status") == "live" and not sub.get("ending"):
        raise HTTPException(
            409,
            "달삯이 아직 도오. 먼저 그만두신 뒤에 지워 드리겠소 — "
            "지금 지우면 카드는 걸린 채로 남소.")

    keeps = [o["order_id"] for o in got["orders"]
             if o.get("status") in ("paid", "refunded")] \
        if got["orders"] and "order_id" in (got["orders"][0] or {}) else []

    plan = {
        "removes": {
            "구매 목록": len(got["orders"]),
            "인장": len(got["seals"]),
            "발길 수": got["visits"],
            "구독 기록": 1 if sub else 0,
        },
        "keeps": {
            "거래 기록": len(got["orders"]),
            "왜": ("전자상거래법 제6조 — 대금결제 기록은 5년 보관하오. "
                   "다만 그 기록에서 **이 브라우저와의 연결은 끊소.** "
                   "다시는 되찾기로 열 수 없소."),
        },
    }
    if not req.confirm:
        return {"ok": True, "done": False, "plan": plan,
                "say": "이대로 지우시겠소? 되돌릴 수 없소."}

    # ── 지웁니다 ──────────────────────────────────────────
    #   순서가 중요합니다. 연결(orders:)을 먼저 끊고 나서 속을 지웁니다 —
    #   거꾸로 하면 중간에 멈췄을 때 열쇠만 남아 빈 곳을 가리킵니다.
    store.delete("orders:" + req.session_id)
    for o in got["orders"]:
        oid = o.get("order_id")
        if not oid:
            continue
        row = store.get_json("order:" + oid)
        if isinstance(row, dict):
            # 거래 기록은 남기고 **세션만 뗍니다**.
            row["session_id"] = None
            row["forgotten_at"] = datetime.now(timezone.utc).isoformat()
            store.set_json("order:" + oid, row)
    store.delete("seals:" + uk)
    store.delete("sub:" + uk)
    store.delete("visit:" + uk)

    return {"ok": True, "done": True, "plan": plan,
            "say": "지웠소. 이 브라우저와 이어진 자리는 더 없소."}
