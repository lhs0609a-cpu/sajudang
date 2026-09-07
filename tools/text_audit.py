# -*- coding: utf-8 -*-
"""
글 감사 — **어색한 글자·조사·낮추는 말**을 한자리에서 찾는다.

    python tools/text_audit.py

★ 손님이 짚은 것 (2026-09-07)

    「풍운도령가 종이를 덮었다.」

  「령」에는 받침이 있으니 **「풍운도령이」** 라야 합니다. 화면이
  `${lens.name}가` 라고 손으로 박아 두어, 스무 사람 중 받침 없는
  이름(몽화·화경·연담·훈장…)만 맞고 나머지는 전부 틀렸습니다.

★ 왜 되풀이되나

  서버에는 조사 도우미가 있습니다 (`bank.josa` · `lens_cuts._fmt` ·
  `topic._fmt`). **화면에는 없습니다.** 그래서 서버 문장은 맞고
  화면 문장만 틀립니다 — 같은 집에서 두 규칙이 도는 셈입니다.

★ 무엇을 잡나

  ① 화면(tsx·ts)에서 `${…}` 바로 뒤에 붙은 조사
  ② 어디서든 **캐릭터 이름 + 틀린 조사** (풍운도령가 · 몽화이 …)
  ③ 뱅크·화면글에서 `{자리표시}` 뒤에 붙은 조사 중 `_fmt` 를
     안 거치는 파일
  ④ **보이지 않는 글자** — 너비 없는 빈칸 · BOM · 전각 빈칸
     (NBSP 는 뺍니다 — 이 집이 과부 줄을 막는 데 **일부러** 씁니다)
  ⑤ **손님을 낮추는 말** — 「흔한 자리요」 처럼 세어 준 것이 아니라
     깎아내린 것으로 읽히는 낱말

  ①②④⑤ 는 버그입니다. ③은 그 파일이 `_fmt` 를 타면 괜찮으므로
  «봐 둘 것» 으로만 냅니다.

★ ④ 에서 NBSP 를 뺀 까닭

  처음에는 NBSP 도 「보이지 않는 글자」로 세어 여덟 자를 지웠습니다.
  그랬더니 `tests/test_widow.py` 가 **과부 줄 넷**을 잡았습니다 —
  그 빈칸들은 실수가 아니라 **마지막 줄에 조각만 남는 것을 막는**
  자리였습니다. 되돌렸습니다.

  교훈: 안 보이는 글자라고 다 쓰레기가 아닙니다. 지우기 전에
  무엇이 그걸 지키고 있는지 봐야 합니다.

★ ⑤ 는 왜 버그인가

  손님이 짚었습니다 — "흔함 이런거 기분나쁠 수 있는거 싹 다 없애."
  값을 치른 직후에 「흔한 자리요」를 들으면 세어 준 것이 아니라
  깎인 것으로 읽힙니다. **감추지는 않습니다** — 「같은 자리에 선
  사람이 많은 쪽이오」 라고 같은 사실을 그대로 냅니다.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

# 받침에 따라 갈리는 조사 짝. (받침 있을 때, 없을 때)
PAIRS = [
    ("이", "가"), ("은", "는"), ("을", "를"), ("과", "와"),
    ("으로", "로"), ("이오", "요"), ("이라", "라"), ("이며", "며"),
    ("이고", "고"), ("아", "야"), ("이여", "여"), ("이랑", "랑"),
]
_ALL = sorted({j for p in PAIRS for j in p}, key=len, reverse=True)


def batchim(word: str) -> bool | None:
    """마지막 글자에 받침이 있는가. 한글이 아니면 None."""
    for ch in reversed(word):
        if "가" <= ch <= "힣":
            return (ord(ch) - 0xAC00) % 28 != 0
        if ch.isalnum():
            return None
    return None


def right(word: str, josa: str) -> str | None:
    """이 자리에 와야 하는 조사. 판정 못 하면 None."""
    b = batchim(word)
    if b is None:
        return None
    for hard, soft in PAIRS:
        if josa in (hard, soft):
            return hard if b else soft
    return None


# ── 캐릭터 이름 ────────────────────────────────────────────
def lens_names() -> list:
    raw = json.loads((ROOT / "seed" / "lenses.json").read_text("utf-8"))
    ls = raw["lenses"] if isinstance(raw, dict) and "lenses" in raw else raw
    ls = ls if isinstance(ls, list) else list(ls.values())
    return [l["name"] for l in ls]


# ── ① 화면의 `${…}` 뒤 조사 ────────────────────────────────
_TPL = re.compile(r"\$\{[^{}]{1,80}\}(" + "|".join(_ALL) + r")(?![가-힣])")
# ── ③ 뱅크의 `{자리표시}` 뒤 조사 ──────────────────────────
_PH = re.compile(r"\{[a-zA-Z_][a-zA-Z0-9_]{0,30}\}(" + "|".join(_ALL) + r")(?![가-힣])")


def scan_screens() -> list:
    out = []
    for p in sorted((ROOT / "apps" / "web").rglob("*.ts*")):
        if "node_modules" in p.parts:
            continue
        for i, line in enumerate(p.read_text("utf-8").splitlines(), 1):
            # 주석은 건너뜁니다 — 버그를 적어 둔 글이 버그로 잡힙니다.
            if line.lstrip().startswith(("*", "//", "/*")):
                continue
            for m in _TPL.finditer(line):
                out.append((p.relative_to(ROOT), i, m.group(0), line.strip()[:90]))
    return out


def scan_names() -> list:
    names = lens_names()
    pat = re.compile("(" + "|".join(re.escape(n) for n in names) + ")("
                     + "|".join(_ALL) + r")(?![가-힣])")
    out = []
    targets = list((ROOT / "apps" / "web").rglob("*.ts*")) + \
        list((ROOT / "seed").glob("*.json"))
    for p in sorted(targets):
        if "node_modules" in p.parts:
            continue
        for i, line in enumerate(p.read_text("utf-8").splitlines(), 1):
            # 주석은 건너뜁니다 — 버그를 적어 둔 글이 버그로 잡힙니다.
            if line.lstrip().startswith(("*", "//", "/*")):
                continue
            for m in pat.finditer(line):
                name, j = m.group(1), m.group(2)
                want = right(name, j)
                if want and want != j:
                    out.append((p.relative_to(ROOT), i, name + j,
                                name + want, line.strip()[:90]))
    return out


def scan_bank() -> list:
    out = []
    for p in sorted((ROOT / "seed").glob("*.json")):
        for i, line in enumerate(p.read_text("utf-8").splitlines(), 1):
            for m in _PH.finditer(line):
                out.append((p.name, i, m.group(0)))
    return out


# ── ④ 보이지 않는 글자 ────────────────────────────────────
# ★ NBSP( )는 **여기 넣지 않습니다** (2026-09-07).
#
#   이 집은 그것을 **일부러** 씁니다 — 문단 마지막 줄에 조각만 남는
#   과부 줄을 막는 자리입니다 (`tools/widow.py` · `tests/test_widow.py`).
#   제가 「보이지 않는 글자」로 잘못 알고 여덟 자를 지웠다가 과부 줄
#   넷을 만들었습니다. 도구가 도구를 부순 셈입니다.
#
#   나머지 넷은 쓸 자리가 없습니다.
INVISIBLE = {
    "​": "너비 없는 빈칸",
    "﻿": "BOM",
    "　": "전각 빈칸",
    " ": "줄 구분자",
    "­": "소프트 하이픈",
}


def scan_invisible() -> list:
    out = []
    targets = [p for p in (ROOT / "apps" / "web").rglob("*.ts*")
               if "node_modules" not in p.parts]
    targets += list((ROOT / "seed").glob("*.json"))
    for p in sorted(targets):
        t = p.read_text("utf-8")
        for ch, name in INVISIBLE.items():
            if ch in t:
                out.append((p.relative_to(ROOT), name, t.count(ch)))
    return out


# ── ⑤ 손님을 낮추는 말 ────────────────────────────────────
#
# ★ 「흔한 일이오」 는 **감싸는 말**입니다 (그대만 그런 것이 아니오).
#   막는 것은 **그 사람의 자리를 두고** 흔하다 하는 쪽입니다.
BELITTLE = [
    (re.compile(r"흔한 자리|흔한 배치|흔하다고 시시"), "손님의 자리를 흔하다 함"),
    (re.compile(r"값 이야기는|값은 아직 묻지 않았다"), "값 얘기를 차갑게 꺼냄"),
    (re.compile(r"보잘것|하찮|시시하"), "깎는 낱말"),
]


def scan_belittle() -> list:
    out = []
    for p in sorted((ROOT / "seed").glob("*.json")):
        for i, line in enumerate(p.read_text("utf-8").splitlines(), 1):
            if line.lstrip().startswith('"_"') or "★" in line:
                continue
            for pat, why in BELITTLE:
                if pat.search(line):
                    out.append((p.name, i, why, line.strip()[:80]))
    for p in sorted((ROOT / "apps" / "web").rglob("*.tsx")):
        if "node_modules" in p.parts:
            continue
        for i, line in enumerate(p.read_text("utf-8").splitlines(), 1):
            st = line.strip()
            if st.startswith(("*", "//", "/*")):
                continue
            for pat, why in BELITTLE:
                if pat.search(line):
                    out.append((str(p.relative_to(ROOT)), i, why, st[:80]))
    return out


def main() -> int:
    bad = 0
    print("=" * 74)
    print("① 화면에서 자리표시 뒤에 손으로 박은 조사 — 무조건 버그")
    print("=" * 74)
    rows = scan_screens()
    for p, i, hit, line in rows:
        print("  %s:%d  %s" % (p, i, hit))
        print("      %s" % line)
    print("  %d곳" % len(rows))
    bad += len(rows)

    print()
    print("=" * 74)
    print("② 캐릭터 이름 뒤 조사가 받침과 안 맞는 자리")
    print("=" * 74)
    rows = scan_names()
    for p, i, got, want, line in rows:
        print("  %s:%d  「%s」 → 「%s」" % (p, i, got, want))
        print("      %s" % line)
    print("  %d곳" % len(rows))
    bad += len(rows)

    print()
    print("=" * 74)
    print("③ 뱅크의 {자리표시} 뒤 조사 — `_fmt` 를 타면 괜찮소 (봐 둘 것)")
    print("=" * 74)
    rows = scan_bank()
    seen = {}
    for name, i, hit in rows:
        seen.setdefault(name, []).append(hit)
    for name, hits in sorted(seen.items()):
        print("  %-22s %3d곳  예) %s" % (name, len(hits), ", ".join(hits[:4])))
    print("  %d곳 / 파일 %d개" % (len(rows), len(seen)))

    print()
    print("=" * 74)
    print("④ 보이지 않는 글자 — 화면은 같아 보이나 찾기가 안 되오")
    print("=" * 74)
    rows = scan_invisible()
    for p, name, n in rows:
        print("  %-46s %s ×%d" % (p, name, n))
    print("  %d곳" % len(rows))
    bad += len(rows)

    print()
    print("=" * 74)
    print("⑤ 손님을 낮추는 말")
    print("=" * 74)
    rows = scan_belittle()
    for src, i, why, line in rows:
        print("  %s:%s  [%s]" % (src, i, why))
        print("      %s" % line)
    print("  %d곳" % len(rows))
    bad += len(rows)

    print()
    print("-" * 74)
    if bad:
        print("  ①② 는 버그요. %d곳을 고쳐야 하오." % bad)
    else:
        print("  [OK] 자리표시 뒤 조사를 손으로 박은 데가 없소.")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
