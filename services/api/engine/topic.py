# -*- coding: utf-8 -*-
"""
고민축 — 물으신 자리에서 **무엇을 세는가**. docs/20_고민축_설계.md

★ 왜 생겼나 (2026-09-06)

  손님이 짚었소 — "돈에 대해 물었는데 돈 관련 이야기는 전혀 구현이
  안 되어 있어."

  맞습니다. 09-05 에 고친 것은 「여섯 칸에서 **낱말**이 갈리는가」
  였습니다. 훅 다섯 단과 리포트 한 컷이 고민마다 다른 낱말을 골라
  썼습니다. 그런데 **세는 값**은 그대로였습니다 —

      돈을 물어도   재성을 「개수 하나」로만 보고
      몸을 물어도   오행을 「많다·적다」로만 보고

  실무가 돈을 볼 때 세는 것은 재성의 **갈래(정재·편재)**, **투출**,
  **궁위**, **재고**, **공망·충**, 그리고 **대운에서 그 자리가 드는
  때**입니다. 그걸 한 줄도 안 세고 있었습니다.

★ 여기서 하는 일

      ① 저울   그 고민에서 세는 값 넉다섯 칸        scale()
      ② 때     그 자리가 대운에서 언제 바뀌는가      turn()
      ③ 얼굴   넉 자가 이 자리에서 어떤 꼴로 나오나  face()
      ④ 물음   더 물어야 할 것 하나                  ask_spec() · ask_cut()

  ② 짜임(관계)은 `engine/pattern.py` 가 이미 하는 일이라 거기서
  늘렸습니다. 한 자리에 두 벌을 두지 않습니다.

★ 지어내지 않습니다

  판정은 전부 Feature Store 값입니다. 조건이 안 맞는 칸은 **안 냅니다.**
  문장은 `seed/topic.json` 에만 있고, 여기서는 어느 칸을 고를지만
  정합니다. 없는 조합은 TopicError 로 터뜨립니다.

★ 넘지 않는 선

  몸 축은 **병을 말하지 않고 결을 말합니다.** 옛 표가 오행을 어느
  장부에 붙여 읽었는지는 사실이라 전할 수 있지만, 「그대는 어디가
  나쁘오」는 진단이라 금지입니다 (docs/11 · guard).

  돈 축은 **시점 지시**를 안 합니다. 「재성 대운은 마흔둘부터」는
  달력이고, 「그때 사시오」는 지시입니다. 앞은 내고 뒤는 안 냅니다.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

from . import guard
from . import why as _why
from .constants import (
    CHUNG, CONTROLS, CONTROLLED_BY, ELEMENT_OF_GAN, ELEMENT_OF_JI,
    GENERATES, GENERATED_BY, HIDDEN, TEN_GOD_GROUP, ten_god,
)

SEED = Path(__file__).resolve().parents[3] / "seed"

CONCERNS = ("money", "work", "love", "people", "dir", "health", "real_estate")

# 한 컷에 세는 칸 수. 다섯을 넘기면 그건 저울이 아니라 명세서요.
MAX_ROWS = 5


class TopicError(KeyError):
    """표에 없는 조합. 지어내지 않고 터뜨린다."""


class TopicInputError(ValueError):
    """손님이 고른 것이 목록에 없음. 화면 말투로 되돌려 준다."""


# ══════════════════════════════════════════════════════════
# 확정값 — 바꾸면 기존 결과가 달라진다
# ══════════════════════════════════════════════════════════
#
# ★ 재고(財庫) — 재성 오행이 갈무리되는 지지.
#   土庫를 辰으로 잡습니다. 戌로 보는 유파도 있으나 **한 벌만** 씁니다.
#   이건 계산이 아니라 선택이라 여기 못박습니다 (docs/20 §4-1).
GO_JI = {"목": "未", "화": "戌", "토": "辰", "금": "丑", "수": "辰"}

# 기운이 도는 쪽. 「좋은 방향」이 아니라 **도는 쪽**으로만 씁니다.
WHERE = {"목": "동", "화": "남", "토": "가운데", "금": "서", "수": "북"}

# 십신 열을 다섯 묶음으로
GROUP_OF = dict(TEN_GOD_GROUP)

# ══════════════════════════════════════════════════════════
# 지지끼리의 관계 — 확정표 (2026-09-06)
# ══════════════════════════════════════════════════════════
#
# ★ 왜 늘렸나
#
#   손님이 「나머지도 진짜 사주에 맞게 채우라」 하셨소. 일·사랑·사람·
#   방향을 실무가 볼 때 세는 것은 개수 말고도 **글자끼리 맺는 관계**요 —
#   형(刑)은 다툼·구설·수술 자리로, 삼합·방합은 판이 한쪽으로 뭉치는
#   자리로, 천간합은 묶여서 제 노릇을 못 하는 자리로 읽소.
#
#   전부 **셀 수 있습니다.** 지지 넷을 놓고 표와 맞춰 보면 끝이오.
#
# ★ 유파 선택입니다 — 한 벌만 씁니다
#
#   형에는 삼형(寅巳申·丑戌未) · 상형(子卯) · 자형(辰辰·午午·酉酉·亥亥)
#   까지 넣고, 파(破)·해(害)는 **안 씁니다**. 유파마다 갈리고, 이 집은
#   못박은 것만 냅니다. 바꾸면 기존 결과가 달라집니다 (docs/20 §6).
SAMHYEONG = (("寅", "巳", "申"), ("丑", "戌", "未"))   # 삼형 — 셋이 다 있어야
SANGHYEONG = ("子", "卯")                              # 상형 — 둘
JAHYEONG = ("辰", "午", "酉", "亥")                     # 자형 — 같은 글자 둘

# 삼합 — 셋이 모이면 그 오행으로 판이 굳소. 가운데(왕지)가 있어야 반합.
SAMHAP = {("申", "子", "辰"): ("수", "子"), ("寅", "午", "戌"): ("화", "午"),
          ("巳", "酉", "丑"): ("금", "酉"), ("亥", "卯", "未"): ("목", "卯")}
# 방합 — 계절이 통째로 모인 것
BANGHAP = {("寅", "卯", "辰"): "목", ("巳", "午", "未"): "화",
           ("申", "酉", "戌"): "금", ("亥", "子", "丑"): "수"}
# 천간합 — 묶이면 제 노릇을 덜 하오
GAN_HAP = {"甲": "己", "己": "甲", "乙": "庚", "庚": "乙", "丙": "辛",
           "辛": "丙", "丁": "壬", "壬": "丁", "戊": "癸", "癸": "戊"}


def hyeong(f) -> str:
    """형(刑)이 어떤 꼴로 걸렸는가. 없으면 빈 문자열."""
    jis = [p["ji"] for p in f.pillars]
    for trio in SAMHYEONG:
        if all(j in jis for j in trio):
            return "삼형"
    if all(j in jis for j in SANGHYEONG):
        return "상형"
    for j in JAHYEONG:
        if jis.count(j) >= 2:
            return "자형"
    # 삼형 중 둘만 — 옛 책은 이것도 형으로 보되 가볍게 읽소
    for trio in SAMHYEONG:
        if sum(1 for j in trio if j in jis) >= 2:
            return "반형"
    return ""


def hyeong_at(f) -> list:
    """형에 걸린 지지들. 없으면 빈 목록. (일지가 여기 드는지가 중요하오)"""
    jis = [p["ji"] for p in f.pillars]
    for trio in SAMHYEONG:
        if all(j in jis for j in trio):
            return list(trio)
    if all(j in jis for j in SANGHYEONG):
        return list(SANGHYEONG)
    for j in JAHYEONG:
        if jis.count(j) >= 2:
            return [j]
    for trio in SAMHYEONG:
        got = [j for j in trio if j in jis]
        if len(got) >= 2:
            return got
    return []


def hap_group(f) -> tuple:
    """
    지지가 무리를 이뤘는가. (꼴, 오행) — 없으면 ("", "").

    삼합 > 방합 > 반합 차례로 봅니다. 굳은 정도가 그 차례요.
    """
    jis = [p["ji"] for p in f.pillars]
    for trio, (el, king) in SAMHAP.items():
        if all(j in jis for j in trio):
            return "삼합", el
    for trio, el in BANGHAP.items():
        if all(j in jis for j in trio):
            return "방합", el
    for trio, (el, king) in SAMHAP.items():
        if king in jis and sum(1 for j in trio if j in jis) >= 2:
            return "반합", el
    return "", ""


def gan_hap_with(f) -> str:
    """일간이 다른 천간과 합하는가. 그 글자. 없으면 빈 문자열."""
    mate = GAN_HAP.get(f.day_gan)
    if not mate:
        return ""
    for p in f.pillars:
        if p.get("label") != "일주" and p["gan"] == mate:
            return mate
    return ""


def gyeok(f) -> str:
    """
    격(格) — **월지에서 무엇으로 서는가.** 십신 이름으로 돌려줍니다.

    ★ 실무의 차례를 그대로 따릅니다 —
        ① 월지 지장간 중 **천간에 투출한 것**이 있으면 그 십신이 격
        ② 없으면 월지 **본기**의 십신이 격
        ③ 월지가 일간의 록(祿)이면 건록격, 겁재 자리면 양인격

      격은 「그 사람이 무엇으로 서는가」를 한 낱말로 잡는 자리라,
      일·진로를 물을 때 실무가 가장 먼저 봅니다. 다만 성패·구응까지는
      안 봅니다 — 그건 유파가 갈리고, 이 집은 **셀 수 있는 데까지**만
      냅니다.
    """
    month = None
    for p in f.pillars:
        if p.get("label") == "월주":
            month = p
    if not month:
        return ""
    hidden = [g for g, _ in HIDDEN[month["ji"]]]
    gans = [p["gan"] for p in f.pillars if p.get("label") != "일주"]

    # ③ 먼저 봅니다 — 록·인 자리는 투출과 상관없이 그 이름으로 서오.
    bon = ten_god(hidden[0], f.day_gan)
    if bon == "비견":
        return "건록격"
    if bon == "겁재":
        return "양인격"
    # ① 투출
    #
    # ★ 비견·겁재는 **격 이름으로 안 씁니다.** 그 자리는 위에서 이미
    #   건록격·양인격으로 부르고, 월지 본기가 아닌 데서 비겁이 튀어
    #   나왔다고 「비견격」이라 하지는 않습니다. 실제로 그 이름이
    #   나와 표에서 터진 자리가 있었습니다.
    for h in hidden:
        if h in gans:
            got = ten_god(h, f.day_gan)
            if got not in ("비견", "겁재"):
                return got + "격"
    # ② 본기
    return bon + "격"


@lru_cache(maxsize=1)
def table() -> dict:
    raw = json.loads((SEED / "topic.json").read_text("utf-8"))
    out = {k: v for k, v in raw.items() if k != "_"}
    # 부동산은 별도 고민으로 운영하되 기존 명리 계산 표를 재사용한다.
    out.setdefault("ASK", {})["real_estate"] = {
        "title": "집·토지·상가를 움직일 때 무엇을 먼저 확인할까",
        "q": "지금 가장 가까운 부동산 고민은 무엇인가요?",
        "options": {
            "buy": "매수·분양 시기",
            "sell": "매도·갈아타기 시기",
            "move": "전세·월세·이사",
            "invest": "투자·상가·토지",
        },
        "q2": "결정을 늦추게 만드는 현실 조건은 무엇인가요?",
        "options2": {
            "price": "가격·대출 부담",
            "timing": "시기 판단",
            "family": "가족·공동명의",
            "contract": "계약 조건",
        },
    }
    # 모든 고민은 「무슨 분야인가」에서 멈추지 않고,
    # 지금 실제로 어느 단계인지와 이번 상담에서 얻고 싶은 결론까지
    # 확인해야 같은 말의 반복을 피할 수 있다. 기존 ASK 표를 깨지 않도록
    # 공통 표에 두 단계만 덧붙인다. 프론트는 q4/q5를 이미 지원한다.
    detail_asks = {
        "money": {
            "q4": "지금 돈 문제는 어느 단계까지 와 있소?",
            "options4": {"notice": "문제를 막 알아차림", "plan": "계획을 세우는 중", "action": "이미 실행 중", "debt": "빚·연체를 정리 중", "repeat": "같은 문제가 반복됨"},
            "q5": "이번 상담에서 반드시 숫자로 확인하고 싶은 것은 무엇이오?",
            "options5": {"income": "수입을 늘릴 지점", "leak": "새는 돈의 원인", "debt": "빚을 줄이는 순서", "choice": "지금 선택의 우선순위", "habit": "반복되는 소비 습관"},
        },
        "work": {
            "q4": "일에서 지금 실제로 막힌 장면은 무엇이오?",
            "options4": {"entry": "시작·이직 전", "load": "업무가 몰림", "boss": "상사·조직과 충돌", "result": "성과·평가가 안 나옴", "exit": "그만둘지 고민 중"},
            "q5": "이번 해석에서 가장 먼저 정하고 싶은 결과는 무엇이오?",
            "options5": {"role": "내가 맡을 일의 범위", "move": "이직·이동 여부", "skill": "키울 능력 한 가지", "pay": "연봉·수입의 방향", "rest": "번아웃을 막는 기준"},
        },
        "love": {
            "q4": "두 사람 사이에서 마지막으로 실제로 벌어진 일은 무엇이오?",
            "options4": {"start": "고백·관계 시작 전", "silence": "연락·대화가 끊김", "fight": "같은 이유로 다툼", "future": "결혼·동거를 의논 중", "break": "이별 후 재회 고민"},
            "q5": "이번 상담에서 상대와 나 사이 무엇을 가장 분명히 알고 싶소?",
            "options5": {"heart": "상대의 현재 마음", "cause": "반복되는 다툼의 원인", "choice": "계속할지 멈출지", "future": "결혼·장기 가능성", "talk": "지금 꺼낼 대화의 순서"},
        },
        "people": {
            "q4": "그 관계에서 최근 실제로 일어난 장면은 무엇이오?",
            "options4": {"message": "답장·말투가 달라짐", "request": "부탁·금전 문제가 생김", "conflict": "선 넘는 말·행동", "group": "가족·직장 안의 문제", "cut": "거리를 두려는 중"},
            "q5": "이번 상담에서 관계의 어느 선을 정하고 싶소?",
            "options5": {"trust": "믿을 수 있는지", "boundary": "어디까지 받아줄지", "talk": "어떻게 말할지", "distance": "얼마나 거리를 둘지", "repair": "다시 회복할 수 있는지"},
        },
        "dir": {
            "q4": "두 선택지 중 지금 실제로 먼저 해야 하는 일은 무엇이오?",
            "options4": {"apply": "지원·신청부터", "talk": "누군가와 상의부터", "number": "돈·조건 계산부터", "date": "마감·시한 확인부터", "pause": "일단 멈추고 관찰 중"},
            "q5": "결정이 났다고 느끼려면 무엇이 분명해야 하오?",
            "options5": {"money": "감당할 비용", "people": "함께할 사람의 동의", "risk": "잃을 수 있는 것", "proof": "확인해야 할 정보", "date": "움직일 날짜"},
        },
        "health": {
            "q4": "불편함이 일상에서 가장 먼저 드러나는 때는 언제오?",
            "options4": {"morning": "아침에 일어날 때", "work": "일·집중할 때", "meal": "먹고 난 뒤", "night": "잠들기 전", "stress": "긴장·감정이 커질 때"},
            "q5": "이번 상담에서 생활의 무엇부터 바꾸고 싶소?",
            "options5": {"sleep": "수면 시간", "meal": "식사 리듬", "move": "움직임·운동", "rest": "쉬는 방식", "check": "검사를 받을 기준"},
        },
        "real_estate": {
            "q": "지금 가장 가까운 부동산 고민은 무엇인가요?",
            "options": {"buy": "내 집 매수·분양", "sell": "매도·갈아타기", "move": "전세·월세·이사", "invest": "상가·토지 투자", "auction": "경매·공매", "inherit": "상속·증여·공동명의"},
            "q2": "결정을 늦추게 만드는 현실 조건은 무엇인가요?",
            "options2": {"price": "가격·대출 부담", "timing": "시기·시장 판단", "family": "가족·공동명의", "contract": "계약·권리 조건", "region": "지역·입지 선택", "tax": "세금·자금 계획"},
            "q3": "그 부동산으로 최종적으로 이루려는 목적은 무엇인가요?",
            "options3": {"live": "직접 거주", "rent": "임대 수익", "capital": "시세 차익", "rebuild": "재건축·개발", "commercial": "사업장 운영", "inheritance": "가족에게 이전"},
            "q4": "현재 거래는 실제로 어느 단계까지 진행됐나요?",
            "options4": {"research": "정보를 모으는 중", "viewed": "현장을 보고 비교 중", "loan": "대출·자금 심사 중", "negotiate": "가격·조건을 협의 중", "contract": "계약서·잔금을 확인 중", "owned": "이미 보유한 집을 다시 판단 중"},
            "q5": "이번 상담에서 반드시 확인하고 싶은 한 가지는 무엇인가요?",
            "options5": {"afford": "내 자금으로 감당 가능한 범위", "timing": "지금 움직일지 기다릴지", "risk": "계약·권리의 위험", "return": "수익·보유 가치", "family": "가족 간 지분·갈등", "next": "당장 할 다음 행동"},
        },
    }
    for concern, detail in detail_asks.items():
        out.setdefault("ASK", {}).setdefault(concern, {}).update(detail)
    def fill(node):
        if isinstance(node, dict):
            for value in list(node.values()):
                fill(value)
            if "money" in node and "real_estate" not in node:
                node["real_estate"] = node["money"]
        elif isinstance(node, list):
            for value in node:
                fill(value)
    fill(out)
    return out


def _pick(*keys) -> str:
    node = table()
    for k in keys:
        if not isinstance(node, dict) or k not in node:
            raise TopicError("topic.%s 없음" % "][".join(str(x) for x in keys))
        node = node[k]
    return node


# ══════════════════════════════════════════════════════════
# 자리표시 뒤의 조사 — lens_cuts 와 같은 규칙
# ══════════════════════════════════════════════════════════
# ★ 자리표시와 조사 **사이에 태그가 낍니다.**
#
#   「<b>{strong}</b>이 여덟 글자에 겹쳐 있소」 라고 써 두면 조사 앞에
#   `</b>` 가 있어, 받침을 보는 자리에서 **글자를 못 찾습니다.**
#   손님 화면에 「나무 이 여덟 글자에」 가 그대로 나갔습니다.
#   lens_cuts 에서 한 번 겪은 것과 같은 자리인데, 거기는 굵은 글씨를
#   자리표시 밖에 두어 안 걸렸을 뿐입니다. 태그를 넘어서 봅니다.
_TAGS = r"((?:</?[a-zA-Z][^>]*>)*)"
_JOSA_AFTER = re.compile(
    r"\{(\w+)\}" + _TAGS + r"\s*([이가은는을를와과])(?=\s|$|[.,!?)\]<])")
# ★ 서술격도 받침을 봅니다 — 「하나요」 「둘이오」.
#   수를 말로 내면(count_word) 받침이 낱말마다 달라, 손으로 박으면
#   반은 틀립니다. 「관성이 하나이오」 가 그 자리였습니다.
_COPULA_AFTER = re.compile(
    r"\{(\w+)\}" + _TAGS + r"\s*(이오|요)(?=\s|$|[.,!?)\]<])")
# ★ 「으로/로」 도 같은 자리입니다 (2026-09-15).
#   이 짝이 표에 없어서 `{weak}으로` 가 「불으로」 로 그대로 나갔습니다.
#   받침을 보고 고르는 조사는 여기 한 벌에 다 있어야, 다음에 쓰는
#   사람이 손으로 박지 않습니다 (CLAUDE.md 「자리표시 뒤에 조사를
#   손으로 박기」).
_RO_AFTER = re.compile(
    r"\{(\w+)\}" + _TAGS + r"\s*(으로|로)(?=\s|$|[.,!?)\]<])")
_JOSA_PAIR = {"이": ("이", "가"), "가": ("이", "가"),
              "은": ("은", "는"), "는": ("은", "는"),
              "을": ("을", "를"), "를": ("을", "를"),
              "와": ("과", "와"), "과": ("과", "와"),
              "이오": ("이오", "요"), "요": ("이오", "요"),
              "으로": ("으로", "로"), "로": ("으로", "로")}


def _batchim(val: str) -> bool:
    """마지막 글자에 받침이 있는가. 한자는 **읽는 소리**로 고른다."""
    from .bank import has_batchim
    from .constants import GAN_SOUND, JI_SOUND
    if not val:
        return False
    last = val[-1]
    if "가" <= last <= "힣":
        return has_batchim(val)
    sound = JI_SOUND.get(last) or GAN_SOUND.get(last)
    return has_batchim(sound) if sound else False


def _rieul(val: str) -> bool:
    """마지막 글자의 받침이 ㄹ 인가. 「으로」 와 「로」 를 가르는 자리요."""
    if not val:
        return False
    last = val[-1]
    if not ("가" <= last <= "힣"):
        from .constants import GAN_SOUND, JI_SOUND
        snd = JI_SOUND.get(last) or GAN_SOUND.get(last)
        if not snd:
            return False
        last = snd[-1]
        if not ("가" <= last <= "힣"):
            return False
    return (ord(last) - 0xAC00) % 28 == 8      # ㄹ


def _fmt(tpl: str, w: dict) -> str:
    """자리표시를 갈아 끼우되 뒤따르는 조사를 받침에 맞춘다."""
    def sub(m):
        key, tags, j = m.group(1), m.group(2), m.group(3)
        if key not in w:
            return m.group(0)
        val = str(w[key])
        if not val:
            return val
        hard, soft = _JOSA_PAIR[j]
        # ★ 「으로/로」 만 셈이 다릅니다 — ㄹ 받침은 「로」 를 씁니다
        #   (불로 · 물로 · 하늘로). 받침 있고 없고로만 고르면 「불으로」
        #   가 나갑니다.
        if j in ("으로", "로"):
            return val + tags + (hard if (_batchim(val) and not _rieul(val))
                                 else soft)
        return val + tags + (hard if _batchim(val) else soft)

    out = _RO_AFTER.sub(sub, _COPULA_AFTER.sub(sub, tpl))
    return _JOSA_AFTER.sub(sub, out).format(**w)


# ══════════════════════════════════════════════════════════
# 밑감 — 여덟 글자에서 뽑는 값
# ══════════════════════════════════════════════════════════
def el_of_group(day_gan: str, group: str) -> str:
    """이 묶음이 무슨 오행인가. 일간에서 나옵니다."""
    me = ELEMENT_OF_GAN[day_gan]
    return {"비겁": me, "식상": GENERATES[me], "재성": CONTROLS[me],
            "관성": CONTROLLED_BY[me], "인성": GENERATED_BY[me]}[group]


def _gan_gods(f) -> list:
    """천간에 드러난 십신 (일간은 자기 자신이라 뺍니다)."""
    return [ten_god(p["gan"], f.day_gan) for p in f.pillars
            if p.get("label") != "일주"]


def group_tuchul(f, group: str) -> bool:
    """이 묶음이 **천간에 드러났는가.**"""
    return any(GROUP_OF.get(g) == group for g in _gan_gods(f))


def _group_pillars(f, group: str) -> list:
    """이 묶음이 앉은 기둥들. 천간·지지 본기를 다 봅니다."""
    out = []
    for p in f.pillars:
        gods = []
        if p.get("label") != "일주":
            gods.append(ten_god(p["gan"], f.day_gan))
        gods.append(ten_god(HIDDEN[p["ji"]][0][0], f.day_gan))
        if any(GROUP_OF.get(g) == group for g in gods):
            out.append(p)
    return out


def group_seats(f, group: str) -> list:
    """이 묶음이 앉은 궁위 이름들."""
    return [p["label"] for p in _group_pillars(f, group)]


def _group_jis(f, group: str) -> list:
    """이 묶음이 본기로 앉은 지지들."""
    return [p["ji"] for p in f.pillars
            if GROUP_OF.get(ten_god(HIDDEN[p["ji"]][0][0], f.day_gan)) == group]


def _group_gans(f, group: str) -> list:
    """이 묶음이 **천간에 드러난** 자리들 — 투출(透出).

    ★ 왜 따로 세나

      같은 「재성 하나」라도 지지 속에만 숨은 것과 천간에 나온 것은
      실무가 다르게 봅니다. 드러난 것은 밖으로 나가는 힘이고, 숨은
      것은 안에서만 도는 힘입니다. 짝을 볼 때 이 갈래가 가장 크게
      갈립니다 — 마음이 밖으로 나갔는가, 안에만 있었는가.

      일간(나 자신)은 안 셉니다. 그건 짝이 아니라 나요.
    """
    out = []
    for i, p in enumerate(f.pillars):
        if i == 2:          # 일간 = 나 자신
            continue
        if GROUP_OF.get(ten_god(p["gan"], f.day_gan)) == group:
            out.append(p["gan"])
    return out


def tuchul(f, group: str) -> bool:
    """이 묶음이 천간에 드러났는가."""
    return bool(_group_gans(f, group))


def rooted(f, group: str) -> bool:
    """드러난 것에 **뿌리**가 있는가 — 천간에도 있고 지지에도 있는가.

    오래가는 것은 개수가 아니라 뿌리입니다. 천간에만 뜬 것은 바람에
    흔들리고, 지지에만 있는 것은 밖으로 안 나옵니다.
    """
    return bool(_group_gans(f, group)) and bool(_group_jis(f, group))


def jaego(f) -> Optional[str]:
    """재고(財庫) — 그대의 재성 기운이 **갈무리되는 지지**가 있는가.

    ★ 부동산·묵혀 두는 재산을 볼 때 실무가 먼저 보는 자리입니다.
      쥐는 힘(재성)이 **어디에 담기는가**요 — 흐르는 돈과 담기는 돈은
      다릅니다.

    ★ 이 자리로 **사고파는 때를 말하지 않습니다** (docs/11).
      「담기는 자리가 있소/없소」 까지입니다. 그 앞으로는 안 갑니다.
    """
    el = ELEMENT_OF_GAN.get(f.day_gan)
    if not el:
        return None
    # 재성 = 내가 이기는 오행
    jae_el = CONTROLS.get(el)
    go = GO_JI.get(jae_el)
    if not go:
        return None
    return go if any(p["ji"] == go for p in f.pillars) else None


def gongmang_hit(f, group: str) -> bool:
    """이 묶음이 앉은 지지가 **비어 있다고 보던 자리**에 걸렸는가."""
    gm = f.gongmang or ""
    return any(ji in gm for ji in _group_jis(f, group))


def chung_hit(f, group: str) -> bool:
    """이 묶음이 앉은 지지가 다른 지지와 부딪히는가."""
    jis = [p["ji"] for p in f.pillars]
    for ji in _group_jis(f, group):
        for other in jis:
            if other is not ji and CHUNG.get(ji) == other:
                return True
    return False


def chung_pairs(f) -> int:
    """여덟 글자 안에서 부딪히는 지지 쌍의 수."""
    jis = [p["ji"] for p in f.pillars]
    n = 0
    for i in range(len(jis)):
        for j in range(i + 1, len(jis)):
            if CHUNG.get(jis[i]) == jis[j]:
                n += 1
    return n


def visible(f, el: str) -> int:
    """겉에 보이는 그 기운의 개수 — 손님이 직접 세면 같은 수가 나오는 값."""
    n = 0
    for p in f.pillars:
        if ELEMENT_OF_GAN.get(p["gan"]) == el:
            n += 1
        if ELEMENT_OF_JI.get(p["ji"]) == el:
            n += 1
    return n


def isolated(f, el: str) -> bool:
    """
    고립 — 그 기운이 하나뿐인데 **낳아 줄 자리가 없는** 것.

    개수만 세면 「하나 있다」로 끝나는데, 하나가 혼자 서 있는 것과
    받쳐 주는 것이 곁에 있는 것은 다릅니다.
    """
    if visible(f, el) != 1:
        return False
    return visible(f, GENERATED_BY[el]) == 0


def has_sinsal(f, key: str) -> bool:
    return any(s.get("key") == key for s in (f.sinsal or []))


def _sinsal_at(f, key: str) -> list:
    for s in (f.sinsal or []):
        if s.get("key") == key:
            return list(s.get("at") or [])
    return []


def johu(f) -> str:
    """온도 — 불과 물의 기울기. lens_cuts._johu 와 같은 문턱을 씁니다."""
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


def _pred(n: int) -> str:
    """
    수를 **서술어 한 벌**로. 「없음이오」 「여섯 넘게요」 를 막는 자리요.

    ★ 자리표시 뒤에 서술격을 손으로 박으면 낱말마다 받침이 달라
      반은 틀립니다. 「쥘 자리는 없음이오」 가 실제로 나갔습니다.
      수를 낼 때는 **말이 끝난 꼴**로 냅니다.
    """
    from .bank import count_word
    if n == 0:
        return "하나도 없소"
    if n >= 6:
        return "여섯이 넘소"
    w = count_word(n)
    return w + ("이오" if _batchim(w) else "요")


def _words(f) -> dict:
    """자리표시에 갈아 끼울 말들. **수는 말로** 냅니다."""
    from .bank import count_word, element_word
    g = f.ten_gods
    return {
        "you": "그대",
        "day_gan": f.day_gan, "day_ji": f.day_ji,
        "strong": element_word(f.strong_el), "weak": element_word(f.weak_el),
        "yong": element_word(f.yongsin),
        "strength": f.strength,
        "jae": count_word(f.jae), "gwan": count_word(f.gwan),
        "sik": count_word(f.sik), "bi": count_word(f.bi),
        "inn": count_word(f.inn),
        "jeongjae": count_word(g["정재"]), "pyeonjae": count_word(g["편재"]),
        "jeonggwan": count_word(g["정관"]), "pyeongwan": count_word(g["편관"]),
        "where": WHERE[f.yongsin],
        "gongmang": f.gongmang,
        # 서술어 한 벌 — 뒤에 「이오/요」 를 손으로 붙이지 마시오.
        "jae_say": _pred(f.jae), "gwan_say": _pred(f.gwan),
        "sik_say": _pred(f.sik), "bi_say": _pred(f.bi),
        "inn_say": _pred(f.inn),
    }


# ══════════════════════════════════════════════════════════
# 저울 — 고민마다 세는 칸
# ══════════════════════════════════════════════════════════
#
# ★ 칸 하나는 (열쇠, 갈래, 근거, 조용한가) 넷으로 이뤄집니다.
#   «조용한 칸» 은 말할 것이 없는 칸입니다 — 창고가 없고 공망도 안
#   걸렸다면 그건 굳이 낼 말이 아닙니다. 다섯 칸이 안 차면 그때
#   메꾸는 데 씁니다. 있는 것부터 말하고, 없는 것은 자리가 남을 때
#   말합니다.
def _row(k, case, ev, quiet=False, w=None):
    return {"k": k, "case": case, "ev": ev, "quiet": quiet, "w": w or {}}


def _rows_money(f) -> list:
    g = f.ten_gods
    jj, pj = g["정재"], g["편재"]
    jae_el = el_of_group(f.day_gan, "재성")
    rows = []

    case = ("none" if f.jae == 0 else
            "both" if jj and pj else
            "jeong" if jj else "pyeon")
    rows.append(_row("hold", case, "정재 %d · 편재 %d" % (jj, pj)))

    if f.strength == "신강" and f.jae >= 2:
        lift = "왕왕"
    elif f.strength == "신약" and f.jae >= 3:
        lift = "재다신약"
    elif f.strength == "신강" and f.jae <= 1:
        lift = "재약신강"
    else:
        lift = "고름"
    rows.append(_row("lift", lift, "재성 %d · %s" % (f.jae, f.strength)))

    if f.jae:
        open_ = group_tuchul(f, "재성")
        rows.append(_row("show", "open" if open_ else "hidden",
                         "재성 %d · 천간에 %s"
                         % (f.jae, "드러남" if open_ else "안 드러남")))
        seats = group_seats(f, "재성")
        if seats:
            rows.append(_row("seat", seats[0],
                             "재성 %d · 앉은 기둥 %s"
                             % (f.jae, " · ".join(seats))))
        rows.append(_row("bridge", "놓임" if f.sik else "끊김",
                         "식상 %d → 재성 %d" % (f.sik, f.jae)))

    leak = "셋이상" if f.bi >= 3 else ("둘" if f.bi == 2 else "적음")
    rows.append(_row("leak", leak, "비겁 %d · 재성 %d" % (f.bi, f.jae),
                     quiet=(leak == "적음")))

    go = GO_JI[jae_el]
    has_go = any(p["ji"] == go for p in f.pillars)
    rows.append(_row("store", "있음" if has_go else "없음",
                     "재성 %s의 창고 글자(고지) %s %d자리"
                     % (jae_el, go, sum(1 for p in f.pillars
                                        if p["ji"] == go)),
                     quiet=not has_go, w={"go": go}))

    if f.jae:
        if gongmang_hit(f, "재성"):
            rows.append(_row("empty", "공망",
                             "재성 %d · 앉은 글자가 공망 %s"
                             % (f.jae, f.gongmang)))
        elif chung_hit(f, "재성"):
            rows.append(_row("empty", "충",
                             "재성 %d · 앉은 지지가 부딪힘(충) 1" % f.jae))

    live = ("용신" if jae_el == f.yongsin else
            "기신" if jae_el == f.strong_el else "무관")
    rows.append(_row("live", live,
                     "재성 %s %d자리 · 용신 %s" % (jae_el, visible(f, jae_el),
                                              f.yongsin),
                     quiet=(live == "무관")))
    return rows


def _rows_health(f) -> list:
    from .bank import element_word
    rows = []
    ORGAN = table()["ORGAN"]

    strong_n, weak_n = visible(f, f.strong_el), visible(f, f.weak_el)
    rows.append(_row("lean", "넘침" if strong_n >= 3 else "고름",
                     "%s %d자리" % (f.strong_el, strong_n),
                     w={"organ": ORGAN[f.strong_el]["at"],
                        "over": ORGAN[f.strong_el]["over"]}))
    rows.append(_row("floor", "바닥" if weak_n == 0 else "얕음",
                     "%s %d자리" % (f.weak_el, weak_n),
                     w={"organ": ORGAN[f.weak_el]["at"],
                        "under": ORGAN[f.weak_el]["under"]}))

    lone = [e for e in ("목", "화", "토", "금", "수") if isolated(f, e)]
    if lone:
        rows.append(_row("alone", "고립",
                         "%s 1자리 · 낳아 줄 %s 0자리"
                         % (lone[0], GENERATED_BY[lone[0]]),
                         w={"lone": element_word(lone[0]),
                            "feeder": element_word(GENERATED_BY[lone[0]])}))

    heat = johu(f)
    rows.append(_row("heat", heat,
                     "화 %d자리 · 수 %d자리"
                     % (visible(f, "화"), visible(f, "수")),
                     quiet=(heat == "고름")))

    rows.append(_row("lift", f.strength,
                     "%s · 나를 돕는 글자 %d · 태어난 달(월령) %s · 일지 %s"
                     % (f.strength, f.bi + f.inn,
                        "얻음" if f.deuk_ryeong else "못 얻음",
                        "얻음" if f.deuk_ji else "못 얻음")))

    n = chung_pairs(f)
    rows.append(_row("shake", "둘이상" if n >= 2 else ("하나" if n else "없음"),
                     "서로 부딪히는 지지(충) %d쌍%s" % (n, " · 일지 충" if f.ilji_chung else ""),
                     quiet=(n == 0)))

    g = f.ten_gods
    if f.gwan >= 3:
        press = "관살"
    elif f.sik >= 3:
        press = "식상"
    elif g["편인"] >= 1 and g["식신"] >= 1:
        press = "도식"
    elif f.inn >= 3:
        press = "인성"
    else:
        press = "없음"
    rows.append(_row("press", press,
                     "관성 %d · 식상 %d · 인성 %d" % (f.gwan, f.sik, f.inn),
                     quiet=(press == "없음")))

    blade = ("양인" if has_sinsal(f, "yangin") else
             "백호" if has_sinsal(f, "baekho") else
             "괴강" if has_sinsal(f, "gwaegang") else "없음")
    blade_at = _sinsal_at(f, {"양인": "yangin", "백호": "baekho",
                              "괴강": "gwaegang"}.get(blade, ""))
    rows.append(_row("blade", blade,
                     ("%s %d자리 · %s" % (blade, len(blade_at),
                                         " · ".join(blade_at))
                      if blade != "없음" else "칼 이름이 붙은 신살 0자리"),
                     quiet=(blade == "없음")))
    return rows


def g_mix(f, jeong: str, pyeon: str) -> bool:
    """혼잡 — 같은 묶음 안에 **결이 다른 둘**이 다 있는가."""
    return f.ten_gods.get(jeong, 0) >= 1 and f.ten_gods.get(pyeon, 0) >= 1


def _rows_work(f) -> list:
    g = f.ten_gods
    jg, pg = g["정관"], g["편관"]
    rows = []
    case = ("none" if f.gwan == 0 else
            "both" if jg and pg else
            "jeong" if jg else "pyeon")
    rows.append(_row("rule", case, "정관 %d · 편관 %d" % (jg, pg)))
    # ★ 격(格) — 실무가 일·진로에서 **가장 먼저** 보는 자리요.
    #   「무엇으로 서는가」를 한 낱말로 잡소 (topic.gyeok).
    gk = gyeok(f)
    if gk:
        month = [p for p in f.pillars if p.get("label") == "월주"]
        mj = month[0]["ji"] if month else ""
        rows.append(_row("gyeok", gk,
                         "월지 %s · 지장간 %d자 · %s"
                         % (mj or "?", len(HIDDEN[mj]) if mj else 0, gk)))
    # ★ 자리를 흔드는 것 — 충과 형. 일에서는 «자리가 바뀌는 결»이오.
    hy = hyeong(f)
    n_ch = chung_pairs(f)
    shake = ("형충" if hy and n_ch else "형" if hy else
             "충" if n_ch else "없음")
    rows.append(_row("shake", shake,
                     "서로 부딪히는 지지(충) %d쌍 · 형 %s" % (n_ch, hy or "없음"),
                     quiet=(shake == "없음"), w={"hy": hy or "없음"}))
    rows.append(_row("lift", f.strength,
                     "%s · 비겁 %d · 관성 %d" % (f.strength, f.bi, f.gwan)))
    if f.gwan:
        open_ = group_tuchul(f, "관성")
        rows.append(_row("show", "open" if open_ else "hidden",
                         "관성 %d · 천간에 %s"
                         % (f.gwan, "드러남" if open_ else "안 드러남")))
        seats = group_seats(f, "관성")
        if seats:
            rows.append(_row("seat", seats[0],
                             "관성 %d · 앉은 기둥 %s"
                             % (f.gwan, " · ".join(seats))))
    rows.append(_row("voice", "셋이상" if f.sik >= 3 else
                     ("있음" if f.sik else "없음"),
                     "식상 %d · 관성 %d" % (f.sik, f.gwan)))
    rows.append(_row("paper", "있음" if f.inn else "없음",
                     "인성 %d · 관성 %d" % (f.inn, f.gwan),
                     quiet=(f.inn == 0)))
    rows.append(_row("self", "셋이상" if f.bi >= 3 else "있음",
                     "비겁 %d" % f.bi, quiet=(f.bi < 3)))
    return rows


def _rows_love(f) -> list:
    from .bank import concern_group
    rows = []
    grp = concern_group("love", f.sex)
    if f.sex not in ("M", "F"):
        rows.append(_row("spouse", "모름",
                         "성별 미상 · 짝을 보는 글자 0벌"))
        return rows
    n = {"재성": f.jae, "관성": f.gwan}[grp]
    case = ("none" if n == 0 else "many" if n >= 3 else
            "two" if n == 2 else "one")
    rows.append(_row("spouse", case,
                     "%s %d · %s" % (grp, n, "남명" if f.sex == "M" else "여명"),
                     w={"grp": grp}))
    # ★ 관살혼잡 · 재성혼잡 — 짝을 보는 글자가 **결이 다른 둘**인가.
    #   개수만 세면 「둘」인데, 실무는 그 둘이 같은 결인지를 보오.
    jeong, pyeon = (("정재", "편재") if grp == "재성" else ("정관", "편관"))
    if g_mix(f, jeong, pyeon):
        rows.append(_row("mix", "혼잡",
                         "%s %d · %s %d"
                         % (jeong, f.ten_gods[jeong], pyeon, f.ten_gods[pyeon]),
                         w={"grp": grp}))
    # ★ 일간이 다른 천간과 **묶이는가**. 옛 책은 이걸 «정에 매인 자리»로
    #   읽었소 — 붙으면 제 노릇을 덜 하오.
    mate = gan_hap_with(f)
    if mate:
        rows.append(_row("gan_hap", "있음",
                         "일간 %s · 합하는 천간 %s %d자리"
                         % (f.day_gan, mate,
                            sum(1 for p in f.pillars if p["gan"] == mate)),
                         w={"mate": mate}))
    if n:
        open_ = group_tuchul(f, grp)
        rows.append(_row("show", "open" if open_ else "hidden",
                         "%s %d · 천간에 %s"
                         % (grp, n, "드러남" if open_ else "안 드러남"),
                         w={"grp": grp}))
        seats = group_seats(f, grp)
        if seats:
            rows.append(_row("seat", seats[0],
                             "%s %d · 앉은 기둥 %s"
                             % (grp, n, " · ".join(seats)),
                             w={"grp": grp}))
    # ★ 배우자궁에 **무엇이 앉았는가** — 실무가 사랑에서 가장 먼저 보는
    #   자리요. 짝을 보는 글자(재성·관성)가 몇인지와 별개로, 발밑 그
    #   한 글자가 «곁에 두는 사람의 결»을 말하오. 늘 섭니다.
    seat_god = ten_god(HIDDEN[f.day_ji][0][0], f.day_gan)
    rows.append(_row("seat_god", seat_god,
                     "일지 %s · 본기 %s · %s %d"
                     % (f.day_ji, HIDDEN[f.day_ji][0][0], seat_god,
                        f.ten_gods.get(seat_god, 0))))
    ilji = ("둘다" if f.ilji_chung and f.ilji_hap else
            "충" if f.ilji_chung else
            "합" if f.ilji_hap else "없음")
    rows.append(_row("ilji", ilji,
                     "일지 %s · 충 %d · 합 %d"
                     % (f.day_ji, 1 if f.ilji_chung else 0,
                        len(f.ilji_hap or [])),
                     quiet=(ilji == "없음")))
    flower = ("둘다" if has_sinsal(f, "dohwa") and has_sinsal(f, "wonjin") else
              "도화" if has_sinsal(f, "dohwa") else
              "원진" if has_sinsal(f, "wonjin") else "없음")
    rows.append(_row("flower", flower,
                     "도화 %d자리 · 원진 %d자리"
                     % (len(_sinsal_at(f, "dohwa")),
                        len(_sinsal_at(f, "wonjin"))),
                     quiet=(flower == "없음")))
    if n and gongmang_hit(f, grp):
        rows.append(_row("empty", "공망",
                         "%s %d · 앉은 글자가 공망 %s"
                         % (grp, n, f.gongmang), w={"grp": grp}))
    return rows


def _rows_people(f) -> list:
    rows = []
    peers = ("넷이상" if f.bi >= 4 else "셋" if f.bi == 3 else
             "둘" if f.bi == 2 else "적음")
    rows.append(_row("peers", peers, "비겁 %d" % f.bi))
    # ★ 형(刑) — 옛 책이 다툼·구설·시비를 붙여 읽던 자리요.
    #   사고나 재판을 예고하는 표로 쓰지 않소 (docs/14 §7).
    hy = hyeong(f)
    if hy:
        rows.append(_row("hyeong", hy,
                         "형 %s · 걸린 지지 %d자리 (%s)"
                         % (hy, len(hyeong_at(f)), " ".join(hyeong_at(f)))))
    # ★ 무리 — 지지가 삼합·방합으로 뭉쳤는가. 사람 자리에서는
    #   «한쪽으로 쏠린 판»이오.
    kind, el = hap_group(f)
    if kind:
        rows.append(_row("group", kind,
                         "%s · %s 국(局) · %s %d자리"
                         % (kind, el, el, visible(f, el)),
                         w={"kind": kind, "gel": el}))
    rows.append(_row("line", "있음" if f.gwan else "없음",
                     "관성 %d" % f.gwan))
    rows.append(_row("mouth", "셋이상" if f.sik >= 3 else
                     ("있음" if f.sik else "없음"), "식상 %d" % f.sik))
    rows.append(_row("take", "셋이상" if f.inn >= 3 else
                     ("있음" if f.inn else "없음"), "인성 %d" % f.inn,
                     quiet=(f.inn == 0)))
    ilji = ("둘다" if f.ilji_chung and f.ilji_hap else
            "충" if f.ilji_chung else
            "합" if f.ilji_hap else "없음")
    rows.append(_row("ilji", ilji,
                     "일지 %s · 충 %d · 합 %d"
                     % (f.day_ji, 1 if f.ilji_chung else 0,
                        len(f.ilji_hap or [])),
                     quiet=(ilji == "없음")))
    rows.append(_row("wonjin", "있음" if has_sinsal(f, "wonjin") else "없음",
                     "원진 %d자리%s"
                     % (len(_sinsal_at(f, "wonjin")),
                        (" · " + " · ".join(_sinsal_at(f, "wonjin")))
                        if has_sinsal(f, "wonjin") else ""),
                     quiet=not has_sinsal(f, "wonjin")))
    return rows


def _rows_dir(f) -> list:
    rows = []
    rows.append(_row("horse", "있음" if has_sinsal(f, "yeokma") else "없음",
                     "역마 %d자리%s"
                     % (len(_sinsal_at(f, "yeokma")),
                        (" · " + " · ".join(_sinsal_at(f, "yeokma")))
                        if has_sinsal(f, "yeokma") else "")))
    rows.append(_row("cover", "있음" if has_sinsal(f, "hwagae") else "없음",
                     "화개 %d자리%s"
                     % (len(_sinsal_at(f, "hwagae")),
                        (" · " + " · ".join(_sinsal_at(f, "hwagae")))
                        if has_sinsal(f, "hwagae") else ""),
                     quiet=not has_sinsal(f, "hwagae")))
    # ★ 무리 — 지지가 한 오행으로 뭉치면 «갈 곳이 이미 정해진» 판이오.
    kind, el = hap_group(f)
    if kind:
        rows.append(_row("group", kind,
                         "%s · %s 국(局) %d자리 · 도는 방향 %s"
                         % (kind, el, visible(f, el), WHERE[el]),
                         w={"kind": kind, "gel": el, "gwhere": WHERE[el]}))
    # ★ 힘이 흐르는 쪽. 갈림길에서 «무엇으로 정하는가» 요.
    rows.append(_row("lean", f.flow,
                     "가장 센 십신 묶음 %s · %s %d자리"
                     % (f.flow, f.flow_el, visible(f, f.flow_el))))
    rows.append(_row("rule", "없음" if f.gwan == 0 else "있음",
                     "관성 %d" % f.gwan))
    rows.append(_row("where", f.yongsin,
                     "용신 %s %d자리 · 도는 방향 %s"
                     % (f.yongsin, visible(f, f.yongsin), WHERE[f.yongsin])))
    nxt = _next_daeun(f)
    if nxt:
        age, left = nxt
        band = ("지금" if left <= 0 else "곧" if left <= 2 else
                "중간" if left <= 6 else "멀다")
        rows.append(_row("turn", band,
                         "다음 대운 %d세 · %d해 남음" % (age, left),
                         w={"age": age, "left": _years(left)}))
    return rows


# 「1해」 는 말이 아니오. 세는 말은 관형사로 냅니다.
_YEAR_WORD = {1: "한", 2: "두", 3: "세", 4: "네", 5: "다섯",
              6: "여섯", 7: "일곱", 8: "여덟", 9: "아홉"}


def _years(n: int) -> str:
    return _YEAR_WORD.get(n, str(n))


def _rows_real_estate(f):
    rows = _rows_money(f)
    prompts = [
        "부동산에서 먼저 볼 것은 수익률이 아니라 보유 목적과 감당 가능한 기간이오.",
        "계약금·중도금·잔금·이자까지 한 번에 적어야 실제 부담을 볼 수 있소.",
        "살 때의 이유와 팔거나 나올 조건을 함께 정해야 판단이 흔들리지 않소.",
    ]
    for row, prompt in zip(rows[:3], prompts):
        row["ev"] = prompt
    return rows[:3]


_ROWS = {"money": _rows_money, "health": _rows_health, "work": _rows_work,
         "love": _rows_love, "people": _rows_people, "dir": _rows_dir,
         "real_estate": _rows_real_estate}


# ══════════════════════════════════════════════════════════
# 되물음의 답이 **흘러가는 자리** (2026-09-10 · docs/40 §9)
# ══════════════════════════════════════════════════════════
#
# ★ 답이 처방에 거의 안 닿고 있었습니다.
#
#   사랑에서 「혼자 마음만」 과 「끝나는 중」 을 골랐을 때 유료 31컷을
#   견주니 **달라진 컷이 하나**(topic_ask)였습니다. 짝사랑이든 이별이든
#   저울·짜임·때가 글자 하나 안 달랐습니다. 물어 놓고 처방은 그대로요.
#
#   여덟 글자가 모자란 게 아니었습니다. 사랑에서 셀 수 있는 사실 열
#   가지로 2,000명이 353가지 조합(실효 177갈래)으로 갈리는데, 물음은
#   그중 8갈래만 쓰고 있었습니다.
#
# ★ 새로 세지 않습니다. 답은 **어느 칸·어느 짜임을 먼저 볼지**를 고릅니다.
#   조건이 안 맞는 것은 여전히 안 냅니다 — 지어내는 것이 없습니다.
#   답 안 한 사람은 예전과 **같은 글**을 받습니다.
def _focus(concern: str, sub: Optional[dict]) -> Optional[dict]:
    if not sub or not sub.get("choice"):
        return None
    return (table().get("SUB_FOCUS", {}).get(concern) or {}).get(sub["choice"])


def focus_pats(concern: str, sub: Optional[dict]) -> Optional[list]:
    """이 답에서 **먼저 볼 짜임** 차례. 없으면 None."""
    fx = _focus(concern, sub)
    return list(fx.get("pats") or []) if fx else None


def _sub_label(concern: str, sub: Optional[dict]) -> str:
    spec = table()["ASK"].get(concern) or {}
    return (spec.get("options") or {}).get((sub or {}).get("choice") or "", "")


def scale(f, concern: str, sub: Optional[dict] = None) -> list:
    """
    이 고민에서 세는 칸들. 최대 다섯.

    sub : 되물음에 고른 답 {"choice", "choice2"}. 있으면 **그 자리 칸을
          먼저** 세웁니다. 없으면 예전과 같습니다.

    돌려주는 것: [{"k","say","ev"}]
    """
    if concern not in _ROWS:
        raise TopicError("모르는 고민 축: %r" % (concern,))
    rows = _ROWS[concern](f)
    order = {id(r): i for i, r in enumerate(rows)}
    fx = _focus(concern, sub)
    if fx and fx.get("rows"):
        # ★ 답에 맞는 칸을 **앞에** 세웁니다. 다만 **조용한 칸은 끌어올리지
        #   않습니다** (2026-09-10).
        #
        #   처음에는 「답이 가리키면 조용한 칸이라도 세운다」 였습니다.
        #   같은 자로 재 보니 답 안 한 때는 문턱(2%) 아래던 돈 저울이
        #   **답하면 4.29%** 로 뛰었습니다. 조용한 칸은 조용한 까닭이
        #   있습니다 — 그 사람에게서 셀 것이 적어 누구에게나 같은 말
        #   (「없음」「적음」)이 나옵니다. 그걸 앞에 세우면 답을 한 사람일수록
        #   **남과 같은 글**을 받습니다. 정교하게 하려던 것이 거꾸로 뭉개졌소.
        #
        #   그래서 **소리 나는 칸끼리 차례만** 바꿉니다. 소리 나는 칸이 다섯에
        #   못 차면 조용한 칸으로 채우는 것은 예전과 같습니다.
        pri = {k: i for i, k in enumerate(fx["rows"])}
        keep = sorted(rows, key=lambda r: (r["quiet"],
                                           0 if r["k"] in pri else 1,
                                           pri.get(r["k"], 99),
                                           order[id(r)]))[:MAX_ROWS]
    else:
        loud = [r for r in rows if not r["quiet"]]
        quiet = [r for r in rows if r["quiet"]]
        keep = loud[:MAX_ROWS]
        if len(keep) < MAX_ROWS:
            keep += quiet[:MAX_ROWS - len(keep)]
        keep.sort(key=lambda r: order[id(r)])

    base = _words(f)
    out = []
    for r in keep:
        spec = _pick("SCALE", concern, r["k"])
        tpl = spec["case"].get(r["case"])
        if tpl is None:
            raise TopicError("topic.SCALE[%s][%s] 에 %r 갈래가 없소"
                             % (concern, r["k"], r["case"]))
        w = dict(base)
        w.update(r["w"])
        out.append({"k": r["k"], "label": spec["label"],
                    "say": _fmt(tpl, w), "ev": r["ev"],
                    "case": r["case"]})
    return out


def scale_sid(concern: str, rows: list, sub: Optional[dict] = None) -> str:
    # ★ 답이 다르면 번호도 다릅니다. 같은 번호로 묶으면 짝사랑에게 맞은
    #   문장과 이별에게 맞은 문장의 공감률이 한 통에 섞입니다.
    tail = (":@" + sub["choice"]) if sub and sub.get("choice") else ""
    return "scale:%s:%s%s" % (concern,
                              ",".join("%s=%s" % (r["k"], r["case"])
                                       for r in rows), tail)


# ══════════════════════════════════════════════════════════
# 때 — 그 자리가 대운에서 언제 바뀌는가
# ══════════════════════════════════════════════════════════
#
# ★ 달력이지 예언이 아닙니다. 나이와 해를 박되 **그 해에 무슨 일이
#   생긴다고 말하지 않습니다.** 바뀌는 때만 셉니다 (CLAUDE.md).
def _next_daeun(f) -> Optional[tuple]:
    """다음 대운 칸의 (시작 나이, 남은 해). 마지막 칸이면 None."""
    nxt = f.daeun_now + 1
    if nxt >= len(f.daeun):
        return None
    age = int(f.daeun[nxt]["start_age"])
    return age, max(0, age - int(f.age))


def turn(f, concern: str, sub: Optional[dict] = None) -> Optional[dict]:
    """
    물으신 자리가 대운에서 드는 때.

    돌려주는 것: {"say","ev","sid"} · 볼 수 없으면 None
    """
    from .bank import concern_group
    grp = concern_group(concern, f.sex)
    if not grp:
        return None
    now_grp = GROUP_OF.get(f.daeun_ten_god, f.daeun_ten_god)

    from .bank import count_word

    parts = [_fmt(_pick("TURN", "now", concern, now_grp),
                  {"now": f.daeun_ten_god, "grp": grp})]

    # ★ 지금 칸의 **자리**를 셉니다 (2026-09-06).
    #
    #   전에는 「지금은 인성 대운이오」 로 끝났습니다. 재보니 이 컷의
    #   최다 점유가 돈에서 1.92%로, 공통 컷 문턱(2%)에 붙어 있었습니다.
    #   축이 둘(고민 × 대운 십신)뿐이라 그렇습니다.
    #
    #   셋째 축은 **수**로 붙입니다 — 몇 살에 들어와 몇 살까지고 몇 해
    #   남았는가. 지어내지 않고, 손님이 대운 맵을 펴면 맞춰 볼 수 있는
    #   값입니다. 가짓수는 덤이고 근거가 먼저입니다.
    from .bite import phase_of
    here = f.daeun[f.daeun_now]
    start = int(here["start_age"])
    nxt = _next_daeun(f)
    if nxt:
        end, left = nxt[0], nxt[1]
        left_say = ("<b>올해</b>가 바로 대운이 바뀌는 해요" if left <= 0 else
                    "바뀌기까지 <b>%s 해</b> 남았소" % _years(left))
        parts.append(
            "지금 대운은 <b>%d살</b>에 시작해 <b>%d살</b>까지요. 그대는 지금 "
            "<b>%d살</b>이니 %s. %s"
            % (start, end, int(f.age), left_say,
               _pick("TURN", "phase", phase_of(int(f.age), start))))
    else:
        parts.append(
            "지금 대운은 <b>%d살</b>에 시작한 <b>마지막 대운</b>이오. 다음 "
            "대운이 더는 없으니, 지금 안 하면 이 대운 동안은 끝내 안 하게 "
            "되오." % start)

    # 이 자리의 대운이 **다음에** 드는 칸
    hit = None
    for d in f.daeun[f.daeun_now + 1:]:
        if GROUP_OF.get(d["ten_god"]) == grp:
            hit = d
            break
    if hit:
        age = int(hit["start_age"])
        parts.append(_fmt(_pick("TURN", "hit", concern),
                          {"grp": grp, "age": age,
                           # ★ 양력 생년 + 나이. saju_year(입춘)에 양력
                           #   나이를 더하면 1·2월생이 한 해 어긋납니다.
                           "year": f.birth_year + age, "tg": hit["ten_god"]}))
    else:
        parts.append(_fmt(_pick("TURN", "none", concern), {"grp": grp}))
    # ★ 세운 한 줄 — 물으신 자리를 **올해** 건드리는가 (2026-09-10).
    #
    #   답이 가리키는 자리(`SUB_FOCUS.grp`)를 올해 세운이 치는지만
    #   셉니다. 무슨 일이 생긴다고 말하지 않습니다 — 그 자리가 올해
    #   한 번 움직인다는 셈까지요. 몸 고민에는 안 답니다(건강을 해로
    #   못 박으면 그건 예언이오).
    yr_mark = ""
    if sub and sub.get("choice") and concern != "health":
        fx = _focus(concern, sub) or {}
        sg = None
        if sub.get("choice2"):
            sg = (table().get("SUB2_GRP", {}).get(concern) or {}).get(sub["choice2"])
        sg = sg or fx.get("grp")
        if sg == "@love":
            sg = grp
        if sg:
            yg = GROUP_OF.get(f.year_ten_god, f.year_ten_god)
            yr_hit = (yg == sg)
            parts.append(_fmt(_pick("TURN", "year", "hit" if yr_hit else "miss"),
                              {"year_gz": f.year_gz, "year_tg": f.year_ten_god,
                               "grp": sg, "label": _sub_label(concern, sub)}))
            yr_mark = ":yr=%s:@%s" % ("hit" if yr_hit else "miss", sub["choice"])
    parts.append(_pick("TURN", "tail"))

    return {
        "say": "".join('<p class="tale">%s</p>' % p for p in parts),
        # ★ 「대운 십신」 은 십신 이름이 아니라 **축**이라, 이치가
        #   why.AXIS 에 있소. why.line 으로 부르면 이치도 출처도 안
        #   붙어 관측만 남소 (tests/test_evidence 가 잡소).
        "ev": _why.axis_line(
            "지금 %d살 · 대운 %s(%s) · %d살부터 · 다음 %s 대운 %s"
            % (int(f.age), f.daeun[f.daeun_now]["gz"], f.daeun_ten_god,
               int(f.daeun[f.daeun_now]["start_age"]), grp,
               ("%d살" % int(hit["start_age"])) if hit else "앞으로 올 대운에 없음"),
            "daeun_ten_god"),
        "sid": "turn:%s:%s:%s%s" % (concern, now_grp,
                                    "hit" if hit else "none", yr_mark),
    }


def pattern_tail(concern: str, strength: str) -> str:
    """
    짜임 컷의 맺음 — 그 짜임들을 **어떻게 읽을 것인가.**

    ★ 축을 하나 더 곱하는 자리이기도 하오. 짜임 이름만 늘어놓으니
      최다 점유가 2.50%로 문턱(2%)을 넘었소 — 같은 고민에서 같은
      짜임 셋이 자주 겹치기 때문이오. 신강약은 짜임과 **서로 다른
      것을 보는** 축이라 곱해도 말이 안 어긋나오.
    """
    return _pick("PAT_TAIL", concern, strength)


# ══════════════════════════════════════════════════════════
# 얼굴 — 넉 자가 이 자리에서 어떤 꼴로 나오나
# ══════════════════════════════════════════════════════════
#
# ★ 넉 자를 성격 프로필로 두껍게 만들려고 받는 것이 아닙니다.
#   이 집에서 넉 자의 쓸모는 하나뿐입니다 —
#
#     넉 자는 그대가 **스스로 고른 답**이고
#     여덟 글자는 **고를 수 없었던 것**이다
#
#   그 둘이 어긋난 자리가 곧 「그렇게 보이려고 애쓰는 자리」요.
#   그러니 결합의 자리도 하나입니다 — **어긋남을 고민의 말로 옮긴다.**
#
# ★ 축은 **둘만** 씁니다. 넷을 다 말하면 그건 성격검사지 사주가
#   아닙니다. 어느 둘인지는 고민마다 확정돼 있습니다 (topic.AXIS_OF).
# ★ 그 축이 **무엇을 세어 나온 값인지**.
#
#   전에는 「그대는 T요」 로 끝났습니다. 여덟 글자에서 뽑은 넉 자인데
#   무엇을 세었는지는 안 적혀 있었습니다 — 이 집에서 그건 근거가 아니라
#   선언입니다. 재보니 이 컷의 최다 점유가 3.7%로 공통 컷 문턱(2%)을
#   넘고 있었는데, 원인도 같았습니다: 축이 글자 둘뿐이라 가짓수가
#   열여섯에서 멈춥니다. 세어서 적으면 근거가 서고 쏠림도 풀립니다.
AXIS_COUNT = {
    "EI": (("밖으로 나서는 힘", ("비견", "겁재", "식신", "상관")),
           ("안으로 모으는 힘", ("정인", "편인", "정관", "편관"))),
    "SN": (("눈앞 현실을 보는 힘", ("정재", "편재", "정관", "편관")),
           ("넓게 떠올리는 힘", ("편인", "상관", "편재"))),
    "TF": (("따져서 정하는 힘", ("정관", "편관", "정재", "편재")),
           ("마음으로 정하는 힘", ("식신", "상관", "정인"))),
    "JP": (("미리 정해 두는 힘", ("정관", "정재", "정인")),
           ("그때그때 바꾸는 힘", ("상관", "편재", "겁재"))),
}


def _axis_counted(f, key: str) -> str:
    """이 축이 무슨 십신을 세어 나왔는가. 손님이 세면 같은 수요."""
    from .bank import count_word
    (hi_w, hi_g), (lo_w, lo_g) = AXIS_COUNT[key]
    hi = sum(f.ten_gods.get(g, 0) for g in hi_g)
    lo = sum(f.ten_gods.get(g, 0) for g in lo_g)

    # ★ 0은 「없음」 이 아니라 «하나도 없다» 고 하오. 여섯을 넘으면
    #   count_word 가 「여섯 넘게」 를 주는데, 그건 뒤에 조사가 못 붙는
    #   꼴이라 「여섯이 넘」 으로 적소. 둘 다 **어간**이라 뒤에 고·소가
    #   그대로 붙소.
    def say(word, v):
        if v == 0:
            return "<b>%s</b>은 하나도 없" % word, ""
        if v >= 6:
            return "<b>%s</b>이 여섯이 넘" % word, ""
        return "<b>%s</b>이 %s" % (word, count_word(v)), count_word(v)

    if hi == 0 and lo == 0:
        return ("<b>%s</b>도 <b>%s</b>도 여덟 글자에 <b>하나도 없소</b>. "
                "여덟 글자로는 이 축을 가를 수 없어, 적으신 글자를 바꾸지 않고 두오."
                % (hi_w, lo_w))

    hi_say, hi_num = say(hi_w, hi)
    lo_say, lo_num = say(lo_w, lo)
    mid = "고, " if not hi_num else ("이고, " if _batchim(hi_num) else "고, ")
    tail = "소." if not lo_num else ("이오." if _batchim(lo_num) else "요.")
    out = "%s%s%s%s" % (hi_say, mid, lo_say, tail)

    # ★ 강약이 이 축을 한 번 더 미오. 감추면 근거와 결론이 어긋나오 —
    #   힘의 수는 안으로가 많은데 글자는 E 로 나오는 자리가 생기오.
    if key == "EI" and f.strength in ("신강", "신약"):
        out += (" 그대는 <b>%s</b>이라 밖으로 나서는 쪽을 <b>둘</b> %s 보았소."
                % (f.strength, "더 얹어" if f.strength == "신강" else "덜어"))
    # ★ 근거 줄에 **아라비아 숫자**를 남깁니다 (2026-09-07).
    #
    #   여기까지는 한글 수사(「셋이오」)로만 적었습니다. 사람이 읽기에는
    #   그게 맞는데, 근거 줄은 **셈을 보이는 자리**라 손님이 만세력을
    #   펴고 대 볼 수 있어야 합니다. 재보니 근거 줄에 숫자가 든 컷이
    #   25%뿐이었습니다 (engine/worth 에서 가장 낮은 칸).
    # ★ 「(5 : 1)」 은 손님이 못 읽었습니다 (2026-09-11) — 수는 근거 줄에 둡니다.
    return out


def face(f, concern: str, axis4: Optional[str] = None) -> Optional[dict]:
    """
    넉 자 × 고민. 돌려주는 것: {"say","ev","sid","from_input"}
    """
    from .bank import AXES, saju_axis
    axes = table()["AXIS_OF"].get(concern)
    if not axes:
        return None
    idx = dict(AXES)
    a = saju_axis(f)
    said = (axis4 or "").upper()
    usable = len(said) == 4

    rows, letters, gaps = [], [], []
    for key in axes:
        mine = a[key]
        ch = said[idx[key]] if usable else ""
        # ★ 빈 글자는 **어느 축에도 든다**고 나옵니다 — 파이썬에서
        #   `"" in "SN"` 은 참입니다. 넉 자를 안 적은 사람에게 빈 열쇠로
        #   표를 뒤지다 터졌습니다. 비었으면 사주축으로 갑니다.
        if not ch or ch not in key:
            ch = mine
        same = ch == mine
        letters.append(ch)
        rows.append({
            "axis": key, "letter": ch, "mine": mine, "same": same,
            "face": _pick("AXIS_FACE", ch, concern),
            "gap": None if same else _pick("AXIS_GAP", "%s→%s" % (mine, ch),
                                           concern),
        })
        if not same:
            gaps.append("%s→%s" % (mine, ch))

    from_input = usable and any(r["letter"] != "" for r in rows)
    lead = _pick("FACE", "lead_in" if usable else "lead_out")
    body = ['<p class="tale">%s</p>' % lead]
    for r in rows:
        body.append('<p class="hit"><b>%s</b> %s</p>' % (r["letter"], r["face"]))
        body.append('<p class="cnt">%s</p>' % _axis_counted(f, r["axis"]))
        if r["gap"]:
            body.append('<p class="tale">헌데 여덟 글자는 적으신 것과 달리 <b>%s</b> 글자가 나오오. %s</p>'
                        % (r["mine"], r["gap"]))
    body.append('<p class="tale">%s</p>'
                % _pick("FACE", "tail_gap" if gaps else "tail_same"))

    return {
        "say": "".join(body),
        # ★ 근거 줄에 센 수를 답니다 — 축 몇을 보고 몇이 어긋났는지.
        "ev": _why.axis_line(
            "%s · 여덟 글자에서 뽑은 넉 자 %s · 본 축 %d · 어긋난 축 %d"
            % (("적으신 넉 자 %s" % said) if usable else "넉 자를 안 적으셨소",
               "".join(a[k] for k, _ in AXES), len(rows), len(gaps)),
            "concern"),
        "sid": "face:%s:%s:%s" % (concern, "".join(letters),
                                  ",".join(gaps) or "-"),
        "from_input": bool(usable),
    }


def cut_line(f, cut_id: str, concern: Optional[str]) -> str:
    """
    **공통 척추 컷**이 물으신 자리에서 내는 한 줄.

    ★ 손님이 짚은 것 (2026-09-07)

      "고민이 다른데 왜 정답이 다 똑같아."

      전용 컷(`concern_scale` `concern_turn` `concern_face`)은 갈리는데
      **척추 열 컷이 안 갈렸습니다** — 없는 것 · 희소도 · 지금 어디에 ·
      필요한 것 · 대운 맵 · 신살 · 귀인 · 조상 · 이번 주 · 마감.
      그 열이 리포트 분량의 절반이라, 손님에게는 「다 똑같다」로 읽힙니다.

    ★ 컷을 새로 만들지 않습니다. 그 컷이 **이미 센 값**을 물으신 자리의
      말로 한 번 더 짚습니다 — 뜬 말 뒤에 살림의 말을 붙이는
      `real.py` 와 같은 자리입니다.

    ★ 모르면 빈 문자열입니다. 지어내지 않습니다.
    """
    if not concern:
        return ""
    tpl = (table().get("CUT_AT", {}).get(cut_id, {}) or {}).get(concern)
    if not tpl:
        return ""
    from .bank import concern_group
    w = dict(_words(f))
    w["grp"] = concern_group(concern, f.sex) or ""
    # ★ 긴 컷에는 **두 줄**입니다 (2026-09-17).
    #
    #   손님이 다시 짚었습니다 — 「돈을 선택했는데 왜 돈에 대한걸
    #   말안해」. 기계는 돌고 있었는데 분량이 모자랐습니다: 희소도
    #   1,001자와 신살 1,307자에 물으신 자리의 말이 **한 번**뿐이라,
    #   손님 눈에는 안 보입니다. 한 줄로 천 자를 물들일 수는 없소.
    #
    #   그래서 값은 글 하나 또는 여럿을 받습니다. 컷을 새로 만들지는
    #   않습니다 — 그 컷이 이미 센 값을 물으신 자리의 말로 짚을 뿐이오.
    rows = tpl if isinstance(tpl, (list, tuple)) else [tpl]
    return "".join('<p class="tale">%s</p>' % _fmt(x, w) for x in rows if x)


def hook_line(concern, stage) -> str:
    """훅 한 마디가 **물으신 자리의 말**로 한 번 옮기는 줄.

    ★ 새로 점치는 것이 아닙니다 — 그 마디가 이미 한 말을 손님이
      쓰는 말로 옮길 뿐이오. `engine/real` 이 뜬 말 뒤에 살림의 말을
      붙이는 것과 같은 자리입니다.

    ★ 모르면 빈 글자입니다. 고민을 안 물었으면 안 답니다.
    """
    if not concern:
        return ""
    row = (table().get("HOOK_AT", {}) or {}).get(str(stage)) or {}
    t = row.get(concern)
    return '<p class="tale atask">%s</p>' % t if t else ""


def ask_line(concern, stage) -> str:
    """그 단을 **여는 물음**. 물으신 자리에서 묻습니다.

    ★ 여태 `bank.build_hook` 안에 박혀 있어 고민축이 닿을 자리가
      없었습니다 (2026-09-19). 재보니 2.5단·3단은 여는 물음을 머리에
      이고 **앞 280자가 통째로 고정**이었습니다 — 손님이 그 단을 열고
      280자를 읽을 때까지 자기가 무엇을 물었는지 흔적을 못 봤습니다.

    ★ 낱말만 갈아 끼우지 않습니다. 1단은 「부정확인」 단이라, 그
      고민에서 손님이 사주에 품고 온 기대를 그대로 겨눕니다 —
      돈이면 「얼마를 버는지」, 사랑이면 「이 사람이 인연인지」.

    ★ 없으면 빈 글자입니다. 부르는 자리가 예전 문구를 답니다.
    """
    if not concern:
        return ""
    row = (table().get("ASK_AT", {}) or {}).get(str(stage)) or {}
    return row.get(concern) or ""


def q_line(concern, stage) -> str:
    """손님이 그렇소/아니오를 누르기 **직전의 한 마디**.

    ★ 재보니 이 줄이 90.4% 고정이었습니다 — 무엇을 물었든 「이 말은
      어떻소?」 「이제 알겠소?」 였습니다. 누르는 자리라 짧게 둡니다.
      길어지면 누르는 자리가 아니라 읽는 자리가 됩니다.
    """
    if not concern:
        return ""
    row = (table().get("Q_AT", {}) or {}).get(str(stage)) or {}
    return row.get(concern) or ""


def next_line(concern) -> str:
    """훅의 **마지막 줄**. 다음 자리로 가는 다리.

    ★ 앞을 깎지 않습니다. 「여덟 자 중 셋으로 본 것」 처럼 방금 좋았다고
      느낀 것을 8분의 3으로 만들지 않소 — 격차는 **남은 물음**으로 냅니다.
    ★ `HOOK_AT["3"]` 과 뜻이 겹치면 안 됩니다. 그 줄은 이름이 **어디서
      나오는가** 고, 이 줄은 이름만으로 **안 풀리는 것**입니다.
    """
    if not concern:
        return ""
    return (table().get("NEXT_AT", {}) or {}).get(concern) or ""


def lens_line(lens_id: Optional[str], concern: Optional[str]) -> str:
    """
    **이 사람이 그 자리를 보는가** — 관점 컷 앞에 한 번 답니다.

    ★ 손님이 짚은 것 (2026-09-07)

      "캐릭터도 그 캐릭 전문성에 맞게끔 상담해야하고."

      관점 컷은 그 사람의 고정된 눈이라 고민이 바뀌어도 안 갈립니다.
      그건 버그가 아니오 — 월하선녀가 돈 얘기를 하면 그건 월하선녀가
      아닙니다. 어긋난 것은 **그 사람이 제 자리인지 아닌지를 말하지
      않는다**는 것이었습니다.

      그래서 두 줄만 둡니다 —
        · 제 자리면  「사랑이라면 내 자리예요. 저는 곁자리부터 봐요」
        · 아니면     「물으신 건 제 자리가 아니에요. 저는 곁자리만 봐요」

      아닌 것을 아니라고 말하는 것이 이 집의 방식입니다. 감추면
      손님은 「왜 몸 보는 사람이 사랑을 말하지」 하고 멈춥니다.
    """
    if not lens_id:
        return ""
    t = table()
    on = (t.get("LENS_ON", {}).get(lens_id, {}) or {}).get(concern or "")
    say = on or t.get("LENS_OFF", {}).get(lens_id, "")
    if not say:
        return ""
    return '<p class="tale %s">%s</p>' % ("hit" if on else "sm", say)


def face_line(f, concern: str, axis4: Optional[str] = None,
              slot: int = 0) -> Optional[dict]:
    """
    훅에 붙는 **한 줄.** 넉 자가 물으신 자리에서 내는 얼굴.

    slot  몇 번째 축을 낼 것인가. `AXIS_OF[concern]` 은 축을 **둘**
          주는데 여태 첫 칸만 쓰고 있었습니다 (2026-09-21).

          재보니 넉 자를 열여섯 칸 중 무엇으로 골라도 **훅 0·1·2·3단은
          한 글자도 안 갈렸습니다** (17칸 → 1가지). 갈리는 것은 2.5단
          하나뿐이었소. 그런데 표(`AXIS_FACE` 48칸 · `AXIS_GAP` 48칸)는
          이미 다 차 있었고, 쓰이는 것은 **그 절반**이었습니다.

          표를 늘리기 전에 어느 칸이 안 쓰이는지부터 셉니다 (CLAUDE.md
          「표를 만들고 한 군데만 꽂아 두기」).

    ★ 왜 한 줄인가 (2026-09-07)

      손님이 짚었소 — "사랑에 대한건데 사랑에 대해서는 전혀 말하지
      않아." 재보니 훅 2.5단이 230~424자로 다섯 단 중 가장 긴데
      **고민 낱말이 0회**였소. 넉 자 대조는 성격만 보고 물으신 자리를
      안 봤소.

    ★ 네 축을 다 내지는 않소. 그건 값을 치른 자리(`concern_face`)요.
      **어긋난 축이 있으면 그 첫 축**, 없으면 첫 축 하나만 냅니다 —
      저울을 첫 칸만 내는 것(`free_line`)과 같은 셈법이오.
    """
    from .bank import AXES, saju_axis
    axes = table()["AXIS_OF"].get(concern)
    if not axes:
        return None
    # 2026-09-21: 물으신 자리의 축을 먼저, 그 다음 남은 축.
    #
    #   `AXIS_OF` 는 고민마다 축 둘을 고릅니다 - 돈이면 TF.JP. 그 둘이
    #   그 자리에서 가장 크게 움직이는 축이라 먼저 냅니다. 허나
    #   `AXIS_FACE`.`AXIS_GAP` 은 여덟 글자 곱하기 여섯 고민을 다 들고
    #   있소 (마흔여덟 칸씩). 훅 다섯 마디에 나눠 걸려면 칸이 넷은
    #   있어야 하니, 남은 축도 뒤에 잇습니다.
    axes = list(axes) + [k for k, _ in AXES if k not in axes]
    idx = dict(AXES)
    mine_all = saju_axis(f)
    said = (axis4 or "").upper()
    usable = len(said) == 4

    same_rows, gap_rows = [], []
    for key in axes:
        mine = mine_all[key]
        ch = said[idx[key]] if usable else ""
        if not ch or ch not in key:
            ch = mine
        (same_rows if ch == mine else gap_rows).append((key, ch, mine))
    # ★ 어긋난 축을 먼저, 그 다음 겹친 축. 칸을 돌려 가며 냅니다 —
    #   한 훅 안에서 같은 축을 두 번 내면 그건 되풀이지 갈린 것이 아니오.
    rows = gap_rows + same_rows
    if not rows:
        return None
    key, ch, mine = rows[slot % len(rows)]

    if ch == mine:
        say = ('<p class="hit"><b>%s</b> %s</p>'
               % (ch, _pick("AXIS_FACE", ch, concern)))
        sid = "faceline:%s:%s" % (concern, ch)
    else:
        say = ('<p class="hit"><b>%s → %s</b> %s</p>'
               % (mine, ch, _pick("AXIS_GAP", "%s→%s" % (mine, ch), concern)))
        sid = "faceline:%s:%s→%s" % (concern, mine, ch)
    return {"say": say, "ev": _axis_counted(f, key), "sid": sid}


# ══════════════════════════════════════════════════════════
# 물음 — 더 물어야 할 것 하나
# ══════════════════════════════════════════════════════════
#
# ★ 「돈을 골랐으니 수입원을 내시오」 는 묻는 것이 아니라 받아 내는
#   것입니다. 그래서 물음은 **고를 것만** 냅니다 — 자유 입력은 안
#   받습니다 (개인정보가 섞이고 가드를 우회합니다).
#
# ★ 답은 **저장하지 않습니다.** 계산하고 버립니다.
def ask_spec(concern: str) -> Optional[dict]:
    """화면이 그릴 물음. 문장 원문은 안 내려보냅니다."""
    spec = table()["ASK"].get(concern)
    if not spec:
        return None
    out = {"id": concern, "title": spec["title"], "q": spec["q"],
           "options": [{"id": k, "label": v}
                       for k, v in spec["options"].items()]}
    for n in (2, 3, 4, 5):
        qkey, okey = "q%d" % n, "options%d" % n
        if spec.get(qkey):
            out[qkey] = spec[qkey]
            out[okey] = [{"id": k, "label": v}
                         for k, v in spec[okey].items()]
    return out


# 적은 것이 글자와 겹치는가 — 셀 수 있는 값으로만 판정합니다.
def _love_group(f) -> str:
    """짝을 보는 글자 묶음. 남=재성 · 여=관성 (bank.CONCERN_AXIS)."""
    from . import bank as _bank
    return _bank.concern_group("love", f.sex)


def _ask_hit(f, concern: str, slot: str, choice: str) -> Optional[bool]:
    g = f.ten_gods
    if concern == "money" and slot == "from":
        return {"pay": g["정재"] >= 1,
                "biz": g["편재"] >= 1,
                # 집·땅 — 담기는 자리(재고)와 흙을 봅니다.
                # ★ 「지금 사시오/파시오」 는 안 냅니다. 자리만 읽소.
                "estate": jaego(f) is not None or visible(f, "토") >= 3,
                # 굴리는 것(주식·코인 따위) — **편재**를 봅니다.
                #
                # ★ 이 집은 무엇이 오를지는 모릅니다. 그건 사주가 아니오.
                #   다만 **크게 걸었을 때 버티는 사람인가**는 셀 수 있소 —
                #   굴리는 자리(편재) · 감당(재다신약) · 나눌 입(군겁쟁재).
                #   그건 시점 지시가 아니라 **그릇**이오 (docs/11 을 안 넘소).
                "invest": g["편재"] >= 1,
                "many": g["편재"] >= 1 or has_sinsal(f, "yeokma"),
                "none": f.jae == 0 or f.inn >= 3}.get(choice)
    if concern == "money" and slot == "leak":
        return {"people": f.bi >= 2,
                "spread": g["편재"] >= 1 and f.strength == "신약",
                "stay": gongmang_hit(f, "재성") or f.jae == 0,
                "dunno": None}.get(choice)
    if concern == "health" and slot == "from":
        want = {"sleep": "화", "belly": "토", "power": "수", "mind": "목"}
        el = want.get(choice)
        return None if el is None else (
            el in f.weak_els or visible(f, el) >= 3)
    # ── 사랑 ──────────────────────────────────────────
    #
    # ★ 유파는 이 집이 이미 정한 것을 그대로 씁니다.
    #     짝 글자   남=재성 · 여=관성 (bank.CONCERN_AXIS.gF)
    #     배우자궁   **일지** (features.palaces 일주 · docs/14 §6)
    #     도화       「끌리는 자리」까지만. 길흉을 단정하지 않소 (docs/14 §7)
    #
    # ★ 홍염(紅艶)은 안 씁니다 — 이 집의 신살 표에 없습니다.
    #   없는 것으로 세면 그건 계산이 아니라 지어내기요 (절대 규칙 1).
    if concern == "love" and slot == "from":
        grp = _love_group(f)
        return {
            # 마음만 있는 자리 — 밖으로 나갔는가(투출)를 보오
            "alone": tuchul(f, grp) or has_sinsal(f, "dohwa"),
            # 만나는 중 — 곁자리가 묶였는가(합), 부딪히는가(충)
            "dating": bool(f.ilji_hap) and not f.ilji_chung,
            "conflict": bool(f.ilji_chung) or has_sinsal(f, "wonjin"),
            "marriage": rooted(f, grp) and not f.ilji_chung,
            "married": bool(f.ilji_hap) or rooted(f, grp),
            # 끝났거나 끝나는 중 — 끊기는 자리
            "broke": bool(f.ilji_chung) or gongmang_hit(f, grp)
                     or has_sinsal(f, "wonjin"),
            # 오래갈지 — 개수가 아니라 뿌리
            "long": rooted(f, grp),
            # 재회 성사 여부는 명식으로 판정하지 않습니다. 선택한 장면에
            # 맞춘 분석 순서만 바꾸고 맞다/틀리다는 표시하지 않습니다.
            "reunion": None,
        }.get(choice)
    if concern == "work" and slot == "leak":
        # ★ 두 번째 물음은 **셈이 갈리는 자리에만** 둡니다 (docs/40 §9).
        #   일에서 보는 것이 무엇인가 — 자리·벌이·사람·버팀은 각각
        #   관성·재성·비겁·인성으로 **실제로 갈립니다.** 그래서 둡니다.
        #   (사랑의 「누가 끝냈소」는 여덟 글자가 몰라 안 둡니다.)
        return {"rise": f.gwan >= 1, "pay": f.jae >= 1,
                "people": f.bi >= 1, "hold": f.inn >= 1,
                "dunno": None}.get(choice)
    if concern == "work" and slot == "from":
        # ★ 시험이 「준비 중」에 뭉개져 있었습니다 (2026-09-10).
        #   훈장(시험·공부·자격증)이 붙어 있는 자리인데 물음에는
        #   갈래가 없었습니다. 셋을 갈라 세웁니다 —
        #     내 일  식상생재(만든 것이 값으로 건너가는 다리)
        #     시험   인성 · 문창귀인
        #     옮김   역마 · 맡는 자리의 충
        return {"org": f.gwan >= 1,
                "biz": f.sik >= 1 and f.jae >= 1,
                "exam": f.inn >= 2 or has_sinsal(f, "munchang"),
                "move": has_sinsal(f, "yeokma") or chung_hit(f, "관성"),
                # 옛 열쇳말도 그대로 받습니다 — 이미 답한 손님이 있소.
                "alone": f.bi >= 2 or f.gwan == 0,
                "ready": f.inn >= 2,
                "rest": f.sik >= 3 or f.strength == "신약"}.get(choice)
    if concern == "people" and slot == "from":
        seat = {"home": "년주", "work": "월주", "old": "일주", "new": "시주"}
        lb = seat.get(choice)
        if lb is None:
            return None
        # ★ 시주는 **태어난 시를 알아야** 서는 기둥이오 (2026-09-23).
        #   모르는 사람에게 「시주에 받쳐 주는 글자가 없소」 라고 하면
        #   그건 없는 기둥을 채운 것이오 — 이 집이 금하는 바로 그것이오.
        if lb == "시주" and not f.hour_known:
            return None
        return any(s.get("pillar") == lb for s in (f.helpers or []))
    if concern == "dir" and slot == "from":
        return {"stay": not has_sinsal(f, "yeokma"),
                "move": has_sinsal(f, "yeokma")}.get(choice)
    if concern == "love":
        return None
    return None


# ══════════════════════════════════════════════════════════
# 갈래마다 **사실 셋** — 세고 나서 짚는다 (docs/40 §10)
# ══════════════════════════════════════════════════════════
#
# ★ 왜 셋인가 (2026-09-23)
#
#   되물음의 판정이 **갈래마다 사실 하나, 문장 하나** 였습니다.
#
#       방향 · 옮긴다   → 역마가 있나?      사실 하나 → 문장 하나
#       돈 · 굴린다     → 편재가 있나?      사실 하나 → 문장 하나
#
#   여덟 글자는 고민마다 수백 갈래를 가를 줄 아는데(docs/40 §9-2 —
#   사랑만 해도 실효 177갈래) 판정은 한 자릿수만 썼습니다. 그래서
#   갈래가 달라도 답이 비슷하게 읽혔습니다.
#
# ★ 무엇을 새로 세는가 — **아무것도 새로 안 셉니다.**
#
#   아래 자들은 전부 이 파일과 `features` 가 **이미 세고 있던 값**입니다
#   (투출·뿌리·공망·충·일지 합·신살·대운·세운·귀인 자리·재고·오행 수).
#   새로 점치는 것이 아니라, 세어 둔 것을 갈래에 대 보는 것뿐이오.
#
# ★ 자 하나는 (가름, 센 값) 둘을 돌려줍니다.
#
#       가름   True 겹침 · False 어긋남 · None 판정 안 함
#       센 값  손님이 만세력을 펴고 **대 볼 수 있는 말**
#
#   못 세는 자리는 **None** 을 냅니다. 시주를 모르는 사람에게
#   「시주에 귀인이 없소」 라고 하면 그건 지어내는 것이오
#   (절대 규칙 1 — 계산이 없으면 「모른다」).
def _fact_ctx(concern: str, sub: Optional[dict] = None) -> dict:
    """자들이 함께 보는 자리. 고민이 바뀌면 보는 묶음이 바뀌오."""
    from . import bank as _bank
    sub = sub or {}
    row = _bank.bank()["CONCERN_AXIS"][concern]
    return {"concern": concern,
            "choice": str(sub.get("choice") or ""),
            "choice2": str(sub.get("choice2") or ""),
            "grp": row["g"],
            "grpF": row.get("gF") or row["g"]}


def _ctx_group(f, ctx: dict) -> str:
    """물은 자리의 십신 묶음. 사랑은 남녀가 갈리오 (bank.CONCERN_AXIS)."""
    return ctx["grpF"] if f.sex == "F" else ctx["grp"]


def _n_say(n: int, name: str) -> str:
    """
    「재성 2자」 — 센 값은 **재는 말**로 냅니다.

    ★ 「있소·없소」 를 여기 넣지 마시오. 바로 뒤에 오는 문장이 그
      말을 또 하게 되어, 손님은 같은 말을 두 번 읽습니다. 앞은
      **수**이고 뒤는 **뜻**이오.
    """
    return "%s %d자" % (name, n)


def _group_n(f, grp: str) -> int:
    from .bank import GROUP_TOTAL
    return int(getattr(f, GROUP_TOTAL[grp]))


# ── 물은 자리를 세는 자 ──────────────────────────────────
def _fx_group_count(f, ctx):
    grp = _ctx_group(f, ctx)
    return (_group_n(f, grp) >= 1, _n_say(_group_n(f, grp), grp))


def _fx_group_tuchul(f, ctx):
    grp = _ctx_group(f, ctx)
    gans = _group_gans(f, grp)
    return (bool(gans),
            "천간 %s %d자%s"
            % (grp, len(gans), ("(%s)" % "·".join(gans)) if gans else ""))


def _fx_group_root(f, ctx):
    grp = _ctx_group(f, ctx)
    gans, jis = _group_gans(f, grp), _group_jis(f, grp)
    return (bool(gans) and bool(jis),
            "%s 천간 %d자 · 지지 %d자" % (grp, len(gans), len(jis)))


def _fx_group_gongmang(f, ctx):
    grp = _ctx_group(f, ctx)
    return (gongmang_hit(f, grp),
            "공망 %s · 물은 자리 %s" % (f.gongmang or "없음", grp))


def _fx_group_chung(f, ctx):
    grp = _ctx_group(f, ctx)
    return (chung_hit(f, grp),
            "여덟 글자에 부딪히는 짝 %d쌍" % chung_pairs(f))


# ── 곁자리(일지) ────────────────────────────────────────
def _fx_ilji_hap(f, ctx):
    return (bool(f.ilji_hap),
            "일지 %s · 묶이는 글자 %d자%s"
            % (f.day_ji, len(f.ilji_hap or []),
               ("(%s)" % "·".join(f.ilji_hap)) if f.ilji_hap else ""))


def _fx_ilji_chung(f, ctx):
    return (bool(f.ilji_chung),
            "일지 %s · 부딪히는 글자 %d자"
            % (f.day_ji, 1 if f.ilji_chung else 0))


# ── 신살 ────────────────────────────────────────────────
def _sinsal_fact(key: str, name: str):
    def fn(f, ctx):
        at = _sinsal_at(f, key)
        return (bool(at), "%s %d곳%s"
                % (name, len(at), ("(%s)" % "·".join(at)) if at else ""))
    return fn


# ── 때 ──────────────────────────────────────────────────
def _fx_daeun_group(f, ctx):
    grp = _ctx_group(f, ctx)
    now = GROUP_OF.get(f.daeun_ten_god, f.daeun_ten_god)
    d = (f.daeun or [{}])[f.daeun_now] if f.daeun else {}
    return (now == grp,
            "지금 %d살 · 대운 %s %s"
            % (int(f.age), d.get("gz", ""), f.daeun_ten_god))


def _fx_daeun_left(f, ctx):
    nx = _next_daeun(f)
    if not nx:
        return (None, "다음 대운 · 표에 없어 안 세오")
    return (int(nx[0]) - int(f.age) <= 3,
            "다음 대운 %d살 · %d해 남음"
            % (int(nx[0]), int(nx[0]) - int(f.age)))


def _fx_sewoon_group(f, ctx):
    grp = _ctx_group(f, ctx)
    yg = GROUP_OF.get(f.year_ten_god, f.year_ten_god)
    return (yg == grp,
            "올해 %s %s · 물은 자리 %s" % (f.year_gz, f.year_ten_god, grp))


# ── 얼굴 ────────────────────────────────────────────────
def _fx_strength(f, ctx):
    return (f.strength == "신약",
            "신강약 %s · 점수 %d" % (f.strength, int(f.strength_score)))


def _fx_weak_here(f, ctx):
    grp = _ctx_group(f, ctx)
    el = el_of_group(f.day_gan, grp)
    if not el:
        return (None, "물은 자리의 오행을 못 잡았소")
    return (el in f.weak_els,
            "%s의 오행은 %s — 겉에 %d자" % (grp, el, visible(f, el)))


# ── 십신 낱낱 ───────────────────────────────────────────
def _ten_fact(name: str):
    def fn(f, ctx):
        n = int(f.ten_gods.get(name, 0))
        return (n >= 1, _n_say(n, name))
    return fn


def _group_fact(grp: str):
    def fn(f, ctx):
        return (_group_n(f, grp) >= 1, _n_say(_group_n(f, grp), grp))
    return fn


# ── 오행 ────────────────────────────────────────────────
#
# ★ 「겉에 몇 자」 는 손님이 만세력을 펴고 그대로 셀 수 있는 수요.
#   가름은 **치우쳤는가** 입니다 — 없거나(0) 몰렸거나(3 이상).
def _el_fact(el: str):
    def fn(f, ctx):
        n = visible(f, el)
        return (n == 0 or n >= 3, "겉에 %s %d자" % (el, n))
    return fn


# ── 짜임 ────────────────────────────────────────────────
def _fx_sik_jae(f, ctx):
    return (f.sik >= 1 and f.jae >= 1,
            "식상 %d자 · 재성 %d자" % (int(f.sik), int(f.jae)))


def _fx_jae_da(f, ctx):
    return (f.jae >= 2 and f.strength == "신약",
            "재성 %d자 · 신강약 %s" % (int(f.jae), f.strength))


def _fx_gun_geop(f, ctx):
    return (f.bi >= 2 and f.jae >= 1,
            "비겁 %d자 · 재성 %d자" % (int(f.bi), int(f.jae)))


def _fx_jaego(f, ctx):
    go = jaego(f)
    return (go is not None, "담기는 칸 %s" % (go or "0"))


# ── 자리 ────────────────────────────────────────────────
def _helper_fact(pillar: str, need_hour: bool = False):
    def fn(f, ctx):
        # ★ 시주를 모르면 **모른다고 합니다.** 없다고 하면 지어내기요.
        if need_hour and not f.hour_known:
            return (None, "시주 귀인 · 안 세오")
        at = [s.get("sinsal") or s.get("name") or ""
              for s in (f.helpers or []) if s.get("pillar") == pillar]
        at = sorted({x for x in at if x})
        return (bool(at), "%s 귀인 %d%s"
                % (pillar, len(at), ("(%s)" % "·".join(at)) if at else ""))
    return fn


def _fx_hour_known(f, ctx):
    return (f.hour_known,
            "기둥 %d · 글자 %d" % (len(f.pillars), len(f.pillars) * 2))


# ★ 이름은 **표가 부르는 열쇠**입니다. 여기 없는 이름을 표에 적으면
#   `tests/test_topic_facts` 가 「셀 자가 없소」 라고 잡습니다.
_FACTS = {
    "group_count": _fx_group_count,
    "group_tuchul": _fx_group_tuchul,
    "group_root": _fx_group_root,
    "group_gongmang": _fx_group_gongmang,
    "group_chung": _fx_group_chung,
    "ilji_hap": _fx_ilji_hap,
    "ilji_chung": _fx_ilji_chung,
    "dohwa": _sinsal_fact("dohwa", "도화"),
    "yeokma": _sinsal_fact("yeokma", "역마"),
    "wonjin": _sinsal_fact("wonjin", "원진"),
    "munchang": _sinsal_fact("munchang", "문창"),
    "hwagae": _sinsal_fact("hwagae", "화개"),
    "daeun_group": _fx_daeun_group,
    "daeun_left": _fx_daeun_left,
    "sewoon_group": _fx_sewoon_group,
    "strength": _fx_strength,
    "weak_here": _fx_weak_here,
    "jeongjae": _ten_fact("정재"),
    "pyeonjae": _ten_fact("편재"),
    "jeonggwan": _ten_fact("정관"),
    "pyeongwan": _ten_fact("편관"),
    "jeongin": _ten_fact("정인"),
    "pyeonin": _ten_fact("편인"),
    "sangwan": _ten_fact("상관"),
    "siksin": _ten_fact("식신"),
    "gyeopjae": _ten_fact("겁재"),
    "bigyeon": _ten_fact("비견"),
    "jae_group": _group_fact("재성"),
    "gwan_group": _group_fact("관성"),
    "sik_group": _group_fact("식상"),
    "bi_group": _group_fact("비겁"),
    "inn_group": _group_fact("인성"),
    "el_mok": _el_fact("목"),
    "el_hwa": _el_fact("화"),
    "el_to": _el_fact("토"),
    "el_geum": _el_fact("금"),
    "el_su": _el_fact("수"),
    "sik_jae": _fx_sik_jae,
    "jae_da": _fx_jae_da,
    "gun_geop": _fx_gun_geop,
    "jaego": _fx_jaego,
    "helper_year": _helper_fact("년주"),
    "helper_month": _helper_fact("월주"),
    "helper_day": _helper_fact("일주"),
    "helper_hour": _helper_fact("시주", need_hour=True),
    "hour_known": _fx_hour_known,
}


def count_of(f, concern: str, fact_id: str,
             sub: Optional[dict] = None) -> Optional[tuple]:
    """
    세는 자 하나를 이름으로 부른다. `(가름, 센 값)` — 없으면 None.

    ★ 표(`seed/topic.json` FACTS)를 거치지 않고 **자만** 빌려 쓰는
      자리요. 첫 해석이 이걸 씁니다 — 같은 자를 두 벌 만들면 무료
      구간과 유료 구간이 서로 다른 수를 대게 되오.
    """
    fn = _FACTS.get(fact_id)
    if not fn:
        return None
    return fn(f, _fact_ctx(concern, sub))


def fact_rows(f, concern: str, sub: Optional[dict]) -> list:
    """
    고른 갈래에 걸리는 **사실 셋**. 표에 없으면 빈 목록이오.

    돌려주는 것: [{"id", "label", "count", "verdict", "say"}]
    """
    pick = str((sub or {}).get("choice") or "")
    rows = ((table().get("FACTS") or {}).get(concern) or {}).get(pick) or []
    ctx = _fact_ctx(concern, sub)
    out = []
    for row in rows:
        fn = _FACTS.get(row.get("id"))
        if not fn:
            continue
        verdict, count = fn(f, ctx)
        key = "hit" if verdict else ("miss" if verdict is False else "unk")
        say = row.get(key) or row.get("unk") or row.get("miss")
        if not say:
            continue
        out.append({"id": row["id"], "label": row.get("label") or row["id"],
                    "count": count, "verdict": verdict, "say": say})
    return out


def ask_cut(f, concern: str, payload: dict) -> Optional[dict]:
    """
    손님이 고른 것과 여덟 글자를 맞대 본 컷.

    ★ 「모르겠소」는 판정하지 않습니다 — 노출로만 셉니다.
      그렇소·아니오 둘만 두면 애매한 사람이 거짓 답을 눌러
      공감률이 오염됩니다 (CLAUDE.md).
    """
    spec = table()["ASK"].get(concern)
    if not spec or not payload:
        return None
    pick = str(payload.get("choice") or "")
    if pick not in spec["options"]:
        raise TopicInputError(
            "고르신 것이 목록에 없소: %r (고를 수 있는 것: %s)"
            % (pick, " · ".join(spec["options"].values())))
    pick2 = str(payload.get("choice2") or "")
    if spec.get("options2") and pick2 and pick2 not in spec["options2"]:
        raise TopicInputError(
            "고르신 것이 목록에 없소: %r (고를 수 있는 것: %s)"
            % (pick2, " · ".join(spec["options2"].values())))
    pick3 = str(payload.get("choice3") or "")
    if spec.get("options3") and pick3 and pick3 not in spec["options3"]:
        raise TopicInputError(
            "고르신 것이 목록에 없소: %r (고를 수 있는 것: %s)"
            % (pick3, " · ".join(spec["options3"].values())))
    # choice4/choice5는 캐릭터별 전문 질문이 덮어쓸 수 있다.
    # 여기서 기본 고민표로 검증하면 캐릭터가 제시한 유효한 답을 거부한다.
    picks = {4: str(payload.get("choice4") or ""),
             5: str(payload.get("choice5") or "")}

    w = _words(f)

    def said(lead, label):
        # 「월급라 하셨소」 가 나가던 자리요. 받침을 보고 답니다.
        return ('<p class="tale">%s <b>%s</b>%s 하셨소.</p>'
                % (lead, label, "이라" if _batchim(label) else "라"))

    parts = [said(spec["lead"], spec["options"][pick])]
    hit = _ask_hit(f, concern, "from", pick)
    say = spec["say"][pick]
    parts.append('<p class="hit">%s</p>'
                 % _fmt(say["hit" if hit else "miss"] if hit is not None
                        else say["dunno"], w))
    ev = ["%s → %s" % (spec["options"][pick],
                       "글자와 겹침" if hit else
                       ("글자는 다른 것을 가리킴" if hit is False else "판정 안 함"))]
    # ★ 사실 셋 — 센 값을 앞에 세우고 살림의 말로 짚습니다 (docs/40 §10).
    #
    #   전에는 갈래마다 **사실 하나 · 문장 하나** 였습니다. 그러면
    #   갈래를 아무리 갈라도 답이 한 줄이라 비슷하게 읽힙니다.
    #   센 값은 손님이 만세력을 펴고 대 볼 수 있는 말이라야 하오 —
    #   그래서 문장 앞에 굵게 세웁니다 (근거 줄에도 같이 적습니다).
    facts = fact_rows(f, concern, payload)
    fmark = ""
    for fx in facts:
        parts.append('<p class="cnt"><b>%s</b> — %s</p>'
                     % (fx["count"], _fmt(fx["say"], w)))
        ev.append("%s · %s" % (fx["label"], fx["count"]))
        fmark += ("h" if fx["verdict"] else
                  ("m" if fx["verdict"] is False else "u"))
    hit2 = None
    if pick2:
        parts.append(said(spec["lead2"], spec["options2"][pick2]))
        hit2 = _ask_hit(f, concern, "leak", pick2)
        say2 = spec["say2"][pick2]
        parts.append('<p class="hit">%s</p>'
                     % _fmt(say2["hit" if hit2 else "miss"] if hit2 is not None
                            else say2["dunno"], w))
        ev.append("%s → %s" % (spec["options2"][pick2],
                               "글자와 겹침" if hit2 else
                               ("글자는 다른 것을 가리킴" if hit2 is False else "판정 안 함")))
    if pick3:
        parts.append(said(spec["lead3"], spec["options3"][pick3]))
        say3 = spec["say3"][pick3]
        parts.append('<p class="hit">%s</p>' % _fmt(say3["dunno"], w))
        ev.append("%s → 사용자가 원하는 판단" % spec["options3"][pick3])
    for n in (4, 5):
        value = picks[n]
        options = spec.get("options%d" % n)
        if value and options and value in options:
            label = options[value]
            parts.append('<p class="tale"><b>%s</b>라고 하셨소. 이 답을 이번 해석의 범위로 삼겠소.</p>' % label)
            ev.append("%s → 상담 범위" % label)
    parts.append('<p class="tale">%s</p>' % spec["tail"])

    body = "".join(parts)
    return {
        "id": "topic_ask", "title": spec["title"],
        "source": _why.axis_line(" · ".join(ev), "concern"),
        "html": guard.enforce(body, {"cut": "topic_ask"}),
        # ★ 손님이 적은 것은 **그 자리에서** 값을 합니다 (2026-09-10).
        #
        #   전에는 1층(유료)이었습니다. 무료 구간에서 묻고 답은 값을
        #   치러야 보이면, 그건 묻는 것이 아니라 **받아 내는 것**이오.
        #   이 파일이 이미 경계하던 「물어 놓고 안 받는 자리」와 같은 병입니다.
        #
        #   깊이는 그대로 값 뒤에 있습니다 — 세는 자리(concern_scale) ·
        #   짜임(concern_pattern) · 때(concern_turn) · 얼굴(concern_face)
        #   넷은 안 건드립니다. 무료는 **적은 것과 글자가 겹치는가**까지요.
        "min_level": 0,
        # ★ 사실 셋의 가름까지 번호에 넣습니다. 안 넣으면 「뿌리가 있는
        #   사람」과 「없는 사람」의 공감률이 한 통에 섞이오.
        "statement_id": "ask:%s:%s:%s:%s:%s:%s%s:%s"
                        % (concern, pick, pick2 or "-", pick3 or "-",
                           picks[4] or "-", picks[5] or "-",
                           (":f=" + fmark) if fmark else "",
                           "%s%s" % ("h" if hit else ("m" if hit is False else "u"),
                                     "h" if hit2 else
                                     ("m" if hit2 is False else "u"))),
    }


# ══════════════════════════════════════════════════════════
# 무료 한 줄 — 값을 치르기 전에도 세고 있다는 것이 보이게
# ══════════════════════════════════════════════════════════
def free_line(f, concern: str) -> str:
    """
    훅 마감에 붙는 저울 한 줄. 가장 앞 칸 하나만 냅니다.

    ★ 맛보기가 아니라 **셈**입니다. 뒤를 안 사도 손님이 만세력을
      펴고 맞는지 틀리는지 댈 수 있어야 합니다.
    """
    rows = scale(f, concern)
    if not rows:
        return ""
    r = rows[0]
    return r["say"]
