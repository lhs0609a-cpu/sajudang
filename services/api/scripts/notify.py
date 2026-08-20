"""
알림 스케줄러 — docs/01 §5 리텐션 5층 / docs/04 §9

    DATABASE_URL=... python -m scripts.notify [--dry]

하루 한 번 돌립니다. 사용자마다 그날 보낼 알림을 **하나만** 만듭니다.
이미 그날 예약이 있으면 건너뜁니다.

회고 루프는 statement_log 에서 6개월 전 answer=1 문장을 꺼내 씁니다.
쌓인 것이 없으면 회고를 만들지 않습니다. (지어내지 않습니다)
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import db          # noqa: E402
import models      # noqa: E402
from engine.retention import plan_for   # noqa: E402


def lookback_for(s, user_id) -> dict | None:
    """6개월 전에 '그렇다'고 한 문장 하나."""
    from sqlalchemy import func, select
    now = datetime.now(timezone.utc)
    row = s.execute(
        select(models.StatementLog)
        .where(models.StatementLog.user_id == user_id,
               models.StatementLog.answer == 1,
               models.StatementLog.shown_at <= now - timedelta(days=150),
               models.StatementLog.shown_at >= now - timedelta(days=215))
        .order_by(func.random())
        .limit(1)
    ).scalar_one_or_none()
    if row is None:
        return None
    return {"statement_id": row.statement_id,
            "shown_at": row.shown_at.isoformat() if row.shown_at else None}


def main() -> int:
    dry = "--dry" in sys.argv
    if not db.HAS_DB:
        print("DATABASE_URL 이 없습니다.")
        return 1

    from sqlalchemy import select
    today = date.today()
    made = skipped = 0

    with db.session() as s:
        charts = s.execute(
            select(models.Chart).where(models.Chart.user_id.isnot(None))
        ).scalars().all()

        for ch in charts:
            # 하루 1건 — 이미 그날 예약이 있으면 건너뛴다
            exists = s.execute(
                select(models.Notification.id)
                .where(models.Notification.user_id == ch.user_id,
                       models.Notification.send_at >= datetime.combine(
                           today, datetime.min.time()),
                       models.Notification.send_at < datetime.combine(
                           today + timedelta(days=1), datetime.min.time()))
                .limit(1)
            ).first()
            if exists:
                skipped += 1
                continue

            birth = date(ch.birth_year, ch.birth_month, ch.birth_day)
            plan = plan_for(ch.features, birth, today,
                            lookback_statement=lookback_for(s, ch.user_id))
            if not plan:
                continue

            print("%s  %-9s %s" % (ch.user_id, plan["kind"],
                                   plan["payload"].get("text", "")))
            if not dry:
                s.add(models.Notification(
                    user_id=ch.user_id, kind=plan["kind"],
                    payload=plan["payload"], send_at=plan["send_at"]))
            made += 1

    print("예약 %d건 · 이미 있어 건너뜀 %d건%s"
          % (made, skipped, " (dry-run)" if dry else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
