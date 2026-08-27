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


# ══════════════════════════════════════════════════════════
# 자격 — 이 사람이 실제로 무엇을 치렀는가
# ══════════════════════════════════════════════════════════
#
# ★ 여기가 비어 있었습니다.
#   `/v1/omnibus` 는 주문 기록을 보는데 **리포트 본체는 클라이언트가
#   보낸 tier 를 그대로 믿었습니다.** 값을 한 푼도 안 치른 요청에
#   `tier="one"` 을 실어 보내면 19컷 8,339자가 그대로 나갔습니다.
#   화면은 그 값을 localStorage 에서 읽어 보냅니다 — 브라우저에서
#   한 글자만 고치면 스무 캐릭터가 전부 열렸습니다.
#
# ★ 402 로 거절하지 않고 **치른 만큼으로 낮춰서** 내려보냅니다.
#   무료 구간은 누구에게나 보여야 하고, 무엇이 잠겼는지는 `locked` 가
#   제목과 근거로 말합니다. 빈 화면을 보이는 것이 가장 나쁩니다.
#   응답의 `tier` 는 **실제로 내려간 티어**입니다 — 화면이 그걸 보고
#   자기 기록을 고칠 수 있어야 합니다.
#
# ★ '이 자리 하나' 는 그 캐릭터에만 붙습니다.
#   풍운도령을 치르고 홍매파를 열 수는 없습니다. 캐릭터 값이 곧
#   「이 자리 하나」 값이기 때문입니다 (payments.price_of).
TIER_RANK = {"free": 0, "one": 1, "all": 2, "sub": 2}


def _paid_orders(session_id: str | None):
    """이 세션이 치른 주문들. 클라이언트 말이 아니라 저장된 기록입니다."""
    if not session_id:
        return
    for oid in store.get_json("orders:" + session_id) or []:
        o = store.get_json("order:" + oid)
        if o and o.get("status") == "paid":
            yield o


def entitled_tier(session_id: str | None, lens_id: str) -> str:
    """이 사람이 이 캐릭터에게서 실제로 열 수 있는 티어."""
    best = "free"
    for o in _paid_orders(session_id):
        t = o.get("tier")
        if t not in TIER_RANK:
            continue
        # '이 자리 하나' 는 치른 그 캐릭터에서만 열립니다.
        if t == "one" and o.get("lens_id") != lens_id:
            continue
        if TIER_RANK[t] > TIER_RANK[best]:
            best = t
    return best


@router.post("/report", response_model=ReportResponse)
def post_report(req: ReportRequest) -> ReportResponse:
    raw = load_features(req.chart_id)
    try:
        lens_mod.get(req.lens_id)
    except lens_mod.LensError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # 클라이언트가 부른 티어와 치른 티어 중 **낮은 쪽**으로 냅니다.
    allowed = entitled_tier(req.session_id, req.lens_id)
    tier = req.tier if TIER_RANK[req.tier] <= TIER_RANK[allowed] else allowed

    f = Features(**raw)
    try:
        data = build_report(f, req.chart_id, req.lens_id, tier,
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
      8만 자가 빠져나갑니다. (리포트 본체도 이제 같은 기록을 봅니다 —
      `entitled_tier`)
    """
    best = None
    for o in _paid_orders(session_id):
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
