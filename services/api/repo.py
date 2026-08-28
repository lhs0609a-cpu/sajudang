"""
statement_log 기록·집계 — docs/04 §6

DB 가 있으면 DB, 없으면 JSONL 파일에 append 합니다.
어느 쪽이든 **응답 100건 미만이면 공감률을 돌려주지 않습니다.**
(실데이터 없이 공감률 숫자를 띄우면 거짓 광고입니다. CLAUDE.md 절대 규칙 2)
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import db

log = logging.getLogger("repo")

MIN_RESPONSES_TO_SHOW = 100     # ★ 이 값을 내리지 마세요

ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = Path(os.getenv("STATEMENT_LOG_PATH", ROOT / "var" / "statement_log.jsonl"))
REVIEW_PATH = Path(os.getenv("REVIEW_LOG_PATH", ROOT / "var" / "reviews.jsonl"))


def _snapshot(features: dict) -> dict:
    """그 문장이 나온 조건 스냅샷. 나중에 '어떤 사주에 잘 먹히나' 분석용."""
    return {
        "day_gan": features.get("day_gan"),
        "strength": features.get("strength"),
        "top_ten_god": features.get("top_ten_god"),
        "weak_el": features.get("weak_el"),
        "strong_el": features.get("strong_el"),
        "flow": features.get("flow"),
    }


def record_answer(statement_id: str, chart_id: str, answer: Optional[int],
                  features: dict, stage: Optional[str] = None,
                  lens_id: Optional[str] = None,
                  concern: Optional[str] = None,
                  axis4: Optional[str] = None,
                  user_id: Optional[str] = None) -> int:
    row = {
        "statement_id": statement_id,
        "chart_id": chart_id,
        "user_id": user_id,
        "lens_id": lens_id,
        "concern": concern,
        "stage": stage or statement_id.split(":")[0],
        "axis4": axis4,
        # ★ None = 「글쎄올시다」. **노출로만** 셉니다.
        #   이분법이 공감률을 오염시키고 있었습니다 — 애매한 사람이
        #   거짓 '그렇소' 를 눌렀습니다. 분모에서 뺍니다 (_counts).
        "answer": None if answer is None else int(answer),
        "answered_at": (None if answer is None
                        else datetime.now(timezone.utc).isoformat()),
        "shown_at": datetime.now(timezone.utc).isoformat(),
    }
    row.update(_snapshot(features))

    if db.HAS_DB:
        import models
        import uuid as _uuid
        with db.session() as s:
            # charts 행이 있으면 FK 로, 없으면 캐시 키로 남긴다.
            # 어느 쪽이든 '어떤 사주였는지' 를 잃지 않는다.
            #
            # ★ 이름을 chart 로 둡니다. 예전에는 여기서도 row 를 써서
            #   위에서 만든 dict 를 덮어썼고, 바로 아래 row["stage"] 가
            #   ORM 객체를 첨자로 읽어 터졌습니다. DB 를 붙이는 순간
            #   응답 기록이 전부 실패하는 자리였습니다.
            chart = s.query(models.Chart).filter(
                models.Chart.cache_key == chart_id).one_or_none()
            s.add(models.StatementLog(
                statement_id=statement_id,
                chart_id=chart.id if chart else None,
                chart_key=chart_id,
                user_id=_uuid.UUID(user_id) if user_id else None,
                lens_id=lens_id, concern=concern, stage=row["stage"],
                day_gan=row["day_gan"], strength=row["strength"],
                top_ten_god=row["top_ten_god"], weak_el=row["weak_el"],
                strong_el=row["strong_el"], flow=row["flow"], axis4=axis4,
                answer=None if answer is None else int(answer),
                shown_at=datetime.now(timezone.utc),
                answered_at=(None if answer is None
                             else datetime.now(timezone.utc))))
        return 1

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(row, ensure_ascii=False) + "\n")
    return 1


# ══════════════════════════════════════════════════════════
# 후기 — 받는 척만 하고 버리던 자리
# ══════════════════════════════════════════════════════════
#
# ★ 여기가 아예 없었습니다.
#   화면(c6)이 별점을 받고 후기 칸을 그렸는데, 별점은 화면 상태만
#   바꾸고 후기 칸에는 value 도 onChange 도 없었습니다. 손님이 친
#   글자는 **버튼을 누르는 순간 사라졌습니다.**
#
#   바로 아래에는 "결제하고 끝까지 읽은 분의 후기에만 '결제 확인됨'
#   표시가 붙습니다" 라고 적혀 있었습니다. 붙일 후기가 한 건도 저장되지
#   않았습니다.
#
# ★ 자유 입력이라 두 가지를 먼저 합니다.
#   ① 개인정보를 지웁니다 — 전화·이메일·긴 숫자열. 손님이 무심코 적고,
#     우리는 그걸 보관할 이유가 없습니다.
#   ② 금지어 필터를 통과 못 하면 **안 보이게** 저장합니다. 지우지는
#     않습니다 — 손님이 실제로 한 말이라 우리 쪽에서는 읽어야 합니다.
#     다만 화면에는 절대 안 나갑니다.
REVIEW_MAX = 1000

_PII = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[메일]"),
    (re.compile(r"(?<!\d)01[016-9][-. ]?\d{3,4}[-. ]?\d{4}(?!\d)"), "[번호]"),
    (re.compile(r"(?<!\d)\d{6}[-]\d{7}(?!\d)"), "[주민번호]"),
    (re.compile(r"(?<!\d)\d{9,}(?!\d)"), "[숫자]"),
]


def scrub_pii(text: str) -> str:
    """후기에 섞여 들어온 연락처·식별번호를 지운다. 보관할 이유가 없다."""
    for pat, rep in _PII:
        text = pat.sub(rep, text)
    return text


def record_review(lens_id: str, rating: Optional[int], body: str,
                  verified: bool, chart_id: Optional[str] = None,
                  user_id: Optional[str] = None) -> dict:
    """
    후기 한 건. 돌려주는 것: {"stored": bool, "visible": bool}

    visible=False 는 금지어에 걸렸다는 뜻입니다. 저장은 하되 화면에는
    내보내지 않습니다.
    """
    from engine import guard

    body = scrub_pii((body or "").strip())[:REVIEW_MAX]
    ok, _hits = guard.check(body)
    visible = bool(ok)

    if db.HAS_DB:
        import models
        import uuid as _uuid
        with db.session() as s:
            s.add(models.Review(
                user_id=_uuid.UUID(user_id) if user_id else None,
                lens_id=lens_id,
                rating=int(rating) if rating else None,
                body=body or None,
                verified=bool(verified),
                visible=visible))
        return {"stored": True, "visible": visible}

    REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REVIEW_PATH.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps({
            "lens_id": lens_id,
            "chart_key": chart_id,
            "rating": int(rating) if rating else None,
            "body": body or None,
            "verified": bool(verified),
            "visible": visible,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }, ensure_ascii=False) + "\n")
    return {"stored": True, "visible": visible}


def review_stats(lens_id: Optional[str] = None) -> dict:
    """
    쌓인 후기 수와 평균. **표시는 아직 하지 않습니다** —
    공감률과 같은 규칙을 씁니다. 여기서는 세기만 합니다.
    """
    n = 0
    total = 0
    if db.HAS_DB:
        import models
        from sqlalchemy import func, select
        with db.session() as s:
            q = select(func.count(), func.coalesce(func.sum(models.Review.rating), 0)) \
                .select_from(models.Review) \
                .where(models.Review.rating.isnot(None))
            if lens_id:
                q = q.where(models.Review.lens_id == lens_id)
            n, total = s.execute(q).one()
    elif REVIEW_PATH.exists():
        with REVIEW_PATH.open(encoding="utf-8") as fp:
            for line in fp:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if lens_id and r.get("lens_id") != lens_id:
                    continue
                if r.get("rating") is None:
                    continue
                n += 1
                total += int(r["rating"])
    return {"count": int(n),
            "average": round(total / n, 2) if n else None}


# ══════════════════════════════════════════════════════════
# 공감률 — 점추정 대신 하한
# ══════════════════════════════════════════════════════════
#
# ★ 두 가지가 겹쳐 있습니다.
#
#   1. 작은 표본
#      52/100 과 520/1000 은 둘 다 52% 지만 확신의 크기가 다릅니다.
#      점추정을 그대로 띄우면 백 명에게 물어본 것과 천 명에게 물어본
#      것이 화면에서 같아 보입니다.
#
#      Wilson score 하한을 씁니다. 표본이 작으면 알아서 내려가고,
#      쌓이면 점추정에 붙습니다.
#
#          52/ 100  점추정 52.0%  →  하한 42.3%
#         520/1000  점추정 52.0%  →  하한 48.9%
#         100/ 100  점추정  100%  →  하한 96.3%   ← 100%라 단정하지 않습니다
#
#   2. 선택 편향
#      100건을 **가장 먼저** 넘는 문장은 가장 많이 겹치는 문장입니다.
#      그래서 노출 수(shown)와 노출 대비 응답률(answer_rate)을 함께
#      내려보냅니다. 무엇을 보고 있는지 알 수 있어야 합니다.
#
# ★ 하한이 낮은 문장을 감추는 방법도 있지만 쓰지 않습니다.
#   감추면 화면에 남는 숫자가 전부 높아 보입니다 — 그건 또 다른
#   거짓말입니다. **감추지 않고 낮게 말합니다.**

WILSON_Z = 1.96          # 95% 신뢰구간


def wilson_lower(hit: int, total: int, z: float = WILSON_Z) -> float:
    """Wilson score 하한 (0.0 ~ 1.0). total 이 0이면 0.0."""
    if total <= 0:
        return 0.0
    p = hit / total
    d = 1.0 + z * z / total
    centre = p + z * z / (2 * total)
    margin = z * ((p * (1 - p) / total + z * z / (4 * total * total)) ** 0.5)
    return max(0.0, (centre - margin) / d)


def _counts(statement_id: str) -> tuple[int, int, int]:
    """(그렇다, 응답, 노출). 노출은 답을 안 한 것까지 셉니다."""
    hit = total = shown = 0

    if db.HAS_DB:
        import models
        from sqlalchemy import func, select
        with db.session() as s:
            base = select(func.count()).select_from(models.StatementLog).where(
                models.StatementLog.statement_id == statement_id)
            shown = s.scalar(base) or 0
            total = s.scalar(base.where(
                models.StatementLog.answer.isnot(None))) or 0
            hit = s.scalar(base.where(models.StatementLog.answer == 1)) or 0
    elif LOG_PATH.exists():
        with LOG_PATH.open(encoding="utf-8") as fp:
            for line in fp:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("statement_id") != statement_id:
                    continue
                shown += 1
                if r.get("answer") is None:
                    continue
                total += 1
                hit += 1 if r["answer"] == 1 else 0
    return hit, total, shown


def exposure(statement_id: str) -> int:
    """
    이 문장이 **몇 번 나갔는가.** 공감률과 다릅니다 — 맞았는지가 아니라
    나갔는지를 셉니다.

    ★ 공감률이 100건 전까지 비어 있는 동안, 그 자리에 아무 신호도 없이
      결제 갈림길까지 갔습니다. 사회적 증거가 0인 채로 갑니다.
      숫자를 지어내지 않고 채울 수 있는 것이 이겁니다 — "이 문장을
      N명이 받아 갔소" 는 정확도 주장이 아니라 사실 진술입니다.
    """
    return _counts(statement_id)[2]


def agreement(statement_id: str) -> Optional[dict]:
    """
    공감률. 응답이 MIN_RESPONSES_TO_SHOW 미만이면 **None** 을 돌려준다.
    화면은 None 이면 아무것도 그리지 않는다.

    rate 는 **하한**입니다. point 는 참고용으로만 같이 내려보냅니다.
    """
    hit, total, shown = _counts(statement_id)

    if total < MIN_RESPONSES_TO_SHOW:
        return None
    return {
        "statement_id": statement_id,
        "hit": hit,
        "total": total,
        "shown": shown,
        "rate": round(100.0 * wilson_lower(hit, total), 1),
        "point": round(100.0 * hit / total, 1),
        "answer_rate": round(100.0 * total / shown, 1) if shown else None,
        "basis": "Wilson 하한 95%",
    }
