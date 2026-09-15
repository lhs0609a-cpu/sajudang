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

from . import topic as _topic
from .constants import GENERATED_BY, HIDDEN, ten_god as ten_god_of

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
    "년주": "짝을 보는 글자가 <b>년주</b>에 앉았소. 윗대와 먼 곳을 보는 기둥이라, "
            "짝을 <b>일찍 만나거나 멀리서 만나는</b> 편이오. 집안이 얽히기도 하오.",
    "월주": "짝을 보는 글자가 <b>월주</b>에 앉았소. 여덟 글자에서 가장 힘이 센 "
            "기둥이라, <b>일터·학교·자란 동네에서 이어지는</b> 인연이 많소.",
    "일주": "짝을 보는 글자가 <b>일주</b>, 곧 그대 자신의 기둥에 앉았소. 가장 가까운 "
            "곳이라 <b>끌리는 힘도 크고 부딪히는 힘도 크오</b>.",
    "시주": "짝을 보는 글자가 <b>시주</b>에 앉았소. 늦은 나이를 보는 기둥이라 짝이 "
            "<b>늦게 정해지는</b> 편이오. 서둘러 만난 사람과 오래 안 가는 것이 그 때문이오.",
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
        gloss="여럿이 돈 한 몫을 두고 다툼",
        at=("money", "people"),
        test=lambda f: f.bi >= 3 and f.jae <= 1,
        why=lambda f: "비겁 %d · 재성 %d" % (f.bi, f.jae),
        say="나눠 줄 사람은 많은데 손에 쥘 돈은 적소. 버는 재주가 없는 것이 아니라 "
            "<b>버는 족족 나가는 짜임</b>이오. 크게 벌수록 크게 새 나가오.",
        ask="context")

    add(key="jaeda_sinyak", name="재다신약(財多身弱)",
        gloss="돈은 많은데 감당할 힘이 모자람",
        at=("money", "health"),
        test=lambda f: f.jae >= 3 and f.strength == "신약",
        why=lambda f: "재성 %d · %s" % (f.jae, f.strength),
        say="잡을 돈은 널렸는데 <b>그걸 들어 올릴 힘이 모자라오</b>. 기회가 없는 "
            "것이 아니라 기회가 와도 감당이 안 되는 것이오. 일을 벌이는 것보다 "
            "<b>가진 것을 지키는 것</b>이 먼저요.")

    # ★ 여기부터 2026-09-06 에 늘린 자리입니다 (docs/20 §4-2).
    #   돈을 물었을 때 실무가 보는 것은 「재성 몇 개」가 아니라
    #   갈래·투출·궁위·재고·공망이고, 그걸 한 줄도 안 세고 있었습니다.
    #   흔한 짜임(식상생재·재생관)은 **뒤로** 물렸습니다 — 앞자리는
    #   상한 셋뿐이라, 누구에게나 걸리는 것이 먼저 오면 드문 자리가
    #   영영 안 나옵니다.
    add(key="sinwang_jaewang", name="신왕재왕(身旺財旺)",
        gloss="버티는 힘도 세고 돈도 많음",
        at=("money",),
        test=lambda f: f.strength == "신강" and f.jae >= 2,
        why=lambda f: "%s · 재성 %d" % (f.strength, f.jae),
        say="버티는 힘도 잡을 돈도 <b>같이 있소</b>. 벌인 일을 그대가 감당해 "
            "내는 짜임이라, 크게 벌였을 때 무너진 적이 적을 것이오. "
            "다만 <b>언제 멈출지</b>는 아무도 안 정해 주오.")

    add(key="jae_gongmang", name="재성 공망(空亡)",
        gloss="돈 글자가 비어 있다고 보던 곳에 앉음",
        at=("money",),
        test=lambda f: f.jae >= 1 and _topic.gongmang_hit(f, "재성"),
        why=lambda f: "재성이 앉은 글자가 공망 %s" % f.gongmang,
        say="돈을 보는 글자가 <b>비어 있다고 보던 곳</b>에 앉았소. 옛사람은 "
            "이것을 <b>공들인 만큼 손에 안 남는 돈</b>으로 읽었소 — 돈이 없다는 "
            "뜻이 아니라 <b>돈을 모으는 방법이 달라야 한다</b>는 뜻이오.",
        ask="context")

    add(key="tamjae", name="탐재괴인(貪財壞印)",
        gloss="돈 욕심이 나를 받쳐 주던 것을 깎음",
        at=("money", "health"),
        test=lambda f: f.jae >= 2 and f.inn >= 1 and f.strength == "신약",
        why=lambda f: "재성 %d · 인성 %d · %s" % (f.jae, f.inn, f.strength),
        say="돈을 잡으려는 마음이 <b>그대를 받쳐 주던 것을 깎소</b>. 벌이를 "
            "늘리려고 공부·휴식·기댈 사람을 먼저 접었을 것이오. "
            "그 셋이 곧 그대를 버티게 해 주던 것이오.")

    add(key="sisang_pyeonjae", name="시상편재(時上偏財)",
        gloss="태어난 시각 글자에 큰돈 글자가 앉음",
        at=("money",),
        test=lambda f: f.hour_known and len(f.pillars) >= 4
        and ten_god_of(f.pillars[3]["gan"], f.day_gan) == "편재",
        why=lambda f: "시주 천간 %s · 편재" % f.pillars[3]["gan"],
        say="<b>시주 천간에 편재</b>가 앉았소. 옛 책이 크게 좋게 보던 배치요 — "
            "나이 들어 벌이는 일이 크고, <b>젊을 때 벌이는 늘 성에 안 "
            "찼을</b> 것이오.")

    add(key="jaego", name="재고(財庫)",
        gloss="번 돈을 모아 두는 창고",
        at=("money",),
        test=lambda f: any(p["ji"] == _topic.GO_JI[
            _topic.el_of_group(f.day_gan, "재성")] for p in f.pillars),
        why=lambda f: "재성 %s의 고지 %s"
        % (_topic.el_of_group(f.day_gan, "재성"),
           _topic.GO_JI[_topic.el_of_group(f.day_gan, "재성")]),
        say="번 돈을 <b>모아 두는 창고</b>가 있소. 버는 재주와 모으는 "
            "재주는 다른데, 그대에게는 모으는 재주가 있소. "
            "다만 <b>열어야 쓰는</b> 창고요 — 모으기만 하다 못 쓴 돈이 있을 것이오.")

    add(key="jae_hidden", name="재성 암장(暗藏)",
        gloss="돈 글자가 아랫 글자 속에만 숨음",
        at=("money",),
        test=lambda f: f.jae >= 1 and not group_tuchul(f, "재성"),
        why=lambda f: "재성 %d · 천간에 안 드러남" % f.jae,
        say="돈을 보는 글자가 <b>겉으로 안 드러나오</b>. 남 눈에는 잘 버는 "
            "듯 보이는데 그대 손에는 안 잡히거나, 통장에는 있는데 "
            "쓸 수가 없는 돈이오.")

    add(key="siksang_jae", name="식상생재(食傷生財)",
        gloss="만든 것이 돈이 됨",
        at=("money", "work"),
        test=lambda f: f.sik >= 1 and f.jae >= 1,
        why=lambda f: "식상 %d → 재성 %d" % (f.sik, f.jae),
        say="만든 것이 <b>돈으로 이어지는 길</b>이 나 있소. 남 밑에서 받는 월급보다 "
            "제 손으로 만든 것이 돈이 되는 짜임이오.")

    add(key="jae_none", name="재성 없음",
        gloss="돈 글자가 안 보임",
        at=("money",),
        test=lambda f: f.jae == 0,
        why=lambda f: "재성 0 · 여덟 글자에 없소",
        say="돈을 보는 글자가 <b>겉에 안 보이오</b>. 없다고 못 버는 것이 아니라, "
            "돈이 <b>현금으로 바로 안 오오</b> — 돈 대신 이름·직책·"
            "기회로 오는 사람이 많소.")

    add(key="jae_saeng_gwan", name="재생관(財生官)",
        gloss="번 돈이 직함·명예로 바뀜",
        at=("money", "work"),
        test=lambda f: f.jae >= 1 and f.gwan >= 1,
        why=lambda f: "재성 %d → 관성 %d" % (f.jae, f.gwan),
        say="번 돈이 <b>직함이나 명예로 바뀌는 길</b>이 나 있소. 돈만 좇는 사람이 "
            "아니라 <b>돈이 이름으로 남아야</b> 성에 차는 사람이오. "
            "그래서 제 몫을 늦게 말하다 손해 본 적이 있소.")

    # ── 일 ────────────────────────────────────────────────
    add(key="sanggwan_gwan", name="상관견관(傷官見官)",
        gloss="할 말 하는 힘과 규칙이 마주 섬",
        at=("work", "people"),
        test=lambda f: f.ten_gods.get("상관", 0) >= 1
        and f.ten_gods.get("정관", 0) >= 1,
        why=lambda f: "상관 %d · 정관 %d" % (f.ten_gods.get("상관", 0),
                                            f.ten_gods.get("정관", 0)),
        say="옳은 말을 하고도 <b>지는 때</b>가 있소. 규칙을 지키려는 마음과 "
            "규칙에 대드는 마음이 한 몸에 있어, 회사에서 자주 부딪히오. "
            "재주가 없어서가 아니오.",
        ask="context")

    add(key="gwan_in", name="관인상생(官印相生)",
        gloss="맡은 일이 배움으로 이어짐",
        at=("work",),
        test=lambda f: f.gwan >= 1 and f.inn >= 1,
        why=lambda f: "관성 %d · 인성 %d" % (f.gwan, f.inn),
        say="맡은 일이 <b>자격증과 경력으로 남는</b> 짜임이오. 회사 같은 조직 안에서 "
            "크는 사람이라, 혼자 일을 벌이는 것보다 <b>이름이 걸린 직책</b>에서 "
            "인정을 받소.")

    add(key="gwan_none", name="관성 없음",
        gloss="잡아 주는 규칙 글자가 안 보임",
        at=("work", "dir"),
        test=lambda f: f.gwan == 0,
        why=lambda f: "관성 0 · 여덟 글자에 없소",
        say="나를 잡아 주는 규칙 글자가 <b>겉에 없소</b>. 남이 시키는 곳에서는 "
            "오래 못 버티고, <b>제가 정한 규칙</b>으로만 서는 사람이오. "
            "자유로운 것이 아니라 <b>기댈 규칙이 없는</b> 것이오.")

    add(key="sal_in", name="살인상생(殺印相生)",
        gloss="압박이 배움으로 바뀜",
        at=("work", "health"),
        test=lambda f: f.ten_gods.get("편관", 0) >= 1 and f.inn >= 1,
        why=lambda f: "편관 %d · 인성 %d" % (f.ten_gods.get("편관", 0), f.inn),
        say="몰아붙이는 압박이 <b>배움으로 바뀌는</b> 길이 나 있소. 압박이 "
            "그대를 깎지 않고 <b>자격과 이름으로 바뀌는</b> 짜임이라, "
            "힘든 곳에서 오래 버틴 만큼 남는 것이 있소.")

    add(key="siksin_jesal", name="식신제살(食神制殺)",
        gloss="만드는 힘으로 압박을 이김",
        at=("work",),
        test=lambda f: f.ten_gods.get("식신", 0) >= 1
        and f.ten_gods.get("편관", 0) >= 1,
        why=lambda f: "식신 %d · 편관 %d" % (f.ten_gods.get("식신", 0),
                                            f.ten_gods.get("편관", 0)),
        say="누르는 압박을 <b>무언가 만들어 내는 힘으로 눌러 두는</b> 짜임이오. "
            "시키는 대로만 하면 눌리고, <b>제 손으로 만들어 내놓을 때</b> 그 "
            "압박이 도구가 되오 — 부담이 오히려 일을 밀어 준다는 말이오.")

    add(key="gwan_many", name="관살혼잡(官殺混雜)",
        gloss="나를 누르는 것이 여럿 겹침",
        at=("work", "health"),
        test=lambda f: f.ten_gods.get("정관", 0) >= 1
        and f.ten_gods.get("편관", 0) >= 1,
        why=lambda f: "정관 %d · 편관 %d" % (f.ten_gods.get("정관", 0),
                                            f.ten_gods.get("편관", 0)),
        say="나를 누르는 것이 <b>성질이 다른 둘</b>이오. 지켜야 할 규칙과 몰아붙이는 "
            "압박이 같이 오니, <b>어느 것을 따를지</b> 고민하다 힘이 다 빠지오.")

    # ── 사랑 ──────────────────────────────────────────────
    add(key="spouse_none", name="배우자성 없음",
        gloss="짝을 보는 글자가 겉에 없음",
        at=("love",),
        test=lambda f: bool(spouse_group(f))
        and _count(f, spouse_group(f)) == 0,
        why=lambda f: "%s 0 · %s" % (spouse_group(f),
                                     "남명" if f.sex == "M" else "여명"),
        say="짝을 보는 글자가 <b>겉에 안 보이오</b>. 인연이 없다는 말이 아니오 — "
            "<b>사람 보는 눈이 늦게 트이고</b>, 다가온 사람을 알아보는 데 시간이 "
            "걸리는 짜임이오.",
        ask="partner")

    add(key="spouse_many", name="배우자성 여럿",
        gloss="짝을 보는 글자가 겹침",
        at=("love",),
        test=lambda f: bool(spouse_group(f))
        and _count(f, spouse_group(f)) >= 3,
        why=lambda f: "%s %d" % (spouse_group(f), _count(f, spouse_group(f))),
        say="짝을 보는 글자가 <b>여럿</b>이오. 사람이 안 오는 것이 아니라 "
            "<b>고르는 데 오래 걸리오</b>. 글자가 겹친 만큼 따지는 것도 많소.",
        ask="partner")

    add(key="spouse_seat", name="배우자궁",
        gloss="짝을 보는 글자가 어느 기둥에 앉았나",
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
        gloss="짝 글자가 아랫 글자 속에만 있음",
        at=("love",),
        test=lambda f: bool(spouse_group(f))
        and _count(f, spouse_group(f)) >= 1
        and not group_tuchul(f, spouse_group(f)),
        why=lambda f: "%s %d · 천간에 안 드러남"
        % (spouse_group(f), _count(f, spouse_group(f))),
        say="짝을 보는 글자가 <b>겉으로 안 드러나오</b>. 가까이 있어도 "
            "<b>늦게 알아보는</b> 편이라, 지나고 나서 «그때 그 사람이었구나» "
            "하는 일이 있소.",
        ask="meet")

    add(key="spouse_open", name="배우자성이 드러남",
        gloss="짝 글자가 윗 글자에 드러남",
        at=("love",),
        test=lambda f: bool(spouse_group(f))
        and _count(f, spouse_group(f)) >= 1
        and group_tuchul(f, spouse_group(f)),
        why=lambda f: "%s %d · 천간에 드러남"
        % (spouse_group(f), _count(f, spouse_group(f))),
        say="짝을 보는 글자가 <b>겉에 드러나 있소</b>. 인연이 <b>남들 보는 앞에서</b> "
            "오는 편이라, 숨겨 두고 만나기가 잘 안 되오. 주변 사람이 먼저 아오.",
        ask="meet")

    add(key="spouse_gongmang", name="배우자성 공망(空亡)",
        gloss="짝 글자가 비어 있다고 보던 곳에 앉음",
        at=("love",),
        test=lambda f: bool(spouse_group(f))
        and _count(f, spouse_group(f)) >= 1
        and _topic.gongmang_hit(f, spouse_group(f)),
        why=lambda f: "%s이 앉은 글자가 공망 %s" % (spouse_group(f), f.gongmang),
        say="짝을 보는 글자가 <b>비어 있다고 보던 곳</b>에 앉았소. "
            "옛사람은 이것을 <b>공들인 만큼 돌아오지 않는 인연</b>으로 "
            "읽었소 — 사람이 없다는 뜻이 아니라 <b>기대를 거는 방법이 "
            "달라야 한다</b>는 뜻이오.",
        ask="partner")

    add(key="ilji_chung", name="일지 충(沖)",
        gloss="내 발밑 글자가 다른 글자와 부딪힘",
        at=("love", "people", "health"),
        test=lambda f: bool(f.ilji_chung),
        why=lambda f: "일지 %s 충" % f.day_ji,
        say="그대 <b>발밑 글자가 다른 글자와 부딪히오</b>. 가까운 사이일수록 크게 "
            "흔들리니, 사람 일이 <b>흐지부지 끝나지 않고 한 번에 갈리오</b>.",
        ask="partner")

    add(key="ilji_hyeong", name="일지 형(刑)",
        gloss="내 발밑 글자가 다툼의 짝에 걸림",
        at=("love", "people", "health"),
        test=lambda f: f.day_ji in _topic.hyeong_at(f),
        why=lambda f: "형 %s · 일지 %s" % (_topic.hyeong(f), f.day_ji),
        say="그대 <b>발밑 글자가 형에 걸렸소</b>. 옛 책은 형을 다툼과 "
            "말싸움으로 읽었소 — 가장 가까운 사이에서 <b>말로 마음이 상하는</b> "
            "편이라, 먼 사람보다 곁의 사람과 더 자주 부딪히오.",
        ask="partner")

    add(key="ilji_hap", name="일지 합(合)",
        gloss="내 발밑 글자가 다른 글자와 붙음",
        at=("love", "people"),
        test=lambda f: bool(f.ilji_hap),
        why=lambda f: "일지 %s 합" % f.day_ji,
        say="그대 <b>발밑 글자가 다른 글자와 붙어 있소</b>. 사람과 잘 가까워지되 "
            "<b>관계를 끊는 데 오래 걸리오</b>. 정리했다 여긴 뒤에도 마음이 잘 "
            "안 비오.",
        ask="partner")

    add(key="dohwa", name="도화(桃花)",
        gloss="사람을 끌어당김",
        at=("love", "people"),
        test=lambda f: bool(_sinsal_at(f, "dohwa")),
        why=lambda f: "도화 · %s" % " · ".join(_sinsal_at(f, "dohwa")),
        say="<b>사람을 끌어당기는 힘</b>이 있소. 옛사람은 이걸 인기로도 보고 "
            "남의 입에 오르내리는 일로도 보았소 — 좋다 나쁘다를 정한 것이 아니라 "
            "<b>사람이 모여든다</b>는 것을 가리키는 이름이오.")

    add(key="wonjin", name="원진(怨嗔)",
        gloss="까닭 없이 어긋나는 사이",
        at=("love", "people"),
        test=lambda f: bool(_sinsal_at(f, "wonjin")),
        why=lambda f: "원진 · %s" % " · ".join(_sinsal_at(f, "wonjin")),
        say="<b>까닭을 대기 어려운 어긋남</b>이 있소. 크게 잘못한 것이 "
            "없는데 마음이 잘 안 가는 사이가 생기오. 사람을 탓하기 전에 이 글자부터 보시오.",
        ask="partner")

    # ── 사람 ──────────────────────────────────────────────
    add(key="bigyeop_many", name="비겁 과다",
        gloss="나와 같은 글자가 여럿",
        at=("people", "money"),
        test=lambda f: f.bi >= 4,
        why=lambda f: "비겁 %d" % f.bi,
        say="나와 같은 글자가 <b>여럿</b>이오. 곁에 사람이 없는 것이 아니라 "
            "<b>겨루는 사람이 먼저 오는</b> 짜임이오. 나눌 때마다 몫 때문에 다투기 쉽소.")

    add(key="in_many", name="인성 과다",
        gloss="배우고 기대는 글자가 여럿",
        at=("people", "work", "dir"),
        test=lambda f: f.inn >= 3,
        why=lambda f: "인성 %d" % f.inn,
        say="배우고 기대는 글자가 <b>여럿</b>이오. 배우는 것은 잘하는데, "
            "<b>배운 것을 밖으로 내놓을 때 막히오</b>. 준비만 길어지기 쉽소.")

    add(key="yangin", name="양인(羊刃)",
        gloss="칼날처럼 센 기세",
        at=("people", "health", "work"),
        test=lambda f: bool(_sinsal_at(f, "yangin")),
        why=lambda f: "양인 · %s" % " · ".join(_sinsal_at(f, "yangin")),
        say="<b>칼날처럼 날카로운 기세</b>가 있소. 밀어붙이는 힘이 세니 이룰 때 크게 "
            "이루고, <b>부딪힐 때 크게 부딪히오</b>. 그 힘을 어디에 쓸지 미리 정해 두어야 하오.")

    # ── 방향 ──────────────────────────────────────────────
    add(key="yeokma", name="역마(驛馬)",
        gloss="자주 옮겨 다님",
        at=("dir", "work"),
        test=lambda f: bool(_sinsal_at(f, "yeokma")),
        why=lambda f: "역마 · %s" % " · ".join(_sinsal_at(f, "yeokma")),
        say="<b>자주 옮겨 다니는 글자</b>가 있소. 한곳에 붙박여 있으면 도리어 지치고, "
            "<b>옮기고 오갈 때</b> 일이 잘 풀리는 짜임이오.")

    add(key="samhap_guk", name="삼합국(三合局)",
        gloss="아랫 글자 셋이 한 가지 성질로 뭉침",
        at=("dir", "people", "work"),
        test=lambda f: _topic.hap_group(f)[0] == "삼합",
        why=lambda f: "삼합 · %s 국(局)" % _topic.hap_group(f)[1],
        say="지지 셋이 <b>한 가지 성질로 뭉쳤소</b>. 삶의 방향이 이미 한쪽으로 "
            "굳어 있어, 그 방향으로 갈 때는 남보다 빠르고 <b>반대로 방향을 틀 때는 "
            "힘이 두 배로</b> 드오.")

    add(key="yeokma_jae", name="역마 재성",
        gloss="옮겨 다니는 글자에 돈이 붙음",
        at=("dir", "money"),
        test=lambda f: bool(_sinsal_at(f, "yeokma"))
        and f.ten_gods.get("편재", 0) >= 1,
        why=lambda f: "역마 %s · 편재 %d"
        % (" · ".join(_sinsal_at(f, "yeokma")), f.ten_gods.get("편재", 0)),
        say="옮겨 다니는 글자에 <b>크게 오가는 돈</b>이 붙었소. 한곳에 "
            "앉아 버는 사람이 아니라 <b>오가며 버는</b> 사람이라, 발이 묶이면 "
            "벌이도 같이 묶이오.")

    add(key="banghap_guk", name="방합국(方合局)",
        gloss="아랫 글자가 한 계절로 모임",
        at=("dir", "work"),
        test=lambda f: _topic.hap_group(f)[0] == "방합",
        why=lambda f: "방합 · %s" % _topic.hap_group(f)[1],
        say="지지가 <b>한 계절로 모였소</b>. 같은 성질이 두텁게 쌓여 "
            "그런 일에서는 남보다 깊이 가되, <b>성질이 다른 일을 만나면 크게 "
            "낯설어</b> 하오.")

    add(key="hwagae", name="화개(華蓋)",
        gloss="혼자 깊이 파고듦",
        at=("dir", "work"),
        test=lambda f: bool(_sinsal_at(f, "hwagae")),
        why=lambda f: "화개 · %s" % " · ".join(_sinsal_at(f, "hwagae")),
        say="<b>혼자 파고드는 글자</b>가 있소. 사람들 속에서 얻는 것보다 "
            "<b>혼자 물러나 깊이 공부할 때</b> 얻는 것이 더 큰 사람이오.")

    # ── 몸 ────────────────────────────────────────────────
    #
    # ★ 여기서는 **병을 말하지 않습니다.** 옛 표가 오행을 어느 장부에
    #   붙여 읽었는지는 사실이라 전하되, 「어디가 나쁘오」는 진단이라
    #   금지입니다 (docs/11 · guard). 짜임이 말하는 것은 «어디서 힘이
    #   새고 어디서 부딪히는가» 까지요.
    add(key="gorip", name="고립(孤立)",
        gloss="하나뿐인데 받쳐 줄 글자가 없음",
        at=("health",),
        test=lambda f: any(_topic.isolated(f, e)
                           for e in ("목", "화", "토", "금", "수")),
        why=lambda f: " · ".join(
            "%s 하나 · 낳아 줄 %s 없음" % (e, GENERATED_BY[e])
            for e in ("목", "화", "토", "금", "수") if _topic.isolated(f, e)),
        say="개수로는 있는데 <b>받쳐 줄 글자가 없는</b> 것이 있소. "
            "하나뿐인 데다 채워 주는 글자가 비어, <b>쓰면 쓰는 만큼 "
            "바닥나오</b>. 그 힘을 쓸 때마다 남보다 두 배로 지치오.",
        ask="context")

    add(key="dosik", name="도식(倒食)",
        gloss="생각하는 힘이 먹고 쉬는 것을 밀어냄",
        at=("health", "work"),
        test=lambda f: f.ten_gods.get("편인", 0) >= 1
        and f.ten_gods.get("식신", 0) >= 1,
        why=lambda f: "편인 %d · 식신 %d" % (f.ten_gods.get("편인", 0),
                                            f.ten_gods.get("식신", 0)),
        say="받아들이는 글자와 내놓는 글자가 <b>한 몸에서 맞물려</b> 있소. "
            "옛사람은 이것을 <b>먹고 자는 버릇이 흐트러지는 짜임</b>으로 "
            "읽었소 — 생각이 많아지면 끼니와 잠이 먼저 밀리오.")

    add(key="sik_many", name="식상 과다",
        gloss="내놓는 글자가 넘침",
        at=("health", "people", "dir"),
        test=lambda f: f.sik >= 3,
        why=lambda f: "식상 %d" % f.sik,
        say="밖으로 내놓는 글자가 <b>넘치오</b>. 힘을 다 쓰고 잠으로 채우는 "
            "사람인데, <b>잠만 자면 회복되던 나이가 지나가고</b> 있소.")

    add(key="pyeongo", name="편고(偏枯)",
        gloss="한쪽이 넘치고 한쪽이 빔",
        at=("health",),
        test=lambda f: min(f.elements.values()) < 1.0
        and max(f.elements.values()) >= 3.0,
        why=lambda f: "%s %s · %s %s"
        % (f.strong_el, _amt(f.elements[f.strong_el]),
           f.weak_el, _amt(f.elements[f.weak_el])),
        say="나무·불·흙·쇠·물 다섯이 <b>한쪽으로 몰리고 한쪽이 비었소</b>. 넘치는 "
            "것이 모자란 것을 만드는 짜임이라, 지칠 때 늘 같은 식으로 지칠 것이오. "
            "병을 말하는 것이 아니라 <b>힘을 쓰는 버릇</b>을 말하는 것이오.",
        ask="context")

    add(key="johu_cold", name="조후 — 한랭",
        gloss="차갑고 축축한 쪽으로 기움",
        at=("health", "money"),
        test=lambda f: f.elements.get("수", 0) >= 3
        and f.elements.get("화", 0) < 1,
        why=lambda f: "수 %s · 화 %s" % (_amt(f.elements.get("수", 0)),
                                        _amt(f.elements.get("화", 0))),
        say="여덟 글자가 <b>차고 축축한</b> 쪽으로 치우쳤소 — 물이 많고 불이 "
            "모자라다는 말이오. 데워 주는 불이 적으니 <b>시작이 더디고 마음이 "
            "안으로 쌓이오</b>. 속을 밖으로 꺼낼 곳을 하나 만들어 두어야 하오.")

    add(key="johu_hot", name="조후 — 조열",
        gloss="덥고 메마른 쪽으로 기움",
        at=("health", "money"),
        test=lambda f: f.elements.get("화", 0) >= 3
        and f.elements.get("수", 0) < 1,
        why=lambda f: "화 %s · 수 %s" % (_amt(f.elements.get("화", 0)),
                                        _amt(f.elements.get("수", 0))),
        say="여덟 글자가 <b>덥고 메마른</b> 쪽으로 치우쳤소 — 불이 많고 물이 "
            "모자라다는 말이오. 불붙듯 시작은 빠르나 <b>오래 못 가오</b>. "
            "마음을 식혀 줄 사람이나 쉬는 시간을 곁에 두어야 하오.")

    add(key="gongmang_ilji", name="공망(空亡)",
        gloss="비어 있다고 보던 글자",
        at=("love", "people", "dir"),
        test=lambda f: bool(f.gongmang) and f.day_ji in (f.gongmang or ""),
        why=lambda f: "공망 %s · 일지 %s" % (f.gongmang, f.day_ji),
        say="그대 발밑 글자가 <b>비어 있다고 보던</b> 글자에 걸렸소. 옛사람은 "
            "이것을 <b>애써도 손에 안 남는 일</b>로 읽었소 — 없다는 뜻이 "
            "아니라 <b>붙잡는 방법이 달라야 한다</b>는 뜻이오.")

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


