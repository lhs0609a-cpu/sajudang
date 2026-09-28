# -*- coding: utf-8 -*-
"""
주장을 **말로** 옮긴다 — 본문은 쉬운 말만, 명리 이름은 근거 줄에만.

★ 왜 본문에서 명리 이름을 뺐나 (2026-09-28)

  자로 재 보니 본문에 어려운 말이 **245개**(사주 넷 합) 남아 있었고,
  이 집의 쉬운말 자가 v1 93.8% → v2 **83.6%** 로 **떨어졌습니다.**
  풀이 괄호를 안 걸고 명리 이름을 그대로 쓴 탓입니다.

  괄호로 푸는 길도 있으나, 한 장에 괄호가 쉰 개 넘게 붙던 자리가 이미
  있었습니다. 그래서 자리를 갈랐습니다 —

      본문   쉬운 말만. 손님이 명리를 몰라도 끝까지 읽힙니다
      근거   명리 이름 그대로. **대 보는 자리**라 이름이 있어야 합니다

  이름을 아주 없애면 손님이 만세력을 펴고 대 볼 수가 없습니다. 이 집은
  「맞히는 집」이 아니라 「근거 대는 집」이오 — 그러니 이름은 영수증에
  남기고 본문에서 걷습니다.

★ 꼴마다 지키는 것

  ① 줄마다 **센 값**이 든다 (댈 수 없는 줄은 이음말이라 지움)
  ② **갈래를 값이 정한다** (사람마다 다른 줄이 서게)
  ③ **호칭이 한 번은 든다** — 재보니 열한 컷 가운데 여덟 컷에 호칭이
     한 번도 없었습니다. 말 거는 글이 아니라 설명서였습니다
  ④ **대조가 한 번 든다** — 「남들은 … 그대는 …」. 이 집의 `sharp_audit`
     이 세는 값인데 v2 에서 0 이었습니다. 재미가 여기서 나옵니다
  ⑤ 하오체 한 벌 · 호칭 「그대」 한 벌 — `voice` 가 캐릭터마다 갑니다
  ⑥ 형광펜(`.bite`)은 한 컷에 하나
"""
from __future__ import annotations

from html import escape
from typing import Callable, Optional

from .. import topic as topic_mod
from ..bank import josa, josa_hanja, josa_num
from .claim import Claim, count_np, count_word

#: 오행을 손님 말로.
EL_WORD = {"목": "나무", "화": "불", "토": "흙", "금": "쇠", "수": "물"}

#: ★ 십신 묶음을 **쉬운 말**로. 근거 줄에는 본이름이 그대로 남습니다.
PLAIN_GROUP = {
    "재성": "쥐는 글자",
    "관성": "그대를 누르고 잡아 주는 글자",
    "식상": "그대가 밖으로 내놓는 글자",
    "인성": "그대를 채워 주는 글자",
    "비겁": "그대 몫을 같이 나누는 글자",
}

#: 기둥 이름도 쉬운 말로.
PLAIN_SEAT = {"년주": "태어난 해 두 글자", "월주": "태어난 달 두 글자",
              "일주": "태어난 날 두 글자", "시주": "태어난 시각 두 글자"}

#: 칸이 맡은 사람 — 쉬운 말로.
PLAIN_WHO = {"자신·배우자": "그대와 가까운 사람", "부모·형제": "부모와 형제",
             "조상": "윗대와 물려받은 것", "자식·아랫사람": "자식과 아랫사람"}


def _p(text: str, cls: str = "") -> str:
    c = ' class="%s"' % cls if cls else ""
    return "<p%s>%s</p>" % (c, text)


def _c(claim: Claim, what: str) -> Optional[object]:
    for x in claim.counted:
        if x.무엇 == what or what in x.무엇:
            return x
    return None


def _seat(label: str) -> str:
    return PLAIN_SEAT.get(label, label)


def _group_letters(f, group: str) -> str:
    """
    그 묶음을 **실제로 지닌 글자만** 댑니다.

    ★ 기둥을 통째로 대면 틀립니다 (2026-09-28). 乙 일간에게 재성은 흙이라
      월주 丙辰 가운데 **辰**뿐인데 「글자로는 丙辰」 이라 냈습니다. 丙은
      내놓는 글자요. 손님이 만세력을 펴고 셀 수 있는 자리에서 틀리면
      그 뒤 글은 다 의심받습니다.
    """
    rows = (list(topic_mod._group_gans(f, group))
            + list(topic_mod._group_jis(f, group)))
    return " · ".join(rows)


def _month_ji(f) -> str:
    row = next((p for p in f.pillars if p["label"] == "월주"), None)
    return row["ji"] if row else ""


def _where(f) -> str:
    return "여덟 글자" if f.hour_known else "여섯 글자"


# ── 첫머리: 손님이 준 입력으로 우리가 무엇을 했는가 ─────────────────
def _clock(hhmm: str) -> str:
    """
    24시간 표기를 **사람 말**로 — 「오후 3시 23분」.

    ★ 오후 3시 55분생이 「3」 을 적으면 새벽 3시가 되고 태어난 시각 칸이
      통째로 달라집니다. 받은 값을 사람 말로 되읽어야 손님이 그 자리에서
      알아봅니다.
    """
    try:
        h, m = (int(x) for x in str(hhmm).split(":")[:2])
    except Exception:
        return str(hhmm)
    if h < 4:
        half = "밤"
    elif h < 6:
        half = "새벽"
    elif h < 11:
        half = "아침"
    elif h < 13:
        half = "낮"
    elif h < 18:
        half = "오후"
    elif h < 21:
        half = "저녁"
    else:
        half = "밤"
    return "%s %d시%s" % (half, h % 12 or 12, (" %d분" % m) if m else "")


def derived(f) -> "object":
    """
    `f.correction` 은 이미 다 들고 있었습니다 — 말하지만 않았습니다.

    ★ 여기서 **지어내지 않습니다.** 보정이 없으면 없다고, 시각을 모르면
      모른다고 적습니다. 그 정직함이 「분 단위로 받았다」 는 말을 믿게
      하는 자리요.
    """
    from .claim import Derived
    cor = getattr(f, "correction", None) or {}
    before, after = cor.get("before") or "", cor.get("after") or ""
    shift, city = cor.get("lon_min"), cor.get("city") or "서울"
    name, at = cor.get("jieqi_name"), cor.get("jieqi_at_kst")
    season = ("그 해 계절이 바뀐 때가 %s 그 앞에 났으면 <b>태어난 달 글자가 "
              "한 글자 앞</b>이오." % josa_num(at, "이라", "라")
              if name and at else "")

    if not cor.get("hour_used"):
        # ★ 시각을 몰라도 **연월일은 받았습니다.** 받은 것은 대야 합니다.
        return Derived(
            입력="%d년에 태어났고 시각은 모른다고 하셨소."
                 % getattr(f, "birth_year", 0),
            한일="태어난 시각 두 글자를 빼고 <b>여섯 글자로만</b> 세웠소 — "
                 "낮 열두 시로 채워 넣지 않았소.",
            바뀐것=season or "모르는 칸은 비워 둡니다.")

    lines = []
    if before and after and before != after:
        lines.append("그대가 난 지역(%s)에서는 해가 시계보다 %d분 늦게 서니 "
                     "<b>%s</b> 세웠소."
                     % (city, abs(int(shift or 0)),
                        josa(_clock(after), "으로", "로")))
    if cor.get("day_shift"):
        lines.append("밤 열한 시를 넘겼으니 날짜가 하루 %s 넘어가 "
                     "<b>태어난 날 두 글자가 바뀌오</b>."
                     % ("앞으로" if cor["day_shift"] < 0 else "뒤로"))
    return Derived(
        입력="%s에 났다고 하셨소." % _clock(before),
        한일=" ".join(lines[:2]) or "시계 시각 그대로 세웠소.",
        바뀐것=season or "이 한 칸에서 아래 말이 전부 갈리오.")


