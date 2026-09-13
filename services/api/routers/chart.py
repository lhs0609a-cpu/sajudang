"""POST /v1/chart — 명식 산출. 가장 많이 불리는 엔드포인트."""
import hashlib

from fastapi import APIRouter, HTTPException

import store
from service_clock import today
from version import ENGINE_VER
from engine.calendar import build_chart
from engine.features import build_features
from engine.solar_terms import SolarTermError
from schemas.api import ChartRequest, ChartResponse

router = APIRouter(prefix="/v1", tags=["chart"])

# 명식 캐시가 사는 기간. 리포트·릴레이·일진이 전부 chart_id 로 이걸 꺼내
# 쓰므로 한 사람의 여정보다는 넉넉히 길어야 합니다. 90일이면 회고 루프와
# 공유 링크(90일)까지 덮습니다.
CHART_TTL = 90 * 24 * 3600


def _k_ver(key: str) -> str:
    """이 명식을 **어느 판으로** 세웠는가."""
    return "chartver:%s" % key


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
            detail="저장된 명식을 다시 계산해야 하오. 입력 정보와 구매 내역은 유지되오.",
            headers={"X-Chart-Rebuild": "1"})
    if (store.get_json(_k_ver(chart_id)) != ENGINE_VER or
            store.get_json("chartdate:" + chart_id) != today().isoformat()):
        raise HTTPException(status_code=409, detail="오늘 기준으로 명식을 갱신해야 하오.",
                            headers={"X-Chart-Rebuild": "1"})
    # The cache date is already checked above; reuse it for older snapshots.
    return {**f, "as_of": f.get("as_of") or store.get_json("chartdate:" + chart_id)}


@router.get("/chart/{chart_id}", response_model=ChartResponse)
def get_chart(chart_id: str) -> ChartResponse:
    """
    이미 세운 명식을 chart_id 로 다시 가져온다.

    브라우저를 새로고침하면 화면 상태는 날아가지만 chart_id 는 남소.
    이게 없으면 새로고침 한 번에 "아직 세우지 않았소" 로 돌아가오.
    """
    f = load_features(chart_id)
    return ChartResponse(chart_id=chart_id, features=f, cached=True,
                         rarity=_rarity(f))


