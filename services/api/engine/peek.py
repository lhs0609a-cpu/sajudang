"""
엿보기 — 목패를 고른 뒤, 값을 치르기 전에 보는 자리.

★ 손님이 시킨 것 (2026-09-04)

  "자리 하나든 스무 사람 전부든 누르면 다음에는 각 캐릭터들이 나와서
  «당신에게 가장 중요한 건 ~~» 블러 처리하고, «당신에게 치명적인 건 ~~»
  «당신이 돈 버는 날은 ~~» 이런 식으로 … 너무나 궁금해서 결제 안 하고는
  미칠 정도로."

★ 그런데 블러는 **가림이지 잠금이 아닙니다**

  이 집의 절대 규칙 — 「잠긴 컷은 본문이 아예 안 내려옵니다. 블러로
  가린 게 아니라 서버가 안 줍니다」 (docs/02 §7). 글을 내려보내고
  CSS 로 흐리면 개발자도구에서 그대로 읽힙니다. 값을 치른 사람과
  안 치른 사람이 같은 것을 받는 셈입니다.

  그래서 **앞머리만 진짜로 보내고, 뒤는 서버에 남기고 길이만** 냅니다.
  화면은 그 길이만큼 흐린 칸을 그립니다 — 벗겨도 나올 게 없습니다.

★ 지어내지 않습니다

  질문도 앞머리도 **이미 계산된 그 사람의 컷**에서 나옵니다. 없는
  말을 만들어 궁금하게 하는 것은 이 집이 금지한 것입니다. 여기서
  하는 일은 있는 것을 **가리는 것**뿐입니다.

  그리고 근거 줄은 **가리지 않습니다.** 무엇을 보고 한 말인지는
  값을 치르기 전에도 보여 줍니다 — 그게 이 집의 자리입니다.

★ 브레이크는 그대로입니다

  재촉하지 않습니다. 남은 시간도, 남은 자리도, 지어낸 수도 없습니다.
  궁금함은 **그 사람의 여덟 글자에서** 나와야지 시계에서 나오면 안 됩니다.
"""
from __future__ import annotations

import re
from typing import Optional

from . import lens as lens_mod
from . import lens_cuts as lc_mod
from . import voice as voice_mod
from .report import _BLOCK_TAG, build_report

# 앞머리로 보여 주는 길이 — 조사에서 끊기지 않게 뒤로 물러섭니다.
#
# ★ 맛보기(report._teaser)보다 **짧습니다.** 저기는 페이월에서 「무엇을
#   놓치는지」를 알려 주는 자리라 본문의 40%까지 냅니다. 여기는 목패를
#   고른 사람이 마지막으로 보는 자리라, 문장이 **끊긴 채**로 남아야
#   합니다. 다 읽히면 궁금할 까닭이 없습니다.
HEAD_MAX = 18
HEAD_MIN = 6
BAD_TAIL = "은는이가을를의에서도만과와로으며고나지야한할하며되"

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
# ★ 용어 풀이는 **걷어 냅니다.**
#
#   맛보기 앞머리에 「대운 (십 년마다 읽는 자리가 바뀌는 것)」 이 들어오면
#   열여덟 자를 풀이가 다 먹습니다. 궁금해야 할 자리에 사전이 앉는
#   셈입니다. 풀이는 값을 치른 뒤 본문에서 그대로 나옵니다.
_GLOSS = re.compile(r'<i class="gl">.*?</i>', re.S)
# 태그가 걷힌 뒤 남는 괄호 풀이 — 「대운 (십 년마다 바뀌는 큰 마디)」
_PAREN = re.compile(r"\s*[(（][^)）]{2,}[)）]")
# 맛보기는 잘려 오므로 **닫는 괄호가 없는** 풀이도 걷어야 합니다 —
# 「대운 (십 년마다 바뀌는 큰 마디」 처럼 열린 채로 끝납니다.
_PAREN_OPEN = re.compile(r"\s*[(（][^)）]*$")


def _plain(html: str) -> str:
    # ★ 블록은 띄우고 **인라인은 붙입니다.**
    #
    #   전에는 태그를 전부 빈칸으로 바꿨습니다. 그랬더니 `<b>상관</b>이`
    #   가 「상관 이」로, `<b>불</b>이오` 가 「불 이오」로 나왔습니다 —
    #   조사가 낱말에서 떨어져 나와 손님 눈에 오탈자로 보입니다.
    #   본문 세는 자리(report._plain)는 진작 이렇게 하고 있었습니다.
    t = _GLOSS.sub("", html or "")
    t = _TAG.sub("", _BLOCK_TAG.sub(" ", t))
    t = _PAREN_OPEN.sub("", _PAREN.sub("", t))
    return _WS.sub(" ", t).strip()


