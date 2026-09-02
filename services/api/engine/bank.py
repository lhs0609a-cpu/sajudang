"""
문장 뱅크 조합 — 훅 5단. docs/06_콘텐츠_문장뱅크.md §0

★ seed/bank.json 은 서버 전용입니다. 클라이언트 번들에 넣지 마세요.
  API 는 **렌더된 HTML 만** 내려보냅니다. (docs/02 §7)

산출식
    0   찌르기   STAB[고민][약오행] + STAB2[주도십신]
    1   부정확인 MYTH_TG[주도십신][고민] + MYTH_ST[신강약][고민] + PATT[주도십신].b
    2   순서     IGNITE[주도십신][고민] → FLOW[흐름] → RESULT[약오행] → BLAME[주도십신][신강약]
    2.5 어긋남   사주4축 vs 입력4글자 → GAP[from→to]   (불일치가 있을 때만)
    3   이름     NAME2[약오행][흐름]

statement_id
    `{stage}:{key1}:{key2}...` — 응답 기록(hit율)의 단위.
    쓰인 키를 전부 넣습니다. 집계는 접두사로 묶으면 되고, 반대로
    뭉뚱그려 기록해 두면 나중에 쪼갤 수 없습니다.
"""
from __future__ import annotations

import html as _html
import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from . import guard
from . import terms
from . import why as _why
from .constants import ELEMENT_OF_GAN

SEED = Path(__file__).resolve().parents[3] / "seed"

AXES = [("EI", 0), ("SN", 1), ("TF", 2), ("JP", 3)]
AXIS_NAME = {"E": "드러나는", "I": "안으로 도는", "S": "현실을 딛는",
             "N": "가능성을 보는", "T": "판단으로 가는", "F": "마음으로 가는",
             "J": "정해두는", "P": "열어두는"}


@lru_cache(maxsize=1)
def bank() -> dict:
    return json.loads((SEED / "bank.json").read_text("utf-8"))


@lru_cache(maxsize=1)
def meta() -> dict:
    return json.loads((SEED / "meta.json").read_text("utf-8"))


def element_word(el: str) -> str:
    """목 → 나무"""
    return meta()["elements"].get(el, el)


def concern_word(concern: str) -> str:
    return meta()["concerns"].get(concern, concern)


def has_batchim(word: str) -> bool:
    """마지막 글자에 받침이 있는가. 조사 선택용."""
    if not word:
        return False
    code = ord(word[-1])
    if 0xAC00 <= code <= 0xD7A3:
        return (code - 0xAC00) % 28 != 0
    return False


def amount_word(v: float) -> str:
    """
    오행의 세기를 사람 말로.

    ★ `f.elements` 는 **안에서 쓰는 점수**입니다 (0.3 · 1.2 · 4.0).
      가중치를 매겨 더한 값이라 사람이 읽을 수 있는 수가 아닙니다.
      그런데 근거 줄에 「불 0.2」 처럼 그대로 나가고 있었습니다.

      근거는 보이되 규칙은 감춥니다 (CLAUDE.md). 손님이 알아야 할 것은
      「불이 옅다」이지 0.2 가 아닙니다. 0.2 를 보면 1.0 은 뭔지, 몇부터
      많은 건지 묻게 되는데 그건 우리 분기표입니다.
    """
    if v < 0.5:
        return "거의 없음"
    if v < 1.2:
        return "옅음"
    if v < 2.2:
        return "보통"
    if v < 3.2:
        return "짙음"
    return "아주 짙음"


def amount_adj(v: float) -> str:
    """
    같은 세기를 **문장 안에서 쓸 꼴**로.

    ★ 딱지 자리와 문장 자리는 말꼴이 다릅니다.

      근거 줄에는 「나무 거의 없음」 이 맞지만, 문장에 그대로 끼우면
      「물이 아주 짙음인 게 아니오」 가 되어 사람 말이 아닙니다.
      뜻은 같고 꼴만 다릅니다 — 문턱은 amount_word 와 한 벌입니다.
    """
    return {"거의 없음": "거의 없는", "옅음": "옅은", "보통": "어슷한",
            "짙음": "짙은", "아주 짙음": "아주 짙은"}[amount_word(v)]


