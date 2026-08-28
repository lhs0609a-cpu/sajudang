"""
말투 — 캐릭터마다 다른 목소리.

★ 여기가 통째로 없었습니다.
  `docs/07_캐릭터_20인_설정집.md` 은 스무 명의 말투를 이미 정해 놓았습니다 —
  은별 무녀는 "…어긋나네요", 홍매파는 "됐고, 생년월일이나 대봐",
  훈장은 "재주는 있다. 헌데 잘못 골랐어", 삼거리 노파는 "딴 데 가서 듣게",
  연담·화경은 "…보겠습니다", 청동자는 "괜찮아요. 진짜로요".

  그런데 **엔진이 그걸 무시하고 전부 하오체로 통일해** 버렸습니다.
  재보니 스무 명 중 **열여섯이 똑같이 "그대"** 라고 부르고, 어미도
  전부 `~오/~소` 한 결이었습니다. 관점은 스무 개 다 다른데(여는 말
  20/20) 목소리가 하나라, 두 사람을 이어 읽으면 중앙값 56%가 글자
  그대로 같은 글로 읽혔습니다.

★ 문장 뱅크를 스무 벌로 다시 쓰지 않습니다.
  뱅크는 하오체 한 벌로 두고, **맨 끝에서 어미만 바꿔 끼웁니다.**
  그러면 공통 컷(리포트의 60~90%)까지 그 사람 목소리로 나갑니다.

★ 지어내지 않습니다 — 불규칙 활용을 건드리지 않습니다.
  「쉽소 → 쉬워요」(ㅂ불규칙), 「그렇소 → 그래요」(ㅎ불규칙),
  「다르오 → 달라요」(르불규칙) 같은 것은 어간을 바꿔야 합니다.
  그런 변환은 한 글자만 틀려도 문장이 깨집니다.

  그래서 **어간을 그대로 두고 붙이기만 하면 되는 어미**로만 짰습니다:

      하오체   있소   · 하오    ← 뱅크 원문 (기본)
      합쇼체   있습니다 · 합니다   받침 있으면 -습니다 / 없으면 -ㅂ니다
      하게체   있네   · 하네    어간 + 네
      반말     있지   · 하지    어간 + 지
      해요체   있네요  · 하네요   어간 + 네요

  다섯 다 어간을 안 건드립니다. 「쉽소」는 「쉽습니다·쉽네·쉽지·쉽네요」가
  되고, 하나도 안 깨집니다. 못 다루는 꼴은 **그대로 둡니다** —
  하오체로 남는 것이 틀린 문장이 되는 것보다 낫습니다.
"""
from __future__ import annotations

import re
from typing import Optional

# ══════════════════════════════════════════════════════════
# 말투 다섯
# ══════════════════════════════════════════════════════════
HAO = "hao"          # 하오체 — 뱅크 원문 그대로
HAPSYO = "hapsyo"    # 합쇼체 — 정중
HAGE = "hage"        # 하게체 — 손윗사람이 아랫사람에게
BANMAL = "banmal"    # 반말 — 툭 던지는
HAEYO = "haeyo"      # 해요체 — 다정·친근

VOICES = (HAO, HAPSYO, HAGE, BANMAL, HAEYO)


# ══════════════════════════════════════════════════════════
# 한글 받침 보기
# ══════════════════════════════════════════════════════════
_BASE = 0xAC00
_LAST = 0xD7A3
_JONG = 28


def _has_batchim(ch: str) -> Optional[bool]:
    """받침이 있는가. 한글이 아니면 None."""
    if not ch:
        return None
    o = ord(ch)
    if not (_BASE <= o <= _LAST):
        return None
    return (o - _BASE) % _JONG != 0


def _add_bieup(ch: str) -> Optional[str]:
    """받침 없는 글자에 ㅂ 을 받쳐 준다. 하 → 합 · 다르 의 '르' → 릅"""
    o = ord(ch)
    if not (_BASE <= o <= _LAST) or (o - _BASE) % _JONG != 0:
        return None
    return chr(o + 17)          # ㅂ 은 종성 17번


# ══════════════════════════════════════════════════════════
# 한 낱말 바꾸기
# ══════════════════════════════════════════════════════════
#
# 다루는 꼴 — 문장 끝에 오는 하오체만
#     …시오   시키는 말 (하시오 · 마시오 · 주시오)
#     …소     받침 있는 어간 (있소 · 않소 · 읽소 · 않았소 · 보겠소)
#     …오     받침 없는 어간 (하오 · 보오 · 것이오 · 아니오 · 바뀌오)
# ★ 반말·하게체는 '시' 를 뗍니다.
#   「정하시지」는 반말이라면서 존대가 섞인 말입니다. 어간에 바로
#   붙입니다 — 하시오 → 하지(반말) · 하게(하게체).
_IMP_KEEP_SI = {HAPSYO: "십시오", HAEYO: "세요"}
_IMP_DROP_SI = {HAGE: "게", BANMAL: "지"}
_TAIL = {
    HAGE: "네",
    BANMAL: "지",
    HAEYO: "네요",
}


