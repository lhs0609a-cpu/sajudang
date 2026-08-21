"""
POST /v1/events — 계측. 어디서 나가는지 보려고 남깁니다.
GET  /v1/funnel — 퍼널 조회 (열쇠 필요).

★ 본문에 개인정보가 들어와도 서버가 버립니다.
  analytics._clean 이 화이트리스트로 걸러서, 이름·생일이 실려 와도
  기록되지 않습니다. 막는 자리를 프런트에만 두면 언젠가 샙니다.

★ 계측이 실패해도 200 을 돌려줍니다.
  화면이 계측 때문에 멈추면 안 됩니다. 기록 수만 알려 줍니다.
"""
from __future__ import annotations

import hmac
import os

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

import analytics

router = APIRouter(prefix="/v1", tags=["events"])

FUNNEL_KEY = os.getenv("FUNNEL_KEY", "").strip()


class EventIn(BaseModel):
    name: str
    screen: str
    sid: str
    stage: int | None = None
    ms: int | None = None
    n: int | None = None
    yes: int | None = None


class EventBatch(BaseModel):
    events: list[EventIn] = Field(default_factory=list, max_length=analytics.MAX_BATCH)


@router.post("/events")
def post_events(batch: EventBatch) -> dict:
    n = analytics.record([e.model_dump() for e in batch.events])
    return {"ok": True, "recorded": n, "sent": len(batch.events)}


@router.delete("/events")
def clear_events(x_funnel_key: str | None = Header(default=None)) -> dict:
    """
    계측을 비운다. **열쇠가 있어야 합니다.**

    쓸 자리는 하나뿐입니다 — 배포 직후 시험하며 만든 사건을 치우고
    진짜 숫자를 0 부터 세기. 실사용이 시작된 뒤에는 부르지 마세요.
    지운 것은 돌아오지 않습니다.
    """
    if not FUNNEL_KEY:
        raise HTTPException(503, "FUNNEL_KEY 가 설정되지 않았습니다.")
    if not x_funnel_key or not hmac.compare_digest(x_funnel_key, FUNNEL_KEY):
        raise HTTPException(401, "열쇠가 맞지 않습니다.")
    return {"ok": True, "deleted": analytics.clear()}


@router.get("/funnel")
def get_funnel(x_funnel_key: str | None = Header(default=None)) -> dict:
    """
    ★ 열쇠가 없으면 막습니다.

    퍼널 숫자는 영업 정보입니다. FUNNEL_KEY 를 안 걸어 두면 아무나
    전환율을 읽어 갑니다. 키를 안 정해 두면 아예 닫습니다 — 열어 두는
    쪽이 기본이면 언젠가 그대로 배포됩니다.
    """
    if not FUNNEL_KEY:
        raise HTTPException(503, "FUNNEL_KEY 가 설정되지 않았습니다.")
    if not x_funnel_key or not hmac.compare_digest(x_funnel_key, FUNNEL_KEY):
        raise HTTPException(401, "열쇠가 맞지 않습니다.")
    return analytics.funnel()
