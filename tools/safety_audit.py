# -*- coding: utf-8 -*-
"""아픈 말에 **손잡이가 붙어 있는가** — 사람마다, 자리마다.

    python tools/safety_audit.py [인원수]

★ 왜 이 자가 있나 (2026-09-16)

  손님이 말했습니다 —

    "이거의 핵심은 정말 팩폭하면서도 동시에 위로를 줘야 한다는 거야.
     희망이 생겨야 해 삶에. 그로 인해서 자살하는 사람이 늘어나지
     않도록 설계해줘."

  이 집은 아픈 말을 **일부러** 합니다. 팩폭 축이 그걸 점수로 매기고,
  뱅크는 「틀릴 수 없는 말만 쓰기」 를 금합니다. 그건 맞습니다 —
  아프지 않은 말은 아무것도 안 바꿉니다.

  그런데 아프게 하는 집에는 **아프게 한 뒤의 책임**이 따릅니다.
  이 자는 그 책임이 지켜지는지만 봅니다. 셋을 셉니다.

      ① 아픈 말 뒤에 위로가 오는가          (blade → solace)
      ② 그 장에 앞을 보는 자리가 있는가      (hope)
      ③ 마지막이 아픈 말이 아닌가            (peak-end)

  그리고 **가장 중요한 넷째** —

      ④ 값을 안 치르고 나가는 사람도 손잡이를 받는가

  무료 구간에서 나가는 사람이 가장 많습니다. 그 사람들이 아픈 말만
  받고 나가면, 이 집은 아프게만 하고 문을 닫은 것입니다.
"""
from __future__ import annotations

import argparse
import collections
import random
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "services" / "api") not in sys.path:
    sys.path.insert(0, str(ROOT / "services" / "api"))
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from engine import bank as bank_mod                   # noqa: E402
from engine import dramaturgy as D                    # noqa: E402
from engine import heart as heart_mod                 # noqa: E402
from engine import screenscan as S                    # noqa: E402
from engine.calendar import build_chart               # noqa: E402
from engine.features import build_features            # noqa: E402
from engine.report import build_report                # noqa: E402
from journey_sim import people as sample_people       # noqa: E402

TODAY = date(2026, 9, 16)
CONCERNS = ("money", "work", "love", "people", "dir", "health")

# 앞을 보는 자리 — 이게 하나도 없으면 그 장은 진단서입니다.
FORWARD = {"hope", "week", "yongsin", "helper", "closing_cut", "counter"}
# 알아주는 자리 — 컷 통째가 손잡이인 것. 표는 집이 듭니다.
HOLD = set(heart_mod.HOLD_CUTS)

# ★ 아픈 말은 **팩폭 점수로 재면 안 됩니다.**
#
#   처음에 팩폭 축으로 「가장 아픈 컷」 을 골랐더니 **명식 표**가
#   나왔습니다. 갑자 한자가 스물넷이라 반증 가능한 말이 가장 많아서요.
#   표는 아프지 않습니다 — 세는 자리입니다.
#
#   집은 아픈 자리를 **스스로 짚어 두었습니다.** 훅의 `blade`(찌르는
#   한 줄)와 리포트의 `bite`(센 사실)입니다. 그 표지를 셉니다.
BLADE = re.compile(r'class="(?:blade|bite|stab)[" ]')
# 손잡이 — 아프게 한 뒤에 잡으라고 내미는 것
#   훅은 `bladerelief`, 리포트는 `hold` (engine/heart.hold_line).
#   자와 글이 **같은 표**를 봐야 합니다.
RELIEF = re.compile(r'class="(?:bladerelief|hold)[" ]')
# 말뭉치는 집이 듭니다 (engine/heart.HOLD_WORDS) — 두 벌을 들면
# 자가 위로를 아픈 말로 셉니다.
HOLD_WORD = re.compile(heart_mod.HOLD_WORDS)