def count_word(n: int) -> str:
    """
    개수는 **셀 수 있는 사실**이라 냅니다. 다만 표가 아니라 말로.

    「상관 2」는 분기표처럼 보이고 「상관이 둘」은 근거로 읽힙니다.
    같은 것을 말하는데 하나는 기계가 하는 말이고 하나는 사람이 하는
    말입니다.
    """
    words = ("없음", "하나", "둘", "셋", "넷", "다섯")
    return words[n] if 0 <= n < len(words) else "여섯 넘게"


def josa(word: str, with_batchim: str, without: str) -> str:
    """`josa("나무", "이", "가")` → "나무가"."""
    return word + (with_batchim if has_batchim(word) else without)


def josa_hanja(hanja: str, with_batchim: str, without: str) -> str:
    """
    한자 뒤의 조사. **읽는 소리**로 고릅니다 — `申` 는 '신' 이라 `申이`,
    `午` 는 '오' 라 `午가` 입니다. 글자로는 알 수 없습니다.
    소리를 모르는 글자면 받침 없는 쪽으로 둡니다.
    """
    from .constants import GAN_SOUND, JI_SOUND
    sound = JI_SOUND.get(hanja) or GAN_SOUND.get(hanja)
    if not sound:
        return hanja + without
    return hanja + (with_batchim if has_batchim(sound) else without)


class BankError(KeyError):
    """뱅크에 없는 조합. 지어내지 않고 터뜨린다."""


def _pick(table: str, *keys: str) -> str:
    node = bank()[table]
    for k in keys:
        if not isinstance(node, dict) or k not in node:
            raise BankError("bank.%s[%s] 없음" % (table, "][".join(keys)))
        node = node[k]
    return node


# ══════════════════════════════════════════════════════════
# 성향 4글자 ↔ 사주 4축
# ══════════════════════════════════════════════════════════
def saju_axis(f) -> dict:
    """
    사주에서 4축을 추정한다. 검사 결과가 아니라 **여덟 글자에서 나온 값**이다.

    ※ "MBTI" 는 등록상표 — 화면 표기는 "성향 4글자". (docs/11)
    """
    g = f.ten_gods
    out = g["비견"] + g["겁재"] + g["식신"] + g["상관"]      # 밖으로 도는 힘
    inn = g["정인"] + g["편인"] + g["정관"] + g["편관"]      # 안으로 도는 힘
    real = g["정재"] + g["편재"] + g["정관"] + g["편관"]     # 현실·규칙
    idea = g["편인"] + g["상관"] + g["편재"]                # 발상·확장
    logic = g["정관"] + g["편관"] + g["정재"] + g["편재"]    # 판단·통제
    feel = g["식신"] + g["상관"] + g["정인"]                # 정서·표현
    plan = g["정관"] + g["정재"] + g["정인"]                # 계획·정리
    flex = g["상관"] + g["편재"] + g["겁재"]                # 즉흥·전환
    st = 2 if f.strength == "신강" else (-2 if f.strength == "신약" else 0)
    return {
        "EI": "E" if out + st >= inn else "I",
        "SN": "S" if real >= idea else "N",
        "TF": "T" if logic >= feel else "F",
        "JP": "J" if plan >= flex else "P",
        "raw": {"out": out + st, "inn": inn, "real": real, "idea": idea,
                "logic": logic, "feel": feel, "plan": plan, "flex": flex},
    }


def axis_string(f) -> str:
    a = saju_axis(f)
    return "".join(a[k] for k, _ in AXES)


def gap_list(f, axis4: Optional[str]) -> list:
    """
    사주 4축과 입력 4글자가 어긋난 자리.
    axis4 가 없거나 형식이 틀리면 빈 목록.
    """
    return axis_compare(f, axis4)["gaps"]