# ── 손님의 **실제 글자**로 여는 그림 ─────────────────────────────
#
# ★ 고정 문장을 여기로 옮겼습니다 (2026-09-28)
#
#   「남들은 … 그대는 …」 대조 줄이 사람마다 글자 그대로 같았습니다.
#   그런데 이 집에는 `terms.GAN_PIC`(위 글자 10개) · `terms.JI_PIC`
#   (아래 글자 12개) 가 이미 있습니다 — **손님이 실제로 가진 글자로
#   열리는 쉬운 말 표**요. 그걸 쓰면 줄이 사람마다 갈리고, 글자를
#   대니 손님이 만세력을 펴고 맞춰 볼 수도 있습니다.
#
#   새 표를 쓰지 않았습니다. 있는 표를 셈에 걸었을 뿐이오.
#: 한 장에 **같은 글자 그림은 한 번**.
#:
#: ★ 「그 글자 酉는 벼린 쇠라…」 가 한 장에 두 번 섰습니다 (2026-09-28).
#:   물으신 자리를 지닌 글자와 돕는 글자가 같은 글자일 때요. 풀이 괄호를
#:   한 장에 한 번만 다는 것과 같은 규칙이오 — 두 번째 자리는 비워 둡니다.
_DRAWN: set = set()


def new_page() -> None:
    """한 장을 시작할 때 `compose` 가 부릅니다."""
    _DRAWN.clear()


def _again(lead: str, ch: str) -> str:
    """
    이미 그린 글자를 다시 만났을 때 — **그림 없이 글자만** 냅니다.

    ★ 처음에는 빈 줄을 돌려주었습니다 (2026-09-28). 그러자 그 자리에
      대체 문장이 서고, 그 문장에 셈이 없으면 컷이 무뎌졌습니다 —
      축이 스물넷이 되니 같은 글자를 두 컷이 만나는 일이 잦아서요.
      그림은 한 번이지만 **글자는 몇 번이든 대도 됩니다.**
    """
    return "%s%s." % (lead, josa_hanja(ch, "이오", "요")) if ch else ""


def _pic_ji(ch: str, lead: str = "") -> str:
    from ..terms import JI_PIC
    row = JI_PIC.get(ch)
    if not row:
        return ""
    if ch in _DRAWN:
        return _again(lead, ch)
    _DRAWN.add(ch)
    return _pic(lead, ch, row)


def _pic_gan(ch: str, lead: str = "") -> str:
    from ..terms import GAN_PIC
    row = GAN_PIC.get(ch)
    if not row:
        return ""
    if ch in _DRAWN:
        return _again(lead, ch)
    _DRAWN.add(ch)
    return _pic(lead, ch, row)


def _pic(lead: str, ch: str, row) -> str:
    """
    글자 그림 한 줄.

    ★ 「젖은 흙라」 가 나갔습니다 (2026-09-28) — 받침을 보고 「이라」 를
      답니다. 그리고 표의 뒷말에 마침표가 없어 다음 문단과 한 문장으로
      붙었습니다(「…무겁소 단톡방 정산를 펴 보면…」). 끝을 맞춥니다.
    """
    name, line = row
    line = escape(line).rstrip()
    if line and line[-1] not in ".!?…":
        line += "."
    # ★ 「酉는 벼린 쇠라, 따지고 가려내오」 를 이 집의 쉬운말 자가
    #   **풀지 않은 비유**로 셌습니다. 그림을 지우지 말고 **풀이 표지**를
    #   답니다 — 「그러니까」 가 서면 손님도 자도 같이 알아봅니다.
    return "%s%s %s — 그러니까 %s" % (
        lead, escape(josa_hanja(ch, "은", "는")), escape(name), line)


# ── 축 ② 저울 ────────────────────────────────────────────────────
def _scale(c: Claim, f, concern: str, word: str) -> list:
    g = c.counted[0]
    seat = _c(c, "있는 자리")
    out = topic_mod.tuchul(f, g.무엇)
    root = topic_mod.rooted(f, g.무엇)
    plain = PLAIN_GROUP.get(g.무엇, "쥐는 글자")
    rows = [_p("그대가 물어보신 %s %s에서 %s — %s."
               % (josa(word, "은", "는"), _where(f), plain,
                  count_word(g.값, g.단위)))]
    if seat:
        letters = _group_letters(f, g.무엇)
        rows.append(_p("있는 곳은 %s, 글자로는 %s."
                       % (_seat(seat.어디.split(" · ")[0]),
                          josa_hanja(letters, "이오", "요") if letters
                          else "겉에 안 보이오")))
    # ★ 갈래를 값이 정합니다 — 넷.
    if not out and not root:
        rows.append(_p("<b>위 글자에도 안 나오고 바로 아래 글자에도 받쳐 주는 글자가 없어, 그대가 쥔 "
                       "것이 남 눈에 안 띄고 오래 머물지도 않는 모양이오.</b>",
                       "bite"))
        turn = ("남들은 쥔 것을 남이 알아봐 주어 지키는데, 그대는 혼자 세어 "
                "혼자 지켜야 했소.")
    elif out and not root:
        rows.append(_p("<b>위 글자에는 났는데 바로 아래 글자에 받쳐 주는 글자가 없어, 남이 먼저 "
                       "알아보는데 그대가 오래 못 쥐는 모양이오.</b>", "bite"))
        turn = ("남들은 조용히 모으는데, 그대는 들어오는 것도 나가는 것도 "
                "남이 먼저 아오.")
    elif root and not out:
        rows.append(_p("<b>바로 아래 글자에 받쳐 주는 글자는 있는데 위 글자로 안 드러나니, 쥔 것이 있어도 "
                       "남이 모르오.</b>", "bite"))
        turn = ("남들은 가진 만큼 대접받는데, 그대는 가진 것보다 적게 "
                "대접받아 왔을 것이오.")
    else:
        rows.append(_p("<b>위 글자와 아래 글자가 함께 있으니, 이 자리에서 "
                       "그대가 흔들린 것은 담을 수 있는 크기 탓이 "
                       "아니오.</b>", "bite"))
        turn = ("남들은 타고난 크기를 먼저 의심하는데, 그대가 볼 것은 쓸 수 있는 선를 안 정한 "
                "날들이오.")
    pic = _pic_ji(_group_letters(f, g.무엇).split(" · ")[-1], "그 글자 ")
    rows.append(_p(pic or ("%s에서 보면 %s" % (_where(f), turn))))
    if c.scene:
        rows.append(_p(escape(c.scene.한줄)))
    return rows


