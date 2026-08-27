"""여덟 글자를 **두 번째 방법으로 다시 구해** 엔진과 맞춘다.

    python tools/crosscheck.py            # 절기 + 회귀 50건 + 무작위 2,000명
    python tools/crosscheck.py 500        # 무작위 표본 수 지정

★ 왜 필요한가
  엔진 테스트는 엔진이 스스로 일관적인지를 봅니다. 절입 시각이 통째로
  틀려 있어도 "일관되게 틀린" 것은 못 잡습니다. 회귀 50건의 기대값은
  아직 전부 "?" 라 그 50건도 skip 됩니다. 그래서 **다른 계산으로**
  같은 답이 나오는지 봐야 합니다.

★ 무엇이 독립인가 — 여기서 sxtwl 은 한 줄도 쓰지 않습니다
  · 절입   태양 황경을 Meeus(Astronomical Algorithms 25장)로 직접 풀어
           λ = 315°(입춘) … 를 이분법으로 찾습니다. ΔT 보정 포함.
  · 일주   기준일을 엔진과 다르게 잡습니다. 엔진은 1900-01-01 甲戌,
           여기서는 2000-01-01 戊午 로 셉니다.
  · 년주   1984년 = 甲子년 에서 셉니다.
  · 월주   월지는 위에서 직접 푼 절입으로 가르고, 월간은 오호둔.
  · 시주   시지는 조자시 경계로, 시간은 오서둔.

★ 무엇이 독립이 아닌가 — 정직하게 적습니다
  표준시 변천·서머타임·진태양시 보정은 엔진의 `chart.solar_time` 을
  그대로 받아 씁니다. 그건 별도 테스트가 이미 지키고 있습니다
  (test_calendar.py 의 표준시·서머타임·진태양시 항목).
  즉 이 도구는 **"보정된 시각으로부터 여덟 글자를 뽑는 부분"** 과
  **"절입 시각 자체"** 를 봅니다.

★ 절입 비교 허용오차
  Meeus 저정밀 해는 황경 오차가 약 0.01° — 시간으로 약 15분입니다.
  그래서 20분을 허용합니다. 여기서 걸리는 것은 분 단위 오차가 아니라
  **날짜가 통째로 어긋나는** 종류입니다. 분 단위는 KASI 공표값과
  맞추는 test_calendar.py 의 입춘 대조가 봅니다.
"""
from __future__ import annotations

import math
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

GAN = "甲乙丙丁戊己庚辛壬癸"
JI = "子丑寅卯辰巳午未申酉戌亥"

# ══════════════════════════════════════════════════════════
# 1. 태양 황경 — sxtwl 없이
# ══════════════════════════════════════════════════════════
def jd_of(dt: datetime) -> float:
    """그레고리력 datetime(UT) → 율리우스일."""
    y, m = dt.year, dt.month
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    day = (dt.day + (dt.hour + (dt.minute + dt.second / 60.0) / 60.0) / 24.0)
    return (math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1))
            + day + b - 1524.5)


def dt_of(jd: float) -> datetime:
    """율리우스일 → datetime(UT). 초 단위 반올림."""
    z = math.floor(jd + 0.5)
    f = (jd + 0.5) - z
    alpha = math.floor((z - 1867216.25) / 36524.25)
    a = z + 1 + alpha - math.floor(alpha / 4)
    b = a + 1524
    c = math.floor((b - 122.1) / 365.25)
    d = math.floor(365.25 * c)
    e = math.floor((b - d) / 30.6001)
    day = b - d - math.floor(30.6001 * e) + f
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715
    di = int(day)
    secs = round((day - di) * 86400.0)
    return datetime(int(year), int(month), di) + timedelta(seconds=secs)


def delta_t_seconds(year: float) -> float:
    """TT - UT. Espenak & Meeus 다항식 (1900~2050 구간)."""
    if year < 1920:
        t = year - 1900
        return (-2.79 + 1.494119 * t - 0.0598939 * t ** 2
                + 0.0061966 * t ** 3 - 0.000197 * t ** 4)
    if year < 1941:
        t = year - 1920
        return 21.20 + 0.84493 * t - 0.076100 * t ** 2 + 0.0020936 * t ** 3
    if year < 1961:
        t = year - 1950
        return 29.07 + 0.407 * t - t ** 2 / 233.0 + t ** 3 / 2547.0
    if year < 1986:
        t = year - 1975
        return 45.45 + 1.067 * t - t ** 2 / 260.0 - t ** 3 / 718.0
    if year < 2005:
        t = year - 2000
        return (63.86 + 0.3345 * t - 0.060374 * t ** 2 + 0.0017275 * t ** 3
                + 0.000651814 * t ** 4 + 0.00002373599 * t ** 5)
    if year < 2050:
        t = year - 2000
        return 62.92 + 0.32217 * t + 0.005589 * t ** 2
    t = year - 1820
    return -20 + 32 * (t / 100.0) ** 2


