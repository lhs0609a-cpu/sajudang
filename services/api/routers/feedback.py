"""
POST /v1/feedback — 응답 기록. hit율 데이터의 원천.

★ 이게 쌓여야 공감률을 화면에 띄울 수 있습니다. 100건 미만이면 안 띄웁니다.
"""
from fastapi import APIRouter, HTTPException

import repo
from routers.chart import load_features
from schemas.api import FeedbackRequest, FeedbackResponse

router = APIRouter(prefix="/v1", tags=["feedback"])


@router.post("/feedback", response_model=FeedbackResponse)
def post_feedback(req: FeedbackRequest) -> FeedbackResponse:
    features = load_features(req.chart_id)
    n = repo.record_answer(
        req.statement_id, req.chart_id, req.answer, features,
        stage=req.stage, lens_id=req.lens_id,
        concern=req.concern, axis4=req.axis4)
    return FeedbackResponse(ok=True, recorded=n)


@router.get("/agreement")
def get_agreement(statement_id: str) -> dict:
    """
    공감률 조회. 응답 100건 미만이면 `{"shown": false}` — 숫자를 주지 않는다.
    화면에서 "예시" 숫자를 만들어 채우지 마세요.
    """
    a = repo.agreement(statement_id)
    if a is None:
        return {"shown": False, "min_responses": repo.MIN_RESPONSES_TO_SHOW}
    return {"shown": True, **a}
