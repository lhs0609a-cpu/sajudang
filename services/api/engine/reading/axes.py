# -*- coding: utf-8 -*-
"""
주장 생산자 — 축마다 **한 꼴**, 문장은 셈이 채운다.

★ 여기서 표를 새로 쓰지 않습니다 (2026-09-28)

  여태 새 층은 늘 표로 붙었습니다 — `ROLES`(20×7) `PRACTICES`(7)
  `TYPES`(16) `GUIDES`(7) `INTERVIEWS`(20) `CASES`(7). 손으로 쓴
  한국말이 231,908자가 됐는데 손님 축 겹침은 69.1% 였습니다. 표는
  `(고민 × 캐릭터 × MBTI)` 로 뽑히고 **여덟 글자가 그 열쇠에 없어서**요.

  이 파일은 반대로 갑니다. 축 하나에 꼴 하나를 두고, 슬롯을 **셈이**
  채웁니다. 가짓수는 칸 수가 아니라 센 값의 조합에서 나옵니다.
  캐릭터 스무 명은 여기서 갈리지 않습니다 — `voice`(다섯 결)와
  축 우선순위가 가릅니다. 문장을 스무 벌 쓰면 한 사람 안에서 결이
  섞입니다(그렇게 쓴 문장이 1,044개 있었습니다).

★ 조건이 안 맞으면 **안 냅니다.**

  생산자는 `None` 을 돌려줍니다. 「모르오」 라고 쓰는 것과 같은 규칙이오 —
  재고가 없는데 재고 얘기를 하면 그게 소설입니다.
"""
from __future__ import annotations

from typing import Callable, Optional

from .. import bank as bank_mod
from .. import topic as topic_mod
from .. import rarity as rarity_mod
from ..bank import josa
from .claim import Claim, ClaimError, Counted, Ground, Scene, count_word

#: 유파 출처 — 근거 줄 꼬리. 한 자리에 둡니다.
SRC_TG = "자평 명리 · 십신"
SRC_ST = "자평 명리 · 신강약"
SRC_DA = "자평 명리 · 대운"
SRC_PAL = "자평 명리 · 궁위"
SRC_SIN = "자평 명리 · 신살"

#: 오행을 손님 말로.
EL_WORD = {"목": "나무", "화": "불", "토": "흙", "금": "쇠", "수": "물"}

#: 살림의 물건 — 고민마다 **어제 손에 쥔 것**.
#:
#: ★ 뜬 낱말을 쓰지 마시오. 「자리」 「얼굴」 「철」 을 물건 자리에 넣으면
#:   그 표 전체가 흐려집니다 (`Scene` 이 거부합니다).
PROPS = {
    "money":       ("카드값", "단톡방 정산", "구독", "견적서", "통장"),
    "work":        ("이력서", "회의록", "마감표", "인수인계 문서", "출퇴근 기록"),
    "love":        ("읽음 표시", "기념일 달력", "같이 찍은 사진", "약속 메모"),
    "people":      ("단톡방", "축의금 봉투", "안 읽은 메시지", "모임 회비"),
    "dir":         ("합격 발표 화면", "이력서", "학원 결제 내역", "면접 일정"),
    "health":      ("영양제 통", "알람 시각", "병원 예약 문자", "걸음 수 화면"),
    "real_estate": ("등기부등본", "관리비 고지서", "계약서", "대출 상환표"),
}


def _axis_of(concern: str, sex: str = "") -> tuple:
    """물어보신 자리를 어느 십신 묶음으로 보는가. ★ `bank.CONCERN_AXIS` 한 자리."""
    row = bank_mod.bank()["CONCERN_AXIS"][concern]
    group = row.get("gF") if (sex == "F" and row.get("gF")) else row["g"]
    return group, row["w"]


#: 오행을 살림 물건과 잇는 자리 — 물건을 **셈으로** 고르게.
_EL_SEED = {"목": 0, "화": 1, "토": 2, "금": 3, "수": 4}


def _prop(concern: str, n: int, f=None) -> str:
    """
    살림의 물건 하나.

    ★ 물건이 스무 명에게 같았습니다 (2026-09-28). 「단톡방 정산 앞에서
      미루지도 밀어붙이지도 못한 날이…」 가 여섯 사람에게 글자 그대로
      나갔습니다 — 자리를 `n` 하나로만 골랐기 때문이오.

      물건은 주장이 아니라 **그림**이라, 무엇을 고르든 참말이 달라지지
      않습니다. 그래서 고르는 자리에 셈을 겁니다 — 태어난 날의 위 글자와
      가장 얇은 쪽. 그러면 사람마다 다른 물건이 서고, 그 사람 눈에는
      똑같이 자기 살림이오.
    """
    row = PROPS.get(concern) or PROPS["money"]
    seed = 0
    if f is not None:
        from ..constants import ELEMENT_OF_GAN
        seed = (_EL_SEED.get(ELEMENT_OF_GAN.get(f.day_gan, ""), 0) * 3
                + _EL_SEED.get(getattr(f, "weak_el", ""), 0))
    return row[(n + seed) % len(row)]


# ══ 축 ① 명식 장부 ═══════════════════════════════════════════════
def chart(f, concern: str) -> Optional[Claim]:
    """
    ★ 명식은 무엇을 물었든 같은 여덟 글자요. 고민을 안 들입니다.

    기둥 수를 글에 박지 마시오 — 시각 미상이면 여섯 글자입니다.
    「저울 눈금처럼 여덟 칸이」 가 세 기둥 손님에게 나간 자리요.
    """
    n = len(f.pillars) * 2
    seen = sum(1 for _ in f.pillars) * 2
    return Claim(
        axis="chart", kind="ledger",
        verdict="누가 세어도 같은 수가 나오는 자리",
        counted=(Counted(값=n, 단위="자", 무엇="세운 글자",
                         어디="세 기둥" if not f.hour_known else "네 기둥"),),
        ground=Ground(
            본것="절입 시각으로 세운 기둥",
            이치="태어난 때에 정해져 평생 안 바뀌오",
            출처="자평 명리"),
        asked=0.0, needs="free")


