# -*- coding: utf-8 -*-
"""
한 장의 **주인**. 고르기 · 차례 · 예산 · 처방 · 파는 말이 여기 한 자리.

★ 왜 이 자리가 필요한가 (2026-09-28)

  여태 고르는 자리가 **넷**이었습니다 —

      apps/web/components/FreeReadingDetail.tsx   FREE_DETAIL_IDS
      apps/web/app/pay/page.tsx                   cuts.filter(...)
      engine/report.apply_view                    차례
      engine/report.build_report                  tier 잠금

  화면이 고르니 서버는 자기가 무엇을 두 번 내보내는지 몰랐습니다.
  `freeRevelation` 이 `spine` 의 bite 를 1단계 머리로 쓰고, 근거 절이
  같은 컷을 또 펴서 **본문과 근거 줄이 통째로 두 번** 나갔습니다.

  이 집이 완료율에서 겪은 자리와 같습니다 — 「화면도 라우터도 완료율을
  제 손으로 세지 마세요」. 그 사고는 아무도 안 죽고 숫자만 틀립니다.
"""
from __future__ import annotations

from typing import Optional

from .. import guard as guard_mod
from . import axes as axes_mod
from . import render as render_mod
from .claim import Budget, Claim, ClaimError, Page, Prescription, count_word

#: 감정 곡선 — 아픈 말 → 위로 → 셈 → 때 → 희망.
#:
#: ★ 미뤄 둔 컷으로 끝내지 마시오. 기억은 마지막이 지배합니다.
#  아픈 말 → 앞뒤 → 얼굴·틀·철 → 위로 → 셈 → 때 → 희망
CURVE = ("scale", "weave", "shadow", "face", "frame", "season",
         "lack", "missing", "alone", "rarity", "birthday",
         "hold", "clash", "tied", "vault", "marks",
         "forebears", "palace", "turn", "decades", "hindsight",
         "counter", "year", "helper")

#: 부록으로 내리는 축 — 명식·계산 근거.
APPENDIX = ("chart", "unknown_hour")

#: 오늘 할 하나 — **축마다 한 줄**입니다.
#:
#: ★ 고민마다 일곱 벌을 쓰지 않습니다. 물어보신 자리 낱말은 슬롯이 받고,
#:   무엇을 볼지는 **축**이 정합니다. 지금 이 집의 처방이 44개였던
#:   까닭은 컷마다 제 처방을 달았기 때문이오.
DO = {
    # ★ 고민이 일곱인데 **돈 꼴을 그대로** 썼습니다 (2026-09-28).
    #   「사람」 을 물은 손님에게 「사람 약속 하나에 금액·지급일·범위를
    #   적으시오」 가 나갔습니다. 이 축은 일곱 고민에 다 서는 자리라
    #   처방도 **어느 고민에나 맞는 말**이어야 하오.
    "scale": ("{letters} 가운데 {group}가 {n} 사람이니, {word}에 관한 "
              "약속 하나에 무엇을·언제까지·어디까지를 적으시오.",
              "지금 {age}이니, 밤에 볼 것은 아낀 크기가 아니라 그 문장이 "
              "남았는가요.",
              "적을 약속이 아직 없으면 {letters} 가운데 쥐는 글자가 몇인지가 "
              "오늘의 답이오."),
    "shadow": ("잘하는 일로 오늘 한 것 하나와 그 때문에 못 한 것 하나를 "
               "나란히 적으시오.",
               "밤에 볼 것은 어느 쪽이 더 컸는가요. {letters}에서 나온 "
               "앞뒤요.",
               "못 한 것이 없던 날이면 그 힘이 오늘은 짐이 아니었소."),
    "face":  ("받쳐 주는 칸이 {n} 사람이니, 오늘 미룬 것 하나와 밀어붙인 "
              "것 하나를 적으시오.",
              "밤에 볼 것은 어느 쪽이 더 편했는가요. 지금 {age}요.",
              "둘 다 없던 날이면 {letters}를 다시 볼 것도 없는 날이오."),
    "lack":  ("겉에 {n} 살아온 사람이니, 설명하다 만 그 얘기를 한 사람에게 "
              "한 문장으로 적으시오.",
              "밤에 볼 것은 상대가 알아들었는가가 아니라 보냈는가요. "
              "지금 {age}요.",
              "보낼 사람이 없으면 {letters} 옆에 그 문장만 남는 날이오."),
    "hold":  ("두꺼운 쪽이 {n} 사람이니, 늘 쓰던 그 방법 말고 작게 시험할 "
              "한 가지를 적으시오.",
              "밤에 볼 것은 결과가 아니라 시험을 했는가요.",
              "시험할 것이 안 떠오르면 늘 쓰던 방법이 아직 통하는 것이오."),
    "vault": ("남은 것을 어디에 넣어 두는지 한 줄로 적으시오.",
              "밤에 볼 것은 남은 액수가 아니라 넣어 둔 곳이오. 비는 글자는 "
              "{letters} 쪽이오.",
              "넣어 둘 곳이 없다는 것이 오늘의 답일 수 있소."),
    "palace": ("지금 {age}이니, 이 나이에 이래도 되나 싶던 그 일을 한 줄로 "
               "적으시오.",
               "밤에 볼 것은 답이 아니라 적었는가요.",
               "떠오르는 일이 없으면 그 칸은 지금 조용한 것이오."),
    "turn":  ("지금 {age}이니, 다음 칸까지 남은 햇수를 적고 그 사이에 할 "
              "하나를 고르시오.",
              "밤에 볼 것은 계획이 아니라 햇수를 적었는가요.",
              "할 것이 안 떠오르면 햇수만 적어 두는 것으로 되오."),
    "year":  ("올해 안에 끝낼 하나를 적고 날짜를 붙이시오.",
              "밤에 볼 것은 끝냈는가가 아니라 날짜를 붙였는가요.",
              "날짜를 못 붙이겠으면 올해 일이 아닌 것이오."),
    "helper": ("돕는 글자가 {n} 있는 사람이니, 도움을 청할 사람·시간·정보 가운데 "
               "하나를 적으시오.",
               "밤에 볼 것은 도움이 왔는가가 아니라 청했는가요.",
               "청할 데가 없다는 것부터가 적어 둘 일이오."),
}



