"""릴레이 규칙이 인구의 몇 %에 걸리는지 재서 규칙 파일에 적는다.

    python tools/relay_reach.py            # 재기만
    python tools/relay_reach.py --write    # relay_rules.json 에 써넣음

★ 왜 이 값을 저장하는가
  추천이 한 캐릭터로 쏠리는 걸 막으려면 **이미 많이 나가는 캐릭터를
  깎아야** 합니다(추천시스템의 popularity bias 재순위). 깎으려면 그
  캐릭터가 얼마나 나가는지 알아야 합니다.

  실시간 노출 카운터를 두는 방법도 있지만, 워커가 여럿이면 경쟁이
  생기고 결과가 요청 순서에 따라 흔들립니다. 규칙은 결정적이므로
  도달률도 결정적입니다 — 미리 재서 박아두는 편이 낫습니다.

★ 값이 낡으면 어떻게 아는가
  tests/test_bank.py 가 저장값이 있는지 봅니다. 규칙을 고치면
  도달률이 달라지므로 이 도구를 다시 돌리세요.

★ 시각 미상 비율은 무엇을 썼는지 파일에 남깁니다
  가정값으로 잰 도달률과 실측으로 잰 도달률은 다른 숫자입니다.
  나중에 이 파일만 보고도 구별할 수 있어야 합니다.
"""
from __future__ import annotations

import io
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import relay as RL                   # noqa: E402
from tools import population as POP              # noqa: E402

RULES = ROOT / "seed" / "relay_rules.json"
N = 6000


def measure(n: int = N) -> dict:
    hit = Counter()
    for f in POP.sample(n):
        for it in RL.evaluate(f):
            hit[it["rule_id"]] += 1
    return {k: round(v / n, 3) for k, v in hit.items()}


def main() -> int:
    print(POP.banner(N))
    share, src = POP.hour_unknown_share()
    reach = measure()
    d = json.loads(RULES.read_text(encoding="utf-8"))
    print("%-13s %-11s %4s %8s %8s" % ("rule", "lens", "prio", "도달률", "저장값"))
    changed = 0
    for r in sorted(d["rules"], key=lambda x: -x["priority"]):
        got = reach.get(r["id"], 0.0)
        old = r.get("reach")
        flag = "" if old == got else "  ←"
        if old != got:
            changed += 1
        print("%-13s %-11s %4d %7.1f%% %8s%s"
              % (r["id"], r["lens_id"], r["priority"], 100 * got,
                 "-" if old is None else "%.1f%%" % (100 * old), flag))
        r["reach"] = got
    dead = [r["id"] for r in d["rules"] if r["reach"] == 0.0]
    if dead:
        print("\n★ 아무에게도 안 걸리는 규칙 %d개: %s" % (len(dead), ", ".join(dead)))
    if "--write" in sys.argv:
        d["reach_measured_with"] = {
            "sample": N, "hour_unknown_share": round(share, 4), "source": src}
        io.open(RULES, "w", encoding="utf-8", newline="\n").write(
            json.dumps(d, ensure_ascii=False, indent=1) + "\n")
        print("\n기록했습니다 (%d개 갱신) · 시각 미상 %s" % (changed, src))
    else:
        print("\n(--write 를 붙이면 규칙 파일에 씁니다)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
