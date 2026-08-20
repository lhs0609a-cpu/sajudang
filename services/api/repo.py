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
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import db

log = logging.getLogger("repo")

MIN_RESPONSES_TO_SHOW = 100     # ★ 이 값을 내리지 마세요

ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = Path(os.getenv("STATEMENT_LOG_PATH", ROOT / "var" / "statement_log.jsonl"))


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


def record_answer(statement_id: str, chart_id: str, answer: int,
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
        "answer": int(answer),
        "answered_at": datetime.now(timezone.utc).isoformat(),
        "shown_at": datetime.now(timezone.utc).isoformat(),
    }
    row.update(_snapshot(features))

    if db.HAS_DB:
        import models
        import uuid as _uuid
        with db.session() as s:
            # charts 행이 있으면 FK 로, 없으면 캐시 키로 남긴다.
            # 어느 쪽이든 '어떤 사주였는지' 를 잃지 않는다.
            row = s.query(models.Chart).filter(
                models.Chart.cache_key == chart_id).one_or_none()
            s.add(models.StatementLog(
                statement_id=statement_id,
                chart_id=row.id if row else None,
                chart_key=chart_id,
                user_id=_uuid.UUID(user_id) if user_id else None,
                lens_id=lens_id, concern=concern, stage=row["stage"],
                day_gan=row["day_gan"], strength=row["strength"],
                top_ten_god=row["top_ten_god"], weak_el=row["weak_el"],
                strong_el=row["strong_el"], flow=row["flow"], axis4=axis4,
                answer=int(answer), answered_at=datetime.now(timezone.utc)))
        return 1

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(row, ensure_ascii=False) + "\n")
    return 1


def agreement(statement_id: str) -> Optional[dict]:
    """
    공감률. 응답이 MIN_RESPONSES_TO_SHOW 미만이면 **None** 을 돌려준다.
    화면은 None 이면 아무것도 그리지 않는다.
    """
    hit = total = 0

    if db.HAS_DB:
        import models
        from sqlalchemy import func, select
        with db.session() as s:
            total = s.scalar(select(func.count()).select_from(models.StatementLog)
                             .where(models.StatementLog.statement_id == statement_id,
                                    models.StatementLog.answer.isnot(None))) or 0
            hit = s.scalar(select(func.count()).select_from(models.StatementLog)
                           .where(models.StatementLog.statement_id == statement_id,
                                  models.StatementLog.answer == 1)) or 0
    elif LOG_PATH.exists():
        with LOG_PATH.open(encoding="utf-8") as fp:
            for line in fp:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("statement_id") != statement_id:
                    continue
                if r.get("answer") is None:
                    continue
                total += 1
                hit += 1 if r["answer"] == 1 else 0

    if total < MIN_RESPONSES_TO_SHOW:
        return None
    return {"statement_id": statement_id, "hit": hit, "total": total,
            "rate": round(100.0 * hit / total, 1)}
