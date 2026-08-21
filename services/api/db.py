"""
DB 연결.

    DATABASE_URL=postgresql+psycopg2://sajudang:sajudang@localhost:5432/sajudang
    DATABASE_URL=sqlite:////data/app.sqlite          ← 한 대짜리 배포

★ 왜 SQLite 도 받는가
  Postgres 가 붙기 전까지 statement_log 가 DB 에 안 쌓이면
    · 공감률이 영영 안 뜨고 (100건이 안 모입니다)
    · 회고 루프가 안 돕니다 (6개월 전 문장을 못 꺼냅니다)
    · 마이그레이션이 영영 미검증으로 남습니다
  한 대에서는 SQLite 로 돌리다가 Postgres 로 갈아탑니다.
  models.py 가 방언 중립이라 스키마는 같습니다.

★ SQLite 로 여러 워커를 띄우지 마세요. 쓰기가 직렬화되어 잠깁니다.
  Dockerfile 이 --workers 1 로 고정해 둔 이유입니다.
"""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

log = logging.getLogger("db")

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

engine = None
SessionLocal = None
DIALECT = None


def _make(url: str):
    if url.startswith("sqlite"):
        # check_same_thread=False — uvicorn 이 스레드풀에서 부릅니다.
        eng = create_engine(
            url, future=True,
            connect_args={"check_same_thread": False, "timeout": 15},
        )

        @event.listens_for(eng, "connect")
        def _pragma(dbapi_conn, _rec):        # noqa: ANN001
            cur = dbapi_conn.cursor()
            # WAL — 읽기가 쓰기를 막지 않습니다. 한 대짜리에선 이게 큽니다.
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA synchronous=NORMAL")
            cur.execute("PRAGMA busy_timeout=15000")
            # ★ SQLite 는 외래키를 기본으로 끕니다. 켜 두지 않으면
            #   Postgres 에서 걸릴 오류가 여기서만 조용히 통과합니다.
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

        return eng
    return create_engine(url, pool_pre_ping=True, future=True)


if DATABASE_URL:
    try:
        engine = _make(DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine, expire_on_commit=False,
                                    class_=Session, future=True)
        DIALECT = engine.dialect.name
        log.info("db: %s (%s)", DATABASE_URL.split("@")[-1], DIALECT)
    except Exception as e:                     # noqa: BLE001
        log.warning("db: 연결 설정 실패 (%s) — 파일 폴백", e)
        engine = None
        SessionLocal = None
        DIALECT = None

HAS_DB = engine is not None


def info() -> dict:
    """/health 가 보여 줄 것. 접속 문자열은 절대 넣지 않습니다."""
    return {"enabled": HAS_DB, "dialect": DIALECT}


@contextmanager
def session():
    if not HAS_DB:
        raise RuntimeError("DATABASE_URL 이 없습니다")
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
