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

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"

# ★ 셈은 **엔진에 한 벌** 있습니다 (services/api/engine/typo.py).
#
#   주인 화면의 줄길이 축이 같은 자를 써야 합니다. 두 벌로 두면
#   화면 폭을 바꾸는 날 한쪽만 고칩니다 — 도구는 알고 점수는 모르는
#   일이 생깁니다. `tests/test_typo.py` 가 둘이 같은지 봅니다.
sys.path.insert(0, str(ROOT / "services" / "api"))
from engine import typo as _typo                       # noqa: E402

WIDTH = _typo.WIDTH
GATE_WIDTH = _typo.GATE_WIDTH

SIZE = _typo.SIZE

# 과부로 보는 길이 — 마지막 줄이 이보다 짧으면 짚습니다
WIDOW = _typo.WIDOW

width_of = _typo.width_of


wrap = _typo.wrap


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
        # * 한 {} 안의 글 여럿은 **갈래**지 이어지는 글이 아닙니다
        #   (2026-09-10). `{busy ? "A" : locked ? "B" : "C"}` 는 화면에
        #   셋 중 하나만 나오는데, 이어 붙여 재니 넉 줄짜리 글이 되어
        #   **없는 과부**가 잡혔습니다. 갈래를 따로 보면 셋 다 멀쩡했습니다.
        #
        #   가장 긴 갈래로 봅니다 — 감기는지 보는 자리라 가장 나쁜
        #   갈래가 통과하면 나머지도 통과합니다.
        ko = [g for g in got if re.search("[가-힣]", g)]
        return " " + (max(ko, key=len) if ko else "") + " "

    # 값이 끼어드는 자리는 두 글자쯤으로 봅니다 (숫자가 들어옵니다)
    s = re.sub(chr(92) + "$" + chr(92) + "{[^{}]*" + chr(92) + "}", "00", s)
    s = re.sub(chr(92) + "{([^{}]*)" + chr(92) + "}", pick, s)
    s = re.sub("<[^>]*>", "", s)
    s = s.replace("&nbsp;", chr(160))
    s = re.sub("[ " + chr(9) + chr(13) + chr(10) + "]+", " ", s)
    # * 식을 글로 바꿀 때 앞뒤에 빈칸을 넣습니다(낱말이 붙지 않게).
    #   그런데 뒤가 마침표면 화면에 없는 빈칸이 생겨 「…상황 .」 이 되고,
    #   그 한 칸 때문에 줄이 밀려 없는 과부가 잡힙니다. 문장부호 앞은 붙입니다.
    #   가운뎃점(·)은 「A · B」 처럼 양옆에 빈칸을 두는 것이 이 집의 꼴이라
    #   건드리지 않습니다. 문장 끝 부호만 붙입니다.
    s = re.sub(r"\s+([.,!?…])", r"\1", s)
    return s.strip()


# 손님이 보는 **줄** 단위로 자릅니다.
#
# * <br /> 는 손님 화면에서 줄이 실제로 끊기는 자리입니다. 그런데 태그만
#   지우고 이어 붙이면 두 줄이 한 줄이 되고, 사이에 빈칸이 없어 낱말까지
#   붙습니다 - 「눌러<br />세 곳까지」 가 「눌러세 곳까지」 가 됐습니다.
#   있지도 않은 긴 줄을 재고, 없는 낱말을 만들었습니다.
#
#   lines={[...]} 자리는 이미 이렇게 자르고 있었습니다. 문단과 버튼도
#   같은 자로 봅니다.
_BR = re.compile(r"<br\s*/?>", re.I)


def _pieces(raw):
    """한 덩이에서 **줄로 끊긴 글**들을 낸다."""
    for seg in _BR.split(raw):
        t = strip_tags(seg)
        if len(t) >= 8 and re.search("[가-힣]", t):
            yield t


# JSX 여는 표의 **진짜 끝**을 찾습니다.
#
# * <button[^>]*> 로 잡으면 onClick={() => ...} 안의 > 에서 멈춥니다.
#   그러면 남은 코드가 글로 딸려 나와 「setTab("b4")}> 내 명식 …」 같은
#   글줄이 생기고, 그 군더더기 때문에 한 줄짜리 버튼이 두 줄로 감겨
#   **없는 과부**가 잡힙니다. <p 가 <path 를 물던 것과 같은 병입니다.
#
#   중괄호 깊이와 따옴표를 세면서 걷습니다.
def _tag_end(code, at):
    depth, quote, i = 0, "", at
    while i < len(code):
        c = code[i]
        if quote:
            if c == quote:
                quote = ""
        elif c in ("'", '"', "`"):
            quote = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == ">" and depth <= 0:
            return i + 1
        i += 1
    return -1