# ══ 축 ② 물어보신 자리의 저울 ═══════════════════════════════════════
def scale(f, concern: str) -> Optional[Claim]:
    """
    고민이 바뀌면 **보는 축**이 바뀝니다. 개수 하나만 보지 않습니다 —
    겉에 났는가(투출) · 받쳐 주는 글자가 있는가 · 어느 자리에 앉았는가.
    """
    group, word = _axis_of(concern, getattr(f, "sex", ""))
    n = f.ten_gods and {"재성": f.jae, "관성": f.gwan, "식상": f.sik,
                        "비겁": f.bi, "인성": f.inn}.get(group)
    if n is None:
        return None
    out = topic_mod.tuchul(f, group)
    root = topic_mod.rooted(f, group)
    seats = topic_mod.group_seats(f, group)
    counted = [Counted(값=n, 단위="자", 무엇=group, 어디="여섯 글자"
                       if not f.hour_known else "여덟 글자")]
    if seats:
        counted.append(Counted(값=len(seats), 단위="칸", 무엇="%s 있는 자리" % group,
                               어디=" · ".join(seats)))
    # 판정 — 개수가 아니라 **개수 사이의 관계**
    if n == 0:
        v = "%s 쥐는 글자가 한 자도 없는 자리" % josa(word, "을", "를")
    elif not out and not root:
        v = "쥐는 글자가 %s이고 겉에도 뿌리에도 안 선 자리" % count_word(n, "자")
    elif out and not root:
        v = "겉으로는 보이는데 아래 글자가 안 받쳐 주는 자리"
    elif root and not out:
        v = "받쳐 주는 글자는 있는데 겉으로 안 내는 자리"
    else:
        v = "겉과 받쳐 주는 글자가 함께 선 자리"
    prop = _prop(concern, 0, f)
    return Claim(
        axis="scale", kind="verdict", verdict=v, counted=tuple(counted),
        ground=Ground(
            본것="물어보신 자리를 %s으로 보고 센 값" % group,
            이치="겉에 난 글자는 남이 보고 뿌리 있는 글자는 오래 갑니다",
            출처=SRC_TG),
        scene=Scene(물건=prop,
                    한줄="%s 먼저 계산하고 나머지를 뒤로 미룬 달이 있었을 "
                         "것이오." % josa(prop, "을", "를")),
        asked=1.0, needs="free")


# ══ 축 ③ 없는 것 ═════════════════════════════════════════════════
def lack(f, concern: str) -> Optional[Claim]:
    """
    ★ `weak_el` 을 「없는 것」으로 단정하지 마시오.

      가장 적은 오행은 **한 자 있어도** 뽑힙니다. 19,900원 자리가
      「나무가 없다」 고 했는데 시주 천간에 乙이 보였던 적이 있습니다.
      손님이 만세력을 펴고 셀 수 있는 자리에서 틀리면 그 뒤 글은 다
      의심받소. **보이는 글자로** 세어 「없다」와 「가장 얇다」를 가릅니다.
    """
    el = f.weak_el
    if not el:
        return None
    seen = topic_mod.visible(f, el)
    word = EL_WORD[el]
    v = ("%s 겉에 한 자도 안 보이는 자리" % josa(word, "이", "가") if seen == 0
         else "%s 가장 얇은 자리" % josa(word, "이", "가"))
    prop = _prop(concern, 2, f)
    return Claim(
        axis="lack", kind="solace", verdict=v,
        counted=(Counted(값=seen, 단위="자", 무엇=word, 어디="겉에"),
                 Counted(값=f.elements[el], 단위="개", 무엇="%s 무게" % word,
                         어디="지장간까지")),
        ground=Ground(
            본것="겉에 보이는 글자와 지장간을 함께 센 값",
            이치="가장 얇은 기운이 하는 일은 늘 남보다 힘이 더 듭니다",
            출처=SRC_ST),
        scene=Scene(물건=prop,
                    한줄="%s 이야기를 하다 만 적이 여러 번 있을 것이오." % prop),
        asked=0.4, needs="free")


# ══ 축 ④ 쥔 것 ═══════════════════════════════════════════════════
def hold(f, concern: str) -> Optional[Claim]:
    el = f.strong_el
    if not el or el == f.weak_el:
        return None
    word = EL_WORD[el]
    return Claim(
        axis="hold", kind="verdict",
        verdict="%s 가장 두꺼운 자리" % josa(word, "이", "가"),
        # ★ 두 칸의 `무엇` 이 같아서 `render._c` 가 앞엣것을 집었습니다 —
        #   「겉으로 4.4자」 가 나갔습니다(겉에 보이는 글자는 정수요).
        counted=(Counted(값=f.elements[el], 단위="개", 무엇="%s 무게" % word,
                         어디="글자 속까지"),
                 Counted(값=topic_mod.visible(f, el), 단위="자",
                         무엇="%s 겉" % word, 어디="겉에")),
        ground=Ground(
            본것="오행 다섯을 나란히 세운 값",
            이치="두꺼운 기운은 쓰기 쉬워 먼저 손이 갑니다",
            출처=SRC_ST),
        scene=Scene(물건=_prop(concern, 3, f),
                    한줄="%s 펴 보면 그 쪽으로 손이 먼저 간 흔적이 있소."
                         % josa(_prop(concern, 3, f), "을", "를")),
        asked=0.3, needs="12900")


