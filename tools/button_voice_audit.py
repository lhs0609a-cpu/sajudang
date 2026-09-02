"""
버튼 말투 감사 — **누르는 사람은 손님인데 도령이 말하고 있었다.**

    python tools/button_voice_audit.py
    python tools/button_voice_audit.py --all

★ 무슨 일이 있었나

  손님이 2026-09-02 에 짚었습니다 — "이거 답변 누르는 건 「모르겠습니다.
  세 기둥으로 보겠습니다」 이런 식으로 직접 유저가 할 법한 말로 써야지."

  버튼이 이렇게 적혀 있었습니다 —

      모르오 · 세 기둥으로 보겠소
      내 날을 다 적었소
      그렇소 / 아니오

  전부 **하오체**입니다. 하오체는 이 집 사람들의 말투입니다(voice.py).
  그런데 버튼을 누르는 것은 손님입니다. 손님이 도령의 말투로 자기
  말을 하고 있었습니다 — 대사와 조작이 같은 목소리라, 손님은 그게
  자기 말인 줄 모릅니다.

  손님은 **합쇼체**로 말합니다. 도령에게 존대하는 자리입니다.

★ 표지판은 안 셉니다

  「진열대로」 「본문으로」 「대운 맵」 은 말이 아니라 **표지판**입니다.
  어디로 가는지를 적은 것이지 손님이 하는 말이 아닙니다. 이런 것은
  동사로 끝나지 않으므로 자연히 안 걸립니다.

★ 무엇을 잡나

  버튼 글이 **동사로 끝나는데 합쇼체가 아닌 것**을 잡습니다 —
  …소 · …오 · …다(…니다 제외) · …지 · …네.

  관리자 화면(admin · DevRail)은 뺍니다. 손님이 보는 자리가 아닙니다.
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"

# 손님이 안 보는 자리
SKIP = ("admin", "DevRail", "PromptModal")

BTN = re.compile(r"<button\b[^>]*>(.*?)</button>", re.S)
STR = re.compile(r'"([^"\\<>{}]{1,60})"')
TAGS = re.compile(r"<[^>]+>")
EXPR = re.compile(r"\{[^{}]*\}")

# 합쇼체 — 손님이 도령에게 하는 말
OK_TAIL = ("습니다", "ㅂ니다", "십시오", "니다", "습니까", "ㅂ니까", "까")

# 걸리는 꼬리 — 하오체와 한다체
BAD_TAIL = ("소", "오", "다", "지", "네", "요", "군", "구려")


def labels(src: str):
    """버튼 하나가 실제로 보여 주는 글자들."""
    for m in BTN.finditer(src):
        raw = m.group(1)
        line = src[:m.start()].count("\n") + 1
        # 삼항으로 갈리는 글도 각각 봅니다 — 한쪽만 고치면 나머지가 샙니다.
        parts = [t.strip() for t in STR.findall(raw)]
        plain = TAGS.sub(" ", EXPR.sub(" ", raw))
        plain = re.sub(r"\s+", " ", plain).strip()
        if plain:
            parts.append(plain)
        for t in parts:
            t = t.strip()
            if t and re.search(r"[가-힣]", t):
                yield line, t


def flagged(text: str) -> bool:
    """동사로 끝나는데 합쇼체가 아닌가."""
    # 딱지·표지판은 끝의 기호·괄호를 떼고 봅니다
    t = re.sub(r"[\s·→←↗✕()\[\]0-9A-Za-z]+$", "", text).strip()
    if not t:
        return False
    if t.endswith(OK_TAIL):
        return False
    return t.endswith(BAD_TAIL)


def scan():
    out = []
    for p in sorted(WEB.rglob("*.tsx")):
        rel = p.relative_to(ROOT).as_posix()
        if any(k in rel for k in SKIP):
            continue
        src = io.open(p, encoding="utf-8").read()
        seen = set()
        for line, t in labels(src):
            if flagged(t) and (rel, t) not in seen:
                seen.add((rel, t))
                out.append((rel, line, t))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()

    bad = scan()
    print("버튼 말투 감사 — 손님의 말은 합쇼체로")
    print("=" * 70)
    if not bad:
        print("[OK] 도령 말투로 적힌 버튼 없음")
        return 0
    print("합쇼체가 아닌 버튼 %d 개" % len(bad))
    print("-" * 70)
    for rel, line, t in (bad if a.all else bad[:40]):
        print("  %-38s %4d  %s" % (rel.replace("apps/web/", ""), line, t[:44]))
    if not a.all and len(bad) > 40:
        print("  … %d 개 더. --all 로 다 봅니다." % (len(bad) - 40))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
