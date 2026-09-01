"""
과부 줄(widow) 찾기 — 마지막 줄에 조각만 홀로 남는 자리.

    python tools/widow.py
    python tools/widow.py --all     아슬아슬한 것까지

★ 무엇이 문제인가

  대문에서 이런 일이 있었다.

      왜 그리 말했는지까지 적어 드리오. 맞힌다고는
      안 하오.

  「안 하오.」 세 글자가 혼자 남았다. 가운데 정렬이라 더 티가 난다.
  이걸 조판에서 **과부 줄(widow)** 이라 한다 — 문단 **끝** 줄에
  조각만 남는 것. 반대로 첫 줄이 떨어져 나가면 고아 줄(orphan)이다.

  글이 틀린 것도 아니고 버그도 아닌데, 읽는 사람에게는 **덜 만든
  것처럼** 보인다. 첫 화면에서 그러면 그 인상이 끝까지 간다.

★ 어떻게 재나

  화면 폭은 정해져 있다(440px 틀 · `.scr` 좌우 22px). 글자 크기도
  토큰으로 정해져 있다. 그러면 한 줄에 몇 자가 들어가는지 셀 수 있다.

      한 줄 = (본문 폭) / (글자 폭)
      한글은 글자 하나가 거의 1em, 로마자·숫자·공백은 그 절반쯤

  글을 그 길이로 잘라 마지막 줄에 몇 자가 남는지 본다. 넷 이하면
  과부 줄이다.

★ 어떻게 고치나

  1. `<br>` 로 뜻이 끊기는 자리에서 직접 끊는다 (제일 확실하다)
  2. 마지막 두 마디를 `&nbsp;` 로 묶어 같이 내려보낸다
  3. 말을 줄인다

  CSS 의 `text-wrap: pretty` 도 브라우저가 알아서 피해 주지만,
  `<br>` 이 섞이면 잘 안 먹는다. 첫 화면처럼 중요한 자리는 손으로
  끊는다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"

# 틀 440 · .scr 좌우 22 → 396. 가운데 정렬 글은 .gatecopy 가 26 을 더 먹는다.
WIDTH = 396
GATE_WIDTH = 388

# 클래스 → 글자 크기(px). tokens.css 의 사다리와 짝입니다.
SIZE = {
    "nr": 16.0,        # --fs-5  나레이션
    "say": 17.5,       # --fs-6  도령의 말
    "promise": 16.0,   # --fs-5
    "sm": 14.0,        # --fs-3  부가 설명
    "btn": 15.0,       # --fs-4  버튼
    "lab": 13.0,       # --fs-2
}

# 과부로 보는 길이 — 마지막 줄이 이보다 짧으면 짚습니다
WIDOW = 4


def width_of(ch: str) -> float:
    """한글은 거의 1em, 나머지는 절반쯤."""
    return 1.0 if "가" <= ch <= "힣" or "一" <= ch <= "鿿" else 0.5


def wrap(text: str, px: float, box: int) -> list[str]:
    """띄어쓰기에서만 끊습니다 (word-break: keep-all)."""
    cap = box / px
    lines, cur, w = [], "", 0.0
    for word in text.split(" "):
        ww = sum(width_of(c) for c in word)
        if cur and w + 0.5 + ww > cap:
            lines.append(cur)
            cur, w = word, ww
        else:
            if cur:
                cur += " "
                w += 0.5
            cur += word
            w += ww
    if cur:
        lines.append(cur)
    return lines


def strip_tags(s: str) -> str:
    """
    화면에 실제로 나가는 글로 만듭니다.

    * 첫 판은 소스를 그대로 셌습니다. 그런데 JSX 는 줄바꿈과 들여쓰기를
      **공백 하나로 접습니다.** 그걸 글자로 세면 있지도 않은 줄이 생겨
      없는 과부를 짚습니다 - 실제로 둘을 헛짚었습니다.

      그리고 식({...}) 은 무엇이 들어올지 여기서 모릅니다. 안의 글만
      건지고 껍데기는 버립니다.
    """
    def pick(m):
        got = re.findall(chr(91) + "`" + chr(34) + chr(39) + chr(93)
                         + "([^`" + chr(34) + chr(39) + "]*)"
                         + chr(91) + "`" + chr(34) + chr(39) + chr(93),
                         m.group(1))
        return " " + " ".join(g for g in got if re.search("[가-힣]", g)) + " "

    # 값이 끼어드는 자리는 두 글자쯤으로 봅니다 (숫자가 들어옵니다)
    s = re.sub(chr(92) + "$" + chr(92) + "{[^{}]*" + chr(92) + "}", "00", s)
    s = re.sub(chr(92) + "{([^{}]*)" + chr(92) + "}", pick, s)
    s = re.sub("<[^>]*>", "", s)
    s = s.replace("&nbsp;", chr(160))
    s = re.sub("[ " + chr(9) + chr(13) + chr(10) + "]+", " ", s)
    return s.strip()


def harvest():
    """화면에 나가는 한글 글줄을 뽑습니다."""
    out = []
    pat = [
        # <Narration lines={[...]}/>  안의 문자열
        (r'lines=\{\[(.*?)\]\}', "nr"),
        # 상수로 둔 서사·약속
        (r'^const (?:PROMISE|OPENING|BEATS)\b[^=]*=\s*(.*?);\s*$', "promise"),
    ]
    for p in sorted(list((WEB / "app").rglob("*.tsx")) +
                    list((WEB / "components").rglob("*.tsx"))):
        if p.name == "DevRail.tsx":
            continue
        src = p.read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"),
                      src, flags=re.S)
        code = re.sub(r"//[^\n]*", "", code)
        rel = str(p.relative_to(WEB))

        for rx, kind in pat:
            for m in re.finditer(rx, code, re.S | re.M):
                line = code.count("\n", 0, m.start()) + 1
                for s in re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1)):
                    for seg in re.split(r"<br\s*/?>", s):
                        t = strip_tags(seg)
                        if len(t) >= 8 and re.search(r"[가-힣]", t):
                            out.append((rel, line, kind, t))

        # <Say> 와 <p className="sm"> 안의 글
        for rx, kind in ((r"<Say[^>]*>\s*([^<{][^<]{7,})<", "say"),
                         (r'className="sm[^"]*"[^>]*>\s*([^<{][^<]{7,})<', "sm")):
            for m in re.finditer(rx, code):
                t = strip_tags(m.group(1))
                if re.search(r"[가-힣]", t):
                    out.append((rel, code.count("\n", 0, m.start()) + 1, kind, t))
    return out


def main() -> int:
    loose = "--all" in sys.argv
    rows = harvest()

    bad = []
    for rel, line, kind, text in rows:
        px = SIZE.get(kind, 16.0)
        box = GATE_WIDTH if kind == "promise" else WIDTH
        lines = wrap(text, px, box)
        if len(lines) < 2:
            continue
        tail = sum(width_of(c) for c in lines[-1])
        if tail <= WIDOW or (loose and tail <= WIDOW + 2):
            bad.append((rel, line, kind, lines, tail))

    print("=" * 76)
    print("  과부 줄(widow) — 마지막 줄에 조각만 홀로 남는 자리")
    print("=" * 76)

    if not bad:
        print("\n  [OK] 걸리는 자리 없음  (글줄 %d개를 봤습니다)" % len(rows))
        return 0

    print()
    for rel, line, kind, lines, tail in bad:
        print("  %s:%d  (%s)" % (rel, line, kind))
        for i, l in enumerate(lines):
            mark = "  ← 여기가 홀로 남습니다" if i == len(lines) - 1 else ""
            print("     %s%s" % (l, mark))
        print()

    print("-" * 76)
    print("  글줄 %d개 중 %d곳" % (len(rows), len(bad)))
    print("  고치는 법 — <br> 로 뜻이 끊기는 자리에서 직접 끊거나,")
    print("  마지막 두 마디를 &nbsp; 로 묶어 같이 내려보냅니다.")
    print("-" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
