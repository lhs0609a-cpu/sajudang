"""POST /v1/hook — 무료 훅 5단."""
from fastapi import APIRouter, HTTPException

import store
from engine import bank, lens as lens_mod, voice as voice_mod
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
            you=lens_mod.you_word(req.lens_id, req.name, raw.get("sex")),
            misses=req.misses)
    except bank.BankError as e:
        # 뱅크에 없는 조합이면 지어내지 않고 알린다
        raise HTTPException(status_code=422, detail=str(e))

    # ★ 훅도 그 사람 말투로 나갑니다 (2026-09-03).
    #
    #   `build_hook` 은 호칭만 갈아 끼우고 **말투는 안 갈았습니다.**
    #   그래서 해요체 캐릭터를 고르고 들어온 손님이 훅에서는 하오체를
    #   듣고 리포트에서는 해요체를 들었습니다 — 사람이 바뀐 것처럼
    #   읽힙니다. 훅은 손님이 이 집에서 **처음 읽는 글**이라 여기서
    #   목소리가 어긋나면 뒤가 다 흔들립니다.
    #
    #   묻는 말과 응답 두 줄도 같이 태웁니다. 대사 세 줄 중 둘만
    #   갈면 그게 더 눈에 띕니다.
    tone = lens_mod.view(req.lens_id).get("voice")
    if tone and tone != voice_mod.HAO:
        for s in segs:
            for k in ("html", "question", "yes", "no"):
                if s.get(k):
                    s[k] = voice_mod.speak(s[k], tone)

    store.set_json(key, segs, ttl=HOOK_TTL)
    return HookResponse(chart_id=req.chart_id, segments=segs, cached=False)
