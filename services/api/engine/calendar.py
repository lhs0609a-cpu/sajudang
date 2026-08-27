"""
만세력 — docs/05_계산엔진_사양서.md 구현.

★ 이 파일이 서비스의 근간입니다. 절기·대운수 근사식 절대 금지.

산출 순서
    ① 시각 보정   표준시 변천 → 서머타임 → 진태양시
    ② 사주팔자    년주(입춘) → 월주(절입) → 일주(율리우스) → 시주(오서둔)
    ③ 대운        순행/역행 · 대운수는 절입일 기준 정식 계산

정책 상수는 파일 상단에 모아 두었습니다. 바꾸면 기존 사용자 결과가
달라지므로 변경 시 마이그레이션 계획을 먼저 세우세요.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Literal, Optional

from .constants import GAN, JI, OHO, OSEO, YIN_YANG
from . import solar_terms as st
from . import timezone_kr as tz
from .timezone_kr import std_label, table_is_dst as is_dst, table_std_meridian as std_meridian

# ── 정책 상수 ──────────────────────────────────────────────
# 자시 정책. "조자시": 23:00~23:59 를 익일 일주로 넘김 (권장·확정)
#            "야자시": 당일 일주 유지, 시주만 子
ZI_POLICY: Literal["조자시", "야자시"] = "조자시"

# 절입 경계를 무엇으로 비교하는가.
#   "corrected" — 진태양시로 보정한 시각과 비교 (참조 구현체·docs/05 §1-4 순서)
#   "standard"  — 보정 전 표준시각과 비교 (절입 공표값과 같은 프레임)
# 두 방식은 절입 전후 약 32분(서울 기준) 구간의 출생자에서만 결과가 갈립니다.
JIEQI_BASIS: Literal["corrected", "standard"] = "corrected"

# 대운수 나머지 처리. "round" 반올림 / "floor" 버림
DAEUN_ROUNDING: Literal["round", "floor"] = "round"
DAEUN_COUNT = 8          # 대운 몇 구간까지 산출할지

# 시각 미상일 때 절입·일주 경계 판정에 쓰는 기준 시각 (시주는 산출하지 않는다)
HOUR_UNKNOWN_PROXY_MIN = 12 * 60


# ── 날짜 검사 ──────────────────────────────────────────────
#
# ★ 화면과 **같은 규칙 · 같은 말투**여야 합니다.
#   apps/web/lib/birth.ts 의 birthProblem() 과 짝입니다. 그쪽이 먼저
#   막아 주지만 진짜 방어선은 이쪽이고, 이쪽이 영어로 말하면 주소로
#   바로 들어온 사람에게 파이썬 원문이 뜹니다.
_DAYS_IN = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def days_in_month(year: int, month: int) -> int:
    if month == 2 and ((year % 4 == 0 and year % 100 != 0) or year % 400 == 0):
        return 29
    return _DAYS_IN[month - 1]


def check_birth_date(year: int, month: int, day: int) -> None:
    """없는 날이면 우리말로 거절한다. 문제 없으면 조용히 돌아간다."""
    if not 1 <= month <= 12:
        raise ValueError("달은 1에서 12 사이요. (받은 것 %r)" % (month,))
    last = days_in_month(year, month)
    if not 1 <= day <= last:
        raise ValueError("%d년 %d월은 %d일까지요. (받은 것 %r)"
                         % (year, month, last, day))


# ── 시각 보정 ──────────────────────────────────────────────
CITY_LON = {
    "서울": 126.98, "인천": 126.71, "수원": 127.01, "춘천": 127.73,
    "강릉": 128.90, "대전": 127.38, "청주": 127.49, "전주": 127.15,
    "광주": 126.85, "목포": 126.39, "대구": 128.60, "안동": 128.73,
    "포항": 129.36, "부산": 129.08, "울산": 129.31, "창원": 128.68,
    "제주": 126.53,
}
DEFAULT_CITY = "서울"


def jdn(y: int, m: int, d: int) -> int:
    """율리우스 일수. docs/05 §2-3"""
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045


JDN_BASE = jdn(1900, 1, 1)          # 1900-01-01 = 甲戌
_BASE_GAN = GAN.index("甲")
_BASE_JI = JI.index("戌")


def day_ganji(d: date) -> tuple[str, str]:
    n = jdn(d.year, d.month, d.day) - JDN_BASE
    return GAN[(n + _BASE_GAN) % 10], JI[(n + _BASE_JI) % 12]


# ── 자료구조 ───────────────────────────────────────────────
@dataclass(frozen=True)
class Pillar:
    gan: str
    ji: str
    label: str

    @property
    def gz(self) -> str:
        return self.gan + self.ji


@dataclass
class Correction:
    """화면에 그대로 노출하는 보정 내역. docs/05 §10"""
    std_label: str
    std_deg: float
    dst: bool
    city: str
    lon: float
    lon_min: float                 # 진태양시 보정량(분)
    before: str                    # 입력 시각
    after: str                     # 보정 후 시각
    day_shift: int                 # -1 / 0 / +1
    zi_policy: str
    jieqi_basis: str
    jieqi_name: str                # 그 사주가 속한 절
    jieqi_at_kst: str              # 절입 시각 (당시 한국 표준시 표기)
    hour_used: bool                # 시주를 산출했는가
    boundary_note: Optional[str] = None


@dataclass
class Daeun:
    index: int
    gan: str
    ji: str
    start_age: int

    @property
    def gz(self) -> str:
        return self.gan + self.ji


@dataclass
class Chart:
    pillars: list                  # 시각 미상이면 3개 (년월일)
    year_pillar: Pillar
    month_pillar: Pillar
    day_pillar: Pillar
    hour_pillar: Optional[Pillar]
    day_gan: str
    day_ji: str
    hour_known: bool
    sex: str
    saju_year: int
    forward: bool                  # 대운 순행 여부
    daeun_start: float             # 대운수 (소수 포함 원값)
    daeun: list
    correction: Correction
    birth_instant_utc: datetime
    solar_time: datetime           # 진태양시(균시차 제외) 기준 일시


# ── 본체 ───────────────────────────────────────────────────
def _fmt_hm(total_min: float) -> str:
    m = int(round(total_min)) % 1440
    return "%02d:%02d" % (m // 60, m % 60)


def build_chart(year: int, month: int, day: int,
                hour: Optional[int], minute: Optional[int],
                sex: str, hour_known: bool = True,
                city: str = DEFAULT_CITY,
                longitude: Optional[float] = None) -> Chart:
    """
    사주 명식을 세운다.

    hour_known=False 이면 시주를 산출하지 않고 3주만 돌려준다.
    12시로 가정해 시주를 채우지 않는다 — 없는 정보를 만드는 것이므로.
    (다만 절입·일주 경계 판정에는 기준 시각이 하나 필요하므로 정오를 쓰고,
     그 때문에 결과가 갈릴 수 있는 경우 correction.boundary_note 에 남긴다.)
    """
    if sex not in ("M", "F"):
        raise ValueError("sex 는 'M' 또는 'F' 여야 합니다: %r" % (sex,))

    # ★ 날짜가 있는 날인지 여기서 본다.
    #   전에는 이 검사가 없어서 2월 30일이 tz.offsets() 안쪽까지 흘러갔고,
    #   파이썬의 "day is out of range for month" 가 그대로 400 본문으로
    #   나갔습니다. 화면(apps/web/lib/birth.ts)은 우리말로 막는데 서버만
    #   영어로 말하고 있었습니다 — 방어선 둘의 말이 달랐습니다.
    check_birth_date(year, month, day)

    lon = longitude if longitude is not None else CITY_LON.get(city, CITY_LON[DEFAULT_CITY])

    if hour_known:
        if hour is None:
            raise ValueError("hour_known=True 인데 hour 가 없습니다")
        clock_min = hour * 60 + (minute or 0)
        before = "%02d:%02d" % (hour, minute or 0)
    else:
        clock_min = HOUR_UNKNOWN_PROXY_MIN
        before = "미상"

    # ① 표준시 변천 · 서머타임 — 전환 '시각'까지 반영 (timezone_kr)
    total_off, dst_delta, std = tz.offsets(
        year, month, day, clock_min // 60, clock_min % 60)
    dst = dst_delta.total_seconds() != 0
    lon_min = (lon - std) * 4.0

    # 표준시 기준 분 (서머타임 되돌림)
    std_min = clock_min - int(dst_delta.total_seconds() // 60)

    # 절대 시각 (UTC)
    birth_utc = (datetime(year, month, day)
                 + timedelta(minutes=clock_min)
                 - total_off)

    # ② 진태양시 (균시차 미반영 — docs/05 §1-5, 2차 검토 항목)
    solar_min = std_min + lon_min
    day_shift = 0
    if solar_min < 0:
        solar_min += 1440
        day_shift = -1
    elif solar_min >= 1440:
        solar_min -= 1440
        day_shift = 1
    solar_date = date(year, month, day) + timedelta(days=day_shift)
    solar_dt = (datetime(solar_date.year, solar_date.month, solar_date.day)
                + timedelta(minutes=solar_min))

    # ③ 절입 비교 기준 시각
    if JIEQI_BASIS == "corrected":
        ref = birth_utc + timedelta(minutes=lon_min)
    else:
        ref = birth_utc

    saju_year = st.saju_year_of(ref)
    jq_idx, jq_at, month_ji = st.current_jie(ref)

    # 년주
    yg = GAN[(saju_year - 4) % 10]
    yj = JI[(saju_year - 4) % 12]
    # 월간 — 오호둔
    off = (JI.index(month_ji) - JI.index("寅")) % 12
    mg = GAN[(GAN.index(OHO[yg]) + off) % 10]

    # 일주 — 진태양시 날짜 기준, 조자시면 익일로 넘김
    solar_hour = int(solar_min // 60)
    zi_rollover = (ZI_POLICY == "조자시" and hour_known and solar_hour == 23)
    day_date = solar_date + timedelta(days=1) if zi_rollover else solar_date
    dg, dj = day_ganji(day_date)

    year_p = Pillar(yg, yj, "년주")
    month_p = Pillar(mg, month_ji, "월주")
    day_p = Pillar(dg, dj, "일주")
    pillars = [year_p, month_p, day_p]

    hour_p = None
    if hour_known:
        hi = ((solar_hour + 1) % 24) // 2
        hour_p = Pillar(GAN[(GAN.index(OSEO[dg]) + hi) % 10], JI[hi], "시주")
        pillars.append(hour_p)

    # ④ 대운
    forward = (YIN_YANG[yg] == 1) == (sex == "M")
    prev_jie, next_jie = st.neighbouring_jie(ref)
    delta = (next_jie - ref) if forward else (ref - prev_jie)
    days = delta.total_seconds() / 86400.0
    raw = days / 3.0
    start = int(raw + 0.5) if DAEUN_ROUNDING == "round" else int(raw)
    start = max(1, start)

    daeun = []
    for i in range(DAEUN_COUNT):
        k = (i + 1) if forward else -(i + 1)
        daeun.append(Daeun(
            index=i,
            gan=GAN[(GAN.index(mg) + k) % 10],
            ji=JI[(JI.index(month_ji) + k) % 12],
            start_age=start + i * 10,
        ))

    # ⑤ 보정 내역
    note = None
    if not hour_known:
        risks = []
        if jq_at.date() == ref.date():
            risks.append("절입일 출생 — 태어난 시각에 따라 월주가 달라질 수 있소")
        if abs((ref - st.ipchun_utc(saju_year)).total_seconds()) < 86400:
            risks.append("입춘 전후 — 시각에 따라 년주가 달라질 수 있소")
        risks.append("자시(23시~) 출생이면 일주가 하루 넘어가오")
        note = " / ".join(risks)
    elif abs((ref - jq_at).total_seconds()) < 86400:
        note = "%s 절입 전후 24시간 이내 출생" % st.term_name(jq_idx)

    era_offset = timedelta(hours=std / 15.0)
    # 표시용 — 초 단위 반올림
    jq_local = jq_at + era_offset + timedelta(seconds=30)
    jq_local = jq_local.replace(second=0, microsecond=0)

    corr = Correction(
        std_label=std_label(year, month, day),
        std_deg=std,
        dst=dst,
        city=city,
        lon=lon,
        lon_min=round(lon_min, 1),
        before=before,
        after=_fmt_hm(solar_min) if hour_known else "미상",
        day_shift=day_shift if hour_known else 0,
        zi_policy=ZI_POLICY,
        jieqi_basis=JIEQI_BASIS,
        jieqi_name="%s(%s)" % (st.term_name(jq_idx), st.term_hanja(jq_idx)),
        jieqi_at_kst=jq_local.strftime("%Y-%m-%d %H:%M"),
        hour_used=hour_known,
        boundary_note=note,
    )

    return Chart(
        pillars=pillars,
        year_pillar=year_p, month_pillar=month_p,
        day_pillar=day_p, hour_pillar=hour_p,
        day_gan=dg, day_ji=dj,
        hour_known=hour_known, sex=sex,
        saju_year=saju_year,
        forward=forward,
        daeun_start=round(raw, 3),
        daeun=daeun,
        correction=corr,
        birth_instant_utc=birth_utc,
        solar_time=solar_dt,
    )


def pillars_text(chart: Chart) -> str:
    """디버그·테스트용 한 줄 표기. 시각 미상이면 시주 자리를 ◇◇ 로."""
    parts = [p.gz for p in chart.pillars]
    if not chart.hour_known:
        parts.append("◇◇")
    return " ".join(parts)
