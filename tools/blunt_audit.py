"""
말이 손에 잡히는가, 그리고 물러서지 않는가 — 전수조사.

    python tools/blunt_audit.py [표본수]

★ 손님이 한 말 둘

  "너무 추상적이라 이해가 안 된다. 비유를 해서 쉽게 풀이해라."
  "쎈 말도 거침없이 뱉어야 한다. 팩폭 때릴 수 있도록."

  둘은 같은 자리를 가리킵니다. 화면에 나온 글이 이랬습니다 —

      이건 성격이 아니라 구조요. 힘이 나가는 자리와 받는 자리가
      어긋나 있소.
      내놓는 데 힘이 쓰이니, 내놓고 나면 빈자리가 크오.
      일지가 戌이라 닫는 데서 움직이오.

  낱말 사전을 붙여도 이 문장은 안 쉬워집니다. **문장 자체**가
  「힘 · 자리 · 결 · 쪽 · 흐름」 으로만 되어 있기 때문입니다.
  그리고 아무것도 단정하지 않아 하나도 안 아픕니다.

★ 이 도구가 세는 것 셋

  ① 뜬 말   힘·기운·자리·결·쪽·흐름·구조 — 명리 안에서만 뜻이 있는 말
  ② 산 말   돈·일·사람·말·잠·약속·상사·집 — 손님 살림의 말
  ③ 물러섬  ~게요 · ~쯤 · 아마 · 조금 · ~수도 — 빠져나가는 말

  ①이 ②보다 많으면 무슨 말인지 모르고, ③이 많으면 안 아픕니다.

★ 세지 않는 것 — 넘으면 안 되는 선

  팩폭은 **센 말**이지 **단정**이 아닙니다. 병·수명·이혼·투자 시점은
  세게 말하는 것과 상관없이 금지입니다 (docs/11 · CLAUDE.md).
  아프게 만들려다 여기를 넘는 것이 가장 흔한 사고라 따로 셉니다.
"""
from __future__ import annotations

import random
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine.bank import build_hook                # noqa: E402
from engine.calendar import build_chart           # noqa: E402
from engine.features import build_features        # noqa: E402
from engine.lens import released                  # noqa: E402
from engine.report import build_report            # noqa: E402

TAG = re.compile(r"<[^>]+>")
BOX = re.compile(r'<div class="gls">.*?</div>', re.S)

# ① 뜬 말 — 명리 안에서만 뜻이 있는 말
AIR = re.compile(r"기운|자리|흐름|구조|결이|결을|결은|쪽이|쪽으로|쪽에|"
                 r"힘이|힘을|힘은|빈자리|배치")

# ② 산 말 — 손님 살림의 말
LIFE = re.compile(
    r"돈|월급|삯|빚|일|직장|상사|동료|사람|친구|가족|부모|자식|말|잠|밥|"
    r"약속|집|방|계약|시험|면접|이사|연락|카톡|주말|퇴근|출근|통장|"
    r"저축|장사|손님|아침|저녁|밤|새벽")

# ③ 물러서는 말
HEDGE = re.compile(r"게요|쯤|아마|조금|약간|다소|수도 있|편이|듯|"
                   r"경향|하기도|그럴 수|정도")

# 넘으면 안 되는 선
BANNED = re.compile(r"다치|병들|앓|죽|이혼|헤어지|사고 나|망하|대박|"
                    r"사라|팔라|낫는다|고친다")


def paras(html: str):
    """
    **문단** 단위. 손님은 문장을 따로 읽지 않습니다.

    ★ 문장으로만 재면 고친 것이 안 보입니다.

      뜬 문장 뒤에 산 문장을 붙였더니 문장 수는 그대로였습니다 —
      뜬 문장은 여전히 뜬 문장이니까요. 그런데 손님은 그 둘을 이어
      읽고 뜻을 압니다. 그러니 두 눈금을 다 냅니다: 문장 단위는
      **아직 남은 안개**를 보여 주고, 문단 단위는 **손님이 실제로
      막히는 자리**를 보여 줍니다.
    """
    body = BOX.sub(" ", html)
    out = []
    for m in re.finditer(r"<p[^>]*>(.*?)</p>", body, re.S):
        t = re.sub(r"\s+", " ", TAG.sub(" ", m.group(1))).strip()
        if len(t) > 8:
            out.append(t)
    return out


