"""
훑어읽기 감사 — 강조만 읽어도 말이 되는가

    .\\dev.ps1 skim              재고 문턱을 넘는지 본다
    .\\dev.ps1 skim --show       형광펜만 이어 붙인 글을 사람이 읽어 본다
    .\\dev.ps1 skim --lens pungun --concern work

★ 무엇을 재는가

  손님이 19,900원짜리 한 장(29컷 12,582자)을 다 읽지 않습니다.
  그래서 강조 넷을 얹었습니다 (engine/skim.py) —
  굵게(센 사실) · 형광펜(그 컷의 결론) · 밑줄(할 것) · 수(나이·해·갯수).

  잴 것은 **형광펜만 이어 읽었을 때 말이 되는가**입니다. 그건 기계가
  못 봅니다. 그래서 이 도구는 두 가지를 합니다 —

      ① 셀 수 있는 것을 센다   줄 수 · 길이 · 겹침 · 빈 리포트
      ② 못 세는 것은 **보여 준다**  `--show` 로 이어 붙여 사람에게

★ 문턱을 왜 그렇게 두는가

  형광펜이 너무 적으면 훑어읽기가 안 되고, 너무 많으면 그건 요약이
  아니라 또 본문입니다. 재보니 한 장에 열둘~열여덟 줄이 나옵니다.
  아래 문턱은 그 언저리에 둡니다.

★ 없는 데는 안 칠합니다.
  컷마다 하나씩 채우려고 아무 줄에나 칠하면 손님이 결론이 아닌 것을
  결론으로 읽습니다. 그러니 「형광펜 없는 컷」은 흠이 아닙니다.
  흠은 **리포트 한 장에 형광펜이 너무 적은 것**입니다.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "services", "api"))
os.environ.setdefault("STORE_PATH", os.path.join(ROOT, ".skim.sqlite"))

from engine import lens as lens_mod                      # noqa: E402
from engine import skim as skim_mod                      # noqa: E402
from engine.calendar import build_chart                  # noqa: E402
from engine.features import build_features               # noqa: E402
from engine.report import build_report                   # noqa: E402

TAG = re.compile(r"<[^>]+>")
U = re.compile(r"<u>(.*?)</u>", re.S)
NU = re.compile(r'<span class="nu">(.*?)</span>', re.S)

CONCERNS = ("money", "work", "love", "people", "dir", "health")

# 한 장에 형광펜이 적어도 몇 줄이어야 훑어읽기가 되는가.
PEN_MIN = 8
# 형광펜 한 줄이 이보다 길면 그건 요약이 아니라 문단입니다.
PEN_CHARS_MAX = 90

# ★ 위쪽 문턱은 **줄 수가 아니라 몫**으로 잽니다.
#
#   처음엔 「22줄까지」로 두었는데, 컷이 스물아홉에서 서른셋으로 늘자
#   바로 걸렸습니다. 줄 수는 리포트가 길어지면 같이 늘어나는 값이라
#   문턱으로 쓸 수가 없습니다.
#
#   요약인지 아닌지를 정하는 것은 **본문에서 차지하는 몫**입니다.
#   한 장의 12%를 넘게 칠했으면 그건 요약이 아니라 또 본문입니다.
PEN_SHARE_MAX = 0.12

# 서로 다른 명식 넷. 한 사람만 보면 우연에 속습니다.
PEOPLE = ((1993, 11, 25, 15, 55, "M"), (1978, 3, 3, 21, 40, "F"),
          (2001, 7, 19, 8, 5, "F"), (1966, 6, 30, 14, 55, "M"))


def _people():
    for spec in PEOPLE:
        yield build_features(build_chart(*spec), as_of=date(2026, 9, 7))


def _one(f, lens_id, concern):
    rep = build_report(f, "t", lens_id, "one", concern, "INFP")
    pens, unders, nums, cuts, body = [], [], 0, [], 0
    for c in rep["cuts"]:
        h = c["html"] or ""
        p = skim_mod.pen_lines(h)
        u = [TAG.sub("", x).strip() for x in U.findall(h)]
        nums += len(NU.findall(h))
        body += len(TAG.sub("", h).strip())
        pens += p
        unders += u
        cuts.append((c["id"], c.get("title") or "", p, u))
    return rep, pens, unders, nums, cuts, body


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true",
                    help="형광펜만 이어 붙인 글을 낸다")
    ap.add_argument("--lens", default="pungun")
    ap.add_argument("--concern", default="work")
    args = ap.parse_args()

    print("훑어읽기 감사 — 강조만 읽어도 말이 되는가")
    print("=" * 74)

    if args.show:
        f = next(_people())
        rep, pens, unders, nums, cuts, body = _one(f, args.lens, args.concern)
        lens = lens_mod.get(args.lens)
        pen_chars = sum(len(x) for x in pens)
        print("%s · %s · %s원 · %d컷 · %s자 (형광펜 %s자 · %.1f%%)"
              % (lens["name"], args.concern, format(lens["price"], ","),
                 len(rep["cuts"]), format(body, ","), format(pen_chars, ","),
                 100 * pen_chars / max(body, 1)))
        print("-" * 74)
        print("[형광펜만 이어 읽기]  %d줄" % len(pens))
        for i, line in enumerate(pens, 1):
            print("  %2d. %s" % (i, line))
        print()
        print("[밑줄 — 손님이 할 것]  %d줄" % len(unders))
        for i, line in enumerate(unders, 1):
            print("  %2d. %s" % (i, line))
        print()
        print("[형광펜이 없는 컷]")
        for cid, title, p, _u in cuts:
            if not p:
                print("   · %-22s %s" % (cid, title))
        return 0

    # ── 전량 ────────────────────────────────────────────
    released = [l["id"] for l in lens_mod.released()]
    rows, thin, fat, long_lines = [], [], [], []
    people = list(_people())
    # ★ `hash()` 를 쓰면 안 됩니다 — 파이썬은 프로세스마다 해시 씨앗을
    #   바꿉니다. 같은 저장소에서 돌릴 때마다 다른 사람이 뽑혀 [OK] 와
    #   [FAIL] 이 번갈아 나왔습니다. 재는 도구가 흔들리면 못 씁니다.
    for li, lid in enumerate(released):
        for ci, concern in enumerate(CONCERNS):
            f = people[(li + ci) % len(people)]
            rep, pens, unders, nums, cuts, body = _one(f, lid, concern)
            share = sum(len(x) for x in pens) / max(body, 1)
            rows.append((lid, concern, len(rep["cuts"]), len(pens),
                         len(unders), nums, share))
            if len(pens) < PEN_MIN:
                thin.append((lid, concern, len(pens)))
            if share > PEN_SHARE_MAX:
                fat.append((lid, concern, share))
            for line in pens:
                if len(line) > PEN_CHARS_MAX:
                    long_lines.append((lid, concern, len(line), line[:50]))

    n = len(rows)
    cuts_avg = sum(r[2] for r in rows) / n
    pen_avg = sum(r[3] for r in rows) / n
    u_avg = sum(r[4] for r in rows) / n
    nu_avg = sum(r[5] for r in rows) / n
    print("리포트 %d장 (스무 사람 × 고민 여섯)" % n)
    print("  한 장 평균   컷 %.1f · 형광펜 %.1f줄 · 밑줄 %.1f줄 · 수 %.1f"
          % (cuts_avg, pen_avg, u_avg, nu_avg))
    print("  형광펜 폭    %d ~ %d줄 · 본문의 %.1f~%.1f%%"
          % (min(r[3] for r in rows), max(r[3] for r in rows),
             100 * min(r[6] for r in rows), 100 * max(r[6] for r in rows)))
    print()

    # 값 등급마다 — 비싼 자리가 훑어읽기도 더 주는가
    print("값 등급마다 — 비싼 자리가 훑어읽기도 더 주는가")
    by_price = {}
    for lid, concern, cuts, pen, u, nu, _sh in rows:
        p = int(lens_mod.get(lid)["price"])
        by_price.setdefault(p, []).append((cuts, pen, u))
    for p in sorted(by_price, reverse=True):
        v = by_price[p]
        print("  %8s원   컷 %4.1f · 형광펜 %4.1f줄 · 밑줄 %3.1f줄"
              % (format(p, ","), sum(x[0] for x in v) / len(v),
                 sum(x[1] for x in v) / len(v),
                 sum(x[2] for x in v) / len(v)))
    print()

    bad = 0
    if thin:
        bad += len(thin)
        print("형광펜이 %d줄 미만 — 훑어읽기가 안 되오  (%d장)"
              % (PEN_MIN, len(thin)))
        for lid, concern, k in thin[:10]:
            print("   · %-11s %-7s %d줄" % (lid, concern, k))
    if fat:
        bad += len(fat)
        print("형광펜이 본문의 %.0f%% 초과 — 요약이 아니라 또 본문이오  (%d장)"
              % (100 * PEN_SHARE_MAX, len(fat)))
        for lid, concern, k in fat[:10]:
            print("   · %-11s %-7s %.1f%%" % (lid, concern, 100 * k))
    if long_lines:
        bad += len(long_lines)
        print("형광펜 한 줄이 %d자 초과  (%d줄)"
              % (PEN_CHARS_MAX, len(long_lines)))
        for lid, concern, k, s in long_lines[:8]:
            print("   · %-11s %-7s %3d자  %s…" % (lid, concern, k, s))

    print()
    if bad:
        print("[FAIL] 고칠 것 %d건" % bad)
        print("  형광펜은 `.bite` 단락과 **문장 꼴 굵게**에만 붙소.")
        print("  적으면 그 캐릭터 뱅크에 결론 줄이 없다는 뜻이오 —")
        print("  아무 줄에나 칠하지 말고 `.bite` 를 한 줄 쓰시오.")
        return 1
    print("[OK] 한 장에 형광펜 %.1f줄 · 밑줄 %.1f줄 · 본문의 %.1f%%"
          % (pen_avg, u_avg, 100 * sum(r[6] for r in rows) / n))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
