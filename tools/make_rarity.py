"""
희소도 표를 만든다 — seed/rarity.json

    python tools/make_rarity.py 40000

★ 요청 때 4만 명을 돌릴 수는 없습니다. 한 번 세어 표로 둡니다.
★ 축을 고쳤으면 반드시 다시 도세요. engine/rarity.is_stale() 이 봅니다.
★ 표본 크기를 표에 같이 적습니다 — 얇은 칸은 환산하지 않고 표본 그대로
  말하기 때문에, 그 숫자가 어디서 나왔는지가 화면까지 따라갑니다.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT))

from engine import rarity                       # noqa: E402
from tools.population import banner, sample     # noqa: E402

NOTE = [
    "배치 희소도 — tools/make_rarity.py 가 만듭니다. 손으로 고치지 마세요.",
    "",
    "★ 지어낸 값이 아니라 인구 표본에서 **센** 값입니다.",
    "  '적중률' 이 아니라 '이 배치가 몇 명' 이라, 검증 가능합니다.",
    "",
    "★ 축을 고쳤으면 이 표를 다시 만들어야 합니다.",
    "  engine/rarity.is_stale() 이 어긋남을 잡고 테스트가 셉니다.",
]


def main() -> int:
    n = 40000
    for a in sys.argv[1:]:
        if a.isdigit():
            n = int(a)

    print(banner(n))
    counts = Counter()
    ilju = Counter()
    for i, f in enumerate(sample(n, seed=20260827), 1):
        counts[rarity.key_of(f)] += 1
        ilju[f.pillars[2]["gz"]] += 1
        if i % 5000 == 0:
            print("  … %d/%d" % (i, n))

    axes = [a for a, _ in rarity.AXES]
    out = {
        "_": NOTE,
        "axes": axes,
        "sample": n,
        "cells": {k: {"n": v} for k, v in sorted(counts.items())},
        # 일주 예순 갑자. 누구나 하나씩 가지므로 **골라 담을 수 없는** 수입니다.
        # 배치가 흔한 사람에게도 셀 수 있는 자리를 하나 남겨 둡니다.
        "ilju": {k: {"n": v} for k, v in sorted(ilju.items())},
    }
    dest = ROOT / "seed" / "rarity.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")

    print("\n칸 %d개 · 표본 %s명 → %s"
          % (len(counts), format(n, ","), dest.relative_to(ROOT)))

    rows = counts.most_common()
    print("\n가장 흔한 다섯")
    for k, v in rows[:5]:
        print("  %-28s %6.2f%%  1만 명에 %5d명" % (k, v / n * 100, round(v / n * 10000)))
    print("\n가장 드문 다섯")
    for k, v in rows[-5:]:
        per = round(v / n * 10000)
        tail = "1만 명에 %d명" % per if v >= rarity.MIN_FOR_SCALE else "표본에 %d명뿐" % v
        print("  %-28s %6.2f%%  %s" % (k, v / n * 100, tail))

    thin = sum(1 for _, v in rows if v < rarity.MIN_FOR_SCALE)
    print("\n환산 못 하는 얇은 칸 %d개 — 이 칸은 표본 그대로 말합니다" % thin)

    # 사람마다 어떤 띠에 드는가. 이게 곧 화면에 나갈 말의 분포입니다.
    band = Counter()
    for k, v in rows:
        share = v / n
        b = ("아주드묾" if share < 0.005 else "드묾" if share < 0.02
             else "적잖음" if share < 0.08 else "흔함")
        band[b] += v
    print("\n사람이 받게 될 말의 분포")
    for b in ("아주드묾", "드묾", "적잖음", "흔함"):
        print("  %-6s %6.1f%%" % (b, band[b] / n * 100))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
