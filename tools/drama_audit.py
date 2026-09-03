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

    # ★ 화면 소스를 못 읽으면 **숫자를 안 냅니다.**
    #
    #   연출 점수는 `apps/web/**/page.tsx` 를 소스째 읽어서 셉니다.
    #   그게 없는 자리(배포 이미지 · 다른 디렉터리에서 실행)에서는
    #   엔진이 짓는 여섯 화면만 잡히고, 그래도 **합계는 그럴듯하게**
    #   나옵니다. 반쪽 숫자를 멀쩡한 점수로 읽고 고칠 자리를 정하면
    #   그게 제일 나쁩니다.
    if not s.get("has_source"):
        print("연출 점수를 못 재오 — 화면 소스(apps/web)가 없소.")
        print("  잡힌 것은 엔진이 짓는 %d화면뿐이라 숫자를 안 내오."
              % s["screens"])
        print("  저장소 뿌리에서 돌리시오:  .\dev.ps1 drama")
        return 1

    print("연출 감사 — 화면 %d" % s["screens"])
    print("=" * 72)
    print("  당김 %3d · 팩폭 %3d · 울림 %3d · 명확 %3d · 쉬움 %3d · 비유 %3d"
          % (s["pull"], s["bite"], s["heart"], s["clear"],
             s["plain"], s["figure"]))
    print("  →  합 %d (%s)" % (s["total"], grade(s["total"])))
    print("-" * 76)
    print("%-5s %-10s %4s %4s %4s %4s %4s %4s %5s  %s"
          % ("id", "이름", "당김", "팩폭", "울림", "명확", "쉬움", "비유",
             "합", "액트아웃"))
    for r in sorted(rows, key=lambda r: r["total"]):
        print("%-5s %-10s %4d %4d %4d %4d %4d %4d %5d  %s"
              % (r["id"], r["title"], r["pull"], r["bite"], r["heart"],
                 r["clear"], r["plain"], r["figure"], r["total"],
                 " · ".join(r["actout"]) or "—"))
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
