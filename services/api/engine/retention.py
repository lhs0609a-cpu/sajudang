"""
리텐션 — docs/01 §5 "리텐션 5층" · docs/04 §9

    매일     일진 (원가 0)                365회/년
    매달     절입일 월운 갱신              12
    연 2회   입춘 세운 · 생일              2
    불규칙   분기점 예고 (대운 전환)       1~3
    반기     회고 루프                     2

★ 하루 1건 제한. 여러 트리거가 겹치면 **우선순위 높은 것 하나만** 보냅니다.
★ 회고 루프는 statement_log 에서 6개월 전 answer=1 문장을 꺼내 씁니다.
  쌓인 게 없으면 **보내지 않습니다.** 지어내지 않습니다.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from . import solar_terms as st
from .calendar import day_ganji
from .constants import GAN, JI

# 겹쳤을 때 무엇을 남길지. 숫자가 클수록 먼저.
PRIORITY = {
    "lookback": 90,     # 반기 회고 — 가장 강한 재방문 동기
    "turning": 85,      # 대운 전환
    "year": 80,         # 입춘 세운
    "birthday": 75,     # 생일
    "month": 60,        # 절입일 월운
    "new_lens": 50,     # 새 캐릭터 출시
    "daily": 10,        # 일진
}

KST_OFFSET = timedelta(hours=9)


def _kst(dt: datetime) -> datetime:
    return dt + KST_OFFSET


def jeolip_days(year: int) -> list[tuple[date, str]]:
    """그 해의 12절 절입일 (KST 날짜) — 월운 갱신 트리거."""
    out = []
    for idx, utc in st.jie_terms(year):
        out.append((_kst(utc).date(), st.term_name(idx)))
    return out


def is_jeolip(on: date) -> Optional[str]:
    for d, name in jeolip_days(on.year):
        if d == on:
            return name
    # 연초의 소한은 전년도 목록에 들어 있다
    for d, name in jeolip_days(on.year - 1):
        if d == on:
            return name
    return None


def is_ipchun(on: date) -> bool:
    return _kst(st.ipchun_utc(on.year)).date() == on


def daeun_turning_age(features: dict) -> Optional[int]:
    """다음 대운 전환 나이. 없으면 None."""
    age = features.get("age", 0)
    for d in features.get("daeun", []):
        if d["start_age"] > age:
            return d["start_age"]
    return None


def plan_for(features: dict, birth: date, on: Optional[date] = None,
             lookback_statement: Optional[dict] = None,
             new_lens: Optional[str] = None) -> Optional[dict]:
    """
    그날 보낼 알림 **하나**를 고른다. 없으면 None.

    lookback_statement : repo 에서 꺼낸 6개월 전 answer=1 문장. 없으면 회고는 건너뛴다.
    """
    on = on or date.today()
    candidates: list[dict] = []

    # ── 반기 회고 ──────────────────────────────────────────
    if lookback_statement:
        candidates.append({
            "kind": "lookback",
            "payload": {
                "statement_id": lookback_statement.get("statement_id"),
                "shown_at": lookback_statement.get("shown_at"),
                "text": "여섯 달 전 그대가 그렇다고 한 말이 있소. 지금도 그러시오?",
            },
        })

    # ── 대운 전환 ──────────────────────────────────────────
    turning = daeun_turning_age(features)
    if turning is not None and turning - features.get("age", 0) == 1:
        candidates.append({
            "kind": "turning",
            "payload": {"start_age": turning,
                        "text": "내년에 대운이 바뀌오. 십 년에 한 번 있는 자리요."},
        })

    # ── 입춘 세운 ──────────────────────────────────────────
    if is_ipchun(on):
        candidates.append({
            "kind": "year",
            "payload": {"text": "입춘이오. 올해의 간지가 오늘부터 바뀌오."},
        })

    # ── 생일 ──────────────────────────────────────────────
    if (on.month, on.day) == (birth.month, birth.day):
        candidates.append({
            "kind": "birthday",
            "payload": {"text": "오늘이 그 날이오. 한 해 치를 다시 보겠소?"},
        })

    # ── 절입일 월운 ────────────────────────────────────────
    jeolip = is_jeolip(on)
    if jeolip:
        candidates.append({
            "kind": "month",
            "payload": {"term": jeolip,
                        "text": "%s이오. 달의 기운이 오늘 바뀌오." % jeolip},
        })

    # ── 새 캐릭터 ─────────────────────────────────────────
    if new_lens:
        candidates.append({
            "kind": "new_lens",
            "payload": {"lens_id": new_lens, "text": "새 사람이 자리에 앉았소."},
        })

    # ── 일진 ──────────────────────────────────────────────
    gan, ji = day_ganji(on)
    candidates.append({
        "kind": "daily",
        "payload": {"gz": gan + ji, "text": "오늘은 %s일이오." % (gan + ji)},
    })

    if not candidates:
        return None

    # 하루 1건 — 우선순위 높은 것 하나만
    best = max(candidates, key=lambda c: PRIORITY[c["kind"]])
    return {
        "kind": best["kind"],
        "priority": PRIORITY[best["kind"]],
        "send_at": datetime.combine(on, datetime.min.time()) + timedelta(hours=9),
        "payload": best["payload"],
        "dropped": [c["kind"] for c in candidates if c is not best],
    }