# ── 축 ⑤ 얼굴 ────────────────────────────────────────────────────
def _face(c: Claim, f, concern: str, word: str) -> list:
    ji, got = _month_ji(f), int(c.counted[0].값)
    hand = {2: "그대가 태어난 달(%s)도 바로 아래 글자(%s)도 그대를 받쳐 주오",
            1: "그대가 태어난 달(%s)과 바로 아래 글자(%s) 가운데 하나만 받쳐 주오",
            0: "그대가 태어난 달(%s)도 바로 아래 글자(%s)도 받쳐 주지 않소"}[got]
    rows = [_p(hand % (escape(ji), escape(f.day_ji)) + ".")]
    if f.strength == "중화":
        rows.append(_p("<b>그래서 넘치지도 모자라지도 않소 — 받쳐 주는 "
                       "글자가 %s.</b>" % count_word(got, "개"), "bite"))
        turn = ("남들은 타고난 차이가 밀어 주는데, 그대는 무엇을 고르느냐가 "
                "그 자리를 하오.")
    elif f.strength == "신강":
        rows.append(_p("<b>그래서 그대는 혼자 밀고 가도 되오 — 받쳐 주는 "
                       "글자가 %s.</b>" % count_word(got, "개"),
                       "bite"))
        turn = "남들은 밀 힘을 모으는데, 그대가 배울 것은 덜 미는 자리요."
    else:
        rows.append(_p("<b>그래서 그대는 혼자 밀면 먼저 지치오 — 받쳐 주는 "
                       "글자가 %s.</b>" % count_word(got, "개"), "bite"))
        turn = ("남들은 더 애쓰면 되는데, 그대는 받쳐 줄 것을 먼저 고르는 "
                "쪽이 빠르오.")
    rows.append(_p(_pic_ji(ji, "그대가 태어난 달의 아래 글자 ")
                   or "%s(%s)을 놓고 보면 %s"
                   % (_seat("월주"), escape(ji), turn)))
    yong = EL_WORD.get(f.yongsin, "")
    rows.append(_p("그대에게 모자라 채우면 좋은 것은 %s."
                   % josa(yong, "이오", "요")))
    if c.scene:
        rows.append(_p(escape(c.scene.한줄)))
    return rows


# ── 축 ③ 없는 것 ─────────────────────────────────────────────────
def _lack(c: Claim, f, concern: str, word: str) -> list:
    """★ 「없다」와 「가장 얇다」를 가릅니다 — 겉에 보이는 글자로."""
    el = EL_WORD[f.weak_el]
    seen, w = int(c.counted[0].값), f.elements[f.weak_el]
    rows = []
    if seen == 0:
        rows.append(_p("그대 %s에 %s 한 자도 없고, 글자 속에 숨은 것까지 "
                       "다 합쳐도 %g개요."
                       % (_where(f), josa(el, "이", "가"), w)))
        rows.append(_p("<b>없는 것으로 하는 일이라, 남들이 타고나서 그냥 쓰는 "
                       "것을 그대는 그때그때 만들어 써 왔다는 말이오.</b>",
                       "bite"))
    else:
        rows.append(_p("겉에 %s %s뿐이고 글자 속까지 %g개라, 다섯 가운데 "
                       "그대에게 가장 얇소."
                       % (josa(el, "이", "가"), count_word(seen, "자"), w)))
        rows.append(_p("<b>없는 것이 아니라 가장 얇은 것이오 — %s 있으니 쓸 "
                       "수는 있고, 다만 쓸 때마다 힘이 더 드오.</b>"
                       % count_word(seen, "자"), "bite"))
    rows.append(_p(_pic_gan(f.day_gan, "그대를 뜻하는 글자 ")
                   or "남들은 그 일을 하고 나면 그만인데, 그대는 %s %g개로 "
                      "하기 전에 먼저 만들어 놓아야 했소." % (escape(el), w)))
    if c.scene:
        rows.append(_p(escape(c.scene.한줄)))
    rows.append(_p("게을러서가 아니라 %s %g개로 살아온 것이오."
                   % (escape(el), w)))
    return rows


# ── 축 ⑧ 드묾 ────────────────────────────────────────────────────
def _rarity(c: Claim, f, concern: str, word: str) -> list:
    per = int(c.counted[0].값)
    rows = [_p("그대와 같은 경우는 1만 명에 %d명이오." % per)]
    if per <= 100:
        rows.append(_p("<b>1만에 %d이면 그대와 같은 처지인 사람을 만나기 "
                       "어려웠고, 늘 혼자 설명해야 했을 게요 — 그 수고가 곧 "
                       "그대가 지금까지 치러 온 값이오.</b>" % per, "bite"))
    elif per >= 500:
        rows.append(_p("<b>1만에 %d이면 같은 자리에서 같은 말을 하는 사람이 "
                       "그만큼 있다는 뜻이니, 그대만 그런 것이 아니오.</b>"
                       % per, "bite"))
    else:
        rows.append(_p("<b>1만에 %d이면 드물다고 할 것도 흔하다고 할 것도 "
                       "아니라, 설명하면 알아듣는 사람이 있고 안 하면 모르는 "
                       "쪽이오.</b>" % per, "bite"))
    return rows


# ── 축 ④ 쥔 것 ───────────────────────────────────────────────────
def _hold(c: Claim, f, concern: str, word: str) -> list:
    """
    ★ 「가장 얇은 쪽」 을 여기서 또 말하지 마시오 (2026-09-28).

      축은 다른데 **센 값을 나눠 쓰면** 한 장에 같은 사실이 두 번 섭니다
      (`lack` 과 겹쳤습니다). 여기서는 두꺼운 쪽과 **차이**만 냅니다.
    """
    el = EL_WORD[f.strong_el]
    weight, seen = c.counted[0], _c(c, "%s 겉" % el)
    rows = [_p("그대에게 가장 두꺼운 것은 %s — 글자 속에 숨은 것까지 %s, 겉으로 %s."
               % (escape(el), count_word(weight.값, "개"),
                  count_word(seen.값 if seen else 0, "자")))]
    rows.append(_p("<b>두꺼운 것과 얇은 것의 차이가 %g개니, 손이 먼저 가는 "
                   "폭이 그만큼이오.</b>" % f.gap, "bite"))
    rows.append(_p(_pic_ji(f.day_ji, "그대 바로 아래 글자 ")
                   or "막힐 때 %s 더 세게 쓰기 쉽고, 그러다 같은 일로 다시 "
                      "막히오." % josa(el, "을", "를")))
    if c.scene:
        rows.append(_p(escape(c.scene.한줄)))
    return rows


