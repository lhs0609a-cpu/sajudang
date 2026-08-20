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
def get_daily(chart_id: str) -> DailyResponse:
    today = date.today()
    key = "daily:%s:%s" % (chart_id, today.isoformat())
    cached = store.get_json(key)
    if cached is not None:
        return DailyResponse(**cached)

    f = Features(**load_features(chart_id))
    data = build_daily(f, today)
    store.set_json(key, data, ttl=_seconds_to_midnight())
    return DailyResponse(**data)
