"""
연출 감사 — 화면마다 「다음 화가 보고 싶어지는가」.

    python tools/drama_audit.py            요약 + 표
    python tools/drama_audit.py --why      화면마다 모자란 것 전부

★ 관리자 화면과 **같은 것**을 봅니다 (engine/screenscan · engine/dramaturgy).
  도구가 따로 재면 "도구는 통과인데 화면은 붉은" 자리가 생깁니다.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine.dramaturgy import grade            # noqa: E402
from engine.screenscan import scan_all, summary  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--why", action="store_true", help="모자란 것 전부")
    a = ap.parse_args()

    rows = scan_all()
    s = summary(rows)
    print("연출 감사 — 화면 %d" % s["screens"])
    print("=" * 72)
    print("  당김 %3d · 팩폭 %3d · 충실 %3d · 쉬움 %3d   →  합 %d (%s)"
          % (s["pull"], s["bite"], s["depth"], s["plain"],
             s["total"], grade(s["total"])))
    print("-" * 72)
    print("%-5s %-10s %5s %5s %5s %5s %6s  %s"
          % ("id", "이름", "당김", "팩폭", "충실", "쉬움", "합", "액트아웃"))
    for r in sorted(rows, key=lambda r: r["total"]):
        print("%-5s %-10s %5d %5d %5d %5d %6d  %s"
              % (r["id"], r["title"], r["pull"], r["bite"], r["depth"],
                 r["plain"], r["total"], " · ".join(r["actout"]) or "—"))
        if a.why:
            for m in r["missing"]:
                print("        · %s" % m)
    print("-" * 72)
    print("가장 약한 다섯: %s"
          % " · ".join("%s %s(%d)" % (w["id"], w["title"], w["total"])
                       for w in s["weakest"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
