"""
회귀 테스트 고정 케이스 50건 생성 — tests/fixtures/charts.json

expected 는 "?" 로 비워 둡니다. **기존 만세력 앱 2종 이상**과 대조해
직접 채우세요. 채우기 전까지 그 케이스는 skip 됩니다.

    python tools/make_fixtures.py          # 없으면 생성 (있으면 거부)
    python tools/make_fixtures.py --force  # 덮어쓰기 (채워 둔 기대값이 날아갑니다)

대조표는 tools/fixture_sheet.py 로 뽑으세요.
"""
from __future__ import annotations

import json
import sys
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import solar_terms as st          # noqa: E402
from engine.timezone_kr import TABLE_DST_RANGES  # noqa: E402

OUT = ROOT / "tests" / "fixtures" / "charts.json"

BLANK = {"year": "?", "month": "?", "day": "?", "hour": "?",
         "daeun_start_age": None}


def case(cid, note, y, m, d, hh, mi, sex, hour_known=True, city="서울"):
    return {
        "id": cid,
        "note": note,
        "input": {"year": y, "month": m, "day": d,
                  "hour": hh, "minute": mi, "sex": sex,
                  "hour_known": hour_known, "city": city},
        "expected": dict(BLANK),
    }


def build() -> list:
    cases = []

    # ── 1) 절입일 전후 ±2일 · 10건 ──────────────────────────
    # 실제 절입 시각을 sxtwl 로 뽑아, 그 앞뒤 이틀을 케이스로 만든다.
    picks = [(1988, 5), (1995, 9), (2001, 13), (2007, 17), (2015, 21)]
    n = 0
    for year, jq_index in picks:
        at = None
        for idx, t in st.jie_terms(year):
            if idx == jq_index:
                at = t + timedelta(hours=9)      # KST 표기
                break
        assert at is not None
        for delta in (-2, +2):
            d0 = at + timedelta(days=delta)
            n += 1
            cases.append(case(
                "jieqi-%02d" % n,
                "%s 절입(%s) %+d일" % (st.term_name(jq_index),
                                     at.strftime("%m-%d %H:%M"), delta),
                d0.year, d0.month, d0.day, at.hour, at.minute, "FM"[n % 2]))

    # ── 2) 2월 1~7일 · 10건 (입춘 경계) ─────────────────────
    # 실제 입춘 절입 시각의 앞뒤로 하나씩. 년주가 갈리는 지점을 반드시
    # 양쪽 다 덮는다. (전부 입춘 이전으로 몰리면 전환을 검증하지 못한다.)
    for i, year in enumerate([1990, 1996, 2000, 2012, 2020]):
        at = st.ipchun_utc(year) + timedelta(hours=9)      # KST
        for j, off in enumerate((-40, +40)):
            t = at + timedelta(minutes=off)
            n = i * 2 + j + 1
            cases.append(case(
                "ipchun-%02d" % n,
                "입춘(%s KST) %+d분 — 년주가 %s"
                % (at.strftime("%m-%d %H:%M"), off,
                   "%d년" % (year - 1) if off < 0 else "%d년" % year),
                t.year, t.month, t.day, t.hour, t.minute, "FM"[n % 2]))

    # ── 3) 자시 23~01시 · 10건 ─────────────────────────────
    zi = [(1985, 3, 12, 23, 5), (1990, 7, 20, 23, 40), (1995, 11, 3, 23, 59),
          (2000, 6, 15, 0, 10), (2003, 9, 9, 0, 45), (2008, 1, 25, 23, 20),
          (2011, 4, 18, 1, 0), (2014, 8, 30, 23, 50), (2018, 12, 7, 0, 30),
          (2021, 5, 22, 23, 15)]
    for i, (y, m, d, hh, mi) in enumerate(zi, 1):
        cases.append(case("zi-%02d" % i, "자시 경계 %02d:%02d" % (hh, mi),
                          y, m, d, hh, mi, "FM"[i % 2]))

    # ── 4) 1954~1961년생 · 5건 (표준시 127.5°) ──────────────
    std = [(1954, 4, 10, 9, 0, "서울"), (1956, 11, 2, 14, 30, "부산"),
           (1958, 3, 17, 6, 45, "대구"), (1960, 12, 24, 20, 15, "광주"),
           (1961, 7, 8, 11, 50, "서울")]
    for i, (y, m, d, hh, mi, city) in enumerate(std, 1):
        cases.append(case("std1275-%02d" % i, "표준시 127.5° 구간 · %s" % city,
                          y, m, d, hh, mi, "FM"[i % 2], city=city))

    # ── 5) 서머타임 12구간 각 1건 ──────────────────────────
    for i, (a, b) in enumerate(TABLE_DST_RANGES, 1):
        y, m, d = a
        # 시행 첫날은 시행 시각(02시) 문제가 있으므로 하루 뒤 정오로 잡는다
        from datetime import date as _date
        d1 = _date(y, m, d) + timedelta(days=1)
        cases.append(case("dst-%02d" % i,
                          "서머타임 %d년 구간 (%d.%d.%d~%d.%d.%d)"
                          % (y, a[0], a[1], a[2], b[0], b[1], b[2]),
                          d1.year, d1.month, d1.day, 12, 0, "FM"[i % 2]))

    # ── 6) 일반 · 3건 ─────────────────────────────────────
    cases.append(case("plain-01", "일반", 1993, 5, 15, 10, 20, "F"))
    cases.append(case("plain-02", "일반 · 남", 1978, 10, 3, 17, 45, "M"))
    cases.append(case("plain-03", "시각 미상", 1986, 6, 21, None, None, "F",
                      hour_known=False))

    return cases


def main() -> int:
    force = "--force" in sys.argv
    if OUT.exists() and not force:
        print("이미 있습니다: %s" % OUT)
        print("채워 둔 기대값을 지우려면 --force 를 주세요.")
        return 1
    cases = build()
    assert len(cases) == 50, "50건이어야 합니다 (현재 %d건)" % len(cases)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(cases, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("%d건 생성: %s" % (len(cases), OUT))
    print("기대값은 기존 만세력 앱 2종 이상과 대조해 직접 채우세요.")
    print("대조표: python tools/fixture_sheet.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
