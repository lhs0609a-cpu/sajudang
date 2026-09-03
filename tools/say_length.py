"""
말풍선이 얼마나 긴가 — 한 번에 쏟는 자리를 찾는다.

    python tools/say_length.py            표
    python tools/say_length.py --show     긴 것 전문

★ 왜 이 도구가 생겼는가 (2026-09-03)

  손님이 a5 화면에서 멈췄습니다. 도령의 말 한 덩이가 **열세 줄**이었고,
  화면에는 말풍선 하나만 있었습니다.

      "지금 전반적으로 말이 너무 길어, 적당하면서도 임팩트있게,
       그리고 대화형식으로 글이 띄어져야할거아냐 자연스럽게"

  이 집의 화면은 **대화**입니다. 대화는 주고받는 것이라 한 사람이
  열세 줄을 이어 말하면 그건 대화가 아니라 연설입니다. 손님은 읽는
  게 아니라 훑고, 훑으면 아무것도 안 남습니다.

★ 무엇을 재는가

    글자 수   말풍선 하나가 몇 자인가
    문장 수   몇 문장을 한 덩이에 넣었는가
    이어짐    같은 사람이 잇달아 몇 번 말하는가 (덩이만 나누고 화면을
              안 나누면 그것도 연설입니다)

★ 문턱은 대사 한 마디의 길이입니다

  웹툰 말풍선은 두세 줄입니다. 이 집의 폭(약 440px · 16px)에서 한 줄이
  대략 열여덟 자니, **세 줄이면 쉰 자 남짓**입니다. 넉넉히 잡아 한
  덩이 120자 · 4문장을 문턱으로 둡니다. 넘으면 나누라는 뜻이지
  지우라는 뜻이 아닙니다.

★ 나레이션(Narration)은 안 셉니다.
  그건 지문이라 원래 짧고, 대사와 규칙이 다릅니다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"

# 한 덩이가 넘으면 안 되는 선
MAX_CHARS = 120
MAX_SENT = 4

PAGES = ("app/page.tsx", "app/lobby/page.tsx", "app/report/[id]/page.tsx",
         "app/pay/page.tsx", "app/me/page.tsx", "app/daily/page.tsx",
         "app/relay/page.tsx", "app/summary/page.tsx",
         "app/s/[token]/SharedView.tsx",
         "components/HookSegments.tsx")

# ★ <Say> 는 정규식으로 못 자릅니다 (2026-09-03).
#
#   속성값 안에 > 가 듭니다 —
#       <Say html="혹시 <b>성향 검사</b>를 해본 적 있소?<br>…" />
#   그래서 `<Say\b[^>]*>` 는 여는 태그를 여기서 못 끝내고, 자기가 닫는
#   꼴인 줄도 모른 채 **다음 </Say> 까지** 삼킵니다. 그 사이의 코드와
#   주석이 통째로 「대사」 가 되어, a4b 가 559자짜리 말풍선을 가진 것처럼
#   나왔습니다. 자가 부풀면 고칠 자리를 못 찾습니다.
#
#   따옴표를 세면서 손으로 훑습니다. 짧은 코드가 정확한 자보다 낫지 않습니다.
# 마디의 경계 — Narration.Say 가 여기서 갈라 마디마다 따로 놓습니다.
#   자도 같은 자리에서 갈라야 화면에서 보이는 것과 같아집니다.
BR = re.compile(r'<br\s*/?>', re.I)
SCREEN = re.compile(r'<Shell\s[^>]*screen="(\w+)"')
TAG = re.compile(r"<[^>]*>")
BRACE = re.compile(r"\{[^{}]*\}")


# 화면에 안 나가는 주석 — {/* … */}
#
# ★ 이걸 안 걷어서 훅 부품의 **코드 주석**이 201자짜리 대사로 잡혔습니다.
#   주석은 손님이 안 읽습니다.
COMMENT = re.compile(r"\{/\*.*?\*/\}", re.S)


def mask_comments(src: str) -> str:
    """
    주석을 **자리는 두고** 지운다 — 줄바꿈은 살립니다.

    ★ 주석 안에 `<Say>` 라고 적어 둔 자리가 있습니다. 그걸 안 지우면
      훑는 자가 그걸 진짜 대사로 알고 다음 </Say> 까지 삼켜, 코드 주석이
      201자짜리 말풍선으로 잡힙니다. 길이만 지우면 줄 번호가 어긋나니
      줄바꿈은 그대로 두고 나머지만 빈칸으로 바꿉니다.
    """
    def blank(m):
        return "".join(c if c == chr(10) else " " for c in m.group(0))
    return COMMENT.sub(blank, src)


def plain(chunk: str) -> str:
    """말풍선 안의 **읽는 글**만. 주석·태그·값 자리는 걷습니다."""
    t = COMMENT.sub(" ", chunk)
    t = t.replace("<br />", " ").replace("<br/>", " ").replace("<br>", " ")
    t = BRACE.sub("▮", t)
    t = TAG.sub("", t)
    t = t.replace("{\" \"}", " ").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", t).strip()


def sentences(t: str) -> list:
    return [s for s in re.split(r"(?<=[.!?…])\s+", t) if len(s.strip()) > 1]


def screen_at(src: str, at: int) -> str:
    """그 자리가 어느 화면인가 — 앞에서 가장 가까운 Shell 선언."""
    got = "?"
    for m in SCREEN.finditer(src):
        if m.start() > at:
            break
        got = m.group(1)
    return got


def says(src: str):
    """(대사 글, 그 자리) 를 차례로 낸다. 여는 태그를 손으로 끝냅니다."""
    i = 0
    while True:
        i = src.find("<Say", i)
        if i < 0:
            return
        j, quote, depth = i + 4, "", 0
        while j < len(src):
            c = src[j]
            if quote:
                if c == quote:
                    quote = ""
            elif c in "\"'`":
                quote = c
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            elif c == ">" and depth == 0:
                break
            j += 1
        tag = src[i:j + 1]
        if tag.rstrip().endswith("/>"):
            # 자기가 닫는 꼴 — 대사는 html 속성 안에 있습니다
            m = re.search(r'html=(?:"(.*?)"|\{`(.*?)`\})', tag, re.S)
            body = (m.group(1) or m.group(2)) if m else ""
            i = j + 1
        else:
            k = src.find("</Say>", j)
            if k < 0:
                return
            body, i = src[j + 1:k], k + 6
        yield body, i


def scan() -> list:
    rows = []
    for rel in PAGES:
        p = WEB / rel
        if not p.exists():
            continue
        src = mask_comments(p.read_text(encoding="utf-8"))
        for body, at in says(src):
            # ★ 손님이 보는 것은 <Say> 한 덩이가 아니라 **말풍선 하나**
            #   입니다 (Narration.Say 가 <br /> 에서 가릅니다).
            for j, part in enumerate(BR.split(body)):
                t = plain(part)
                if not t:
                    continue
                rows.append({
                    "file": rel,
                    "screen": screen_at(src, at),
                    "line": src[:at].count(chr(10)) + 1,
                    "beat": j + 1,
                    "chars": len(t),
                    "sent": len(sentences(t)),
                    "text": t,
                })
    return rows


def main() -> int:
    show = "--show" in sys.argv
    rows = scan()
    bad = [r for r in rows
           if r["chars"] > MAX_CHARS or r["sent"] > MAX_SENT]
    bad.sort(key=lambda r: -r["chars"])

    print("=" * 76)
    print("  말풍선 길이 — 한 번에 쏟는 자리")
    print("=" * 76)
    print()
    print("  말풍선 %d개 · 문턱 %d자 · %d문장" % (len(rows), MAX_CHARS, MAX_SENT))
    if rows:
        avg = sum(r["chars"] for r in rows) / len(rows)
        print("  평균 %d자 · 가장 긴 것 %d자"
              % (round(avg), max(r["chars"] for r in rows)))
    print()
    print("  넘는 것 %d개" % len(bad))
    print("     %-5s %-26s %6s %5s" % ("화면", "파일:줄", "글자", "문장"))
    for r in bad:
        print("     %-5s %-26s %6d %5d"
              % (r["screen"],
                 "%s:%d#%d" % (r["file"].split("/")[-1], r["line"], r["beat"]),
                 r["chars"], r["sent"]))
        if show:
            print("        %s" % r["text"][:300])
            print()
    print()
    print("-" * 76)
    print("  대화는 주고받는 것이오. 한 사람이 열세 줄을 이어 말하면")
    print("  그건 대화가 아니라 연설이고, 손님은 읽는 게 아니라 훑소.")
    print("-" * 76)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
