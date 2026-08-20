"""
캐시·카운터 — docs/02 §6

Redis 가 있으면 Redis, 없으면 프로세스 메모리로 돕니다. 어느 쪽이든
**브레이크 카운터는 반드시 동작**해야 하므로 인터페이스를 같게 두었습니다.

    REDIS_URL=redis://localhost:6379/0

메모리 폴백은 단일 프로세스에서만 맞습니다. 운영에서는 Redis 를 쓰세요.
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Optional

log = logging.getLogger("store")

REDIS_URL = os.getenv("REDIS_URL", "").strip()

_redis = None
if REDIS_URL:
    try:
        import redis as _redis_lib
        _redis = _redis_lib.from_url(REDIS_URL, decode_responses=True)
        _redis.ping()
        log.info("store: redis %s", REDIS_URL)
    except Exception as e:                     # noqa: BLE001
        log.warning("store: redis 연결 실패 (%s) — 메모리로 폴백", e)
        _redis = None

BACKEND = "redis" if _redis else "memory"

_mem: dict[str, tuple[Optional[float], Any]] = {}


def _expired(entry) -> bool:
    exp, _ = entry
    return exp is not None and exp < time.time()


def _mem_get(key: str):
    e = _mem.get(key)
    if e is None:
        return None
    if _expired(e):
        _mem.pop(key, None)
        return None
    return e[1]


def get_json(key: str):
    if _redis:
        raw = _redis.get(key)
        return json.loads(raw) if raw else None
    return _mem_get(key)


def set_json(key: str, value, ttl: Optional[int] = None) -> None:
    if _redis:
        raw = json.dumps(value, ensure_ascii=False)
        if ttl:
            _redis.setex(key, ttl, raw)
        else:
            _redis.set(key, raw)
        return
    _mem[key] = (time.time() + ttl if ttl else None, value)


def incr(key: str, ttl: Optional[int] = None) -> int:
    if _redis:
        n = _redis.incr(key)
        if ttl and n == 1:
            _redis.expire(key, ttl)
        return int(n)
    cur = _mem_get(key) or 0
    cur += 1
    exp = _mem.get(key, (None, None))[0]
    if exp is None and ttl:
        exp = time.time() + ttl
    _mem[key] = (exp, cur)
    return cur


def get_int(key: str) -> int:
    v = get_json(key) if not _redis else _redis.get(key)
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def exists(key: str) -> bool:
    if _redis:
        return bool(_redis.exists(key))
    return _mem_get(key) is not None


def clear_all() -> None:
    """테스트용. 운영 코드에서 부르지 마세요."""
    if _redis:
        _redis.flushdb()
    _mem.clear()


# ── 키 규약 ────────────────────────────────────────────────
DAY = 86400


def k_chart(chart_id: str) -> str:
    return "chart:%s" % chart_id


def k_hook(chart_id: str, concern: str, axis4: str, lens_id: str) -> str:
    return "hook:%s:%s:%s:%s" % (chart_id, concern, axis4 or "-", lens_id or "-")


def k_relay_session(session_id: str) -> str:
    return "relay:session:%s" % session_id


def k_purchase_day(user_key: str, day: str) -> str:
    return "purchase:%s:%s" % (user_key, day)


def k_reunion_cooldown(user_key: str) -> str:
    return "reunion:%s" % user_key


def k_visits(user_key: str, day: str) -> str:
    return "visit:%s:%s" % (user_key, day)