# ══ 축 ⑤ 얼굴 (신강약) ════════════════════════════════════════════
def face(f, concern: str) -> Optional[Claim]:
    """
    ★ 내부 점수(`strength_score`)를 내지 마시오 — 여섯 자리에서 샜습니다.
      그 판정에 **실제로 들어간 것**을 댑니다: 태어난 달과 바로 아래 글자.
    """
    got = int(f.deuk_ryeong) + int(f.deuk_ji)
    v = {"신강": "밀어붙이는 힘이 넉넉한 자리",
         "중화": "한쪽으로 크게 치우치지 않은 자리",
         "신약": "혼자 밀기보다 받쳐 줄 것이 있어야 도는 자리"}[f.strength]
    return Claim(
        axis="face", kind="verdict", verdict=v,
        counted=(Counted(값=got, 단위="개", 무엇="받쳐 주는 자리",
                         어디="태어난 달과 아래 글자"),),
        ground=Ground(
            본것="태어난 달이 받쳐 주는가와 아래 글자가 받쳐 주는가",
            # ★ 근거가 **주장을 받쳐야** 합니다 (2026-09-28).
            #   판정이 신강인데 이치는 「비슷하면 중화라 하오」 였습니다 —
            #   손님이 그 줄에서 바로 어긋남을 봅니다. 유료 감사가 v1 에서
            #   찾은 것과 같은 갈래요(근거 줄과 본문이 어긋남).
            #   ★ 이치는 **규칙**이오 — 이 사람의 수를 적으면 어긋납니다.
            #     「받쳐 주는 자리 1개」 인데 「둘이면」 이라 적혀 나갔습니다.
            #     수는 바로 앞 센 값이 들고, 여기는 왜 그렇게 읽는지만.
            이치="태어난 달과 발밑이 받쳐 주는 수로 신강·중화·신약을 가르오",
            출처=SRC_ST),
        scene=Scene(물건=_prop(concern, 1, f),
                    한줄="%s 앞에서 미루지도 밀어붙이지도 못한 날이 있었을 것이오."
                         % _prop(concern, 1, f)),
        asked=0.3, needs="free")


# ══ 축 ⑥ 때 (대운 국면) ═══════════════════════════════════════════
def turn(f, concern: str) -> Optional[Claim]:
    """
    ★ 그 해에 무슨 일이 생긴다고 말하지 않습니다. **바뀌는 때**만 셉니다.

      그리고 물어보신 자리를 **켭니다** — 새로 점치는 것이 아니오.
      고민이 어느 십신 묶음인지는 `CONCERN_AXIS` 가 이미 정했고 칸마다
      십신은 이미 세어져 있소. 켜지 않으면 손님이 어느 칸이 제 칸인지
      제 손으로 찾아야 합니다.
    """
    if not f.daeun:
        return None
    group, word = _axis_of(concern, getattr(f, "sex", ""))
    from ..constants import TEN_GOD_GROUP
    lit = [d for d in f.daeun
           if TEN_GOD_GROUP.get(d.get("ten_god") or "") == group
           and d["start_age"] >= f.age]
    nxt = next((d for d in f.daeun if d["start_age"] > f.age), None)
    counted = [Counted(값=f.age, 단위="살", 무엇="지금 나이", 어디="올해")]
    if nxt:
        counted.append(Counted(값=nxt["start_age"], 단위="살", 무엇="다음 칸",
                               어디="대운"))
        counted.append(Counted(값=nxt["start_age"] - f.age, 단위="해",
                               무엇="남은 햇수", 어디="다음 칸까지"))
    if lit:
        counted.append(Counted(값=lit[0]["start_age"], 단위="살",
                               무엇="%s 켜지는 칸" % word, 어디="대운"))
        v = "%s 자리가 켜지는 칸이 아직 앞에 있는 자리" % word
    else:
        v = "%s 자리가 켜지는 칸이 지나온 쪽에 있는 자리" % word
    return Claim(
        axis="turn", kind="verdict", verdict=v, counted=tuple(counted),
        ground=Ground(
            본것="대운 칸마다 십신을 세고 물어보신 자리에 걸리는 칸만 켠 것",
            이치="여덟 글자는 안 바뀌고 바뀌는 것은 열 해마다 도는 칸이오",
            출처=SRC_DA),
        scene=Scene(물건=_prop(concern, 4, f),
                    한줄="%s 열어 놓고 몇 해 뒤를 계산해 본 적이 있을 것이오."
                         % josa(_prop(concern, 4, f), "을", "를")),
        asked=0.8, needs="free")


# ══ 축 ⑦ 궁위 (나이가 든 자리) ════════════════════════════════════
def palace(f, concern: str) -> Optional[Claim]:
    """
    ★ 문서에 있는 표를 쓰시오 (docs/14 §6).

      궁위 나이 구간이 확정돼 있는데 한 번도 안 쓰이고 있었습니다.
      「년주에 있소」 는 틀릴 수가 없고 「열다섯 안쪽 얘기라 이미
      지나온 자리요」 는 손님이 그 자리에서 압니다.
    """
    now = next((p for p in f.palaces
                if not p.get("unknown") and _in_band(p.get("age"), f.age)), None)
    if not now:
        return None
    lo, hi = _band(now["age"])
    counted = [Counted(값=f.age, 단위="살", 무엇="지금 나이", 어디="올해"),
               Counted(값=lo, 단위="살", 무엇="이 칸이 여는 나이", 어디=now["pillar"])]
    if hi:
        counted.append(Counted(값=hi, 단위="살", 무엇="이 칸이 닫는 나이",
                               어디=now["pillar"]))
    return Claim(
        axis="palace", kind="verdict",
        verdict="%s 칸을 지나는 중인 자리" % now["who"],
        counted=tuple(counted),
        ground=Ground(
            본것="네 기둥에 붙은 궁위와 그 칸의 나이 구간",
            이치="기둥마다 보는 사람과 보는 나이가 따로 있소",
            출처=SRC_PAL),
        scene=Scene(물건=_prop(concern, 3, f),
                    한줄="%s 두고 이 나이에 이래도 되나 싶던 날이 있었을 것이오."
                         % josa(_prop(concern, 3, f), "을", "를")),
        asked=0.3, needs="9900")


def _band(s: str) -> tuple:
    import re
    m = re.findall(r"\d+", s or "")
    if not m:
        return 0, None
    return int(m[0]), (int(m[1]) if len(m) > 1 else None)


def _in_band(s: str, age: int) -> bool:
    lo, hi = _band(s)
    return lo <= age and (hi is None or age <= hi)


