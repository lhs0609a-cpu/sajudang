"""
두드리는 횟수 — 값이 걸린 자리를 무차별 대입에서 지킵니다 (§21).

★ 왜 필요한가

  이 집에는 **손님 계정이 없습니다.** 그래서 자격을 되찾는 길이
  주문번호 하나입니다(`/v1/pay/restore`). 그 자리는 계정으로 치면
  「아이디·비밀번호 없이 영수증 번호만으로 로그인」 입니다.

  주문번호는 80비트(uuid4 앞 20자)라 찍어서 맞히기는 어렵습니다.
  다만 어렵다는 것과 **막아 두었다는 것**은 다릅니다. 주인 문은
  진작 5분에 열 번으로 막고 있었는데(`adminauth._too_many`), 정작
  값이 걸린 손님 쪽 문은 아무나 몇 번이든 두드릴 수 있었습니다.

★ 세는 단위

  로그인이 없으니 「누구」 를 셀 수 없습니다. 대신 **무엇을 두드리는가**
  로 셉니다 — 되찾기는 세션 하나가 몇 번 시도했는가.
  세션은 손님이 바꿀 수 있지만, 바꾸면 이미 모아 둔 자격도 같이
  잃으므로 공짜가 아닙니다.

★ 개인정보를 안 씁니다

  IP 를 열쇠로 쓰지 않습니다. IP 는 개인정보이고, 이 집은 계측에도
  준식별자를 안 싣습니다 (CLAUDE.md). 해시한 세션만 씁니다.
"""
from __future__ import annotations

import hashlib

import store


class TooMany(Exception):
    """말투는 화면과 같게. 서버가 파이썬 원문으로 대답하지 않습니다."""


def _key(bucket: str, who: str) -> str:
    return "try:%s:%s" % (bucket, hashlib.sha256(who.encode()).hexdigest()[:16])


def hit(bucket: str, who: str, *, limit: int, window: int) -> int:
    """한 번 두드렸다고 적고, 지금까지 몇 번인지 돌려줍니다."""
    return store.incr(_key(bucket, who), ttl=window)


def check(bucket: str, who: str, *, limit: int, window: int,
          say: str = "너무 자주 두드리셨소. 잠시 뒤에 다시 해 보시오.") -> None:
    """
    넘었으면 막습니다.

    ★ 세고 나서 봅니다 — 막힌 뒤에도 계속 두드리면 계속 셉니다.
      그래야 두드리기를 멈출 때까지 창이 안 열립니다.
    """
    if hit(bucket, who, limit=limit, window=window) > limit:
        raise TooMany(say)
