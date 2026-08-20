"""
오늘의 일진 — docs/02 §5 GET /v1/daily

그날의 일간지를 실제로 계산해 내 일간과의 관계를 봅니다.
**무슨 일이 일어난다고 말하지 않습니다.** 관계와 점수만 내놓습니다.
(단정·시점 지시는 guard 에서도 막힙니다. docs/11)
"""
from __future__ import annotations

from datetime import date

from .calendar import day_ganji
from .constants import CHUNG, CONTROLS, ELEMENT_OF_GAN, GENERATES, element_of
from .bank import element_word

# 점수 가중 — 조정 가능한 파라미터
BASE = 58
BONUS_YONGSIN = 26
PENALTY_STRONG = -14
PENALTY_CHUNG = -20
BONUS_SAME_JI = 8
FLOOR, CEIL = 12, 96

RELATION_TEXT = {
    "같은 기운이 겹치는": "같은 기운이 하나 더 놓이는 날이오. 밀어붙이기는 쉽고, 물러서기는 어렵소.",
    "기운이 빠져나가는": "내놓는 쪽으로 기울어지는 날이오. 쏟고 나면 비는 걸 염두에 두시오.",
    "눌리는": "위에서 누르는 기운이 있는 날이오. 굳이 맞서지 않아도 되오.",
    "내가 다스리는": "손에 잡히는 쪽으로 도는 날이오. 벌이는 것보다 정리가 낫소.",
    "기운을 받는": "받는 쪽으로 도는 날이오. 도움을 청하기 어렵지 않은 날이지.",
}


def relation(day_el: str, me_el: str) -> str:
    if day_el == me_el:
        return "같은 기운이 겹치는"
    if GENERATES[me_el] == day_el:
        return "기운이 빠져나가는"
    if CONTROLS[me_el] == day_el:
        return "내가 다스리는"
    if CONTROLS[day_el] == me_el:
        return "눌리는"
    return "기운을 받는"


def build_daily(f, on: date | None = None) -> dict:
    on = on or date.today()
    gan, ji = day_ganji(on)
    el = ELEMENT_OF_GAN[gan]
    me = ELEMENT_OF_GAN[f.day_gan]
    rel = relation(el, me)

    score = BASE
    if el == f.yongsin:
        score += BONUS_YONGSIN
    if el == f.strong_el:
        score += PENALTY_STRONG
    if ji == CHUNG[f.day_ji]:
        score += PENALTY_CHUNG
    if ji == f.day_ji:
        score += BONUS_SAME_JI
    score = max(FLOOR, min(CEIL, score))

    # 한자 뒤 조사는 읽는 법에 따라 갈린다. 조사가 붙지 않는 형태로 쓴다.
    notes = []
    if el == f.yongsin:
        notes.append("오늘 천간이 용신 %s에 해당하오." % element_word(f.yongsin))
    if ji == CHUNG[f.day_ji]:
        notes.append("일지 %s — 오늘 지지와 부딪히는 날이오." % f.day_ji)
    elif ji == f.day_ji:
        notes.append("일지 %s — 오늘 지지와 겹치오." % f.day_ji)

    return {
        "date": on.isoformat(),
        "gz": gan + ji,
        "gan": gan,
        "ji": ji,
        "element": el,
        "relation": rel,
        "score": score,
        "text": RELATION_TEXT[rel],
        "notes": notes,
        "source": "%s일간 ↔ 오늘 %s(%s)" % (f.day_gan, gan + ji, element_word(el)),
        "free": True,
    }
