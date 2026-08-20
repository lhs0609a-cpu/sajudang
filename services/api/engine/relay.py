"""
릴레이 엔진 — 사주 조건이 다음 캐릭터를 추천한다. seed/relay_rules.json

    priority 내림차순 → 이미 읽은/거절한 렌즈 제외 → 상위 3개
    forced : 노파·연담 다음에는 청동자를 강제로 앞에 붙인다 (정서 안전망)

★ 브레이크는 설정으로 끌 수 없습니다. (CLAUDE.md 절대 규칙 4)

    세션당 릴레이 2명 · 하루 결제 2건 · 재회 7일 쿨다운
    거절한 캐릭터 재권유 없음 · 무거운 리포트 뒤 무료 캐릭터 강제
    하루 3회 접속 시 만류 문구

매출 최적화 요청이 와도 이 값들은 유지합니다. 조건부로 우회하는 코드를
넣지 마세요. 브레이크는 `BREAKS` 상수에서만 읽습니다.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from . import lens as lens_mod

SEED = Path(__file__).resolve().parents[3] / "seed"

TOP_N = 3


@lru_cache(maxsize=1)
def _rules_file() -> dict:
    return json.loads((SEED / "relay_rules.json").read_text("utf-8"))


def rules() -> list:
    return _rules_file()["rules"]


def forced_map() -> dict:
    return _rules_file()["forced"]


@lru_cache(maxsize=1)
def BREAKS() -> dict:
    """
    브레이크 값. 파일에서 읽되 **하한을 코드가 강제**한다.
    시드를 고쳐 브레이크를 느슨하게 만들 수 없도록.
    """
    b = dict(_rules_file()["breaks"])
    b["per_session_relay"] = min(int(b.get("per_session_relay", 2)), 2)
    b["per_day_purchase"] = min(int(b.get("per_day_purchase", 2)), 2)
    b["reunion_cooldown_days"] = max(int(b.get("reunion_cooldown_days", 7)), 7)
    b["visit_warn_at"] = min(int(b.get("visit_warn_at", 3)), 3)
    return b


# ── 조건 평가 ──────────────────────────────────────────────
def _fields(f) -> dict:
    """조건식이 참조할 수 있는 값. 여기 없는 필드는 규칙에서 쓸 수 없다."""
    daeun = f.daeun[f.daeun_now]
    return {
        "always": True,
        "el[weak_el]": f.elements[f.weak_el],
        "el[strong_el]": f.elements[f.strong_el],
        "gap": f.gap,
        "ilji_chung": f.ilji_chung,
        "gwan": f.gwan,
        "jae": f.jae,
        "sik": f.sik,
        "bi": f.bi,
        "inn": f.inn,
        "gwan_and_jae": min(f.gwan, f.jae),
        "strength": f.strength,
        "strength_score": f.strength_score,
        "flow": f.flow,
        "top_ten_god": f.top_ten_god,
        "daeun_ten_god": f.daeun_ten_god,
        "weak_el": f.weak_el,
        "strong_el": f.strong_el,
        "hour_known": f.hour_known,
        "age": f.age,
        "_daeun_gz": daeun["gz"],
        "_day_ji": f.day_ji,
    }


class RelayRuleError(ValueError):
    pass


def _compare(got, op: str, want) -> bool:
    if op == "==":
        return got == want
    if op == "!=":
        return got != want
    if op == ">=":
        return got >= want
    if op == "<=":
        return got <= want
    if op == ">":
        return got > want
    if op == "<":
        return got < want
    if op == "in":
        return got in want
    if op == "not in":
        return got not in want
    raise RelayRuleError("모르는 연산자: %r" % (op,))


def _reason(template: str, f, vals: dict, cond: dict) -> str:
    ctx = {
        "weak_el": f.weak_el, "strong_el": f.strong_el,
        "gap": f.gap, "gwan": f.gwan, "jae": f.jae, "sik": f.sik,
        "bi": f.bi, "inn": f.inn,
        "strength": f.strength, "strength_score": f.strength_score,
        "flow": f.flow, "top_ten_god": f.top_ten_god,
        "daeun_ten_god": f.daeun_ten_god,
        "daeun_gz": vals["_daeun_gz"], "day_ji": vals["_day_ji"],
        "v": vals.get(cond.get("field")),
    }
    try:
        return template.format(**ctx)
    except (KeyError, IndexError):
        return template


def evaluate(f, read: Optional[list] = None, skipped: Optional[list] = None
             ) -> list:
    """
    조건을 만족하는 렌즈를 priority 내림차순으로. 읽은/거절한 것은 뺀다.
    거절한 캐릭터는 **다시 권하지 않는다**.
    """
    read = set(read or [])
    skipped = set(skipped or [])
    vals = _fields(f)

    out = []
    for r in rules():
        if r["lens_id"] in read or r["lens_id"] in skipped:
            continue
        cond = r["condition"]
        field = cond["field"]
        if field not in vals:
            raise RelayRuleError(
                "규칙 %s 가 모르는 필드를 봅니다: %r" % (r["id"], field))
        if not _compare(vals[field], cond["op"], cond["value"]):
            continue
        try:
            info = lens_mod.public(r["lens_id"])
        except lens_mod.LensError:
            continue
        out.append({
            "rule_id": r["id"],
            "lens_id": r["lens_id"],
            "name": info["name"],
            "priority": r["priority"],
            "price": info["price"],
            "released": info["released"],
            "reason": _reason(r.get("reason", ""), f, vals, cond),
            "quote": lens_mod.get(r["lens_id"]).get("opening_quote"),
        })
    out.sort(key=lambda x: -x["priority"])
    return out


def recommend(f, read: Optional[list] = None, skipped: Optional[list] = None,
              session_relay_count: int = 0,
              last_lens: Optional[str] = None) -> dict:
    """
    릴레이 추천 결과.

    session_relay_count : 이번 세션에서 이미 릴레이로 넘어간 횟수
    last_lens           : 방금 읽은 렌즈 (forced 판정용)
    """
    breaks = BREAKS()
    blocked = session_relay_count >= breaks["per_session_relay"]

    ranked = evaluate(f, read, skipped)
    top = ranked[:TOP_N]

    # 정서 안전망 — 무거운 리포트 뒤에는 무료 캐릭터를 강제로 앞에 붙인다
    forced = []
    target = forced_map().get(last_lens) if last_lens else None
    if target and target not in (read or []) and target not in (skipped or []):
        forced = [target]
        top = [t for t in top if t["lens_id"] != target]

    return {
        "recommend": [] if blocked else top,
        "forced": forced,
        "blocked": blocked,
        "block_reason": ("세션당 릴레이는 %d명까지요. 오늘은 여기까지 하십시다."
                         % breaks["per_session_relay"]) if blocked else None,
        "breaks": breaks,
    }
