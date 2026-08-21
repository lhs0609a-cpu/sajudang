"""
사주당 API — FastAPI.

    uvicorn main:app --reload --port 8000

★ 문장 뱅크 원문·렌즈 프롬프트·릴레이 조건식은 절대 응답에 넣지 않습니다.
  렌더된 HTML 만 내려보냅니다. (docs/02 §7)

★ GuardMiddleware 는 끄지 마세요. (CLAUDE.md 절대 규칙 3)
"""
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI                          # noqa: E402
from fastapi.middleware.cors import CORSMiddleware   # noqa: E402

import db                                            # noqa: E402
import store                                         # noqa: E402
from guard_middleware import GuardMiddleware         # noqa: E402
from routers import (                                # noqa: E402
    chart, daily, feedback, hook, pay, relay, report, share,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-5s [%(name)s] %(message)s")

ENGINE_VER = "0.2.0"     # ★ 만세력을 고치면 올리세요. charts.engine_ver 에 남습니다.

# 브라우저가 이 API 를 부를 수 있는 출처. 쉼표로 여러 개.
#   CORS_ORIGINS=https://sajudang-three.vercel.app,http://localhost:3000
# ★ 배포 도메인을 여기 넣지 않으면 브라우저가 요청을 막습니다.
#   서버는 200 을 주는데 화면만 조용히 비는 형태라 찾기 어렵습니다.
CORS_ORIGINS = [
    o.strip() for o in
    os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]

app = FastAPI(title="사주당 API", version=ENGINE_VER)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GuardMiddleware)

for r in (chart, hook, report, relay, feedback, daily, pay, share):
    app.include_router(r.router)


@app.get("/health")
def health() -> dict:
    from engine import timezone_kr as tz
    import payments
    return {
        "ok": True,
        "engine_ver": ENGINE_VER,
        "tz_source": tz.TZ_SOURCE,
        "store": store.BACKEND,
        "db": db.HAS_DB,
        "payments": payments.ENABLED,
        "cors_origins": CORS_ORIGINS,
    }
