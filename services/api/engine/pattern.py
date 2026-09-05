# -*- coding: utf-8 -*-
"""
관계 판정 — 실무가 **실제로 보는 자리**.

★ 왜 생겼나 (2026-09-04)

  손님이 짚었소 — "전문성이 있어야지. 캐릭터별로 전문가잖아. 재회든
  연애든 돈이든 전문가 사주 특징 파악해서 우리 로직에 다 접목해."

  엔진은 이미 많이 세고 있었습니다 — 십신 개수 · 오행 개수 · 신강약 ·
  용신 · 흐름 · 일지 충합 · 신살 열셋 · 공망 · 궁위 · 대운.

  그런데 **그것들 사이의 관계**를 안 보고 있었습니다. 실무에서 돈을
  볼 때 세는 것은 「재성 1개」가 아니라 **「비겁이 셋인데 재성이
  하나」**(군겁쟁재)입니다. 일을 볼 때는 「정관 1개」가 아니라
  **「상관과 정관이 같이 있다」**(상관견관)입니다.

  관계는 개수보다 강합니다. 개수는 누구나 세지만, 관계는 그 사람의
  자리를 말합니다.

★ 지어내지 않습니다 — **판정합니다**

  여기 있는 것은 전부 자평 명리에서 이름이 붙어 쓰이는 짜임이고,
  조건은 **셀 수 있는 값**으로만 씁니다. 조건이 안 맞으면 그 짜임은
  **안 냅니다.** 억지로 붙이면 누구에게나 맞는 말이 되어, 이 집이
  금지한 바넘 문장이 됩니다.

★ 단정하지 않습니다

  짜임은 **자리를 가리키는 이름**이지 결과가 아닙니다. 「재물이 없다」
  「이혼한다」 「병이 온다」로 쓰지 않습니다 (guard 가 다시 봅니다).
  짜임이 말하는 것은 «어디서 힘이 새고 어디서 부딪히는가» 까지입니다.

★ 고민마다 보는 짜임이 다릅니다

  같은 명식이라도 돈을 물으면 재성 쪽 짜임을, 사랑을 물으면 배우자성과
  일지 쪽 짜임을 봅니다. 그것이 「고민에 맞게 본다」는 말의 뜻입니다.
"""
from __future__ import annotations

from typing import Optional

from .constants import HIDDEN

# 고민 → 이 자리를 보는 짜임을 고를 때 쓰는 열쇠
CONCERNS = ("money", "work", "love", "people", "dir", "health")


# ══════════════════════════════════════════════════════════
# 밑감 — 드러났는가, 숨었는가
# ══════════════════════════════════════════════════════════
#
# ★ 실무가 개수 다음으로 보는 것이 **투출**입니다.
#
#   같은 「재성 하나」라도 천간에 드러난 것과 지지 속에 숨은 것은
#   다르게 봅니다. 드러난 것은 밖으로 쓰이고 남이 알아보며, 숨은
#   것은 안에서만 돌아 제 손에 안 잡힙니다.
def _gan_gods(f) -> list:
    """천간에 드러난 십신 (일간은 자기 자신이라 뺍니다)."""
    from .features import ten_god
    return [ten_god(p["gan"], f.day_gan) for p in f.pillars
            if p.get("label") != "일주"]


def _ji_gods(f) -> list:
    """지지 본기의 십신."""
    from .features import ten_god
    return [ten_god(HIDDEN[p["ji"]][0][0], f.day_gan) for p in f.pillars]


def tuchul(f, god: str) -> bool:
    """이 십신이 **천간에 드러났는가.**"""
    return god in _gan_gods(f)


def group_tuchul(f, group: str) -> bool:
    """이 묶음(재성·관성 …)이 천간에 드러났는가."""
    from .constants import TEN_GOD_GROUP
    return any(TEN_GOD_GROUP.get(g) == group for g in _gan_gods(f))


def spouse_group(f) -> str:
    """
    배우자를 보는 자리.

    ★ 남명은 재성, 여명은 관성으로 봅니다 — 자평의 오랜 기준이오.
      성별을 모르면 **정하지 않습니다.** 지어내면 그때부터 남의
      사주가 됩니다.
    """
    if f.sex == "M":
        return "재성"
    if f.sex == "F":
        return "관성"
    return ""


