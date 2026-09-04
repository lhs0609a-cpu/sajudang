"""
첫 줄과 끝 줄 — 자리마다 할 일이 다르다.

    python tools/first_last.py
    python tools/first_last.py --show    첫 줄·끝 줄을 그대로

★ 손님이 못박은 세 자리 (2026-09-04)

    처음      팩폭으로 뼈를 때려서 「이거 내 이야기야」 공감하게
    마지막    다음 페이지를 보고 싶어 미치도록
    결제 전   궁금해 미치도록

★ 이미 재고 있던 것과 아닌 것

  연출 점수의 **당김**은 끝을 봅니다 — 액트아웃 다섯 꼴(밝힘·뒤집기·
  딜레마·끊긴 동작·남긴 물음)과 콜드 오픈을 셉니다. 거기는 자가 있습니다.

  **팩폭**은 화면 전체에서 셀 수 있는 말을 셉니다. 그런데 **어디에**
  있는지는 안 봅니다. 셀 수 있는 말이 스무 줄째에 처음 나오면, 손님은
  그 앞에서 이미 훑기 시작합니다. 첫인상은 첫 줄이 만듭니다.

  그래서 이 자는 **자리**만 봅니다 — 무엇이 있는가가 아니라, 그것이
  맨 앞에 있는가.

★ 무엇을 세는가

    첫 팩폭   첫 두 줄 안에 **셀 수 있는 것**이 있는가
              (수 · 글자 · 나이 · 해 · 「0」 · 「없소」)
    끝 고리   마지막 두 줄이 다음을 가리키는가
              (물음표 · 다음 자리 이름 · 아직/남았/열리오)

★ 재지 않는 것 — 글의 좋고 나쁨. 그건 연출 점수가 봅니다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import screenscan as S                     # noqa: E402

# 셀 수 있는 것 — 손님이 세어 보고 다르면 우리가 지는 말
COUNTABLE = re.compile(
    r"[0-9]|하나도 없|없소|없어요|없습니다|"
    r"\b(하나|둘|셋|넷|다섯|여섯|일곱|여덟|아홉|열)\b|"
    r"몇|살이|년은|자리가")

# 다음을 가리키는 끝
HOOK = re.compile(
    r"[?？]|「[^」]{2,20}」|아직|남았|남은|다음|뒤에|더 있|열리|"
    r"안 (?:했|보|열)|이제")

# 앞뒤로 볼 줄 수
EDGE = 2


def lines(text: str) -> list:
    out = [x.strip() for x in re.split(r"(?<=[.!?…])\s+|\n+", text)]
    return [x for x in out if len(x) > 4]


def main() -> int:
    show = "--show" in sys.argv
    S._screens.cache_clear()
    rows = S.scan_all()
    text = {}
    for sid, v in S._screens().items():
        text[sid] = v[0]
    eng = S._engine_text()
    for sid, html in eng.items():
        text[sid] = html + " " + text.get(sid, "")

    print("=" * 76)
    print("  첫 줄과 끝 줄 — 처음은 팩폭, 끝은 고리")
    print("=" * 76)
    print()
    print("     %-5s %-11s %8s %8s" % ("화면", "이름", "첫 팩폭", "끝 고리"))

    bad_head, bad_tail = [], []
    for r in rows:
        sid = r["id"]
        ls = lines(re.sub(r"<[^>]+>", " ", text.get(sid, "")))
        if not ls:
            continue
        head = " ".join(ls[:EDGE])
        tail = " ".join(ls[-EDGE:])
        h = bool(COUNTABLE.search(head))
        t = bool(HOOK.search(tail))
        if not h:
            bad_head.append((sid, r["title"], head))
        if not t:
            bad_tail.append((sid, r["title"], tail))
        print("     %-5s %-11s %8s %8s"
              % (sid, r["title"], "○" if h else "✕", "○" if t else "✕"))
        if show and (not h or not t):
            if not h:
                print("        첫 : %s" % head[:66])
            if not t:
                print("        끝 : %s" % tail[:66])

    print()
    print("-" * 76)
    print("  첫 줄에 셀 수 있는 말이 없는 화면 %d" % len(bad_head))
    print("  끝이 다음을 안 가리키는 화면 %d" % len(bad_tail))
    print("-" * 76)
    print("  ※ 첫인상은 첫 줄이 만드오. 셀 수 있는 말이 스무 줄째에")
    print("    나오면 손님은 그 앞에서 이미 훑기 시작하오.")
    print("-" * 76)
    return 1 if (bad_head or bad_tail) else 0


if __name__ == "__main__":
    raise SystemExit(main())
