"""
주인 자리로 들어온 요청인가 — **요청 하나 동안만** 기억합니다.

★ 왜 필요한가

  주인은 파는 물건을 눈으로 봐야 합니다. 그런데 이 집의 유료 자리는
  **치른 주문**이 열고(`routers/report.entitled_tier`), 주인에게는
  치른 주문이 없습니다. 그래서 여태 주인이 자기 가게의 19,900원짜리
  글을 보려면 제 카드로 긁어야 했습니다 — PG 키도 없는 집에서요.

  주인 문은 이미 걸려 있습니다(`adminauth` · `keyguard`). 그 문으로
  들어온 요청이면 유료 자리를 **다 열어 줍니다.**

★ 클라이언트 말은 여전히 안 믿습니다

  화면이 `admin: true` 를 실어 보내는 꼴이면 그건 잠금이 아니라
  가림입니다 — 브라우저에서 한 글자만 고치면 스무 사람이 열립니다.
  여는 것은 **쪽지(`x-admin-token`)나 열쇠(`x-funnel-key`)가 서버에서
  맞았을 때**뿐이고, 견주는 자리는 주인 화면과 같은 한 곳입니다.

★ 왜 머리표를 자격 자리까지 들고 가지 않고 이 자리를 두는가

  자격을 보는 데가 한 곳이 아닙니다 — 리포트 본체 · 스무 사람 종합 ·
  보관함 다시 읽기 · 되짚기 · 운세 상품. 그 다섯에 머리표 인자를
  손으로 실어 보내면 한 군데 빼먹는 날이 오고, 그날 빠진 자리는
  아무도 모릅니다. 문지기가 한 번 보고 **요청 하나 동안** 적어 두면
  자격을 세는 자리는 그것만 봅니다.

★ 손님처럼 보기

  주인도 무료 구간이 어떻게 보이는지 봐야 합니다. 그때는 머리표에
  `x-admin-view: guest` 를 실으면 이 자리가 꺼집니다.

★ 브레이크는 안 풉니다

  세션당 릴레이 2명 · 하루 결제 2건 · 재회 7일 쿨다운은 값이 아니라
  **손님을 지키는 자리**라 주인에게도 그대로 돕니다
  (CLAUDE.md 절대 규칙 4). 이 자리가 푸는 것은 **값으로 잠긴 것**뿐입니다.
"""
from __future__ import annotations

import hmac
from contextvars import ContextVar, Token

from starlette.middleware.base import BaseHTTPMiddleware

#: 요청 하나 동안만 삽니다. 기본은 **꺼진 쪽**입니다 — 열린 쪽이
#: 기본이면 언젠가 그대로 배포됩니다 (keyguard 와 같은 결).
_ON: ContextVar[bool] = ContextVar("sajudang_admin_view", default=False)

#: 머리표 이름. 화면(`apps/web/lib/api.ts`)과 프록시
#: (`apps/web/app/api/backend/[...path]/route.ts`)가 같은 이름을 씁니다.
TOKEN_HEADER = "x-admin-token"
KEY_HEADER = "x-funnel-key"
GUEST_HEADER = "x-admin-view"


def check(token: str | None, key: str | None) -> bool:
    """
    주인인가. **거절하지 않고** 참·거짓만 냅니다.

    ★ `keyguard.require_admin` 은 아니면 401 을 던집니다. 이 자리는
      손님 요청에도 매번 불리므로 던지면 안 됩니다 — 쪽지가 없는 것은
      잘못이 아니라 그냥 손님입니다.

    ★ 시간을 안 흘립니다 — `hmac.compare_digest` (keyguard 와 같은 결).
    """
    import adminauth
    import keyguard

    if token and adminauth.session_of(token):
        return True
    want = getattr(keyguard, "FUNNEL_KEY", "")
    if key and want and hmac.compare_digest(key, want):
        return True
    return False


def on() -> bool:
    """이 요청이 주인 자리로 들어왔는가."""
    return _ON.get()


def set_on(value: bool) -> Token:
    return _ON.set(bool(value))


def reset(token: Token) -> None:
    _ON.reset(token)


class AdminViewMiddleware(BaseHTTPMiddleware):
    """
    문지기 — 머리표를 한 번 보고 적어 둡니다.

    ★ 여기서 아무것도 거절하지 않습니다. 잠그는 것은 `/v1/admin/*` 의
      몫이고, 이 자리는 **열 수 있는가**만 적습니다.
    """

    async def dispatch(self, request, call_next):
        guest = (request.headers.get(GUEST_HEADER) or "").strip().lower() == "guest"
        mark = set_on(not guest and check(request.headers.get(TOKEN_HEADER),
                                         request.headers.get(KEY_HEADER)))
        try:
            return await call_next(request)
        finally:
            reset(mark)