# ══════════════════════════════════════════════════════════
# 겹친 자리와 어긋난 자리
# ══════════════════════════════════════════════════════════
#
# ★ 왜 겹친 자리를 먼저 말하는가
#
#   전에는 어긋난 자리만 말했고, 94%가 '어긋남' 을 깊게 파는 쪽으로
#   갔습니다. 처음에는 축 설계가 틀렸다고 봤습니다 — `saju_axis` 가
#   항 개수가 다른 합을 비교하니 한쪽이 구조적으로 이긴다고요.
#
#   바깥을 찾아보니 진단이 뒤집혔습니다. 한국에는 정반대인 두 분포가
#   있습니다. 정식 MBTI 한국 대표표본(n=19,070)은 S·T·J 편중이고,
#   무료 16Personalities(n=70,266)는 I·N·F·P 편중입니다. "MBTI 뭐야?"
#   에 답하는 사람은 거의 전부 후자를 말합니다. 정식 기준으로는 우리
#   축이 오히려 잘 맞습니다. **틀린 건 축이 아니라 기준이었습니다.**
#
#   그래서 백분위 보정을 실제로 구현해 돌려봤습니다. 2.5단을 깊게 파는
#   비율이 94.4% → 92.5%. 거의 안 움직입니다. 이진 축 넷이면 넷이 다
#   맞을 확률이 잘해야 6%라, **계산으로 될 일이 아니었습니다.**
#
#   말하는 방식의 문제였습니다. 겹친 자리를 먼저 말하고, 깊은 해석은
#   셋 이상 어긋난 사람에게만 보냅니다.
#
# ★ 덤 — 입력값 자체가 흔들립니다.
#   MBTI 는 5주 뒤 재검사에서 39~76%가 다른 유형이 나옵니다. 이건
#   제품 서사에 오히려 맞습니다: "여덟 자는 안 바뀌오. 그대가 적은
#   넉 자는 지난달과 다를 수 있소."

GAP_DEEP_AT = 3      # 이만큼 어긋난 사람에게만 깊이 들어간다 (약 36%)


def axis_compare(f, axis4: Optional[str]) -> dict:
    """
    사주 4축 ↔ 입력 4글자.

        matches  겹친 자리 [{axis, letter, t}]
        gaps     어긋난 자리 [{axis, from, to, pair, t, w}]
        deep     깊은 해석(w)을 붙일 것인가
        usable   비교할 수 있는 입력이었는가
    """
    empty = {"matches": [], "gaps": [], "deep": False, "usable": False}
    if not axis4 or len(axis4) != 4:
        return empty
    axis4 = axis4.upper()
    a = saju_axis(f)
    B = bank()
    matches, gaps = [], []
    for key, i in AXES:
        ch = axis4[i]
        if ch not in key:                # 형식이 이상하면 그 축은 건너뛴다
            continue
        if a[key] == ch:
            matches.append({"axis": key, "letter": ch,
                            "t": B["MATCH"][ch]})
        else:
            pair = "%s→%s" % (a[key], ch)
            g = B["GAP"].get(pair)
            if g:
                gaps.append({"axis": key, "from": a[key], "to": ch,
                             "pair": pair, "t": g["t"], "w": g["w"]})
    if not matches and not gaps:
        return empty
    return {"matches": matches, "gaps": gaps,
            "deep": len(gaps) >= GAP_DEEP_AT, "usable": True}


def axis_block(cmp: dict, strength: Optional[str] = None,
               cls: str = "gap") -> str:
    """겹친 자리 → 어긋난 자리 순서로 한 덩어리. 훅과 리포트가 같이 씁니다."""
    n = len(cmp["matches"])
    parts = ['<p class="lead">%s</p>' % bank()["MATCH_LEAD"][str(n)]]
    for m in cmp["matches"]:
        parts.append('<p class="mt"><b>%s</b> %s</p>' % (m["letter"], m["t"]))
    for g in cmp["gaps"]:
        deep = ('<br><span class="w">%s</span>' % g["w"]) if cmp["deep"] else ""
        parts.append('<p class="gp"><b>%s → %s</b><br>%s%s</p>'
                     % (g["from"], g["to"], g["t"], deep))
    if strength:                      # 신강약(3) 을 곱해 쏠림을 줄인다
        parts.append('<p class="tl">%s</p>' % bank()["MATCH_TAIL"][strength])
    return '<div class="scene %s">%s</div>' % (cls, "".join(parts))


