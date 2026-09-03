"""
주인 자리의 자물쇠 — 아이디와 비밀번호.

★ 왜 열쇠 하나로는 모자란가

  여태 주인 화면은 `FUNNEL_KEY` 한 줄이었습니다. 그건 **사람이 아니라
  기계를 위한 열쇠**입니다 — `tools/funnel.py` 가 머리표에 실어 보내는
  값이지요. 사람이 쓰기에는 두 가지가 불편합니다:

    · 스물네 자짜리 난수를 외워서 칠 수 없습니다. 어딘가에 적어 두게
      되고, 적어 둔 것은 새어 나갑니다.
    · 바꾸려면 배포를 다시 해야 합니다.

  그래서 사람 문을 하나 더 냅니다 — 아이디와 비밀번호. 기계 문은
  그대로 둡니다(도구가 씁니다).

★ 비밀번호는 **저장하지 않습니다**

  저장소에도, 서버에도, 로그에도 평문은 없습니다. 남는 것은
  PBKDF2-HMAC-SHA256 해시 한 줄뿐이고, 그것도 환경변수로 받습니다.

      ADMIN_EMAIL          lhs0609c@naver.com
      ADMIN_PASSWORD_HASH  pbkdf2_sha256$210000$<소금>$<해시>

  해시는 `.\dev.ps1 admin-pass` 로 만듭니다. 파이썬 표준 라이브러리만
  씁니다 — 새 의존성을 안 답니다.

★ 시간을 안 흘립니다

  견줄 때는 `hmac.compare_digest` 입니다. `==` 는 앞자리부터 틀리는
  데까지 걸리는 시간이 달라서, 그 차이로 한 자 한 자 알아낼 수
  있습니다 (keyguard 와 같은 결).

★ 문을 두드리는 횟수를 셉니다

  비밀번호가 짧거나 뻔하면 자물쇠보다 **두드리는 속도**가 먼저
  뚫립니다. 한 자리에서 5분에 열 번까지만 받습니다.

★ 들어오면 쪽지를 하나 줍니다

  로그인이 맞으면 임의의 토큰을 만들어 곳간에 두고, 그걸 머리표
  (`x-admin-token`)로 받습니다. 비밀번호는 로그인 한 번에만 오가고,
  그 뒤로는 안 오갑니다. 쪽지는 하루가 지나면 삭습니다.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time
from typing import Optional

import store

# ── 설정 ──────────────────────────────────────────────────
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "").strip()
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "").strip()

ALGO = "pbkdf2_sha256"
ROUNDS = 210_000          # OWASP 2023 권고선
SESSION_TTL = 86_400      # 쪽지는 하루
TRY_WINDOW = 300          # 5분
TRY_MAX = 10              # 그 안에 열 번까지


class AuthError(Exception):
    """말투는 화면과 같게. 서버가 파이썬 원문으로 대답하지 않습니다."""


# ── 해시 ──────────────────────────────────────────────────
def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def make_hash(password: str, *, rounds: int = ROUNDS,
              salt: Optional[bytes] = None) -> str:
    """
    비밀번호 → 저장해도 되는 한 줄.

    소금은 열여섯 바이트씩 새로 뽑습니다. 같은 비밀번호라도 해시가
    매번 달라야, 새어 나간 해시 표로 되짚지 못합니다.
    """
    if not password:
        raise AuthError("비밀번호가 비었소.")
    salt = salt or secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
    return "%s$%d$%s$%s" % (ALGO, rounds, _b64(salt), _b64(dk))


def verify_hash(password: str, stored: str) -> bool:
    """맞는가. 꼴이 깨져 있으면 **틀린 것으로** 봅니다 — 열지 않습니다."""
    try:
        algo, rounds, salt_b64, want = stored.split("$", 3)
        if algo != ALGO:
            return False
        salt = base64.b64decode(salt_b64)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                                 salt, int(rounds))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(_b64(dk), want)


# ── 문을 두드린 횟수 ──────────────────────────────────────
def _throttle_key(who: str) -> str:
    """
    ★ 아이디로 셉니다. 주소(IP)로 세면 회선 하나 뒤의 여러 사람이
      서로를 막고, 주소를 바꾸는 쪽은 못 막습니다. 이 집의 주인은
      한 사람이라 아이디로 세는 편이 맞습니다.
    """
    return "adminfail:%s:%d" % (who[:64], int(time.time()) // TRY_WINDOW)


def _too_many(who: str) -> bool:
    return int(store.get_json(_throttle_key(who)) or 0) >= TRY_MAX


def _note_fail(who: str) -> None:
    store.incr(_throttle_key(who), ttl=TRY_WINDOW)


# ── 로그인 ────────────────────────────────────────────────
def configured() -> bool:
    """주인 문이 걸려 있는가."""
    return bool(ADMIN_EMAIL and ADMIN_PASSWORD_HASH)


def login(email: str, password: str) -> str:
    """
    맞으면 쪽지(토큰)를 돌려줍니다. 틀리면 **무엇이 틀렸는지 안 알려
    줍니다** — 아이디가 있는지 없는지를 흘리면 그것부터 캐냅니다.
    """
    if not configured():
        raise AuthError("주인 문이 아직 안 걸렸소. ADMIN_EMAIL 과 "
                        "ADMIN_PASSWORD_HASH 를 세우시오.")

    who = (email or "").strip().lower()
    if _too_many(who):
        raise AuthError("여러 번 어긋났소. 5분 뒤에 다시 오시오.")

    # 아이디가 틀려도 해시를 한 번 돌립니다. 안 그러면 아이디가
    # 맞았는지 아닌지가 **걸린 시간**으로 새어 나갑니다.
    ok_id = hmac.compare_digest(who, ADMIN_EMAIL.lower())
    ok_pw = verify_hash(password or "", ADMIN_PASSWORD_HASH)
    if not (ok_id and ok_pw):
        _note_fail(who)
        raise AuthError("아이디나 비밀번호가 맞지 않소.")

    token = secrets.token_urlsafe(32)
    store.set_json("admintok:" + token,
                   {"email": ADMIN_EMAIL, "at": time.time()},
                   ttl=SESSION_TTL)
    return token


def logout(token: str | None) -> None:
    if token:
        store.delete("admintok:" + token)


def session_of(token: str | None) -> Optional[dict]:
    """쪽지가 살아 있는가."""
    if not token:
        return None
    got = store.get_json("admintok:" + token)
    return got if isinstance(got, dict) else None