def _break_runs(rows: list, limit: int) -> list:
    """
    같은 박자가 잇달지 않게 **차례만** 바꾼다.

    ★ 리듬은 글을 더 써서 만드는 것이 아니오 — 차례로 만드오.
      감정 곡선은 지키고, 같은 박자가 문턱을 넘을 때만 뒤에서 하나를
      끌어옵니다. 못 끌어오면 그대로 둡니다 (억지로 섞으면 곡선이 깨짐).
    """
    out: list = []
    pool = list(rows)
    while pool:
        run = 1
        for i in range(len(out) - 1, -1, -1):
            if out[i].rhythm and out[i].rhythm == pool[0].rhythm:
                run += 1
            else:
                break
        if run > limit:
            alt = next((i for i, c in enumerate(pool[1:], 1)
                        if c.rhythm != pool[0].rhythm), None)
            if alt is not None:
                pool.insert(0, pool.pop(alt))
        out.append(pool.pop(0))
    return out


def _score(c: Claim) -> tuple:
    """
    고르는 자 — 물어보신 자리에 걸리는가가 먼저, 그 다음이 드묾.

    ★ 희소도를 골라 담지 마시오. 축은 미리 정해져 있고(`axes.PRODUCERS`)
      여기서는 **차례만** 정합니다.
    """
    rare = 0.0
    if c.pop:
        rare = max(0.0, 1.0 - c.pop)
    return (c.asked, rare, -CURVE.index(c.axis) if c.axis in CURVE else 0)


_LEVEL = {"free": 0, "9900": 1, "12900": 2, "15900": 3, "19900": 4}