# ══ 축 ⑧ 희소도 (위로) ════════════════════════════════════════════
def how_rare(f, concern: str) -> Optional[Claim]:
    """
    ★ 골라 담지 마시오. 축 넷을 미리 정하고 그 칸을 그대로 냅니다.
      흔하면 흔하다고 합니다 — 여러 자리를 재서 가장 드문 것만 말하면
      누구나 드물어집니다.

    ★ 위로도 **셈에서** 나옵니다. 흔하면 「혼자가 아니오」, 드물면
      「이해받기 어려웠던 게 당연하오」.
    """
    look = rarity_mod.look(f)
    if not look:
        return None
    per = look.get("per10k")
    # ★ 표에 없는 배치면 **안 냅니다.** 지어내지 않고 「모르오」 로 두는
    #   것과 같은 규칙이오 — 희소도를 셀 수 없는데 「드물다」 고 하면
    #   그건 계산이 아니라 말입니다. (표를 다시 세려면 make_rarity.py)
    if per is None:
        return None
    v = ("같은 배치를 만나기 어려운 자리" if per <= 100
         else "혼자가 아닌 자리" if per >= 500
         else "흔하지도 드물지도 않은 자리")
    return Claim(
        axis="rarity", kind="solace", verdict=v,
        counted=(Counted(값=per, 단위="명", 무엇="같은 배치", 어디="1만 명에"),),
        ground=Ground(
            본것="축 넷을 미리 정해 놓고 그 칸을 인구에서 센 값",
            이치="흔한 배치는 이해받기 쉽고 드문 배치는 혼자 설명해야 했소",
            출처="성신당 희소도 표"),
        asked=0.2, needs="free")


# ══ 축 ⑨ 돕는 이 (희망) ═══════════════════════════════════════════
def helper(f, concern: str) -> Optional[Claim]:
    """
    ★ 희망은 **이미 가진 것**을 셉니다. 「좋아질 것이오」 는 약속이라
      검증 불가능한 주장이고 시점 확정 금지입니다.

    ★ 없는 기둥을 「없다」 고 적지 마시오 — 시각 미상이면 판정을
      안 하고 「모르오」 라 적습니다.
    """
    if not f.helpers:
        return None
    group, word = _axis_of(concern, getattr(f, "sex", ""))
    mine = [h for h in f.helpers if h.get("ten_god_group") == group]
    rows = mine or f.helpers
    seats = sorted({h["pillar"] for h in rows})
    v = ("%s 자리에 돕는 글자가 있는 자리" % word if mine
         else "돕는 글자가 이미 앉아 있는 자리")
    return Claim(
        axis="helper", kind="hope", verdict=v,
        counted=(Counted(값=len(rows), 단위="개", 무엇="길신",
                         어디=" · ".join(seats)),),
        ground=Ground(
            본것="길신이 있는 기둥과 그 기둥의 십신 묶음",
            이치="돕는 글자는 그 기둥이 맡은 사람 쪽에서 옵니다",
            출처=SRC_SIN),
        scene=Scene(물건=_prop(concern, 1, f),
                    한줄="%s 때문에 손을 벌려 본 적이 있다면 그 쪽이오."
                         % _prop(concern, 1, f)),
        asked=0.5, needs="free")


# ══ 축 ⑩ 재고·공망 — 걸릴 때만 ════════════════════════════════════
def vault(f, concern: str) -> Optional[Claim]:
    """조건이 안 맞으면 **안 냅니다.** 없는 재고 얘기는 소설이오."""
    group, word = _axis_of(concern, getattr(f, "sex", ""))
    jg = topic_mod.jaego(f)
    empty = topic_mod.gongmang_hit(f, group)
    if not jg and not empty:
        return None
    if jg and empty:
        v = "쥔 것을 넣어 둘 곳은 있는데 그 자리가 비는 자리"
    elif jg:
        v = "쥔 것을 넣어 두는 곳이 따로 있는 자리"
    else:
        v = "%s 자리가 공망에 걸린 자리" % word
    counted = [Counted(값=1 if jg else 0, 단위="개", 무엇="재고", 어디="지지"),
               Counted(값=1 if empty else 0, 단위="개",
                       무엇="공망에 걸린 %s" % group, 어디=f.gongmang or "순중")]
    return Claim(
        axis="vault", kind="verdict", verdict=v, counted=tuple(counted),
        ground=Ground(
            본것="지지의 재고와 일주 순중공망",
            이치="넣어 두는 곳과 비는 곳은 따로 셉니다",
            출처=SRC_TG),
        scene=Scene(물건=_prop(concern, 0, f),
                    한줄="%s 남았는데도 손에 쥔 느낌이 안 나던 달이 있었을 것이오."
                         % josa(_prop(concern, 0, f), "이", "가")),
        asked=0.7, needs="15900")


# ══ 축 ⑪ 올해 ════════════════════════════════════════════════════
def this_year(f, concern: str) -> Optional[Claim]:
    if not getattr(f, "year_gz", None):
        return None
    return Claim(
        axis="year", kind="verdict",
        verdict="올해가 그대에게 %s 드는 자리"
                % josa(f.year_ten_god, "으로", "로"),
        counted=(Counted(값=f.year_num, 단위="해", 무엇="올해", 어디="입춘으로 가른"),
                 Counted(값=f.age, 단위="살", 무엇="지금 나이", 어디="올해")),
        ground=Ground(
            본것="올해 천간을 일간에 대 본 것",
            이치="해가 바뀌는 자리는 설이 아니라 입춘이오",
            출처=SRC_TG),
        scene=Scene(물건=_prop(concern, 2, f),
                    한줄="올해 %s 손대야 하나 미뤄야 하나 망설인 적이 있소."
                         % josa(_prop(concern, 2, f), "을", "를")),
        asked=0.6, needs="19900")


