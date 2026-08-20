"""
24절기 — sxtwl 정밀 산출. docs/05_계산엔진_사양서.md §2-1, §2-2

★ 근사 테이블 금지. 매년 절입 시각이 다르다.

sxtwl 의 절입 시각은 **동경 120°(UTC+8, 북경시)** 기준으로 나온다.
이 모듈은 전부 **UTC(naive)** 로 정규화해서 돌려준다. 표준시 변천을 겪은
한국 데이터를 다루려면 UTC 로 두는 편이 사고가 없다.

검증 (KASI 한국천문연구원 공표값, KST):
    2025 입춘 2/3 23:10   2000 입춘 2/4 21:40   1985 입춘 2/4 06:12
"""
from __future__ import annotations

from datetime import datetime, timedelta
from functools import lru_cache

import sxtwl

# sxtwl jqIndex 순서 (0 = 동지)
JQ_NAMES = ["동지", "소한", "대한", "입춘", "우수", "경칩", "춘분", "청명",
            "곡우", "입하", "소만", "망종", "하지", "소서", "대서", "입추",
            "처서", "백로", "추분", "한로", "상강", "입동", "소설", "대설"]
JQ_HANJA = ["冬至", "小寒", "大寒", "立春", "雨水", "驚蟄", "春分", "淸明",
            "穀雨", "立夏", "小滿", "芒種", "夏至", "小暑", "大暑", "立秋",
            "處暑", "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪"]

# 節(절) = 홀수 인덱스. 中氣(중기)는 월 경계가 아니다.
# 節 인덱스 → 월지
JIE_TO_JI = {
    1: "丑",   # 소한
    3: "寅",   # 입춘
    5: "卯",   # 경칩
    7: "辰",   # 청명
    9: "巳",   # 입하
    11: "午",  # 망종
    13: "未",  # 소서
    15: "申",  # 입추
    17: "酉",  # 백로
    19: "戌",  # 한로
    21: "亥",  # 입동
    23: "子",  # 대설
}

SXTWL_UTC_OFFSET = timedelta(hours=8)   # sxtwl 반환값 = UTC+8

# sxtwl 이 안정적으로 다루는 범위 밖이면 계산을 거부한다 (지어내지 않는다)
MIN_YEAR, MAX_YEAR = 1900, 2100


class SolarTermError(ValueError):
    pass


def _to_utc(jd: float) -> datetime:
    t = sxtwl.JD2DD(jd)
    sec = float(t.s)
    whole = int(sec)
    micro = int(round((sec - whole) * 1_000_000))
    if micro >= 1_000_000:      # 반올림이 1초를 넘긴 경우
        whole += 1
        micro -= 1_000_000
    dt = datetime(int(t.Y), int(t.M), int(t.D), int(t.h), int(t.m)) \
        + timedelta(seconds=whole, microseconds=micro)
    return dt - SXTWL_UTC_OFFSET


@lru_cache(maxsize=512)
def terms_of_saju_year(saju_year: int) -> tuple[tuple[int, datetime], ...]:
    """
    사주년 `saju_year` 한 해의 절기 25개.
    입춘(saju_year) 부터 입춘(saju_year+1) 까지. (jqIndex, utc) 오름차순.
    """
    if not (MIN_YEAR <= saju_year <= MAX_YEAR):
        raise SolarTermError(
            f"지원 범위 밖입니다: {saju_year}년 ({MIN_YEAR}~{MAX_YEAR})")
    return tuple((int(it.jqIndex) % 24, _to_utc(it.jd))
                 for it in sxtwl.getJieQiByYear(saju_year))


@lru_cache(maxsize=512)
def ipchun_utc(year: int) -> datetime:
    """해당 양력 연도의 입춘 절입 시각 (UTC)."""
    return terms_of_saju_year(year)[0][1]


def saju_year_of(instant: datetime) -> int:
    """입춘 기준 사주 연도. 입춘 절입 '시각' 이전이면 전년도."""
    y = instant.year
    if instant < ipchun_utc(y):
        y -= 1
    # 12월 하순 출생이 다음 해 입춘을 넘는 일은 없으나 방어적으로 확인
    elif y + 1 <= MAX_YEAR and instant >= ipchun_utc(y + 1):
        y += 1
    return y


def jie_terms(saju_year: int) -> list[tuple[int, datetime]]:
    """
    그 사주년의 12절(節)만. 입춘 → … → 소한 순.

    terms_of_saju_year 는 입춘(y) ~ 입춘(y+1) 25개를 주므로 節만 걸러내면
    끝에 다음 해 입춘이 하나 더 붙는다. 그건 다음 사주년 것이므로 잘라낸다.
    """
    jie = [(i, t) for i, t in terms_of_saju_year(saju_year) if i % 2 == 1]
    return jie[:12]


def current_jie(instant: datetime) -> tuple[int, datetime, str]:
    """
    `instant` 가 속한 절(節). (jqIndex, 절입 UTC, 월지) 를 돌려준다.
    """
    sy = saju_year_of(instant)
    found = None
    for idx, t in jie_terms(sy):
        if t <= instant:
            found = (idx, t)
        else:
            break
    if found is None:
        raise SolarTermError(f"절 판정 실패: {instant!r} (사주년 {sy})")
    return found[0], found[1], JIE_TO_JI[found[0]]


def neighbouring_jie(instant: datetime) -> tuple[datetime, datetime]:
    """
    대운수용. (직전 절입, 다음 절입) UTC.
    사주년 경계를 넘어야 할 수 있으므로 앞뒤 해를 함께 훑는다.
    """
    sy = saju_year_of(instant)
    seq: list[datetime] = []
    for y in (sy - 1, sy, sy + 1):
        if MIN_YEAR <= y <= MAX_YEAR:
            seq.extend(t for _, t in jie_terms(y))
    seq = sorted(set(seq))
    prev = next_ = None
    for t in seq:
        if t <= instant:
            prev = t
        elif next_ is None:
            next_ = t
    if prev is None or next_ is None:
        raise SolarTermError(f"인접 절입을 찾지 못했습니다: {instant!r}")
    return prev, next_


def term_name(jq_index: int) -> str:
    return JQ_NAMES[jq_index % 24]


def term_hanja(jq_index: int) -> str:
    return JQ_HANJA[jq_index % 24]
