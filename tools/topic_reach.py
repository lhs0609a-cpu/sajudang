# -*- coding: utf-8 -*-
"""물은 자리가 **글에 실제로 닿는가**.

    python tools/topic_reach.py [인원수]

★ 손님이 두 번째로 짚은 자리입니다

  "근데 돈을 선택했는데 왜 돈에 대한걸 말안해?"

  CLAUDE.md 에 이미 적혀 있는 자리요 — 「고민을 낱말로만 가르기」.
  2026-09-05 에 낱말을 갈라 놓고도 같은 말을 들었습니다. 그때 고친
  것은 **세는 값**을 갈라 놓은 것이고(engine/topic), 이 자는 그
  값이 손님이 읽는 **글자**까지 왔는지를 봅니다.

★ 두 가지를 셉니다

    ① 물은 자리의 말이 몇 줄에 나오는가   (돈·벌이·빚·통장 …)
    ② 고민을 바꾸면 글이 얼마나 갈리는가  (money vs work 글자 차이)

  ②가 낮으면 고민 칸은 이름표일 뿐입니다. ①이 낮으면 축은 갈렸는데
  **말이 안 따라온** 것입니다 — 손님 눈에는 둘 다 같습니다.
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT / "tools"))

from engine import bank as bank_mod                  # noqa: E402
from engine import dramaturgy as D                   # noqa: E402
from engine import screenscan as S                   # noqa: E402
from engine.calendar import build_chart              # noqa: E402
from engine.features import build_features           # noqa: E402
from engine.report import build_report               # noqa: E402
from journey_sim import people as sample_people      # noqa: E402

TODAY = date(2026, 9, 16)

# 물은 자리의 **살림의 말**. 명리 용어가 아니라 손님이 쓰는 말입니다 —
# 「재성이 하나요」 는 돈 얘기로 안 셉니다. 손님이 그 말을 모릅니다.
# ★ 말뭉치를 두 번 좁게 잡았습니다 (2026-09-17).
#
#   처음에 「마음 가는」 만 넣었더니 「사람을 만나고 **마음을 주어**
#   왔소」 를 사랑 얘기로 안 셌습니다. 자가 좁으면 멀쩡한 글을
#   「딴 얘기」 로 찍습니다 — 손잡이를 아픈 말로 셌던 자리와 같소.
#
#   손님이 **그 자리를 부를 때 쓰는 말**을 넣습니다. 다만 너무
#   넓히면 아무 글이나 통과하오 — 「마음」 하나로는 안 세고
#   「마음을 주」 「마음이 가」 처럼 자리가 보여야 셉니다.
# 표는 **엔진이 듭니다** — 무료로 열 컷을 고를 때 엔진도 같은 자를
# 써야 하기 때문입니다 (engine/topic · docs/45).
from engine.topic import CONCERNS, KO, WORDS, mentions   # noqa: E402,F401

def hits(text: str, concern: str) -> int:
    return len(re.findall(WORDS[concern], text))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("n", nargs="?", type=int, default=30)
    a = ap.parse_args()

    rows = {c: {"hook": [], "free": [], "hook_n": [], "free_n": []}
            for c in CONCERNS}
    same = []
    for p in sample_people(a.n, seed=20260917):
        try:
            f = build_features(
                build_chart(p["year"], p["month"], p["day"], p["hour"],
                            p["minute"], p["sex"], p["hour_known"], p["city"]),
                as_of=TODAY)
        except Exception:                              # noqa: BLE001
            continue
        txt = {}
        for c in CONCERNS:
            segs = bank_mod.build_hook(f, c, p["axis4"], "", "그대")
            h = D.plain(S.hook_html(segs))
            rep = build_report(f, "t", "pungun", "free", c, p["axis4"])
            fr = D.plain(" ".join(x["html"] for x in rep["cuts"]))
            txt[c] = (h, fr)
            rows[c]["hook"].append(hits(h, c))
            rows[c]["free"].append(hits(fr, c))
            rows[c]["hook_n"].append(len(h))
            rows[c]["free_n"].append(len(fr))
        # 고민을 바꾸면 글이 얼마나 갈리나 (돈 ↔ 일)
        a1, b1 = txt["money"][1], txt["work"][1]
        keep = sum(1 for x, y in zip(a1, b1) if x == y)
        same.append(100.0 * keep / max(1, max(len(a1), len(b1))))

    print("=" * 74)
    print("  물은 자리가 글에 닿는가 — %d명" % len(same))
    print("=" * 74)
    print("  %-5s %12s %12s %12s %12s"
          % ("물음", "훅 낱말", "훅 1천자당", "무료 낱말", "무료 1천자당"))
    for c in CONCERNS:
        r = rows[c]
        hk = sum(r["hook"]) / max(1, len(r["hook"]))
        fr = sum(r["free"]) / max(1, len(r["free"]))
        hn = sum(r["hook_n"]) / max(1, len(r["hook_n"]))
        fn = sum(r["free_n"]) / max(1, len(r["free_n"]))
        print("  %-5s %12.1f %12.1f %12.1f %12.1f"
              % (KO[c], hk, 1000 * hk / max(1, hn), fr, 1000 * fr / max(1, fn)))
    print()
    print("  돈과 일이 **글자 그대로 같은 비율**: %.0f%%"
          % (sum(same) / max(1, len(same))))
    print()
    print("-" * 74)
    print("  ★ 낱말은 손님이 쓰는 말만 셉니다 — 「재성이 하나요」 는")
    print("    돈 얘기로 안 셉니다. 손님이 그 말을 모르오.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
