# -*- coding: utf-8 -*-
"""
훅이 **고른 고민을 보는가** — 같은 사람에게 고민만 바꿔서 대조합니다.

★ 왜 이 자를 만들었나 (2026-09-19)

  손님이 짚었습니다 — 「지금 훅이 너무 다 똑같아. 일이랑 사랑이랑
  다 똑같아.」

  그런데 있던 검사(`tests/test_hook_concern.py`)는 **통과하고**
  있었습니다. 그 검사가 센 것이 「이 마디가 갈리는가(한 글자라도)」
  였기 때문입니다. 한 글자만 달라도 그 마디는 「갈린 것」으로
  세어졌고, 다섯 마디가 다 한 줄씩 갈리니 100%가 나왔습니다.

  손님이 읽는 것은 **글자**입니다. 그래서 이 자는 갈래가 아니라
  **글자를 셉니다** — 여섯 고민에 글자 그대로 나가는 몫이 얼마인가.

      2026-09-19 아침   58.1%   (훅 10만 7천 자 중 6만 2천 자)
      2026-09-19 저녁   43.1%

★ 0%를 노리지 않습니다

  고정이라야 하는 글이 있습니다 — 이 집의 뼈대(「세어 보시오」
  「여태 그래 왔소」), 명식에서 나온 값(일간 · 태어난 계절 · 대운
  나이), 넉 자 대조. 그건 고민이 바꿀 자리가 아닙니다.

  보아야 할 것은 **어느 자리가** 안 갈리는가 입니다. 아래 두 표가
  그걸 찍습니다 — 마디별 · 마디 안의 몇 번째 문장.

쓰는 법
    python tools/hook_concern.py            # 40명
    python tools/hook_concern.py 120        # 더 넓게
    python tools/hook_concern.py 40 --show  # 안 갈리는 문장 목록
"""
from __future__ import annotations

import collections
import difflib
import itertools
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT / "tools"))

import journey_sim as J                                   # noqa: E402

def _concerns() -> tuple:
    """제품이 열어 둔 고민 칸을 그대로 받습니다.

    ★ `journey_sim.CONCERNS` 는 여섯에서 멈춰 있었습니다. 화면에 일곱째
      칸(부동산)이 열린 뒤에도 이 자가 그 칸을 한 번도 안 재서, 부동산
      훅이 돈과 **글자 그대로** 같은 것을 아무도 못 봤습니다 (2026-09-24).
    """
    import typing
    from schemas.api import Concern
    return tuple(typing.get_args(Concern))


CONCERNS = _concerns()
BOX = "이게 무슨 말인가"          # 용어 풀이 상자의 머리말

# 넘으면 빨간 불. 이 값을 올리려거든 **왜 그 자리가 고정이라야
# 하는지**를 먼저 적으시오 — 자를 글에 맞추면 그날로 자는 거울이 되오.
CEILING = {"0": 0.45, "1": 0.53, "2": 0.26, "2.5": 0.58, "3": 0.48}
TOTAL_CEILING = 0.45


def plain(h: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h or "")).strip()


def sents(t: str) -> list:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s*", t) if s.strip()]


def measure(n: int = 40, seed: int = 20260919, today: date | None = None) -> dict:
    """돌려주는 것: {"stages": {단: (안 갈린 글자, 전체)}, ...}"""
    today = today or date.today()
    pop = J.people(n, seed=seed)
    stage = collections.defaultdict(lambda: [0, 0])
    part = collections.defaultdict(lambda: [0, 0])      # 본문 / 용어풀이상자
    field = collections.defaultdict(lambda: [0, 0])     # question / yes / no
    pos = collections.defaultdict(lambda: [0, 0])       # (단, 몇 번째 문장)
    pair = collections.defaultdict(list)                # (고민, 고민) -> 겹침
    frozen: collections.Counter = collections.Counter()
    ok = 0
    for p in pop:
        try:
            ch = J.build_chart(p["year"], p["month"], p["day"], p["hour"],
                               p["minute"], p["sex"], p["hour_known"], p["city"])
            f = J.build_features(ch, as_of=today)
            byc = {c: J.bank_mod.build_hook(f, c, p["axis4"], "", "그대")
                   for c in CONCERNS}
        except Exception:                                # noqa: BLE001
            continue
        ok += 1
        for k in range(min(len(v) for v in byc.values())):
            st = byc[CONCERNS[0]][k].get("stage", str(k))
            for fld in ("question", "yes", "no"):
                vals = [plain(byc[c][k].get(fld)) for c in CONCERNS]
                ln = len(vals[0])
                field[fld][0] += ln if len(set(vals)) == 1 else 0
                field[fld][1] += ln
            texts = [plain(byc[c][k].get("html")) for c in CONCERNS]
            for a, b in itertools.combinations(range(len(CONCERNS)), 2):
                pair[(CONCERNS[a], CONCERNS[b])].append(
                    difflib.SequenceMatcher(None, texts[a], texts[b]).ratio())
            # 본문과 용어 풀이 상자를 갈라 셉니다 — 상자는 사전이라
            # 고민이 바꿀 자리가 아닌 낱말이 섞여 있습니다.
            for name, idx in (("본문", 0), ("용어풀이상자", 1)):
                arr = []
                for t in texts:
                    i = t.find(BOX)
                    arr.append(t[:i] if i >= 0 else (t if idx == 0 else ""))
                    if idx == 1 and i >= 0:
                        arr[-1] = t[i:]
                ss = [sents(x) for x in arr]
                for j, s in enumerate(ss[0]):
                    same = all(s in o for o in ss[1:])
                    ln = len(s)
                    part[name][0] += ln if same else 0
                    part[name][1] += ln
                    stage[st][0] += ln if same else 0
                    stage[st][1] += ln
                    if name == "본문":
                        pos[(st, j)][0] += ln if same else 0
                        pos[(st, j)][1] += ln
                        if same:
                            frozen[s] += 1
    return {"n": ok, "stages": dict(stage), "parts": dict(part),
            "fields": dict(field), "pos": dict(pos), "pairs": dict(pair),
            "frozen": frozen}