def hurt(html: str) -> int:
    """이 컷에 아픈 말이 몇 줄인가 — 집이 짚어 둔 표지로."""
    return len(BLADE.findall(html or ""))


def holds(html: str) -> int:
    """이 컷에 손잡이가 몇 줄인가."""
    return (len(RELIEF.findall(html or ""))
            + len(HOLD_WORD.findall(D.plain(html))))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("n", nargs="?", type=int, default=300)
    a = ap.parse_args()

    rng = random.Random(20260916)
    pop = sample_people(a.n, seed=20260916)
    bad = collections.Counter()
    who = collections.defaultdict(set)
    ex: dict = {}
    hook_end = collections.Counter()
    n_ok = 0

    cur = {"i": -1}

    def note(k, ctx):
        bad[k] += 1
        who[k].add(cur["i"])
        ex.setdefault(k, ctx)

    for p in pop:
        try:
            f = build_features(
                build_chart(p["year"], p["month"], p["day"], p["hour"],
                            p["minute"], p["sex"], p["hour_known"], p["city"]),
                as_of=TODAY)
        except Exception:                              # noqa: BLE001
            continue
        concern = rng.choice(CONCERNS)
        n_ok += 1
        cur["i"] = n_ok

        # ── ④ 무료 구간 — 훅 다섯 마디
        segs = bank_mod.build_hook(f, concern, p["axis4"], "", "그대")
        hh = [x["html"] for x in segs]
        hook_end[concern] += 1
        if sum(hurt(x) for x in hh) and not sum(holds(x) for x in hh):
            note("훅 · 아픈 말만 있고 손잡이가 없소", concern)
        for i, x in enumerate(hh):
            if hurt(x) and not holds(x):
                note("훅 %d마디 · 아프게 하고 그냥 넘어가오" % (i + 1), concern)
        if hh and hurt(hh[-1]) and not holds(hh[-1]):
            note("훅 끝마디가 아픈 말로 끝나오", concern)

        # ── 리포트 세 등급
        for tier in ("free", "one", "all"):
            try:
                rep = build_report(f, "safety", "pungun", tier, concern,
                                   p["axis4"])
            except Exception as e:                     # noqa: BLE001
                note("리포트가 터짐(%s)" % tier, type(e).__name__)
                continue
            cuts = rep["cuts"]
            ids = [c["id"] for c in cuts]
            if not (set(ids) & HOLD):
                note("%s · 알아주는 자리가 없소" % tier, ids[:6])
            if "hope" not in ids and tier != "free":
                note("%s · 앞을 보는 자리(희망)가 없소" % tier, ids[:6])
            if ids and ids[-1] not in FORWARD:
                note("%s · 마지막이 앞을 보는 자리가 아니오" % tier, ids[-1])
            # 아픈 컷마다 — 그 안이거나 뒤 세 컷 안에 손잡이가 와야 하오
            for i, c in enumerate(cuts):
                if not hurt(c["html"]):
                    continue
                near = cuts[i:i + 4]
                if any(holds(x["html"]) for x in near):
                    continue
                if set(x["id"] for x in near) & HOLD:
                    continue
                note("%s · 아픈 컷 뒤에 손잡이가 없소" % tier,
                     "%s → %s" % (c["id"], [x["id"] for x in cuts[i + 1:i + 4]]))

    print("=" * 74)
    print("  아픈 말에 손잡이가 붙어 있는가 — %d명" % n_ok)
    print("=" * 74)
    if not bad:
        print("  [OK] 모든 자리에 손잡이가 붙어 있소")
        return 0
    for k, v in bad.most_common():
        print("  %-34s %5d건 · %4d명 (%5.1f%%)  %s"
              % (k, v, len(who[k]), 100.0 * len(who[k]) / max(1, n_ok),
                 str(ex.get(k))[:24]))
    print()
    print("-" * 74)
    print("  ★ 아프게 하는 집에는 아프게 한 뒤의 책임이 따르오.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
