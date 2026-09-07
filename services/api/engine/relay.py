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
from .bank import born_season, element_word, josa, josa_hanja

SEED = Path(__file__).resolve().parents[3] / "seed"

TOP_N = 3

# 아무 규칙도 안 걸렸을 때 세우는 캐릭터. **무료여야 합니다.**
# 근거 없이 값을 받는 캐릭터를 권하면 그건 추천이 아니라 강매입니다.
FALLBACK_LENS = "dongja"


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
def _years_to_next_daeun(f) -> int:
    """다음 대운까지 남은 해. 마지막 칸이면 크게 돌려 규칙에 안 걸리게."""
    nxt = f.daeun_now + 1
    if nxt >= len(f.daeun):
        return 99
    return max(0, int(f.daeun[nxt]["start_age"]) - int(f.age))


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
        # ── 규칙 20개를 위해 넓힌 자리 ────────────────────
        # ★ 스무 명에게 각자의 조건을 주려면 볼 수 있는 값이 그만큼
        #   있어야 합니다. 열 명이 규칙 없이 남아 있던 이유가 이것입니다.
        "season": born_season(f),
        "deuk_ryeong": f.deuk_ryeong,
        "deuk_ji": f.deuk_ji,
        "top_ten_god_tied": f.top_ten_god_tied,
        "sinsal_good": sum(1 for s in f.sinsal if s["kind"] == "길신"),
        "sinsal_bad": sum(1 for s in f.sinsal if s["kind"] == "살"),
        "helper_pillars": len({h["pillar"] for h in f.helpers}),
        "ilji_hap": len(f.ilji_hap),
        "daeun_started": f.daeun_started,
        "zero_els": sum(1 for v in f.elements.values() if v == 0),
        # 온도 — 백운선사가 보는 자리. 십신을 세지 않고 화·수만 봅니다.
        "temp_gap": abs(f.elements["화"] - f.elements["수"]),
        # 통근 — 풍운도령. 월령과 일지를 둘 다 얻었는가.
        "deuk_both": bool(f.deuk_ryeong and f.deuk_ji),
        # 대운이 바뀔 때까지 남은 해. 일관이 날을 보는 자리.
        "daeun_years_left": _years_to_next_daeun(f),
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
    """
    화면에 보이는 근거 한 줄.

    ★ 근거는 보이되 **규칙은 감춥니다.**
      전에는 `목 0.0 ≤ 1.0` 을 그대로 렌더했습니다. `목 0.0` 은 그 사람의
      명식이라 보여도 되지만 `≤ 1.0` 은 우리 문턱입니다. 문턱이 새면
      규칙을 역산할 수 있고, 사용자는 자기 얘기가 아니라 분기표를 봅니다.
      그래서 여기 들어오는 문구에는 **연산자와 문턱값을 쓰지 않습니다.**
      tests/test_wiring.py 가 새는 문구를 잡습니다.
    """
    ctx = {
        "weak_el": f.weak_el, "strong_el": f.strong_el,
        "weak_word": element_word(f.weak_el),
        "strong_word": element_word(f.strong_el),
        "weak_n": f.elements[f.weak_el], "strong_n": f.elements[f.strong_el],
        # ★ 조사가 붙은 이름. 근거에서 숫자를 걷어내고 말로 쓰려면
        #   "나무가 / 불이" 를 골라 줄 자리가 있어야 합니다.
        "weak_iga": josa(element_word(f.weak_el), "이", "가"),
        "strong_iga": josa(element_word(f.strong_el), "이", "가"),
        "weak_eneun": josa(element_word(f.weak_el), "은", "는"),
        "strong_eneun": josa(element_word(f.strong_el), "은", "는"),
        "day_ji_iga": josa_hanja(f.day_ji, "이", "가"),
        "day_ji_eneun": josa_hanja(f.day_ji, "은", "는"),
        "daeun_gz_iga": josa_hanja(vals["_daeun_gz"][-1], "이", "가"),
        "gap": f.gap, "gwan": f.gwan, "jae": f.jae, "sik": f.sik,
        "bi": f.bi, "inn": f.inn,
        "strength": f.strength, "strength_score": f.strength_score,
        "flow": f.flow, "top_ten_god": f.top_ten_god,
        "daeun_ten_god": f.daeun_ten_god,
        "daeun_gz": vals["_daeun_gz"], "day_ji": vals["_day_ji"],
        "season": vals["season"], "temp_gap": vals["temp_gap"],
        "helper_pillars": vals["helper_pillars"],
        "sinsal_good": vals["sinsal_good"], "sinsal_bad": vals["sinsal_bad"],
        "ilji_hap": vals["ilji_hap"],
        "v": vals.get(cond.get("field")),
    }
    try:
        return template.format(**ctx)
    except (KeyError, IndexError):
        return template