#: 축의 차례 — **감정 곡선**입니다 (아픈 말 → 위로 → 셈·때 → 희망).
#: 마감은 `compose` 가 따로 세웁니다.
PRODUCERS: tuple[tuple[str, Callable], ...] = (
    ("scale",  scale),
    ("face",   face),
    ("lack",   lack),
    ("rarity", how_rare),
    ("hold",   hold),
    ("vault",  vault),
    ("palace", palace),
    ("turn",   turn),
    ("year",   this_year),
    ("helper", helper),
    ("chart",  chart),
)


def build(f, concern: str) -> list:
    """
    쓸 수 있는 주장을 **전부** 뽑습니다. 고르는 것은 `compose` 가 합니다.

    ★ 여기서 고르면 자리가 둘이 됩니다 — 이 집이 완료율·목패 값에서
      겪은 그 사고요.
    """
    out = []
    for name, fn in PRODUCERS:
        try:
            c = fn(f, concern)
        except ClaimError:
            raise
        if c is not None:
            out.append(c)
    return out


# ══ 축 ⑫ 같은 힘의 앞과 뒤 (뒤집기) ═══════════════════════════════
def shadow(f, concern: str) -> Optional[Claim]:
    """
    강점과 **같은 힘의 그림자** 짝.

    ★ 새 표를 쓰지 않습니다 (2026-09-28)

      `spine.read(f)` 가 척추 칸마다 `pairs`(강점↔그림자)와
      `contrast`(남들은↔그대는)를 이미 들고 있습니다. 척추 칸은 여덟
      글자에서 나오니 **사람마다 갈리고**, 이 집의 `sharp_audit` 이
      세는 「뒤집기」·「대조」가 바로 이 짝이오.

      v2 에 이 축이 없어서 자가 대조 0 · 뒤집기 0 을 찍었습니다. 제가
      글을 없앤 것이 아니라 **축이 없었던 것**이오.

    ★ 칭찬만 하지 않는 장치입니다. 강점만 내면 「좋은 이야기만 써 준다」
      가 되고, 그건 국내 후기에서 약점으로 적히는 자리입니다.
    """
    from .. import spine as spine_mod
    try:
        sp = spine_mod.read(f)
    except Exception:
        return None
    pairs = list(sp.get("pairs") or [])[:2]
    if not pairs:
        return None
    return Claim(
        axis="shadow", kind="pair",
        verdict="같은 힘이 앞과 뒤로 갈리는 자리",
        counted=(Counted(값=len(pairs), 단위="개", 무엇="앞뒤 짝",
                         어디=sp.get("name") or "척추"),
                 Counted(값=f.ten_gods.get(sp.get("key") or "", 0) or len(pairs),
                         단위="개", 무엇="이 줄기 글자", 어디="여섯 글자"
                         if not f.hour_known else "여덟 글자")),
        ground=Ground(
            본것="힘이 가장 많이 가는 줄기와 그 줄기가 만드는 앞뒤",
            이치="잘하는 일과 지치는 일은 같은 곳에서 나옵니다",
            출처=SRC_TG),
        scene=Scene(물건=_prop(concern, 1, f),
                    한줄="%s 앞에서 그 힘이 도움이 된 날과 짐이 된 날이 "
                         "따로 있었을 것이오." % _prop(concern, 1, f)),
        asked=0.5, needs="free")


# ★ `shadow` 는 표 아래에 적혀 있으니 여기서 끼웁니다 — 표를 위에 두고
#   함수를 아래 두면 이름이 아직 없습니다. 자리는 저울 바로 뒤요.
PRODUCERS = PRODUCERS[:1] + (("shadow", shadow),) + PRODUCERS[1:]


# ══════════════════════════════════════════════════════════════════
# 축 ⑬~㉔ — 이미 세어져 있으나 꼴이 없어 안 나가던 것들 (2026-09-28)
#
# ★ 새 표를 쓰지 않습니다. 부르는 자리만 만듭니다 —
#     pattern.read        짜임 43개
#     sinsal_read.split   신살 (물은 자리에 걸리는 것만)
#     topic.gyeok/johu    틀 · 철
#     topic.chung_pairs   부딪히는 글자
#     topic.gan_hap_with  묶이는 글자
#     topic.isolated      혼자 남은 글자
#     rarity.ilju         태어난 날 두 글자가 인구에 몇
#     f.ancestor          윗대 자리
#     spine.empty_group   없는 묶음
#     f.daeun             열 해 표
# ══════════════════════════════════════════════════════════════════


def _n_of(f, group: str) -> int:
    return {"재성": f.jae, "관성": f.gwan, "식상": f.sik,
            "비겁": f.bi, "인성": f.inn}.get(group, 0)


# ══ 축 ⑬ 짜임 ════════════════════════════════════════════════════
def weave(f, concern: str) -> Optional[Claim]:
    """★ 조건이 안 맞으면 **안 냅니다.** 없는 짜임을 말하면 소설이오."""
    from .. import pattern as pattern_mod
    try:
        rows = pattern_mod.read(f, concern, 1)
    except Exception:
        return None
    if not rows:
        return None
    row = rows[0]
    group, word = _axis_of(concern, getattr(f, "sex", ""))
    return Claim(
        axis="weave", kind="verdict",
        verdict=row.get("gloss") or "글자끼리 맞물린 자리",
        counted=(Counted(값=_n_of(f, group), 단위="자", 무엇=group,
                         어디="여섯 글자" if not f.hour_known else "여덟 글자"),
                 Counted(값=len(f.pillars) * 2, 단위="자", 무엇="세운 글자",
                         어디="전부")),
        ground=Ground(
            본것="글자 개수 사이의 관계 — %s (%s)"
                 % (row.get("name") or "짜임", row.get("why") or "개수와 자리"),
            이치="같은 개수라도 어느 글자와 맞물렸느냐로 갈립니다",
            출처=SRC_TG),
        scene=Scene(물건=_prop(concern, 0, f),
                    한줄="%s 놓고 앞뒤가 맞물려 돌아간 달이 있었을 것이오."
                         % josa(_prop(concern, 0, f), "을", "를")),
        asked=0.9, needs="free")