def _word(w: str, voice: str) -> str:
    """낱말 하나. 못 다루는 꼴이면 그대로 돌려준다."""
    if voice == HAO or len(w) < 2:
        return w

    # ── 시키는 말 ──────────────────────────────────────
    if w.endswith("시오"):
        if voice in _IMP_KEEP_SI:
            return w[:-2] + _IMP_KEEP_SI[voice]
        return w[:-2] + _IMP_DROP_SI[voice]

    # ── 서술 ───────────────────────────────────────────
    end = w[-1]
    if end not in "오소":
        return w
    stem = w[:-1]
    if not stem:
        return w

    bat = _has_batchim(stem[-1])
    if bat is None:
        return w                      # 한글이 아니면 손대지 않는다

    # 받침 있는 어간에는 '소', 없는 어간에는 '오' 가 붙습니다.
    # 어긋나면 하오체가 아닌 다른 말이니 손대지 않습니다.
    if (end == "소") != bool(bat):
        return w

    if voice == HAPSYO:
        if bat:
            return stem + "습니다"
        made = _add_bieup(stem[-1])
        return (stem[:-1] + made + "니다") if made else w

    return stem + _TAIL[voice]


# ══════════════════════════════════════════════════════════
# 글 한 덩이 바꾸기
# ══════════════════════════════════════════════════════════
#
# ★ HTML 안쪽만 건드립니다. 태그(<b>, <p class="..">)는 그대로 둡니다 —
#   속성값에 손대면 화면이 깨집니다.
_TAGS = re.compile(r"<[^>]*>")

# 문장 끝 — 문장부호 앞이나, 글/태그가 끝나는 자리
_ENDING = re.compile(r"([가-힣]{2,})(?=\s*(?:[.!?…]|$))")


def _piece(text: str, voice: str) -> str:
    return _ENDING.sub(lambda m: _word(m.group(1), voice), text)


# ══════════════════════════════════════════════════════════
# 호칭
# ══════════════════════════════════════════════════════════
#
# ★ 컷 여러 곳이 호칭을 **"그대" 로 박아** 두고 있었습니다.
#   관점(lens_view)에는 자네·아저씨라고 적혀 있는데 본문은 전부
#   "그대에게", "그대가" 였습니다. 홍매파도 삼거리 노파도 청동자도요.
#
# ★ 「그대로」를 건드리면 안 됩니다.
#   그건 호칭이 아니라 '있는 그대로' 의 그대로입니다. 한 글자 차이로
#   "자네로 도오" 같은 말이 됩니다.
#
# ★ 조사를 같이 고쳐야 합니다.
#   뱅크는 「그대」(받침 없음) 기준으로 쓰여 있어서 "그대가 · 그대는 ·
#   그대를" 입니다. 받침 있는 호칭으로 바꾸면 **"당신가 · 손님는"** 이
#   됩니다. 바로 눈에 띄는 종류의 깨짐이라, 뒤따르는 조사까지 봅니다.
_JOSA = {"가": "이", "는": "은", "를": "을", "와": "과", "라": "이라"}
_YOU = re.compile(r"그대(?!로)([가는를와라])?")


def _batchim(word: str) -> bool:
    """마지막 글자에 받침이 있는가. 한글이 아니면 없는 것으로 본다."""
    b = _has_batchim(word[-1]) if word else None
    return bool(b)


def address(html: str, you: Optional[str]) -> str:
    """박아 둔 호칭을 그 캐릭터의 것으로 바꾼다. 조사도 같이 맞춘다."""
    if not html or not you or you == "그대":
        return html
    hard = _batchim(you)

    def sub(m):
        josa = m.group(1) or ""
        # ★ 「너가」는 비문입니다. 주격에서만 '네' 로 바뀝니다 —
        #   너를 · 너에게 · 너는 은 그대로 두고 '너가' 만 잡습니다.
        if you == "너" and josa == "가":
            return "네가"
        if hard and josa in _JOSA:
            josa = _JOSA[josa]
        return you + josa

    return _YOU.sub(sub, html)


def speak(html: str, voice: Optional[str]) -> str:
    """
    렌더된 HTML 의 **문장 끝 어미만** 그 캐릭터의 말투로 바꾼다.

    ★ 맨 마지막에 부릅니다. 뱅크는 하오체 한 벌로 두고 여기서 갈라
      쓰기 때문에, 문장을 스무 벌로 쓰지 않아도 목소리가 스물이 됩니다.
    """
    if not html or not voice or voice == HAO:
        return html
    out, last = [], 0
    for m in _TAGS.finditer(html):
        out.append(_piece(html[last:m.start()], voice))
        out.append(m.group(0))          # 태그는 그대로
        last = m.end()
    out.append(_piece(html[last:], voice))
    return "".join(out)
