"""
DB 연결. DATABASE_URL 이 없으면 DB 없이 동작합니다(파일 폴백).

    DATABASE_URL=postgresql+psycopg2://sajudang:sajudang@localhost:5432/sajudang
"""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

log = logging.getLogger("db")

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

engine = None
SessionLocal = None

if DATABASE_URL:
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
        SessionLocal = sessionmaker(bind=engine, expire_on_commit=False,
                                    class_=Session, future=True)
        log.info("db: %s", DATABASE_URL.split("@")[-1])
    except Exception as e:                     # noqa: BLE001
        log.warning("db: 연결 설정 실패 (%s) — 파일 폴백", e)
        engine = None

HAS_DB = engine is not None


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