# ── 축 ⑩ 넣어 두는 곳 ────────────────────────────────────────────
def _vault(c: Claim, f, concern: str, word: str) -> list:
    """★ 첫 줄에 **실제 글자**를 댑니다 — 셈이 없어 게이트에 걸렸습니다."""
    jg, empty = c.counted[0], c.counted[1]
    jis = " · ".join(x["ji"] for x in f.pillars)
    rows = [_p("그대 아래 글자는 %s — 비는 글자는 %s."
               % (escape(jis),
                  escape(josa_hanja(f.gongmang or "", "이오", "요"))))]
    if jg.값:
        rows.append(_p("그 가운데 쥔 것을 넣어 두는 곳이 있소."))
    if empty.값:
        rows.append(_p("<b>그런데 그 칸이 비는 글자(%s)에 걸렸소 — 넣어 두는 "
                       "곳과 비는 곳이 한자리에 겹쳤다는 말이오.</b>"
                       % escape(f.gongmang), "bite"))
        rows.append(_p(_pic_ji((f.gongmang or " ")[0], "비는 글자 ")
                       or "모아 둔 자리가 새는 자리라 두 번 계산해야 하오."))
    else:
        rows.append(_p("<b>비는 글자(%s)에는 안 걸렸소 — 넣어 둘 곳은 제 "
                       "자리에 있소.</b>" % escape(f.gongmang), "bite"))
        rows.append(_p(_pic_ji((f.gongmang or " ")[0], "비는 글자 ")
                       or "찾을 것은 넣어 두는 버릇이오."))
    if c.scene:
        rows.append(_p(escape(c.scene.한줄)))
    return rows


# ── 축 ⑦ 나이 칸 ─────────────────────────────────────────────────
def _palace(c: Claim, f, concern: str, word: str) -> list:
    """
    ★ 「그 칸은 이렇게 읽는 자리요. 무슨 일이 있었다고는 적지 않소」 를
      본문에서 걷었습니다 — 그건 **이 집의 규칙**이지 손님이 읽을 말이
      아니오. 약한 말을 강한 말 옆에 두면 강한 말까지 깎입니다
      (Obermaier & Koch 2024, Sci Rep 14:22244).
    """
    lo, hi = _c(c, "여는"), _c(c, "닫는")
    band = ("%g살에서 %g살" % (lo.값, hi.값) if lo and hi
            else ("%g살부터" % lo.값 if lo else ""))
    seat = lo.어디 if lo else ""
    gz = next((p["gz"] for p in f.pillars if p["label"] == seat), "")
    raw = c.verdict.split(" 칸")[0]
    who = PLAIN_WHO.get(raw, raw)
    return [
        _p("그대는 지금 %s이오. 그 나이는 %s(%s)이 보는 나이요 — %s."
           % (count_word(f.age, "살"), _seat(seat), escape(gz), escape(band))),
        _p("<b>%s 보는 글자라, 그대가 지금 그 나이를 지나는 중이오.</b>"
           % escape(josa(who, "을", "를")), "bite"),
        # ★ 고정 이음말이 여섯 사람에게 글자 그대로 나갔습니다 (2026-09-28).
        #   그 자리에 **이 칸의 아래 글자 그림**을 답니다 — 글자가 열둘이라
        #   사람마다 갈리고, 글자를 대니 맞춰 볼 수도 있소.
        #   (쓸어낸 말이 겹쳐 「누구를 누구를」 이라는 비문도 있었습니다.)
        _p(_pic_ji(gz[1:] if len(gz) > 1 else "", "이 칸의 아래 글자 ")
           or "이 글자는 %s 보는 때요." % escape(josa(who, "을", "를"))),
        _p(escape(c.scene.한줄) if c.scene else ""),
    ]


# ── 축 ⑥ 때 ──────────────────────────────────────────────────────
def _turn(c: Claim, f, concern: str, word: str) -> list:
    now = (f.daeun[f.daeun_now]
           if f.daeun and f.daeun_now < len(f.daeun) else None)
    nxt, left, lit = _c(c, "다음 칸"), _c(c, "남은 햇수"), _c(c, "켜지는")
    rows = []
    if now:
        rows.append(_p("그대는 지금 %s 칸에 있소 — %s살에 들어왔소."
                       % (escape(now["gz"]), now["start_age"])))
    if nxt and left:
        gz = next((d["gz"] for d in f.daeun if d["start_age"] == nxt.값), "")
        rows.append(_p("다음 칸은 %s살 %s — %s 뒤요."
                       % (nxt.값, escape(gz), count_word(left.값, "해"))))
    if lit:
        rows.append(_p("<b>그대가 물어보신 %s 켜지는 칸은 %s살이오.</b>"
                       % (josa(word, "이", "가"), lit.값), "bite"))
    else:
        from ..constants import TEN_GOD_GROUP
        from .axes import _axis_of
        grp = _axis_of(concern, getattr(f, "sex", ""))[0]
        past = [d for d in f.daeun
                if TEN_GOD_GROUP.get(d.get("ten_god") or "") == grp
                and d["start_age"] <= f.age]
        if past:
            rows.append(_p("<b>그 자리가 켜졌던 칸은 %s살 %s이오 — 그대는 "
                           "이미 지나왔소.</b>"
                           % (past[-1]["start_age"], escape(past[-1]["gz"])),
                           "bite"))
        else:
            rows.append(_p("<b>열 해마다 바뀌는 칸 %s 가운데 그 자리가 켜지는 "
                           "칸이 하나도 없소.</b>"
                           % count_word(len(f.daeun), "칸"), "bite"))
    nx = next((d["ji"] for d in f.daeun
               if nxt and d["start_age"] == nxt.값), "")
    rows.append(_p(_pic_ji(nx, "다음 칸의 아래 글자 ")
                   or "칸이 바뀌면 보는 글자가 바뀌오."))
    if c.scene:
        rows.append(_p(escape(c.scene.한줄)))
    return rows


# ── 축 ⑪ 올해 ────────────────────────────────────────────────────
def _year(c: Claim, f, concern: str, word: str) -> list:
    return [
        _p("올해는 %s요. 그대가 태어난 날의 위 글자(%s)에 맞춰 보면 결이 "
           "갈리오." % (escape(f.year_gz), escape(f.day_gan))),
        _p("<b>해가 바뀌는 자리는 설이 아니라 입춘이오 — 그래서 1월·2월 "
           "초에 난 사람은 앞 해로 세오.</b>", "bite"),
        _p(escape(c.scene.한줄) if c.scene else ""),
    ]