def _head(text: str) -> tuple[str, int]:
    """
    앞머리와 **가릴 글자 수**.

    가릴 글자는 돌려주지 않습니다. 길이만 냅니다 — 화면은 그만큼
    흐린 칸을 그립니다.
    """
    text = text.strip()
    if len(text) <= HEAD_MIN:
        return "", len(text)
    head = text[:HEAD_MAX].rstrip()
    while len(head) > HEAD_MIN and head[-1] in BAD_TAIL:
        head = head[:-1].rstrip()
    if len(head) < HEAD_MIN:
        head = text[:HEAD_MIN]
    return head, max(1, len(text) - len(head))


# ── 무엇을 묻는가 ─────────────────────────────────────────
#
# ★ 컷 제목을 **손님의 말**로 바꿉니다.
#
#   컷 제목은 이 집이 쓰는 말입니다 — 「5 · 필요한 것」. 그건 목차지
#   물음이 아닙니다. 손님이 궁금해할 꼴로 바꿔 묻되, **없는 것을
#   묻지는 않습니다** — 그 컷이 실제로 답하는 것만 묻습니다.
ASK = {
    "daeun_now": "그대가 지금 서 있는 자리는",
    "yongsin": "그대에게 모자란 것은",
    "lack": "그대에게 아예 없는 것은",
    "why": "왜 하필 지금 그대인가 하면",
    "rarity": "만 명 중 그대 같은 사람은",
    "place": "그대의 돈과 사람이 도는 자리는",
    "axis": "그대의 넉 자와 여덟 글자가 어긋난 자리는",
    "sinsal": "그대 곁에 선 이름들은",
    "helper": "그대를 돕는 사람이 오는 쪽은",
    "ancestor": "그대가 고른 적 없이 받은 것은",
    "daeun_map": "그대의 판이 바뀌는 나이는",
    "week": "그대가 이번 주에 하실 한 가지는",
    "closing_cut": "그대가 오늘 하나만 고른다면",
    "chart": "그대의 여덟 글자는",
    "place_now": "지금 그대에게 도는 자리는",
}


# ★ 관점 컷은 **축으로** 묻습니다 (2026-09-04).
#
#   손님이 짚은 것 — "이 부분은 당신한테 하는 말이어야지, 뭔 말이야 이게."
#
#   관점 컷의 제목은 그 캐릭터가 **제 보는 법**에 붙인 이름입니다 —
#   「뿌리가 있는가」 「격을 잡는다」 「덥고 마른가, 춥고 젖은가」. 목차로는
#   맞지만 손님에게 하는 물음이 아닙니다. 넉 줄이 나란히 서면 스무 사람이
#   자기 소개를 하고 있고, 손님 얘기는 한 줄도 없습니다.
#
#   그렇다고 예순아홉 가지 제목마다 물음을 손으로 지어내면 그건 **없는
#   말을 만드는 것**입니다. 대신 그 컷이 **실제로 재는 자리**(첫 축)로
#   묻습니다. 축은 스물넷뿐이고, 축이 곧 답하는 것이라 지어낼 것이 없습니다.
ASK_AXIS = {
    "deuk": "그대가 딛고 선 땅은",
    "top_ten_god": "그대를 끌고 가는 힘은",
    "daeun_phase": "그대가 지금 서 있는 마디는",
    "daeun_ten_god": "지금 대운이 그대에게 시키는 것은",
    "next_daeun_tg": "그대의 다음 마디가 가져오는 것은",
    "year_ji": "그대가 고른 적 없이 물려받은 것은",
    "month_ji": "그대가 난 철이 정해 준 것은",
    "ilji_state": "그대 발밑 자리는",
    "score_band": "그대의 힘이 센지 여린지는",
    "strength": "그대가 미는 쪽인지 밀리는 쪽인지는",
    "weak_el": "그대에게 모자란 것은",
    "strong_el": "그대에게 넘치는 것은",
    "yongsin": "그대에게 있어야 할 것은",
    "zero_band": "그대의 여덟 글자에서 빈 칸은",
    "gap_band": "그대의 치우침이 얼마나 큰가는",
    "flow": "그대의 힘이 빠져나가는 쪽은",
    "gwan_jae": "그대의 일과 돈이 놓인 자리는",
    "age_band": "지금 그대 나이가 놓인 칸은",
    "season": "그대가 난 철은",
    "johu": "그대의 여덟 글자가 추운지 더운지는",
    "seupjo": "그대의 여덟 글자가 젖었는지 말랐는지는",
    "sinsal_mark": "그대 곁에 선 이름들은",
    "palace": "그대의 네 자리 중 무거운 곳은",
    "hour_known": "그대의 시주를 아는 것이 가르는 것은",
}


