# -*- coding: utf-8 -*-
"""
값값 점수 — 치른 값이 아깝지 않은가. 100점 만점.

    python tools/worth_score.py

★ 셈은 여기 없습니다.

  `services/api/engine/worth.py` 가 셉니다. 이 파일은 **그것을 사람이
  읽게 그리는 자리**입니다. 두 군데서 세면 관리자 화면과 터미널이
  다른 숫자를 냅니다 — 그 순간 둘 다 못 믿게 됩니다.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import worth  # noqa: E402

BAR = 34


def bar(n: int) -> str:
    full = round(BAR * n / 100)
    return "█" * full + "·" * (BAR - full)


def main() -> int:
    worth.clear()
    d = worth.score()
    print("=" * 76)
    print("  값값 점수 — 치른 값이 아깝지 않은가")
    print("=" * 76)
    print("\n  %s  %3d / 100   「%s」" % (bar(d["total"]), d["total"], d["grade"]))
    print("  %s\n" % d["say"])
    for a in d["axes"]:
        print("  %-11s %s %3d   무게 %2d   %s"
              % (a["name"], bar(a["score"]), a["score"], a["weight"], a["ask"]))
        for p in a.get("parts", []):
            print("       %-26s %-12s %3d" % (p["k"], p["v"], p["s"]))
        if a.get("why"):
            print("       ※ %s" % a["why"])
        print()
    print("-" * 76)
    print("  먼저 볼 자리 — %s"
          % " · ".join("%s(%d)" % (w["name"], w["score"]) for w in d["weakest"]))
    print("""
  ★ 이건 관문이 아니라 **거울**입니다. 최저점을 걸어 두면 점수를
    올리려고 문장을 지우게 됩니다 — 뜬 말을 줄이려고 명리 용어를
    빼면 근거가 사라집니다. 두 축이 서로를 잡고 있습니다.""")
    print("-" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
