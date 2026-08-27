"""문장 중복률 — 훅 · 유료 리포트 컷 · 일진. 문장을 추가할 때마다 실행.

    python tools/dup_rate.py            목표: 훅 전체 15% 이하 · 컷 쏠림 2% 이하
    python tools/dup_rate.py -n 5000

★ 가짓수보다 쏠림을 보세요
  `helper` 는 1,334가지였는데 길신이 없는 사람(10.3%)이 전부 **같은 한
  문장**을 받고 있었습니다. 가짓수만 보면 넉넉해 보입니다.
  그래서 '유효 가짓수'(1/Σp²) 와 '최다 점유'를 같이 찍습니다.
  유효 가짓수는 쏠린 만큼 줄어듭니다.

★ 왜 유료 컷을 같이 재는가
  전에는 훅만 쟀습니다. 그 결과 **유료 리포트가 무료 훅보다 더
  겹쳤습니다.** 용신 컷은 용신(5) × 신강여부(2) = 10가지가 상한이라
  문장을 더 써도 늘지 않는 구조였습니다. 3,000명 중 415명이 같은
  문장을 받았습니다.

★ 반복이 위험한 진짜 이유 — Barnum 효과
  Forer(1949) 이래 반복 검증된 결과: 전원에게 똑같은 성격 기술을 줘도
  평균 정확도 평가가 4.3/5 입니다. 한 사람은 다섯 중 하나를 받아도
  자기 얘기라고 느낍니다. 다만 결정적 단서가 붙습니다 —
  **"개인화되었다고 믿을 때만"** 그렇습니다.
  그래서 진짜 위험은 반복 자체가 아니라 **반복이 들통나는 것**입니다.
  일진은 매일·다수에게 동시에 나가 캡처 비교가 가장 쉬운 자리입니다.
"""
from __future__ import annotations

import random
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine.calendar import build_chart          # noqa: E402
from engine.features import build_features       # noqa: E402
from engine.bank import build_hook               # noqa: E402
from engine.report import build_report           # noqa: E402
from engine.daily import build_daily             # noqa: E402

CONCERNS = ["money", "work", "love", "people", "dir", "health"]
T16 = [a + b + c + d for a in "IE" for b in "NS" for c in "TF" for d in "JP"]

HOOK_MAX_DUP = 15.0      # 훅 전체 중복률 상한
CUT_MAX_SHARE = 2.0      # 컷 하나에서 한 문장이 가질 수 있는 최대 점유

# 관점 컷의 **본문만** 볼 때의 문턱. 근거 줄(읽은 글자를 대는 자리)은
# 사람마다 달라 가짓수를 크게 부풀립니다. 그것 때문에 본문이 겹치는
# 것이 안 보이면 통과한 숫자가 거짓말이 됩니다. 그래서 따로, 느슨하게,
# 그러나 **보이게** 잽니다.
PROSE_MAX_SHARE = 8.0

_tag = re.compile(r"<[^>]*>")
_num = re.compile(r"[0-9.]+")


def strip(t: str) -> str:
    return _num.sub("", _tag.sub("", t)).strip()


def effective(c: Counter) -> float:
    """유효 가짓수 1/Σp². 쏠린 만큼 줄어든다."""
    n = sum(c.values())
    if not n:
        return 0.0
    return 1.0 / sum((v / n) ** 2 for v in c.values())


def report_row(name: str, c: Counter, n: int) -> tuple[float, str]:
    top = c.most_common(1)[0][1] if c else 0
    share = 100.0 * top / n if n else 0.0
    return share, ("  %-11s %6d가지  유효 %7.1f  최다 %5.2f%%"
                   % (name, len(c), effective(c), share))


def _every_lens_cut(f):
    """스무 캐릭터의 관점 컷을 전부. 한 캐릭터만 보면 두어 개만 재게 됩니다."""
    from engine import lens as lens_mod
    from engine import lens_cuts as lens_cuts_mod
    for l in lens_mod.all_lenses():
        if not l.get("released"):
            continue
        for lc in lens_cuts_mod.build(f, l["id"]):
            yield lc


