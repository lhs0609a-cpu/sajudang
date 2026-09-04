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

from .report import build_report

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
    t = _TAG.sub(" ", _GLOSS.sub("", html or ""))
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
    "why": "왜 하필 지금인가 하면",
    "rarity": "만 명 중 그대 같은 사람은",
    "place": "그대의 돈과 사람이 도는 자리는",
    "axis": "넉 자와 여덟 글자가 어긋난 자리는",
    "sinsal": "그대 곁에 선 이름들은",
    "helper": "그대를 돕는 사람이 오는 쪽은",
    "ancestor": "그대가 고른 적 없이 받은 것은",
    "daeun_map": "읽는 자리가 바뀌는 나이는",
    "week": "이번 주에 하실 한 가지는",
    "closing_cut": "오늘 하나만 고르라면",
    "chart": "그대의 여덟 글자는",
    "place_now": "지금 도는 자리는",
}


def ask_of(cut_id: str, title: str) -> str:
    """물음. 모르는 컷이면 제목을 그대로 씁니다 — 지어내지 않습니다."""
    if cut_id in ASK:
        return ASK[cut_id]
    # 「4 · 지금 어디에」 → 「지금 어디에」
    t = re.sub(r"^\s*[\d.]+\s*·\s*", "", title or "").strip()
    return t or "이 자리는"


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
                "lens_name": name,
                "ask": ask_of(c.get("id") or "", c.get("title") or ""),
                "head": head,
                "mask": mask,
                "source": c.get("source"),
                "chars": c.get("chars"),
            })
    # ★ 한 사람이 목록을 다 차지하지 않게 **돌려 가며** 뽑습니다.
    #   스무 사람 전부를 산 사람에게 한 사람 것만 여섯 줄 보이면
    #   무엇을 샀는지 안 보입니다.
    out: list = []
    seen: dict = {}
    while rows and len(out) < limit:
        moved = False
        for lid in lens_ids:
            pool = [r for r in rows if r["lens_id"] == lid]
            i = seen.get(lid, 0)
            if i < len(pool) and len(out) < limit:
                out.append(pool[i])
                seen[lid] = i + 1
                moved = True
        if not moved:
            break
    return out
