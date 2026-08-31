"""
틀릴 수 있는 말인가 — 문장이 무언가를 **금지**하는가.

    python tools/falsifiable.py            # 스무 명 전부
    python tools/falsifiable.py pungun     # 한 사람만
    python tools/falsifiable.py --hook     # 훅 다섯 단

★ 왜 이걸 재나

  "당신은 때때로 외롭다" 는 아무 관찰도 금지하지 않습니다. 어떤 결과가
  나와도 살아남으니 **틀릴 수가 없습니다.** 그래서 '맞다' 는 나와도
  '소름 돋는다' 는 안 나옵니다. 놀라움은 틀릴 수도 있었는데 맞았을
  때만 옵니다. (CLAUDE.md — 틀릴 수 없는 말만 쓰지 말 것)

  값을 치르는 순간은 뼈를 맞은 순간입니다. 그러니 문장이 몇 %나
  **부정 가능한가**를 세야 합니다. 이건 취향이 아니라 셀 수 있는 값입니다.

★ 무엇을 세나

  [금지한다]  숫자 · 관찰 가능한 행동 · 못 박은 때
      "서른둘에 바뀌오"          — 서른셋이면 틀립니다
      "정리했다면서 프로필을 본다" — 안 보면 틀립니다
      "관성이 셋이오"            — 둘이면 틀립니다

  [금지 안 한다]  빈도 완화어 · 양가 표현 · 성향 명사만
      "때때로 지치오"      — 안 지치는 사람이 없습니다
      "강하면서도 여리오"  — 어느 쪽이든 맞습니다
      "예민한 기질이오"    — 뭘 보면 아닌지 알 수 없습니다

★ 이 도구는 문장의 좋고 나쁨을 재지 않습니다.
  **부정 가능성**만 잽니다. 그것만으로도 어디가 비었는지 나옵니다.
"""
from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "services" / "api") not in sys.path:
    sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import bank as bank_mod              # noqa: E402
from engine import lens as lens_mod              # noqa: E402
from engine.calendar import build_chart          # noqa: E402
from engine.features import build_features       # noqa: E402
from engine.report import build_report, _plain   # noqa: E402

# 여러 명식으로 봅니다 — 한 사람만 보면 그 사람 운이 좋았을 뿐입니다.
CHARTS = [
    (1997, 3, 22, 14, 10, "F"),
    (1985, 11, 3, 7, 40, "M"),
    (2001, 6, 18, 21, 5, "F"),
    (1972, 9, 9, 3, 25, "M"),
]

# ── 금지하는 것 ────────────────────────────────────────────
NUM = re.compile(r"\d")                       # 나이 · 연도 · 개수
WHEN = re.compile(r"올해|내년|작년|이번 주|다음 달|스물|서른|마흔|쉰|예순")
ACT = re.compile(
    r"(본다|한다|간다|산다|온다|잔다|먹는다|미룬다|고른다|버린다|남긴다|"
    r"묻는다|적는다|센다|멈춘다|끊는다|참는다|미뤄|끊지|참고|"
    r"보오|하오|가오|접소|미루오|고치오|묻소|적소|셌소|끊소|참소|멈추오)")

# ── 금지 안 하는 것 ────────────────────────────────────────
FREQ = re.compile(r"때때로|가끔|종종|자주|대체로|보통|흔히|웬만|더러|이따금|곧잘")
BOTH = re.compile(r"하면서도|인 동시에|한편으로|이기도 하고|면서 또|이면서")
VAGUE = re.compile(r"성향|기질|경향|타입|스타일|편이오|편이|듯하|것 같")

SPLIT = re.compile(r"[.!?…]")


def judge(text: str) -> tuple:
    """(문장 수, 금지하는 문장, 금지 안 하는 문장)"""
    sents = [s.strip() for s in SPLIT.split(text) if len(s.strip()) > 4]
    hard = sum(1 for s in sents
               if NUM.search(s) or WHEN.search(s) or ACT.search(s))
    soft = sum(1 for s in sents
               if FREQ.search(s) or BOTH.search(s) or VAGUE.search(s))
    return len(sents), hard, soft


