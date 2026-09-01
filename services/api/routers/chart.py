"""POST /v1/chart — 명식 산출. 가장 많이 불리는 엔드포인트."""
import hashlib

from fastapi import APIRouter, HTTPException

import store
from engine.calendar import build_chart
from engine.features import build_features
from engine.solar_terms import SolarTermError
from schemas.api import ChartRequest, ChartResponse

router = APIRouter(prefix="/v1", tags=["chart"])

# 명식 캐시가 사는 기간. 리포트·릴레이·일진이 전부 chart_id 로 이걸 꺼내
# 쓰므로 한 사람의 여정보다는 넉넉히 길어야 합니다. 90일이면 회고 루프와
# 공유 링크(90일)까지 덮습니다.
CHART_TTL = 90 * 24 * 3600


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
    f = load_features(chart_id)
    return ChartResponse(chart_id=chart_id, features=f, cached=True,
                         rarity=_rarity(f))


def _rarity(feat: dict) -> dict | None:
    """
    이 배치가 인구에서 몇 명인가.

    ★ 표가 없거나 낡았으면 **아무것도 안 냅니다.** 지어낸 숫자를
      진짜처럼 내면 이 집이 하지 않기로 한 일을 하는 것입니다.
    """
    from engine import rarity as rr
    from engine.features import Features
    try:
        if rr.is_stale():
            return None
        f = Features(**feat)
        look = rr.look(f)
        return {
            "words": look.get("words"),          # 1만 명에 1,050명
            "band": look.get("band"),            # 흔함 / 드묾 …
            "per10k": look.get("per10k"),
            "ilju": (look.get("ilju") or {}).get("words"),
            "ilju_gz": (look.get("ilju") or {}).get("gz"),
            "ilju_per10k": (look.get("ilju") or {}).get("per10k"),
        }
    except Exception:                            # noqa: BLE001
        # 희소도는 곁가지입니다. 못 세면 명식은 그대로 나갑니다.
        return None


@router.post("/chart", response_model=ChartResponse)
def post_chart(req: ChartRequest) -> ChartResponse:
    key = chart_key(req)
    cached = store.get_json(store.k_chart(key))
    if cached is not None:
        return ChartResponse(chart_id=key, features=cached, cached=True,
                             rarity=_rarity(cached))

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
    # 같은 입력이면 같은 결과라 캐시합니다. 다만 **무기한은 아닙니다** —
    # 다시 세우는 데 0.2ms 밖에 안 드는데 한 벌이 5KB 라, 만기를 안 주면
    # 저장소가 줄어들 힘이 하나도 없습니다. 만료돼도 다음 요청에 다시
    # 만들어지므로 사용자에게는 아무 차이가 없습니다.
    store.set_json(store.k_chart(key), features, ttl=CHART_TTL)
    return ChartResponse(chart_id=key, features=features, cached=False,
                         rarity=_rarity(features))