def axis_sid(cmp: dict, strength: Optional[str] = None) -> str:
    """이 단의 statement_id. 겹친 자리와 어긋난 자리를 둘 다 담습니다."""
    return "axis:%d:%s:%s%s" % (
        len(cmp["matches"]),
        "".join(m["letter"] for m in cmp["matches"]) or "-",
        ",".join(g["pair"] for g in cmp["gaps"]) or "-",
        (":" + strength) if strength else "")


# ══════════════════════════════════════════════════════════
# 훅 5단
# ══════════════════════════════════════════════════════════
def _seg(stage, label, source, body, question, yes, no, sid,
         show_source=True, source_below=False):
    """
    source_below — 근거를 본문 **아래**에 두라는 표시.

    ★ 0단이 근거 없이 나가고 있었습니다.
      `show_source=False` 라 손님이 이 집에서 처음 읽는 문장이 하필
      근거가 없는 문장이었습니다. "근거 대는 집" 이라는 자리가 가장 센
      첫 문장에서 사라진 것입니다. 게다가 화면이 공감률을 `source` 가
      있을 때만 그려서, **0단은 응답이 쌓여도 영영 공감률이 안 붙었습니다.**

      그렇다고 근거를 첫 문장 **위**에 놓으면 찌르기가 무뎌집니다.
      그래서 자리만 옮깁니다 — 찌르고, 그 아래에 무엇을 보고 한 말인지
      적습니다.
    """
    return {
        "stage": stage,
        "label": label,
        "source": source if show_source else None,
        "source_below": bool(source_below),
        "html": guard.enforce(body, {"stage": stage, "statement_id": sid}),
        "question": question,
        "yes": yes,
        "no": no,
        "statement_id": sid,
    }


# 월지 → 계절. 절기 기준입니다 — 寅卯辰 이 봄입니다.
# (양력 달이 아닙니다. 입춘에 해가 바뀌는 것과 같은 이치입니다.)
SEASON_OF_JI = {
    "寅": "봄", "卯": "봄", "辰": "봄",
    "巳": "여름", "午": "여름", "未": "여름",
    "申": "가을", "酉": "가을", "戌": "가을",
    "亥": "겨울", "子": "겨울", "丑": "겨울",
}


def born_season(f) -> str:
    """태어난 달의 기운. 월지에서 봅니다."""
    return SEASON_OF_JI[f.pillars[1]["ji"]]


# ══════════════════════════════════════════════════════════
# 물은 자리 ↔ 글자가 센 자리
# ══════════════════════════════════════════════════════════
#
# ★ 이건 계산이 아니라 유파 선택입니다. 표는 seed/bank.json 의
#   CONCERN_AXIS 한 곳에 있습니다. 사랑은 남녀가 갈립니다 —
#   남자는 재성, 여자는 관성으로 보는 것이 통설입니다.
GROUP_TOTAL = {"비겁": "bi", "식상": "sik", "재성": "jae",
               "관성": "gwan", "인성": "inn"}


def concern_group(concern: str, sex: str) -> str:
    """이 고민을 여덟 글자의 어느 자리에서 보는가."""
    row = bank()["CONCERN_AXIS"][concern]
    if sex == "F" and row.get("gF"):
        return row["gF"]
    return row["g"]