def build(f, concern: str, tier: str = "free",
          lens_id: Optional[str] = None) -> Page:
    """
    한 장을 짠다.

    돌려주는 것은 `Page` 요 — 화면이 고를 것이 없습니다. 차례·잠금·
    파는 자리까지 여기서 정해져 나갑니다.
    """
    budget = Budget.of(tier)
    level = _LEVEL[tier]
    group, word = axes_mod._axis_of(concern, getattr(f, "sex", ""))

    pool = axes_mod.build(f, concern)
    open_now = [c for c in pool if _LEVEL[c.needs] <= level]
    locked = [c for c in pool if _LEVEL[c.needs] > level]

    appendix = [c for c in open_now if c.axis in APPENDIX]
    body_pool = [c for c in open_now if c.axis not in APPENDIX]

    # ── 고르기: 예산만큼. 물어보신 자리에 걸리는 것부터 ──
    body_pool.sort(key=_score, reverse=True)
    picked = body_pool[:budget.cuts]

    # ── 차례: 감정 곡선 ──
    picked.sort(key=lambda c: CURVE.index(c.axis) if c.axis in CURVE else 99)

    # ── 말로 옮기기 ──
    render_mod.new_page()          # 같은 글자 그림을 한 장에 한 번만
    for c in list(picked) + list(appendix):
        html = render_mod.body(c, f, concern, word)
        object.__setattr__(c, "body", guard_mod.enforce(
            html, {"cut": "reading:%s" % c.axis}))
        object.__setattr__(c, "rhythm", render_mod.RHYTHM.get(c.axis, ""))

    # ★ 모양이 없어 못 펴진 주장은 **안 냅니다.**
    picked = [c for c in picked if c.body]
    picked = _break_runs(picked, budget.same_rhythm)

    # ── 한 장의 주장 하나 ──
    head = next((c for c in picked if c.kind == "verdict"), None)
    thesis = head.verdict if head else "%s 자리를 세어 본 자리" % word

    # ── 오늘 할 하나 — **한 개** ──
    # ★ 처방이 **사람마다 같았습니다** (2026-09-28). 표가 축으로만 열려서
    #   아홉 줄이 스무 명에게 글자 그대로 나갔습니다 — 겹침 100%.
    #   슬롯을 셈으로 채웁니다: 센 값 · 나이 · 실제 글자.
    from .claim import count_word as _cw
    rx = None
    for c in picked:
        row = DO.get(c.axis)
        if not row:
            continue
        k = c.counted[0] if c.counted else None
        # ★ 0 이면 `count_word` 가 **맺는 말**을 돌려줍니다 — 「쥐는 글자가
        #   한 자도 없소인 사람이니」 가 120장에 나갔습니다. 이어지는 꼴로
        #   짓습니다: 0 → 「없는」 · 그밖 → 「한 자인」.
        if k is None:
            n_slot = "모르는"
        elif k.값 == 0:
            n_slot = "없는"
        else:
            n_slot = "%s인" % _cw(k.값, k.단위)
        # ★ 묶음 이름도 슬롯이오 (2026-09-28). 「쥐는 글자」 를 박아 두니
        #   일을 물은 손님에게도 「쥐는 글자」 가 나갔습니다 — 일은
        #   「누르고 잡아 주는 글자」 요.
        from .render import PLAIN_GROUP as _PG
        slot = {
            "word": word,
            "group": _PG.get(k.무엇, k.무엇) if k else "그 글자",
            "n": n_slot,
            "age": _cw(getattr(f, "age", 0), "살"),
            "letters": " · ".join(p["gz"] for p in f.pillars),
        }
        rx = Prescription(한가지=row[0].format(**slot),
                          확인=row[1].format(**slot),
                          갈림=row[2].format(**slot), 축=c.axis)
        break

    # ── 파는 말은 **한 곳** ──
    offer_at = None
    if locked and picked:
        offer_at = picked[-1].axis

    page = Page(thesis=thesis, claims=picked, prescription=rx,
                budget=budget, offer_at=offer_at, appendix=appendix,
                derived=render_mod.derived(f))
    page.check()

    # ── 예산: 넘치면 **고릅니다** (자르지 않습니다) ──
    while page.chars > budget.chars and len(page.claims) > 3:
        drop = min(page.claims, key=lambda c: (c.asked, len(c.body)))
        page.claims.remove(drop)

    page.check()
    return page


def locked_list(f, concern: str, tier: str = "free") -> list:
    """
    무엇이 잠겼는지 — **제목과 센 값만.** 본문은 안 내려보냅니다.

    ★ 제목을 범주로 두지 마시오. 잠긴 컷 제목은 값을 부르는 표면이오 —
      목차가 아니라 **주장**입니다. `verdict` 가 이미 그 모양이오.
    """
    level = _LEVEL[tier]
    out = []
    for c in axes_mod.build(f, concern):
        if _LEVEL[c.needs] <= level:
            continue
        out.append({"axis": c.axis, "title": c.verdict,
                    "counted": c.counted[0].수 if c.counted else "",
                    "needs": c.needs})
    return out