def _sinsal_at(f, key: str) -> list:
    """그 신살이 앉은 자리들. 없으면 빈 목록."""
    for s in (f.sinsal or []):
        if s.get("key") == key:
            return list(s.get("at") or [])
    return []


# 궁위 이름 — 짝 글자가 앉은 자리가 곧 **어떤 결로 오느냐**요.
_SEAT_SAY = {
    "년주": "짝을 보는 글자가 <b>년주</b>에 앉았소. 웃대·먼 데의 자리라, "
            "<b>일찍 만나거나 멀리서 오는</b> 결이오. 집안이 얽히는 자리이기도 하오.",
    "월주": "짝을 보는 글자가 <b>월주</b>에 앉았소. 여덟 글자에서 가장 무거운 "
            "자리라, <b>일·배움·자란 데서 이어지는</b> 인연이 많소.",
    "일주": "짝을 보는 글자가 <b>일주</b>, 곧 그대 자리에 앉았소. 가장 가까운 "
            "자리라 <b>붙는 힘도 크고 부딪히는 힘도 크오</b>.",
    "시주": "짝을 보는 글자가 <b>시주</b>에 앉았소. 늦자리라 <b>늦게 자리가 "
            "잡히는</b> 결이오. 서두른 자리가 오래 안 가는 것이 그 때문이오.",
}


def _group_seats(f, group: str) -> list:
    """이 묶음이 앉은 궁위들. 없으면 빈 목록."""
    from .constants import TEN_GOD_GROUP
    from .features import ten_god
    out = []
    for p in f.pillars:
        got = []
        if p.get("label") != "일주":
            got.append(ten_god(p["gan"], f.day_gan))
        got.append(ten_god(HIDDEN[p["ji"]][0][0], f.day_gan))
        if any(TEN_GOD_GROUP.get(g) == group for g in got):
            out.append(p.get("label") or "")
    return [x for x in out if x]


def _count(f, group: str) -> int:
    return {"비겁": f.bi, "식상": f.sik, "재성": f.jae,
            "관성": f.gwan, "인성": f.inn}[group]


