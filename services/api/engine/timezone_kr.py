"""
한국 표준시 변천 · 서머타임 — docs/05_계산엔진_사양서.md §1-1, §1-2

1차 소스는 IANA tzdata(`Asia/Seoul`)입니다. 문서의 손표(標)와 값이 같으면서
전환 '시각'까지 정확합니다. (1987-05-10 은 02:00 시행이라 그날 0~2시 출생자는
서머타임이 아닙니다. 손표로는 이 구분이 안 됩니다.)

문서의 표는 `TABLE_*` 로 남겨 두고 테스트에서 교차검증합니다.
tzdata 가 없는 환경에서는 표로 자동 폴백합니다.
"""
from __future__ import annotations

from datetime import datetime, timedelta

try:
    from zoneinfo import ZoneInfo
    _KST = ZoneInfo("Asia/Seoul")
except Exception:                                  # pragma: no cover
    _KST = None

TZ_SOURCE = "tzdata:Asia/Seoul" if _KST else "table"


# ── 문서 §1-1 손표 (교차검증용) ─────────────────────────────
def table_std_meridian(y: int, m: int, d: int) -> float:
    t = y * 10000 + m * 100 + d
    if t < 19120101:
        return 127.5      # 1908.4.1 ~ 1911.12.31
    if t < 19540321:
        return 135.0      # 1912.1.1  ~ 1954.3.20
    if t < 19610810:
        return 127.5      # 1954.3.21 ~ 1961.8.9
    return 135.0          # 1961.8.10 ~


# ── 문서 §1-2 서머타임 12구간 (교차검증용) ──────────────────
TABLE_DST_RANGES = [
    ((1948, 6, 1), (1948, 9, 12)), ((1949, 4, 3), (1949, 9, 10)),
    ((1950, 4, 1), (1950, 9, 9)), ((1951, 5, 6), (1951, 9, 8)),
    ((1955, 5, 5), (1955, 9, 8)), ((1956, 5, 20), (1956, 9, 29)),
    ((1957, 5, 5), (1957, 9, 21)), ((1958, 5, 4), (1958, 9, 20)),
    ((1959, 5, 3), (1959, 9, 19)), ((1960, 5, 1), (1960, 9, 17)),
    ((1987, 5, 10), (1987, 10, 11)), ((1988, 5, 8), (1988, 10, 9)),
]


def table_is_dst(y: int, m: int, d: int) -> bool:
    t = (y, m, d)
    return any(a <= t <= b for a, b in TABLE_DST_RANGES)


def std_label(y: int, m: int, d: int) -> str:
    """화면에 그대로 노출하는 표준시 구간 이름. docs/05 §10"""
    t = y * 10000 + m * 100 + d
    if t < 19080401:
        return "1908.4 이전 · 지방 평균시"
    if t < 19120101:
        return "1908~1911 · 동경 127.5°"
    if t < 19540321:
        return "1912~1954.3 · 동경 135°"
    if t < 19610810:
        return "1954.3~1961.8 · 동경 127.5°"
    return "1961.8~ · 동경 135°"


# ── 실제 산출 ──────────────────────────────────────────────
def offsets(y: int, m: int, d: int, hour: int, minute: int
            ) -> tuple[timedelta, timedelta, float]:
    """
    벽시계 시각(사용자가 말한 시각)을 받아
    (총 UTC 오프셋, 서머타임분, 표준자오선 도) 를 돌려준다.

    서머타임 해제일의 겹치는 1시간은 fold=0 — 즉 '서머타임 쪽'으로 해석한다.
    (해당 구간 출생자는 어차피 시각이 애매하므로 정책을 하나로 고정한다.)
    """
    if _KST is not None:
        dt = datetime(y, m, d, hour, minute, tzinfo=_KST)
        total = dt.utcoffset() or timedelta(0)
        dst = dt.dst() or timedelta(0)
        std = total - dst
        return total, dst, round(std.total_seconds() / 3600.0 * 15.0, 4)

    # 폴백 — 문서의 손표
    deg = table_std_meridian(y, m, d)
    dst = timedelta(hours=1) if table_is_dst(y, m, d) else timedelta(0)
    std = timedelta(hours=deg / 15.0)
    return std + dst, dst, deg