# ══ 축 ⑭ 옛 이름이 붙은 글자 (신살) ════════════════════════════════
def marks(f, concern: str) -> Optional[Claim]:
    """
    ★ 물은 자리에 걸리는 것만 폅니다 — 여덟 개를 다 펴면 그건 사전이오.
    ★ 이 이름으로 병·사고·재물을 단정하지 않습니다 (docs/14 §7).
    """
    from .. import sinsal_read
    try:
        on, _off = sinsal_read.split(f.sinsal or [], concern)
    except Exception:
        return None
    if not on:
        return None
    seats = sorted({s for row in on for s in (row.get("at") or [])})
    return Claim(
        axis="marks", kind="verdict",
        verdict="옛 이름이 붙은 글자가 걸린 자리",
        counted=(Counted(값=len(on), 단위="개", 무엇="걸린 이름",
                         어디=" · ".join(seats) or "여섯 글자"),
                 Counted(값=len(f.sinsal or []), 단위="개", 무엇="이름 전부",
                         어디="여섯 글자" if not f.hour_known else "여덟 글자")),
        ground=Ground(
            본것="옛사람이 이름 붙인 글자와 그 글자가 있는 자리",
            이치="이름이 아니라 그 이름이 어느 글자에 붙었는지를 봅니다",
            출처=SRC_SIN),
        scene=Scene(물건=_prop(concern, 2, f),
                    한줄="%s 두고 남들과 다른 결로 움직인 적이 있을 것이오."
                         % josa(_prop(concern, 2, f), "을", "를")),
        asked=0.6, needs="12900")


# ══ 축 ⑮ 부딪히는 글자 ════════════════════════════════════════════
def clash(f, concern: str) -> Optional[Claim]:
    n = topic_mod.chung_pairs(f)
    if not n and not getattr(f, "ilji_chung", False):
        return None
    return Claim(
        axis="clash", kind="verdict",
        verdict="맞부딪히는 글자가 있는 자리",
        counted=(Counted(값=n or 1, 단위="개", 무엇="부딪히는 짝",
                         어디="아래 글자끼리"),),
        ground=Ground(
            본것="아래 글자끼리 정면으로 맞서는 짝",
            이치="맞선 글자는 한쪽이 흔들릴 때 같이 흔들립니다",
            출처=SRC_TG),
        scene=Scene(물건=_prop(concern, 1, f),
                    한줄="%s 사이에 두고 마음이 두 쪽으로 갈린 날이 있었을 것이오."
                         % josa(_prop(concern, 1, f), "을", "를")),
        asked=0.7, needs="9900")


# ══ 축 ⑯ 묶이는 글자 ══════════════════════════════════════════════
def tied(f, concern: str) -> Optional[Claim]:
    """
    ★ 「삼합는」 이 나갔습니다 (2026-09-28). `hap_group` 은 **묶음 이름**을
      돌려주는데 그것을 글자 자리에 넣었습니다. 글자가 있을 때만 글자를
      대고, 묶음일 때는 그 묶음이 든 아래 글자를 댑니다.
    """
    gan = topic_mod.gan_hap_with(f)
    grp = topic_mod.hap_group(f)
    if not gan and not (grp and grp[0]):
        return None
    where = gan or " · ".join(p["ji"] for p in f.pillars)
    return Claim(
        axis="tied", kind="verdict",
        verdict="다른 글자와 묶이는 글자가 있는 자리",
        counted=(Counted(값=1, 단위="개", 무엇="묶이는 글자", 어디=where),),
        ground=Ground(
            본것="서로 짝이 되어 묶이는 글자",
            이치="묶인 글자는 제 일을 하다 상대 일까지 맡습니다",
            출처=SRC_TG),
        scene=Scene(물건=_prop(concern, 3, f),
                    한줄="%s 맡았다가 남의 몫까지 하게 된 적이 있을 것이오."
                         % josa(_prop(concern, 3, f), "을", "를")),
        asked=0.5, needs="15900")


# ══ 축 ⑰ 틀 (격) ═════════════════════════════════════════════════
def frame(f, concern: str) -> Optional[Claim]:
    g = topic_mod.gyeok(f)
    if not g:
        return None
    return Claim(
        axis="frame", kind="verdict",
        verdict="태어난 달 글자가 틀을 잡은 자리",
        counted=(Counted(값=_n_of(f, _axis_of(concern,
                                             getattr(f, "sex", ""))[0]),
                         단위="자", 무엇="물어보신 자리 글자",
                         어디="여섯 글자" if not f.hour_known else "여덟 글자"),
                 Counted(값=len(f.pillars), 단위="칸", 무엇="세운 기둥",
                         어디="전부")),
        ground=Ground(
            본것="태어난 달의 아래 글자와 그 글자가 밖으로 났는가 (%s)" % g,
            이치="태어난 달이 그 사람의 틀을 먼저 잡습니다",
            출처=SRC_TG),
        scene=Scene(물건=_prop(concern, 4, f),
                    한줄="%s 다룰 때 남과 다른 순서로 한다는 말을 들은 적이 있소."
                         % josa(_prop(concern, 4, f), "을", "를")),
        asked=0.6, needs="15900")


# ══ 축 ⑱ 철 (조후) ════════════════════════════════════════════════
def season(f, concern: str) -> Optional[Claim]:
    j = topic_mod.johu(f)
    if not j:
        return None
    return Claim(
        axis="season", kind="verdict",
        verdict="태어난 철이 %s 자리" % j,
        counted=(Counted(값=f.elements.get("화", 0), 단위="개", 무엇="불",
                         어디="글자 속까지"),
                 Counted(값=f.elements.get("수", 0), 단위="개", 무엇="물",
                         어디="글자 속까지")),
        ground=Ground(
            본것="태어난 달과 불·물의 무게",
            이치="추운 철에 난 사람은 따뜻한 것이 먼저 필요합니다",
            출처=SRC_ST),
        scene=Scene(물건=_prop(concern, 1, f),
                    한줄="%s 앞에서 몸이 먼저 지친 계절이 따로 있었을 것이오."
                         % _prop(concern, 1, f)),
        asked=0.4, needs="9900")


