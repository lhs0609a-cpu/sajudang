"""
성신당 API — FastAPI.

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

from fastapi import FastAPI, Request                 # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware   # noqa: E402
from fastapi.responses import JSONResponse           # noqa: E402
from starlette.exceptions import HTTPException as StarletteHTTPException  # noqa: E402

import db                                            # noqa: E402
import store                                         # noqa: E402
from guard_middleware import GuardMiddleware         # noqa: E402
from routers import (                                # noqa: E402
    chart, daily, events, feedback, hook, pay, relay, report, share,
    voice as voice_router, admin as admin_router,
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


app = FastAPI(title="성신당 API", version=ENGINE_VER, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GuardMiddleware)


# ══════════════════════════════════════════════════════════
# 거절할 때 — 우리 말로, 그리고 **받은 것을 되돌려 주지 않고**
# ══════════════════════════════════════════════════════════
#
# ★ 오류 응답에 생년월일이 통째로 실려 나가고 있었습니다.
#
#     {"detail":[{"type":"missing","loc":["body","sex"],
#                 "msg":"Field required",
#                 "input":{"year":1997,"month":3,"day":22,"hour":14,
#                          "minute":10,"birth_city":"서울"}}]}
#
#   필드 하나만 빠뜨려도 pydantic 이 **받은 본문을 그대로 되돌려 줍니다.**
#   생년월일시와 고을은 준식별자입니다. 계측에 안 싣기로 해 놓고
#   오류 응답으로 내보내고 있었습니다 — 로그·프록시·모니터링에 그대로
#   남습니다.
#
#   더 나쁜 자리가 하나 더 있습니다: `/v1/report` 는 extras 로 **상대
#   사주**(제3자의 생년월일)를 받습니다. 그게 틀리면 본인 동의도 없는
#   남의 생년월일이 오류 응답에 에코됐습니다.
#
#   그래서 `input` 과 `url` 을 뺍니다. **무엇이 빠졌는지만** 말합니다.
#
# ★ 그리고 우리 말로 거절합니다.
#   "Method Not Allowed" · "Not Found" 는 파이썬이 하는 말이지 이 집이
#   하는 말이 아닙니다. (CLAUDE.md — 서버가 파이썬 원문으로 대답하지 말 것)
_WHERE = {"body": "본문", "query": "주소", "path": "주소", "header": "머리"}


@app.exception_handler(RequestValidationError)
async def _bad_request(request: Request, exc: RequestValidationError):
    missing = []
    for e in exc.errors():
        loc = [str(x) for x in e.get("loc", []) if x not in ("body",)]
        where = _WHERE.get(str(e.get("loc", ["body"])[0]), "본문")
        missing.append("%s의 %s" % (where, ".".join(loc) or "값"))
    said = ("%s 이(가) 잘못됐거나 빠졌소." % " · ".join(dict.fromkeys(missing))
            if missing else "보내신 것을 읽지 못했소.")
    # ★ 받은 값은 안 돌려줍니다. 무엇이 빠졌는지만.
    return JSONResponse(status_code=422, content={"detail": said})


@app.exception_handler(StarletteHTTPException)
async def _http_error(request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if exc.status_code == 404 and detail in ("Not Found", None):
        detail = "그런 자리는 없소."
    elif exc.status_code == 405 and detail in ("Method Not Allowed", None):
        detail = "그 방법으로는 안 받소. 이 자리는 POST 로만 받소."
    elif exc.status_code == 500:
        detail = "안에서 무언가 어긋났소. 값은 빠져나가지 않았소."
    return JSONResponse(status_code=exc.status_code,
                        content={"detail": detail},
                        headers=getattr(exc, "headers", None))

for r in (chart, hook, report, relay, feedback, daily, pay, share, events,
          voice_router, admin_router):
    app.include_router(r.router)


def _voice_stats() -> dict:
    """
    소리가 켜졌는가, 곳간에 몇 마디가 쌓였는가.

    ★ 곳간 수를 보는 이유 — 값이 트래픽이 아니라 **서로 다른 말의 수**에
      묶이는 구조라, 이 숫자가 곧 지금까지 든 값입니다.
    """
    import voice
    try:
        n = len(list(voice.CACHE.glob("*.mp3"))) if voice.CACHE.is_dir() else 0
    except Exception:                                # noqa: BLE001
        n = 0
    return {"enabled": voice.enabled(), "cached": n,
            "dir": str(voice.CACHE)}


def _rarity_stats() -> dict:
    from engine import rarity as rr
    from routers import chart as chart_router
    out: dict = {"why": chart_router.rarity_why()}
    try:
        out["seed"] = str(rr.SEED)
        out["has_table"] = (rr.SEED / "rarity.json").exists()
        out["stale"] = rr.is_stale()
        # ★ 컨테이너에서 **직접 세어 봅니다.**
        #
        #   배포본에서 값이 안 나오는데 까닭도 안 남았습니다. 그러면
        #   「안 불린 것」인지 「불렸는데 실패한 것」인지 모릅니다.
        #   여기서 한 번 세어 보면 엔진 쪽인지 라우터 쪽인지 갈립니다.
        from engine.calendar import build_chart
        from engine.features import build_features
        f = build_features(build_chart(1993, 11, 25, 13, 0, "M", True))
        out["sample"] = rr.look(f).get("words")
    except Exception as e:                       # noqa: BLE001
        out["error"] = "%s: %s" % (type(e).__name__, e)
    return out


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
        # 소리 — 열쇠가 있어야 납니다. 없으면 화면이 조용히 넘어갑니다.
        "voice": _voice_stats(),
        # 희소도가 안 나오면 **왜인지**. 곁가지라 조용히 빠지는데,
        # 조용히 빠지면 배포본에서 원인을 못 찾습니다.
        "rarity": _rarity_stats(),
        "cors_origins": CORS_ORIGINS,
    }
