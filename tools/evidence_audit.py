"""
근거가 근거 노릇을 하는가 — 전수조사.

    python tools/evidence_audit.py [표본수]

★ 「과학적으로 입증」 은 못 씁니다

  사주는 과학적으로 검증된 적이 없습니다. 그렇게 쓰면 거짓말이고
  이 집이 금지한 것입니다(docs/11 · CLAUDE.md). 적중률·통계라는
  말도 마찬가지입니다.

  그런데 **근거를 단단하게 만드는 길은 따로 있습니다.** 회의적인
  독자를 설득하는 것은 「과학이오」 라는 말이 아니라, 따라갈 수 있는
  **논증**입니다.

★ 근거 한 줄에 있어야 하는 것 넷

    ① 관측   여덟 글자에서 **무엇을 읽었는가**
             — 손님이 제 표를 보고 확인할 수 있어야 합니다
    ② 이치   그 관측을 **어떤 규칙**으로 읽었는가
             — 규칙 없이 관측만 대면 그건 우연입니다
    ③ 결론   그래서 **무엇이라 말하는가**
             — 앞의 둘과 이어져야 합니다
    ④ 출처   그 규칙이 **어느 갈래에서 왔는가**
             — 지어낸 인용은 안 됩니다. 갈래 이름까지만 댑니다

  지금은 ①만 있습니다 —

      돈 → 재성이 하나 · 가장 센 자리 식상
      통근 없음 · 정관

  읽은 것을 나열했을 뿐이라, 손님은 **그래서 뭐** 라고 묻습니다.

★ 이 도구가 세는 것

  실제로 만들어지는 근거 줄을 뽑아 위 넷이 있는지 봅니다.
"""
from __future__ import annotations

import random
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine.bank import build_hook              # noqa: E402
from engine.calendar import build_chart         # noqa: E402
from engine.features import build_features      # noqa: E402
from engine.report import build_report          # noqa: E402

CONCERNS = ["money", "work", "love", "people", "dir", "health"]

# ① 관측 — 표에서 확인할 수 있는 것
OBS = re.compile(
    r"일간|일지|월지|월주|년주|시주|통근|글자|재성|관성|인성|식상|비겁|"
    r"[甲乙丙丁戊己庚辛壬癸]|[子丑寅卯辰巳午未申酉戌亥]|나무|불|흙|쇠|물")

# ② 이치 — **짜임**으로 봅니다.
#
#   처음에는 한국어 어미로 찾았습니다(이라·므로·보오…). 그랬더니
#   「대운이 몇 번째 칸인지로 나이대를 **가르오**」 처럼 이치가 분명히
#   있는 줄을 못 알아봤습니다. 어미 목록은 아무리 늘려도 샙니다.
#
#   engine/why.py 가 붙이는 짜임은 정해져 있습니다 —
#   관측 다음에 줄표(—)가 오고 규칙이 옵니다. 그걸로 봅니다.
RULE = re.compile(r"—\s*\S")

# ③ 결론 — 그래서 무엇인가
CONC = re.compile(r"그래서|그러니|따라서|→|—|라 (?:읽|보|하)")

# ④ 출처 — 어느 갈래인가
SRC = re.compile(r"자평|명리|십신|격국|용신|신살|오행|고서|유파|〔|\[")


def sample(n: int):
    rng = random.Random(20260902)
    out = Counter()
    for _ in range(n):
        c = build_chart(rng.randint(1960, 2006), rng.randint(1, 12),
                        rng.randint(1, 28), rng.randint(0, 23), 0,
                        rng.choice("FM"), True)
        f = build_features(c)
        concern = rng.choice(CONCERNS)
        for s in build_hook(f, concern):
            if s.get("source"):
                out[s["source"]] += 1
        try:
            r = build_report(f, "cid", "pungun", "all", concern, None)
        except Exception:                        # noqa: BLE001
            continue
        for cut in r.get("cuts", []):
            if cut.get("source"):
                out[cut["source"]] += 1
    return out


def main() -> int:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    lines = sample(n)

    print("=" * 76)
    print("  근거가 근거 노릇을 하는가 — %d가지" % len(lines))
    print("=" * 76)
    print()

    have = Counter()
    weak = []
    for txt, cnt in lines.items():
        got = []
        if OBS.search(txt):
            got.append("관측")
        if RULE.search(txt):
            got.append("이치")
        if CONC.search(txt):
            got.append("결론")
        if SRC.search(txt):
            got.append("출처")
        for g in got:
            have[g] += 1
        if len(got) <= 1:
            weak.append((cnt, txt, got))

    tot = len(lines) or 1
    print("  %-6s %6s   %s" % ("있는 것", "가짓수", "몫"))
    print("  " + "-" * 46)
    for k in ("관측", "이치", "결론", "출처"):
        print("  %-6s %6d   %5.1f%%" % (k, have[k], 100.0 * have[k] / tot))

    print()
    if weak:
        weak.sort(reverse=True)
        print("  ★ 관측만 있고 이치가 없는 줄 — %d가지 (%.0f%%)"
              % (len(weak), 100.0 * len(weak) / tot))
        print("     읽은 것을 나열했을 뿐이라 손님은 「그래서 뭐」 라고 묻습니다.")
        for cnt, txt, _ in weak[:10]:
            print("     %s" % txt[:62])

    print()
    print("-" * 76)
    print("  ※ 「과학적으로 입증」 은 쓸 수 없습니다. 회의적인 독자를")
    print("    설득하는 것은 그 말이 아니라 **따라갈 수 있는 논증**입니다 —")
    print("    무엇을 보고(관측), 어떤 이치로(규칙), 그래서 이렇게(결론),")
    print("    그 이치는 어디서 왔는가(출처).")
    print("-" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