def sun_longitude(jd_ut: float) -> float:
    """겉보기 태양 황경(도). Meeus 25장 저정밀."""
    year = 2000.0 + (jd_ut - 2451545.0) / 365.25
    jde = jd_ut + delta_t_seconds(year) / 86400.0
    t = (jde - 2451545.0) / 36525.0
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t * t
    m = math.radians(357.52911 + 35999.05029 * t - 0.0001537 * t * t)
    c = ((1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(m)
         + (0.019993 - 0.000101 * t) * math.sin(2 * m)
         + 0.000289 * math.sin(3 * m))
    omega = math.radians(125.04 - 1934.136 * t)
    return (l0 + c - 0.00569 - 0.00478 * math.sin(omega)) % 360.0


def _diff(jd: float, target: float) -> float:
    return ((sun_longitude(jd) - target + 180.0) % 360.0) - 180.0


def solve_term(target_deg: float, near: datetime) -> datetime:
    """황경이 `target_deg` 가 되는 순간(UT). `near` 부근에서 찾는다."""
    lo = jd_of(near) - 12.0
    while _diff(lo, target_deg) > 0:
        lo -= 5.0
    hi = lo + 1.0
    while _diff(hi, target_deg) < 0:
        hi += 1.0
        if hi - lo > 60:
            raise RuntimeError("절입을 못 찾음: %s %s" % (target_deg, near))
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if _diff(mid, target_deg) < 0:
            lo = mid
        else:
            hi = mid
    return dt_of((lo + hi) / 2.0)


# 節(절) 12개 — (월지 index, 황경, 대략 양력 월일)
JIE = [("寅", 315, (2, 4)), ("卯", 345, (3, 6)), ("辰", 15, (4, 5)),
       ("巳", 45, (5, 6)), ("午", 75, (6, 6)), ("未", 105, (7, 7)),
       ("申", 135, (8, 8)), ("酉", 165, (9, 8)), ("戌", 195, (10, 8)),
       ("亥", 225, (11, 7)), ("子", 255, (12, 7)), ("丑", 285, (1, 6))]


def jie_of_year(saju_year: int) -> list:
    """사주년의 12절 — (월지, UT). 입춘 → 소한."""
    out = []
    for ji, deg, (mm, dd) in JIE:
        y = saju_year + (1 if mm == 1 else 0)
        out.append((ji, solve_term(deg, datetime(y, mm, dd))))
    return out


# ══════════════════════════════════════════════════════════
# 2. 간지 — 엔진과 다른 기준으로
# ══════════════════════════════════════════════════════════
JDN_2000 = 2451545          # 2000-01-01 = 戊午 = 60갑자 54번
GZ_2000 = 54


def day_gz(d: date) -> str:
    n = (jd_of(datetime(d.year, d.month, d.day, 12)) + 0.5)
    idx = (int(n) - JDN_2000 + GZ_2000) % 60
    return GAN[idx % 10] + JI[idx % 12]


def year_gz(saju_year: int) -> str:
    idx = (saju_year - 1984) % 60      # 1984 = 甲子년
    return GAN[idx % 10] + JI[idx % 12]


def month_gz(saju_year: int, month_ji: str) -> str:
    """월간 = 오호둔. 甲己년 丙寅두(頭)."""
    ygan = (saju_year - 1984) % 10
    head = (ygan * 2 + 2) % 10                      # 그 해 寅월의 천간
    step = (JI.index(month_ji) - JI.index("寅")) % 12
    return GAN[(head + step) % 10] + month_ji


def hour_gz(day_gan: str, hour_ji: str) -> str:
    """시간 = 오서둔. 甲己일 甲子두(頭)."""
    head = (GAN.index(day_gan) * 2) % 10
    step = JI.index(hour_ji)
    return GAN[(head + step) % 10] + hour_ji


# ══════════════════════════════════════════════════════════
# 3. 엔진과 대조
# ══════════════════════════════════════════════════════════
from engine.calendar import build_chart            # noqa: E402
from engine import solar_terms as st               # noqa: E402

KST = timedelta(hours=9)
TOLERANCE_MIN = 20          # Meeus 저정밀 해의 한계 (황경 0.01° ≈ 15분)


def check_terms(y0: int, y1: int):
    """절입 시각 — 독립 계산 vs 엔진(sxtwl).

    ★ 날짜가 갈리는데 허용오차 안이면 그건 **내 쪽 한계**입니다.
      절입이 자정에서 몇 분 떨어져 있으면, 15분 정밀도로는 어느 날인지
      가릴 수 없습니다. 엔진을 탓할 일이 아니므로 따로 셉니다.
      (저정밀 해는 KASI 대비 3~12분 일찍 나오는 쏠림이 있습니다.
       분 단위는 test_calendar.py 의 입춘 KASI 대조가 봅니다.)
    """
    bad, near_midnight = [], []
    for y in range(y0, y1 + 1):
        mine = jie_of_year(y)
        theirs = st.jie_terms(y)
        assert len(mine) == len(theirs) == 12
        for (ji, t_mine), (idx, t_eng) in zip(mine, theirs):
            eng_ji = st.JIE_TO_JI[idx]
            gap = abs((t_mine - t_eng).total_seconds()) / 60.0
            if eng_ji != ji:
                bad.append((y, ji, eng_ji, "월지 어긋남", gap))
            elif gap > TOLERANCE_MIN:
                bad.append((y, ji, st.term_name(idx), "%.1f분 차이" % gap, gap))
            elif (t_mine + KST).date() != (t_eng + KST).date():
                near_midnight.append((y, st.term_name(idx),
                                      (t_eng + KST).strftime("%m-%d %H:%M"),
                                      gap))
    return bad, near_midnight


def rebuild(ch) -> str:
    """엔진의 보정 결과만 받아, 여덟 글자를 독립 규칙으로 다시 짠다."""
    ref = ch.birth_instant_utc + timedelta(minutes=ch.correction.lon_min)

    # 년주 — 입춘(직접 푼 것) 기준
    y = ref.year
    if ref < solve_term(315, datetime(y, 2, 4)):
        y -= 1
    yp = year_gz(y)

    # 월주 — 12절(직접 푼 것) 중 ref 이하의 마지막 것
    month_ji = None
    for ji, at in jie_of_year(y):
        if ref >= at:
            month_ji = ji
    assert month_ji, "절입 이전으로 떨어졌습니다"
    mp = month_gz(y, month_ji)

    # 일주 — 조자시면 익일
    s = ch.solar_time
    d = s.date() + (timedelta(days=1)
                    if (ch.hour_known and s.hour == 23) else timedelta())
    dp = day_gz(d)

    out = [yp, mp, dp]
    if ch.hour_known:
        out.append(hour_gz(dp[0], JI[((s.hour + 1) % 24) // 2]))
    return " ".join(out)


def engine_gz(ch) -> str:
    return " ".join(p.gz for p in ch.pillars)


def main(n=2000) -> int:
    print("여덟 글자 교차검증 — sxtwl 을 쓰지 않는 두 번째 계산과 대조")
    print()

    print("[1] 절입 시각  1930~2050 · 12절 × 121년 = 1,452건")
    bad, near = check_terms(1930, 2050)
    if bad:
        print("    ★ 어긋남 %d건" % len(bad))
        for row in bad[:15]:
            print("      %d %s %s — %s" % row[:4])
    else:
        print("    OK — 1,452건 전부 %d분 안에서 일치" % TOLERANCE_MIN)
    if near:
        print("    참고 · 자정에서 %d분 안쪽이라 날짜를 가릴 수 없는 절입 %d건"
              % (TOLERANCE_MIN, len(near)))
        for y, nm, at, gap in near:
            print("      %d %s  엔진 %s KST (차 %.1f분)" % (y, nm, at, gap))

    print()
    print("[2] 회귀 50건 (tests/fixtures/charts.json)")
    import json
    cases = json.loads((ROOT / "tests" / "fixtures" / "charts.json")
                       .read_text(encoding="utf-8"))
    diffs = []
    for c in cases:
        i = c["input"]
        ch = build_chart(i["year"], i["month"], i["day"], i["hour"],
                         i["minute"], i["sex"], i.get("hour_known", True),
                         i.get("city", "서울"))
        a, b = engine_gz(ch), rebuild(ch)
        if a != b:
            diffs.append((c["id"], c.get("note", ""), a, b))
    print("    %d건 중 어긋남 %d건" % (len(cases), len(diffs)))
    for cid, note, a, b in diffs[:20]:
        print("      %-12s %s" % (cid, note))
        print("        엔진 %s" % a)
        print("        독립 %s" % b)

    print()
    print("[3] 무작위 %d명 (1930~2050)" % n)
    rng = random.Random(20260825)
    rdiff = []
    for _ in range(n):
        y = rng.randint(1930, 2050)
        m = rng.randint(1, 12)
        d = rng.randint(1, 28)
        hh, mm = rng.randint(0, 23), rng.randint(0, 59)
        ch = build_chart(y, m, d, hh, mm, rng.choice("FM"), True)
        a, b = engine_gz(ch), rebuild(ch)
        if a != b:
            rdiff.append(("%04d-%02d-%02d %02d:%02d" % (y, m, d, hh, mm), a, b))
    print("    어긋남 %d건" % len(rdiff))
    for when, a, b in rdiff[:20]:
        print("      %s   엔진 %s / 독립 %s" % (when, a, b))

    total = len(bad) + len(diffs) + len(rdiff)
    print()
    if total:
        print("[FAIL] 어긋남 %d건 — 어느 쪽이 맞는지 확인이 필요합니다" % total)
        return 1
    print("[OK] 두 계산이 전부 같은 답을 냈습니다")
    return 0


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 2000))