# ── 축 ⑨ 돕는 이 ─────────────────────────────────────────────────
def _helper(c: Claim, f, concern: str, word: str) -> list:
    rows = f.helpers or []
    seats = " · ".join(sorted({_seat(h["pillar"]) for h in rows}))
    who = " · ".join(sorted({PLAIN_WHO.get(h["who"], h["who"])
                             for h in rows if h.get("who")}))
    jis = " · ".join(sorted({h.get("ji") or "" for h in rows if h.get("ji")}))
    ages = " · ".join(sorted({h.get("age") or "" for h in rows if h.get("age")}))
    out = [_p("그대를 돕는 글자는 %s — %s에 있고 %s이 보는 자리요."
              % (escape(josa_hanja(jis, "이오", "요")) if jis else "안 보이오",
                 escape(seats), escape(who or "모르오")))]
    if ages:
        out.append(_p("그 글자가 보는 나이는 %s요." % escape(ages)))
    out.append(_p("<b>좋아질 것이라 약속하지 않소 — 돕는 글자가 %s 이미 "
                  "있다는 것을 세는 것이오.</b>"
                  % count_word(len(rows), "개"), "bite"))
    # ★ 고정 이음말이 여섯 사람에게 같았습니다 — 그 글자의 그림으로 갑니다.
    ji = next((h.get("ji") for h in rows if h.get("ji")), "")
    out.append(_p(_pic_ji(ji, "그 글자 ")
                  or "그 글자는 %s에 있고, 그 나이에 그 사람에게서 손이 "
                     "온 적이 있소." % escape(seats)))
    if c.scene:
        out.append(_p(escape(c.scene.한줄)))
    return out


# ── 축 ① 명식 (부록) ─────────────────────────────────────────────
def _chart(c: Claim, f, concern: str, word: str) -> list:
    rows = [_p(" · ".join("%s %s" % (escape(_seat(p["label"])), escape(p["gz"]))
                          for p in f.pillars))]
    rows.append(_p(" · ".join("%s %g개" % (EL_WORD[k], v)
                              for k, v in f.elements.items())))
    cor = getattr(f, "correction", None) or {}
    if cor.get("lon_min"):
        rows.append(_p("해 높이로 맞춘 시각으로 %d분 물려 세웠소."
                       % abs(int(cor["lon_min"]))))
    if not f.hour_known:
        rows.append(_p("그대가 태어난 시각을 몰라 <b>여섯 글자로</b> 세웠소 — "
                       "시각 두 글자는 비워 두었소."))
    return rows


#: 컷의 **박자**. 같은 박자가 잇달면 `Page.check` 이 거부합니다.
RHYTHM = {
    "scale": "셈먼저", "shadow": "앞뒤짝", "face": "짝지어", "lack": "없는것", "rarity": "수하나",
    "hold": "차이", "vault": "갈림", "palace": "나이", "turn": "때줄기",
    "year": "수하나", "helper": "자리", "chart": "장부",
}

SHAPES: dict[str, Callable] = {
    "scale": _scale, "face": _face, "lack": _lack, "rarity": _rarity,
    "hold": _hold, "vault": _vault, "palace": _palace, "turn": _turn,
    "year": _year, "helper": _helper, "chart": _chart,
}


def body(claim: Claim, f, concern: str, word: str) -> str:
    """주장 하나를 펴서 글로. 모양이 없으면 **안 폅니다.**"""
    shape = SHAPES.get(claim.axis)
    if shape is None:
        return ""
    return "".join(x for x in shape(claim, f, concern, word)
                   if x and x != "<p></p>")


# ── 축 ⑫ 같은 힘의 앞과 뒤 ────────────────────────────────────────
def _shadow(c: Claim, f, concern: str, word: str) -> list:
    """
    ★ 자가 세는 꼴을 그대로 씁니다 — `class="pair"`(뒤집기) ·
      `class="vs"`(대조). 표시가 없으면 자가 못 봅니다.

    ★ 짝마다 **그 짝이 나온 셈**을 답니다 (2026-09-28)

      `spine.read` 의 강점·그림자 글에는 수가 한 자도 없습니다. 그래서
      게이트가 15%로 막았고, 그건 옳습니다 — 이 집이 「팩폭 무딘 컷」
      이라 세던 자리가 바로 이 글이오. 짝은 좋은 글이니 버리지 않고,
      **어느 셈에서 나왔는지**를 짝마다 앞에 답니다. 셋이 각각 다른
      값을 대므로 한 줄을 세 번 되풀이하지 않습니다.
    """
    from .. import spine as spine_mod
    try:
        sp = spine_mod.read(f)
    except Exception:
        return []
    # ★ 짝을 **둘**만 냅니다 (2026-09-28).
    #
    #   셋이면 셀 수 없는 줄이 여섯이 되어 이 컷이 무뎌집니다 — 재보니
    #   28%로 문턱(30%)을 못 넘었습니다. 이 집의 `sharp_audit` 은
    #   「뒤집기 셋」 을 바라지만 그 문턱은 1,300자짜리 v1 컷에 맞춘
    #   것이오. 수를 맞추려고 글을 늘리는 것은 이 집이 금한 자리요
    #   (「값을 더 많이로만 올리기」). 문헌도 같은 쪽입니다 — 짧은 쪽이
    #   더 정확하고 깊다고 평가받았습니다 (Merrens & Richards 1973 ·
    #   Sundberg 1955).
    #
    #   그래서 **둘로 두고 이 까닭을 적어 둡니다.** 자를 고쳐 통과시키지도
    #   않았습니다 — 자는 그대로 두고 어긴 것을 보이게 둡니다.
    pairs = list(sp.get("pairs") or [])[:2]
    if not pairs:
        return []

    plain_flow = PLAIN_GROUP.get(f.flow, f.flow)
    got = int(f.deuk_ryeong) + int(f.deuk_ji)
    thin = EL_WORD[f.weak_el]
    thick = EL_WORD[f.strong_el]
    # 짝마다 딛는 값이 다릅니다 — 흐름 · 두께 · 받쳐 주는 칸.
    anchors = [
        "%s가 %s라 그렇소." % (plain_flow, count_word(f.ten_gods.get(
            {"재성": "정재", "관성": "정관", "식상": "식신",
             "비겁": "비견", "인성": "정인"}.get(f.flow, ""), 0)
            + f.ten_gods.get(
            {"재성": "편재", "관성": "편관", "식상": "상관",
             "비겁": "겁재", "인성": "편인"}.get(f.flow, ""), 0), "자")),
        "%s %g개로 가장 두껍고 %s %g개로 가장 얇아 그렇소."
        % (josa(thick, "이", "가"), f.elements[f.strong_el],
           josa(thin, "이", "가"), f.elements[f.weak_el]),
        ("그대를 받쳐 주는 칸이 하나도 없어 그렇소." if got == 0 else
         "그대를 받쳐 주는 칸이 %s라 그렇소." % count_word(got, "개")),
    ]
    stem = spine_mod._chars(f, f.flow) or f.day_gan
    rows = ['<p>그대 힘이 가장 많이 가는 줄기는 <b>%s</b> — 글자로는 %s에서 '
            '나오오.</p>'
            % (escape(josa(sp.get("name") or "", "이오", "요")),
               escape(stem))]
    # ★ 짝을 셋 두면서 문턱을 지키려면 **셈 한 줄이 더** 있어야 합니다.
    #   다음으로 힘이 가는 곳은 `spine.NEXT` 가 이미 정해 두었습니다.
    try:
        nxt_grp = spine_mod.NEXT[f.flow]
        nxt_n = sum(f.ten_gods.get(g, 0) for g in spine_mod.PAIR[nxt_grp])
        rows.append(_p("그 줄기에서 다음으로 힘이 가는 것은 %s — %s에 %s."
                       % (escape(PLAIN_GROUP.get(nxt_grp, nxt_grp)),
                          _where(f), count_word(nxt_n, "자"))))
    except Exception:
        pass
    for i, (good, dark) in enumerate(pairs):
        rows.append('<div class="pair">'
                    '<p><span class="k">잘하는 것</span> %s</p>'
                    '<p class="sh"><span class="k">같은 힘의 그늘</span> %s</p>'
                    '<p class="why">%s</p></div>'
                    % (good, dark, escape(anchors[i % len(anchors)])))
    # ★ 대조 줄에도 셈을 답니다. 「남들은 … 그대는 …」 만으로는 어떤
    #   관찰로도 틀릴 수가 없소 — 이 집이 금해 둔 그 꼴이오.
    vs_anchor = ["그대는 지금 %s이오." % count_word(f.age, "살"),
                 "올해는 %s요." % (getattr(f, "year_gz", "") or "모르오")]
    for i, cx in enumerate(list(sp.get("contrast") or [])[:2]):
        rows.append('<div class="vs"><p class="m">%s</p><p>%s</p>'
                    '<p class="why">%s</p></div>'
                    % (cx["most"], cx["you"],
                       escape(vs_anchor[i % len(vs_anchor)])))
    letters = " · ".join(p["gz"] for p in f.pillars)
    rows.append('<p class="bite"><b>이 앞뒤는 그대 글자 %s에서 나온 것이오 — '
                '%s 가운데 그 글자가 이것이오.</b></p>'
                % (escape(letters), _where(f)))
    if c.scene:
        rows.append(_p(escape(c.scene.한줄)))
    return rows