def features():
    for y, m, d, h, mi, sx in CHARTS:
        yield build_features(build_chart(y, m, d, h, mi, sx, True, "서울"))


BAR = "█"


def bar(pct: float, width: int = 22) -> str:
    n = int(round(pct / 100 * width))
    return BAR * n + "·" * (width - n)


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    only_hook = "--hook" in sys.argv
    print("=" * 76)
    print("  틀릴 수 있는 말인가 — 문장이 무엇을 금지하는가")
    print("=" * 76)

    fs = list(features())

    if only_hook:
        agg = collections.defaultdict(lambda: [0, 0, 0])
        for f in fs:
            for c in ("love", "money", "work", "people", "dir", "health"):
                for s in bank_mod.build_hook(f, c, "INFP", "가은", "그대"):
                    n, hard, soft = judge(_plain(s["html"]))
                    a = agg[s["stage"] + "단"]
                    a[0] += n; a[1] += hard; a[2] += soft
        print("\n훅 — 단별")
        print("  %-8s %6s %8s %7s  %s" % ("단", "문장", "금지함", "비율", ""))
        for k in sorted(agg):
            n, hard, soft = agg[k]
            p = 100 * hard / max(n, 1)
            print("  %-8s %6d %8d %6.0f%%  %s" % (k, n, hard, p, bar(p)))
        return 0

    lenses = [l for l in lens_mod.released()
              if not args or l["id"] in args]

    per_cut = collections.defaultdict(lambda: [0, 0, 0])
    per_lens = collections.defaultdict(lambda: [0, 0, 0])
    for f in fs:
        for l in lenses:
            tier = "one" if l.get("price") else "free"
            rep = build_report(f, "t", l["id"], tier, "love", "INFP",
                               name="가은")
            for c in rep["cuts"]:
                n, hard, soft = judge(_plain(c["html"]))
                for tgt in (per_cut[c["id"]], per_lens[l["id"]]):
                    tgt[0] += n; tgt[1] += hard; tgt[2] += soft

    print("\n컷별 — 금지하는 문장이 적은 것부터")
    print("  %-16s %6s %8s %7s  %s" % ("컷", "문장", "금지함", "비율", ""))
    rows = sorted(per_cut.items(), key=lambda kv: kv[1][1] / max(kv[1][0], 1))
    for cid, (n, hard, soft) in rows:
        p = 100 * hard / max(n, 1)
        mark = "  ← 뼈가 안 남소" if p < 10 else ""
        print("  %-16s %6d %8d %6.0f%%  %s%s"
              % (cid, n, hard, p, bar(p), mark))

    print("\n캐릭터별")
    print("  %-12s %6s %8s %7s  %s" % ("캐릭터", "문장", "금지함", "비율", ""))
    lrows = sorted(per_lens.items(), key=lambda kv: kv[1][1] / max(kv[1][0], 1))
    for lid, (n, hard, soft) in lrows:
        p = 100 * hard / max(n, 1)
        print("  %-12s %6d %8d %6.0f%%  %s"
              % (lens_mod.get(lid)["name"], n, hard, p, bar(p)))

    tot = sum(v[0] for v in per_cut.values())
    th = sum(v[1] for v in per_cut.values())
    ts = sum(v[2] for v in per_cut.values())
    print("\n" + "─" * 76)
    print("  전체 문장 %d · 금지하는 문장 %d (%.0f%%) · 무른 문장 %d (%.0f%%)"
          % (tot, th, 100 * th / tot, ts, 100 * ts / tot))
    dead = [c for c, v in per_cut.items() if v[1] == 0]
    if dead:
        print("  ★ 금지하는 문장이 **하나도 없는** 컷 %d개:" % len(dead))
        print("     " + " · ".join(sorted(dead)))
    print("─" * 76)
    print("  이 집은 셀 수 있는 것을 이미 갖고 있습니다 — 대운수(절입까지")
    print("  실제 일수) · 십신 개수 · 희소도 · 세운. 안 쓰고 있을 뿐입니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