def main(n: int = 3000) -> int:
    rng = random.Random(20260826)
    seen = set()
    stages: dict[str, Counter] = {}
    cuts: dict[str, Counter] = {}
    # ★ 관점 컷은 캐릭터마다 다릅니다. 한 캐릭터만 보면 스무 컷 중
    #   두어 개만 재게 됩니다. 전 캐릭터를 돌립니다.
    lens_cuts_all: dict[str, Counter] = {}
    # ★ 그리고 **근거 줄을 뺀 본문만** 따로 잽니다.
    #   근거 줄은 글자를 대는 자리라 사람마다 다릅니다 — 그것 때문에
    #   본문이 겹치는 것이 가려지면, 통과한 숫자가 거짓말이 됩니다.
    lens_prose: dict[str, Counter] = {}
    daily_body: Counter = Counter()
    on = date(2026, 8, 27)          # 같은 날 — 서로 비교당하는 자리

    for _ in range(n):
        c = build_chart(rng.randint(1960, 2006), rng.randint(1, 12),
                        rng.randint(1, 28), rng.randint(0, 23), 0,
                        rng.choice("FM"), True)
        f = build_features(c)
        axis4 = rng.choice(T16 + [None])
        concern = rng.choice(CONCERNS)

        segs = build_hook(f, concern, axis4)
        for s in segs:
            stages.setdefault(s["stage"], Counter())[strip(s["html"])] += 1
        seen.add("".join(strip(s["html"]) for s in segs))

        rep = build_report(f, "cid", "pungun", "all", concern, axis4)
        for cut in rep["cuts"]:
            if cut["id"].startswith("lc_"):
                continue                    # 아래에서 전 캐릭터로 잽니다
            cuts.setdefault(cut["id"], Counter())[strip(cut["html"])] += 1

        for lc in _every_lens_cut(f):
            body = strip(lc["html"])
            lens_cuts_all.setdefault(lc["id"], Counter())[body] += 1
            lens_prose.setdefault(lc["id"], Counter())[
                body.split("읽은 자리")[0].strip()] += 1

        daily_body[strip(build_daily(f, on)["text"] + " ".join(
            build_daily(f, on)["notes"]))] += 1

    fail = []

    print("표본 %d명\n" % n)
    print("훅 5단")
    for k in sorted(stages):
        share, line = report_row(k, stages[k], n)
        print(line)
    dup = 100 - len(seen) / n * 100
    print("  %-11s %6d가지  중복률 %5.1f%%" % ("전체", len(seen), dup))
    if dup > HOOK_MAX_DUP:
        fail.append("훅 전체 중복률 %.1f%% > %.1f%%" % (dup, HOOK_MAX_DUP))

    print("\n유료 리포트 컷")
    for k in sorted(cuts):
        share, line = report_row(k, cuts[k], n)
        print(line + ("   ← 문턱 초과" if share > CUT_MAX_SHARE else ""))
        if share > CUT_MAX_SHARE:
            fail.append("컷 %s 최다 점유 %.2f%% > %.1f%%"
                        % (k, share, CUT_MAX_SHARE))

    print("\n관점 컷 — 그 캐릭터만 보는 자리 (전 20인)")
    for k in sorted(lens_cuts_all):
        tot = sum(lens_cuts_all[k].values())
        share, line = report_row(k, lens_cuts_all[k], tot)
        print(line + ("   ← 문턱 초과" if share > CUT_MAX_SHARE else ""))
        if share > CUT_MAX_SHARE:
            fail.append("관점 컷 %s 최다 점유 %.2f%% > %.1f%%"
                        % (k, share, CUT_MAX_SHARE))

    # ★ 근거 줄을 뺀 **본문만** 따로.
    #   근거 줄은 읽은 글자를 대는 자리라 사람마다 다릅니다. 그것 때문에
    #   본문이 겹치는 것이 안 보이면 통과한 숫자가 거짓말이 됩니다.
    print("\n  └ 근거 줄을 뺀 본문만 — 근거 줄이 쏠림을 가리지 않게")
    worst = []
    for k in sorted(lens_prose):
        c = lens_prose[k]
        worst.append((100 * max(c.values()) / sum(c.values()), k, len(c)))
    worst.sort(reverse=True)
    for share, k, kinds in worst[:6]:
        print("    %-22s %5d가지  본문 최다 %5.2f%%%s"
              % (k, kinds, share,
                 "   ← 본문이 쏠림" if share > PROSE_MAX_SHARE else ""))
    top = worst[0][0] if worst else 0.0
    print("    가장 큰 본문 점유 %.2f%%  (문턱 %.1f%%)" % (top, PROSE_MAX_SHARE))
    if top > PROSE_MAX_SHARE:
        fail.append("관점 컷 본문 최다 점유 %.2f%% > %.1f%% — 축이 고르지 "
                    "않습니다. 표를 늘리거나 고른 축으로 바꾸세요."
                    % (top, PROSE_MAX_SHARE))

    print("\n일진 (같은 날 %s)" % on)
    share, line = report_row("daily", daily_body, n)
    print(line + ("   ← 문턱 초과" if share > CUT_MAX_SHARE else ""))
    if share > CUT_MAX_SHARE:
        fail.append("일진 최다 점유 %.2f%% > %.1f%%" % (share, CUT_MAX_SHARE))

    if fail:
        print("\n[FAIL] 뱅크 확장 필요")
        for x in fail:
            print("  · " + x)
        return 1
    print("\n[OK]")
    return 0


if __name__ == "__main__":
    N = 3000
    if "-n" in sys.argv:
        N = int(sys.argv[sys.argv.index("-n") + 1])
    sys.exit(main(N))
