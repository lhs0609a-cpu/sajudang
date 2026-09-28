# -*- coding: utf-8 -*-
"""
한 장의 **단위** — 컷이 아니라 주장.

★ 왜 다시 짜는가 (2026-09-28)

  엔진의 글이 22,476줄 · 4,363칸 · 231,908자였습니다. 그런데 손님 축으로
  재 보니 **한 장의 69.1%가 사람이 바뀌어도 글자 그대로 같았습니다.**
  가장 큰 컷(`spine_scene` 1,661자 · 이름이 「실제 장면과 반복 조건」)은
  **99%**였고, `practice.*` 는 전부 100%였습니다.

  까닭은 단위였습니다. 여태 「표 칸 하나 = 완성된 문장 하나」였습니다.
  그러니 가짓수를 늘리는 길이 **칸을 늘리는 것**뿐이었고, 칸의 열쇠는
  `(고민 × 캐릭터 × MBTI × 흐름)` 이라 **여덟 글자가 그 열쇠에
  없었습니다.** `practice.build(concern, flow)` 가 `f` 를 아예 안 받는
  것이 우연이 아니라 구조였습니다.

  여기서는 단위를 바꿉니다 — 「칸 = 슬롯이 뚫린 주장 한 꼴」이고
  문장은 **셈이 채웁니다.** 가짓수가 칸 수에서 나오지 않고 셈의
  조합에서 나옵니다.

★ 그리고 이 집이 배운 금을 **타입이 막습니다.**

  여태 그 금들은 CLAUDE.md 에 글로 적혀 있었고 자들이 뒤에서 잡았습니다.
  뒤에서 잡는 자는 고치고 나서야 압니다 — 그 사이 배포가 나갑니다.
  여기서는 어긴 주장을 **만들 수가 없습니다**:

      근거에 수를 안 대기        → `counted` 없이 Claim 을 못 만듭니다
      단위 없는 수를 내기        → `Counted.단위` 가 필수입니다
      장면을 물건 없이 쓰기      → `Scene.물건` 이 필수이고 뜬 낱말을 거부합니다
      제목에 어미를 달기         → `verdict` 가 어미를 거부합니다
      같은 축을 한 장에 두 번    → `Page` 가 축을 하나만 받습니다
      시키는 일을 둘로          → 처방은 `Page` 에 **한 칸**입니다
      명식 컷에 고민을 들이기    → kind="ledger" 는 asked 를 0 으로 못박습니다
      틀릴 수 없는 말 쓰기       → counted 가 있으니 만세력을 펴고 댈 수 있습니다

  검사는 `tests/test_reading_claim.py` 가 셉니다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

# ── 셀 수 있는 단위 ───────────────────────────────────────────────
#
# ★ 단위 없는 수는 근거가 아니라 **벽**입니다. 「정관 0」 「중화(3)」 가
#   나갔던 자리요 — 손님은 그게 글자 수인지 점수인지 모릅니다.
#   그래서 단위를 **목록으로** 못박습니다. 새 단위가 필요하면 여기
#   적으시오 — 아무 말이나 단위 자리에 들어가면 목록이 뜻을 잃습니다.
UNITS = {
    "자": "여덟 글자 안의 글자 수",
    "개": "셀 수 있는 것의 수",
    "살": "나이",
    "해": "햇수",
    "명": "인구 만 명에 몇 명",
    "칸": "대운·궁위의 칸",
    "번": "횟수",
}

#: ★ **내부 점수는 단위가 아닙니다.** `strength_score` 가 여섯 자리에서
#: 샌 적이 있습니다. 손님이 만세력을 펴고 댈 수 없는 수는 근거가 아니오.
BANNED_UNITS = {"점", "%", "퍼센트", "score", "배", "위"}

# 한글 수 — `\d` 만 보는 자가 절반을 못 본 자리요 (`bank.count_word`).
#
# ★ 셋·넷은 매인이름씨에 따라 꼴이 갈립니다 — 「석 자」 는 맞고 「석 개」 는
#   비문이오(세 개). 단위로 갈라 둡니다.
_KO_NUM = ("영", "한", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉", "열")
_KO_NUM_JA = ("영", "한", "두", "석", "넉", "다섯", "여섯", "일곱", "여덟", "아홉", "열")
_KO_UNITS = ("자", "개", "칸", "번")


def count_word(n: float, unit: str) -> str:
    """
    수를 **손님 말**로. 「쇠는 셋이오」를 자가 못 본 자리를 기억하시오.

    띄웁니다 — 「한 자」. 「한자」 는 다른 낱말이오.

    ★ 0 은 **맺는 말**을 돌려줍니다 (「한 자도 없소」 · 「없소」). 문장
      한가운데에 그대로 끼우면 「겉에 쇠가 한 자도 없소인데도」 가 됩니다 —
      그 자리에서는 `count_np` 를 쓰시오.
    """
    if n != int(n):
        return "%g%s" % (n, unit)
    i = int(n)
    if unit in _KO_UNITS and 0 <= i <= 10:
        if i == 0:
            return "한 %s도 없소" % unit if unit == "자" else "없소"
        table = _KO_NUM_JA if unit == "자" else _KO_NUM
        return "%s %s" % (table[i], unit)
    return "%d%s" % (i, unit)


# ── 댈 수 있는 값이 든 문장 ────────────────────────────────────────
#
# ★ 왜 이 자가 타입 안에 있는가 (2026-09-28)
#
#   손님이 「날카롭지 않다」 했을 때 재 보니, 한 장 2,014문장 가운데
#   센 값이 든 것이 **15.8%**였습니다. 나머지 67.4%는 단정인데 **어떤
#   관찰로도 거짓이 안 되는** 말이었습니다. 한 컷이 열다섯 문장인데
#   댈 수 있는 것이 둘인 자리가 일곱 개 있었습니다.
#
#   `counted` 를 필수로 만든 것은 **근거 줄**을 지켰을 뿐입니다. 본문은
#   여전히 뜬 말로 채울 수 있었습니다. 그래서 본문도 셉니다.
#
#   ★ 한글 수를 빠뜨리지 마시오. 이 집은 「쇠는 셋이오」 라고 적습니다 —
#     `\d` 만 보는 자는 절반을 못 봅니다.
FACT = re.compile(
    r"[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]"
    r"|\d"
    r"|(?:비견|겁재|식신|상관|편재|정재|편관|정관|편인|정인"
    r"|재성|관성|식상|인성|비겁|신강|신약|중화|용신|대운|절입|공망"
    r"|일간|일지|월지|년주|월주|일주|시주|지장간|진태양시|재고|희소도)"
    r"|(?:한|두|석|넉|세|네|다섯|여섯|일곱|여덟|아홉|열)\s?(?:자|개|칸|번|살|해)"
    r"|하나뿐"
    # ★ **명식에서 짚을 수 있는 자리**도 댈 수 있는 값이오 (2026-09-28).
    #
    #   「겉에도 안 나오고 발밑에도 뿌리가 없소」 는 수가 안 들었지만
    #   손님이 만세력을 펴고 천간·지지를 보고 **틀렸다고 말할 수
    #   있습니다.** 자가 수만 보면 이런 줄을 뜬 말로 셉니다.
    #
    #   금은 하나요 — 명식의 **자리 이름**만 넣습니다. 「마음」 「자리」
    #   「힘」 같은 이 집의 뜬 낱말을 여기 넣으면 그날로 자는 거울이
    #   되오 (`_FLOATY` 와 같은 금이오).
    r"|(?:겉에|발밑|뿌리|투출|통근|천간|지지|순중|길신|신살|궁위"
    r"|앉은|앉았|기둥|절입)"
    # ★ **쉬운 말로 적은 같은 자리**도 셉니다 (2026-09-28).
    #
    #   본문을 쉬운 말로 다시 쓰자 이 자가 「댈 값이 없다」 고 막았습니다.
    #   자가 명리 **이름**을 세고 있었기 때문이오 — 「중화」 를 빼고
    #   「넘치지도 모자라지도 않은 쪽」 이라 쓰면 0점이 됐습니다.
    #
    #   그런데 줄을 댈 수 있게 하는 것은 이름이 아니라 **수 · 실제 글자 ·
    #   명식의 자리**입니다. 「태어난 달 칸」 은 월주와 같은 자리를 가리키고
    #   손님은 만세력을 펴고 똑같이 셀 수 있소.
    #
    #   금은 그대로입니다 — **자리와 글자만** 넣고 「마음」 「힘」 「몫」 같은
    #   뜬 낱말은 안 넣습니다 (`_FLOATY` 와 같은 금이오). 자를 글에 맞추면
    #   그날로 자는 거울이 되오.
    r"|(?:태어난 (?:해|달|날|시각) 두 글자|위 글자|아래 글자|숨은"
    r"|비는 글자|돕는 글자|넣어 두는 곳|받쳐 주는 글자|그 글자|이 글자"
    r"|두 글자|보는 나이|그 나이)"
    # 오행의 쉬운 이름 — 만세력에서 그대로 셉니다.
    # 오행의 쉬운 이름 — 뒤에 한글이 안 붙으면 그 이름이오.
    #   「불 쪽」 「쇠요」 는 세고 「물건」 「불편」 은 안 셉니다.
    #   뒤에 토씨나 빈칸이 오면 그 이름이오 — 「불 쪽」 「쇠라」 「나무요」.
    #   「물건」 「불편」 처럼 다른 낱말이 되는 자리는 안 셉니다.
    r"|(?:나무|불|흙|쇠|물)(?=\s|$|[^가-힣]|쪽|가|이|는|은|를|을|로|와|과"
    r"|만|뿐|요|도|랑|라)"
    # 명식 그 자체를 가리키는 말.
    r"|여덟 글자|여섯 글자")

_SENT = re.compile(r"(?<=오\.)|(?<=소\.)|(?<=요\.)|(?<=다\.)|(?<=[.!?])\s+")
_TAG_BLOCK = re.compile(r"</?(?:p|div|br|li|ul|ol|h[1-6])(?![a-zA-Z0-9])[^>]*>",
                        re.I)
_TAG_INLINE = re.compile(r"</?[a-zA-Z][^>]*>")


def plain(html: str) -> str:
    """
    태그를 걷은 글.

    ★ 끼는 태그(`<b>` `<mark>`)를 빈칸으로 바꾸면 **낱말이 갈라집니다.**
      줄을 끊는 태그만 빈칸이오 (`tools/seen_page.plain` 과 같은 규칙).
    """
    t = _TAG_BLOCK.sub(" ", html or "")
    t = _TAG_INLINE.sub("", t)
    return re.sub(r"\s+", " ", t).strip()


def sentences(html: str) -> list:
    return [x.strip() for x in _SENT.split(plain(html)) if len(x.strip()) >= 8]


def fact_ratio(html: str) -> float:
    """댈 수 있는 값이 든 문장의 몫. 0~1."""
    ss = sentences(html)
    if not ss:
        return 0.0
    return sum(1 for s in ss if FACT.search(s)) / len(ss)


def count_np(n: float, unit: str) -> str:
    """
    문장 **한가운데**에 끼울 수 있는 꼴. 0 이어도 맺지 않습니다.

        count_word(0, "자") → "한 자도 없소"   (맺는 말)
        count_np(0, "자")   → "한 자도"        (이어지는 말)
    """
    if n == 0:
        return "한 자도" if unit == "자" else "하나도"
    return count_word(n, unit)


class ClaimError(ValueError):
    """주장을 지을 수 없을 때. **지어내지 말고 멈춥니다.**"""


# ── 센 값 ────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Counted:
    """
    손님이 만세력을 펴고 **대 볼 수 있는** 수 하나.

    네 조각이 다 있어야 합니다 — 값·단위·무엇을·어디서.
    「재성 1」 은 틀릴 수가 없고 「겉에 재성 한 자」 는 틀릴 수 있습니다.
    """
    값: float
    단위: str
    무엇: str
    어디: str

    def __post_init__(self):
        if self.단위 in BANNED_UNITS:
            raise ClaimError(
                "내부 점수는 근거가 아니오: %r — 손님이 대 볼 수 있는 단위를 쓰시오"
                % self.단위)
        if self.단위 not in UNITS:
            raise ClaimError("모르는 단위: %r (아는 것: %s)"
                             % (self.단위, " · ".join(sorted(UNITS))))
        for name in ("무엇", "어디"):
            if not str(getattr(self, name)).strip():
                raise ClaimError("%s 가 비었소 — 무엇을 어디서 세었는지 적으시오" % name)

    @property
    def 말(self) -> str:
        """손님 말로 — 「겉에 재성 한 자」"""
        return "%s %s %s" % (self.어디, self.무엇, count_word(self.값, self.단위))

    @property
    def 수(self) -> str:
        """근거 줄로 — 「재성 1자(겉)」. ★ 아라비아 숫자를 답니다."""
        return "%s %g%s(%s)" % (self.무엇, self.값, self.단위, self.어디)


# ── 이치 ─────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Ground:
    """
    왜 그렇게 읽는가. 셋이 다 있어야 손님이 **어디가 틀렸는지** 짚습니다.

    ★ 이치 자리에서 뜻풀이를 하지 마시오. 풀이는 괄호가 맡습니다 —
      「월지(태어난 달의 아래 글자)는 태어난 달의 아래 글자라…」 가
      나갔던 자리요.
    """
    본것: str      # 무엇을 보았나
    이치: str      # 어떤 규칙으로 읽었나
    출처: str      # 어느 유파의 규칙인가

    def __post_init__(self):
        for name in ("본것", "이치", "출처"):
            if not str(getattr(self, name)).strip():
                raise ClaimError("근거의 %s 가 비었소 — 셋이 다 있어야 짚을 수 있소" % name)
        if re.search(r"[<>≤≥=]|\d+\s*(?:이상|이하|초과|미만)", self.이치):
            raise ClaimError("이치에 연산자·문턱값을 쓰지 마시오: %r "
                             "— 근거는 보이되 규칙은 감춥니다" % self.이치)


# ── 살림의 장면 ──────────────────────────────────────────────────
#
# ★ 이 집의 뜬 낱말. 장면의 **물건** 자리에 오면 그림이 안 그려집니다.
#   276칸을 채웠을 때 216칸이 이랬고 자는 한 눈금도 안 움직였습니다.
_FLOATY = {"자리", "얼굴", "철", "마음", "기운", "힘", "몫", "때", "쪽", "무게",
           "그림자", "흐름", "순서", "기준", "조건", "관계", "상황", "부분"}


@dataclass(frozen=True)
class Scene:
    """
    뜬 말 뒤에 붙는 **눈에 보이는 물건** 한 줄.

    「요즘 가장 피하고 싶은 그 일」 은 맞는 말이나 그림이 안 그려집니다.
    어제 손에 쥔 것을 대시오 — 카드값 · 단톡 · 견적 · 이력서 · 구독.
    """
    물건: str
    한줄: str

    def __post_init__(self):
        if not self.물건.strip():
            raise ClaimError("장면에 물건이 없소 — 어제 손에 쥔 것을 대시오")
        if self.물건 in _FLOATY:
            raise ClaimError("뜬 낱말은 물건이 아니오: %r — 그 표 전체가 흐려집니다"
                             % self.물건)
        if self.물건 not in self.한줄:
            raise ClaimError("장면에 물건이 안 보이오: %r 가 한줄에 없소" % self.물건)



# ── 도출 명시 ────────────────────────────────────────────────────
@dataclass(frozen=True)
class Derived:
    """
    **손님이 준 입력으로 우리가 무엇을 했는지** 한 줄. 첫머리에 섭니다.

    ★ 문헌이 가리키는 가장 큰 레버입니다 (2026-09-28)

      Snyder (1974) 는 **똑같은** 호로스코프를 주고 「무엇에서 나왔다고
      말했는지」만 바꿨습니다 —

          "사람들에게 대체로 맞는 말"        수용도 3.24
          생년 + 월을 물어봄                      3.76
          생년 + 월 + **일**을 물어봄             4.38   (F=7.56, p<.0002)

      글을 **한 글자도 안 고치고** 나온 차이요. 논문은 덧붙입니다 —
      진지한 명리가는 시·분까지 받는데, 그 정도로 구체한 입력이면
      수용도가 더 오를 것이라고.

      이 집은 분 단위 · 진태양시 · sxtwl 절입 시각 · 조자시까지 셉니다.
      **시장에서 가장 정밀한 입력을 쥐고 있는데 그걸 말하지 않고
      있었습니다.** 이 한 줄은 새 콘텐츠가 아니라 이미 한 계산을 소리
      내어 말하는 것이오.

      그리고 이 줄은 「요즘 앱은 그냥 AI 에 학습시켜 사주 보게 하는 것」
      이라는 시장의 기본 의심에 대한 유일한 반박이기도 합니다.
    """
    입력: str        # 손님이 적은 값 그대로 ("오후 3시 55분" · "미상")
    한일: str        # 우리가 한 계산
    바뀐것: str      # 그래서 무엇이 달라졌나

    def __post_init__(self):
        for name in ("입력", "한일", "바뀐것"):
            if not str(getattr(self, name)).strip():
                raise ClaimError("도출 명시의 %s 가 비었소" % name)
        if not (re.search(r"\d", self.입력) or "미상" in self.입력
                or "모르" in self.입력):
            raise ClaimError(
                "도출 명시에 손님이 적은 값이 없소: %r — 「무엇에서 나왔다」 가 "
                "빠지면 이 줄은 그냥 머리말이오" % self.입력)

    @property
    def html(self) -> str:
        """
        ★ 꼬리를 **여기서 붙이지 않습니다** (2026-09-28).

          「…에 났다이라 하셨소」 「…모른다고 하시니에 났다 하셨소」 가
          차례로 나갔습니다. 붙이는 자리와 짓는 자리가 갈려 있어서요.
          `입력` 은 **문장 앞토막을 그대로** 담고, 여기서는 잇기만 합니다.
        """
        return ('<p class="derived">%s %s %s</p>'
                % (self.입력.rstrip(), self.한일, self.바뀐것))


# ── 주장 ─────────────────────────────────────────────────────────
#: 주장의 갈래. 갈래마다 지킬 것이 다릅니다.
KINDS = {
    "ledger":  "명식 장부 — 무엇을 물었든 같은 여덟 글자. 고민을 들이지 않습니다",
    "verdict": "판정 — 센 값 + 살림의 장면. 이 집이 파는 것",
    "solace":  "위로 — 아픈 말 뒤. **셈에서** 나옵니다",
    "hope":    "희망 — 이미 가진 것과 바뀌는 때. 약속하지 않습니다",
    "depth":   "깊이 — 비싼 자리만 여는 다른 종류",
    "pair":    "뒤집기 — 잘하는 것과 같은 힘의 그늘. 칭찬만 하지 않는 장치",
}

#: 표지판·제목은 `voice` 층을 안 탑니다(html·source 만 갑니다). 그래서
#: 어미를 달면 스무 명이 전부 하오체로 그 한 줄을 말합니다 — 반말
#: 캐릭터에게서도요. 꼴은 「…하는 자리」 요: 주장이면서 어미가 없습니다.
_ENDING = re.compile(r"(?:습니다|십시오|는다|이다|구나|군요|네요|"
                     r"[오소요네다지어야까죠])$")


@dataclass(frozen=True)
class Claim:
    """
    한 장에 한 번 쓰이는 **주장 하나**.

    `axis` 가 열쇠입니다 — 한 장에 같은 축은 한 번뿐입니다. 여태
    「버는 힘 ≠ 남기는 힘」 하나를 다섯 자리(h1 · spine · spine_depth ·
    closing_cut · 잠김 teaser)에서 말하고 있었습니다.
    """
    axis: str
    kind: str
    verdict: str                       # 어미 없는 한 줄
    counted: tuple[Counted, ...]
    ground: Ground
    scene: Optional[Scene] = None
    asked: float = 0.0                 # 물으신 자리에 걸리나 0~1
    pop: Optional[float] = None        # 인구에서 몇 명 (희소도)
    needs: str = "free"                # 어느 등급에서 여나
    body: str = ""                     # 펴는 글. 비면 render 가 꼴로 짓습니다
    #: 이 컷의 **박자**. `render.RHYTHM` 이 답니다. 같은 박자가 잇달으면
    #: `Page.check` 이 거부합니다.
    rhythm: str = ""

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ClaimError("모르는 갈래: %r" % self.kind)
        if not self.axis.strip():
            raise ClaimError("축이 없소 — 축이 없으면 겹침을 못 셉니다")
        v = self.verdict.strip()
        if not v:
            raise ClaimError("주장이 비었소")
        if v.endswith((".", "!", "?", "…")):
            raise ClaimError("주장에 마침표를 달지 마시오: %r — 표지판이오" % v)
        if _ENDING.search(v):
            raise ClaimError(
                "주장에 어미를 달지 마시오: %r — 표지판은 voice 층을 안 타므로 "
                "스무 명이 전부 하오체로 그 한 줄을 말합니다. "
                "꼴은 「…하는 자리」 요" % v)
        if not self.counted:
            raise ClaimError(
                "센 값이 없소: %r — 틀릴 수 없는 말은 어떤 관찰에서도 "
                "살아남아 '소름 돋는다' 가 안 나옵니다" % v)
        if self.kind == "ledger" and self.asked:
            raise ClaimError("명식은 무엇을 물었든 같은 여덟 글자요 — "
                             "장부에 고민을 들이지 마시오")
        if self.kind == "verdict" and self.scene is None:
            raise ClaimError("판정에 살림의 장면이 없소: %r — 뜬 말로 끝납니다" % v)
        if not 0.0 <= self.asked <= 1.0:
            raise ClaimError("asked 는 0~1 이오: %r" % (self.asked,))

    # ── 근거 줄 ──
    @property
    def source(self) -> str:
        """
        컷 위에 그려지는 한 줄. **아라비아 숫자가 듭니다.**

        재보니 수가 든 근거 줄이 25%뿐이었고 100점 표에서 가장 낮은
        칸(8점)이었습니다. 세는 값은 이미 다 있었고 대기만 했습니다.
        """
        return "%s · %s — %s 〔%s〕" % (
            self.ground.본것,
            " · ".join(c.수 for c in self.counted),
            self.ground.이치,
            self.ground.출처)


# ── 처방 ─────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Prescription:
    """
    한 장에 **하나**. 둘이면 손님은 하나도 안 합니다.

    재보니 한 장에 시키는 일이 **44개**였습니다.
    """
    한가지: str        # 오늘 끝낼 하나
    확인: str          # 밤에 무엇을 보면 됐는지 아는가
    갈림: str          # 상황이 다르면 어디서 갈리나
    축: str            # 어느 셈에서 나왔나

    def __post_init__(self):
        for name in ("한가지", "확인", "갈림", "축"):
            if not str(getattr(self, name)).strip():
                raise ClaimError("처방의 %s 가 비었소" % name)
        n = len(re.findall(r"(?:시오|십시오|하세요)", self.한가지))
        if n != 1:
            raise ClaimError("오늘 할 일은 하나요 — 시키는 말이 %d개: %r"
                             % (n, self.한가지))
        # ★ 확인·갈림은 **시키는 말이 아닙니다** (2026-09-28).
        #
        #   재보니 한 장에 시키는 일이 44개였습니다. 처방을 하나로 줄여
        #   놓고도 그 안에 「…확인하시오」 「…정하시오」 를 더 달면 셋이
        #   되오. 둘이면 손님은 하나도 안 합니다.
        for name in ("확인", "갈림"):
            if re.search(r"(?:시오|십시오|하세요)", str(getattr(self, name))):
                raise ClaimError(
                    "%s 에 시키는 말을 달지 마시오: %r — 오늘 할 일은 "
                    "한가지 한 칸뿐이오" % (name, getattr(self, name)))


# ── 예산 ─────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Budget:
    """
    한 장의 분량을 **규칙으로** 못박습니다.

    넘치면 자르는 것이 아니라 **고릅니다** — 물으신 자리에 걸리는
    것부터. 분량이 규칙이 아니면 표를 하나 더 붙이는 것이 늘 이깁니다.
    """
    cuts: int
    chars: int
    hedges: int = 2         # 면책 — 지금 여섯입니다
    offers: int = 1         # 파는 말 — 지금 여덟 번입니다
    figures: int = 2        # 비유. 둘을 나란히 붙이면 둘 다 흘립니다
    #: ★ 컷마다 **댈 수 있는 값이 든 문장**의 최소 몫 (2026-09-28).
    #:
    #:   지금 한 장 전체가 15.8%입니다. 열다섯 문장에 둘인 컷이 있었습니다.
    #:
    #:   ★ **갈래마다 다릅니다.** 위로를 반증가능하게 만들라는 것은 잘못된
    #:     잣대요 — 위로는 셈에 **닻을 내리면** 됩니다(그래서 `counted` 가
    #:     필수요). 판정은 이 집이 파는 것이라 대부분 댈 수 있어야 하고,
    #:     장부는 셈 그 자체라 거의 전부요.
    #:
    #:     문턱을 갈래로 두지 않고 한 값으로 두면, 통과시키려고 위로 컷에
    #:     수를 억지로 박게 됩니다 — 그건 자를 글에 맞추는 것이오.
    fact_floor: float = 0.5
    #: ★ 「뒤집기」 갈래를 따로 둔 까닭 (2026-09-28)
    #:
    #:   강점 셋과 그 그늘 셋은 **본디 셀 수 없는 줄**입니다 — 「급할 때
    #:   앞에 서는 힘」 은 만세력을 펴고 맞춰 볼 수가 없소. 그런데 이
    #:   짝은 이 집이 「칭찬만 하지 않는」 자리로 쓰는 장치이고, 국내
    #:   후기에서 「좋은 이야기만 써 준다」 가 약점으로 적히는 그 자리를
    #:   막습니다.
    #:
    #:   그래서 판정 문턱(0.6)을 그대로 대면 이 컷은 영영 못 섭니다.
    #:   대신 **짝마다 그 짝이 나온 셈을 대게** 하고(`render._shadow`)
    #:   문턱은 그 몫에 맞춥니다. 위로를 반증가능하게 만들라는 것이
    #:   잘못된 잣대인 것과 같은 자리요.
    floors: tuple = (("ledger", 0.8), ("verdict", 0.6), ("depth", 0.5),
                     ("solace", 0.34), ("hope", 0.34), ("pair", 0.3))

    def floor_of(self, kind: str) -> float:
        return dict(self.floors).get(kind, self.fact_floor)
    #: ★ 첫 컷의 **첫 세 문장**에 들어야 할 센 값의 최소 개수.
    #:   재보니 첫 300자에 0~1개였고 스무 명 가운데 열 명이 0개였습니다.
    #:   손님이 「내 얘기다」 할 재료가 첫 화면에 없었다는 말이오.
    open_facts: int = 3
    #: ★ 같은 리듬이 잇달아 몇 컷까지. 컷 144개의 갈래 조합이 22가지뿐이고
    #:   상위 다섯이 80컷이었습니다 — 셋째 컷부터 손님은 훑습니다.
    same_rhythm: int = 2

    @staticmethod
    def of(tier: str) -> "Budget":
        return {
            "free":  Budget(cuts=9,  chars=5000),
            "9900":  Budget(cuts=14, chars=7500),
            "12900": Budget(cuts=17, chars=9000),
            "15900": Budget(cuts=20, chars=10500),
            "19900": Budget(cuts=23, chars=12000),
        }[tier]


# ── 한 장 ────────────────────────────────────────────────────────
@dataclass
class Page:
    """
    한 장의 **주인**. 여태 이 자리가 없었습니다.

    서버는 컷을 내려보내고 화면이 한 장을 짰습니다 —
    `FREE_DETAIL_IDS` 가 `components/FreeReadingDetail.tsx` 에 있어
    서버는 자기가 무엇을 두 번 내보내는지 몰랐습니다. `spine` 이 본문과
    근거 줄까지 두 번 나간 까닭이 그것입니다.
    """
    thesis: str                        # 한 장의 주장 하나 (어미 없음)
    claims: list = field(default_factory=list)
    prescription: Optional[Prescription] = None
    budget: Budget = field(default_factory=lambda: Budget.of("free"))
    offer_at: Optional[str] = None      # 파는 말을 놓는 **한 곳** (축 이름)
    #: 손님이 준 입력으로 우리가 무엇을 했는가 — **첫머리 한 줄**.
    derived: Optional[Derived] = None
    #: ★ 명식·계산 근거는 **접는 부록**입니다 (2026-09-28).
    #:
    #:   여태 본문 안에 있었고, 그래서 손님이 「오늘 할 일」을 읽고 나서
    #:   다시 진단을 읽었습니다. 영수증은 펴서 볼 사람만 폅니다 —
    #:   근거는 컷마다 한 줄(`source`)로 이미 붙습니다.
    appendix: list = field(default_factory=list)

    def check(self) -> None:
        """어긴 채로는 내려보내지 않습니다."""
        if _ENDING.search(self.thesis.strip()):
            raise ClaimError("한 장의 주장에 어미를 달지 마시오: %r" % self.thesis)
        seen = {}
        for c in list(self.claims) + list(self.appendix):
            if c.axis in seen:
                raise ClaimError(
                    "같은 축이 두 번 나오오: %r — 한 주장을 다섯 자리에서 "
                    "말하던 그 자리요" % c.axis)
            seen[c.axis] = c
        if len(self.claims) > self.budget.cuts:
            raise ClaimError("컷이 예산을 넘소: %d > %d"
                             % (len(self.claims), self.budget.cuts))
        if self.prescription is None:
            raise ClaimError("오늘 할 하나가 없소")
        if self.offer_at and self.offer_at not in seen:
            raise ClaimError("파는 말을 없는 축에 놓았소: %r" % self.offer_at)

        # ── 날카로움: 컷마다 댈 수 있는 값이 들어야 하오 ──
        #
        # ★ 어긴 것을 **모두 모아** 한 번에 냅니다 (2026-09-28). 하나씩
        #   내면 고치는 사람이 컷 수만큼 돌려야 합니다 — 열 번 돌린 뒤에
        #   알았습니다.
        soft = []
        for c in self.claims:
            if not c.body:
                continue
            r, floor = fact_ratio(c.body), self.budget.floor_of(c.kind)
            if r < floor:
                soft.append("%s(%s) %.0f%% < %.0f%%"
                            % (c.axis, c.kind, r * 100, floor * 100))
        if soft:
            raise ClaimError(
                "댈 값이 모자란 컷 %d개 — %s. 틀릴 수 없는 말은 어떤 "
                "관찰에서도 살아남아 '소름 돋는다' 가 안 나옵니다"
                % (len(soft), " · ".join(soft)))

        # ── 도출 명시: 첫머리에 **무엇에서 나왔는지** ──
        #
        #   재보니 첫 300자의 반증가능성 0 글자가 64.4%였고, 여섯 고민이
        #   **100%** 글자 그대로 같았습니다. 가장 값진 자리를 남에게
        #   쓰고 있었다는 말이오.
        if self.derived is None:
            raise ClaimError(
                "첫머리에 도출 명시가 없소 — 손님이 적은 값으로 무엇을 "
                "했는지 말하지 않으면, 분 단위로 받아 놓고도 「대체로 맞는 말」 "
                "과 같은 자리에 섭니다 (Snyder 1974: 3.24 → 4.38)")

        # ── 첫 화면: 가장 값진 자리를 남에게 쓰지 마시오 ──
        if self.claims:
            head = sentences(self.claims[0].body)[:3]
            n = sum(len(FACT.findall(s)) for s in head)
            if n < self.budget.open_facts:
                raise ClaimError(
                    "첫 컷의 첫 세 문장에 센 값이 %d개뿐이오 (적어도 %d개). "
                    "손님이 가장 먼저 읽는 자리요 — 여기서 못 대면 "
                    "그 뒤 글은 다 떠보는 말로 읽힙니다"
                    % (n, self.budget.open_facts))

        # ── 리듬: 같은 박자를 잇달아 두지 마시오 ──
        run, prev = 1, None
        for c in self.claims:
            if c.rhythm and c.rhythm == prev:
                run += 1
                if run > self.budget.same_rhythm:
                    raise ClaimError(
                        "같은 리듬이 %d컷 잇달았소: %r — 손님은 셋째 컷부터 "
                        "읽는 게 아니라 훑습니다" % (run, c.rhythm))
            else:
                run, prev = 1, c.rhythm

    @property
    def chars(self) -> int:
        return sum(len(c.body) for c in self.claims)
