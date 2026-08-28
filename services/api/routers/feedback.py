"""
POST /v1/feedback — 응답 기록. hit율 데이터의 원천.
POST /v1/review   — 별점·후기. '결제 확인됨' 은 **주문 기록이** 정합니다.

★ 이게 쌓여야 공감률을 화면에 띄울 수 있습니다. 100건 미만이면 안 띄웁니다.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import repo
from engine import lens as lens_mod
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


# ══════════════════════════════════════════════════════════
# 후기
# ══════════════════════════════════════════════════════════
class ReviewRequest(BaseModel):
    lens_id: str
    # 둘 다 선택입니다 — 별점만 주고 갈 수도, 글만 남길 수도 있습니다.
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    body: str = Field(default="", max_length=repo.REVIEW_MAX)
    # 자격을 보는 열쇠. 화면이 "결제했다" 고 말하는 것은 믿지 않습니다.
    session_id: Optional[str] = None
    chart_id: Optional[str] = None


class ReviewResponse(BaseModel):
    ok: bool
    verified: bool
    # 금지어에 걸리면 저장은 하되 화면에는 안 나갑니다. 그 사실을 숨기지
    # 않고 손님에게도 말합니다.
    visible: bool
    say: str


@router.post("/review", response_model=ReviewResponse)
def post_review(req: ReviewRequest) -> ReviewResponse:
    if req.rating is None and not req.body.strip():
        raise HTTPException(status_code=422,
                            detail="별을 놓든 말을 적든, 하나는 있어야 하오.")
    try:
        lens_mod.get(req.lens_id)
    except lens_mod.LensError:
        raise HTTPException(status_code=404, detail="모르는 사람이오.")

    # ★ '결제 확인됨' 은 **치른 주문**이 정합니다. (표시광고법 · docs/11)
    #   화면이 보낸 tier 나 paid 플래그를 믿으면 그건 광고 문구를
    #   손님이 스스로 다는 것과 같습니다.
    from routers.report import entitled_tier
    verified = entitled_tier(req.session_id, req.lens_id) != "free"

    r = repo.record_review(
        lens_id=req.lens_id, rating=req.rating, body=req.body,
        verified=verified, chart_id=req.chart_id)

    if not r["visible"]:
        say = ("남기신 말은 받아 두었소. 다만 여기 내걸 수는 없는 말이 "
               "섞였구려 — 우리 쪽에서만 읽겠소.")
    elif verified:
        say = "고맙소. 값을 치르고 끝까지 읽으신 분의 말로 적어 두겠소."
    else:
        say = "고맙소. 적어 두었소."

    return ReviewResponse(ok=True, verified=verified,
                          visible=r["visible"], say=say)


@router.get("/review/stats")
def review_stats(lens_id: Optional[str] = None) -> dict:
    """
    쌓인 후기 수. **평균 별점은 아직 화면에 내걸지 않습니다** —
    공감률과 같은 규칙입니다. 여기서는 운영자가 보려고 셉니다.
    """
    return repo.review_stats(lens_id)


@router.get("/agreement")
def get_agreement(statement_id: str) -> dict:
    """
    공감률 조회. 응답 100건 미만이면 `{"shown": false}` — 숫자를 주지 않는다.
    화면에서 "예시" 숫자를 만들어 채우지 마세요.
    """
    a = repo.agreement(statement_id)
    if a is None:
        # ★ 숫자가 없다고 자리를 비워 두지 않습니다.
        #   공감률은 못 내지만 **몇 번 나갔는지**는 지어내지 않고 낼 수
        #   있습니다. 정확도 주장이 아니라 사실 진술입니다.
        #   0이면 아무것도 안 냅니다 — 없는 것을 있는 척하지 않습니다.
        return {"shown": False, "seen": repo.exposure(statement_id),
                "min_responses": repo.MIN_RESPONSES_TO_SHOW}
    return {"shown": True, **a}
