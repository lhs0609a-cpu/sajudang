"""
스무 명이 정말 다르게 말하는가 — 전수조사.

    python tools/voice_spread.py [표본수]

★ 관점이 스물이어도 목소리가 하나면 한 사람이다

  캐릭터마다 **보는 자리**는 다릅니다 (lens_cuts 가 그 일을 합니다).
  그런데 손님이 두 사람을 이어 읽으면 그걸 관점의 차이로 못 느끼고
  **같은 글을 두 번 샀다**고 느낍니다. 글자가 같기 때문입니다.

★ 이 도구가 재는 것 셋

  ① 호칭   그대 · 자네 · 그쪽 · 아저씨 — 몇 가지나 되는가
  ② 어미   ~오/~소 · ~습니다 · ~네 · ~지 · ~네요 — 몇 결인가
  ③ 겹침   두 사람의 리포트에서 **글자 그대로 같은 줄**이 몇 %인가

  ③이 핵심입니다. ①②가 갈려도 ③이 안 내려가면 헛일입니다.

★ 문장 뱅크를 스무 벌로 쓰지 않습니다

  뱅크는 한 벌로 두고 맨 끝에서 갈아 끼웁니다. 스무 벌을 쓰면
  중복률·쏠림을 스무 번 재야 하고, 한 벌이 낡으면 열아홉이 남습니다.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import lens as lens_mod              # noqa: E402
from engine.calendar import build_chart          # noqa: E402
from engine.features import build_features       # noqa: E402
from engine.report import build_report           # noqa: E402

TAG = re.compile(r"<[^>]+>")
YOU = re.compile(r"그대|자네|그쪽|아저씨|당신|손님|너\b")

# 어미 다섯 결
ENDS = (
    ("하오체", re.compile(r"(?:오|소)[.!?…]")),
    ("합쇼체", re.compile(r"습니다[.!?…]|ㅂ니다[.!?…]|니다[.!?…]")),
    ("하게체", re.compile(r"네[.!?…]")),
    ("반말", re.compile(r"지[.!?…]|어[.!?…]|아[.!?…]")),
    ("해요체", re.compile(r"요[.!?…]|에요[.!?…]")),
)


def lines(html: str):
    """문장 단위로 가른다. 태그는 걷는다."""
    txt = TAG.sub(" ", html)
    return [s.strip() for s in re.split(r"[.!?…]", txt) if len(s.strip()) > 6]


def main() -> int:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    charts = [(1993, 11, 25, 13), (1988, 3, 3, 7), (2001, 7, 19, 20),
              (1975, 6, 6, 4), (1996, 1, 30, 22), (1982, 9, 12, 15)][:n]

    lenses = [l for l in lens_mod.released()]
    body = {}
    for l in lenses:
        got = []
        for y, m, d, h in charts:
            f = build_features(build_chart(y, m, d, h, 0, "M", True, "서울"))
            tier = "one" if l.get("price") else "free"
            try:
                r = build_report(f, "cid", l["id"], tier, "money", None)
            except Exception:                     # noqa: BLE001
                continue
            for c in r.get("cuts", []):
                got += lines(c.get("html", ""))
        body[l["id"]] = got

    print("=" * 76)
    print("  스무 명이 다르게 말하는가 — 사람 %d명 × 캐릭터 %d"
          % (len(charts), len(lenses)))
    print("=" * 76)
    print()

    # ① 호칭
    call = Counter()
    for lid, ls in body.items():
        w = Counter(m for s in ls for m in YOU.findall(s))
        call[w.most_common(1)[0][0] if w else "(없음)"] += 1
    print("  ① 호칭 %d가지" % len(call))
    for k, v in call.most_common():
        print("       %-8s %2d명" % (k, v))

    # ② 어미
    print()
    tone = Counter()
    for lid, ls in body.items():
        w = Counter()
        for name, rx in ENDS:
            w[name] += sum(1 for s in ls if rx.search(s + "."))
        tone[w.most_common(1)[0][0] if w else "(없음)"] += 1
    print("  ② 어미 %d결" % len(tone))
    for k, v in tone.most_common():
        print("       %-8s %2d명" % (k, v))

    # ③ 겹침 — 두 사람을 이어 읽으면 몇 %가 같은 글인가
    print()
    sets = {k: set(v) for k, v in body.items()}
    pairs = []
    for a, b in combinations(sorted(sets), 2):
        A, B = sets[a], sets[b]
        if not A or not B:
            continue
        pairs.append((len(A & B) / min(len(A), len(B)), a, b))
    pairs.sort(reverse=True)
    med = pairs[len(pairs) // 2][0] if pairs else 0.0
    print("  ③ 두 사람이 **글자 그대로 같은 줄** — 짝 %d개" % len(pairs))
    print("       중앙값  %.0f%%" % (100 * med))
    print("       가장 닮은 짝")
    for r, a, b in pairs[:5]:
        print("         %5.0f%%  %s ↔ %s" % (100 * r, a, b))

    print()
    print("-" * 76)
    print("  ※ ①②가 갈려도 ③이 안 내려가면 헛일입니다. 손님은 어미가")
    print("    아니라 **같은 글을 두 번 샀다**는 걸로 느낍니다.")
    print("-" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