def ask_of(cut_id: str, title: str) -> str:
    """물음. 모르는 컷이면 제목을 그대로 씁니다 — 지어내지 않습니다."""
    if cut_id in ASK:
        return ASK[cut_id]
    got = ASK_AXIS.get(lc_mod.axis_of(cut_id) or "")
    if got:
        return got
    # 「4 · 지금 어디에」 → 「지금 어디에」
    t = re.sub(r"^\s*[\d.]+\s*·\s*", "", title or "").strip()
    return t or "이 자리는"


# ── 앞머리는 **손님 얘기**부터 ───────────────────────────
#
#   관점 컷은 여는 말이 화자 얘기입니다 — 「나는 뿌리부터 보오」
#   「나는 십신을 세지 않소」 「나는 때를 보는 사람입니다」. 맛보기는 컷의
#   앞 40%를 자르니 **여는 말만** 잘려 나왔고, 그래서 엿보기 넉 줄이
#   전부 자기 소개였습니다.
#
#   그래서 여는 말만큼을 건너뛰고, 그 뒤에서 **손님을 부르는 문장**을
#   먼저 고릅니다. 없으면 여는 말 다음 문장을 그대로 씁니다 — 지어내지
#   않습니다.
_SENT = re.compile(r"[^.!?…]+[.!?…]*")
# 손님을 부르는 문장을 찾을 때 몇 문장까지 보는가. 더 뒤로 가면 앞뒤가
# 잘린 채 혼자 서게 됩니다.
LOOK_AHEAD = 4


def _sentences(text: str) -> list:
    return [m.group(0).strip() for m in _SENT.finditer(text or "")
            if m.group(0).strip()]


def _about_you(cut_id: str, body: str, you: str) -> str:
    """이 컷에서 **손님에게 하는 첫 문장.**"""
    sents = _sentences(body)
    if not sents:
        return ""
    skip = len(_sentences(_plain(lc_mod.lead_of(cut_id))))
    rest = sents[skip:] or sents
    for sent in rest[:LOOK_AHEAD]:
        if you and you in sent:
            return sent
    return rest[0]


