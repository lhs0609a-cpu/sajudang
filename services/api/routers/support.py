"""
문의 창구 (SHIP OS §4.11).

    POST /v1/support        말을 건다
    GET  /v1/support/mine   내가 건 말과 답

★ 왜 필요한가

  여태 손님이 이 집에 말을 걸 길은 **환불 확인 요청 하나**였습니다.
  그 밖의 일 — 자격이 안 열린다, 셈이 이상하다, 그만두고 싶다 —
  는 갈 데가 없었습니다. /legal 에 전자우편 칸이 있지만 거기 값이
  안 들어가 있으면 그것도 없는 길입니다.

★ 자유 입력을 받습니다. 그래서 지키는 것이 셋입니다.

  ① **해석에 안 먹입니다.** 이 집은 맥락축에 자유 입력을 금합니다 —
     가드를 우회하기 때문입니다. 여기 글은 주인만 읽고, 문장 엔진
     근처에 가지 않습니다.
  ② **길이를 자릅니다.** 1,000자. 긴 글은 사연이 되고 사연에는
     남의 개인정보가 섞입니다.
  ③ **연락처를 안 묻습니다.** 답은 이 자리에서 봅니다 — 다시 와서
     `GET /v1/support/mine` 으로. 이메일을 받으면 안 받아도 될
     개인정보를 받는 것입니다.

★ 주인이 답한 것도 손님 화면으로 갑니다. 한쪽으로만 흐르면
  그건 창구가 아니라 **건의함**입니다.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

import store
import throttle

router = APIRouter(prefix="/v1/support", tags=["support"])

PREFIX = "support:"
TTL = 365 * 86400
TRIES, WINDOW = 5, 3600          # 한 시간에 다섯 번

# 무엇에 대한 말인가. ★ 자유 낱말이 아니라 **고른 칸**입니다 —
# 갈래가 자유 문자열이면 거기에도 사연이 실립니다.
TOPICS = {
    "unlock": "값을 치렀는데 안 열리오",
    "calc": "셈이 틀린 것 같소",
    "billing": "결제·달삯에 대해",
    "privacy": "내 자료에 대해",
    "other": "그 밖에",
}


def _user_key(session_id: str) -> str:
    return hashlib.sha256(session_id.encode()).hexdigest()[:16]


class Ask(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)
    topic: str = Field(min_length=2, max_length=16)
    body: str = Field(min_length=5, max_length=1000)
    order_id: str = Field(default="", max_length=64)


@router.get("/topics")
def topics() -> dict:
    """화면이 고를 칸을 서버에서 받아 적습니다 — 두 벌이 되면 어긋납니다."""
    return {"topics": [{"id": k, "say": v} for k, v in TOPICS.items()]}


@router.post("")
def ask(req: Ask) -> dict:
    if req.topic not in TOPICS:
        raise HTTPException(422, "그런 갈래는 없소.")
    try:
        throttle.check("support", req.session_id, limit=TRIES, window=WINDOW,
                       say="오늘은 그만 받겠소. 한 시간 뒤에 다시 걸어 주시오.")
    except throttle.TooMany as e:
        raise HTTPException(429, str(e))

    tid = uuid.uuid4().hex[:12]
    row = {
        "id": tid,
        "user_key": _user_key(req.session_id),
        "topic": req.topic,
        # ★ 본문은 손님이 쓴 그대로 둡니다. 여기서 가드를 돌리지
        #   않습니다 — 손님의 말을 고쳐 적으면 그건 문의가 아닙니다.
        #   대신 이 글은 **어디에도 다시 나가지 않습니다.**
        "body": req.body.strip(),
        "order_id": req.order_id.strip(),
        "status": "open",
        "at": datetime.now(timezone.utc).isoformat(),
        "reply": "", "replied_at": "",
    }
    store.set_json(PREFIX + tid, row, ttl=TTL)
    idx = store.get_json("supportof:" + row["user_key"]) or []
    store.set_json("supportof:" + row["user_key"], [*idx, tid], ttl=TTL)
    return {"ok": True, "id": tid,
            "say": "받았소. 답은 「내 서재」에서 보시오."}


def _mine(session_id: str) -> list[dict]:
    uk = _user_key(session_id)
    out = []
    for tid in store.get_json("supportof:" + uk) or []:
        row = store.get_json(PREFIX + tid)
        if isinstance(row, dict):
            out.append({k: v for k, v in row.items() if k != "user_key"})
    out.sort(key=lambda r: r.get("at", ""), reverse=True)
    return out


@router.get("/mine")
def mine(session_id: str = Query(min_length=8, max_length=64)) -> dict:
    return {"threads": _mine(session_id), "topics": TOPICS}
