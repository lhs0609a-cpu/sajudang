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
def _seg(stage, label, source, body, question, yes, no, sid, show_source=True):
    return {
        "stage": stage,
        "label": label,
        "source": source if show_source else None,
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


def build_hook(f, concern: str, axis4: Optional[str] = None,
               name: str = "", you: str = "그대") -> list:
    """
    훅 5단을 조합한다.

    f       : engine.features.Features
    concern : money / work / love / people / dir / health
    axis4   : 성향 4글자 (선택). 없으면 2.5단을 넣지 않는다.
    name    : 사용자가 적은 이름 (선택)
    you     : 캐릭터별 호칭 — 그대 / 자네 / 아저씨

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
        stage="0", label="", show_source=False,
        source="%s일간 · %s %s · %s" % (f.day_gan, element_word(weak),
                                       f.elements[weak], top),
        body='<div class="stab">%s<p>%s</p><p class="sub">%s</p>'
             '<p class="gan">%s</p></div>'
             % (head, stab, stab2, gan_line),
        question="…맞소?",
        yes="그럴 줄 알았소. 어떻게 아느냐 하면—",
        no="그럼 다행이오. 헌데 이건 어떻소.",
        sid="stab:%s:%s:%s" % (concern, weak, f.day_gan)))

    # ── 1단 · 부정확인 ──────────────────────────────────
    m1 = _pick("MYTH_TG", top, concern)
    m2 = _pick("MYTH_ST", strength, concern)
    truth = _pick("PATT", top, "b")
    segs.append(_seg(
        stage="1", label="1 · 먼저, 아닌 것부터",
        source="%s %d · %s %d" % (top, f.ten_gods[top], strength,
                                  f.strength_score),
        body=('<p class="neg">사람들이 %s를 두고 <span class="strk">%s</span>고 하지. '
              '아니오.<br><span class="strk d2">%s</span>는 말도 틀렸소.<br><br>'
              '<b>%s는 사람일 뿐이오.</b></p>')
             % (esc_you, m1, m2, truth),
        question="이 말은 어떻소?",
        yes="그럴 줄 알았소. 그럼 순서를 짚어드리리다.",
        no="괜찮소. 진짜는 다음이오.",
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
    segs.append(_seg(
        stage="2", label="2 · 순서",
        source="%s %d · %s일간 → %s %s(%s) · %s %s · %s생"
               % (top, f.ten_gods[top], ELEMENT_OF_GAN[f.day_gan],
                  f.flow_el, f.elements[f.flow_el], flow,
                  weak, f.elements[weak], sea),
        body=('<div class="scene"><p class="sea">%s</p>'
              '<p>%s는 늘 이 순서요.</p><div class="seq">%s</div>%s</div>'
              % (sea_line, esc_you,
                 "".join('<div><span>%s</span></div>' % s for s in seq),
                 "".join('<p class="%s">%s</p>' % ("hit" if i == 1 else "", l)
                         for i, l in enumerate(lines)))),
        question="…이 순서가 맞소?",
        yes="그럴 줄 알았소. 그럼 이름을 붙여드리리다.",
        no="아직 이르오. 이름을 붙여보면 알 것이오.",
        sid="seq:%s:%s:%s:%s:%s:%s" % (top, concern, flow, weak, strength, sea)))

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
            no = "그럼 잘 맞춰 사신 것이오."
        segs.append(_seg(
            stage="2.5", label=label,
            source="사주 %s ↔ 입력 %s" % (axis_string(f), _html.escape(axis4.upper())),
            body=axis_block(cmp, strength),
            question=q, yes=yes, no=no,
            sid=axis_sid(cmp, strength)))

    # ── 3단 · 이름 ──────────────────────────────────────
    word = bank()["NAME2"].get(weak, {}).get(flow) or bank()["NAMEW"][weak]
    # ★ 이름은 이 사람이 가장 오래 기억하는 한 줄입니다. 캡처를 나란히
    #   놓았을 때 제일 먼저 눈에 띄는 자리라 신강약(3) 을 곱해 둡니다.
    post = ("이건 성격이 아니오. %s일간의 힘이 %s(%s)으로 <b>%s</b> 하는데, "
            "%s %s밖에 없어 멈출 자리가 없는 <b>구조</b>요. %s"
            % (ELEMENT_OF_GAN[f.day_gan], element_word(f.flow_el),
               f.elements[f.flow_el], flow,
               josa(element_word(weak), "이", "가"), f.elements[weak],
               bank()["NAME_POST"][strength]))
    segs.append(_seg(
        stage="3", label="3 · 이름",
        source="%s %s × %s" % (element_word(weak), f.elements[weak], flow),
        body=('<div class="nameB"><p class="pre">오래 느꼈는데 말로는 못 했던 것.<br>'
              '그건 이름이 있소.</p><p class="word">%s</p><p class="post">%s</p></div>'
              % (word, post)),
        question="이제 알겠소?",
        yes="그렇소. 여기까지가 값 없이 하는 얘기요.",
        no="천천히 생각해보시오.",
        sid="name:%s:%s:%s" % (weak, flow, strength)))

    return segs


def tea(f) -> dict:
    """용신별 다과상. 리포트·무료 구간에서 씀."""
    t = bank()["TEA"][f.yongsin]
    return {"element": f.yongsin, "name": t["n"], "text": t["d"]}
