"""
값 사다리 — 값이 오르면 실제로 더 주는가, 얼마나 더 주는가.

★ 왜 생겼는가
  값 ↔ 컷수 상관은 +0.924 로 방향이 맞았는데 **폭이 없었습니다.**
  4,900원이 10컷 · 19,900원이 12컷 — 값은 4.06배인데 분량은 1.2배였고,
  12,900 · 9,900 · 6,900 · 4,900 **네 등급이 전부 10컷**이었습니다.
  등급이 넷인데 상품이 하나면 그건 값이 아니라 이름표입니다.

  상관만 보면 이게 안 보입니다. 상관은 **순서**를 보지 **폭**을 안 봅니다.
  그래서 이 도구는 세 가지를 같이 찍습니다 —
      등급마다 몇 컷인가        (같은 값이 여럿 있으면 최소를 봅니다)
      옆 등급과 몇 컷 차이인가   ← 0 이면 두 등급이 같은 상품입니다
      원당 몇 글자인가          ← 싼 쪽이 크면 비싼 쪽이 손해를 팔고 있습니다

  값을 매기는 표는 seed/lenses.json 한 곳, 사다리 표는
  engine/lens_cuts.OWN_FLOOR 한 곳입니다. 여기서 다시 적지 않습니다.

    python tools/price_ladder.py
    .\dev.ps1 ladder
"""
from __future__ import annotations

import re
import statistics as st
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import lens as lens_mod                      # noqa: E402
from engine import lens_cuts as lens_cuts_mod            # noqa: E402
from engine import report as report_mod                  # noqa: E402
from engine.calendar import build_chart                  # noqa: E402
from engine.features import build_features               # noqa: E402
from engine.report import build_report                   # noqa: E402

TAG = re.compile(r"<[^>]+>")
AS_OF = date(2026, 8, 27)

# 한 사람만 보면 우연에 속습니다. 시각 미상도 한 명 섞습니다 —
# 시주가 없으면 컷이 줄어드는 자리가 있는지 여기서 드러납니다.
PEOPLE = (
    (1993, 7, 14, 5, 20, "F", True),
    (1978, 11, 3, 21, 40, "M", True),
    (2001, 2, 19, 8, 5, "F", True),
    (1966, 6, 30, 14, 55, "M", True),
    (1988, 3, 5, 0, 0, "F", False),
)

# 추가 입력을 채워 넣는 값. extras 는 저장되지 않습니다.
FILL = {
    "blood": {"blood": {"type": "A"}},
    "image": {"image": {"pick": "door"}},
    "cards": {"cards": {"picks": ["gil", "mun", "san"]}},
    "partner": {"partner": {"year": 1990, "month": 4, "day": 11, "hour": 9,
                            "minute": 0, "sex": "M", "hour_known": True}},
    "context": {"context": {"situation": "start", "stance": "hold",
                            "months": 8}},
}
EXTRA_IDS = set(FILL)


def _people():
    for y, mo, d, h, mi, sex, known in PEOPLE:
        yield build_features(
            build_chart(y, mo, d, h, mi, sex, hour_known=known),
            as_of=AS_OF)


def _rows():
    people = list(_people())
    out = []
    for lens in lens_mod.all_lenses():
        if not lens.get("released"):
            continue
        lid, price = lens["id"], int(lens["price"])
        extras = FILL.get(lens_mod.required_input(lid))
        cuts, chars, own, lc_chars = [], [], [], []
        for f in people:
            rep = build_report(f, "t", lid, "one", "love", "INFP", extras)
            cuts.append(len(rep["cuts"]))
            chars.append(sum(len(TAG.sub("", c["html"])) for c in rep["cuts"]))
            mine = [c for c in rep["cuts"]
                    if c["id"].startswith("lc_") or c["id"] in EXTRA_IDS]
            own.append(len(mine))
            lc_chars.append(sum(len(TAG.sub("", c["html"])) for c in mine))
        out.append(dict(
            price=price, id=lid, name=lens["name"],
            need=lens_mod.required_input(lid) or "-",
            lc=lens_cuts_mod.owned(lid),
            floor=lens_cuts_mod.floor_for(price),
            target=lens_cuts_mod.target_for(price),
            cuts=min(cuts), own=min(own),
            chars=sum(chars) / len(chars),
            own_chars=sum(lc_chars) / len(lc_chars)))
    return out


