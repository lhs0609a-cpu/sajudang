# -*- coding: utf-8 -*-
"""
이탈 묶음을 합친다 — 1만 명씩 여러 번 돌린 것을 한 표로.

    python tools/dropout_merge.py out/100k/*.json

★ 왜 나눠 돌리나

  `dropout_sim` 은 한 사람마다 잰 것을 **끝까지 들고 있어야** 합니다.
  「고칠 차례」를 같은 난수로 다시 돌려, 고친 것 하나만 달라지게
  해야 하기 때문입니다. 그래서 인원에 비례해 메모리가 늡니다 —
  10만 명을 한 번에 돌리면 못 버팁니다(실제로 1만 명에서도 다른
  프로그램과 겹치면 죽었습니다).

  씨앗을 바꿔 1만 명씩 열 번 돌리면 **10만 명을 본 것과 같습니다.**
  사람은 씨앗마다 새로 뽑히고(겹침 0.14%), 묶음끼리는 서로 모릅니다.

★ 무엇을 어떻게 합치나

    값 치른 사람 · 도달   더합니다 (세는 값)
    이탈 자리·축         더합니다
    화면 아홉 축         묶음마다 같습니다 — 화면 글은 안 변하니 첫 것을 씁니다
    고칠 차례            묶음마다의 이득을 더합니다

★ 묶음이 서로 어긋나면 말합니다

  화면 글을 고치고 이어 돌리면 앞 묶음과 뒤 묶음이 다른 글을 본
  것입니다. 그걸 그냥 더하면 섞인 수가 됩니다. 아홉 축이 묶음마다
  다르면 멈추고 알립니다.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()

    paths: list[Path] = []
    for pat in a.files:
        paths += [Path(x) for x in sorted(glob.glob(pat))]
    if not paths:
        print("합칠 것이 없소")
        return 2

    tot_n = 0
    cases = ("비관 가정", "기준 가정", "낙관 가정")
    paid = collections.Counter()
    reach = collections.Counter()
    left = {c: collections.Counter() for c in cases}
    why = collections.Counter()
    fixes = collections.defaultdict(lambda: collections.Counter())
    screens0 = None
    mismatch = []

    for p in paths:
        d = json.loads(p.read_text(encoding="utf8"))
        tot_n += d["n"]
        if screens0 is None:
            screens0 = d["screens"]
            path = d["path"]
        elif d["screens"] != screens0:
            diff = [s for s in d["screens"]
                    if d["screens"].get(s) != screens0.get(s)]
            mismatch.append((p.name, diff[:4]))
        for c in cases:
            f = d["funnel"][c]
            paid[c] += f["paid"]
            reach[c] += f["reach"]
            for k, v in f["left"].items():
                left[c][k] += v
        for k, v in d["why"].items():
            why[k] += v
        for row in d["fixes"]:
            key = (row["screen"], row["axis"], row["now"])
            for c in cases:
                fixes[key][c] += row["gain_paid"].get(c, 0) \
                    if isinstance(row["gain_paid"], dict) else 0
            fixes[key]["reach"] += (row["gain_reach"].get("기준 가정", 0)
                                    if isinstance(row["gain_reach"], dict) else 0)

    print("=" * 78)
    print("  이탈 — %d명 (%d묶음을 합친 것)" % (tot_n, len(paths)))
    print("=" * 78)

    if mismatch:
        print()
        print("  ★ 묶음끼리 화면 글이 다르오 — 섞인 수가 되오:")
        for name, diff in mismatch:
            print("     %s  %s" % (name, " ".join(diff)))
        print("     같은 글로 다시 돌리시오.")
        return 1

    print()
    print("  값을 치른 사람")
    for c in cases:
        print("    %-8s %7d명 (%.2f%%)   목패까지 %7d명"
              % (c, paid[c], 100.0 * paid[c] / tot_n, reach[c]))

    print()
    print("  이탈 — 화면별 (기준 가정)")
    base = left["기준 가정"]
    tot_left = sum(base.values())
    for sid, v in base.most_common(20):
        print("    %-10s %7d  %5.1f%%" % (sid, v, 100.0 * v / max(1, tot_left)))

    print()
    print("  이탈 — 축만 모으면 (기준 가정)")
    axis = collections.Counter()
    for k, v in why.items():
        sid, _, ax = k.partition("|")
        axis[ax] += v
    tw = sum(axis.values())
    for ax, v in axis.most_common():
        bar = "█" * int(round(22.0 * v / max(1, tw)))
        print("    %-10s %7d  %5.1f%%  %s" % (ax, v, 100.0 * v / max(1, tw), bar))

    print()
    print("  이탈 — 화면 × 축 상위 (기준 가정)")
    for k, v in why.most_common(16):
        sid, _, ax = k.partition("|")
        print("    %-10s %-10s %7d  %5.1f%%"
              % (sid, ax, v, 100.0 * v / max(1, tw)))

    print()
    print("  고칠 차례 — 그 축을 85점으로 올리면 값 치른 사람이 몇 늘어나는가")
    print("    %-5s %-10s %5s %9s %9s %9s"
          % ("화면", "축", "지금", "비관", "기준", "낙관"))
    rows = sorted(fixes.items(), key=lambda kv: -kv[1]["기준 가정"])
    for (sid, ax, now), g in rows[:14]:
        print("    %-5s %-10s %5d %+9d %+9d %+9d"
              % (sid, ax, now, g["비관 가정"], g["기준 가정"], g["낙관 가정"]))

    print()
    print("-" * 78)
    print("  ★ 세 가정에서 **차례가 안 바뀌는 것**만 먼저 고치시오.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
