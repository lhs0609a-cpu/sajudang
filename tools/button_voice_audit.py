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
# 홑따옴표도 봅니다 (2026-09-24). 겹따옴표만 보던 탓에
# 홑따옴표로 적힌 버튼 글이 감사에서 통째로 빠졌습니다.
STR = re.compile("\"([^\"\\<>{}]{1,60})\"|'([^'\\<>{}]{1,60})'")
TAGS = re.compile(r"<[^>]+>")
EXPR = re.compile(r"\{[^{}]*\}")

# 합쇼체 — 손님이 도령에게 하는 말
OK_TAIL = ("습니다", "ㅂ니다", "십시오", "니다", "습니까", "ㅂ니까", "까")

# 걸리는 꼬리 — 하오체와 한다체
BAD_TAIL = ("소", "오", "다", "지", "네", "요", "군", "구려")


def strip_expr(raw: str) -> str:
    """`{...}` 를 **짝을 맞춰** 걷는다.

    ★ 전에는 정규식 한 벌이라 중괄호가 겹친 자리를 못 걷었습니다.
      `onClick={async () => { … }}` 안의 **주석**이 버튼 글자로 남아,
      화면에 찍힐 때 진짜 버튼 글자를 밀어내고 앞자리를 차지했습니다 —
      같은 버튼의 「인장을 받고 나가겠소」가 그렇게 가려져 있었습니다.
      숫자가 1 이라고 다 고친 게 아니었습니다.
    """
    out, depth = [], 0
    for ch in raw:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def labels(src: str):
    """버튼 하나가 실제로 보여 주는 글자들."""
    for m in BTN.finditer(src):
        raw = m.group(1)
        line = src[:m.start()].count("\n") + 1
        # 삼항으로 갈리는 글도 각각 봅니다 — 한쪽만 고치면 나머지가 샙니다.
        # ★ 문자열은 **중괄호 안에서도** 봅니다 (`{busy ? "…" : "…"}`).
        #   걷는 것은 손으로 쓴 식과 주석이지 화면에 찍히는 글이 아닙니다.
        parts = [(a or b).strip() for a, b in STR.findall(raw)]
        plain = TAGS.sub(" ", strip_expr(raw))
        plain = re.sub(r"\s+", " ", plain).strip()
        if plain:
            parts.append(plain)
        for t in parts:
            t = t.strip()
            # ★ 마침표로 끝나는 것은 **알림 글**이오 — 버튼 글이 아닙니다.
            #   손잡이(onClick) 안에서 setState 로 띄우는 말이 버튼 안에
            #   적혀 있어 라벨로 잡혔습니다 (「결제창을 열지 못했소.
            #   다시 시도해 주시오.」). 그건 집의 말이라 하오체가 맞소.
            if t.rstrip().endswith(".") or ". " in t:
                continue
            if t and re.search(r"[가-힣]", t):
                yield line, t


# 버튼 **안쪽**에 든 도령 말투 — 꼬리만 보면 놓칩니다.
#
# 「시간을 모르오 · 그대로 이어가기」 가 감사를 통과하고 있었습니다
# (2026-09-24). 꼬리가 「이어가기」 라 이름씨로 끝나서요. 손님이 누르는
# 것은 손님의 말인데, 그 안에 「모르오」 가 들어 있었습니다.
MIDDLE = re.compile(
    r"(?<![가-힣])(모르오|맞소|좋소|하오|보오|주오|되오|없소|있소|겠소|겠네|겠어)"
    r"(?![가-힣])|(?:주시오|하시오|보시오|가시오|적으시오)")


def flagged(text: str) -> bool:
    """동사로 끝나는데 합쇼체가 아닌가. **안쪽도** 봅니다."""
    if MIDDLE.search(text):
        return True
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
