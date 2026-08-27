"""
관점 컷 — 그 캐릭터만 보는 자리.

★ 왜 생겼는가
  값이 캐릭터마다 다른데(4,900~19,900원) **받는 것이 값을 안 따라갔습니다.**
  1만 명 시험에서 값 ↔ 글자수 상관이 −0.231, 값 ↔ 컷수 상관이 −0.419 —
  4,900원짜리가 19,900원짜리보다 더 주고 있었습니다. 컷을 늘리는 장치가
  '추가 입력' 하나뿐인데, 비싼 캐릭터들이 그걸 안 받기 때문이었습니다.

  그래서 캐릭터마다 **자기 관점으로만 보는 컷**을 둡니다. 값이 높을수록
  자기 몫 컷이 많습니다. 자기 몫 = 추가 입력 컷 + 관점 컷.

★ 여기서도 새 점사를 지어내지 않습니다
  전부 seed/lens_cuts.json 의 표와 Feature Store 값에서만 조립합니다.
  없는 조합은 LensCutError 로 터뜨립니다 — 조용히 빈칸을 두지 않습니다.

★ 축을 반드시 둘 이상 곱합니다
  한 축만 쓰면 가짓수가 그 축의 크기에서 멈춥니다. 용신 컷이 그래서
  10가지에 갇혀 있었습니다(docs/18 §3). 여기서는 큰 축(10~12) 하나와
  작은 축(3~5) 하나를 곱해 30~60가지를 만듭니다.
  tools/dup_rate.py 가 최다 점유를 봅니다.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from . import guard
from .bank import born_season, element_word, josa

SEED = Path(__file__).resolve().parents[3] / "seed"


class LensCutError(KeyError):
    """표에 없는 조합. 지어내지 않고 터뜨린다."""


@lru_cache(maxsize=1)
def _table() -> dict:
    raw = json.loads((SEED / "lens_cuts.json").read_text("utf-8"))
    return {k: v for k, v in raw.items() if k != "_"}


# ══════════════════════════════════════════════════════════
# 축 — Feature 에서 표의 열쇠를 뽑는다
# ══════════════════════════════════════════════════════════
#
# ★ 열쇠는 **사람이 읽을 수 있는 말**이어야 합니다. seed 를 손보는 사람이
#   `deuk=둘다` 를 보고 무슨 뜻인지 바로 알아야 하기 때문입니다.

def _deuk(f) -> str:
    if f.deuk_ryeong and f.deuk_ji:
        return "둘다"
    if f.deuk_ryeong:
        return "월령만"
    if f.deuk_ji:
        return "일지만"
    return "없음"


def _johu(f) -> str:
    """조후 — 불과 물의 기울기. 백운선사가 보는 자리."""
    d = f.elements["화"] - f.elements["수"]
    if d >= 2.5:
        return "몹시더움"
    if d >= 1.0:
        return "더움"
    if d <= -2.5:
        return "몹시추움"
    if d <= -1.0:
        return "추움"
    return "고름"


def _seupjo(f) -> str:
    """습조 — 젖음과 마름. 흙·쇠는 마르고 물·나무는 젖은 쪽으로 봅니다."""
    dry = f.elements["토"] + f.elements["금"]
    wet = f.elements["수"] + f.elements["목"]
    d = dry - wet
    if d >= 2.0:
        return "마름"
    if d <= -2.0:
        return "젖음"
    return "고름"


def _gap_band(f) -> str:
    """가장 센 것과 가장 약한 것의 차. 은별 무녀가 보는 자리."""
    g = f.gap
    if g >= 4.0:
        return "크게벌어짐"
    if g >= 2.5:
        return "벌어짐"
    if g >= 1.5:
        return "조금벌어짐"
    return "고름"


def _score_band(f) -> str:
    s = f.strength_score
    if s >= 25:
        return "많이넘침"
    if s >= 8:
        return "넘침"
    if s <= -25:
        return "많이모자람"
    if s <= -8:
        return "모자람"
    return "가운데"


def _ilji_state(f) -> str:
    if f.ilji_chung and f.ilji_hap:
        return "충합"
    if f.ilji_chung:
        return "충"
    if f.ilji_hap:
        return "합"
    return "고요"


def _gwan_jae(f) -> str:
    """관과 재의 짜임. 홍매파가 보는 자리."""
    def band(n):
        return "없음" if n == 0 else ("하나" if n == 1 else "여럿")
    return "%s-%s" % (band(f.gwan), band(f.jae))


def _daeun_phase(f) -> str:
    if not f.daeun_started:
        return "들기전"
    left = f.daeun[f.daeun_now]["start_age"] + 10 - f.age
    if left <= 2:
        return "바뀔때"
    if left >= 8:
        return "막들어옴"
    return "한가운데"


def _age_band(f) -> str:
    a = f.age
    if a < 25:
        return "이십대전"
    if a < 40:
        return "삼십대"
    if a < 55:
        return "사십대"
    return "오십대후"


def _zero_band(f) -> str:
    n = sum(1 for v in f.elements.values() if v == 0)
    return {0: "없음", 1: "하나"}.get(n, "둘이상")


def _sinsal_mark(f) -> str:
    """도화·역마·화개가 있는가. 몽화가 보는 자리."""
    keys = {s["key"] for s in f.sinsal}
    on = [n for n, k in (("도화", "dohwa"), ("역마", "yeokma"),
                         ("화개", "hwagae")) if k in keys]
    return "-".join(on) if on else "없음"


def _palace(f) -> str:
    """궁위의 무게 — 길신이 어느 자리에 앉았는가. 면상선생이 보는 자리."""
    ps = {h["pillar"] for h in f.helpers}
    if not ps:
        return "빈자리"
    if "일주" in ps:
        return "제자리"
    if "월주" in ps:
        return "가운데자리"
    return "바깥자리"


def _next_daeun_tg(f) -> str:
    nxt = f.daeun_now + 1
    if nxt >= len(f.daeun):
        return f.daeun[f.daeun_now]["ten_god"]
    return f.daeun[nxt]["ten_god"]


def _month_ji(f) -> str:
    return f.pillars[1]["gz"][1]


def _year_ji(f) -> str:
    return f.pillars[0]["gz"][1]


AXES = {
    "deuk": _deuk,
    "johu": _johu,
    "seupjo": _seupjo,
    "gap_band": _gap_band,
    "score_band": _score_band,
    "ilji_state": _ilji_state,
    "gwan_jae": _gwan_jae,
    "daeun_phase": _daeun_phase,
    "age_band": _age_band,
    "zero_band": _zero_band,
    "sinsal_mark": _sinsal_mark,
    "palace": _palace,
    "next_daeun_tg": _next_daeun_tg,
    "month_ji": _month_ji,
    "year_ji": _year_ji,
    "hour_known": lambda f: "안다" if f.hour_known else "모른다",
    "top_ten_god": lambda f: f.top_ten_god,
    "daeun_ten_god": lambda f: f.daeun_ten_god,
    "strength": lambda f: f.strength,
    "flow": lambda f: f.flow,
    "season": born_season,
    "weak_el": lambda f: f.weak_el,
    "strong_el": lambda f: f.strong_el,
    "yongsin": lambda f: f.yongsin,
    "day_gan": lambda f: f.day_gan,
    "day_ji": lambda f: f.day_ji,
}


def axis_value(f, axis: str) -> str:
    try:
        return AXES[axis](f)
    except KeyError:
        raise LensCutError("모르는 축: %r" % (axis,))


# ══════════════════════════════════════════════════════════
# 조립
# ══════════════════════════════════════════════════════════
def _pick(spec: dict, f, where: str) -> tuple[str, str]:
    """(열쇠, 문장). 표에 없으면 터뜨린다 — 빈칸을 두지 않는다."""
    key = axis_value(f, spec["axis"])
    text = spec["text"]
    if key not in text:
        raise LensCutError("%s · %s 표에 %r 이(가) 없습니다"
                           % (where, spec["axis"], key))
    return key, text[key]


def _words(f) -> dict:
    """문장에서 쓸 수 있는 말. 숫자가 아니라 **말**입니다."""
    return {
        "weak": element_word(f.weak_el),
        "strong": element_word(f.strong_el),
        "yong": element_word(f.yongsin),
        "weak_iga": josa(element_word(f.weak_el), "이", "가"),
        "strong_iga": josa(element_word(f.strong_el), "이", "가"),
        "yong_iga": josa(element_word(f.yongsin), "이", "가"),
        "weak_eneun": josa(element_word(f.weak_el), "은", "는"),
        "strong_eneun": josa(element_word(f.strong_el), "은", "는"),
        "day_gan": f.day_gan,
        "day_ji": f.day_ji,
        "top": f.top_ten_god,
        "strength": f.strength,
        "flow": f.flow,
        "season": born_season(f),
        "daeun_gz": f.daeun[f.daeun_now]["gz"],
        "daeun_tg": f.daeun_ten_god,
        "age": f.age,
        "year_gz": f.pillars[0]["gz"],
        "month_gz": f.pillars[1]["gz"],
        "day_gz": f.pillars[2]["gz"],
        "month_ji": f.pillars[1]["gz"][1],
        "year_ji": f.pillars[0]["gz"][1],
        # 시주는 없을 수 있습니다. 없으면 없다고 씁니다 — 채우지 않습니다.
        "hour_gz": (f.pillars[3]["gz"] if f.hour_known and len(f.pillars) > 3
                    else "시주 없음"),
    }


def build(f, lens_id: Optional[str]) -> list:
    """
    이 캐릭터의 관점 컷들. 없으면 빈 목록.

    돌려주는 것: [{"id","title","source","html","min_level","statement_id"}]
    """
    if not lens_id:
        return []
    specs = _table().get("cuts", {}).get(lens_id) or []
    if not specs:
        return []

    w = _words(f)
    out = []
    for spec in specs:
        ka, ta = _pick(spec["a"], f, spec["id"])
        kb, tb = _pick(spec["b"], f, spec["id"])
        # ★ 세 번째 축은 **고른 축**만 씁니다 (일간·주도십신·일지·대운십신).
        #   앞의 두 축은 뜻이 맞는 대신 고르지 않아서, 축 둘로는 본문
        #   최다 점유가 17%까지 올라갔습니다. 근거 줄이 그걸 가리고
        #   있었고, tools/dup_rate.py 가 이제 본문만 따로 잽니다.
        kc, tc = _pick(spec["c"], f, spec["id"]) if spec.get("c") else ("", "")
        # ★ 근거 줄 — 이 컷이 **무슨 글자를 읽고** 한 말인지 그 자리에서 댑니다.
        #   포지션이 "맞히는 집" 이 아니라 "근거 대는 집" 이라, 관점일수록
        #   무엇을 보고 한 말인지가 붙어 있어야 합니다.
        #   숫자가 아니라 **글자**를 댑니다 — 내부 척도는 여기 안 옵니다.
        tail = spec.get("tail")
        tail_html = ('<p class="ev"><span class="evk">읽은 자리</span>%s</p>'
                     % tail.format(**w)) if tail else ""
        body = ('<p class="tale">%s</p><p class="tale">%s</p>'
                '<p class="tale">%s%s</p>%s'
                % (spec["lead"].format(**w), ta.format(**w), tb.format(**w),
                   (" " + tc.format(**w)) if tc else "", tail_html))
        out.append({
            "id": spec["id"],
            "title": spec["title"],
            "source": spec["source"].format(a=ka, b=kb, **w),
            "html": guard.enforce(body, {"cut": spec["id"]}),
            "min_level": int(spec.get("min_level", 1)),
            "statement_id": "%s:%s:%s:%s" % (spec["id"], ka, kb, kc),
        })
    return out


def owned(lens_id: str) -> int:
    """이 캐릭터의 관점 컷이 몇 개인가. 값 등급 검사가 이걸 봅니다."""
    return len(_table().get("cuts", {}).get(lens_id) or [])


def all_ids() -> list:
    return [c["id"] for cuts in _table().get("cuts", {}).values() for c in cuts]
