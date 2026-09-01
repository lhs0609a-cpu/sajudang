"""
카피 전수점검 — 이 말이 사람을 당기는가.

    python tools/copy_hook.py
    python tools/copy_hook.py --all      곁 버튼까지 전부

★ 무엇을 재나

  버튼에 적힌 말은 두 가지 중 하나입니다.

      틀    「글자를 세우러 들어간다」   — 시스템이 하는 일
      값    「내 운명을 확인하러 간다」  — 손님이 얻는 것

  둘 다 같은 화면으로 갑니다. 그런데 앞의 것은 **일**이고 뒤의 것은
  **보상**입니다. 사람은 일을 하러 누르지 않습니다.

  이 집은 「맞히는 집」이 아니라 「근거 대는 집」이라 과장은 금지입니다
  (docs/11). 그래서 없는 것을 지어내지 않고, **이미 주는 것을 손님의
  말로** 바꿔 적습니다. 「여덟 글자를 세운다」와 「내 사주를 본다」는
  같은 일인데 뒤엣것만 내 일입니다.

★ 세 가지를 셉니다

  1. 자기 지칭   내·나의·그대·당신 이 들어가는가
  2. 얻는 것     운명·자리·때·사람·값 처럼 **받는 것**을 말하는가
                 (글자·명식·진열대·본문 은 **틀**입니다)
  3. 내 행동     -러 간다 / -하러 / -본다 처럼 손님이 주어인가

  주 버튼(그 화면에서 앞으로 나아가는 버튼)이 셋 다 없으면 짚습니다.
  곁 버튼(진열대로·본문으로 같은 이동)은 틀이어도 됩니다 — 오히려
  값을 말하면 어디로 가는지 몰라집니다.

★ 하지 말 것 (docs/11 · CLAUDE.md)

  적중률·과학·통계·반드시 는 여기서도 금지입니다. 그런 말이 들어간
  카피는 후킹이 아니라 **거짓말**이라 따로 잡아 세웁니다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"

# 1 · 손님을 가리키는 말
SELF = ("내 ", "내가", "나의", "그대", "당신", "제 ", "내—")

# 2 · 받는 것 (값) — 손님이 가져가는 것
VALUE = ("운명", "팔자", "사주", "때", "자리", "사람", "값", "돈", "일",
         "사랑", "몸", "방향", "앞", "뒤", "속", "말", "이유", "까닭",
         "약점", "강점", "복", "재물", "인연", "고비", "해", "나이")

# 2' · 틀 (시스템이 하는 일) — 이것만 있으면 약합니다
FRAME = ("글자를 세", "명식", "진열대", "본문", "인장첩", "분석지",
         "계산", "셈", "세운다", "세우러")

# 3 · 손님이 주어인 움직임
MINE = ("간다", "본다", "듣는다", "확인", "알아본다", "받는다", "연다",
        "펴 본다", "고른다", "묻는다")

# 금지 — 검증 못 하는 주장
BANNED = ("적중률", "과학적", "통계학", "반드시", "무조건", "100%",
          "정확히 맞", "틀림없")

# 곁 버튼으로 봐도 되는 말 — 어디로 가는지가 값입니다
SIDE = ("진열대로", "본문으로", "인장첩으로", "처음부터 다시", "뒤로",
        "다시 고른다", "다시 펴 본다", "다시 세워 본다", "건너뛰",
        "그렇소", "아니오", "글쎄올시다", "다 읽었소", "오늘은")


def files():
    for p in sorted(list((WEB / "app").rglob("*.tsx")) +
                    list((WEB / "components").rglob("*.tsx"))):
        if p.name == "DevRail.tsx":
            continue
        yield p


def buttons():
    """화면에 적힌 버튼 글을 전부 뽑습니다."""
    out = []
    for p in files():
        src = p.read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"),
                      src, flags=re.S)
        code = re.sub(r"//[^\n]*", "", code)
        for m in re.finditer(r"<button\b[^>]*>(.{0,160}?)</button>", code, re.S):
            t = re.sub(r"<[^>]*>", " ", m.group(1))
            t = re.sub(r"\{[^{}]*\}", "", t)          # 변수는 지웁니다
            t = " ".join(t.split())
            # 변수로 채우는 버튼은 여기서 글을 알 수 없습니다. 안 셉니다.
            if len(t) < 2 or not re.search(r"[가-힣]{2,}", t):
                continue
            out.append((str(p.relative_to(WEB)),
                        code.count("\n", 0, m.start()) + 1, t))
    return out


def score(text: str) -> tuple[int, list[str]]:
    got = []
    if any(w in text for w in SELF):
        got.append("자기")
    if any(w in text for w in VALUE) and not any(w in text for w in FRAME):
        got.append("값")
    if any(w in text for w in MINE):
        got.append("행동")
    return len(got), got


def main() -> int:
    show_all = "--all" in sys.argv
    rows = buttons()

    weak, banned, ok = [], [], []
    for f, line, t in rows:
        if any(b in t for b in BANNED):
            banned.append((f, line, t))
            continue
        if any(s in t for s in SIDE):
            if show_all:
                ok.append((f, line, t, "곁"))
            continue
        n, got = score(t)
        if n == 0:
            weak.append((f, line, t))
        else:
            ok.append((f, line, t, "·".join(got)))

    print("=" * 76)
    print("  카피 전수점검 — 이 말이 사람을 당기는가")
    print("=" * 76)

    if banned:
        print("\n  ★ 검증 못 하는 주장 — 지워야 합니다 (docs/11)")
        for f, line, t in banned:
            print("     %-26s %4d  %s" % (f[:26], line, t[:44]))

    if weak:
        print("\n  ★ 틀만 말하는 주 버튼 — 손님이 얻는 것이 없습니다")
        print("     %-26s %4s  %s" % ("파일", "줄", "적힌 말"))
        print("     " + "-" * 66)
        for f, line, t in weak:
            print("     %-26s %4d  %s" % (f[:26], line, t[:44]))

    if show_all and ok:
        print("\n  값을 말하는 버튼")
        for f, line, t, tag in ok:
            print("     %-26s %4d  %-34s %s" % (f[:26], line, t[:34], tag))

    total = len(rows)
    print("\n" + "-" * 76)
    print("  버튼 %d개 · 값을 말함 %d · 틀만 말함 %d · 금지어 %d"
          % (total, len(ok), len(weak), len(banned)))
    if weak:
        print("  ※ 같은 화면으로 가더라도 **손님의 말**로 적으면 눌립니다.")
        print("    없는 것을 지어내지 마세요 — 주는 것을 손님 쪽에서 부릅니다.")
    print("-" * 76)
    return 1 if banned else 0


if __name__ == "__main__":
    raise SystemExit(main())
