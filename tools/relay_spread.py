"""릴레이 1순위가 얼마나 고르게 퍼지는지 잰다.

    python tools/relay_spread.py             # 지금 설정으로
    python tools/relay_spread.py --lambda 0  # λ 를 바꿔가며 비교

★ 무엇을 보는가
  최다 점유율과 **1순위에 한 번이라도 오르는 캐릭터 수**. 둘을 같이
  봐야 합니다. λ를 키우면 최다는 내려가지만 간판 캐릭터가 죽습니다.
  그건 쏠림을 푼 게 아니라 뒤집은 것입니다.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import relay as RL                   # noqa: E402
from engine import lens as LENS                  # noqa: E402
from tools import population as POP              # noqa: E402


def run(n: int, lam: float | None) -> int:
    if lam is not None:
        RL._tuning = lambda: {"exposure_lambda": lam,
                              "complement_weight": 0.15}
    first = Counter()
    anywhere = Counter()
    none_at_all = 0
    for f in POP.sample(n):
        top = RL.rerank(RL.evaluate(f))[:RL.TOP_N]
        if not top:
            none_at_all += 1
            continue
        first[top[0]["lens_id"]] += 1
        for t in top:
            anywhere[t["lens_id"]] += 1

    total = sum(first.values())
    print("%s · λ=%s" % (POP.banner(n), RL._tuning()["exposure_lambda"]))
    print("규칙이 하나도 안 걸린 사람 %d명 (%.1f%%) — 무료 캐릭터(%s)가 섭니다\n"
          % (none_at_all, 100 * none_at_all / n, RL.FALLBACK_LENS))
    print("%-11s %8s %8s" % ("lens", "1순위", "상위3"))
    for lid, cnt in first.most_common():
        print("%-11s %7.1f%% %7.1f%%"
              % (lid, 100 * cnt / total, 100 * anywhere[lid] / n))

    all_ids = {l["id"] for l in LENS.all_lenses()}
    never_first = sorted(all_ids - set(first))
    never_any = sorted(all_ids - set(anywhere))
    print("\n최다 1순위 %.1f%% · 1순위에 오르는 캐릭터 %d/%d"
          % (100 * first.most_common(1)[0][1] / total, len(first), len(all_ids)))
    print("상위3에 한 번이라도 드는 캐릭터 %d/%d" % (len(anywhere), len(all_ids)))
    if never_first:
        print("★ 1순위가 한 번도 없는 캐릭터: %s" % ", ".join(never_first))
    if never_any:
        print("★ 아예 안 나오는 캐릭터: %s" % ", ".join(never_any))
    return 0


def main() -> int:
    lam = None
    if "--lambda" in sys.argv:
        lam = float(sys.argv[sys.argv.index("--lambda") + 1])
    n = 3000
    if "-n" in sys.argv:
        n = int(sys.argv[sys.argv.index("-n") + 1])
    return run(n, lam)


if __name__ == "__main__":
    sys.exit(main())
