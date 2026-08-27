"""
POST /v1/report    — 리포트. tier 별 잠금 차등.
POST /v1/omnibus   — 스무 사람 종합. **값을 치른 사람만.**
"""
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

import store
from engine import extras as extras_mod
from engine import lens as lens_mod
from engine.features import Features
from engine.omnibus import build_omnibus
from engine.report import build_report
from routers.chart import load_features
from schemas.api import ReportRequest, ReportResponse

router = APIRouter(prefix="/v1", tags=["report"])


@router.post("/report", response_model=ReportResponse)
def post_report(req: ReportRequest) -> ReportResponse:
    raw = load_features(req.chart_id)
    try:
        lens_mod.get(req.lens_id)
    except lens_mod.LensError as e:
        raise HTTPException(status_code=404, detail=str(e))

    f = Features(**raw)
    try:
        data = build_report(f, req.chart_id, req.lens_id, req.tier,
                            req.concern, req.axis4, req.extras)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    return ReportResponse(**data)


@router.get("/report/choices")
def get_choices() -> dict:
    """
    추가 입력에서 고를 수 있는 것들. 화면이 목록을 만들 때 씁니다.

    ★ 문장 원문은 내려보내지 않습니다 — id 와 라벨만. (docs/02 §7)
    """
    return extras_mod.choices()


# ══════════════════════════════════════════════════════════
# 스무 사람 종합
# ══════════════════════════════════════════════════════════
class OmnibusRequest(BaseModel):
    chart_id: str
    session_id: str
    concern: str = "love"
    axis4: str | None = None
    display_name: str = Field(default="", max_length=12)
    # 결합 축의 추가 입력. 저장하지 않습니다. (engine/extras.py)
    extras: dict | None = None


# 이 티어를 치른 사람만 받습니다. "이 자리 하나" 는 한 사람 값이라
# 스무 사람을 열지 않습니다.
OMNIBUS_TIERS = {"all", "sub"}


def _paid_tier(session_id: str) -> str | None:
    """
    이 사람이 무엇을 치렀는가. 주문 기록에서 봅니다.

    ★ 클라이언트가 보낸 tier 를 믿지 않습니다. 그러면 요청 한 줄로
      8만 자가 빠져나갑니다.
    """
    best = None
    for oid in store.get_json("orders:" + session_id) or []:
        o = store.get_json("order:" + oid)
        if o and o.get("status") == "paid":
            t = o.get("tier")
            if t in OMNIBUS_TIERS:
                best = "all" if t == "all" else (best or t)
    return best


@router.post("/omnibus")
def post_omnibus(req: OmnibusRequest) -> dict:
    """
    스무 사람이 같은 명식을 각자 본 것을 한 권으로.

    브레이크와 어긋나지 않습니다 — 릴레이 상한(세션당 2명)은 **한 자리에서
    여러 사람을 몰아 듣지 말라**는 것이고, 이건 값을 치르고 한 번에 받아
    두고 천천히 읽는 물건입니다.
    """
    if not _paid_tier(req.session_id):
        raise HTTPException(
            status_code=402,
            detail="스무 사람을 다 보려면 '여덟 글자 전부' 부터요.")

    raw = load_features(req.chart_id)
    f = Features(**raw)
    try:
        return build_omnibus(f, req.chart_id, req.concern,
                             req.axis4, req.display_name, req.extras)
    except extras_mod.ExtraInputError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=422, detail=str(e))