def read(f, concern: Optional[str] = None, limit: int = 3,
         focus: Optional[list] = None) -> list:
    """
    이 명식에서 **이 고민에 걸리는** 짜임들.

    ★ 조건이 안 맞으면 **안 냅니다.** 억지로 붙이면 누구에게나 맞는
      말이 되어 바넘 문장이 됩니다. 빈 목록이 나오는 것이 정상이오.

    돌려주는 것: [{"key","name","gloss","why","say","ask"}]
    """
    out = []
    pats = all_patterns()
    # ★ 손님이 되물음에 답했으면 **그 자리 짜임을 먼저** 봅니다 (2026-09-10).
    #
    #   전에는 늘 같은 차례로 앞 셋을 냈습니다. 그래서 짝사랑이든 이별이든
    #   같은 짜임 셋이 섰고, 답이 처방에 안 닿았습니다(31컷 중 1컷).
    #
    #   ★ 새로 세지 않습니다. **어느 것을 먼저 볼지만** 바꿉니다 — 조건이
    #     안 맞는 짜임은 여전히 안 냅니다. 답 안 한 사람은 예전과 같습니다.
    #   `sorted` 는 안정 정렬이라 나머지는 원래 차례를 지킵니다.
    if focus:
        pri = {k: i for i, k in enumerate(focus)}
        pats = sorted(pats, key=lambda p: (0 if p["key"] in pri else 1,
                                           pri.get(p["key"], 99)))
    for p in pats:
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