def _pct(v) -> float:
    return 100.0 * v[0] / v[1] if v[1] else 0.0


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    show = "--show" in sys.argv
    n = int(args[0]) if args else 40
    r = measure(n)
    if not r["n"]:
        print("표본을 하나도 못 세웠소")
        return 1

    tot = [sum(v[0] for v in r["parts"].values()),
           sum(v[1] for v in r["parts"].values())]
    print("훅이 고른 고민을 보는가 — 표본 %d명 · 고민 %d칸\n"
          % (r["n"], len(CONCERNS)))
    print("== 여섯 고민에 **글자 그대로** 나가는 몫 ==")
    for k, v in r["parts"].items():
        print("  %-12s %5.1f%%   (%d / %d자)" % (k, _pct(v), v[0], v[1]))
    print("  %-12s %5.1f%%   (%d / %d자)   문턱 %.0f%%"
          % ("합계", _pct(tot), tot[0], tot[1], 100 * TOTAL_CEILING))

    print("\n== 마디별 ==")
    bad = []
    for st, v in r["stages"].items():
        cap = CEILING.get(str(st))
        mark = ""
        if cap is not None and _pct(v) > 100 * cap:
            mark = "  ← 문턱 %.0f%% 넘음" % (100 * cap)
            bad.append(st)
        print("  %-5s %5.1f%% 안 갈림   (한 사람 %d자 중 %d자)%s"
              % (st, _pct(v), v[1] // r["n"], v[0] // r["n"], mark))

    print("\n== 손님이 누르는 자리 ==")
    for fld, v in r["fields"].items():
        print("  %-9s %5.1f%% 안 갈림" % (fld, _pct(v)))

    print("\n== 마디 안에서 **몇 번째 문장**이 안 갈리는가 ==")
    for st in r["stages"]:
        row = sorted((j, v) for (s, j), v in r["pos"].items() if s == st)
        print("  %-5s " % st + " ".join("%d:%3.0f%%" % (j, _pct(v))
                                        for j, v in row))

    print("\n== 고민 쌍별 글자 겹침 (1.00 = 완전히 같은 글) ==")
    rows = sorted(r["pairs"].items(), key=lambda kv: -sum(kv[1]) / len(kv[1]))
    for (a, b), v in rows[:5]:
        print("  %-6s vs %-6s  %.2f" % (a, b, sum(v) / len(v)))
    print("  …")
    for (a, b), v in rows[-3:]:
        print("  %-6s vs %-6s  %.2f" % (a, b, sum(v) / len(v)))

    if show:
        print("\n== 여섯 고민에 그대로 나가는 문장 ==")
        print("   (뼈대와 명식은 고정이 맞소. 겪은 일·비유·물음이 여기 "
              "있으면 그게 고칠 자리요)")
        for s, c in r["frozen"].most_common(40):
            print("  %3d회  %s" % (c, s[:88]))

    if _pct(tot) > 100 * TOTAL_CEILING:
        bad.append("합계")
    if bad:
        print("\n★ 문턱을 넘은 자리: %s" % " · ".join(str(x) for x in bad))
        return 1
    print("\n통과.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
