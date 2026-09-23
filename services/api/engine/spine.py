# -*- coding: utf-8 -*-
"""
척추 — 이 사람을 **한 줄로** 세우는 자리.

★ 왜 생겼나 (2026-09-11)

  손님이 바깥 글 한 편을 가져왔습니다 — 「세상의 비효율과 돈의 흐름을
  발견해 구조로 만드는 사람」. 같은 명식(癸酉 癸亥 庚戌 甲申)을 우리
  엔진에 넣었더니 30컷 24,413자가 나왔고, 재료는 **거의 다** 있었습니다
  — 식상생재 · 편재격 · 관성 0 · 상관 주도 · 신강.

  그런데 식상생재가 **30컷 중 22번째에 한 줄**이었습니다. 30개 조각이
  서로를 몰라, 「그래서 나는 어떤 사람이오」 에 답하는 자리가 없었습니다.
  같은 사실(불 0)을 일곱 번 말하고, 한 글자(庚)를 세 가지로 불렀습니다.

  그 글이 좋았던 까닭은 **척추가 하나**였기 때문입니다. 한 줄을 먼저
  세우고, 모든 절이 그 한 줄을 증명하고, 강점을 뒤집어 위험을 만들었습니다.

★ 무엇으로 세우는가 — **흐름이 어디에 닿는가**

  흐름(`f.flow`)은 힘이 실제로 나가는 자리입니다. 생(生)의 고리에서
  그 다음 자리가 명식에 **있으면** 힘이 거기까지 닿고, **없으면** 거기서
  끊깁니다.

      비겁 → 식상 → 재성 → 관성 → 인성 → 비겁

  庚 일간이 물(식상)로 흐르고 그 물이 나무(재성, 시간의 甲)에 닿으면
  「만든 것이 쥘 것으로 이어진다」 — 옛 이름으로 식상생재입니다.
  이 고리는 **계산**입니다. 글자의 자리까지 짚어 냅니다(`chain`).

★ 골라 담지 않습니다

  축(흐름 다섯 × 닿음/끊김)은 미리 정했고 그 칸을 그대로 냅니다.
  가장 드문 것, 가장 그럴듯한 것을 고르지 않습니다 (희소도와 같은 규칙).

★ 초안입니다. 리포트(API)에는 아직 안 붙었습니다 — `tools/spine_draft.py`
  가 지금 리포트와 나란히 놓고 보는 시안을 뽑습니다.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from .constants import ELEMENT_OF_GAN, GENERATES, HIDDEN, TEN_GOD_GROUP, ten_god

SEED = Path(__file__).resolve().parents[3] / "seed" / "spine.json"

# 생의 고리 — 이 자리가 낳는 다음 자리
NEXT = {"비겁": "식상", "식상": "재성", "재성": "관성",
        "관성": "인성", "인성": "비겁"}

# ★ 쉬운 말로 (2026-09-11) — 「내놓는 자리」 가 아니라 **무엇인지**.
GROUP_WORD = {"비겁": "친구·동료", "식상": "말·글·솜씨", "재성": "돈·살림",
              "관성": "회사·규칙", "인성": "공부·어른"}

EL_WORD = {"목": "나무", "화": "불", "토": "흙", "금": "쇠", "수": "물"}
EL_HANJA = {"목": "木", "화": "火", "토": "土", "금": "金", "수": "水"}
SEAT = {"년주": "년", "월주": "월", "일주": "일", "시주": "시"}


@lru_cache(maxsize=1)
def table() -> dict:
    return json.loads(SEED.read_text("utf-8"))


def _jo(word: str, with_b: str, without: str) -> str:
    """받침을 보고 조사를 답니다. 한글이 아니면 받침 없는 쪽."""
    ch = word[-1] if word else ""
    has = "가" <= ch <= "힣" and (ord(ch) - 0xAC00) % 28 != 0
    return word + (with_b if has else without)


def count(f, group: str) -> int:
    return {"비겁": f.bi, "식상": f.sik, "재성": f.jae,
            "관성": f.gwan, "인성": f.inn}[group]


def reaches(f) -> bool:
    """흐름이 생의 다음 자리에 닿는가 — 그 자리가 명식에 하나라도 있는가."""
    return count(f, NEXT[f.flow]) >= 1


def key(f) -> str:
    return "%s>%s" % (f.flow, NEXT[f.flow] if reaches(f) else "끊김")


def empty_group(f) -> Optional[str]:
    """
    흐름을 **굽히는** 빈 자리 — 고리를 따라가다 처음 만나는 0.

    ★ 끊긴 사람은 닿지 못한 그 자리부터가 아니라 **그 다음**부터 봅니다.
      닿지 못한 자리는 척추 한 줄이 이미 말했습니다 — 같은 사실을 두 번
      말하지 않습니다.
    """
    g = NEXT[f.flow]
    if not reaches(f):
        g = NEXT[g]
    for _ in range(4):
        if g != f.flow and count(f, g) == 0:
            return g
        g = NEXT[g]
    return None


def seats(f, group: str) -> list:
    """
    이 묶음이 앉은 글자들 — 손님이 만세력을 펴고 짚을 수 있는 자리.
    천간(겉에 드러난 것)을 먼저, 지지 본기를 뒤에.
    돌려주는 것: [(글자, 자리, 십신)]
    """
    top, low = [], []
    for p in f.pillars:
        seat = SEAT.get(p.get("label"), "")
        if p.get("label") != "일주":
            g = ten_god(p["gan"], f.day_gan)
            if TEN_GOD_GROUP.get(g) == group:
                top.append((p["gan"], seat + "간", g))
        g = ten_god(HIDDEN[p["ji"]][0][0], f.day_gan)
        if TEN_GOD_GROUP.get(g) == group:
            low.append((p["ji"], seat + "지", g))
    return top + low


def _group_el(f, group: str) -> str:
    """묶음의 오행 — 일간에서 생의 고리를 몇 칸 갔는가."""
    el = ELEMENT_OF_GAN[f.day_gan]
    for g in ("비겁", "식상", "재성", "관성", "인성"):
        if g == group:
            return el
        el = GENERATES[el]
    return el


def chain_html(f) -> str:
    """
    흐름 세 단 — 「庚(그대) → 癸·癸·亥(식상 3) → 甲(재성 1)」.

    ★ 전부 셈입니다. 글자와 자리를 짚으니 손님이 대 볼 수 있습니다.
    """
    flow, nxt = f.flow, NEXT[f.flow]
    # ★ 칸 안의 말은 **쉬운 말**로 (2026-09-11). 「년간 · 월간 · 월지」 에
    #   풀이 괄호까지 붙어 기호 줄처럼 읽혔습니다 (평가 7번).
    steps = [("<b>%s</b>" % f.day_gan, "그대 자신")]
    groups = [nxt] if flow == "비겁" else [flow, nxt]
    for g in groups:
        at = seats(f, g)
        if at:
            steps.append((
                "<b>%s</b>" % " · ".join(ch for ch, _, _ in at),
                "%s %d개<br />%s" % (GROUP_WORD[g], count(f, g),
                                    " · ".join(SEAT_PLAIN.get(s, s) for _, s, _ in at))))
        else:
            steps.append(("<b>—</b>", "%s 0개<br />여덟 자에 없소" % GROUP_WORD[g]))
    boxes = '<span class="ar">→</span>'.join(
        '<span class="st">%s<small>%s</small></span>' % s for s in steps)

    # ★ 오행의 **실제 관계**로 적습니다 (2026-09-11 · 평가 1번).
    #   전에는 늘 「a가 b를 낳고」 로 적어, 관성·재성·인성 흐름에서
    #   「土生木」 「金生土」 같은 없는 관계가 찍혔습니다. 나 → 흐름 묶음의
    #   관계는 묶음마다 다릅니다 — 식상은 내가 낳고, 재성은 내가 누르고,
    #   관성은 나를 누르고, 인성은 나를 낳습니다. 흐름 → 다음은 늘 낳음.
    m = ELEMENT_OF_GAN[f.day_gan]
    e0 = _group_el(f, groups[0])
    links = []
    if flow == "비겁":
        links.append(_link(m, e0, "gen", True) if reaches(f) else
                     "%s 낳을 글자가 여덟 글자에 없소" % _jo(EL_WORD[m], "이", "가"))
    else:
        kind, a, b = {"식상": ("gen", m, e0), "재성": ("ctl", m, e0),
                      "관성": ("ctl", e0, m), "인성": ("gen", e0, m)}[flow]
        links.append(_link(a, b, kind, False))
        links.append(_link(e0, _group_el(f, groups[1]), "gen", True) if reaches(f)
                     else "%s 낳을 글자는 여덟 글자에 없소" % _jo(EL_WORD[e0], "이", "가"))
    say = ", ".join(links) + "."
    return '<div class="chain">%s</div><p class="tale">%s</p>' % (boxes, say)


SEAT_PLAIN = {"년간": "해 위", "년지": "해 아래", "월간": "달 위", "월지": "달 아래",
              "일지": "날 아래", "시간": "시 위", "시지": "시 아래"}
PATTERN_PLAIN = {"식상생재": "만든 것이 돈이 되는 길",
                 "재생관": "번 돈이 직함과 이름이 되는 길",
                 "관인상생": "맡은 일이 배움과 자격으로 남는 길"}


def _link(a: str, b: str, kind: str, last: bool) -> str:
    """오행 둘의 관계 한 마디 — gen: a가 b를 낳는다 · ctl: a가 b를 누른다."""
    if kind == "gen":
        return "%s %s 낳%s(%s生%s)" % (_jo(EL_WORD[a], "이", "가"), _jo(EL_WORD[b], "을", "를"),
                                    "소" if last else "고", EL_HANJA[a], EL_HANJA[b])
    return "%s %s 누르%s(%s剋%s)" % (_jo(EL_WORD[a], "이", "가"), _jo(EL_WORD[b], "을", "를"),
                                 "오" if last else "고", EL_HANJA[a], EL_HANJA[b])


def _chars(f, group: str) -> str:
    return " · ".join(ch for ch, _, _ in seats(f, group))


def head_html(sp: dict) -> str:
    """
    척추 컷 — 한 줄 · 흐름 세 단 · 옛 이름 · 강약 · 굽히는 자리.

    ★ 무료입니다. 이 집이 「근거 대는 집」 인 까닭이 한 화면에 서는 자리라,
      값 뒤에 두면 손님은 그 까닭을 못 보고 나갑니다.
    """
    out = ('<p class="spname">%s</p><p class="spine">%s</p>'
           % (sp["name"], sp["line"]))
    out += sp["chain_html"]
    if sp["pattern"]:
        base = sp["pattern"].split("(")[0]
        plain = PATTERN_PLAIN.get(base, "")
        out += ('<p class="tale">옛 책은 이 길을 <b>%s</b>%s 불렀소%s</p>'
                % (sp["pattern"], "이라" if _jo(base, "x", "") != base else "라",
                   # ★ 「A라는 뜻이오」 는 이름을 이름으로 바꾼 것이오.
                   #   쉽게 말하면 무엇인지를 앞에 답니다 (2026-09-17).
                   (" 쉽게 말하면 <b>%s</b>이오." % plain) if plain else "."))
    out += '<p class="tale">%s</p>' % sp["strength_line"]
    if sp["empty_line"]:
        out += '<p class="tale">%s</p>' % sp["empty_line"]
    return out


def scene_for(sid: str, concern: str) -> Optional[dict]:
    """열쇠로 바로 찾는 장면 — 답이 한 줄을 틀었을 때 두 번째 후보의 장면."""
    return (_scenes().get(sid) or {}).get(concern or "")


def depth_html(f, sp: dict, concern: Optional[str] = None,
               scn: Optional[dict] = None) -> str:
    """
    같은 힘의 앞과 뒤 — 강점 셋과 그 그림자 · 남들은/그대는 · 착각 · 맞는 판.

    ★ 끝에 **이 앞뒤가 어느 글자에서 나왔는지**를 댑니다. 강점과 그림자는
      척추 열 칸이 나눠 쓰는 글이라, 글자를 안 대면 누구에게나 맞는
      말로 읽힙니다.
    """
    out = "".join(
        '<div class="pair"><p class="tale"><span class="k">강점</span> %s</p>'
        '<p class="tale sh"><span class="k">같은 힘의 그림자</span> %s</p></div>'
        % (a, b) for a, b in sp["pairs"])
    out += "".join(
        '<div class="vs"><p class="tale m">%s</p><p class="tale">%s</p></div>'
        % (c["most"], c["you"]) for c in sp["contrast"])
    # ★ 착각은 한 번만 (2026-09-11). 물으신 고민의 착각(장면 표)이 있으면
    #   그쪽이 더 날카롭고, 둘 다 내면 거의 같은 말이 두 번 나갑니다.
    if not (scn and scn.get("trap")):
        out += ('<p class="tale"><span class="k">가장 위험한 착각</span> %s</p>'
                % sp["risk"])
    # ★ 「맞는 일」 은 일·돈·방향을 물었을 때만 (평가 5번) — 사랑을 물은
    #   사람에게 「공무원·교사」 를 권하던 자리입니다.
    if (concern or "work") in ("work", "money", "dir", "real_estate"):
        out += '<p class="tale"><span class="k">맞는 일</span> %s</p>' % sp["fit"]
    a = _chars(f, f.flow) or f.day_gan
    b = _chars(f, NEXT[f.flow])
    out += ('<p class="sm">이 강점과 그림자는 모두 <b>%s</b>에서 시작해 %s '
            '한 줄기에서 나온 것이오. 여덟 글자에서 그 글자를 찾아보시오.</p>'
            % (a, ("<b>%s</b>까지 이어지는" % b) if b else "이어질 데를 못 찾은"))
    return out


def source(f) -> str:
    nxt = NEXT[f.flow]
    return ("흐름 %s → %s · %s %d · %s %d · %s(%d)"
            % (f.flow, nxt, f.flow, count(f, f.flow), nxt, count(f, nxt),
               f.strength, f.strength_score))


# ★ 셋째 축 — 흐름 **안에서** 어느 쪽이 센가 (2026-09-11).
#
#   척추 열 칸이면 인구의 15%가 같은 한 줄을 받습니다. 같은 식상 흐름도
#   식신(차분히 만들어 내놓는)이 센 사람과 상관(틀을 치며 내지르는)이 센
#   사람은 다른 사람입니다. 재 보니 이 축을 곱하면 30갈래, 강약과 굽히는
#   자리까지 곱하면 264갈래 · 최다 1.98% 입니다 (tools/spine_draft --spread).
#   센 쪽 글(`variants`)이 있으면 그걸 쓰고, 없거나 둘이 같으면 기본 글.
PAIR = {"비겁": ("비견", "겁재"), "식상": ("식신", "상관"),
        "재성": ("편재", "정재"), "관성": ("편관", "정관"),
        "인성": ("편인", "정인")}


def sub(f) -> str:
    """흐름 묶음 안에서 더 많은 십신. 같거나 없으면 빈 글."""
    a, b = PAIR[f.flow]
    na, nb = f.ten_gods.get(a, 0), f.ten_gods.get(b, 0)
    if na > nb:
        return a
    if nb > na:
        return b
    return ""


def read(f) -> dict:
    """이 명식의 척추. 글은 하오체 한 벌 · 「그대」 한 벌입니다."""
    T = table()
    k = key(f)
    e = dict(T["spines"][k])
    s = sub(f)
    var = ((T.get("variants") or {}).get(k) or {}).get(s) if s else None
    if var:
        e.update({kk: vv for kk, vv in var.items() if vv})
    eg = empty_group(f)
    return {
        "key": k,
        "name": e["name"],
        "pattern": e.get("pattern") or "",
        "line": e["line"],
        "chain_html": chain_html(f),
        "strength_line": T["strength"][f.strength],
        "empty": eg,
        "empty_line": T["empty"][eg] if eg else "",
        "pairs": list(zip(e["strengths"], e["shadows"])),
        "contrast": e["contrast"],
        "risk": e["risk"],
        "fit": e["fit"],
        "probes": e["probes"],
        "source": source(f),
        "id": spine_id(f),
        "short": (T.get("short") or {}).get(spine_id(f))
                 or (T.get("short") or {}).get(k) or "그 힘",
    }


# ══════════════════════════════════════════════════════════
# 척추 서른 칸의 이름 · 장면 · 다리 · 두 번째 후보 (2026-09-11)
# ══════════════════════════════════════════════════════════
SCENE = Path(__file__).resolve().parents[3] / "seed" / "scene.json"
BRIDGE = Path(__file__).resolve().parents[3] / "seed" / "lens_bridge.json"


def spine_id(f) -> str:
    """서른 칸의 열쇠 — 「흐름>닿는 자리」 또는 「…/센 십신」 (그 글이 있을 때)."""
    k, s = key(f), sub(f)
    if s and s in ((table().get("variants") or {}).get(k) or {}):
        return "%s/%s" % (k, s)
    return k


@lru_cache(maxsize=1)
def _scenes() -> dict:
    return json.loads(SCENE.read_text("utf-8")) if SCENE.exists() else {}


@lru_cache(maxsize=1)
def _bridges() -> dict:
    return json.loads(BRIDGE.read_text("utf-8")) if BRIDGE.exists() else {}


def scene(f, concern: str) -> Optional[dict]:
    """
    이 사람이 **물으신 고민 속에서** 실제로 하는 모습 둘 · 착각 · 이번 주 한 가지.

    ★ 바깥 글의 「일반 사람은 쿠팡에서 어떻게 벌지 생각하는데, 당신은
      플랫폼을 만들어 수수료를 받으려 한다」 자리입니다. 자유 입력이 없어
      그 사람만의 일은 못 쓰지만, **그 사람이 알아볼 장면**은 씁니다.
    """
    T = _scenes()
    got = (T.get(spine_id(f)) or {}).get(concern or "")
    return got or (T.get(key(f)) or {}).get(concern or "")


def scene_html(sc: dict) -> str:
    out = "".join('<p class="tale">%s</p>' % s for s in sc.get("scenes") or [])
    if sc.get("trap"):
        out += ('<p class="tale"><span class="k">이 고민에서 가장 흔한 착각</span> '
                '%s</p>' % sc["trap"])
    return out


def bridge(lens_id: Optional[str], flow: str) -> str:
    """그 캐릭터가 한 줄을 제 눈으로 다시 읽는 다리. 없으면 빈 글."""
    if not lens_id:
        return ""
    return ((_bridges().get(lens_id) or {}).get(flow)) or ""


def alt_key(f) -> str:
    """
    **두 번째 후보** 척추 — 흐름을 뺀 묶음 가운데 가장 많은 것에서 세운 칸.

    ★ 손님의 답이 한 줄과 어긋날 때 씁니다. 여덟 글자가 두 번째로 미는
      쪽이 곧 그 사람이 한 줄을 **쓰는 방식**일 수 있습니다. 지어내지
      않고 센 수로 고릅니다 — 같으면 생의 고리 차례로.
    """
    order, g = [], NEXT[f.flow]
    for _ in range(4):
        order.append(g)
        g = NEXT[g]
    best = max(order, key=lambda x: (count(f, x), -order.index(x)))
    nxt = NEXT[best]
    return "%s>%s" % (best, nxt if count(f, nxt) >= 1 else "끊김")