def evaluate(f, read: Optional[list] = None, skipped: Optional[list] = None,
             concern: Optional[str] = None,
             ignore_concern_gate: bool = False) -> list:
    """
    조건을 만족하는 렌즈를 priority 내림차순으로. 읽은/거절한 것은 뺀다.
    거절한 캐릭터는 **다시 권하지 않는다**.

    ★ `when_concern` 이 달린 규칙 (2026-09-06)

      재보니 돈을 물은 사람의 **32%**, 몸을 물은 사람의 **35%** 에게만
      그 자리를 보는 캐릭터가 후보에 올랐습니다. 후보에 없으면 재순위로는
      못 올립니다 — 순서를 아무리 잘 매겨도 없는 사람은 안 나옵니다.
      그래서 «그 고민을 물었을 때만 서는» 규칙을 둡니다.

      조건은 여전히 **명식**입니다. 「돈을 물었으니 장사꾼」 은 근거가
      아니라 장사입니다. 「돈을 물었고, 나눌 입이 여럿이오」 라야 근거요.

    ignore_concern_gate : 도달률을 재는 자리(tools/relay_reach.py)에서만
      참입니다. 게이트를 무시하고 **조건만** 보아 인구 비율을 냅니다 —
      그러지 않으면 이 규칙들이 도달률 0으로 잡혀 재순위에서 늘 이깁니다.
    """
    read = set(read or [])
    skipped = set(skipped or [])
    vals = _fields(f)

    out = []
    for r in rules():
        if r["lens_id"] in read or r["lens_id"] in skipped:
            continue
        gate = r.get("when_concern")
        if gate and not ignore_concern_gate and gate != concern:
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


# ── 재순위 — 쏠림을 깎고 보완을 올린다 ────────────────────
#
# ★ 왜 priority 정렬만으로는 안 되는가
#   조건은 인구에 고르게 걸리지 않습니다. 넓은 조건을 가진 캐릭터가
#   늘 1순위를 가져가고, 좁은 조건을 가진 캐릭터는 밀려서 영영 안
#   보입니다. 실제로 3,000명 중 86%가 같은 1순위를 받았고 스무 명 중
#   열한 명은 한 번도 추천되지 않았습니다.
#
#   추천시스템에서는 오래된 문제입니다(popularity bias). 정석 처방은
#   **관련도에서 노출 점유율을 빼는 후처리 재순위** 입니다.
#   모델을 건드리지 않고 정렬 단계에만 붙습니다.
#
#       점수 = priority/100  −  λ × 도달률  +  w × 보완도
#
#   도달률은 실시간 노출 카운터가 아니라 **미리 잰 값**(rule.reach)입니다.
#   규칙이 결정적이라 도달률도 결정적이고, 워커가 여럿이어도 결과가
#   요청 순서에 따라 흔들리지 않습니다. tools/relay_reach.py 가 잽니다.
#
# ★ λ를 키우기 전에 규칙을 좁히세요.
#   λ=1.0 을 넣으면 쏠림은 풀리지만 간판 캐릭터가 0.3%로 죽습니다.
#   그건 과교정입니다. 진짜 원인은 λ가 아니라 넓은 문턱이었습니다.

