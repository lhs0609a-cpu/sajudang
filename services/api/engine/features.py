"""
Feature Store — 모든 해석의 원천. docs/05_계산엔진_사양서.md §3~§8

여기서 나온 값만 문장엔진·렌즈·릴레이가 사용합니다.
계산에 없는 값을 해석 단계에서 지어내지 않기 위한 경계선입니다.

★ hour_known=False 이면 시주를 집계에서 완전히 제외합니다.
  오행·십신·일지충 판정을 3주로만 수행합니다.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Optional

from .calendar import Chart, Daeun
from .constants import (
    CHUNG, HAP, ELEMENTS, GENERATES, GENERATED_BY, CONTROLS, CONTROLLED_BY,
    ELEMENT_OF_GAN, HIDDEN, TEN_GODS, TEN_GOD_GROUP, FLOWS,
    STRENGTH_DEUK_RYEONG, STRENGTH_DEUK_JI, STRENGTH_RATIO_BASE,
    STRENGTH_STRONG_AT, STRENGTH_WEAK_AT, FLOW_BIGYEOP_MARGIN,
    element_of, ten_god,
)


@dataclass
class Features:
    # ── 명식 ──
    pillars: list                    # [{"gan","ji","label","gz"}]
    day_gan: str
    day_ji: str
    hour_known: bool
    sex: str
    saju_year: int

    # ── 오행·강약 ──
    elements: dict                   # {"목":..,"화":..,"토":..,"금":..,"수":..}
    strength: str                    # 신강 / 중화 / 신약
    strength_score: int
    deuk_ryeong: bool
    deuk_ji: bool
    yongsin: str

    # ── 십신 ──
    ten_gods: dict                   # 10종 카운트 (0 포함)
    top_ten_god: str
    gwan: int
    jae: int
    sik: int
    bi: int
    inn: int

    # ── 파생 ──
    strong_el: str
    weak_el: str
    gap: float
    flow: str
    flow_el: str

    # ── 시간 ──
    age: int
    daeun: list                      # [{"gz","gan","ji","start_age","ten_god"}]
    daeun_now: int
    daeun_ten_god: str
    daeun_start: float

    # ── 관계 ──
    ilji_chung: bool
    ilji_hap: list

    # ── 투명성 ──
    correction: dict

    def to_dict(self) -> dict:
        return asdict(self)


def _element_table(pillars) -> dict:
    """천간 1.0 + 지지 지장간(본기 1.0 / 중기 0.3 / 여기 0.2). docs/05 §3"""
    el = {k: 0.0 for k in ELEMENTS}
    for p in pillars:
        el[ELEMENT_OF_GAN[p.gan]] += 1.0
        for g, w in HIDDEN[p.ji]:
            el[ELEMENT_OF_GAN[g]] += w
    return {k: round(v, 1) for k, v in el.items()}


def _strength(el: dict, day_gan: str, month_ji: str, day_ji: str):
    """득령 · 득지 · 득세. docs/05 §4 — 임계값은 constants.py"""
    me = ELEMENT_OF_GAN[day_gan]
    helper = [me, GENERATED_BY[me]]                    # 비겁 + 인성
    deuk_ryeong = element_of(month_ji) in helper
    deuk_ji = element_of(day_ji) in helper
    total = sum(el.values()) or 1.0
    ratio = sum(el[k] for k in helper) / total
    score = ((STRENGTH_DEUK_RYEONG if deuk_ryeong else 0)
             + (STRENGTH_DEUK_JI if deuk_ji else 0)
             + round((ratio - STRENGTH_RATIO_BASE) * 100))
    if score >= STRENGTH_STRONG_AT:
        label = "신강"
    elif score <= STRENGTH_WEAK_AT:
        label = "신약"
    else:
        label = "중화"
    return label, int(score), deuk_ryeong, deuk_ji


def _yongsin(el: dict, day_gan: str, strength: str) -> str:
    """억부법. 조후용신은 1차 제외 (docs/05 §5)."""
    me = ELEMENT_OF_GAN[day_gan]
    if strength == "신강":
        cands = [CONTROLS[me],        # 재성 — 내가 극하는 것
                 GENERATES[me],       # 식상 — 설기
                 CONTROLLED_BY[me]]   # 관성 — 나를 극하는 것
    else:
        cands = [me, GENERATED_BY[me]]   # 비겁 + 인성
    return min(cands, key=lambda e: el[e])


def _ten_gods(pillars, day_gan: str):
    """
    천간(일간 제외) + 지지 본기. docs/05 §6
    4주면 3+4=7개, 3주면 2+3=5개.

    카운트와 함께 '등장 순서'도 돌려준다. 최다 십신이 동률일 때
    년주 쪽을 먼저 잡기 위해서다. (10종 중 하나로 임의 고정하면
    그 십신에 표본이 몰린다 — 분포 검증에서 드러났던 문제.)
    """
    counts = {k: 0 for k in TEN_GODS}
    order = []

    def bump(g):
        name = ten_god(g, day_gan)
        counts[name] += 1
        if name not in order:
            order.append(name)

    for p in pillars:
        if p.label != "일주":
            bump(p.gan)
        bump(HIDDEN[p.ji][0][0])
    return counts, order


def _flow(el: dict, day_gan: str):
    """
    힘이 실제로 어디로 나가는가. docs/05 §8

    ★ 일간 오행을 rest 에서 반드시 뺀다. 빼지 않으면 신강 사주가
      전부 비겁으로 몰린다 (참조 구현체에서 실제로 났던 버그).
    """
    me = ELEMENT_OF_GAN[day_gan]
    rest = [k for k in el if k != me]
    sg = max(rest, key=lambda e: el[e])
    if el[me] - el[sg] >= FLOW_BIGYEOP_MARGIN:
        return "비겁", me
    if GENERATES[me] == sg:
        return "식상", sg
    if CONTROLS[me] == sg:
        return "재성", sg
    if CONTROLS[sg] == me:
        return "관성", sg
    return "인성", sg


def build_features(chart: Chart, as_of: Optional[date] = None) -> Features:
    as_of = as_of or date.today()

    # 계산에 쓰는 기둥 — 시각 미상이면 3주
    cp = chart.pillars
    day_gan, day_ji = chart.day_gan, chart.day_ji

    el = _element_table(cp)
    strength, score, dr, dj = _strength(
        el, day_gan, chart.month_pillar.ji, day_ji)
    yongsin = _yongsin(el, day_gan, strength)
    tg, tg_order = _ten_gods(cp, day_gan)

    strong_el = max(el, key=lambda e: el[e])
    weak_el = min(el, key=lambda e: el[e])
    flow, flow_el = _flow(el, day_gan)

    # max 는 동률이면 먼저 나온 것을 남긴다 → 년주 쪽 우선
    top_ten_god = max(tg_order, key=lambda k: tg[k])

    # 대운 — 현재 구간. 나이는 연 나이(올해 - 태어난 해), 대운수와 같은 기준.
    age = as_of.year - chart.solar_time.year
    daeun_list = []
    for d in chart.daeun:
        daeun_list.append({
            "index": d.index, "gz": d.gz, "gan": d.gan, "ji": d.ji,
            "start_age": d.start_age,
            "ten_god": ten_god(d.gan, day_gan),
        })
    now = 0
    for i, d in enumerate(chart.daeun):
        if d.start_age <= age:
            now = i
    if age < chart.daeun[0].start_age:
        now = 0

    # 일지 충·합 — 일주 자신은 제외
    others = [p.ji for p in cp if p.label != "일주"]
    ilji_chung = CHUNG[day_ji] in others
    ilji_hap = [j for j in others if HAP.get(day_ji) == j]

    return Features(
        pillars=[{"gan": p.gan, "ji": p.ji, "label": p.label, "gz": p.gz}
                 for p in cp],
        day_gan=day_gan, day_ji=day_ji,
        hour_known=chart.hour_known, sex=chart.sex,
        saju_year=chart.saju_year,
        elements=el,
        strength=strength, strength_score=score,
        deuk_ryeong=dr, deuk_ji=dj,
        yongsin=yongsin,
        ten_gods=tg, top_ten_god=top_ten_god,
        gwan=tg["정관"] + tg["편관"],
        jae=tg["정재"] + tg["편재"],
        sik=tg["식신"] + tg["상관"],
        bi=tg["비견"] + tg["겁재"],
        inn=tg["정인"] + tg["편인"],
        strong_el=strong_el, weak_el=weak_el,
        gap=round(el[strong_el] - el[weak_el], 1),
        flow=flow, flow_el=flow_el,
        age=age,
        daeun=daeun_list, daeun_now=now,
        daeun_ten_god=daeun_list[now]["ten_god"],
        daeun_start=chart.daeun_start,
        ilji_chung=ilji_chung, ilji_hap=ilji_hap,
        correction=_correction_dict(chart),
    )


def _birth_year(chart: Chart) -> int:
    """대운 나이 기준이 되는 출생 연도 (양력)."""
    return chart.solar_time.year


def _correction_dict(chart: Chart) -> dict:
    c = chart.correction
    return {
        "std_label": c.std_label, "std_deg": c.std_deg, "dst": c.dst,
        "city": c.city, "lon": c.lon, "lon_min": c.lon_min,
        "before": c.before, "after": c.after, "day_shift": c.day_shift,
        "zi_policy": c.zi_policy, "jieqi_basis": c.jieqi_basis,
        "jieqi_name": c.jieqi_name, "jieqi_at_kst": c.jieqi_at_kst,
        "hour_used": c.hour_used, "boundary_note": c.boundary_note,
    }
