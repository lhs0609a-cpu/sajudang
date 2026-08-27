"""
사주당 API — FastAPI.

    uvicorn main:app --reload --port 8000

★ 문장 뱅크 원문·렌즈 프롬프트·릴레이 조건식은 절대 응답에 넣지 않습니다.
  렌더된 HTML 만 내려보냅니다. (docs/02 §7)

★ GuardMiddleware 는 끄지 마세요. (CLAUDE.md 절대 규칙 3)
"""
import asyncio
import contextlib
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
    chart, daily, events, feedback, hook, pay, relay, report, share,
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

# ── 청소기 ────────────────────────────────────────────────
#
# ★ 저장소는 스스로 줄지 않습니다.
#   store.sweep() 은 있었는데 **부르는 데가 한 곳도 없었습니다.**
#   TTL 이 붙은 것도 그 키를 다시 읽을 때만 지워지므로, 다시 오지 않는
#   사람의 훅 캐시·공유 링크가 영영 남습니다. 볼륨은 1GB 한 장이고
#   app.sqlite·계측 로그가 같은 자리를 씁니다.
SWEEP_EVERY_SEC = int(os.getenv("SWEEP_EVERY_SEC", "3600"))

log = logging.getLogger("main")


async def _sweeper() -> None:
    while True:
        try:
            await asyncio.sleep(SWEEP_EVERY_SEC)
            n = await asyncio.to_thread(store.sweep)
            if n:
                log.info("store 청소 — 지난 항목 %d개 지움", n)
        except asyncio.CancelledError:
            raise
        except Exception:                              # noqa: BLE001
            # 청소가 실패해도 서비스는 계속 돕니다. 조용히 넘기지는 않습니다.
            log.exception("store 청소 실패")


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI):
    task = asyncio.create_task(_sweeper())
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


app = FastAPI(title="사주당 API", version=ENGINE_VER, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GuardMiddleware)

for r in (chart, hook, report, relay, feedback, daily, pay, share, events):
    app.include_router(r.router)


@app.get("/health")
def health() -> dict:
    from engine import timezone_kr as tz
    import payments
    return {
        "ok": True,
        "engine_ver": ENGINE_VER,
        "tz_source": tz.TZ_SOURCE,
        "store": store.stats(),
        "db": db.info(),
        "payments": payments.ENABLED,
        # 켜지지 않았다면 왜인지. 키는 안 실립니다 — 까닭만 나갑니다.
        "payments_live": payments.LIVE,
        "payments_reason": payments.DISABLED_REASON,
        "cors_origins": CORS_ORIGINS,
    }
