# -*- coding: utf-8 -*-
"""쉬운 말 감사 — **스무 사람 · 모든 화면** 전부.

    python tools/easy_all.py [인원수]

★ 왜 넓히나 (2026-09-17)

  `tools/easy_audit.py` 는 좋은 자인데 **한 사람의 한 장**만 봅니다.
  손님이 시킨 것은 「전체 캐릭터부터 모든 페이지 전부」요.

  쉬움은 **자리마다 다릅니다.** 관점 컷은 캐릭터마다 딴 글이고,
  훅은 값을 안 치른 사람이 가장 오래 머무는 자리이며, 화면 글은
  엔진이 손을 안 댑니다. 한 사람만 재면 스무 벌 중 한 벌만 본 것이오.

★ 자는 하나입니다

  흐릿한지 가리는 셈은 `easy_audit` 것을 그대로 빌려 씁니다. 두 벌을
  들면 한쪽만 고쳐져 「도구는 푸른데 화면은 붉은」 자리가 생깁니다.
"""
from __future__ import annotations

import argparse
import collections
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT / "tools"))

import easy_audit as EA                                # noqa: E402
from engine import bank as bank_mod                    # noqa: E402
from engine import lens as lens_mod                    # noqa: E402
from engine import screenscan as SS                    # noqa: E402
from engine.calendar import build_chart                # noqa: E402
from engine.features import build_features             # noqa: E402
from engine.report import build_report                 # noqa: E402

TODAY = date(2026, 9, 17)
CONCERNS = ("money", "work", "love", "people", "dir", "health")
BIRTHS = [(1993, 11, 25, 15, 55, "M", True),
          (1978, 2, 4, 0, 20, "F", True),
          (1966, 12, 31, None, None, "M", False)]


def _f(b):
    y, m, d, h, mi, sex, known = b
    return build_features(build_chart(y, m, d, h, mi, sex, known, "서울"),
                          as_of=TODAY)


def scan(html: str, where: str, tot: collections.Counter,
         bad: collections.Counter, ex: dict) -> None:
    for s in EA.sentences(html):
        tot[where] += 1
        n, fig = EA.vague_of(s)
        if n >= 2 or fig:
            bad[where] += 1
            ex.setdefault(where, s)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("n", nargs="?", type=int, default=3,
                    help="사람 수 (많을수록 오래 걸리오)")
    a = ap.parse_args()

    lenses = [l["id"] for l in lens_mod.released()]
    tot, bad, ex = collections.Counter(), collections.Counter(), {}
    per_lens_tot, per_lens_bad = collections.Counter(), collections.Counter()

    print("=" * 74)
    print("  쉬운 말 — 스무 사람 · 모든 화면 (%d명 × %d고민 × %d사람)"
          % (min(a.n, len(BIRTHS)), len(CONCERNS), len(lenses)))
    print("=" * 74)

    for b in BIRTHS[:a.n]:
        f = _f(b)
        for concern in CONCERNS:
            segs = bank_mod.build_hook(f, concern, "INTJ", "", "그대")
            scan(SS.hook_html(segs), "훅 5단", tot, bad, ex)
            for lid in lenses:
                rep = build_report(f, "e", lid, "free", concern, "INTJ")
                for c in rep["cuts"]:
                    key = "관점 컷" if c["id"].startswith("lc_") else c["id"]
                    scan(c["html"], key, tot, bad, ex)
                    if c["id"].startswith("lc_"):
                        for s in EA.sentences(c["html"]):
                            per_lens_tot[lid] += 1
                            n, fig = EA.vague_of(s)
                            if n >= 2 or fig:
                                per_lens_bad[lid] += 1

    # ── 화면이 제 손으로 쓴 글
    for sid, txt in ((k, v[0]) for k, v in SS._screens().items()):
        if sid in SS.KO:
            scan(txt, "화면 " + sid, tot, bad, ex)

    print("  %-14s %7s %7s %6s   %s" % ("자리", "문장", "흐릿", "%", "보기"))
    rows = sorted(tot, key=lambda k: -(bad[k] / max(1, tot[k])))
    for k in rows:
        if tot[k] < 4:
            continue
        pct = 100.0 * bad[k] / tot[k]
        if not bad[k]:
            continue
        print("  %-14s %7d %7d %5.0f%%   %s"
              % (k, tot[k], bad[k], pct, (ex.get(k) or "")[:34]))
    t, d = sum(tot.values()), sum(bad.values())
    print()
    print("  합 %d문장 중 흐릿한 것 %d (%.0f%%)" % (t, d, 100.0 * d / max(1, t)))
    print()
    print("  스무 사람 · 관점 컷만 (흐릿한 비율)")
    for lid in sorted(per_lens_tot, key=lambda k: -(per_lens_bad[k] / max(1, per_lens_tot[k]))):
        print("     %-10s %4d문장 · %3d (%2.0f%%)"
              % (lid, per_lens_tot[lid], per_lens_bad[lid],
                 100.0 * per_lens_bad[lid] / max(1, per_lens_tot[lid])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