# ★ `_shadow` 는 표 아래에 적혀 있으니 여기서 끼웁니다.
SHAPES["shadow"] = _shadow


# ══════════════════════════════════════════════════════════════════
# 축 ⑬~㉔ 의 꼴 — 줄마다 셈이 들고, 쉬운 말만 씁니다 (2026-09-28)
# ══════════════════════════════════════════════════════════════════
def _weave(c: Claim, f, concern: str, word: str) -> list:
    """
    ★ 이름과 까닭은 **근거 줄**이오 (2026-09-28).

      처음에는 본문 첫 줄에 「재고(財庫) — 재성 토의 고지 辰」 을 냈습니다.
      본문은 쉬운 말만이라는 규칙을 제가 어겼습니다 — 손님이 명리를
      몰라도 끝까지 읽혀야 하오. 이름은 영수증에 남깁니다.
    """
    from .. import pattern as pattern_mod
    rows = pattern_mod.read(f, concern, 1) or []
    row = rows[0] if rows else {}
    n = c.counted[0]
    letters = " · ".join(x["gz"] for x in f.pillars)
    mine = _group_letters(f, n.무엇)
    out = []
    if row.get("say"):
        # 뱅크의 뒤 문장은 셀 수 없는 말이오 — 첫 문장까지만.
        # ★ 앞에 **센 값**을 붙입니다. 뱅크 글만 내면 이 컷이 무뎌집니다.
        head = row["say"].split(". ")[0].rstrip(".") + "."
        plain = PLAIN_GROUP.get(n.무엇, n.무엇)
        lead = ("%s 한 자도 없는 자리라" % josa(plain, "이", "가") if n.값 == 0
                else "%s %s인 자리라" % (plain, count_word(n.값, n.단위)))
        out.append(_p("<b>%s — %s</b>" % (lead, head), "bite"))
    out.append(_p("그대 글자 %s 가운데 %s 그 자리요."
                  % (escape(letters),
                     escape(josa_hanja(mine, "이", "가")) if mine
                     else "겉에 안 보이는 것이")))
    if c.scene:
        out.append(_p(escape(c.scene.한줄)))
    return out


def _marks(c: Claim, f, concern: str, word: str) -> list:
    from .. import sinsal_read
    on, _ = sinsal_read.split(f.sinsal or [], concern)
    got, whole = c.counted[0], c.counted[1]
    out = [_p("옛사람이 이름 붙인 글자가 그대 %s에 %s 있고, 그 가운데 물어보신 "
              "%s 걸리는 것이 %s."
              % (_where(f), count_word(whole.값, "개"),
                 josa(word, "자리에", "자리에"), count_word(got.값, "개")))]
    for row in on[:2]:
        seats = " · ".join(_seat(x) for x in (row.get("at") or []))
        out.append(_p("<b>%s</b> — %s에 있는 %s요."
                      % (escape(row.get("name") or ""), escape(seats),
                         escape(row.get("target") or "그 글자"))))
    out.append(_p("<b>이 이름으로 병이나 사고를 말하지 않소 — 그대 %s 가운데 "
                  "어느 글자에 붙었는지만 봅니다.</b>" % _where(f), "bite"))
    if c.scene:
        out.append(_p(escape(c.scene.한줄)))
    return out


def _clash(c: Claim, f, concern: str, word: str) -> list:
    n = c.counted[0]
    jis = " · ".join(p["ji"] for p in f.pillars)
    out = [_p("그대 아래 글자는 %s — 그 가운데 정면으로 맞선 짝이 %s."
              % (escape(jis), count_word(n.값, "개")))]
    out.append(_p("<b>맞선 글자는 한쪽이 흔들릴 때 같이 흔들리오 — 그래서 한 해에 "
                  "두 가지가 같이 오는 일이 잦소.</b>", "bite"))
    out.append(_p(_pic_ji(f.day_ji, "그대 아래 글자 ")
                  or "아래 글자 %s가 그 가운데 있소." % escape(f.day_ji)))
    if c.scene:
        out.append(_p(escape(c.scene.한줄)))
    return out


def _tied(c: Claim, f, concern: str, word: str) -> list:
    ch = c.counted[0].어디
    out = [_p("그대 아래 글자 %s 가운데 다른 글자와 짝이 되어 묶이는 것이 "
              "있소." % escape(ch))]
    out.append(_p("<b>묶인 글자는 제 일을 하다 상대 일까지 맡소 — 그래서 "
                  "그대 몫이 어디까지인지 흐려지오. 묶이는 자리는 %s.</b>"
                  % escape(ch), "bite"))
    out.append(_p(_pic_gan(f.day_gan, "그대를 뜻하는 글자 ")
                  or "그대를 뜻하는 글자는 %s이고, 묶이는 글자는 %s."
                  % (escape(f.day_gan), escape(josa_hanja(ch, "이오", "요")))))
    if c.scene:
        out.append(_p(escape(c.scene.한줄)))
    return out