def _concern_axis_seg(f, concern: str, esc_you: str) -> dict:
    """넉 자가 없을 때의 2.5단. 손님이 낸 것(고민)과 글자를 맞붙인다."""
    B = bank()
    row = B["CONCERN_AXIS"][concern]
    grp = concern_group(concern, f.sex)
    word = row["w"]
    asked = getattr(f, GROUP_TOTAL[grp])      # 물은 자리의 개수
    loud = f.flow                              # 글자가 가장 센 자리
    same = grp == loud

    lead = ('<p class="ask">%s <b>%s</b>이 걸려 오셨소. '
            '%s 여덟 글자에서 <b>%s</b>으로 보오 — %s <b>%s</b>이오.</p>'
            % (josa(esc_you, "은", "는"), word,
               josa(word, "은", "는"), grp,
               josa("%s %s" % (esc_you, grp), "은", "는"), asked))

    if asked == 0:
        body = lead + '<p class="hit">%s</p>' % (B["CONCERN_EMPTY"] % grp)
        q, yes, no = ("…짚이오?",
                      "그럴 게요. 없는 자리는 애써도 안 늘어나오 — 빌려 쓰는 법을 봐야 하오.",
                      "그럼 다른 데서 메우고 계신 게요. 그것도 공짜는 아니오.")
    elif same:
        body = lead + '<p class="hit">%s</p>' % B["CONCERN_SAME"][grp]
        q, yes, no = ("…그렇소?",
                      "그럴 게요. 가장 센 자리가 가장 안 보이는 법이오.",
                      "그럼 아직 안 터진 게요. 센 자리는 늦게 터지오.")
    else:
        body = (lead
                + '<p class="hit">헌데 %s</p>' % B["CONCERN_ELSE"][loud]
                + '<p class="tale">%s</p>' % B["WHY_TAIL"][loud])
        q, yes, no = ("…물으신 자리가 거기가 맞소?",
                      "그럴 게요. 물음은 %s에서 났는데 걸린 데는 딴 자리요." % word,
                      "그럼 물으신 자리가 맞소. 그건 그것대로 보겠소.")

    return _seg(
        stage="2.5", label="2.5 · 물은 자리와 센 자리",
        source=_why.line(
            "%s → %s %s · 가장 센 자리 %s"
            % (word, josa(grp, "이", "가"), count_word(asked), loud),
            grp, "십신"),
        body='<div class="cax">%s</div>' % body,
        question=q, yes=yes, no=no,
        sid="cax:%s:%s:%s:%s" % (concern, grp, min(asked, 4), loud))


# 몇 번 「아니오」가 쌓이면 방향을 트는가.
#
# ★ 여기가 비어 있었습니다.
#   손님의 응답이 **즉답 한 줄만** 바꾸고, 다음 단의 본문은 응답과
#   무관하게 똑같이 나왔습니다. 세 번 아니라 해도 도령이 한 번도
#   방향을 안 틀었습니다 — 그 순간 손님은 이게 녹음이라는 걸 압니다.
#
#   콜드리딩이 세다고 하는 대목은 문장이 아니라 **고쳐 나가는 행위**
#   자체입니다. 그래서 두 번 어긋나면 짚는 자리를 바꿉니다.
#
# ★ 다만 없는 문장을 지어내지는 않습니다.
#   2단의 불붙는 자리(IGNITE)는 **십신 × 고민** 축입니다. 그걸 접고
#   이미 있는 **계절 · 일간** 축(STAB_SEASON · STAB_GAN)으로 갈아
#   끼웁니다. 순서 세 줄은 흐름·약오행 축이라 그대로 둡니다 —
#   손님이 아니라고 한 것은 십신 쪽이지 흐름 쪽이 아닙니다.
TURN_AT = 2


