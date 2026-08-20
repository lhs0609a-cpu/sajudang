"""
POST /v1/relay — 릴레이 추천.

★ 브레이크는 여기서 끄지 못합니다. 세션 카운터는 Redis(없으면 메모리)에서
  읽고, 쿼리 파라미터로 우회하는 경로를 만들지 마세요. (CLAUDE.md 절대 규칙 4)
"""
from fastapi import APIRouter, HTTPException

import store
from engine import relay as relay_engine
from engine.features import Features
from routers.chart import load_features
from schemas.api import RelayRequest, RelayResponse

router = APIRouter(prefix="/v1", tags=["relay"])

SESSION_TTL = 6 * 3600


@router.post("/relay", response_model=RelayResponse)
def post_relay(req: RelayRequest) -> RelayResponse:
    raw = load_features(req.chart_id)
    f = Features(**raw)

    used = store.get_int(store.k_relay_session(req.session_id))
    try:
        out = relay_engine.recommend(
            f, read=req.read, skipped=req.skipped,
            session_relay_count=used, last_lens=req.last_lens)
    except relay_engine.RelayRuleError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return RelayResponse(**out)


@router.post("/relay/consume")
def consume_relay(session_id: str) -> dict:
    """
    실제로 다음 캐릭터로 넘어갈 때 부른다. 세션 릴레이 카운터를 올린다.
    브레이크의 실효성이 이 호출에 달려 있으므로 프론트에서 빠뜨리지 말 것.
    """
    n = store.incr(store.k_relay_session(session_id), ttl=SESSION_TTL)
    limit = relay_engine.BREAKS()["per_session_relay"]
    return {"used": n, "limit": limit, "blocked": n >= limit}