# ══════════════════════════════════════════════════════════
# 짜임 — 이름이 붙어 쓰이는 자리들
# ══════════════════════════════════════════════════════════
#
# 각 짜임은 이렇게 씁니다 —
#   key    안에서 부르는 이름
#   name   손님에게 보이는 이름 (한자 이름은 풀이와 함께)
#   at     이 짜임을 보는 고민들
#   test   **셀 수 있는 조건**. 안 맞으면 안 냅니다
#   why    근거 — 손님이 만세력을 펴고 세면 같은 수가 나와야 합니다
#   say    뜻 한 줄. 하오체 한 벌 · 「그대」 한 벌
#   ask    이 짜임이 걸렸을 때 **더 물어야 하는 것** (없으면 None)
def _pats() -> list:
    P = []

    def add(**kw):
        P.append(kw)

    # ── 돈 ────────────────────────────────────────────────
    add(key="gunggeop", name="군겁쟁재(群劫爭財)",
        gloss="여럿이 한 몫을 다투는 자리",
        at=("money", "people"),
        test=lambda f: f.bi >= 3 and f.jae <= 1,
        why=lambda f: "비겁 %d · 재성 %d" % (f.bi, f.jae),
        say="나눌 입은 많은데 쥘 자리가 얕소. 버는 재주가 없는 것이 아니라 "
            "<b>버는 족족 나가는 짜임</b>이오. 크게 벌수록 크게 새오.",
        ask="context")

    add(key="jaeda_sinyak", name="재다신약(財多身弱)",
        gloss="재물은 많은데 몸이 여린 자리",
        at=("money", "health"),
        test=lambda f: f.jae >= 3 and f.strength == "신약",
        why=lambda f: "재성 %d · %s" % (f.jae, f.strength),
        say="쥘 것은 널렸는데 <b>들 힘이 모자라오</b>. 기회가 없는 것이 아니라 "
            "기회가 와도 감당이 안 되는 자리요. 벌리는 것보다 <b>지키는 것</b>이 "
            "먼저요.")

    add(key="siksang_jae", name="식상생재(食傷生財)",
        gloss="만들어서 파는 흐름",
        at=("money", "work"),
        test=lambda f: f.sik >= 1 and f.jae >= 1,
        why=lambda f: "식상 %d → 재성 %d" % (f.sik, f.jae),
        say="만든 것이 <b>돈으로 이어지는 길</b>이 나 있소. 남 밑에서 받는 삯보다 "
            "제 손으로 낸 것이 값이 되는 짜임이오.")

    add(key="jae_none", name="재성 없음",
        gloss="쥐는 자리가 안 보임",
        at=("money",),
        test=lambda f: f.jae == 0,
        why=lambda f: "재성 0 · 여덟 글자에 없소",
        say="쥐는 자리가 <b>겉에 안 보이오</b>. 없다고 못 버는 것이 아니라, "
            "돈이 <b>손에 잡히는 꼴로 안 오오</b> — 값이 아니라 이름·자리·"
            "기회로 오는 사람이 많소.")

    # ── 일 ────────────────────────────────────────────────
    add(key="sanggwan_gwan", name="상관견관(傷官見官)",
        gloss="내지르는 힘과 규율이 마주 선 자리",
        at=("work", "people"),
        test=lambda f: f.ten_gods.get("상관", 0) >= 1
        and f.ten_gods.get("정관", 0) >= 1,
        why=lambda f: "상관 %d · 정관 %d" % (f.ten_gods.get("상관", 0),
                                            f.ten_gods.get("정관", 0)),
        say="옳은 말을 하고도 <b>지는 자리</b>가 있소. 규율을 지키는 힘과 "
            "규율을 치는 힘이 한 몸에 있어, 조직에서 자주 부딪히오. "
            "재주가 없어서가 아니오.",
        ask="context")

    add(key="gwan_in", name="관인상생(官印相生)",
        gloss="맡은 것이 배움으로 이어지는 자리",
        at=("work",),
        test=lambda f: f.gwan >= 1 and f.inn >= 1,
        why=lambda f: "관성 %d · 인성 %d" % (f.gwan, f.inn),
        say="맡은 것이 <b>자격과 문서로 남는</b> 짜임이오. 조직 안에서 크는 결이라, "
            "혼자 벌이는 것보다 <b>이름이 걸린 자리</b>에서 값이 서오.")

    add(key="gwan_none", name="관성 없음",
        gloss="눌러 주는 자리가 안 보임",
        at=("work", "dir"),
        test=lambda f: f.gwan == 0,
        why=lambda f: "관성 0 · 여덟 글자에 없소",
        say="나를 눌러 모양을 잡아 주는 자리가 <b>겉에 없소</b>. 시키는 데서 "
            "오래 못 버티고, <b>제가 정한 규율</b>로만 서는 사람이오. "
            "자유로운 것이 아니라 <b>기댈 틀이 없는</b> 것이오.")

    add(key="gwan_many", name="관살혼잡(官殺混雜)",
        gloss="누르는 것이 여럿 겹친 자리",
        at=("work", "health"),
        test=lambda f: f.ten_gods.get("정관", 0) >= 1
        and f.ten_gods.get("편관", 0) >= 1,
        why=lambda f: "정관 %d · 편관 %d" % (f.ten_gods.get("정관", 0),
                                            f.ten_gods.get("편관", 0)),
        say="누르는 자리가 <b>결이 다른 둘</b>이오. 지켜야 할 규율과 몰아붙이는 "
            "압이 같이 오니, <b>어느 쪽을 따를지</b>에서 힘이 다 나가오.")

    # ── 사랑 ──────────────────────────────────────────────
    add(key="spouse_none", name="배우자성 없음",
        gloss="짝을 보는 글자가 겉에 없음",
        at=("love",),
        test=lambda f: bool(spouse_group(f))
        and _count(f, spouse_group(f)) == 0,
        why=lambda f: "%s 0 · %s" % (spouse_group(f),
                                     "남명" if f.sex == "M" else "여명"),
        say="짝을 보는 글자가 <b>겉에 안 보이오</b>. 인연이 없다는 말이 아니오 — "
            "<b>고르는 눈이 늦게 열리고</b>, 온 사람을 알아보는 데 시간이 "
            "걸리는 짜임이오.",
        ask="partner")

    add(key="spouse_many", name="배우자성 여럿",
        gloss="짝을 보는 글자가 겹침",
        at=("love",),
        test=lambda f: bool(spouse_group(f))
        and _count(f, spouse_group(f)) >= 3,
        why=lambda f: "%s %d" % (spouse_group(f), _count(f, spouse_group(f))),
        say="짝을 보는 글자가 <b>여럿</b>이오. 사람이 안 오는 것이 아니라 "
            "<b>고르는 데서 오래 걸리오</b>. 겹친 만큼 재는 눈도 여럿이오.",
        ask="partner")

    add(key="spouse_seat", name="배우자궁",
        gloss="짝을 보는 글자가 앉은 자리",
        at=("love",),
        test=lambda f: bool(spouse_group(f))
        and _count(f, spouse_group(f)) in (1, 2)
        and bool(_group_seats(f, spouse_group(f))),
        why=lambda f: "%s %d · %s"
        % (spouse_group(f), _count(f, spouse_group(f)),
           " · ".join(_group_seats(f, spouse_group(f)))),
        say=lambda f: _SEAT_SAY[_group_seats(f, spouse_group(f))[0]],
        ask="meet")

    add(key="spouse_hidden", name="배우자성이 숨음",
        gloss="짝 글자가 지지에만 있음",
        at=("love",),
        test=lambda f: bool(spouse_group(f))
        and _count(f, spouse_group(f)) >= 1
        and not group_tuchul(f, spouse_group(f)),
        why=lambda f: "%s %d · 천간에 안 드러남"
        % (spouse_group(f), _count(f, spouse_group(f))),
        say="짝을 보는 글자가 <b>겉으로 안 드러나오</b>. 가까이 있어도 "
            "<b>늦게 알아보는</b> 결이라, 지나고 나서 «그때 그 사람이었구나» "
            "하는 자리가 있소.",
        ask="meet")

    add(key="spouse_open", name="배우자성이 드러남",
        gloss="짝 글자가 천간에 있음",
        at=("love",),
        test=lambda f: bool(spouse_group(f))
        and _count(f, spouse_group(f)) >= 1
        and group_tuchul(f, spouse_group(f)),
        why=lambda f: "%s %d · 천간에 드러남"
        % (spouse_group(f), _count(f, spouse_group(f))),
        say="짝을 보는 글자가 <b>겉에 드러나 있소</b>. 인연이 <b>보이는 자리에서</b> "
            "오는 결이라, 숨겨 두고 만나는 일이 잘 안 되오. 주변이 먼저 아오.",
        ask="meet")

    add(key="ilji_chung", name="일지 충(沖)",
        gloss="발밑 자리가 부딪힘",
        at=("love", "people", "health"),
        test=lambda f: bool(f.ilji_chung),
        why=lambda f: "일지 %s 충" % f.day_ji,
        say="그대 <b>발밑 자리가 부딪히오</b>. 가까운 자리일수록 크게 흔들리니, "
            "사람 일이 <b>미지근하게 끝나지 않고 한 번에 갈리오</b>.",
        ask="partner")

    add(key="ilji_hap", name="일지 합(合)",
        gloss="발밑 자리가 붙음",
        at=("love", "people"),
        test=lambda f: bool(f.ilji_hap),
        why=lambda f: "일지 %s 합" % f.day_ji,
        say="그대 <b>발밑 자리가 붙는</b> 자리요. 사람이 잘 붙되 <b>끊는 데서 "
            "오래 걸리오</b>. 정리했다 여긴 뒤에도 자리가 안 비오.",
        ask="partner")

    add(key="dohwa", name="도화(桃花)",
        gloss="끌리고 끌리는 자리",
        at=("love", "people"),
        test=lambda f: bool(_sinsal_at(f, "dohwa")),
        why=lambda f: "도화 · %s" % " · ".join(_sinsal_at(f, "dohwa")),
        say="<b>끌림이 오가는 자리</b>가 있소. 옛사람은 이걸 인기로도 보고 "
            "구설로도 보았소 — 좋고 나쁨을 정한 표가 아니라 <b>사람이 모이는 "
            "자리</b>를 가리키는 표요.")

    add(key="wonjin", name="원진(怨嗔)",
        gloss="까닭 없이 어긋나는 자리",
        at=("love", "people"),
        test=lambda f: bool(_sinsal_at(f, "wonjin")),
        why=lambda f: "원진 · %s" % " · ".join(_sinsal_at(f, "wonjin")),
        say="<b>까닭을 대기 어려운 어긋남</b>이 있는 자리요. 크게 잘못한 것이 "
            "없는데 마음이 안 붙는 결이오. 사람을 탓하기 전에 이 자리를 보시오.",
        ask="partner")

    # ── 사람 ──────────────────────────────────────────────
    add(key="bigyeop_many", name="비겁 과다",
        gloss="같은 자리가 여럿",
        at=("people", "money"),
        test=lambda f: f.bi >= 4,
        why=lambda f: "비겁 %d" % f.bi,
        say="나와 같은 자리가 <b>여럿</b>이오. 곁이 없는 것이 아니라 "
            "<b>겨루는 사람이 먼저 오는</b> 짜임이오. 나눌 때 몫이 늘 갈리오.")

    add(key="in_many", name="인성 과다",
        gloss="받는 자리가 여럿",
        at=("people", "work"),
        test=lambda f: f.inn >= 3,
        why=lambda f: "인성 %d" % f.inn,
        say="받는 자리가 <b>여럿</b>이오. 배우고 기대는 데는 밝은데, "
            "<b>내놓는 데서 막히오</b>. 준비가 길어지는 결이오.")

    add(key="yangin", name="양인(羊刃)",
        gloss="날이 선 자리",
        at=("people", "health", "work"),
        test=lambda f: bool(_sinsal_at(f, "yangin")),
        why=lambda f: "양인 · %s" % " · ".join(_sinsal_at(f, "yangin")),
        say="<b>날이 선 자리</b>가 있소. 밀어붙이는 힘이 세니 이룰 때 크게 "
            "이루고, <b>부딪힐 때 크게 부딪히오</b>. 힘을 쓸 데를 정해 두어야 하오.")

    # ── 방향 ──────────────────────────────────────────────
    add(key="yeokma", name="역마(驛馬)",
        gloss="움직이는 자리",
        at=("dir", "work"),
        test=lambda f: bool(_sinsal_at(f, "yeokma")),
        why=lambda f: "역마 · %s" % " · ".join(_sinsal_at(f, "yeokma")),
        say="<b>움직이는 자리</b>가 있소. 한자리에 붙박여 있으면 도리어 지치고, "
            "<b>옮기고 오갈 때</b> 결이 풀리는 짜임이오.")

    add(key="hwagae", name="화개(華蓋)",
        gloss="혼자 파고드는 자리",
        at=("dir", "work"),
        test=lambda f: bool(_sinsal_at(f, "hwagae")),
        why=lambda f: "화개 · %s" % " · ".join(_sinsal_at(f, "hwagae")),
        say="<b>혼자 파고드는 자리</b>가 있소. 사람 속에서 얻는 것보다 "
            "<b>물러나 깊이 들어갈 때</b> 나오는 것이 큰 결이오.")

    # ── 몸 ────────────────────────────────────────────────
    add(key="pyeongo", name="편고(偏枯)",
        gloss="한쪽으로 몰리고 한쪽이 빈 자리",
        at=("health",),
        test=lambda f: min(f.elements.values()) < 1.0
        and max(f.elements.values()) >= 3.0,
        why=lambda f: "%s %s · %s %s"
        % (f.strong_el, _amt(f.elements[f.strong_el]),
           f.weak_el, _amt(f.elements[f.weak_el])),
        say="기운이 <b>한쪽으로 몰리고 한쪽이 비었소</b>. 넘치는 쪽이 모자란 "
            "쪽을 만드는 짜임이라, 지치는 자리가 늘 같은 자리일 것이오. "
            "병을 말하는 것이 아니라 <b>쓰는 결</b>을 말하는 것이오.",
        ask="context")

    add(key="johu_cold", name="조후 — 한랭",
        gloss="차고 젖은 자리",
        at=("health", "money"),
        test=lambda f: f.elements.get("수", 0) >= 3
        and f.elements.get("화", 0) < 1,
        why=lambda f: "수 %s · 화 %s" % (_amt(f.elements.get("수", 0)),
                                        _amt(f.elements.get("화", 0))),
        say="<b>차고 젖은</b> 쪽으로 치우쳤소. 데우는 자리가 얕으니 "
            "<b>시작이 더디고 안으로 쌓이오</b>. 밖으로 내는 자리를 하나 "
            "만들어 두어야 하오.")

    add(key="johu_hot", name="조후 — 조열",
        gloss="덥고 마른 자리",
        at=("health", "money"),
        test=lambda f: f.elements.get("화", 0) >= 3
        and f.elements.get("수", 0) < 1,
        why=lambda f: "화 %s · 수 %s" % (_amt(f.elements.get("화", 0)),
                                        _amt(f.elements.get("수", 0))),
        say="<b>덥고 마른</b> 쪽으로 치우쳤소. 붙는 것은 빠르나 <b>오래 못 "
            "가오</b>. 식히고 적시는 자리를 곁에 두어야 하오.")

    add(key="gongmang_ilji", name="공망(空亡)",
        gloss="비어 있다고 보던 자리",
        at=("love", "people", "dir"),
        test=lambda f: bool(f.gongmang) and f.day_ji in (f.gongmang or ""),
        why=lambda f: "공망 %s · 일지 %s" % (f.gongmang, f.day_ji),
        say="발밑 자리가 <b>비어 있다고 보던</b> 자리에 걸렸소. 옛사람은 "
            "여기를 <b>애써도 손에 안 남는 자리</b>로 읽었소 — 없다는 뜻이 "
            "아니라 <b>쥐는 방식이 달라야 한다</b>는 뜻이오.")

    return P


