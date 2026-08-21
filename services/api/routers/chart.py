"""POST /v1/chart — 명식 산출. 가장 많이 불리는 엔드포인트."""
import hashlib

from fastapi import APIRouter, HTTPException

import store
from engine.calendar import build_chart
from engine.features import build_features
from engine.solar_terms import SolarTermError
from schemas.api import ChartRequest, ChartResponse

router = APIRouter(prefix="/v1", tags=["chart"])


def chart_key(req: ChartRequest) -> str:
    raw = "|".join(str(x) for x in [
        req.year, req.month, req.day, req.hour, req.minute,
        req.hour_known, req.sex, req.birth_city])
    return hashlib.sha256(raw.encode()).hexdigest()


def load_features(chart_id: str) -> dict:
    """다른 라우터가 chart_id 로 Feature 를 꺼낼 때 쓴다."""
    f = store.get_json(store.k_chart(chart_id))
    if f is None:
        raise HTTPException(
            status_code=404,
            detail="모르는 chart_id 요. /v1/chart 로 명식부터 세우시오.")
    return f


@router.get("/chart/{chart_id}", response_model=ChartResponse)
def get_chart(chart_id: str) -> ChartResponse:
    """
    이미 세운 명식을 chart_id 로 다시 가져온다.

    브라우저를 새로고침하면 화면 상태는 날아가지만 chart_id 는 남습니다.
    이게 없으면 새로고침 한 번에 "아직 세우지 않았소" 로 돌아갑니다.
    """
    return ChartResponse(chart_id=chart_id,
                         features=load_features(chart_id), cached=True)


@router.post("/chart", response_model=ChartResponse)
def post_chart(req: ChartRequest) -> ChartResponse:
    key = chart_key(req)
    cached = store.get_json(store.k_chart(key))
    if cached is not None:
        return ChartResponse(chart_id=key, features=cached, cached=True)

    try:
        chart = build_chart(
            req.year, req.month, req.day, req.hour, req.minute,
            req.sex, hour_known=req.hour_known, city=req.birth_city)
    except SolarTermError as e:
        # 계산할 수 없으면 지어내지 않고 거절한다
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    features = build_features(chart).to_dict()
    # 같은 입력이면 같은 결과 — TTL 무기한
    store.set_json(store.k_chart(key), features)
    return ChartResponse(chart_id=key, features=features, cached=False)
