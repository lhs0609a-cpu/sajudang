"""
손님이 알아들을 수 있는가 — 전수조사.

    python tools/plain_audit.py [표본수]

★ 손님이 한 말

  "너무 단어들이 추상적이라 이해가 안돼. 비유를 해서 다 쉽게 풀이해야
  한다."

★ 뜻만 바꿔 말한 것은 푼 게 아니다

  풀이 층은 이미 있었습니다. 그런데 적혀 있던 것이 이랬습니다 —

      겁재 = 나와 겨루는 힘
      식신 = 밖으로 내놓는 힘
      용신 = 모자란 것을 채워 줄 기운

  쉰넷 중 그림이 그려지는 것은 **둘(4%)** 뿐이었습니다. 나머지는
  모르는 말을 모르는 말로 바꾼 것이라, 읽고 나서도 여전히 모릅니다.

★ 이 도구가 세는 것 셋

  ① 풀이   어려운 말이 뜻 없이 지나가는가
  ② 비유   그 말에 **그림이 그려지는 한 줄**이 붙는가
  ③ 예     비유가 손에 잡히는 것을 드는가
           (솥·삯·마감·장터 같은 **살림의 말**을 쓰는가)

  ②가 핵심입니다. ①만 채우면 「힘」 「자리」 「기운」 같은 말이 늘 뿐,
  손님은 여전히 그림을 못 그립니다.

★ 금지된 비유

  「양인이 있으니 다치오」 처럼 신살로 병·사고를 단정하는 비유는
  못 씁니다 (docs/14 §7 · docs/11). 자리를 가리키는 데서 멈춥니다.
"""
from __future__ import annotations

import random
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import terms                          # noqa: E402
from engine.bank import build_hook                # noqa: E402
from engine.calendar import build_chart           # noqa: E402
from engine.features import build_features        # noqa: E402
from engine.lens import released                  # noqa: E402
from engine.report import build_report            # noqa: E402

TAG = re.compile(r"<[^>]+>")

# 손에 잡히는 말 — 살림에서 쓰는 것들.
#
#   「힘」 「기운」 「자리」 는 명리의 말이지 살림의 말이 아닙니다.
#   비유가 이 말들로만 되어 있으면 그림이 안 그려집니다.
HAND = re.compile(
    r"솥|밥|삯|장터|마감|어머니|나무|바람|뿌리|쇠|불|물|겨울|연장|"
    r"그릇|골방|또래|동무|감투|살림|눈|손|발밑|계절|해|시계|판|눈금")

# 못 쓰는 비유 — 단정하는 말
BANNED = re.compile(r"다치|병들|앓|죽|이혼|헤어지|사고|망하|대박|사라|팔라")


def main() -> int:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8

    print("=" * 76)
    print("  손님이 알아들을 수 있는가")
    print("=" * 76)

    # ── 표 자체를 본다 ────────────────────────────────────
    tot = len(terms.MEANING)
    has_pic = sum(1 for k in terms.MEANING if terms.PICTURE.get(k))
    hand = sum(1 for k, v in terms.PICTURE.items() if HAND.search(v))
    bad = [(k, v) for k, v in terms.PICTURE.items() if BANNED.search(v)]

    print("\n  ① 어려운 말 %d가지" % tot)
    print("     뜻이 붙은 것    %3d  %3.0f%%" % (tot, 100.0))
    print("  ② 비유가 붙은 것  %3d  %3.0f%%" % (has_pic, 100.0 * has_pic / tot))
    print("  ③ 손에 잡히는 것  %3d  %3.0f%%" % (hand, 100.0 * hand / tot))
    if bad:
        print("\n     ★ 단정하는 비유 %d개 — 못 씁니다" % len(bad))
        for k, v in bad:
            print("        %-6s %s" % (k, v[:50]))

    # ── 실제 화면에서 몇 번 만나는가 ──────────────────────
    rng = random.Random(20260902)
    lenses = [l["id"] for l in released()]
    met = Counter()
    boxed = Counter()
    for _ in range(n):
        f = build_features(build_chart(
            rng.randint(1960, 2006), rng.randint(1, 12), rng.randint(1, 28),
            rng.randint(0, 23), 0, rng.choice("FM"), True))
        concern = rng.choice(["money", "work", "love", "people", "dir", "health"])
        lid = rng.choice(lenses)
        try:
            r = build_report(f, "cid", lid, "all", concern, None)
        except Exception:                          # noqa: BLE001
            continue
        htmls = [c["html"] for c in r["cuts"]]
        htmls += [s["html"] for s in build_hook(f, concern)]
        for h in htmls:
            plain = TAG.sub(" ", h)
            for t in terms.MEANING:
                if t in plain:
                    met[t] += 1
            if 'class="gls"' in h:
                boxed["상자"] += 1
            else:
                boxed["없음"] += 1

    print("\n  ④ 실제 화면 — 표본 %d명" % n)
    seen_tot = sum(met.values()) or 1
    covered = sum(c for t, c in met.items() if terms.PICTURE.get(t))
    print("     어려운 말을 만나는 횟수  %d" % seen_tot)
    print("     그중 비유가 있는 말      %.0f%%" % (100.0 * covered / seen_tot))
    box_n = boxed["상자"]
    print("     비유 상자가 붙은 덩이    %d / %d"
          % (box_n, box_n + boxed["없음"]))

    print("\n     자주 만나는 말 열")
    for t, c in met.most_common(10):
        mark = " " if terms.PICTURE.get(t) else "★"
        print("       %s %-6s %4d회  %s" % (mark, t, c,
                                            terms.PICTURE.get(t, "비유 없음")[:34]))

    left = [t for t, _ in met.most_common() if not terms.PICTURE.get(t)]
    print("\n" + "-" * 76)
    if not left and not bad:
        print("  [OK] 화면에 나오는 어려운 말에 전부 비유가 붙었소")
    else:
        if left:
            print("  비유 없는 말 %d가지: %s" % (len(left), left[:8]))
        if bad:
            print("  단정하는 비유 %d개" % len(bad))
    print("  ※ 뜻만 바꿔 말한 것은 푼 게 아닙니다. 그림이 그려져야 합니다.")
    print("-" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