def sentences(html: str):
    """비유 상자를 뺀 **본문**만. 상자는 사전이지 글이 아니오."""
    body = BOX.sub(" ", html)
    txt = re.sub(r"\s+", " ", TAG.sub(" ", body)).strip()
    return [s.strip() for s in re.split(r"(?<=[.?!])\s+", txt)
            if len(s.strip()) > 8]


def main() -> int:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    rng = random.Random(20260902)
    lenses = [l["id"] for l in released()]

    lines = []
    plines = []
    for _ in range(n):
        f = build_features(build_chart(
            rng.randint(1960, 2006), rng.randint(1, 12), rng.randint(1, 28),
            rng.randint(0, 23), 0, rng.choice("FM"), True, "서울"))
        concern = rng.choice(["money", "work", "love", "people", "dir",
                              "health"])
        for s in build_hook(f, concern):
            lines += sentences(s["html"])
            plines += paras(s["html"])
        try:
            r = build_report(f, "cid", rng.choice(lenses), "all", concern,
                             None)
        except Exception:                          # noqa: BLE001
            continue
        for c in r["cuts"]:
            lines += sentences(c["html"])
            plines += paras(c["html"])

    tot = len(lines) or 1
    ptot = len(plines) or 1
    pbad = sum(1 for t in plines if AIR.search(t) and not LIFE.search(t))
    air = sum(1 for s in lines if AIR.search(s))
    life = sum(1 for s in lines if LIFE.search(s))
    both = sum(1 for s in lines if AIR.search(s) and not LIFE.search(s))
    hedge = sum(1 for s in lines if HEDGE.search(s))
    bad = [s for s in lines if BANNED.search(s)]

    print("=" * 76)
    print("  말이 손에 잡히는가 — 문장 %d줄" % tot)
    print("=" * 76)
    print()
    print("  ① 뜬 말이 든 줄        %4d  %3.0f%%" % (air, 100.0 * air / tot))
    print("  ② 산 말이 든 줄        %4d  %3.0f%%" % (life, 100.0 * life / tot))
    print("  ★ 뜬 말만 있는 줄      %4d  %3.0f%%   ← 무슨 말인지 모르는 줄"
          % (both, 100.0 * both / tot))
    print("  ③ 물러서는 줄          %4d  %3.0f%%   ← 안 아픈 줄"
          % (hedge, 100.0 * hedge / tot))
    print()
    print("  ★★ 문단 단위 — 손님이 실제로 막히는 자리")
    print("     뜬 말만 있는 문단     %4d / %4d  %3.0f%%"
          % (pbad, ptot, 100.0 * pbad / ptot))
    if bad:
        print("\n  ★ 선을 넘은 줄 %d — 세게 말하는 것과 다릅니다" % len(bad))
        for s in bad[:5]:
            print("     %s" % s[:64])

    print("\n  뜬 말만 있는 줄 — 자주 나오는 것부터")
    for s, c in Counter(s for s in lines
                        if AIR.search(s) and not LIFE.search(s)).most_common(10):
        print("     %2d회  %s" % (c, s[:60]))

    print("\n  물러서는 줄 — 자주 나오는 것부터")
    for s, c in Counter(s for s in lines if HEDGE.search(s)).most_common(6):
        print("     %2d회  %s" % (c, s[:60]))

    print("\n" + "-" * 76)
    print("  ※ 팩폭은 **센 말**이지 **단정**이 아닙니다. 병·수명·이혼·")
    print("    투자 시점은 세게 말하는 것과 상관없이 금지입니다.")
    print("    아프게 하려면 단정할 게 아니라 **구체적**이어야 합니다 —")
    print("    「빈자리가 크오」 는 안 아프고 「그래서 아직 혼자 하오」 는")
    print("    아픕니다. 아픈 것은 세기가 아니라 **정확도**입니다.")
    print("-" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
