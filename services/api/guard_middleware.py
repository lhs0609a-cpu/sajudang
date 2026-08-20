"""
금지어 필터 미들웨어 — 나가는 JSON 응답을 전부 훑는다.

문장은 이미 engine/bank.py 에서 guard.enforce 를 통과합니다.
이건 **안전망**입니다. 새 라우터를 붙이면서 enforce 를 빠뜨려도
여기서 걸립니다. 걸린 건 로그로 남겨 뱅크·프롬프트 개선에 씁니다.

★ 이 미들웨어는 설정으로 끌 수 없습니다. (docs/11 · CLAUDE.md 절대 규칙 3)
"""
from __future__ import annotations

import json
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from engine import guard

log = logging.getLogger("guard.middleware")


class GuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next) -> Response:
        response = await call_next(request)

        ctype = response.headers.get("content-type", "")
        if not ctype.startswith("application/json"):
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            payload = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            return Response(content=body, status_code=response.status_code,
                            headers=dict(response.headers),
                            media_type=response.media_type)

        hits = guard.scan(payload)
        if not hits:
            return Response(content=body, status_code=response.status_code,
                            headers=dict(response.headers),
                            media_type=response.media_type)

        log.error("guard: %s 위반 %d건 %s", request.url.path, len(hits), hits)
        cleaned = guard.enforce_deep(payload, {"path": str(request.url.path)})
        out = JSONResponse(content=cleaned, status_code=response.status_code)
        # content-length 가 바뀌므로 원본 헤더를 그대로 쓰면 안 된다
        for k, v in response.headers.items():
            if k.lower() not in ("content-length", "content-type"):
                out.headers[k] = v
        return out