DEFAULT_LAMBDA = 0.5
DEFAULT_COMPLEMENT_W = 0.15
# ★ 물으신 자리를 실제로 보는 사람인가 (2026-09-06)
#
#   손님이 짚었소 — "지금 어떤 고민이냐에 따라 전부 다 달라지고
#   캐릭터마다도 전문성을 다 넣은 거 맞아?"
#
#   재보니 릴레이가 **고민을 한 줄도 안 보고** 있었습니다. 이 집의
#   뼈대가 릴레이인데, 돈을 물은 사람에게 다음 사람을 고를 때 그
#   물음이 아무 무게도 없었습니다.
#
#   그래서 항을 하나 더합니다.
#
# ★ 값을 0.2 → 0.45 로 올렸습니다 (2026-09-07)
#
#   손님이 또 짚었습니다 — "캐릭터도 그 캐릭 전문성에 맞게끔
#   상담해야하고 이거 계속 문제야."
#
#   재보니 0.2 로는 우선순위 격차를 못 이겼습니다. 삼거리 노파(방향
#   담당·priority 95)가 **여섯 고민 전부에서 1순위 최다**였습니다.
#   돈을 물어도 사랑을 물어도 몸을 물어도 노파가 먼저 섰습니다.
#
#   값을 훑어 재 보니(표본 300명 × 여섯 칸):
#
#       w      담당이 1순위   담당이 상위3   최다 1순위   1순위 도달
#       0.20        70%          87%      노파 14%      19명
#       0.35        84%          88%      행수 11%      19명
#       0.45        88%          88%      행수 11%      19명
#
#   0.45 부터 평평해지고, **쏠림이 오히려 줄었습니다**(14%→11%).
#   크게 두면 쏠린다는 걱정과 반대였습니다 — 고민이 여섯이라 무게가
#   여섯 갈래로 흩어지기 때문입니다. 도달은 19명 그대로입니다.
#   고민을 안 고른 자리(`tools/relay_spread.py`)는 손대지 않으므로
#   최다 1순위 21.4% · 20/20 도 그대로입니다.
DEFAULT_CONCERN_W = 0.45


def _tuning() -> dict:
    d = _rules_file()
    return {
        "exposure_lambda": float(d.get("exposure_lambda", DEFAULT_LAMBDA)),
        "complement_weight": float(
            d.get("complement_weight", DEFAULT_COMPLEMENT_W)),
        "concern_weight": float(d.get("concern_weight", DEFAULT_CONCERN_W)),
    }


def covers(lens_id: str, concern: Optional[str]) -> bool:
    """
    이 사람이 **물으신 자리를 실제로 보는가.**

    ★ 지어내지 않습니다. 캐릭터마다 `seed/lenses.json` 의 `concerns` 에
      못박혀 있고, 그건 그 사람의 전문(specialty·topics)에서 나옵니다.
      비워 둔 사람도 있습니다 — 청동자는 값이 없는 브레이크라 어느
      자리도 «제 자리»라 하지 않습니다.
    """
    if not concern:
        return False
    try:
        got = lens_mod.get(lens_id) or {}
    except lens_mod.LensError:
        return False
    return concern in (got.get("concerns") or ())


def rerank(items: list, last_lens: Optional[str] = None,
           concern: Optional[str] = None) -> list:
    """
    evaluate() 결과를 재순위한다. 목록의 내용은 바꾸지 않고 **순서만** 바꾼다.
    각 항목에 `score` 를 적어 둔다 — 왜 그 순서인지 나중에 볼 수 있게.

        점수 = priority/100 − λ×도달률 + w×보완도 + c×물은자리

    ★ 마지막 항이 2026-09-06 에 붙었습니다. 고민은 손님이 여섯 칸에서
      **직접 고른 것**이라, 다음 사람을 고를 때 그게 아무 무게도 없으면
      그 고름은 리포트 안에서만 살고 연쇄에서는 죽습니다.
    """
    t = _tuning()
    lam, w, cw = (t["exposure_lambda"], t["complement_weight"],
                  t["concern_weight"])
    by_rule = {r["id"]: r for r in rules()}

    out = []
    for it in items:
        it = dict(it)
        reach = float(by_rule.get(it["rule_id"], {}).get("reach") or 0.0)
        comp = lens_mod.complement(last_lens, it["lens_id"]) if last_lens else 0.0
        fit = 1.0 if covers(it["lens_id"], concern) else 0.0
        it["reach"] = reach
        it["complement"] = round(comp, 3)
        it["concern_fit"] = fit
        it["score"] = round(it["priority"] / 100.0 - lam * reach + w * comp
                            + cw * fit, 4)
        out.append(it)
    # 점수 내림차순. 같으면 priority — 결과가 흔들리지 않게 두 번째 키를 둔다.
    out.sort(key=lambda x: (-x["score"], -x["priority"], x["lens_id"]))

    # ★ 한 사람이 두 번 서지 않게 (2026-09-06)
    #
    #   게이트 규칙을 더하면서 **같은 캐릭터에 규칙이 둘** 걸리는 자리가
    #   생겼습니다. 약초의원이 「빈 기운이 있소」와 「몸을 물으셨는데 빈
    #   기운이 있소」에 둘 다 걸리면, 셋을 권하는 자리에 같은 사람이 두
    #   번 섭니다. 배포본에서 실제로 그렇게 나왔습니다 — 재보니 6%입니다.
    #
    #   가장 높은 점수 하나만 남깁니다. 이미 정렬돼 있으니 앞의 것이
    #   그 사람의 가장 좋은 근거입니다.
    seen: set = set()
    only = []
    for it in out:
        if it["lens_id"] in seen:
            continue
        seen.add(it["lens_id"])
        only.append(it)
    return only


