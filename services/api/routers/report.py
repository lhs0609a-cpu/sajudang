"""POST /v1/report — 리포트. tier 별 잠금 차등."""
from fastapi import APIRouter, HTTPException

from engine import lens as lens_mod
from engine.features import Features
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
                            req.concern, req.axis4)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    return ReportResponse(**data)
