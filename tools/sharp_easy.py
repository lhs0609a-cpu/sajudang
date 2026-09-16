# -*- coding: utf-8 -*-
"""쉬움 × 날카로움 — **한 표로** 본다.

    python tools/sharp_easy.py

★ 손님이 물었다 — "엄청 쉽고 날카롭게 전체페이지 다 구성했어?"

  둘은 **서로 당깁니다.** 쉽게 하려고 뜬 말을 걷으면 문장이 순해지고,
  날카롭게 하려고 단정하면 어려워집니다. 그러니 따로 재면 둘 다
  속습니다 — 쉬움만 재면 무딘 글이 만점이고, 팩폭만 재면 아무도
  못 알아듣는 글이 만점입니다.

  한 표에 놓고 **둘 다 낮은 자리**부터 봅니다.

      쉬움    흐릿한 문장 비율 (tools/easy_audit — 낮을수록 좋소)
      날카로움 팩폭 축 (engine/dramaturgy — 높을수록 좋소)
"""
from __future__ import annotations

import collections
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT / "tools"))

import easy_audit as EA                                # noqa: E402
from engine import bank as bank_mod                    # noqa: E402
from engine import dramaturgy as D                     # noqa: E402
from engine import screenscan as SS                    # noqa: E402
from engine.calendar import build_chart                # noqa: E402
from engine.features import build_features             # noqa: E402
from engine.report import build_report                 # noqa: E402

TODAY = date(2026, 9, 17)
CONCERNS = ("money", "work", "love", "people", "dir", "health")
BIRTHS = [(1993, 11, 25, 15, 55, "M", True),
          (1978, 2, 4, 0, 20, "F", True)]


def main() -> int:
    tot = collections.Counter()
    dim = collections.Counter()
    bite = collections.defaultdict(list)

    def look(html, where):
        for s in EA.sentences(html):
            tot[where] += 1
            n, fig = EA.vague_of(s)
            if n >= 2 or fig:
                dim[where] += 1
        if len(D.plain(html)) > 120:
            bite[where].append(D.score(where[:2], where, html, "read")["bite"])

    for b in BIRTHS:
        y, m, d, h, mi, sex, known = b
        f = build_features(build_chart(y, m, d, h, mi, sex, known, "서울"),
                           as_of=TODAY)
        for concern in CONCERNS:
            look(SS.hook_html(bank_mod.build_hook(f, concern, "INTJ", "", "그대")),
                 "훅 5단")
            for c in build_report(f, "e", "pungun", "free", concern, "INTJ")["cuts"]:
                look(c["html"], c["id"])

    rows = {r["id"]: r for r in SS.scan_all()}
    for sid, txt in ((k, v[0]) for k, v in SS._screens().items()):
        if sid not in SS.KO:
            continue
        look(txt, "화면 " + sid)

    print("=" * 74)
    print("  쉽고 날카로운가 — 자리마다 둘을 같이")
    print("=" * 74)
    print("  %-14s %6s %7s %7s   %s" % ("자리", "문장", "흐릿%", "팩폭", ""))
    out = []
    for k in tot:
        if tot[k] < 6:
            continue
        sid = k.replace("화면 ", "")
        # ★ 화면의 팩폭은 **엔진 글을 끼운 값**으로 봅니다.
        #
        #   화면 제 글만 재면 a7 훅이 64 로 나옵니다 — 그 화면의 글은
        #   엔진이 짓고, 화면은 여는 줄과 버튼만 들고 있으니까요.
        #   관리자 화면이 보는 수(`scan_all`)와 같은 것을 써야 하오.
        if k.startswith("화면 "):
            b = (rows.get(sid, {}) or {}).get("bite", 0)
        else:
            b = round(sum(bite[k]) / len(bite[k])) if bite[k] else 0
        out.append((100.0 * dim[k] / tot[k], b, k, tot[k]))
    # 둘 다 나쁜 것부터 — 흐릿한데 무딘 자리
    out.sort(key=lambda x: (-(x[0] - x[1] / 4.0)))
    for pct, b, k, n in out:
        flag = ""
        if pct >= 12 and b < 90:
            flag = "  ★ 흐릿하고 무디오"
        elif pct >= 12:
            flag = "  ← 흐릿하오"
        elif b < 85:
            flag = "  ← 무디오"
        print("  %-14s %6d %6.0f%% %7d   %s" % (k, n, pct, b, flag))
    t, d2 = sum(tot.values()), sum(dim.values())
    print()
    print("  합 %d문장 · 흐릿 %.0f%%" % (t, 100.0 * d2 / max(1, t)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
