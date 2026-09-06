"""GET /v1/daily — 오늘의 일진."""
from datetime import date, datetime, timedelta

from fastapi import APIRouter

import store
from engine.daily import build_daily
from engine.features import Features
from routers.chart import load_features
from schemas.api import DailyResponse

router = APIRouter(prefix="/v1", tags=["daily"])


def _seconds_to_midnight() -> int:
    now = datetime.now()
    nxt = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
    return max(60, int((nxt - now).total_seconds()))


@router.get("/daily", response_model=DailyResponse)
def get_daily(chart_id: str, concern: str | None = None) -> DailyResponse:
    """
    오늘의 일진.

    ★ `concern` 은 **읽는 자리**만 바꿉니다 (2026-09-06). 점수와 셈은
      그대로입니다 — 오늘 간지와 여덟 글자가 맞물린 수는 무엇을
      물었든 같습니다. 캐시 열쇠에 넣어야 돈으로 읽은 것이 몸으로
      읽은 것을 덮지 않습니다.
    """
    today = date.today()
    key = "daily:%s:%s:%s" % (chart_id, today.isoformat(), concern or "-")
    cached = store.get_json(key)
    if cached is not None:
        return DailyResponse(**cached)

    f = Features(**load_features(chart_id))
    data = build_daily(f, today, concern)
    store.set_json(key, data, ttl=_seconds_to_midnight())
    return DailyResponse(**data)
