r"""
SHIP OS 관제탑 — 터미널에서 보는 판 (§39 · §40 · §50).

    .\dev.ps1 shipos              한눈에
    .\dev.ps1 shipos --all        의도적 제외까지 전부
    .\dev.ps1 shipos --gate       릴리스 게이트만 (막히면 exit 1)

★ 여기서 아무것도 세지 않습니다.
  `services/api/shipos.py` 한 자리가 셉니다. 이 파일은 **그린 것만**
  합니다 — 완료율이 두 벌이 되면 어느 쪽이 참인지 아무도 모릅니다.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

import shipos  # noqa: E402

BAR = "=" * 76
MARK = {"live": "●", "partial": "◐", "spec": "◔", "none": "○", "broken": "✕"}


def _bar(p: float, width: int = 40) -> str:
    n = max(0, min(width, round(p * width)))
    return "█" * n + "·" * (width - n)


def main(argv: list[str]) -> int:
    show_all = "--all" in argv
    gate_only = "--gate" in argv

    cov = shipos.coverage()
    wires = shipos.broken_wires()
    gate = shipos.release_gate()
    crit = [w for w in wires if w["severity"] == "critical"]

    if not gate_only:
        p = cov["overall"]
        print("\n" + BAR)
        print("  성신당 · 항해 관제탑")
        print(BAR)
        print("\n  전체 준비도   %s  %.1f%%" % (_bar(p), p * 100))
        t = cov["tally"]
        print("  기능          됨 %d · 절반 %d · 없음 %d · 끊김 %d"
              % (t.get("live", 0), t.get("partial", 0),
                 t.get("none", 0), t.get("broken", 0)))
        print("                의도적 제외 %d (까닭이 적힌 것만)" % cov["na"])

        # ── 역할 × 단계 ──────────────────────────────────
        print("\n  역할 × 여정 단계")
        last = None
        for s in shipos.by_stage():
            if s["role"] != last:
                print("\n    [%s]" % s["role"])
                last = s["role"]
            score = "  —  " if s["score"] is None else "%5.1f%%" % (s["score"] * 100)
            flag = "  ✕ %s" % ", ".join(s["broken"]) if s["broken"] else ""
            print("      %-12s %s  %s%s"
                  % (s["title"], score, " ".join(s["screens"]), flag))

        # ── 끊긴 배선 ────────────────────────────────────
        print("\n  끊긴 배선   critical %d · 전체 %d" % (len(crit), len(wires)))
        for w in wires:
            print("      %-4s %-8s %-38s %s"
                  % (w["id"], "막음" if w["severity"] == "critical" else "주의",
                     w["where"], w["what"]))
        if not wires:
            print("      끊긴 데가 없소.")

        # ── 남은 기능 ────────────────────────────────────
        rows = [r for r in cov["features"]
                if show_all or (r["applicability"] != "na" and r["status"] != "live")]
        print("\n  %s (%d)" % ("기능 전부" if show_all else "아직 남은 기능", len(rows)))
        for r in rows:
            tag = {"required": "필수", "conditional": "조건부", "na": "제외"}[r["applicability"]]
            print("      %s %-4s %-24s %-28s %5.1f%%"
                  % (MARK.get(r["status"], "?"), tag, r["id"], r["title"][:28],
                     r["score"] * 100))
            why = r.get("gap") or r.get("reason")
            if why and not show_all:
                print("           %s" % " ".join(str(why).split())[:120])

        # ── 다음에 무엇부터 ──────────────────────────────
        print("\n  다음에 무엇부터 (§40)")
        for n in shipos.next_actions(10):
            print("      P%d  %-22s %s" % (n["p"], n["why"], n["what"][:70]))
        if not shipos.next_actions(1):
            print("      지금 급한 것은 없소.")

    # ── 릴리스 게이트 ────────────────────────────────────
    print("\n" + BAR)
    print("  릴리스 게이트 (§36)")
    print(BAR)
    for row in gate["checks"]:
        detail = ""
        if not row["pass"] and row["detail"]:
            detail = "  ← %s" % (", ".join(map(str, row["detail"]))
                                 if isinstance(row["detail"], list) else row["detail"])
        print("  %-4s %-32s%s" % ("PASS" if row["pass"] else "FAIL",
                                  row["name"], detail))
    print()
    if gate["ready"]:
        print("  [READY] 내보내도 되오.")
    else:
        stuck = [r["name"] for r in gate["checks"] if not r["pass"]]
        print("  [NOT READY] 막힌 것 %d — %s" % (len(stuck), " · ".join(stuck)))
    print(BAR + "\n")

    # ★ 막혀 있으면 0 을 주지 않습니다. 관문에 걸어 두면 배포가 섭니다.
    return 0 if gate["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
