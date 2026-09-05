"""
결합 축의 추가 입력 — docs/07 §결합 축

★ 왜 이 모듈이 생겼는가

  캐릭터를 바꿔 또 사면 같은 컷을 순서만 바꿔 받았습니다. 처음에는
  추천 문제라 보고 렌즈 보완(lens.complement)을 붙였는데, 재보니 새
  문장이 평균 3.27 → 3.56개, **+0.29개뿐**이었습니다.

  병목은 추천이 아니었습니다. docs/07 이 이미 적어 둔 대로

      입력 데이터가 다를 때만 진짜 다른 상품입니다.

  여덟 글자는 하나뿐입니다. 관점을 아무리 적어도 입력이 같으면
  리포트는 순서만 바뀝니다. 스무 명 중 **열둘**이 추가 입력 없이
  돌고 있었습니다.

★ 무엇을 저장하는가 — 아무것도 저장하지 않습니다

  이 모듈은 요청에 실려 온 값으로 컷을 만들고 버립니다.
  특히 **상대 사주는 제3자의 생년월일**입니다. 본인 동의 없이 받은
  것이라 저장하지 않습니다 (docs/11). 필요하면 매번 다시 받습니다.

★ 얼굴 사진(photo)은 여기 없습니다
  생체인식정보라 저장이 금지돼 있습니다. 저장 없이 처리하는 설계를
  먼저 정해야 합니다. lens.BLOCKED_INPUTS 를 보세요.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from . import guard
from .bank import element_word, josa
from .constants import CHUNG, HAP, ten_god

SEED = Path(__file__).resolve().parents[3] / "seed"


@lru_cache(maxsize=1)
def text() -> dict:
    return json.loads((SEED / "extras.json").read_text("utf-8"))


class ExtraInputError(ValueError):
    """추가 입력이 형식에 안 맞음. 지어내지 않고 터뜨린다."""


# ══════════════════════════════════════════════════════════
# 관계 — 상대 사주
# ══════════════════════════════════════════════════════════
def _partner_features(p: dict):
    """상대 명식을 계산한다. **저장하지 않는다.**"""
    from .calendar import build_chart
    from .features import build_features
    try:
        known = bool(p.get("hour_known", False))
        ch = build_chart(
            int(p["year"]), int(p["month"]), int(p["day"]),
            int(p["hour"]) if known else None,
            int(p.get("minute", 0)) if known else None,
            p.get("sex", "F"), hour_known=known,
            city=p.get("city", "서울"))
    except KeyError as e:
        raise ExtraInputError("상대 생년월일에서 %s 이(가) 비었소." % e)
    except (TypeError, ValueError) as e:
        # calendar.check_birth_date 가 이미 우리말로 말합니다. 덧붙이기만 합니다.
        raise ExtraInputError("상대 쪽 날이 어긋났소 — %s" % e)
    return build_features(ch)


def _ji_relation(mine: str, theirs: str) -> str:
    if theirs == mine:
        return "같음"
    if CHUNG.get(mine) == theirs:
        return "충"
    if HAP.get(mine) == theirs:
        return "합"
    return "무관"


def _fill_relation(f, pf) -> tuple[str, str]:
    """(관계 키, 그 관계가 가리키는 오행)"""
    if pf.elements[f.weak_el] >= 2.0:
        return "채움", f.weak_el
    if pf.elements[f.weak_el] == 0.0:
        return "같이없음", f.weak_el
    if pf.strong_el == f.strong_el:
        return "넘침", f.strong_el
    return "무관", f.weak_el


def partner_cut(f, p: dict) -> dict:
    """
    두 명식의 배치.

    ★ 잘 되겠다 안 되겠다를 말하지 않습니다.
      재회 가능/불가 판정·시점 확정·기다림 종용은 금지입니다 (docs/11).
      어디서 힘이 드는 배치인지만 짚습니다.
    """
    T = text()
    pf = _partner_features(p)
    tg = ten_god(pf.day_gan, f.day_gan)
    ji = _ji_relation(f.day_ji, pf.day_ji)
    fill, fill_el = _fill_relation(f, pf)

    body = (
        '<p class="tale">그대 일간은 <b>%s</b>, 상대 일간은 <b>%s</b>. '
        '그대를 기준으로 보면 <b>%s</b>입니다.</p>'
        '<p class="tale">%s</p>'
        '<p class="tale">%s</p>'
        '<p class="tale">%s</p>'
        '<p class="sm">%s</p>'
        % (f.day_gan, pf.day_gan, tg,
           T["PARTNER_TEN_GOD"][tg],
           T["PARTNER_JI"][ji],
           T["PARTNER_FILL"][fill].format(el_word=element_word(fill_el)),
           T["PARTNER_CLOSE"]))
    return {
        "id": "partner", "title": "상대와의 배치",
        "source": "%s일간 ↔ %s일간 · 일지 %s/%s · %s"
                  % (f.day_gan, pf.day_gan, f.day_ji, pf.day_ji, tg),
        "html": guard.enforce(body, {"cut": "partner"}),
        "min_level": 1,
        "statement_id": "partner:%s:%s:%s" % (tg, ji, fill),
    }


# ══════════════════════════════════════════════════════════
# 맥락 — 지금 무엇을 하고 있는가
# ══════════════════════════════════════════════════════════
#
# ★ 자유 입력을 받지 않습니다.
#   자유 입력은 개인정보가 섞여 들어오고, 가드가 볼 수 없는 텍스트가
#   리포트에 실릴 길을 냅니다. 고르는 값만 받습니다.

def _since_bucket(months: int) -> str:
    if months < 3:
        return "0"
    if months < 6:
        return "1"
    if months < 12:
        return "2"
    return "3"


def context_cut(f, c: dict) -> dict:
    T = text()
    sit = str(c.get("situation") or "")
    if sit not in T["SITUATION"]:
        raise ExtraInputError(
            "모르는 상황: %r (고를 수 있는 것: %s)"
            % (sit, ", ".join(T["SITUATION"])))
    stance = str(c.get("stance") or "")
    if stance not in T["STANCE"]:
        raise ExtraInputError(
            "모르는 태도: %r (고를 수 있는 것: %s)"
            % (stance, ", ".join(T["STANCE"])))
    try:
        months = max(0, int(c.get("since_months", 0)))
    except (TypeError, ValueError):
        raise ExtraInputError("since_months 는 숫자여야 합니다")

    s = T["SITUATION"][sit]
    bucket = _since_bucket(months)

    # 그 일이 쓰는 기운이 이 사람에게 모자란 것인가, 넘치는 것인가
    if s["el"] == f.yongsin or s["el"] in f.weak_els:
        fit = "용신"
    elif s["el"] == f.strong_el:
        fit = "과잉"
    else:
        fit = "보통"

    body = (
        '<p class="tale">지금 <b>%s</b>이라 하셨습니다.</p>'
        '<p class="tale">%s</p>'
        '<p class="tale">%s</p>'
        '<p class="tale">%s</p>'
        '<p class="tale">%s</p>'
        % (s["label"], T["SINCE"][bucket], s["t"], T["STANCE"][stance],
           T["SITUATION_FIT"][fit]))
    return {
        "id": "context", "title": "지금 하고 있는 일",
        "source": "%s · %d개월 · %s · %s 기운(%s)"
                  % (s["label"], months, stance, element_word(s["el"]), fit),
        "html": guard.enforce(body, {"cut": "context"}),
        "min_level": 1,
        "statement_id": "context:%s:%s:%s:%s" % (sit, bucket, stance, fit),
    }


# ══════════════════════════════════════════════════════════
# 검사 — 혈액형
# ══════════════════════════════════════════════════════════
def blood_cut(f, b: dict) -> dict:
    """
    ★ 재미 상품이지만 근거를 지어내지는 않습니다.
      혈액형과 성격의 관계는 여러 번 조사됐고 이렇다 할 게 안 나왔습니다.
      그 사실을 **먼저** 말하고 시작합니다. 그게 이 캐릭터의 첫 대사이기도
      합니다 — "피는 무슨 형이오? …믿지는 마시고."
    """
    T = text()
    t = str(b.get("type") or "").upper()
    if t not in T["BLOOD"]:
        raise ExtraInputError("혈액형은 A · B · O · AB 중 하나입니다: %r" % (t,))
    body = ('<p class="sm">%s</p><p class="tale">%s</p><p class="tale">%s</p>'
            % (T["BLOOD_DISCLAIMER"], T["BLOOD"][t], T["BLOOD_VS"][f.strength]))
    return {
        "id": "blood", "title": "피와 글자",
        "source": "%s형 ↔ %s %d" % (t, f.strength, f.strength_score),
        "html": guard.enforce(body, {"cut": "blood"}),
        "min_level": 0,
        "statement_id": "blood:%s:%s" % (t, f.strength),
    }


# ══════════════════════════════════════════════════════════
# 검사 — 이미지 고르기
# ══════════════════════════════════════════════════════════
def image_cut(f, i: dict) -> dict:
    T = text()
    pick = str(i.get("pick") or "")
    if pick not in T["IMAGE"]:
        raise ExtraInputError(
            "모르는 그림: %r (고를 수 있는 것: %s)" % (pick, ", ".join(T["IMAGE"])))
    im = T["IMAGE"][pick]
    if im["el"] in f.weak_els:
        vs = "같음"
    elif im["el"] == f.strong_el:
        vs = "넘침"
    else:
        vs = "다름"
    body = ('<p class="tale">%s</p><p class="tale">%s</p>'
            % (im["t"], T["IMAGE_VS"][vs]))
    return {
        "id": "image", "title": "고른 그림",
        "source": "%s · %s 기운 ↔ 약 %s / 강 %s"
                  % (im["label"], element_word(im["el"]),
                     element_word(f.weak_el), element_word(f.strong_el)),
        "html": guard.enforce(body, {"cut": "image"}),
        "min_level": 0,
        "statement_id": "image:%s:%s" % (pick, vs),
    }


# ══════════════════════════════════════════════════════════
# 술수 — 카드 석 장
# ══════════════════════════════════════════════════════════
def cards_cut(f, c: dict) -> dict:
    T = text()
    picks = list(c.get("picks") or [])
    if len(picks) != 3:
        raise ExtraInputError("패는 석 장입니다 (받은 것 %d장)" % len(picks))
    for p in picks:
        if p not in T["CARD"]:
            raise ExtraInputError(
                "모르는 패: %r (있는 것: %s)" % (p, ", ".join(T["CARD"])))
    rows = "".join(
        '<p class="tale"><b>%s</b> — %s. %s</p>'
        % (T["CARD_SLOT"][n], T["CARD"][p]["label"], T["CARD"][p]["t"])
        for n, p in enumerate(picks))
    body = ('<p class="sm">%s</p>%s<p class="tale">%s</p>'
            % (T["CARD_DISCLAIMER"], rows, T["CARD_VS"]))
    return {
        "id": "cards", "title": "뽑은 석 장",
        "source": " · ".join(T["CARD"][p]["label"] for p in picks),
        "html": guard.enforce(body, {"cut": "cards"}),
        "min_level": 0,
        "statement_id": "cards:%s:%s" % (",".join(picks),
                                         "same" if len(set(picks)) < 3 else "diff"),
    }


# ══════════════════════════════════════════════════════════
# 배선
# ══════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════
# 만남 — 누구랑, 어떻게 만났는가
# ══════════════════════════════════════════════════════════
#
# ★ 손님이 짚은 것 (2026-09-04)
#
#   "연애 고민이면 누구랑 고민인지 어떻게 만났는지 그런 거 싹 해서…"
#
# ★ 맞히지 않소 — **맞대 보오**
#
#   여덟 글자는 사람을 읽는 것이지 사건을 읽는 것이 아니오. 「어떻게
#   만났는가」 를 글자에서 뽑을 수는 없소.
#
#   그러나 대 볼 수는 있소. 짝을 보는 글자가 **어느 궁에 앉았는지**는
#   이미 셈이 끝나 있소 (engine/pattern._group_seats). 손님이 적은
#   결과 글자가 가리키는 결이 **겹치면 겹친다고, 어긋나면 어긋난다고**
#   말하는 것이오. 이 집이 넉 자에 하는 것과 같은 구조요.
#
# ★ 재회는 판정하지 않소
#
#   「헤어진 사람」 을 골라도 다시 될지 안 될지·언제인지·기다리라는
#   말을 하지 않소 (docs/11). 그대 자리만 보오.
#
# ★ 자유 입력은 안 받소. 정해진 칸으로만 받소.
def meet_cut(f, m: dict) -> dict:
    from . import pattern as _pattern
    T = text()
    who = str(m.get("who") or "")
    how = str(m.get("how") or "")
    if who not in T["MEET_WHO"]:
        raise ExtraInputError(
            "모르는 사이: %r (고를 수 있는 것: %s)"
            % (who, ", ".join(T["MEET_WHO"])))
    if how not in T["MEET_HOW"]:
        raise ExtraInputError(
            "모르는 만남: %r (고를 수 있는 것: %s)"
            % (how, ", ".join(T["MEET_HOW"])))

    grp = _pattern.spouse_group(f)
    seats = _pattern._group_seats(f, grp) if grp else []
    # 짝 글자가 앉은 자리 — 여럿이면 가장 무거운 자리(월주)부터 보오.
    order = ["월주", "일주", "년주", "시주"]
    seat = next((x for x in order if x in seats), "")
    said = T["MEET_HOW"][how]["seat"]

    if not grp:
        # 성별을 모르면 짝 글자를 못 정하오. 지어내지 않소.
        match = '<p class="tale">성별을 안 적으셔서 짝을 보는 글자를 ' \
                '정하지 못했소. 여기서는 적으신 것만 두고 보겠소.</p>'
        key = "nosex"
    elif not seat:
        match = ('<p class="tale">짝을 보는 <b>%s</b>이 여덟 글자에 '
                 '안 보이오. 그러니 적으신 결이 <b>글자보다 앞서</b> '
                 '있는 것이오 — 그대가 만든 자리라는 뜻이오.</p>' % grp)
        key = "none"
    elif seat == said:
        match = '<p class="tale">%s</p>' % T["MEET_SAME"][seat]
        key = "same:%s" % seat
    else:
        match = '<p class="tale">%s</p>' % T["MEET_ELSE"][seat]
        key = "else:%s>%s" % (seat, said)

    body = ('<p class="tale">%s</p>'
            '<p class="cnt"><b>적으신 것 — %s · %s</b></p>'
            '%s'
            '<p class="sm">여기 적으신 것은 <b>남기지 않소</b>. '
            '셈하고 버리오.</p>'
            % (T["MEET_WHO_SAY"][who],
               T["MEET_WHO"][who]["label"], T["MEET_HOW"][how]["label"],
               match))
    return {
        "id": "meet", "title": "만난 결과 글자",
        "source": "%s %s · 적은 결 %s%s"
                  % (grp or "짝 자리", seat or "없음", said,
                     " · 겹침" if seat == said else ""),
        "html": guard.enforce(body, {"cut": "meet"}),
        "min_level": 1,
        "statement_id": "meet:%s:%s:%s" % (who, how, key),
    }


BUILDERS = {
    "partner": partner_cut,
    "meet": meet_cut,
    "context": context_cut,
    "blood": blood_cut,
    "image": image_cut,
    "cards": cards_cut,
}


def build(f, need: Optional[str], extras: Optional[dict]) -> Optional[dict]:
    """
    이 캐릭터가 받아야 하는 추가 입력으로 컷을 하나 만든다.

    need    lens.required_input(lens_id)
    extras  요청에 실려 온 추가 입력 {"partner": {...}} 등

    입력이 없으면 None — 컷을 지어내지 않습니다. 화면은 "이 캐릭터는
    무엇을 더 받아야 하는지" 를 보고 물어보면 됩니다.
    """
    if not need or need not in BUILDERS:
        return None
    payload = (extras or {}).get(need)
    if not payload:
        return None
    return BUILDERS[need](f, payload)


def choices() -> dict:
    """화면이 고르게 보여줄 목록. 문장 원문은 내려보내지 않습니다."""
    T = text()
    return {
        "situation": [{"id": k, "label": v["label"]}
                      for k, v in T["SITUATION"].items()],
        # 만남 — 누구랑 · 어떻게. 자유 입력은 안 받소.
        "meet_who": [{"id": k, "label": v["label"]}
                     for k, v in T["MEET_WHO"].items()],
        "meet_how": [{"id": k, "label": v["label"]}
                     for k, v in T["MEET_HOW"].items()],
        "stance": [{"id": "push", "label": "밀어붙이는 중"},
                   {"id": "hold", "label": "버티는 중"},
                   {"id": "let", "label": "놓으려는 중"}],
        "blood": ["A", "B", "O", "AB"],
        "image": [{"id": k, "label": v["label"]} for k, v in T["IMAGE"].items()],
        "cards": [{"id": k, "label": v["label"]} for k, v in T["CARD"].items()],
    }
