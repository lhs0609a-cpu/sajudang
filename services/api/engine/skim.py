# -*- coding: utf-8 -*-
"""
훑어읽기 층 — **글자는 한 자도 안 바꾸고 태그만 단다.**

★ 손님이 짚었습니다 (2026-09-07)

  "전체 글 다 안 읽을거니까 중요한 워딩 밑줄치고 강조표시해서,
   그것만 읽어도 다 이해가 되게끔."

  19,900원짜리 한 장이 29컷 12,582자입니다. 그런데 이 글에는 **크기가
  하나**뿐이었습니다 — 굵게. 그것도 절반은 낱말에 붙어 있어, 굵은
  데만 이어 읽으면 「癸酉 · 일 · 관성 · 戌」 같은 색인이 나왔습니다.
  요약이 아닙니다.

★ 넷을 두되 뜻이 겹치지 않게 (styles/overrides.css 와 한 벌)

      <b>      센 사실       지금 있던 것. 여기서 안 건드립니다
      <mark>   그 컷의 결론   이것만 이으면 요약이 된다
      <u>      손님이 할 것   처방 · 고를 것
      .nu      나이·해·갯수   틀릴 수 없는 말을 피한 자리

★ 왜 두 번에 나눠 부르는가

  밑줄은 처방 어미(「…시오」)를 찾는데, 그 어미는 **말투 층이 캐릭터
  마다 갈아 끼웁니다** (하오체 「보시오」 · 해요체 「보세요」). 그래서
  자리는 갈리기 **전**에 잡고(`find_do`), 태그는 전부 끝난 **뒤**에
  답니다(`mark`). 지문은 문장 앞머리라 어미가 갈려도 다시 찾습니다.

★ 안 건드리는 것

  · 태그 안 (속성값에 손대면 화면이 깨집니다)
  · 낱말 풀이 `<i class="gl">(…)</i>` 안 — 그건 우리가 끼워 넣은
    말이라 손님의 글이 아닙니다
  · 본문이 아닌 상자 (`side` · `fig` · `gls`) — 밑줄이 사방에 있으면
    밑줄이 아무 말도 안 합니다
  · 태그가 걸쳐 있는 자리. 여는 태그가 밖에 있고 닫는 태그가 안에
    있으면 감싸지 않고 지나갑니다 — 화면을 깨뜨리느니 안 긋습니다
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

# 낱말 풀이는 통째로 한 덩이. 태그보다 **먼저** 잡아야 안이 안 열립니다.
_PIECE = re.compile(r'<i class="gl">.*?</i>|<[^>]+>', re.S)
_TALE = re.compile(r'(<p class="tale">)(.*?)(</p>)', re.S)
_END = re.compile(r"[.!?…]")
# 뱅크의 시키는 말 — 하오체 한 벌입니다. 여기서만 찾고, 화면에 나갈
# 때는 캐릭터 어미로 갈려 있습니다.
_DO = re.compile(r"시오[.!?]?$")
_DIGIT = re.compile(r"\d+")
_SELF = re.compile(r"<(br|hr|img|input)\b[^>]*>", re.I)


# ══════════════════════════════════════════════════════════
# 조각내기 — 글과 태그를 갈라 두고 자리를 센다
# ══════════════════════════════════════════════════════════
def _atoms(inner: str) -> List[dict]:
    """{"kind": text|tag|opaque, "s": 원문}. text 만 글자로 셉니다."""
    out, i = [], 0
    for m in _PIECE.finditer(inner):
        if m.start() > i:
            out.append({"kind": "text", "s": inner[i:m.start()]})
        tag = m.group(0)
        out.append({"kind": "opaque" if tag.startswith('<i class="gl">')
                    else "tag", "s": tag})
        i = m.end()
    if i < len(inner):
        out.append({"kind": "text", "s": inner[i:]})
    return out


def _plain(atoms: List[dict]) -> str:
    return "".join(a["s"] for a in atoms if a["kind"] == "text")


def _sentences(plain: str) -> List[Tuple[int, int]]:
    """
    (시작, 끝) — 끝은 문장부호를 포함합니다.

    ★ 앞뒤 빈칸은 뺍니다. 넣으면 밑줄이 빈칸에서 시작해 앞 문장에
      붙은 것처럼 보입니다.
    """
    out, start = [], 0
    marks = [m.end() for m in _END.finditer(plain)] + [len(plain)]
    for end in marks:
        if end <= start:
            continue
        body = plain[start:end]
        if body.strip():
            lead = len(body) - len(body.lstrip())
            tail = len(body) - len(body.rstrip())
            out.append((start + lead, end - tail))
        start = end
    return out


def _norm(s: str) -> str:
    """지문용 — 사이 띄운 것과 태그가 갈려도 같은 글로 보게."""
    return re.sub(r"\s+", "", s)


def _balanced(atoms: List[dict], a: int, b: int) -> bool:
    """[a, b) 안에서 태그가 스스로 닫히는가. 걸쳐 있으면 안 감쌉니다."""
    depth = 0
    for at in atoms[a:b]:
        if at["kind"] != "tag":
            continue
        t = at["s"]
        if _SELF.match(t):
            continue
        if t.startswith("</"):
            depth -= 1
            if depth < 0:
                return False
        else:
            depth += 1
    return depth == 0


def _cut_at(atoms: List[dict], pos: int) -> int:
    """글자 자리 pos 를 조각 경계로 만들고, 그 앞 조각 번호를 준다."""
    seen = 0
    for i, at in enumerate(atoms):
        if at["kind"] != "text":
            continue
        n = len(at["s"])
        if seen + n < pos:
            seen += n
            continue
        off = pos - seen
        if off == 0:
            return i
        if off == n:
            return i + 1
        atoms[i:i + 1] = [{"kind": "text", "s": at["s"][:off]},
                          {"kind": "text", "s": at["s"][off:]}]
        return i + 1
    return len(atoms)


def _wrap(atoms: List[dict], s: int, e: int, open_t: str, close_t: str) -> bool:
    """글자 [s, e) 를 감싼다. 태그가 걸쳐 있으면 안 감싸고 False."""
    # ★ 앞을 먼저 가릅니다. 뒤를 먼저 가르면 앞을 가르는 순간 조각이
    #   하나 늘어 뒤 번호가 한 칸씩 밀립니다 — 태그가 엉뚱한 데 붙습니다.
    i = _cut_at(atoms, s)
    j = _cut_at(atoms, e)
    if i > j:
        return False
    if not _balanced(atoms, i, j):
        return False
    atoms.insert(j, {"kind": "tag", "s": close_t})
    atoms.insert(i, {"kind": "tag", "s": open_t})
    return True


# ══════════════════════════════════════════════════════════
# 처방 자리 — 말투가 갈리기 **전에** 잡는다
# ══════════════════════════════════════════════════════════
def find_do(html: str) -> Optional[str]:
    """
    손님이 할 것(처방)이 적힌 문장의 **지문**. 없으면 None.

    지문은 문장 앞머리입니다 — 뒤쪽 어미는 캐릭터마다 갈리므로
    그 자리를 빼고 잡습니다.
    """
    if not html:
        return None
    found = None
    for m in _TALE.finditer(html):
        atoms = _atoms(m.group(2))
        plain = _plain(atoms)
        for s, e in _sentences(plain):
            body = plain[s:e].strip()
            if len(body) > 4 and _DO.search(body):
                found = body            # 여럿이면 마지막 것
    if not found:
        return None
    key = _norm(found)
    head = key[:-4] if len(key) > 8 else key[:max(len(key) // 2, 1)]
    return head or None


# ══════════════════════════════════════════════════════════
# 태그 달기 — 전부 끝난 **뒤에**
# ══════════════════════════════════════════════════════════
def mark(html: str, do_spot: Optional[str] = None) -> str:
    """
    밑줄 · 형광펜 · 수. 글자는 그대로 두고 태그만 답니다.

    ★ 형광펜은 **컷마다 한 줄**입니다. 여럿이면 형광펜이 아니라 배경이
      되어 아무 말도 안 합니다. 그 컷 본문의 마지막 문장을 씁니다 —
      이 집의 컷은 결론으로 끝맺습니다.
    """
    if not html:
        return html

    spans = list(_TALE.finditer(html))
    if not spans:
        return html
    last_tale = spans[-1].start()
    already_marked = "<mark" in html
    out, at = [], 0

    for m in spans:
        atoms = _atoms(m.group(2))
        plain = _plain(atoms)
        sents = _sentences(plain)
        used: Optional[Tuple[int, int]] = None

        # ── 밑줄 — 손님이 할 것 ──
        if do_spot and "<u>" not in html:
            for s, e in sents:
                if _norm(plain[s:e]).startswith(do_spot):
                    if _wrap(atoms, s, e, "<u>", "</u>"):
                        used = (s, e)
                        do_spot = None      # 한 장에 한 줄
                    break

        # ── 형광펜 — 그 컷의 결론 ──
        if (not already_marked and sents and m.start() == last_tale
                and sents[-1] != used):
            s, e = sents[-1]
            if e - s >= 6:
                _wrap(atoms, s, e, "<mark>", "</mark>")

        # ── 수 — 나이 · 해 · 갯수 ──
        for a in atoms:
            if a["kind"] == "text":
                a["s"] = _DIGIT.sub(r'<span class="nu">\g<0></span>', a["s"])

        out.append(html[at:m.start()])
        out.append(m.group(1) + "".join(a["s"] for a in atoms) + m.group(3))
        at = m.end()

    out.append(html[at:])
    return "".join(out)