def main() -> int:
    rows = _rows()
    rows.sort(key=lambda r: (-r["price"], r["id"]))

    print("캐릭터마다 — 「이 자리 하나」 (추가 입력은 채워서 잼)\n")
    print("%9s  %-10s %-10s %4s %4s %4s  %5s %5s %7s"
          % ("값", "캐릭터", "추가입력", "관점", "바닥", "목표",
             "자기몫", "총컷", "글자"))
    for r in rows:
        mark = " " if r["lc"] >= r["target"] else "·"
        print("%9s  %-10s %-10s %4d %4d %4d%s %5d %5d %7.0f"
              % (format(r["price"], ","),
                 r["name"], r["need"], r["lc"], r["floor"], r["target"],
                 mark, r["own"], r["cuts"], r["chars"]))

    # ── 등급마다 ────────────────────────────────────────────
    by = {}
    for r in rows:
        by.setdefault(r["price"], []).append(r)
    bands = sorted(by, reverse=True)

    print("\n등급마다 — 같은 값이 여럿이면 **가장 적게 주는 쪽**을 봅니다\n")
    print("%9s %4s %6s %6s %8s %9s %8s"
          % ("값", "인원", "총컷", "자기몫", "글자", "글자/원", "옆과 차"))
    prev = None
    flat = []
    for p in bands:
        g = by[p]
        cuts = min(x["cuts"] for x in g)
        own = min(x["own"] for x in g)
        ch = sum(x["chars"] for x in g) / len(g)
        gapstr = "-" if prev is None else "%+d컷" % (prev - cuts)
        if prev is not None and prev == cuts:
            flat.append(p)
        print("%9s %4d %6d %6d %8.0f %9.3f %8s"
              % (format(p, ","), len(g), cuts, own, ch,
                 ch / p if p else 0, gapstr))
        prev = cuts

    paid = [p for p in bands if p > 0]
    lo, hi = min(paid), max(paid)
    lo_cuts = min(x["cuts"] for x in by[lo])
    hi_cuts = min(x["cuts"] for x in by[hi])
    lo_ch = sum(x["chars"] for x in by[lo]) / len(by[lo])
    hi_ch = sum(x["chars"] for x in by[hi]) / len(by[hi])
    lo_own = min(x["own"] for x in by[lo])
    hi_own = min(x["own"] for x in by[hi])

    print("\n%s원 → %s원   값 %.2f배" % (format(lo, ","), format(hi, ","),
                                     hi / lo))
    print("   총컷    %2d → %2d   %.2f배" % (lo_cuts, hi_cuts, hi_cuts / lo_cuts))
    print("   자기몫  %2d → %2d   %s배"
          % (lo_own, hi_own, "∞" if not lo_own else "%.2f" % (hi_own / lo_own)))
    print("   글자  %4.0f → %4.0f   %.2f배" % (lo_ch, hi_ch, hi_ch / lo_ch))

    xs = [r["price"] for r in rows]
    for key, label in (("cuts", "컷수"), ("chars", "글자"), ("own", "자기몫")):
        ys = [r[key] for r in rows]
        mx, my = st.mean(xs), st.mean(ys)
        cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
        den = (sum((a - mx) ** 2 for a in xs)
               * sum((b - my) ** 2 for b in ys)) ** .5
        print("   값 ↔ %-4s 상관 %+.3f" % (label, cov / den if den else 0))

    # ── 값이 여는 층 ────────────────────────────────────────
    print("\n값이 여는 층 (engine/report.PRICE_RUNGS)")
    for threshold, cid in report_mod.PRICE_RUNGS:
        print("   %9s원 이상  + %s" % (format(threshold, ","), cid))

    # ── 남은 몫 ─────────────────────────────────────────────
    todo = [r for r in rows if r["lc"] < r["target"]]
    bad_floor = [r for r in rows if r["lc"] < r["floor"]]
    bad_step = [p for p in flat if p > 0]

    print()
    if bad_floor:
        for r in bad_floor:
            print("[X] %s(%s원) 관점 컷 %d개 — 바닥이 %d개입니다"
                  % (r["name"], format(r["price"], ","), r["lc"], r["floor"]))
    if todo:
        left = sum(r["target"] - r["lc"] for r in todo)
        print("남은 관점 컷 %d개 — 등급마다" % left)
        seen = []
        for r in sorted(todo, key=lambda x: -x["price"]):
            if r["price"] not in seen:
                seen.append(r["price"])
                print("   %9s원" % format(r["price"], ","))
            print("      %-10s %d → %d" % (r["name"], r["lc"], r["target"]))
    if bad_step:
        print("옆 등급과 컷 수가 같은 자리: %s"
              % " · ".join(format(p, ",") + "원" for p in bad_step))

    if bad_floor:
        print("\n[X] 값이 사다리를 못 지킵니다")
        return 1
    print("\n[OK] 바닥은 지켰습니다%s"
          % ("" if not todo else " (목표까지는 아직입니다)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
