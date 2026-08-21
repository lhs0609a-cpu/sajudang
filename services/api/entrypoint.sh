#!/bin/sh
# 컨테이너가 뜰 때 하는 일.
#
#   ① DATABASE_URL 이 있으면 마이그레이션을 올린다
#   ② uvicorn 을 띄운다
#
# ★ 마이그레이션이 실패해도 서버는 뜹니다.
#   DB 가 없으면 statement_log 는 JSONL 로, 계측도 JSONL 로 갑니다.
#   여기서 죽으면 계산까지 통째로 멈춥니다 — 계산은 DB 가 없어도 됩니다.
#   대신 /health 의 db 가 false 로 남아 눈에 띕니다.
set -e

cd /app

if [ -n "$DATABASE_URL" ]; then
  echo "[entrypoint] alembic upgrade head"
  if python -m alembic upgrade head; then
    echo "[entrypoint] 마이그레이션 완료"
  else
    echo "[entrypoint] ★ 마이그레이션 실패 — DB 없이 계속합니다" >&2
    echo "[entrypoint]   /health 의 db 를 보세요." >&2
    unset DATABASE_URL
  fi
else
  echo "[entrypoint] DATABASE_URL 없음 — 파일 폴백으로 돕니다"
fi

cd /app/services/api
exec python -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-8080}" --workers 1
