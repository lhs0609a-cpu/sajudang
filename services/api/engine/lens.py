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


def you_word(lens_id: Optional[str], name: str = "",
             sex: Optional[str] = None) -> str:
    """
    캐릭터별 호칭 — 그대 / 당신 / 자네 / 너 / 손님 / 이름 / 아저씨…

    ★ 이름·성별을 안 넘기면 「이름」·「성별」 캐릭터는 대신 부르는 말로
      물러섭니다. 지어내지 않습니다.
    """
    if not lens_id:
        return DEFAULT_YOU
    return you_of(lens_id, name, sex)


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
    # 말투. 안 적혀 있으면 하오체 — 뱅크 원문 그대로 나갑니다.
    # (engine/voice.py · seed/lens_view.json)
    "voice": "hao",
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


def you_of(lens_id: Optional[str], name: str = "",
           sex: Optional[str] = None) -> str:
    """
    이 캐릭터가 손님을 뭐라 부르는가.

    ★ 스무 명 중 열여섯이 똑같이 「그대」였습니다. 관점은 스무 개 다
      다른데 부르는 말이 하나면, 읽는 사람에게는 같은 사람이 계속
      말하는 것처럼 들립니다.

      「이름」  손님이 적은 이름으로 부릅니다. 안 적었으면 you_else.
      「성별」  사내면 you_m · 여인이면 you_f (청동자가 아저씨/아주머니).
    """
    v = view(lens_id)
    you = v.get("you") or DEFAULT_YOU

    if you == "이름":
        clean = (name or "").strip()
        # 이름을 안 적은 사람이 열에 넷이 넘습니다. 그때 「이름」이라고
        # 부를 수는 없으니 그 캐릭터의 대신 부르는 말로 물러섭니다.
        return clean or v.get("you_else") or DEFAULT_YOU

    if you == "성별":
        # ★ 모르면 지어내지 않습니다.
        #   sex 가 없을 때 한쪽으로 정하면 그건 추측입니다 — 이 집이
        #   시주를 열두 시로 채우지 않는 것과 같은 이유입니다.
        if sex not in ("M", "F"):
            return v.get("you_else") or DEFAULT_YOU
        return (v.get("you_m") if sex == "M" else v.get("you_f")) or DEFAULT_YOU

    return you


def missing_views() -> list:
    """관점이 안 적힌 캐릭터. 테스트가 이걸 봅니다."""
    return [l["id"] for l in all_lenses() if l["id"] not in _views()]


def complement(prev_id: Optional[str], cand_id: str) -> float:
    """
    앞 캐릭터가 **뒤로 민 자리**(mute)를 다음 캐릭터가 **앞세우는가**(focus).
    0.0 ~ 1.0. 릴레이 재순위에서 가중치를 받습니다.

    ★ 이걸로 두 번째 결제가 팔리지는 않습니다.
      재봤습니다 — 순서는 100% 달라지는데 새 문장은 평균 +0.29개뿐이었습니다.
      여덟 글자가 하나뿐이라 **입력이 같으면 리포트는 순서만 바뀝니다.**
      진짜 병목은 추천이 아니라 추가 입력입니다. `missing_inputs()` 를 보세요.
      그래도 순서를 바꾸는 것은 값이 있어 남겨 둡니다 — 다만 작은 가중치로.
    """
    if not prev_id or prev_id == cand_id:
        return 0.0
    muted = set(view(prev_id).get("mute") or ())
    if not muted:
        return 0.0
    focus = set(view(cand_id).get("focus") or ())
    if not focus:
        return 0.0
    return len(muted & focus) / float(len(muted))


# ══════════════════════════════════════════════════════════
# 결합 축 — 추가 입력
# ══════════════════════════════════════════════════════════
#
# ★ 두 번째 결제가 안 팔리는 진짜 이유가 여기 있습니다.
#
#   캐릭터를 바꿔 또 사면 같은 컷을 순서만 바꿔 받습니다. 처음에는
#   추천 문제라 보고 lens.complement 를 붙였는데, 재보니 새 문장이
#   평균 3.27 → 3.56개, **+0.29개뿐**이었습니다.
#
#   병목은 추천이 아니었습니다. docs/07 §결합 축이 이미 적어 둔 대로
#
#       입력 데이터가 다를 때만 진짜 다른 상품입니다.
#
#   여덟 글자는 하나뿐입니다. 입력이 같으면 관점을 아무리 적어도
#   리포트는 순서만 바뀝니다. 문장이 모자란 게 아니라 입력이 없는 것입니다.
#
#   문서에만 있으면 잊히므로 seed/lenses.json 에 `input` 을 적고
#   여기서 셉니다. 테스트가 숫자를 봅니다.

# 실제로 리포트에 반영되는 추가 입력. 새로 구현하면 여기 넣으세요.
IMPLEMENTED_INPUTS = frozenset({
    "axis4",       # 성향 4글자 — 훅 2.5단 · 리포트 7컷 (engine/bank.axis_compare)
    "birthplace",  # 출생지 — 진태양시 보정 (engine/calendar)
    "blood",       # 혈액형 — 적혈랑        (engine/extras.blood_cut)
    "image",       # 이미지 선택 — 몽화      (engine/extras.image_cut)
    "cards",       # 카드 석 장 — 패선생     (engine/extras.cards_cut)
    "partner",     # 상대 사주 — 관계축 4명  (engine/extras.partner_cut)
    "context",     # 현재 상황 — 맥락축 4명  (engine/extras.context_cut)
})

# 못 붙이는 것과 그 이유. 비워 두면 '아직 안 함' 과 구별되지 않습니다.
BLOCKED_INPUTS = {
    "photo": ("얼굴 사진은 생체인식정보라 저장이 금지돼 있습니다 "
              "(CLAUDE.md · docs/11). 저장 없이 처리하는 설계를 먼저 "
              "정해야 합니다. 면상선생은 출시 최후순위입니다."),
}


def required_input(lens_id: str) -> Optional[str]:
    """이 캐릭터가 받아야 하는 추가 입력. 없으면 None."""
    return get(lens_id).get("input")


def missing_inputs() -> list:
    """
    설계에는 있는데 아직 리포트에 안 쓰이는 추가 입력.

    돌려주는 것: [{"lens_id","name","input","reason"}]
    테스트가 이 목록이 **늘면** 알려줍니다.
    """
    out = []
    for l in all_lenses():
        need = l.get("input")
        if not need or need in IMPLEMENTED_INPUTS:
            continue
        out.append({"lens_id": l["id"], "name": l["name"], "input": need,
                    "reason": BLOCKED_INPUTS.get(need, "미구현")})
    return out


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
