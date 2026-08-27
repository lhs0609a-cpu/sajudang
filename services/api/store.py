"""
캐시·카운터 — docs/02 §6

세 가지 백엔드를 같은 인터페이스로 씁니다. 위에서부터 먼저 잡히는 것을 씁니다.

    1. Redis     REDIS_URL 이 있으면. 여러 대로 늘릴 때.
    2. SQLite    STORE_PATH 가 있으면. 한 대짜리 배포의 기본.
    3. 메모리    아무것도 없으면. 개발·테스트용.

★ 왜 메모리로 배포하면 안 되는가
    · 공유 링크(90일)가 재시작마다 사라집니다.
    · **브레이크가 풀립니다.** 하루 결제 2건·세션 릴레이 2명 카운터가
      초기화되면 제한이 없는 것과 같습니다. (CLAUDE.md 절대 규칙 4)
  그래서 배포에서는 STORE_PATH 나 REDIS_URL 중 하나가 반드시 있어야 합니다.
  `/health` 의 `store` 값으로 확인하세요.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import threading
import time
from typing import Any, Optional

log = logging.getLogger("store")

REDIS_URL = os.getenv("REDIS_URL", "").strip()
STORE_PATH = os.getenv("STORE_PATH", "").strip()

_redis = None
if REDIS_URL:
    try:
        import redis as _redis_lib
        _redis = _redis_lib.from_url(REDIS_URL, decode_responses=True)
        _redis.ping()
        log.info("store: redis")
    except Exception as e:                     # noqa: BLE001
        log.warning("store: redis 연결 실패 (%s)", e)
        _redis = None

# ── SQLite ────────────────────────────────────────────────
_db: Optional[sqlite3.Connection] = None
_lock = threading.Lock()

if _redis is None and STORE_PATH:
    try:
        os.makedirs(os.path.dirname(STORE_PATH) or ".", exist_ok=True)
        _db = sqlite3.connect(STORE_PATH, check_same_thread=False)
        _db.execute("PRAGMA journal_mode=WAL")
        _db.execute("PRAGMA synchronous=NORMAL")
        _db.execute(
            "CREATE TABLE IF NOT EXISTS kv ("
            " k TEXT PRIMARY KEY, v TEXT NOT NULL, exp REAL)")
        _db.execute("CREATE INDEX IF NOT EXISTS kv_exp ON kv(exp)")
        _db.commit()
        log.info("store: sqlite %s", STORE_PATH)
    except Exception as e:                     # noqa: BLE001
        log.warning("store: sqlite 열기 실패 (%s)", e)
        _db = None

BACKEND = "redis" if _redis else ("sqlite" if _db else "memory")

_mem: dict[str, tuple[Optional[float], Any]] = {}


def _now() -> float:
    return time.time()


# ── 메모리 ────────────────────────────────────────────────
def _mem_get(key: str):
    e = _mem.get(key)
    if e is None:
        return None
    exp, val = e
    if exp is not None and exp < _now():
        _mem.pop(key, None)
        return None
    return val


# ── 공통 API ──────────────────────────────────────────────
def get_json(key: str):
    if _redis:
        raw = _redis.get(key)
        return json.loads(raw) if raw else None
    if _db:
        with _lock:
            row = _db.execute(
                "SELECT v, exp FROM kv WHERE k=?", (key,)).fetchone()
        if row is None:
            return None
        v, exp = row
        if exp is not None and exp < _now():
            delete(key)
            return None
        return json.loads(v)
    return _mem_get(key)


def set_json(key: str, value, ttl: Optional[int] = None) -> None:
    if _redis:
        raw = json.dumps(value, ensure_ascii=False)
        if ttl:
            _redis.setex(key, ttl, raw)
        else:
            _redis.set(key, raw)
        return
    if _db:
        exp = _now() + ttl if ttl else None
        with _lock:
            _db.execute(
                "INSERT INTO kv(k, v, exp) VALUES(?,?,?) "
                "ON CONFLICT(k) DO UPDATE SET v=excluded.v, exp=excluded.exp",
                (key, json.dumps(value, ensure_ascii=False), exp))
            _db.commit()
        return
    _mem[key] = (_now() + ttl if ttl else None, value)


def delete(key: str) -> None:
    if _redis:
        _redis.delete(key)
        return
    if _db:
        with _lock:
            _db.execute("DELETE FROM kv WHERE k=?", (key,))
            _db.commit()
        return
    _mem.pop(key, None)


def incr(key: str, ttl: Optional[int] = None) -> int:
    """
    ★ 브레이크 카운터가 이걸 씁니다. 원자적이어야 합니다.
    """
    if _redis:
        n = _redis.incr(key)
        if ttl and n == 1:
            _redis.expire(key, ttl)
        return int(n)
    if _db:
        with _lock:
            row = _db.execute(
                "SELECT v, exp FROM kv WHERE k=?", (key,)).fetchone()
            cur, exp = 0, None
            if row is not None:
                v, e = row
                if e is None or e >= _now():
                    try:
                        cur = int(json.loads(v))
                    except (ValueError, TypeError):
                        cur = 0
                    exp = e
            cur += 1
            if exp is None and ttl:
                exp = _now() + ttl
            _db.execute(
                "INSERT INTO kv(k, v, exp) VALUES(?,?,?) "
                "ON CONFLICT(k) DO UPDATE SET v=excluded.v, exp=excluded.exp",
                (key, json.dumps(cur), exp))
            _db.commit()
            return cur
    cur = _mem_get(key) or 0
    cur += 1
    exp = _mem.get(key, (None, None))[0]
    if exp is None and ttl:
        exp = _now() + ttl
    _mem[key] = (exp, cur)
    return cur


def get_int(key: str) -> int:
    if _redis:
        v = _redis.get(key)
    else:
        v = get_json(key)
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def exists(key: str) -> bool:
    if _redis:
        return bool(_redis.exists(key))
    return get_json(key) is not None


def sweep() -> int:
    """
    지난 항목 청소. 돌려주는 것은 지운 개수.

    ★ 이게 안 돌면 저장소가 **줄지 않습니다.**
      TTL 이 붙어 있어도 지우는 건 그 키를 **다시 읽을 때**뿐이라,
      다시 오지 않는 사람의 훅 캐시·공유 링크는 영영 남습니다.
      1만 명 시험에서 이 함수의 호출처가 한 곳도 없었습니다.
      지금은 main.py 의 청소기가 주기로 부릅니다.
    """
    if _redis:
        return 0                      # 레디스는 스스로 만료시킵니다
    if _db:
        with _lock:
            cur = _db.execute(
                "DELETE FROM kv WHERE exp IS NOT NULL AND exp < ?", (_now(),))
            _db.commit()
            return cur.rowcount or 0
    # 메모리 백엔드도 청소합니다. 여기가 특히 샜습니다 — 읽히지 않는 키는
    # 만료돼도 파이썬 사전에 그대로 남아 프로세스가 살아 있는 동안 쌓입니다.
    now = _now()
    dead = [k for k, (exp, _v) in list(_mem.items())
            if exp is not None and exp < now]
    for k in dead:
        _mem.pop(k, None)
    return len(dead)


def clear_all() -> None:
    """테스트용. 운영 코드에서 부르지 마세요."""
    if _redis:
        _redis.flushdb()
        return
    if _db:
        with _lock:
            _db.execute("DELETE FROM kv")
            _db.commit()
        return
    _mem.clear()


def stats() -> dict:
    """/health 에서 보여줄 값."""
    out = {"backend": BACKEND, "durable": BACKEND in ("redis", "sqlite")}
    if _db:
        with _lock:
            out["keys"] = _db.execute("SELECT count(*) FROM kv").fetchone()[0]
        out["path"] = STORE_PATH
    elif _redis:
        try:
            out["keys"] = _redis.dbsize()
        except Exception:                      # noqa: BLE001
            pass
    else:
        out["keys"] = len(_mem)
    return out


# ── 키 규약 ────────────────────────────────────────────────
DAY = 86400


def k_chart(chart_id: str) -> str:
    return "chart:%s" % chart_id


def k_hook(chart_id: str, concern: str, axis4: str, lens_id: str,
           name: str = "") -> str:
    """
    ★ name 을 반드시 키에 넣습니다.

    chart_id 는 생년월일시·성별·도시 해시입니다. 같은 날 같은 시에 태어난
    다른 사람은 chart_id 가 같습니다. 이름을 키에서 빼면 뒤에 온 사람이
    앞사람 이름이 박힌 훅을 받습니다.
    """
    tag = hashlib.sha256(name.strip().encode()).hexdigest()[:8] if name.strip() else "-"
    return "hook:%s:%s:%s:%s:%s" % (chart_id, concern, axis4 or "-",
                                    lens_id or "-", tag)


def k_relay_session(session_id: str) -> str:
    return "relay:session:%s" % session_id


def k_purchase_day(user_key: str, day: str) -> str:
    return "purchase:%s:%s" % (user_key, day)


def k_reunion_cooldown(user_key: str) -> str:
    return "reunion:%s" % user_key


def k_visits(user_key: str, day: str) -> str:
    return "visit:%s:%s" % (user_key, day)
