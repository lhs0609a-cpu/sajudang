"""사주 4축과 사용자가 적는 넉 자가 몇 자리나 겹치는지 잰다.

    python tools/axis_spread.py

★ 무엇을 보는가
  겹친 자리 수의 분포와, **깊은 해석(GAP w)이 나가는 비율**.
  전에는 94%가 깊은 해석을 받았습니다. 넷 중 하나만 어긋나도
  그 사람의 지난 일을 단정하는 문장이 나갔다는 뜻입니다.

★ 사용자가 적는 넉 자는 어디서 오나
  한국에서 "MBTI 뭐야?" 에 답하는 사람은 거의 전부 무료
  16Personalities 결과를 말합니다. 그 표본(n=70,266, 2021)의
  I·N·F·P 편중을 그대로 씁니다. 정식 MBTI 한국 대표표본
  (n=19,070)과는 T/F 가 38%p 반대입니다 — 어느 쪽을 기준으로
  잡느냐가 이 수치를 통째로 뒤집습니다.
"""
from __future__ import annotations

import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine.calendar import build_chart          # noqa: E402
from engine.features import build_features       # noqa: E402
from engine import bank as B                     # noqa: E402

SEED = 20260826

# 16Personalities 한국 표본의 축별 비율 (첫 글자가 나올 확률)
USER_AXIS = {"EI": 0.487, "SN": 0.439, "TF": 0.327, "JP": 0.437}


def draw_axis4(rng: random.Random) -> str:
    return "".join(k[0] if rng.random() < p else k[1]
                   for k, p in USER_AXIS.items())


def main(n: int = 4000) -> int:
    rng = random.Random(SEED)
    matched = Counter()
    deep = 0
    saju_letter = Counter()
    for _ in range(n):
        c = build_chart(rng.randint(1955, 2010), rng.randint(1, 12),
                        rng.randint(1, 28), rng.randint(0, 23),
                        rng.randint(0, 59), rng.choice("FM"), True)
        f = build_features(c)
        for ch in B.axis_string(f):
            saju_letter[ch] += 1
        cmp = B.axis_compare(f, draw_axis4(rng))
        matched[len(cmp["matches"])] += 1
        deep += 1 if cmp["deep"] else 0

    print("표본 %d명 · 깊게 파는 문턱 = %d자리 어긋남\n" % (n, B.GAP_DEEP_AT))
    print("겹친 자리   사람 비율")
    for k in range(5):
        print("   %d칸     %6.1f%%  %s"
              % (k, 100 * matched[k] / n, "█" * int(40 * matched[k] / n)))
    print("\n깊은 해석이 나가는 비율  %.1f%%" % (100 * deep / n))
    print("(전에는 어긋난 자리가 하나만 있어도 나갔습니다 — 약 94%)")
    print("\n사주가 내는 넉 자")
    for k in ("EI", "SN", "TF", "JP"):
        a = 100 * saju_letter[k[0]] / n
        print("  %s : %s %.1f%% / %s %.1f%%   (사용자 %s %.1f%%)"
              % (k, k[0], a, k[1], 100 - a, k[0], 100 * USER_AXIS[k]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
