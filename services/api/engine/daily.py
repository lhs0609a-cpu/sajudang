"""
오늘의 일진 — docs/02 §5 GET /v1/daily

그날의 일간지를 실제로 계산해 내 일간과의 관계를 봅니다.
**무슨 일이 일어난다고 말하지 않습니다.** 관계와 점수만 내놓습니다.
(단정·시점 지시는 guard 에서도 막힙니다. docs/11)
"""
from __future__ import annotations

from datetime import date

from . import terms as terms_mod
from .calendar import day_ganji
from .constants import CHUNG, CONTROLS, ELEMENT_OF_GAN, GENERATES, element_of
from .bank import bank, born_season, element_word

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


# 일진 화면이 실제로 쓰는 어려운 말. 화면에 박힌 것(일진 · 용신)까지
# 함께 냅니다 — 손님은 엔진 글과 화면 글을 갈라 읽지 않습니다.
DAILY_TERMS = ("일진", "일간", "일지", "지지", "신강", "신약", "용신", "충")


def _pictures(body: list, notes: list, f) -> str:
    """
    이 일진에서 나온 말의 그림 한 줄을 상자로 묶는다.

    ★ 왜 여기에도 다나

      일진은 **값 없이 매일** 오는 자리라 처음 오는 사람이 어려운 말을
      여기서 처음 만납니다. 그런데 풀이가 한 줄도 없었습니다 —
      「단단히 가르는 일간이라」 「신강 · 겨울생」 이 그대로 지나갔습니다.
      리포트 컷은 `terms.picture_box` 로 이미 이걸 합니다.
    """
    said = " ".join(list(body) + list(notes) + [f.strength or ""])
    # 일진 · 일간 · 용신은 화면과 근거 줄에 **늘** 있습니다.
    used = [t for t in DAILY_TERMS
            if t in said or t in ("일진", "일간", "용신")]
    return terms_mod.picture_box(used)


def build_daily(f, on: date | None = None) -> dict:
    on = on or date.today()
    gan, ji = day_ganji(on)
    el = ELEMENT_OF_GAN[gan]
    me = ELEMENT_OF_GAN[f.day_gan]
    rel = relation(el, me)

    # ★ 점수는 **셈한 것을 그대로 말합니다.**
    #
    #   화면이 "오늘 기운 76/100 — 적중률이 아니라 배치 점수요" 라고만
    #   적고 있었습니다. 적중률이 아니라는 건 맞는 말인데, **그럼 뭔지는
    #   안 말했습니다.** 손님에게 76은 아무 뜻도 없는 수가 됩니다.
    #   부정만 하고 정의를 안 주던 자리입니다.
    #
    #   여기는 근거 대는 집이니 방어가 아니라 **셈법 공개**로 처리합니다.
    #   무엇이 몇 점을 올리고 내렸는지 그대로 내려보냅니다.
    score = BASE
    why = [{"k": "기준", "v": BASE, "t": "누구나 여기서 시작하오"}]
    if el == f.yongsin:
        score += BONUS_YONGSIN
        why.append({"k": "용신", "v": BONUS_YONGSIN,
                    "t": "오늘 천간이 그대에게 드는 %s요" % element_word(f.yongsin)})
    if el == f.strong_el:
        score += PENALTY_STRONG
        why.append({"k": "넘치는 기운", "v": PENALTY_STRONG,
                    "t": "이미 많은 %s가 오늘 또 드오" % element_word(f.strong_el)})
    if ji == CHUNG[f.day_ji]:
        score += PENALTY_CHUNG
        why.append({"k": "충", "v": PENALTY_CHUNG,
                    "t": "일지 %s와 오늘 지지가 부딪히오" % f.day_ji})
    if ji == f.day_ji:
        score += BONUS_SAME_JI
        why.append({"k": "겹침", "v": BONUS_SAME_JI,
                    "t": "일지 %s와 오늘 지지가 같소" % f.day_ji})
    raw = score
    score = max(FLOOR, min(CEIL, score))
    if score != raw:
        why.append({"k": "한도", "v": score - raw,
                    "t": "%d~%d 밖으로는 안 나가오" % (FLOOR, CEIL)})

    # 한자 뒤 조사는 읽는 법에 따라 갈린다. 조사가 붙지 않는 형태로 쓴다.
    notes = []
    if el == f.yongsin:
        notes.append("오늘 천간이 용신 %s에 해당하오." % element_word(f.yongsin))
    if ji == CHUNG[f.day_ji]:
        notes.append("일지 %s — 오늘 지지와 부딪히는 날이오." % f.day_ji)
    elif ji == f.day_ji:
        notes.append("일지 %s — 오늘 지지와 겹치오." % f.day_ji)

    # ── 본문을 곱한다 ────────────────────────────────────
    #
    # ★ 일진은 **매일, 다수에게 동시에** 나갑니다. 그래서 캡처를 나란히
    #   놓고 비교하기 가장 쉬운 자리입니다. 전에는 관계 5가지가 상한이라
    #   같은 날 다섯 명 중 한 명꼴로 글자 하나 안 틀리고 같았습니다.
    #
    #   반복 자체가 위험한 게 아닙니다 — Barnum 효과 연구가 말하듯 사람은
    #   여럿이 받은 문장도 제 얘기로 느낍니다. **다만 개인화되었다고 믿을
    #   때만** 그렇습니다. 진짜 위험은 반복이 들통나는 것입니다.
    #   알림 채널을 붙이기 전에 손봐야 하는 이유가 이것입니다.
    #
    #   곱하는 축: 관계(5) × 내 일간(10) × 신강약(3) × 태어난 계절(4)
    B = bank()
    season = born_season(f)
    body = [RELATION_TEXT[rel], B["DAILY_ME"][f.day_gan],
            B["DAILY_TONE"][f.strength], B["DAILY_SEASON"][season],
            B["DAILY_CARE"][f.yongsin]]

    return {
        "date": on.isoformat(),
        "gz": gan + ji,
        "gan": gan,
        "ji": ji,
        "element": el,
        "relation": rel,
        "score": score,
        # 이 점수가 무엇을 센 것인가. 화면이 그대로 펼쳐 보입니다.
        "score_why": why,
        "score_says": ("오늘 일진과 그대 여덟 글자가 맞물린 자리를 센 것이오. "
                       "좋고 나쁨이 아니라 부딪히는 수요."),
        "text": " ".join(body),
        "lines": body,
        "notes": notes,
        "source": "%s일간 ↔ 오늘 %s(%s) · %s · %s생"
                  % (f.day_gan, gan + ji, element_word(el), f.strength, season),
        # 이 화면에서 나온 어려운 말의 **그림 한 줄**. 리포트 컷이
        # 하는 것과 같은 상자입니다 — 모르는 말을 만난 그 자리에 둡니다.
        "terms_html": _pictures(body, notes, f),
        "statement_id": "daily:%s:%s:%s:%s:%s" % (rel, f.day_gan, f.strength,
                                                  season, f.yongsin),
        "free": True,
    }
