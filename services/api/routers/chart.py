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


def _divergence(req: "ChartRequest") -> dict | None:
    """
    다른 만세력과 갈릴 수 있는 자리인가 — **먼저** 말한다.

    ★ 왜 먼저 말하나

      손님은 다른 만세력과 대 봅니다. 백 명 중 넷다섯이 다르게 나옵니다
      (tools/divergence.py). 그때 「우리가 맞소」 도 「그쪽이 맞소」 도
      답이 아닙니다 — 갈리는 자리는 **계산이 아니라 선택**입니다.

      발견당하면 「틀린 집」이 되고, 먼저 말하면 「아는 집」이 됩니다.
      같은 사실인데 순서가 다릅니다.

    ★ 다른 답도 같이 냅니다

      감추면 숨긴 것이 됩니다. 저쪽 유파로는 무엇이 되는지까지 적어야
      손님이 스스로 견줄 수 있습니다.
    """
    from engine import calendar as cal

    def build(**over):
        old = {k: getattr(cal, k) for k in over}
        for k, v in over.items():
            setattr(cal, k, v)
        try:
            return cal.build_chart(
                req.year, req.month, req.day, req.hour, req.minute,
                req.sex, hour_known=req.hour_known, city=req.birth_city)
        finally:
            for k, v in old.items():
                setattr(cal, k, v)

    try:
        base = build()
        mine = [p.gz for p in base.pillars]
        out = []

        for over, why, ours, theirs in (
            ({"ZI_POLICY": "야자시"},
             "밤 11시 이후에 나셨소",
             "조자시 — 다음 날로 넘겨 보오",
             "야자시 — 그날로 두고 보는 집이 있소"),
            ({"JIEQI_BASIS": "standard"},
             "절기가 바뀌는 언저리에 나셨소",
             "진태양시로 고친 시각과 견주오",
             "표준시 그대로 견주는 집이 있소"),
        ):
            try:
                alt = [p.gz for p in build(**over).pillars]
            except Exception:                    # noqa: BLE001
                continue
            if alt == mine:
                continue
            names = ["년주", "월주", "일주", "시주"]
            moved = [names[i] for i in range(min(len(mine), len(alt)))
                     if mine[i] != alt[i]]
            out.append({
                "why": why, "ours": ours, "theirs": theirs,
                "moved": moved,
                "mine": " ".join(mine), "alt": " ".join(alt),
            })
        return {"cases": out} if out else None
    except Exception:                            # noqa: BLE001
        return None


# 마지막으로 못 센 까닭 셋. /health 가 보여 줍니다.
_RARITY_WHY: list[str] = []


def rarity_why() -> list[str]:
    return list(_RARITY_WHY)


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
            _RARITY_WHY.append("표가 지금 축과 안 맞습니다 (make_rarity 를 다시)")
            del _RARITY_WHY[:-3]
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
    except Exception as e:                       # noqa: BLE001
        # 희소도는 곁가지라 명식은 그대로 나갑니다. 다만 **왜 못 셌는지**는
        # 남깁니다 — 삼키면 배포본에서 「그냥 안 나온다」가 되고, 그때는
        # 표가 없는 건지 코드가 틀린 건지 알 길이 없습니다.
        _RARITY_WHY.append("%s: %s" % (type(e).__name__, e))
        del _RARITY_WHY[:-3]
        return None


@router.post("/chart", response_model=ChartResponse)
def post_chart(req: ChartRequest) -> ChartResponse:
    key = chart_key(req)
    cached = store.get_json(store.k_chart(key))
    if cached is not None:
        return ChartResponse(chart_id=key, features=cached, cached=True,
                             rarity=_rarity(cached),
                             divergence=_divergence(req))

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
                         rarity=_rarity(features),
                         divergence=_divergence(req))
