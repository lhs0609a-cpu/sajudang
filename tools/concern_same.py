# -*- coding: utf-8 -*-
"""
고민을 바꿨는데 같은 글이 나오는가 — **사람 축이 아니라 고민 축**으로.

    python tools/concern_same.py [명식 수] [--lens all]

★ 왜 따로 재나

  `same_audit` 은 「스무 사람이 같은 글을 받는가」 를 봅니다.
  `hook_concern` 은 훅만 봅니다. 그 사이가 비어 있었습니다 —
  **한 사람이 고민만 바꿔 다시 물었을 때** 유료 리포트가 갈리는가.

  손님은 이 자를 제 손으로 댑니다. 돈으로 한 번 보고 사랑으로 다시
  보는 사람이 있고, 그 사람 눈에 두 글이 같으면 그 자리에서 끝입니다.

★ 셈

  고민 일곱 칸을 둘씩 짝지어 21짝. 짝마다 **컷 단위로 글자가 같은지**
  봅니다 (태그를 뗀 글). 명식 컷처럼 무엇을 물었든 같아야 하는 자리도
  같이 세니, 100%가 아니라 **몇 %가 같은가**를 봅니다.
  판정은 「짝이 통째로 같은가」 — 그건 손님이 두 번 값을 치를 까닭이
  없다는 뜻입니다.
"""
from __future__ import annotations

import argparse
import collections
import itertools
import logging
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "services" / "api", ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

logging.disable(logging.CRITICAL)

from engine import lens as lens_mod                # noqa: E402
from engine.calendar import build_chart            # noqa: E402
from engine.features import build_features         # noqa: E402
from engine.report import build_report             # noqa: E402
from engine import bank as bank_mod                # noqa: E402

from tools import journey_sim as J                 # noqa: E402

TAG = re.compile(r"<[^>]+>")


def concerns() -> tuple:
    import typing
    from schemas.api import Concern
    return tuple(typing.get_args(Concern))


def txt(h: str) -> str:
    return TAG.sub("", h or "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("n", nargs="?", type=int, default=120)
    ap.add_argument("--tier", default="all")
    a = ap.parse_args()

    CON = concerns()
    pop = J.people(a.n, seed=20260926)
    lenses = [x["id"] for x in lens_mod.released()]
    today = date(2026, 9, 24)

    pairs = list(itertools.combinations(CON, 2))
    twin = collections.Counter()            # 짝 → 통째로 같은 횟수
    ratio = collections.defaultdict(list)   # 짝 → 같은 글자 비율
    whole_same = 0                          # 명식 하나에서 통째 같은 짝이 하나라도
    hook_twin = collections.Counter()
    for i, p in enumerate(pop):
        lens_id = lenses[i % len(lenses)]
        f = build_features(build_chart(p["year"], p["month"], p["day"], p["hour"],
                                      p["minute"], p["sex"], p["hour_known"],
                                      p["city"]), as_of=today)
        reps = {}
        hooks = {}
        for c in CON:
            reps[c] = {x["id"]: txt(x["html"])
                       for x in build_report(f, "sim", lens_id, a.tier, c,
                                             p["axis4"])["cuts"]}
            hooks[c] = "".join(txt(s["html"]) for s in
                               bank_mod.build_hook(f, c, p["axis4"], "", "그대"))
        hit = False
        for x, y in pairs:
            A, Bb = reps[x], reps[y]
            tot = sum(len(v) for v in A.values()) or 1
            same = sum(len(A[k]) for k in A if A.get(k) == Bb.get(k))
            ratio[(x, y)].append(same / tot)
            if same == tot:
                twin[(x, y)] += 1
                hit = True
            if hooks[x] == hooks[y]:
                hook_twin[(x, y)] += 1
        whole_same += hit

    n = a.n
    print("\n고민을 바꿨는데 같은 글 — 명식 %d개 · 목패 %s\n" % (n, a.tier))
    print("  한 명식에서 **통째로 같은 고민 짝**이 하나라도 있는 비율   %.1f%%   (%d/%d)"
          % (100.0 * whole_same / n, whole_same, n))
    print("\n  짝별 — 통째로 같은 비율 / 평균 겹침")
    rows = sorted(pairs, key=lambda k: -twin[k])
    for k in rows:
        xs = ratio[k]
        print("    %-12s %-12s 통째 같음 %5.1f%%   평균 겹침 %5.1f%%   훅도 같음 %5.1f%%"
              % (k[0], k[1], 100.0 * twin[k] / n,
                 100.0 * sum(xs) / len(xs), 100.0 * hook_twin[k] / n))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