def _divergence(req: "ChartRequest") -> dict | None:
    """
    다른 만세력과 갈릴 수 있는 자리인가 — **먼저** 말한다.

    ★ 왜 먼저 말하나

      손님은 다른 만세력과 대 보오. 백 명 중 넷다섯이 다르게 나오오
      (tools/divergence.py). 그때 「우리가 맞소」 도 「그쪽이 맞소」 도
      답이 아니오 — 갈리는 자리는 **계산이 아니라 선택**이오.

      발견당하면 「틀린 집」이 되고, 먼저 말하면 「아는 집」이 되오.
      같은 사실인데 순서가 다르오.

    ★ 다른 답도 같이 내오

      감추면 숨긴 것이 되오. 저쪽 유파로는 무엇이 되는지까지 적어야
      손님이 스스로 견줄 수 있소.
    """
    from engine import calendar as cal

    def build(**over):
        return cal.build_chart(
            req.year, req.month, req.day, req.hour, req.minute,
            req.sex, hour_known=req.hour_known, city=req.birth_city,
            **{k.lower(): v for k, v in over.items()})

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
            # ★ 여태 이걸 안 보고 있었습니다 — 셋 중 **가장 흔한** 자리인데요.
            #
            #   서울은 해가 남중하는 때가 표준시보다 32분 늦습니다. 시지
            #   경계는 두 시간마다 오니, 경계 뒤 32분 안에 태어난 사람은
            #   보정을 쓰는 집과 안 쓰는 집이 갈립니다 — **26.9%**,
            #   넷 중 하나 남짓입니다. 조자시 4.4% · 절입 0.1% 와 견주세요.
            #
            #   2026-09-03 에 손님이 실제로 들고 왔습니다. 1993-11-25
            #   13:00 서울 — 우리는 壬午, 저쪽 만세력은 癸未. 그런데
            #   화면은 「갈리는 자리 없음」 이라 잠자코 있었습니다.
            #   먼저 말하기로 해 놓고 가장 흔한 자리를 빼놓고 있었습니다.
            ({"HOUR_BASIS": "standard"},
             "고을 보정으로 시가 갈리는 자리에 나셨소",
             "태어난 고을의 해로 고쳐 보오 (서울은 32분)",
             "시계 시각 그대로 보는 집이 있소"),
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

    ★ 표가 없거나 낡았으면 **아무것도 안 내오.** 지어낸 숫자를
      진짜처럼 내면 이 집이 하지 않기로 한 일을 하는 것이오.
    """
    from engine import rarity as rr
    from engine.features import Features
    try:
        if rr.is_stale():
            _RARITY_WHY.append("표가 지금 축과 안 맞소 (make_rarity 를 다시)")
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
    from datetime import date
    from engine.calendar import CITY_LON, check_birth_date
    try:
        check_birth_date(req.year, req.month, req.day)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    born = date(req.year, req.month, req.day)
    now = today()
    if born > now:
        raise HTTPException(status_code=400, detail="생년월일이 오늘보다 뒤이오. 태어난 날짜를 확인해 주시오.")
    age = now.year - born.year - ((now.month, now.day) < (born.month, born.day))
    if age < 14:
        raise HTTPException(status_code=400, detail="만 14세 이상만 이용할 수 있소.")
    if req.birth_city not in CITY_LON:
        raise HTTPException(status_code=400, detail="현재 지원하는 국내 출생 도시를 선택해 주시오. 해외 출생은 아직 지원하지 않소.")
    key = chart_key(req)
    cached = store.get_json(store.k_chart(key))
    # ★ 「같은 입력이면 같은 결과」는 **엔진이 안 바뀔 때만** 참이오
    #   (2026-09-07).
    #
    #   이 집은 신살·용신·대운 정책을 고치는 집이오. 그런데 열쇠에
    #   판이 없어서, 고쳐도 **이미 계산된 손님에게는 90일 동안 옛
    #   명식이 나갔소.** 홍염을 넣고 배포한 뒤 실제로 그랬소 —
    #   처음 오는 사람에게는 뜨고, 전에 온 사람에게는 안 떴소.
    #
    #   판이 다르면 캐시를 안 쓰고 다시 세우오. 열쇠(chart_id)는
    #   그대로 두오 — 바꾸면 이미 치른 주문과 리포트가 딴 명식을
    #   가리키오.
    if cached is not None and (store.get_json(_k_ver(key)) != ENGINE_VER or
                              store.get_json("chartdate:" + key) != now.isoformat() or
                              not cached.get("as_of") or
                              (not req.hour_known and not cached.get("hour_sensitivity"))):
        cached = None
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

    features = build_features(chart, as_of=now).to_dict()
    if not req.hour_known:
        from engine.hour_sensitivity import compare
        features["hour_sensitivity"] = compare(req.year, req.month, req.day, req.sex, req.birth_city)
    # 같은 입력이면 같은 결과라 캐시합니다. 다만 **무기한은 아닙니다** —
    # 다시 세우는 데 0.2ms 밖에 안 드는데 한 벌이 5KB 라, 만기를 안 주면
    # 저장소가 줄어들 힘이 하나도 없습니다. 만료돼도 다음 요청에 다시
    # 만들어지므로 사용자에게는 아무 차이가 없습니다.
    store.set_json(store.k_chart(key), features, ttl=CHART_TTL)
    # 어느 판으로 세웠는지 함께 찍습니다 — 명식과 같은 만기로.
    store.set_json(_k_ver(key), ENGINE_VER, ttl=CHART_TTL)
    store.set_json("chartdate:" + key, now.isoformat(), ttl=CHART_TTL)
    return ChartResponse(chart_id=key, features=features, cached=False,
                         rarity=_rarity(features),
                         divergence=_divergence(req))
