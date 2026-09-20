"""
분석지 · 공유 — docs/08 c5(공유카드)의 확장.

    POST /v1/summary        종합 분석지 한 장
    POST /v1/share          공유 링크 발급 (분석지를 그 시점으로 박제)
    GET  /v1/share/{token}  링크 열기 — 받은 사람이 보는 것
    POST /v1/share/{token}/open  열람 기록 (바이럴 계측)

★ 공유 payload 에 생년월일시·도시·보정 시각을 담지 않습니다.
  링크를 받은 사람이 원본 생일을 알 수 없어야 합니다. (docs/11 §10)

★ 링크를 만든 사람은 무엇이 담기는지 미리 봅니다. 몰래 담지 않습니다.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import store
from engine import lens as lens_mod
from engine.calendar import build_chart
from engine.features import Features
from engine.summary import build_summary, share_payload
from routers.chart import load_features
from schemas.api import Concern

router = APIRouter(prefix="/v1", tags=["share"])

SHARE_TTL_DAYS = 90
TOKEN_BYTES = 9          # base64url 12자


class SummaryRequest(BaseModel):
    chart_id: str
    concern: Concern = "love"
    axis4: Optional[str] = Field(default=None, min_length=4, max_length=4)
    lens_id: str = "pungun"
    name: str = Field(default="", max_length=20)


class ShareRequest(SummaryRequest):
    reveal: str = "full"          # full | light
    from_name: str = Field(default="", max_length=20)


def _features_and_chart(chart_id: str):
    raw = load_features(chart_id)
    f = Features(**raw)
    c = f.correction
    # 분석지는 Features 만으로 만들 수 있게 되어 있으나, 명식 객체가 필요한
    # 부분(신살)은 이미 Features 안에 들어 있다. 여기서 재계산하지 않는다.
    return f


@router.post("/summary")
def post_summary(req: SummaryRequest) -> dict:
    f = _features_and_chart(req.chart_id)
    try:
        lens_mod.get(req.lens_id)
    except lens_mod.LensError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return build_summary(None, f, req.concern, req.axis4, req.lens_id, req.name)


@router.post("/share")
def post_share(req: ShareRequest) -> dict:
    if req.reveal not in ("full", "light"):
        raise HTTPException(status_code=400, detail="reveal 은 full 또는 light 요.")
    f = _features_and_chart(req.chart_id)
    summary = build_summary(None, f, req.concern, req.axis4, req.lens_id, req.name)

    token = secrets.token_urlsafe(TOKEN_BYTES)
    payload = share_payload(summary, req.reveal)
    payload["from_name"] = req.from_name.strip() or None
    payload["created_at"] = datetime.now(timezone.utc).isoformat()

    store.set_json("share:" + token, payload, ttl=SHARE_TTL_DAYS * 86400)
    return {
        "token": token,
        "path": "/s/" + token,
        "expires_days": SHARE_TTL_DAYS,
        # 만든 사람이 무엇이 담기는지 미리 본다
        "includes": sorted(k for k in payload
                           if k not in ("created_at", "reveal")),
        "excludes": ["생년월일", "태어난 시각", "태어난 고을", "보정 내역", "연락처"],
    }


@router.get("/share/{token}")
def get_share(token: str) -> dict:
    data = store.get_json("share:" + token)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail="지난 링크요. 90일이 넘으면 스스로 닫히오.")
    views = store.get_int("share:views:" + token)
    return {**data, "views": views}


@router.post("/share/{token}/open")
def open_share(token: str) -> dict:
    """링크를 열어본 횟수. 바이럴이 실제로 도는지 보는 유일한 계측이다."""
    if store.get_json("share:" + token) is None:
        raise HTTPException(status_code=404, detail="지난 링크요.")
    n = store.incr("share:views:" + token, ttl=SHARE_TTL_DAYS * 86400)
    return {"views": n}