# ══ 축 ⑲ 태어난 날 두 글자가 인구에 몇 ════════════════════════════
def birthday(f, concern: str) -> Optional[Claim]:
    row = (rarity_mod.ilju(f) or {})
    per = row.get("per10k")
    if per is None:
        return None
    return Claim(
        axis="birthday", kind="solace",
        verdict="태어난 날 두 글자를 같이 쓰는 사람이 있는 자리",
        counted=(Counted(값=per, 단위="명", 무엇="같은 날 두 글자",
                         어디="1만 명에"),),
        ground=Ground(
            본것="태어난 날 두 글자를 인구에서 센 값",
            이치="같은 두 글자를 쓰는 사람은 같은 자리에서 걸립니다",
            출처="성신당 희소도 표"),
        asked=0.2, needs="12900")


# ══ 축 ⑳ 윗대 자리 ════════════════════════════════════════════════
def forebears(f, concern: str) -> Optional[Claim]:
    a = getattr(f, "ancestor", None) or {}
    if not a.get("pillar"):
        return None
    return Claim(
        axis="forebears", kind="verdict",
        verdict="윗대에서 물려받은 것이 %s 자리"
                % (a.get("stance") or "있는"),
        counted=(Counted(값=1, 단위="칸", 무엇="윗대 글자",
                         어디=a["pillar"]),
                 Counted(값=len(a.get("elements") or []), 단위="개",
                         무엇="윗대 글자의 기운", 어디="두 글자")),
        ground=Ground(
            본것="태어난 해 두 글자와 그 글자가 채우면 좋은 것을 돕는가",
            이치="태어난 해 두 글자는 윗대와 물려받은 것을 봅니다",
            출처=SRC_PAL),
        scene=Scene(물건=_prop(concern, 0, f),
                    한줄="%s 두고 집에서 배운 방식대로 한 적이 있을 것이오."
                         % josa(_prop(concern, 0, f), "을", "를")),
        asked=0.3, needs="19900")


# ══ 축 ㉑ 혼자 남은 글자 ═══════════════════════════════════════════
def alone(f, concern: str) -> Optional[Claim]:
    el = next((e for e in ("목", "화", "토", "금", "수")
               if topic_mod.isolated(f, e)), None)
    if not el:
        return None
    return Claim(
        axis="alone", kind="verdict",
        verdict="%s 혼자 남은 자리" % josa(EL_WORD[el], "이", "가"),
        counted=(Counted(값=topic_mod.visible(f, el), 단위="자",
                         무엇=EL_WORD[el], 어디="겉에"),
                 Counted(값=f.elements[el], 단위="개",
                         무엇="%s 무게" % EL_WORD[el], 어디="글자 속까지")),
        ground=Ground(
            본것="그 기운이 겉에 있으나 도와줄 글자가 곁에 없는가",
            이치="곁에 도울 글자가 없는 기운은 쓰다 말기 쉽습니다",
            출처=SRC_ST),
        scene=Scene(물건=_prop(concern, 2, f),
                    한줄="%s 혼자 붙들고 끝까지 간 일이 있었을 것이오."
                         % josa(_prop(concern, 2, f), "을", "를")),
        asked=0.5, needs="9900")


# ══ 축 ㉒ 없는 묶음 ═══════════════════════════════════════════════
def missing(f, concern: str) -> Optional[Claim]:
    from .. import spine as spine_mod
    try:
        g = spine_mod.empty_group(f)
    except Exception:
        return None
    if not g:
        return None
    return Claim(
        axis="missing", kind="solace",
        verdict="%s 한 자도 없는 자리"
                % josa(PLAIN_MISS.get(g, g), "이", "가"),
        counted=(Counted(값=0, 단위="자", 무엇=g,
                         어디="여섯 글자" if not f.hour_known else "여덟 글자"),),
        ground=Ground(
            본것="다섯 묶음을 나란히 세어 빈 묶음을 찾은 것",
            이치="없는 묶음이 하는 일은 남보다 힘이 더 듭니다",
            출처=SRC_TG),
        asked=0.4, needs="9900")


#: 없는 묶음을 쉬운 말로.
PLAIN_MISS = {"재성": "쥐는 글자", "관성": "그대를 누르고 잡아 주는 글자",
              "식상": "그대가 밖으로 내놓는 글자",
              "인성": "그대를 채워 주는 글자",
              "비겁": "그대 몫을 같이 나누는 글자"}


# ══ 축 ㉓ 열 해 표 ════════════════════════════════════════════════
def decades(f, concern: str) -> Optional[Claim]:
    """★ 표를 내놓고 읽는 법만 적지 마시오 — 물은 자리를 **켭니다**."""
    if not f.daeun:
        return None
    from ..constants import TEN_GOD_GROUP
    group, word = _axis_of(concern, getattr(f, "sex", ""))
    lit = [d for d in f.daeun
           if TEN_GOD_GROUP.get(d.get("ten_god") or "") == group]
    return Claim(
        axis="decades", kind="verdict",
        verdict="열 해마다 바뀌는 때가 %s인 자리" % count_word(len(f.daeun), "칸"),
        counted=(Counted(값=len(f.daeun), 단위="칸", 무엇="열 해 표",
                         어디="전부"),
                 Counted(값=len(lit), 단위="칸", 무엇="%s 켜지는 때" % word,
                         어디="열 해 표"),
                 Counted(값=f.age, 단위="살", 무엇="지금 나이", 어디="올해")),
        ground=Ground(
            본것="열 해마다 바뀌는 글자와 그 글자가 물어보신 자리에 걸리는가",
            이치="여덟 글자는 안 바뀌고 바뀌는 것은 열 해마다 도는 글자요",
            출처=SRC_DA),
        scene=Scene(물건=_prop(concern, 4, f),
                    한줄="%s 열어 놓고 앞으로 몇 해를 셈해 본 적이 있을 것이오."
                         % josa(_prop(concern, 4, f), "을", "를")),
        asked=0.8, needs="12900")