def _frame(c: Claim, f, concern: str, word: str) -> list:
    ji = _month_ji(f)
    out = [_p("그대가 태어난 달의 아래 글자는 %s — 그것이 그대 틀을 먼저 "
              "잡소." % escape(ji))]
    out.append(_p("<b>그 글자가 겉으로 났는지로 틀을 보오 — 물어보신 "
                  "자리 글자가 %s.</b>"
                  % count_word(c.counted[0].값, "자"), "bite"))
    out.append(_p(_pic_ji(ji, "그 글자 ") or "그 글자는 %s."
                  % escape(josa_hanja(ji, "이오", "요"))))
    if c.scene:
        out.append(_p(escape(c.scene.한줄)))
    return out


def _season(c: Claim, f, concern: str, word: str) -> list:
    hot, cold = c.counted[0], c.counted[1]
    out = [_p("그대가 태어난 달의 아래 글자는 %s — 불이 %g개, 물이 %g개요."
              % (escape(_month_ji(f)), hot.값, cold.값))]
    out.append(_p("<b>%s에 났으니 %s</b>"
                  % (escape(_month_ji(f)), escape(c.verdict + "요.")), "bite"))
    out.append(_p("그러니 %s 먼저 채우는 편이 몸에 맞소 — 그것이 겉에 %s."
                  % (josa(EL_WORD.get(f.yongsin, ""), "을", "를"),
                     count_word(topic_mod.visible(f, f.yongsin), "자"))))
    if c.scene:
        out.append(_p(escape(c.scene.한줄)))
    return out


def _birthday(c: Claim, f, concern: str, word: str) -> list:
    per = int(c.counted[0].값)
    gz = next((p["gz"] for p in f.pillars if p["label"] == "일주"), "")
    return [
        _p("그대가 태어난 날 두 글자는 %s — 1만 명에 %d명이 같소."
           % (escape(gz), per)),
        _p("<b>%s</b>" % ("같은 두 글자를 쓰는 사람이 드무니, 같은 자리에서 "
                          "걸린 사람을 만나기 어려웠을 게요."
                          if per <= 150 else
                          "같은 두 글자를 쓰는 사람이 그만큼 있으니, "
                          "그대만 그런 것이 아니오."), "bite"),
    ]


def _forebears(c: Claim, f, concern: str, word: str) -> list:
    a = getattr(f, "ancestor", None) or {}
    els = " · ".join(EL_WORD.get(e, e) for e in (a.get("elements") or []))
    out = [_p("그대가 태어난 해 두 글자는 %s — 기운으로는 %s."
              % (escape(a.get("pillar") or ""),
                 escape(josa(els, "이오", "요")) if els else "모르오"))]
    out.append(_p("<b>그 글자가 그대에게 채우면 좋은 것을 %s — 그래서 "
                  "물려받은 것이 %s.</b>"
                  % ("돕소" if a.get("supports_yongsin") else "돕지 않소",
                     escape(josa(a.get("stance") or "있는 쪽", "이오", "요"))),
                  "bite"))
    out.append(_p("물려받은 결은 %s 쪽이고, 그 두 글자는 %s."
                  % (escape(PLAIN_MISS_R.get(a.get("inherited") or "",
                                             a.get("inherited") or "모르오")),
                     escape(josa_hanja(a.get("pillar") or "", "이오", "요")))))
    if c.scene:
        out.append(_p(escape(c.scene.한줄)))
    return out


def _alone(c: Claim, f, concern: str, word: str) -> list:
    seen, weight = c.counted[0], c.counted[1]
    el = seen.무엇
    out = [_p("겉에 %s %s 있으나 곁에 도울 글자가 없소 — 글자 속까지 %g개요."
              % (josa(el, "이", "가"), count_word(seen.값, "자"), weight.값))]
    out.append(_p("<b>%s 곁에 도울 글자가 없으니 쓰다 마오 — 시작은 그대가 "
                  "하고 끝은 남이 맺은 일이 있었을 것이오.</b>"
                  % josa(el, "은", "는"), "bite"))
    if c.scene:
        out.append(_p(escape(c.scene.한줄)))
    return out


def _missing(c: Claim, f, concern: str, word: str) -> list:
    n = c.counted[0]
    return [
        _p("%s %s에 한 자도 없소."
           % (josa(PLAIN_MISS.get(n.무엇, n.무엇), "이", "가"), _where(f))),
        _p("<b>없는 묶음이 하는 일은 남보다 힘이 더 드오 — 안 한 것이 아니라 "
           "그때그때 만들어 써 왔다는 말이오.</b>", "bite"),
    ]


def _decades(c: Claim, f, concern: str, word: str) -> list:
    """★ 표를 내놓고 읽는 법만 적지 마시오 — 물어보신 자리를 **켭니다**."""
    from ..constants import TEN_GOD_GROUP
    from .axes import _axis_of
    group = _axis_of(concern, getattr(f, "sex", ""))[0]
    # ★ v1 과 **같은 마크업**을 씁니다 (2026-09-28). CSS 는 `.dmap>div` ·
    #   `.dmap .age` · `.dmap b` · `.dmap .now` · `.dmap .lit` 를 봅니다.
    #   제가 처음에 `<span class="d on">` 을 냈는데 그러면 한 줄도 안
    #   먹습니다 — 이 집이 `.dmap` 을 CSS 없이 내려보내 「12庚戌상관」 한
    #   덩이를 낸 그 자리요. 새 꼴을 만들지 말고 있는 꼴에 맞춥니다.
    #
    # ★ 칸 안에는 **나이와 글자만** 둡니다. 십신 이름은 어려운 말이고,
    #   칸 너비가 78px 이라 쉬운 말로 풀면 넘칩니다. 뜻은 바로 아래
    #   형광펜 줄이 말합니다.
    cells = []
    for d in f.daeun:
        lit = TEN_GOD_GROUP.get(d.get("ten_god") or "") == group
        now = d["start_age"] <= f.age < d["start_age"] + 10
        cells.append('<div class="d%s%s"><span class="age">%d</span>'
                     '<b>%s</b></div>'
                     % (" now" if now else "", " lit" if lit else "",
                        d["start_age"], escape(d["gz"])))
    lit = c.counted[1]
    out = [_p("열 해마다 바뀌는 때가 %s — 지금 %s."
              % (josa(count_word(c.counted[0].값, "칸"), "이오", "요"),
                 count_word(f.age, "살")))]
    out.append('<div class="dmap">%s</div>' % "".join(cells))
    if lit.값:
        ages = [d["start_age"] for d in f.daeun
                if TEN_GOD_GROUP.get(d.get("ten_god") or "") == group]
        out.append(_p("<b>물어보신 %s 켜지는 때는 %s이오 — 켠 자리가 %s.</b>"
                      % (josa(word, "이", "가"),
                         " · ".join("%d살" % a for a in ages),
                         count_word(lit.값, "칸")), "bite"))
    else:
        out.append(_p("<b>열 해 표 %s 가운데 물어보신 %s 켜지는 때가 하나도 "
                      "없소 — 그것은 이 표가 아니라 여섯 글자에서 볼 일이오.</b>"
                      % (count_word(c.counted[0].값, "칸"),
                         josa(word, "이", "가")), "bite"))
    out.append('<div class="dmap">%s</div>' % "".join(cells))
    out.append(_p("그 해에 무슨 일이 생긴다는 말이 아니라, 보는 글자가 바뀐다는 "
                  "말이오."))
    if c.scene:
        out.append(_p(escape(c.scene.한줄)))
    return out


