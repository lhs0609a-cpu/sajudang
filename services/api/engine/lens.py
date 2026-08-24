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
    v = _views().get(lens_id)
    if v and v.get("you"):
        return v["you"]
    try:
        return get(lens_id).get("you_word") or DEFAULT_YOU
    except LensError:
        return DEFAULT_YOU


# ══════════════════════════════════════════════════════════
# 관점 — 같은 명식을 스무 명이 다르게 보게 하는 자리
# ══════════════════════════════════════════════════════════
#
# ★ 이게 없으면 렌즈가 이름·색만 바꿉니다.
#   실제로 그랬습니다 — 20명의 리포트가 바이트 단위로 같았습니다.
#   "스무 명이 각자의 관점으로 해석" 이 이 서비스의 한 줄인데
#   그 한 줄이 구현돼 있지 않았습니다.
#
# ★ 근거는 캐릭터가 바꾸지 않습니다.
#   여덟 글자는 하나입니다. 말하는 **순서와 어조**만 다릅니다.

DEFAULT_VIEW = {
    "you": DEFAULT_YOU,
    "lead": None,
    "focus": [],
    "mute": [],
    "open": None,
    "close": None,
    "notes": {},
}


@lru_cache(maxsize=1)
def _views() -> dict:
    raw = json.loads((SEED / "lens_view.json").read_text("utf-8"))
    return {k: v for k, v in raw.items() if k != "_"}


def view(lens_id: Optional[str]) -> dict:
    """캐릭터의 관점. 없는 캐릭터면 기본값 — 화면이 죽지 않게."""
    v = _views().get(lens_id or "")
    if not v:
        return dict(DEFAULT_VIEW)
    out = dict(DEFAULT_VIEW)
    out.update(v)
    return out


def missing_views() -> list:
    """관점이 안 적힌 캐릭터. 테스트가 이걸 봅니다."""
    return [l["id"] for l in all_lenses() if l["id"] not in _views()]


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