def build_hook(f, concern: str, axis4: Optional[str] = None,
               name: str = "", you: str = "그대", misses: int = 0) -> list:
    """
    훅 5단을 조합한다.

    f       : engine.features.Features
    concern : money / work / love / people / dir / health
    axis4   : 성향 4글자 (선택). 없으면 2.5단 자리에 대체 단이 들어간다.
    name    : 사용자가 적은 이름 (선택)
    you     : 캐릭터별 호칭 — 그대 / 자네 / 아저씨
    misses  : 여기까지 「아니오」가 몇 번 나왔는가. TURN_AT 이상이면
              2단이 십신 축을 접고 계절·일간 축으로 다시 짚는다.

    ★ 공감률(“몇 명 중 몇 %”)은 여기서 만들지 않습니다.
      실응답 100건 이상 쌓인 문장만 화면에 노출합니다. (CLAUDE.md 절대 규칙 2)
    """
    if concern not in meta()["concerns"]:
        raise BankError("모르는 고민 축: %r" % (concern,))

    top = f.top_ten_god
    weak = f.weak_el
    flow = f.flow
    strength = f.strength
    esc_name = _html.escape(name.strip()) if name else ""
    esc_you = _html.escape(you)

    segs = []

    # ── 0단 · 찌르기 ────────────────────────────────────
    stab = _pick("STAB", concern, weak)
    stab2 = _pick("STAB2", top)
    # ★ 일간 한 줄. 여기가 그 사람의 '나' 자리입니다.
    #   전에는 근거 줄에만 적히고 본문에서는 안 썼습니다 — 첫 화면에서
    #   일간이 다른 사람이 같은 말을 듣고 있었습니다.
    gan_line = _pick("STAB_GAN", f.day_gan)
    head = ('<p class="hi">%s.</p>' % esc_name) if esc_name else ""
    segs.append(_seg(
        stage="0", label="",
        # 근거를 답니다. 다만 찌르기 **아래**에 답니다 — 위에 놓으면
        # 첫 문장이 강의가 되고, 안 놓으면 여느 점집과 같아집니다.
        show_source=True, source_below=True,
        source=_why.line(
            "%s일간 · %s %s · %s"
            % (f.day_gan, josa(element_word(weak), "이", "가"),
               amount_word(f.elements[weak]), top),
            top, "십신"),
        body='<div class="stab">%s<p>%s</p><p class="sub">%s</p>'
             '<p class="gan">%s</p></div>'
             % (head, stab, stab2, gan_line),
        question="…맞소?",
        yes="그럴 줄 알았소. 어떻게 아느냐 하면—",
        no="아니라 하시니 그건 접겠소. 헌데 이건 어떻소.",
        sid="stab:%s:%s:%s" % (concern, weak, f.day_gan)))

    # ── 1단 · 부정확인 ──────────────────────────────────
    m1 = _pick("MYTH_TG", top, concern)
    m2 = _pick("MYTH_ST", strength, concern)
    truth = _pick("PATT", top, "b")
    segs.append(_seg(
        stage="1", label="1 · 먼저, 아닌 것부터",
        # ★ 근거는 보이되 **내부 척도는 감춥니다.**
        #   여기 신강약 점수(strength_score)가 그대로 나가고 있었습니다 —
        #   '중화 16' 은 사람이 읽을 수 있는 값이 아닙니다. 관점 컷에는
        #   검사가 걸려 있었는데 훅 근거 줄에는 없었습니다.
        #   글자와 개수는 근거고, 점수는 규칙입니다.
        source=_why.line(
            "%s %s · %s"
            % (josa(top, "이", "가"), count_word(f.ten_gods[top]), strength),
            strength if strength in ("신강", "신약", "중화") else top,
            "강약" if strength in ("신강", "신약", "중화") else "십신"),
        body=('<p class="neg">사람들이 %s를 두고 <span class="strk">%s</span>고 하지. '
              '아니오.<br><span class="strk d2">%s</span>는 말도 틀렸소.<br><br>'
              '<b>%s는 사람일 뿐이오.</b></p>')
             % (esc_you, m1, m2, truth),
        question="이 말은 어떻소?",
        yes="그럴 줄 알았소. 그럼 순서를 짚어드리리다.",
        no="그 말이 나올 자리라 넣어 둔 것이오. 다음을 보시오.",
        sid="myth:%s:%s:%s" % (top, concern, strength)))

    # ── 2단 · 순서 ──────────────────────────────────────
    ig = _pick("IGNITE", top, concern)
    igkey = _pick("IGKEY", top, concern)
    fl = bank()["FLOW"][flow]
    rs = bank()["RESULT"][weak]
    bl = _pick("BLAME", top, strength)
    seq = [igkey, fl["k"], rs["k"]]
    lines = [
        "%s. 누가 시킨 것도 아닌데." % ig,
        "그러다 <b>%s</b>, %s." % (fl["t"], rs["t"]),
        "그리고 %s" % bl,
    ]
    # ★ 태어난 달의 기운 한 줄. 월지에서 봅니다.
    #   시기는 말하지 않습니다 — '언제' 는 유료 구간(대운)의 몫입니다.
    sea = born_season(f)
    sea_line = _pick("STAB_SEASON", sea)

    # ── 축을 트는 자리 ──────────────────────────────────
    #
    # 두 번 아니라 하셨으면 십신으로 짚던 것을 접습니다. 첫 줄
    # (IGNITE = 십신 × 고민) 을 계절·일간 줄로 갈아 끼우고, 무엇을
    # 접었는지 손님에게 말합니다. 감추면 그냥 다른 말이 나온 것이고,
    # 말하면 **고쳐 짚는 것**이 됩니다.
    turned = misses >= TURN_AT
    if turned:
        lines[0] = "%s 누가 시킨 것도 아닌데." % _pick("STAB_GAN", f.day_gan)
        turn_line = ('<p class="turn">두 번 아니라 하셨소. '
                     '십신으로 짚던 것을 접고 <b>태어난 달과 일간</b>으로 '
                     '다시 보겠소.</p>')
        seq = [sea, fl["k"], rs["k"]]
    else:
        turn_line = ""

    segs.append(_seg(
        stage="2", label="2 · 순서",
        source=_why.line(
            ("%s생 · %s일간 → %s %s(%s) · %s %s"
             % (sea, f.day_gan, josa(f.flow_el, "이", "가"),
                amount_word(f.elements[f.flow_el]), flow,
                josa(weak, "이", "가"), amount_word(f.elements[weak]))
             if turned else
             "%s %s · %s일간 → %s %s(%s) · %s %s · %s생"
             % (josa(top, "이", "가"), count_word(f.ten_gods[top]),
                ELEMENT_OF_GAN[f.day_gan],
                josa(f.flow_el, "이", "가"),
                amount_word(f.elements[f.flow_el]), flow,
                josa(weak, "이", "가"),
                amount_word(f.elements[weak]), sea)),
            flow, "십신"),
        body=('<div class="scene">%s<p class="sea">%s</p>'
              '<p>%s는 늘 이 순서요.</p><div class="seq">%s</div>%s</div>'
              % (turn_line, sea_line, esc_you,
                 "".join('<div><span>%s</span></div>' % s for s in seq),
                 "".join('<p class="%s">%s</p>' % ("hit" if i == 1 else "", l)
                         for i, l in enumerate(lines)))),
        question="…이 순서가 맞소?",
        yes="그럴 줄 알았소. 그럼 이름을 붙여드리리다.",
        no="순서가 틀렸다 하시니, 이름을 붙여 보고 다시 말하시오.",
        # ★ 튼 단은 **다른 문장으로 집계**됩니다. 그래야 어긋난 축을
        #   버리는 신호로 쓸 수 있습니다 (docs/18 · /v1/funnel).
        sid="seq%s:%s:%s:%s:%s:%s:%s"
            % ("@turn" if turned else "",
               top, concern, flow, weak, strength, sea)))

    # ── 2.5단 · 겹친 자리와 어긋난 자리 ──────────────────
    #
    # ★ 넉 자를 적었으면 **어긋난 데가 없어도** 이 단을 넣습니다.
    #   전에는 불일치가 있을 때만 넣었고, 그래서 넷이 다 맞는 6%에게
    #   — 가장 드문 사람에게 — 아무 말도 하지 않았습니다.
    cmp = axis_compare(f, axis4)
    if cmp["usable"]:
        gaps = cmp["gaps"]
        if not gaps:
            label, q = "2.5 · 겹친 자리", "…이게 맞소?"
            yes = "그렇겠지요. 여덟 자와 넉 자가 다 겹치는 일은 흔치 않소."
            no = "그럼 넉 자를 다시 재보시오. 다음 달에는 다른 유형이 나오기도 하오."
        else:
            label = "2.5 · 겹친 자리와 어긋난 자리"
            q = "…짚이는 데가 있소?"
            yes = ("그럴 게요. 그 사이가 그대를 가장 지치게 하오." if cmp["deep"]
                   else "그 한두 자리가 늘 걸리는 자리요.")
            no = "그럼 아직 안 부딪힌 게요. 어긋난 자리는 늦게 값을 물리오."
        segs.append(_seg(
            stage="2.5", label=label,
            source="사주 %s ↔ 입력 %s" % (axis_string(f), _html.escape(axis4.upper())),
            body=axis_block(cmp, strength),
            question=q, yes=yes, no=no,
            sid=axis_sid(cmp, strength)))
    else:
        # ── 2.5단 대체 · 물은 자리와 글자가 센 자리 ──────────
        #
        # ★ 넉 자를 안 적은 사람에게는 이 단이 통째로 빠지고 있었습니다.
        #   재보니 **16.4%** 입니다. 하필 훅에서 유일하게 **손님이 스스로
        #   낸 것과 여덟 글자를 맞붙이는** 자리라, 가장 "나에 대한 말"
        #   처럼 읽히는 대목이 조건부였습니다.
        #
        #   넉 자가 없어도 손님이 낸 것이 하나 더 있습니다 — **고민**입니다.
        #   물으러 온 자리와 글자가 센 자리를 나란히 놓습니다. 구조는
        #   위와 같습니다: 겹친 자리인가, 어긋난 자리인가.
        segs.append(_concern_axis_seg(f, concern, esc_you))

    # ── 3단 · 이름 ──────────────────────────────────────
    word = bank()["NAME2"].get(weak, {}).get(flow) or bank()["NAMEW"][weak]
    # ★ 이름은 이 사람이 가장 오래 기억하는 한 줄입니다. 캡처를 나란히
    #   놓았을 때 제일 먼저 눈에 띄는 자리라 신강약(3) 을 곱해 둡니다.
    # ★ 이 문장을 다시 썼습니다.
    #   전에는 "…흙(3.2)으로 재성 하는데" 였습니다. 두 가지가 틀렸습니다 —
    #   ① '재성 하는데' 는 비문입니다. 십신 이름에 '하다' 가 안 붙습니다.
    #   ② 이름을 건네는 **가장 뜨거운 순간에 소수점**이 나옵니다.
    #      근거는 이미 근거 줄이 대고 있으니 본문은 사람 말이라야 합니다.
    post = ("이건 성격이 아니오. <b>%s</b>일간의 힘이 <b>%s</b> 쪽으로 %s, "
            "정작 <b>%s</b> 바닥이라 <b>멈출 자리가 없는</b> 구조요. %s"
            % (ELEMENT_OF_GAN[f.day_gan], element_word(f.flow_el),
               bank()["NAME_FLOW"][flow],
               josa(element_word(weak), "이", "가"),
               bank()["NAME_POST"][strength]))
    segs.append(_seg(
        stage="3", label="3 · 이름",
        source=_why.line(
            "%s %s × %s"
            % (josa(element_word(weak), "이", "가"),
               amount_word(f.elements[weak]), flow),
            "용신", "용신"),
        body=('<div class="nameB"><p class="pre">오래 느꼈는데 말로는 못 했던 것.<br>'
              '그건 이름이 있소.</p><p class="word">%s</p><p class="post">%s</p></div>'
              % (word, post)),
        question="이제 알겠소?",
        yes="알면 됐소. 아는 것과 고치는 것은 또 다른 얘기지만.",
        no="지금 아니라 하셔도 이름은 남소. 다음에 걸릴 때 떠오를 게요.",
        sid="name:%s:%s:%s" % (weak, flow, strength)))

    # ★ 훅에서도 어려운 말을 **한 벌에 한 번** 풉니다.
    #   0단이 손님이 이 집에서 처음 읽는 글입니다. 거기서 「편관」이
    #   풀이 없이 나오면 그 순간 손님은 압도당합니다.
    seen: set = set()
    for s in segs:
        s["html"] = terms.gloss(s["html"], seen)
    return segs


def tea(f) -> dict:
    """용신별 다과상. 리포트·무료 구간에서 씀."""
    t = bank()["TEA"][f.yongsin]
    return {"element": f.yongsin, "name": t["n"], "text": t["d"]}