def _unknown_hour(c: Claim, f, concern: str, word: str) -> list:
    return [
        _p("그대가 준 것은 해와 달과 날이오 — 세운 글자가 %s."
           % count_word(c.counted[0].값, "자")),
        _p("<b>태어난 시각 두 글자는 비워 두었소. 낮 열두 시로 채우면 글자 "
           "둘이 거짓이 되고, 그러면 기운 개수도 함께 틀리오.</b>", "bite"),
        _p("시각을 알게 되면 여덟 글자로 다시 셀 수 있소."),
    ]


#: 없는 묶음을 쉬운 말로 — `axes.PLAIN_MISS` 와 같은 표를 두지 않게 받아 씁니다.
from .axes import PLAIN_MISS            # noqa: E402

#: 없는 묶음을 되짚는 표 (물려받은 결).
PLAIN_MISS_R = {"재성": "쥐는 결", "관성": "누르고 잡아 주는 결",
                "식상": "밖으로 내놓는 결", "인성": "채워 주는 결",
                "비겁": "같이 나누는 결"}

SHAPES.update({
    "weave": _weave, "marks": _marks, "clash": _clash, "tied": _tied,
    "frame": _frame, "season": _season, "birthday": _birthday,
    "forebears": _forebears, "alone": _alone, "missing": _missing,
    "decades": _decades, "unknown_hour": _unknown_hour,
})
RHYTHM.update({
    "weave": "맞물림", "marks": "이름", "clash": "맞섬", "tied": "묶임",
    "frame": "틀", "season": "철", "birthday": "수하나",
    "forebears": "윗대", "alone": "혼자", "missing": "없는것",
    "decades": "표", "unknown_hour": "장부",
})


# ══════════════════════════════════════════════════════════════════
# 축 ㉕㉖ 의 꼴 — 비싼 자리만 여는 다른 종류 (2026-09-28)
# ══════════════════════════════════════════════════════════════════
def _hindsight(c: Claim, f, concern: str, word: str) -> list:
    """
    ★ 지나온 칸에 **사건을 지어내지 마시오.** 칸을 가리키고 나이를 대는
      데까지요 — 무슨 일이 있었다고 적으면 그건 점이 아니라 소설이오.
    """
    from ..constants import TEN_GOD_GROUP
    from .axes import _axis_of
    grp = _axis_of(concern, getattr(f, "sex", ""))[0]
    past = [d for d in (f.daeun or []) if d["start_age"] + 10 <= f.age]
    rows = [_p("그대가 이미 지나온 때는 %s — 첫 칸이 %s살에 열렸소."
               % (count_word(c.counted[0].값, "칸"), c.counted[1].값))]
    cells = []
    for d in past:
        lit = TEN_GOD_GROUP.get(d.get("ten_god") or "") == grp
        cells.append('<div class="d%s"><span class="age">%d</span>'
                     '<b>%s</b></div>'
                     % (" lit" if lit else "", d["start_age"],
                        escape(d["gz"])))
    rows.append('<div class="dmap">%s</div>' % "".join(cells))
    lit = [d for d in past if TEN_GOD_GROUP.get(d.get("ten_god") or "") == grp]
    if lit:
        rows.append(_p("<b>물어보신 %s 켜졌던 때는 %s이오 — 그 무렵을 "
                       "떠올려 보면 이 풀이가 맞는지 그대가 아오.</b>"
                       % (josa(word, "이", "가"),
                          " · ".join("%d살" % d["start_age"] for d in lit)),
                       "bite"))
    else:
        rows.append(_p("<b>지나온 %s 가운데 물어보신 %s 켜진 때는 없소 — "
                       "그 자리로 힘들었다면 열 해 표가 아니라 여섯 글자에서 "
                       "온 것이오.</b>"
                       % (count_word(len(past), "칸"),
                          josa(word, "이", "가")), "bite"))
    if c.scene:
        rows.append(_p(escape(c.scene.한줄)))
    return rows


def _counter(c: Claim, f, concern: str, word: str) -> list:
    """
    ★ 면책과 다릅니다. 면책은 어떤 관찰에서도 살아남고, 이 컷은 **어떤
      관찰이면 우리가 틀린 것인지**를 수로 적습니다.

    ★ 0 을 문장 한가운데 끼우지 마시오 (2026-09-28). 「겉에 쇠가 한 자도
      없소인데도」 → 「한 자도」 → 둘 다 비문이었습니다. 한국말은 0 일 때
      **풀이말이 달라집니다** — 이어지는 꼴을 따로 짓습니다.
    """
    a, b, d = c.counted[0], c.counted[1], c.counted[2]
    thin, plain = b.무엇, PLAIN_GROUP.get(a.무엇, a.무엇)

    def run(name, n, unit, tail="고"):
        """이어지는 꼴 — 「쇠가 없고」 · 「쇠가 두 자이고」"""
        return ("%s 없%s" % (josa(name, "이", "가"), tail) if n == 0
                else "%s %s이%s" % (josa(name, "이", "가"),
                                   count_word(n, unit), tail))

    def cond(name, n, unit):
        """조건 꼴 — 「쇠가 없는데도」 · 「쇠가 두 자인데도」. 이름이 비면 수만."""
        lead = (josa(name, "이", "가") + " ") if name else ""
        return ("%s없는데도" % lead if n == 0
                else "%s%s인데도" % (lead, count_word(n, unit)))

    rows = [_p("이 풀이는 수 셋을 딛고 섰소 — %s %s, 겉에 %s, %s."
               % (plain, ("없고" if a.값 == 0 else count_word(a.값, "자")),
                  run(thin, b.값, "자"),
                  run("받쳐 주는 글자", d.값, "개", "소")))]
    # ★ 물어보신 자리 글자도 0 일 수 있소 — 「글자 한 자도 없소인데도」 가
    #   스무 장에 나갔습니다. 조건 꼴을 **둘 다** 씁니다.
    rows.append(_p("<b>그러니 이렇다면 우리가 틀린 것이오 — %s %s %s "
                   "손에 남고, 겉에 %s 그 일이 편했다면요.</b>"
                   % (plain, cond("", a.값, "자").lstrip(),
                      josa(word, "이", "가"),
                      cond(thin, b.값, "자")), "bite"))
    rows.append(_p("그때는 여기서 본 것이 아니라 다른 데를 봐야 하오 — "
                   "%s 사람은 흔치 않으니 거기부터 다시 세겠소."
                   % (("받쳐 주는 글자가 없는" if d.값 == 0
                       else "받쳐 주는 글자가 %s인" % count_word(d.값, "개")))))
    if c.scene:
        rows.append(_p(escape(c.scene.한줄)))
    return rows


SHAPES.update({"hindsight": _hindsight, "counter": _counter})
RHYTHM.update({"hindsight": "지나온", "counter": "되짚기"})
