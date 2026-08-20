"""
출력 금지어 필터 — 모든 응답이 반드시 통과해야 함. docs/02 §8 · docs/11

금지 대상
    질병명 · 수명 · 이혼 단정 · 투자 시점 지시 · 적중률/과학적 입증 주장
    재회 가능/불가 판정 · 시점 확정 · 기다림 종용

쓰는 곳
    1. 문장 조합 단계 — engine/bank.py 가 세그먼트마다 enforce()
    2. 응답 직전 — guard_middleware.GuardMiddleware 가 전 응답을 훑는다 (안전망)

위반은 전부 로그로 남깁니다. 나중에 프롬프트·뱅크 개선에 씁니다.
"""
from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

SEED = Path(__file__).resolve().parents[3] / "seed"

log = logging.getLogger("guard")


@lru_cache(maxsize=1)
def _config() -> dict:
    return json.loads((SEED / "guard.json").read_text("utf-8"))


@lru_cache(maxsize=1)
def _patterns() -> tuple:
    return tuple(re.compile(p) for p in _config()["regex"])


def check(text: str) -> tuple[bool, list]:
    """(통과 여부, 걸린 패턴 목록)"""
    if not text:
        return True, []
    hits = [p.pattern for p in _patterns() if p.search(text)]
    return (not hits), hits


def sanitize(text: str) -> str:
    for a, b in _config()["replacements"].items():
        text = text.replace(a, b)
    return text


SAFE_FALLBACK = "이 부분은 말씀드릴 수 없소. 다른 자리를 보시겠소?"


def enforce(text: str, ctx: dict | None = None) -> str:
    """
    위반이면 치환 1회 → 그래도 안 되면 안전 문장으로 대체.
    docs/02 §8 "재생성 1회 → 실패하면 안전 문장" 과 같은 구조.
    """
    ok, hits = check(text)
    if ok:
        return text
    log.warning("guard violation %s ctx=%s text=%r", hits, ctx, text[:200])
    fixed = sanitize(text)
    ok2, hits2 = check(fixed)
    if ok2:
        return fixed
    log.error("guard unrecoverable %s ctx=%s", hits2, ctx)
    return SAFE_FALLBACK


def scan(obj: Any, path: str = "$") -> list:
    """
    중첩 구조(dict/list) 안의 모든 문자열을 검사해 위반 목록을 돌려준다.
    미들웨어가 응답 전체를 훑을 때 쓴다.
    """
    found = []
    if isinstance(obj, str):
        ok, hits = check(obj)
        if not ok:
            found.append({"path": path, "hits": hits, "text": obj[:200]})
    elif isinstance(obj, dict):
        for k, v in obj.items():
            found.extend(scan(v, "%s.%s" % (path, k)))
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            found.extend(scan(v, "%s[%d]" % (path, i)))
    return found


def enforce_deep(obj: Any, ctx: dict | None = None) -> Any:
    """중첩 구조 안의 문자열을 전부 enforce 한다."""
    if isinstance(obj, str):
        return enforce(obj, ctx)
    if isinstance(obj, dict):
        return {k: enforce_deep(v, ctx) for k, v in obj.items()}
    if isinstance(obj, list):
        return [enforce_deep(v, ctx) for v in obj]
    return obj