def build_peek(f, chart_id: str, lens_ids: list, concern: str,
               axis4: Optional[str] = None, limit: int = 6) -> list:
    """
    이 목패가 여는 자리들 — 물음과 **가려진 답**.

    lens_ids  이 목패로 열리는 사람들. 「이 자리 하나」면 한 사람.
    limit     한 화면에 몇 줄까지. 다 보여 주면 목록이지 엿보기가
              아닙니다.

    돌려주는 것
        lens_id · lens_name   누가 하는 말인가
        ask                   무엇을 묻는가 (그 컷이 실제로 답하는 것)
        head                  답의 **앞머리** — 진짜 글, 조사에서 안 끊김
        mask                  가린 글자 수. 글자 자체는 안 보냅니다.
        source                근거 줄 — 가리지 않습니다
        chars                 그 컷 전체 길이
    """
    rows: list = []
    for lid in lens_ids:
        rep = build_report(f, chart_id, lid, "free", concern, axis4)
        name = (rep.get("lens") or {}).get("name") or lid
        # ★ 앞머리는 **본문**에서 뽑습니다 (2026-09-04).
        #
        #   맛보기(teaser)는 컷의 앞 40%를 자른 것이라 관점 컷에서는
        #   **여는 말**만 옵니다 — 화자가 제 보는 법을 말하는 자리입니다.
        #   손님 얘기는 그 뒤에 있으니 본문을 봐야 찾습니다.
        #
        #   본문은 **서버에서만** 봅니다. 나가는 것은 열여덟 자 앞머리와
        #   가린 글자 **수**뿐이라 잠금은 그대로입니다 — 이 집의 규칙은
        #   「본문을 안 내려보낸다」이지 「본문을 안 읽는다」가 아닙니다.
        full = build_report(f, chart_id, lid, "all", concern, axis4)
        body_of = {c.get("id"): c.get("html") for c in (full.get("cuts") or [])}
        you = lens_mod.you_of(lid, "", getattr(f, "sex", None))
        got = rep.get("locked") or []
        # ★ 여러 사람을 엿볼 때는 **그 사람만 보는 자리**를 먼저 냅니다.
        #
        #   공통 컷은 스무 명이 같은 자리를 봅니다. 그걸 앞에 내면
        #   네 사람이 「지금은 庚申 대운이오」 를 나란히 말합니다 —
        #   궁금해지기는커녕 «다 같은 것» 으로 보입니다. 관점 컷(lc_)이
        #   그 사람을 산 까닭 그 자체이니 그것부터 냅니다.
        if len(lens_ids) > 1:
            own = [c for c in got if str(c.get("id") or "").startswith("lc_")]
            rest = [c for c in got if not str(c.get("id") or "").startswith("lc_")]
            got = own + rest
        for c in got:
            cid = c.get("id") or ""
            body = _about_you(cid, _plain(body_of.get(cid) or ""), you)
            if not body:
                # 본문을 못 찾으면 맛보기로 물러섭니다 — 비우지 않습니다.
                body = _plain(c.get("teaser") or "")
            if not body:
                continue
            head, _ = _head(body)
            if not head:
                continue
            # ★ 가리는 것은 **컷 전체**입니다.
            #
            #   맛보기 길이로 재면 「1자 가림」 같은 것이 나옵니다 —
            #   실제로 안 보이는 것은 이백 자가 넘는데요. 손님이 무엇을
            #   못 보고 있는지 알아야 값을 잽니다. 글자는 안 보냅니다.
            mask = max(1, int(c.get("chars") or 0) - len(head))
            rows.append({
                "lens_id": lid,
                "cut_id": cid,
                "lens_name": name,
                # ★ 물음도 **그 사람이 부르는 말**로 냅니다. 표에는
                #   「그대」 한 벌로 적어 두고 여기서 갈아 끼웁니다 —
                #   물음은 「그대」인데 답은 「자네」면 한 상자 안에서
                #   부르는 사람이 둘이 됩니다.
                "ask": voice_mod.address(ask_of(cid, c.get("title") or ""), you),
                "head": head,
                "mask": mask,
                "source": c.get("source"),
                "chars": c.get("chars"),
            })
    # ★ 한 사람이 목록을 다 차지하지 않게 **돌려 가며** 뽑습니다.
    #   스무 사람 전부를 산 사람에게 한 사람 것만 여섯 줄 보이면
    #   무엇을 샀는지 안 보입니다.
    #
    # ★ 같은 것을 두 사람이 묻지 않게 합니다. 축으로 묻게 되면서 서로
    #   다른 컷이 같은 물음에 닿을 수 있게 됐습니다 — 「그대에게 모자란
    #   것은」 이 두 줄 나란히 서면 그건 두 사람이 아니라 한 사람입니다.
    out: list = []
    seen: dict = {}
    asked: set = set()
    while rows and len(out) < limit:
        moved = False
        for lid in lens_ids:
            pool = [r for r in rows if r["lens_id"] == lid]
            i = seen.get(lid, 0)
            while i < len(pool) and pool[i]["ask"] in asked:
                i += 1
            if i < len(pool) and len(out) < limit:
                out.append(pool[i])
                asked.add(pool[i]["ask"])
                seen[lid] = i + 1
                moved = True
            else:
                seen[lid] = i
        if not moved:
            break
    return out


# ── 사람들이 제일 궁금해하는 네 가지 ─────────────────────────
#
# ★ 손님이 시킨 것 (2026-09-04)
#
#   "여기에 사람들이 제일 궁금한 재물, 사랑, 연애, 운명 이런 거 넣어야지.
#    안 편 자리가 궁금해야지 미친듯이."
#
# ★ 무엇이 잘못돼 있었나
#
#   무료 6단이 끝나는 자리에서 안 편 자리를 이렇게 불렀습니다 —
#       「4 · 지금 어디에」 「5 · 필요한 것」 「6 · 대운 맵」
#   이건 **목차**입니다. 이 집이 컷을 세는 말이지 손님이 궁금해하는
#   말이 아닙니다. 「대운 맵」이 뭔지 모르는 사람에게 「대운 맵이
#   남았소」는 아무것도 안 남깁니다.
#
# ★ 그렇다고 없는 말을 지어내지 않습니다
#
#   네 자리는 전부 **그 사람의 여덟 글자에서 센 것**으로 엽니다 —
#   재성 개수, 배우자 자리에 앉은 글자, 남은 대운 마디 수, 이름 붙은
#   자리 수. 넷 다 셀 수 있고 대 볼 수 있습니다. 그 뒤의 답만
#   가립니다(길이만 냅니다). 궁금함은 시계가 아니라 그 사람의 명식에서
#   나와야 합니다.
#
# ★ 답을 들고 있는 컷이 이미 열려 있으면 그 자리는 **뺍니다.**
#   벽 뒤에 없는 것을 벽 뒤에 있는 척하지 않습니다.