# 한 상자 안에서도 **자식 표마다 줄이 갈립니다** — <b>내 명식</b><span>…</span>
#   는 두 줄로 그려집니다. 이어 붙여 재면 있지도 않은 긴 줄이 됩니다.
def _chunks(inner):
    for seg in re.split(r"<[^>]*>", inner):
        for t in _pieces(seg):
            yield t


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

        # 버튼에 적힌 말 — 폭이 좁아 두 줄이 되면 티가 크게 납니다
        for m in re.finditer(r"<button\b", code):
            head = _tag_end(code, m.start())
            if head < 0:
                continue
            shut = code.find("</button>", head)
            if shut < 0 or shut - head > 400:
                continue
            for t in _chunks(code[head:shut]):
                out.append((rel, code.count(chr(10), 0, m.start()) + 1,
                            "btn", t))

        # 그 밖의 문단 — 안내·경고·풀이
        #
        # * <p 가 <path 를 물고 있었습니다 (2026-09-10).
        #
        #   여는 표를 <p[^>]*> 로 잡으면 SVG 의 <path d="..."> 가 그대로
        #   걸립니다. 그러면 글이 <path> 안에서 시작해 진짜 문단의 </p>
        #   까지 이어져 **코드 조각이 글에 섞입니다.** BodyMap.tsx 에서
        #   「} 그림이나 아래 이름을...」 이라는 있지도 않은 글줄이 나왔고,
        #   그 } 때문에 한 줄에 들어가는 문장이 두 줄로 감겨 **없는 과부**가
        #   잡혔습니다. 자가 부풀면 진짜 조각이 그 안에 묻힙니다.
        for m in re.finditer(r"<p(?![A-Za-z])(?![^>]*className=\"sm)"
                             r"[^>]*>(.{8,400}?)</p>", code, re.S):
            for t in _pieces(m.group(1)):
                out.append((rel, code.count(chr(10), 0, m.start()) + 1, "nr", t))

        # <Say> 와 <p className="sm"> 안의 글
        for rx, kind in ((r"<Say[^>]*>\s*([^<{][^<]{7,})<", "say"),
                         (r'className="sm[^"]*"[^>]*>\s*([^<{][^<]{7,})<', "sm")):
            for m in re.finditer(rx, code):
                t = strip_tags(m.group(1))
                if re.search(r"[가-힣]", t):
                    out.append((rel, code.count("\n", 0, m.start()) + 1, kind, t))
    # ── 리포트 본문 — 문장 뱅크 ──────────────────────────
    #
    # ★ 여기가 통째로 빠져 있었습니다. 화면 글 122줄만 보고 「다 고쳤다」고
    #   했는데, 손님이 **값을 치르고 읽는 글**은 한 줄도 안 봤습니다.
    #   컷 하나가 한 문단이라 마지막 줄이 조각으로 남기 딱 좋습니다.
    for name in ("bank.json", "lens_cuts.json", "extras.json", "sinsal.json"):
        f = ROOT / "seed" / name
        if not f.exists():
            continue
        data = json.loads(f.read_text(encoding="utf-8"))

        def walk(o, path=""):
            if isinstance(o, str):
                t = strip_tags(o)
                if len(t) >= 24 and re.search("[가-힣]", t):
                    out.append(("seed/" + name, 0, "cut", t))
            elif isinstance(o, dict):
                for k, v in o.items():
                    walk(v, path + "/" + str(k))
            elif isinstance(o, list):
                for v in o:
                    walk(v, path)

        walk(data)

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

    hand = [b for b in bad if not b[0].startswith("seed/")]
    auto = [b for b in bad if b[0].startswith("seed/")]

    print()
    if auto:
        print("  ※ 리포트 본문 %d곳 — 여기는 손으로 안 고칩니다." % len(auto))
        print("     본문은 조각을 **조합해** 만들고(훅 5단·관점 컷), 말투 층과")
        print("     풀이 층이 맨 끝에 얹혀 길이가 또 바뀝니다. 조각 하나를")
        print("     손봐도 조합된 결과가 어디서 끊길지 모릅니다.")
        print("     브라우저가 실제로 그린 줄을 보고 고치게 둡니다")
        print("     (`text-wrap: pretty` — .cutbody · .saying).")
        print()

    if not hand:
        print("  [OK] 화면에 박힌 글에는 걸리는 자리 없음")
        print()

    for rel, line, kind, lines, tail in hand:
        print("  %s:%d  (%s)" % (rel, line, kind))
        for i, l in enumerate(lines):
            mark = "  ← 여기가 홀로 남습니다" if i == len(lines) - 1 else ""
            print("     %s%s" % (l, mark))
        print()

    print("-" * 76)
    print("  글줄 %d개 중 %d곳 — 화면 글 %d · 리포트 본문 %d"
          % (len(rows), len(bad), len(hand), len(auto)))
    print("  고치는 법 — <br> 로 뜻이 끊기는 자리에서 직접 끊거나,")
    print("  마지막 두 마디를 &nbsp; 로 묶어 같이 내려보냅니다.")
    print("-" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
