"""
만세력 회귀·불변식 테스트 — docs/05_계산엔진_사양서.md §9

두 종류가 있습니다.

1. 불변식 테스트 — 외부 대조 없이 항상 돌아갑니다.
   율리우스 기준일, 절입 시각(KASI 공표값), 표준시·서머타임,
   자시 정책, 오호둔·오서둔, 대운 방향 등.

2. 회귀 테스트 — tests/fixtures/charts.json 의 50건.
   기대값에 "?" 가 남아 있으면 그 케이스는 skip 됩니다.
   **전량 통과하기 전에는 UI 작업으로 넘어가지 않습니다.**
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from engine import solar_terms as st
from engine import timezone_kr as tz
from engine.calendar import (
    GAN, JI, ZI_POLICY, build_chart, day_ganji, jdn, pillars_text,
)
from engine.constants import OHO, OSEO
from engine.features import build_features

FIXTURES = Path(__file__).parent / "fixtures" / "charts.json"
KST = timedelta(hours=9)


# ══════════════════════════════════════════════════════════
# 1. 일주 — 율리우스 일수
# ══════════════════════════════════════════════════════════
@pytest.mark.parametrize("y,m,d,gz", [
    (1900, 1, 1, "甲戌"),      # docs/05 §2-3 기준일
    (2000, 1, 1, "戊午"),      # docs/05 §2-3 검증값
])
def test_day_ganji_anchors(y, m, d, gz):
    assert "".join(day_ganji(date(y, m, d))) == gz


def test_day_ganji_cycles_60():
    d0 = date(1990, 1, 1)
    assert day_ganji(d0) == day_ganji(d0 + timedelta(days=60))
    seen = {"".join(day_ganji(d0 + timedelta(days=i))) for i in range(60)}
    assert len(seen) == 60, "60갑자가 60가지 전부 나와야 합니다"


def test_jdn_monotonic():
    prev = None
    for i in range(0, 4000, 37):
        d = date(1900, 1, 1) + timedelta(days=i)
        n = jdn(d.year, d.month, d.day)
        if prev is not None:
            assert n > prev
        prev = n


# ══════════════════════════════════════════════════════════
# 2. 절기 — KASI 공표값 대조 (KST)
# ══════════════════════════════════════════════════════════
@pytest.mark.parametrize("year,expect", [
    (1985, "1985-02-04 06:12"),
    (2000, "2000-02-04 21:40"),
    (2024, "2024-02-04 17:27"),
    (2025, "2025-02-03 23:10"),
])
def test_ipchun_matches_kasi(year, expect):
    at = st.ipchun_utc(year) + KST
    # 초 단위 반올림
    at = (at + timedelta(seconds=30)).replace(second=0, microsecond=0)
    assert at.strftime("%Y-%m-%d %H:%M") == expect


def test_twelve_jie_per_year():
    for y in (1930, 1960, 1990, 2020, 2050):
        jies = st.jie_terms(y)
        assert len(jies) == 12, "節은 한 해에 12개여야 합니다"
        assert [i for i, _ in jies] == [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 1]
        # 입춘 → … → 소한 순으로 단조증가
        times = [t for _, t in jies]
        assert times == sorted(times)


def test_month_ji_sequence_over_a_year():
    """한 해를 훑으면 월지가 寅→丑 순으로 12개 전부 나온다."""
    seen = []
    d = datetime(2000, 2, 10)
    while d < datetime(2001, 2, 1):
        _, _, ji = st.current_jie(d)
        if not seen or seen[-1] != ji:
            seen.append(ji)
        d += timedelta(days=3)
    assert seen == list("寅卯辰巳午未申酉戌亥子丑")


def test_saju_year_flips_at_ipchun_not_jan1():
    at = st.ipchun_utc(2024)
    assert st.saju_year_of(at - timedelta(minutes=1)) == 2023
    assert st.saju_year_of(at) == 2024
    assert st.saju_year_of(datetime(2024, 1, 20)) == 2023


def test_out_of_range_refuses():
    with pytest.raises(st.SolarTermError):
        st.terms_of_saju_year(1800)


# ══════════════════════════════════════════════════════════
# 3. 표준시 · 서머타임 — 문서의 손표와 tzdata 교차검증
# ══════════════════════════════════════════════════════════
@pytest.mark.parametrize("y,m,d,deg", [
    (1910, 6, 1, 127.5), (1930, 6, 1, 135.0), (1953, 6, 1, 135.0),
    (1954, 3, 25, 127.5), (1958, 6, 1, 127.5), (1961, 6, 1, 127.5),
    (1962, 6, 1, 135.0), (1993, 6, 1, 135.0),
])
def test_std_meridian_matches_table(y, m, d, deg):
    _, _, got = tz.offsets(y, m, d, 12, 0)
    assert got == deg
    assert tz.table_std_meridian(y, m, d) == deg


def test_dst_ranges_match_table():
    """서머타임 12구간 — 손표와 tzdata 가 구간 한가운데서 일치해야 한다."""
    for (sy, sm, sd), (ey, em, ed) in tz.TABLE_DST_RANGES:
        mid = date(sy, sm, sd) + (date(ey, em, ed) - date(sy, sm, sd)) / 2
        _, dst, _ = tz.offsets(mid.year, mid.month, mid.day, 12, 0)
        assert dst == timedelta(hours=1), "%s 서머타임 누락" % mid
        assert tz.table_is_dst(mid.year, mid.month, mid.day)


def test_dst_start_hour_is_respected():
    """1987-05-10 은 02:00 시행. 그날 01:30 출생자는 서머타임이 아니다."""
    before = build_chart(1987, 5, 10, 1, 30, "M")
    after = build_chart(1987, 5, 10, 4, 30, "M")
    assert before.correction.dst is False
    assert after.correction.dst is True


def test_dst_rolls_back_one_hour():
    c = build_chart(1958, 7, 1, 12, 0, "M", longitude=127.5)
    assert c.correction.dst is True
    assert c.correction.after == "11:00"


# ══════════════════════════════════════════════════════════
# 4. 진태양시 · 날짜 넘김
# ══════════════════════════════════════════════════════════
def test_true_solar_time_seoul():
    c = build_chart(1993, 5, 15, 10, 20, "F", city="서울")
    assert c.correction.lon_min == -32.1
    assert c.correction.after == "09:48"


def test_backward_day_shift_lands_in_early_zi():
    """
    00:10 서울 출생 → 진태양시로 보정하면 전날 23:38, 날짜가 하루 밀린다.
    그런데 23시대는 조자시라 일주가 다시 익일로 돌아온다 → 결국 6/15.
    (야자시 정책이었다면 6/14 가 된다. 정책 차이가 드러나는 지점.)
    """
    c = build_chart(2000, 6, 15, 0, 10, "F", city="서울")
    assert c.correction.day_shift == -1
    assert c.correction.after == "23:38"
    assert c.hour_pillar.ji == "子"
    assert c.day_pillar.gz == "".join(day_ganji(date(2000, 6, 15)))


def test_jieqi_basis_shifts_the_boundary_by_the_longitude_correction():
    """
    절입 경계 정책이 드러나는 지점.

    JIEQI_BASIS="corrected" 이면 진태양시로 보정한 시각을 절입과 비교한다.
    서울은 -32.1분이므로, 공표 절입 시각 직후 32분 안에 태어난 사람은
    아직 전월(전년)로 잡힌다. 표준시로 비교하는 앱과 이 구간에서만 갈린다.

    정책을 바꾸려면 engine/calendar.py 의 JIEQI_BASIS 하나만 고치면 되고,
    바꾸는 순간 기존 사용자 결과가 달라진다는 것을 여기서 못박아 둔다.
    """
    from engine.calendar import JIEQI_BASIS

    at = st.ipchun_utc(2024) + KST                     # 2024-02-04 17:27 KST
    inside = at + timedelta(minutes=15)                # 절입 후 15분
    outside = at + timedelta(minutes=45)               # 절입 후 45분

    c_in = build_chart(inside.year, inside.month, inside.day,
                       inside.hour, inside.minute, "F", city="서울")
    c_out = build_chart(outside.year, outside.month, outside.day,
                        outside.hour, outside.minute, "F", city="서울")

    assert c_out.year_pillar.gz == "甲辰"
    if JIEQI_BASIS == "corrected":
        assert c_in.year_pillar.gz == "癸卯"
    else:
        assert c_in.year_pillar.gz == "甲辰"


# ══════════════════════════════════════════════════════════
# 5. 자시 정책 (조자시)
# ══════════════════════════════════════════════════════════
def test_zi_policy_is_early():
    assert ZI_POLICY == "조자시"


def test_early_zi_rolls_day_forward():
    """경도보정이 0인 조건(동경 135°)에서 23:30 → 일주는 익일."""
    c = build_chart(2000, 6, 15, 23, 30, "F", longitude=135.0)
    assert c.correction.day_shift == 0
    assert c.hour_pillar.ji == "子"
    assert c.day_pillar.gz == "".join(day_ganji(date(2000, 6, 16)))


def test_zi_hour_stem_follows_rolled_day():
    c = build_chart(2000, 6, 15, 23, 30, "F", longitude=135.0)
    assert c.hour_pillar.gan == OSEO[c.day_gan]


# ══════════════════════════════════════════════════════════
# 6. 오호둔 · 오서둔
# ══════════════════════════════════════════════════════════
def test_oho_dun_holds_for_every_chart():
    d = datetime(1970, 1, 1)
    for i in range(0, 3000, 17):
        dd = d + timedelta(days=i)
        c = build_chart(dd.year, dd.month, dd.day, 10, 0, "M")
        off = (JI.index(c.month_pillar.ji) - JI.index("寅")) % 12
        assert c.month_pillar.gan == GAN[(GAN.index(OHO[c.year_pillar.gan]) + off) % 10]


def test_oseo_dun_holds_for_every_chart():
    d = datetime(1970, 1, 1)
    for i in range(0, 3000, 23):
        dd = d + timedelta(days=i)
        c = build_chart(dd.year, dd.month, dd.day, 14, 0, "F")
        hi = JI.index(c.hour_pillar.ji)
        assert c.hour_pillar.gan == GAN[(GAN.index(OSEO[c.day_gan]) + hi) % 10]


# ══════════════════════════════════════════════════════════
# 7. 시각 미상 — 시주를 지어내지 않는다
# ══════════════════════════════════════════════════════════
def test_hour_unknown_returns_three_pillars():
    c = build_chart(1986, 6, 21, None, None, "F", hour_known=False)
    assert len(c.pillars) == 3
    assert c.hour_pillar is None
    assert c.correction.hour_used is False
    assert pillars_text(c).endswith("◇◇")


def test_hour_unknown_excludes_hour_from_features():
    known = build_features(build_chart(1986, 6, 21, 14, 0, "F"))
    unknown = build_features(
        build_chart(1986, 6, 21, None, None, "F", hour_known=False))
    assert len(unknown.pillars) == 3
    # 4주 7개 / 3주 5개
    assert sum(known.ten_gods.values()) == 7
    assert sum(unknown.ten_gods.values()) == 5
    assert sum(unknown.elements.values()) < sum(known.elements.values())


def test_hour_unknown_warns_on_boundary():
    c = build_chart(1986, 6, 21, None, None, "F", hour_known=False)
    assert c.correction.boundary_note
    assert "자시" in c.correction.boundary_note


# ══════════════════════════════════════════════════════════
# 8. 대운
# ══════════════════════════════════════════════════════════
@pytest.mark.parametrize("year,sex,forward", [
    (1984, "M", True),    # 갑자년(양) 남 → 순행
    (1984, "F", False),   # 양년 여 → 역행
    (1985, "M", False),   # 을축년(음) 남 → 역행
    (1985, "F", True),    # 음년 여 → 순행
])
def test_daeun_direction(year, sex, forward):
    c = build_chart(year, 6, 15, 10, 0, sex)
    assert c.forward is forward


def test_daeun_start_age_within_range():
    """대운수는 1~10. 근사식 (day%3)+3 이면 3~5 밖으로 못 나간다."""
    seen = set()
    d = datetime(1970, 1, 1)
    for i in range(0, 3000, 11):
        dd = d + timedelta(days=i)
        c = build_chart(dd.year, dd.month, dd.day, 10, 0, "M")
        seen.add(c.daeun[0].start_age)
        assert 1 <= c.daeun[0].start_age <= 10
    assert len(seen) >= 8, "대운수가 %s 뿐 — 근사식을 쓰고 있지 않은지 보세요" % sorted(seen)


def test_daeun_sequence_steps_by_ten():
    c = build_chart(1993, 5, 15, 10, 20, "F")
    ages = [d.start_age for d in c.daeun]
    assert ages == [ages[0] + 10 * i for i in range(len(ages))]


def test_daeun_gz_walks_the_sixty_cycle():
    c = build_chart(1993, 5, 15, 10, 20, "F")
    step = 1 if c.forward else -1
    prev = (GAN.index(c.month_pillar.gan), JI.index(c.month_pillar.ji))
    for d in c.daeun:
        prev = ((prev[0] + step) % 10, (prev[1] + step) % 12)
        assert d.gz == GAN[prev[0]] + JI[prev[1]]


# ══════════════════════════════════════════════════════════
# 9. 회귀 — tests/fixtures/charts.json
# ══════════════════════════════════════════════════════════
def _load_fixtures():
    if not FIXTURES.exists():
        return []
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


FIXTURE_CASES = _load_fixtures()


@pytest.mark.skipif(not FIXTURE_CASES, reason="charts.json 없음 — make_fixtures 먼저")
@pytest.mark.parametrize("case", FIXTURE_CASES,
                         ids=[c["id"] for c in FIXTURE_CASES])
def test_fixture_chart(case):
    exp = case["expected"]
    pending = [k for k, v in exp.items() if v == "?"]
    if pending:
        pytest.skip("기대값 미입력 (%s) — 기존 만세력 앱 2종과 대조해 채우세요"
                    % ", ".join(pending))

    i = case["input"]
    c = build_chart(i["year"], i["month"], i["day"], i["hour"], i["minute"],
                    i["sex"], hour_known=i.get("hour_known", True),
                    city=i.get("city", "서울"))
    got = {
        "year": c.year_pillar.gz,
        "month": c.month_pillar.gz,
        "day": c.day_pillar.gz,
        "hour": c.hour_pillar.gz if c.hour_pillar else None,
    }
    for key in ("year", "month", "day", "hour"):
        if exp.get(key) in (None, "-"):
            continue
        assert got[key] == exp[key], "%s %s: %s 기대 %s / 산출 %s" % (
            case["id"], case["note"], key, exp[key], got[key])

    if exp.get("daeun_start_age") is not None:
        # docs/05 §9-1 통과 기준: 대운 시작 나이 ±1세
        assert abs(c.daeun[0].start_age - exp["daeun_start_age"]) <= 1, (
            "%s 대운수: 기대 %s / 산출 %s"
            % (case["id"], exp["daeun_start_age"], c.daeun[0].start_age))


def test_fixture_file_has_fifty_cases():
    assert len(FIXTURE_CASES) == 50, (
        "고정 케이스가 50건이어야 합니다 (현재 %d건)" % len(FIXTURE_CASES))
