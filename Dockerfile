# 사주당 계산 API
#
# ★ Python 3.11 고정. sxtwl 은 3.12+ 휠이 없습니다.
#   3.11 에는 manylinux 휠이 있어 컴파일 없이 설치됩니다.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 의존성 먼저 — 소스가 바뀌어도 이 층은 캐시됩니다
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
 && python -c "import sxtwl, zoneinfo; zoneinfo.ZoneInfo('Asia/Seoul'); print('sxtwl + tzdata OK')"

# 런타임에 필요한 것만. 문서·프론트·참조구현체는 넣지 않습니다.
COPY seed/          ./seed/
COPY services/api/  ./services/api/

# 상태 파일 자리 (fly 볼륨이 여기 붙습니다)
RUN mkdir -p /data
ENV STORE_PATH=/data/store.sqlite \
    STATEMENT_LOG_PATH=/data/statement_log.jsonl

WORKDIR /app/services/api
EXPOSE 8080

# 단일 워커. 브레이크 카운터가 SQLite 로 원자적으로 도므로 여러 워커도
# 되지만, 한 대에서 시작합니다. 늘릴 때는 REDIS_URL 을 붙이세요.
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