def _amt(n: float) -> str:
    """숫자를 사람 말로. 내부 척도는 안 냅니다."""
    if n < 1:
        return "1도 안 되"
    return "%d" % round(n)


_TABLE: Optional[list] = None


def all_patterns() -> list:
    global _TABLE
    if _TABLE is None:
        _TABLE = _pats()
    return _TABLE


def read(f, concern: Optional[str] = None, limit: int = 3) -> list:
    """
    이 명식에서 **이 고민에 걸리는** 짜임들.

    ★ 조건이 안 맞으면 **안 냅니다.** 억지로 붙이면 누구에게나 맞는
      말이 되어 바넘 문장이 됩니다. 빈 목록이 나오는 것이 정상이오.

    돌려주는 것: [{"key","name","gloss","why","say","ask"}]
    """
    out = []
    for p in all_patterns():
        if concern and concern not in p["at"]:
            continue
        try:
            if not p["test"](f):
                continue
        except Exception:
            continue
        out.append({
            "key": p["key"],
            "name": p["name"],
            "gloss": p["gloss"],
            "why": p["why"](f),
            # say 는 글이거나, 명식을 보고 고르는 함수요.
            "say": p["say"](f) if callable(p["say"]) else p["say"],
            "ask": p.get("ask"),
        })
        if len(out) >= limit:
            break
    return out


def asks_for(f, concern: str) -> Optional[str]:
    """
    이 고민에서 **더 물어야 하는 것**. 없으면 None.

    ★ 짜임이 걸렸을 때만 묻습니다. 「사랑을 골랐으니 무조건 상대
      사주를 내시오」 는 묻는 것이 아니라 받아 내는 것이오. 걸린
      자리가 있어야 물을 까닭이 서오.
    """
    for r in read(f, concern, limit=99):
        if r.get("ask"):
            return r["ask"]
    return None