# 화면에 내려보내도 되는 필드. 여기 없는 것은 나가지 않습니다.
#
# ★ rule_id · priority · reach · score 는 **우리 분기표**입니다.
#   근거(reason)는 그 사람의 명식이라 보여야 하지만, 어떤 규칙이 몇 점으로
#   이겼는지는 알고리즘입니다. 새면 규칙을 역산할 수 있고, 사용자는 자기
#   얘기가 아니라 순위표를 읽게 됩니다.
PUBLIC_FIELDS = ("lens_id", "name", "price", "released", "reason", "quote")


def _public_item(it: dict) -> dict:
    return {k: it.get(k) for k in PUBLIC_FIELDS}


def recommend(f, read: Optional[list] = None, skipped: Optional[list] = None,
              session_relay_count: int = 0,
              last_lens: Optional[str] = None,
              concern: Optional[str] = None) -> dict:
    """
    릴레이 추천 결과.

    session_relay_count : 이번 세션에서 이미 릴레이로 넘어간 횟수
    last_lens           : 방금 읽은 렌즈 (forced 판정용)
    """
    breaks = BREAKS()
    blocked = session_relay_count >= breaks["per_session_relay"]

    ranked = rerank(evaluate(f, read, skipped, concern), last_lens, concern)
    top = ranked[:TOP_N]

    # ── 아무 규칙도 안 걸린 사람 ──────────────────────────
    #
    # ★ 조건을 좁히면 반드시 생깁니다 (인구의 약 1%).
    #   전에는 `always` 규칙 둘이 이 자리를 메우고 있었습니다. 그런데
    #   누구에게나 걸리는 규칙은 추천이 아니라 배경이라, 재순위에서 늘
    #   꼴찌가 되어 그 캐릭터는 영영 안 팔립니다.
    #
    #   그렇다고 빈 화면을 보일 수는 없습니다. 그래서 **무료 캐릭터**를
    #   세웁니다. 근거가 없을 때 값을 받는 캐릭터를 권하는 건 강매입니다.
    #   근거가 없다고 말하고, 값 없는 자리로 보냅니다.
    if not top and not blocked:
        fb = FALLBACK_LENS
        if fb not in (read or []) and fb not in (skipped or []):
            try:
                info = lens_mod.public(fb)
                top = [{
                    "rule_id": "r_fallback", "lens_id": fb,
                    "name": info["name"], "priority": 0,
                    "price": info["price"], "released": info["released"],
                    "reason": "여덟 글자에서 특별히 도드라지는 자리가 없어요",
                    "quote": lens_mod.get(fb).get("opening_quote"),
                    "reach": 0.0, "complement": 0.0, "score": 0.0,
                }]
            except lens_mod.LensError:
                top = []

    # 정서 안전망 — 무거운 리포트 뒤에는 무료 캐릭터를 강제로 앞에 붙인다
    forced = []
    target = forced_map().get(last_lens) if last_lens else None
    if target and target not in (read or []) and target not in (skipped or []):
        forced = [target]
        top = [t for t in top if t["lens_id"] != target]

    # ★ 왜 이 사람인지 **한 마디**를 답니다.
    #
    #   점수·규칙·도달률은 우리 분기표라 안 냅니다(PUBLIC_FIELDS). 다만
    #   「그대가 고른 자리를 이 사람이 본다」는 것은 손님의 말이라 냅니다 —
    #   그게 없으면 고민을 반영해도 손님은 반영된 줄 모릅니다.
    fit_say = _rules_file().get("concern_say", {}).get(concern or "", "")
    for t in top:
        if fit_say and t.get("concern_fit"):
            t["reason"] = "%s · %s" % (t.get("reason") or "", fit_say)

    return {
        "recommend": [] if blocked else [_public_item(t) for t in top],
        "forced": forced,
        "blocked": blocked,
        "block_reason": ("세션당 릴레이는 %d명까지요. 오늘은 여기까지 하십시다."
                         % breaks["per_session_relay"]) if blocked else None,
        "breaks": breaks,
    }
