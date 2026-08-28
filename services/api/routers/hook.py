"""POST /v1/hook — 무료 훅 5단."""
from fastapi import APIRouter, HTTPException

import store
from engine import bank, lens as lens_mod
from engine.features import Features
from routers.chart import load_features
from schemas.api import HookRequest, HookResponse

router = APIRouter(prefix="/v1", tags=["hook"])

HOOK_TTL = 24 * 3600


@router.post("/hook", response_model=HookResponse)
def post_hook(req: HookRequest) -> HookResponse:
    raw = load_features(req.chart_id)
    # ★ 캐시 열쇠에 misses 를 넣습니다. 안 넣으면 방향을 튼 훅이
    #   안 튼 훅을 덮어써서, 다음 손님이 남의 응답으로 고쳐진 훅을
    #   받습니다.
    key = store.k_hook(req.chart_id, req.concern, req.axis4 or "",
                       req.lens_id or "", "%s#%d" % (req.name, req.misses))
    cached = store.get_json(key)
    if cached is not None:
        return HookResponse(chart_id=req.chart_id, segments=cached, cached=True)

    f = Features(**raw)
    try:
        segs = bank.build_hook(
            f, req.concern, req.axis4, name=req.name,
            you=lens_mod.you_word(req.lens_id), misses=req.misses)
    except bank.BankError as e:
        # 뱅크에 없는 조합이면 지어내지 않고 알린다
        raise HTTPException(status_code=422, detail=str(e))

    store.set_json(key, segs, ttl=HOOK_TTL)
    return HookResponse(chart_id=req.chart_id, segments=segs, cached=False)