def _jae(f) -> int:
    """재성 — 편재 + 정재. 여덟 글자 안에서 돈이 도는 글자."""
    tg = getattr(f, "ten_gods", None) or {}
    return int(tg.get("편재", 0)) + int(tg.get("정재", 0))


def _spouse_pic(f) -> str:
    """배우자 자리(일지)에 앉은 글자를 사람 말로. 못 읽으면 빈 말."""
    from .terms import JI_PIC
    p = JI_PIC.get(getattr(f, "day_ji", "") or "")
    return p[0] if p else ""


def _turns_left(f) -> tuple:
    """남은 대운 마디 수와 **다음 마디가 서는 나이**."""
    daeun = list(getattr(f, "daeun", None) or [])
    now = int(getattr(f, "daeun_now", 0) or 0)
    left = max(0, len(daeun) - now - 1)
    nxt = None
    if now + 1 < len(daeun):
        nxt = daeun[now + 1].get("start_age")
    return left, nxt


def _wants_spec(f) -> list:
    """(자리 이름, 여는 사실, 그 답을 든 컷을 고르는 차례)"""
    jae = _jae(f)
    pic = _spouse_pic(f)
    left, nxt = _turns_left(f)
    n_ss = len(getattr(f, "sinsal", None) or [])

    out = [
        ("재물",
         ("여덟 글자에 <b>재물 글자(재성)</b>가 <b>하나도 없소.</b>"
          if jae == 0 else
          "여덟 글자에 <b>재물 글자(재성)</b>가 <b>%d개</b> 있소." % jae),
         ["place", "_bowl", "_road", "_tide"]),
    ]
    if pic:
        out.append((
            "사랑",
            "배우자 자리(일지)에 앉은 것은 <b>%s</b>(%s)이오." % (f.day_ji, pic),
            ["_seat", "_room", "_tie", "_house"]))
    if left and nxt:
        out.append((
            "운명",
            "판이 바뀌는 마디가 <b>%d번</b> 남았고, 다음은 <b>%d세</b>요." % (left, nxt),
            ["daeun_map", "daeun_now", "_turn", "_age"]))
    if n_ss:
        out.append((
            "사람",
            "그대 곁에 <b>이름 붙은 자리</b>가 <b>%d개</b> 서 있소." % n_ss,
            ["helper", "_side", "_beside", "_seat"]))
    return out


def build_wants(f, locked: list, limit: int = 4,
                voice: Optional[str] = None, you: Optional[str] = None) -> list:
    """
    네 자리 — 재물 · 사랑 · 운명 · 사람.

    locked  `report.build_report` 가 낸 잠긴 컷 목록. 여기서 **다시
            리포트를 세우지 않습니다** — 같은 것을 두 번 세면 두 값이
            갈립니다.

    돌려주는 것
        want   자리 이름 (재물 · 사랑 · 운명 · 사람)
        fact   여는 사실 — 그 사람의 여덟 글자에서 **센 것**
        ask    무엇을 묻는가
        head   답의 앞머리 — 진짜 글
        mask   가린 글자 수. 글자 자체는 안 보냅니다.
        source 근거 줄 — 가리지 않습니다
        chars  그 컷 전체 길이
    """
    by_id = {str(c.get("id") or ""): c for c in (locked or [])}
    used: set = set()
    rows: list = []

    def pick(order):
        for key in order:
            if key.startswith("_"):
                # 관점 컷은 캐릭터마다 id 가 다릅니다 — 꼬리로 찾습니다.
                for cid, c in by_id.items():
                    if cid.endswith(key) and cid not in used:
                        return cid, c
            elif key in by_id and key not in used:
                return key, by_id[key]
        return None, None

    for want, fact, order in _wants_spec(f):
        cid, c = pick(order)
        if not c:
            continue                      # 벽 뒤에 없으면 안 겁니다
        body = _plain(c.get("teaser") or "")
        if not body:
            continue
        head, _ = _head(body)
        if not head:
            continue
        used.add(cid)
        # ★ 여기도 **하오체 한 벌 · 「그대」 한 벌**로 적고 갈아 끼웁니다.
        #   묻는 말은 「그대」인데 답은 「자네」면 한 상자에 부르는 사람이
        #   둘이 됩니다 (tests/test_peek).
        rows.append({
            "want": want,
            "fact": voice_mod.speak(voice_mod.address(fact, you), voice),
            "ask": voice_mod.address(ask_of(cid, c.get("title") or ""), you),
            "head": head,
            "mask": max(1, int(c.get("chars") or 0) - len(head)),
            "source": c.get("source"),
            "chars": c.get("chars"),
        })
        if len(rows) >= limit:
            break
    return rows
