"""
캐릭터 렌즈 — seed/lenses.json 로더. docs/07_캐릭터_20인_설정집.md

★ 렌즈 프롬프트·금지어 목록은 클라이언트로 내려보내지 않습니다. (docs/02 §7)
  화면에 필요한 것만 `public()` 으로 추려서 내려보내세요.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

SEED = Path(__file__).resolve().parents[3] / "seed"

DEFAULT_YOU = "그대"


class LensError(KeyError):
    pass


@lru_cache(maxsize=1)
def all_lenses() -> tuple:
    data = json.loads((SEED / "lenses.json").read_text("utf-8"))
    return tuple(data)


@lru_cache(maxsize=1)
def _by_id() -> dict:
    return {l["id"]: l for l in all_lenses()}


def get(lens_id: str) -> dict:
    try:
        return _by_id()[lens_id]
    except KeyError:
        raise LensError("모르는 렌즈: %r" % (lens_id,))


def you_word(lens_id: Optional[str]) -> str:
    """캐릭터별 호칭 — 그대 / 자네 / 아저씨"""
    if not lens_id:
        return DEFAULT_YOU
    try:
        return get(lens_id).get("you_word") or DEFAULT_YOU
    except LensError:
        return DEFAULT_YOU


def released() -> list:
    return [l for l in all_lenses() if l.get("released")]


def public(lens_id: str) -> dict:
    """화면에 내려보내도 되는 필드만."""
    l = get(lens_id)
    return {
        "id": l["id"], "name": l["name"], "hanja": l.get("hanja"),
        "group": l.get("group"), "archetype": l.get("archetype"),
        "call": l.get("call"), "price": l.get("price"),
        "released": bool(l.get("released")),
    }