# ══ 축 ㉔ 시각을 모르면 못 보는 것 ═════════════════════════════════
def unknown_hour(f, concern: str) -> Optional[Claim]:
    """
    ★ 모르는 것을 **모른다고** 적는 자리.

      시각 미상 손님에게 「시각 두 글자에 받쳐 주는 글자가 없소」 라 하던
      자리가 있었습니다 — 안 선 글자를 **없는 것**으로 적으면 그건 낮
      열두 시로 채우는 것과 같소.
    """
    if f.hour_known:
        return None
    return Claim(
        axis="unknown_hour", kind="ledger",
        verdict="태어난 시각을 몰라 두 글자를 비워 둔 자리",
        counted=(Counted(값=len(f.pillars) * 2, 단위="자", 무엇="세운 글자",
                         어디="여섯 글자"),
                 Counted(값=2, 단위="자", 무엇="비워 둔 글자",
                         어디="태어난 시각 두 글자")),
        ground=Ground(
            본것="받은 것과 받지 못한 것을 가른 자리",
            이치="모르는 글자는 채우지 않고 비워 둡니다",
            출처="자평 명리"),
        asked=0.0, needs="free")


# ★ 새 축을 차례에 끼웁니다 — 이름은 `render.SHAPES` 와 짝이 맞아야 합니다.
PRODUCERS = PRODUCERS + (
    ("weave", weave), ("marks", marks), ("clash", clash), ("tied", tied),
    ("frame", frame), ("season", season), ("birthday", birthday),
    ("forebears", forebears), ("alone", alone), ("missing", missing),
    ("decades", decades), ("unknown_hour", unknown_hour),
)


# ══════════════════════════════════════════════════════════════════
# 축 ㉕㉖ — 비싼 자리만 여는 **다른 종류** (2026-09-28)
#
# ★ 값을 「더 많이」로만 올리지 마시오.
#
#   등급을 넷으로 갈라 놓고 축만 둘 더 열면 손님 눈에는 「더 길다」이지
#   「더 깊다」가 아닙니다. 비싼 자리에는 **싼 자리에 아예 없는 종류**를
#   답니다 — 지나온 자리와 「내가 틀렸다면」.
#
#   「내가 틀렸다면」 은 이 집이 가진 가장 센 신뢰 장치입니다. 콜드리딩의
#   알리바이 규칙(Hyman 1977 규칙 3 — 「안 맞으면 손님 탓」)을 뒤집어
#   **틀릴 조건을 우리가 먼저 적는** 것이오. 그래서 이 축은 반드시
#   반증가능해야 하고, 그 값을 `counted` 가 들고 있습니다.
# ══════════════════════════════════════════════════════════════════


def hindsight(f, concern: str) -> Optional[Claim]:
    """
    지나온 자리 — **무슨 일이 있었다고 적지 않습니다.**

    칸을 가리키고 나이를 대면 손님이 그 자리에서 맞춰 봅니다. 사건을
    적으면 그건 점이 아니라 소설이오.
    """
    past = [d for d in (f.daeun or []) if d["start_age"] + 10 <= f.age]
    if not past:
        return None
    return Claim(
        axis="hindsight", kind="depth",
        verdict="이미 지나온 때가 있는 자리",
        counted=(Counted(값=len(past), 단위="칸", 무엇="지나온 때",
                         어디="열 해 표"),
                 Counted(값=past[0]["start_age"], 단위="살", 무엇="첫 칸이 연 나이",
                         어디="열 해 표"),
                 Counted(값=f.age, 단위="살", 무엇="지금 나이", 어디="올해")),
        ground=Ground(
            본것="열 해마다 바뀌는 글자 가운데 이미 지나간 칸과 그 나이",
            이치="지나온 칸은 맞춰 볼 수 있고 앞선 칸은 그럴 수 없습니다",
            출처=SRC_DA),
        scene=Scene(물건=_prop(concern, 0, f),
                    한줄="그 무렵 %s 어땠는지는 그대가 아오."
                         % josa(_prop(concern, 0, f), "이", "가")),
        asked=0.6, needs="15900")


def counter(f, concern: str) -> Optional[Claim]:
    """
    「내가 틀렸다면」 — **틀릴 조건을 우리가 먼저 적습니다.**

    ★ 「맞는 경험이 없으면 내 이야기로 받아들이지 않아도 되오」 같은 면책과
      다릅니다. 면책은 아무것도 금지하지 않아 어떤 관찰에서도 살아남습니다.
      이 축은 **어떤 관찰이면 우리가 틀린 것인지**를 수로 적습니다.
    """
    group, word = _axis_of(concern, getattr(f, "sex", ""))
    n = {"재성": f.jae, "관성": f.gwan, "식상": f.sik,
         "비겁": f.bi, "인성": f.inn}.get(group)
    if n is None:
        return None
    el = f.weak_el
    if not el:
        return None
    return Claim(
        axis="counter", kind="depth",
        verdict="이 풀이가 틀렸다면 그렇게 보이는 자리",
        counted=(Counted(값=n, 단위="자", 무엇=group,
                         어디="여섯 글자" if not f.hour_known else "여덟 글자"),
                 Counted(값=topic_mod.visible(f, el), 단위="자",
                         무엇=EL_WORD[el], 어디="겉에"),
                 Counted(값=int(f.deuk_ryeong) + int(f.deuk_ji), 단위="개",
                         무엇="받쳐 주는 글자", 어디="태어난 달과 아래 글자")),
        ground=Ground(
            본것="이 풀이가 딛고 선 수 셋 — 물어보신 자리 · 가장 얇은 것 · 받침",
            이치="틀릴 조건을 적어 두면 맞는지 그대가 셀 수 있습니다",
            출처="성신당 근거 규칙"),
        scene=Scene(물건=_prop(concern, 2, f),
                    한줄="%s 두고 위에 적은 것과 반대였다면 우리가 틀린 것이오."
                         % josa(_prop(concern, 2, f), "을", "를")),
        asked=0.5, needs="19900")


PRODUCERS = PRODUCERS + (("hindsight", hindsight), ("counter", counter))
