# -*- coding: utf-8 -*-
"""
무료 구간이 **무엇으로 채워져 있나** — 줄마다 갈라 세는 자.

    python tools/verdict_mix.py             200명
    python tools/verdict_mix.py --show 1    첫 화면을 줄마다 펴 본다

★ 왜 이 자를 만드나 (2026-09-25 · 세 번째)

  손님이 말했습니다 — 「너무 내용만 길고 뭔소리인지 하나도 모르겠어. 이
  사람에 대해 완벽하게 파악해서 날카롭게 질문하고, 이런 사람이다, 이런 것
  때문에 꼬였을 거다, 이런 식으로 진짜 헉 소리 나게 만들어야 하는데.」

  앞선 두 자는 **겹침**을 셌습니다 (`dull_audit` 글자 · `same_point` 뜻).
  이 자는 다른 것을 셉니다 — 한 줄 한 줄이 **무슨 일을 하는가.**

  손님이 가장 먼저 보는 화면(훅 0단 · 446자 · 15줄)을 갈라 보니 —

      단정(그대는 ○이오)   0줄      ← 없습니다
      셈 나열               4줄
      물음                  2줄
      사전(뜻풀이)          5줄  33%
      몸사림(판단 못 함)     1줄
      시킴                  2줄

  손님은 **자기가 어떤 사람인지 한 마디도 못 들은 채** 십신 개수를 세라는
  말을 듣습니다. 그리고 그 셈은 「편관도 편재도 없소 · 4개가 비었소 ·
  0이오」 — 첫 화면이 **결핍 나열**입니다.

  「헉」 은 단정에서 나옵니다. 셈은 그 단정을 **뒤에서 받치는** 것이지
  앞에 세울 것이 아닙니다.

★ 여섯으로 갈라 셉니다

  단정    이 사람이 어떤 사람인지 **말하는** 줄
  인과    「그래서 이렇게 꼬였다」 — 원인과 결과를 잇는 줄
  셈      센 값을 대는 줄
  물음    되묻는 줄
  사전    낱말 뜻을 푸는 줄
  몸사림  못 한다 · 아니다 · 단정할 수 없다
  시킴    오늘 할 일

  **첫 화면**을 따로 봅니다 — 거기서 손님이 살지 나갈지 정합니다.
"""
from __future__ import annotations

import argparse
import collections
import html as _html
import random
import re
import statistics
import sys
from datetime import date
from pathlib import Path
from typing import get_args

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "services" / "api", ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine.bank import build_hook                  # noqa: E402
from engine.calendar import build_chart             # noqa: E402
from engine.features import build_features          # noqa: E402
from engine.report import build_report              # noqa: E402
from schemas.api import Concern                     # noqa: E402

TAG = re.compile(r"<[^>]+>")
SENT = re.compile(r"[^.?!]+[.?!]")
AS_OF = date(2026, 9, 25)
CONCERNS = get_args(Concern)

# ── 줄의 일감을 가리는 자 ─────────────────────────────────────
#
# ★ 차례가 중요합니다. 앞의 것이 이깁니다 — 한 줄이 여러 일을 하면 **가장
#   센 일**로 셉니다. 물음표가 붙은 단정은 단정이 아니라 물음입니다.

#: 몸사림 — 판단을 **거두는** 줄. 이 집의 규칙이 만든 줄이라 필요하되,
#: 한 장에 쌓이면 「아무것도 안 말해 주는 집」이 됩니다.
FLINCH = re.compile(
    r"판단할 수 (는 )?없|정할 수 없|세어서 나오지 않|안 말해 주|"
    r"맡은 일이 아니|말하지 않(소|네)|알 수 없|가를 일이 아니|"
    r"짐작하지 않았|보증하지 않|아닌 대목이 있거든|억지로 끼워|"
    r"맞는 말로 취급하지|단정하는 것은 아니|증거가 아니")

#: 물음 — 손님에게 되묻는 줄.
ASK = re.compile(r"[?？]\s*$")

#: 사전 — 낱말 뜻을 푸는 줄.
DICT_ = re.compile(
    r"^(이게 무슨 말인가)|"
    r"^(비견|겁재|식신|상관|정재|편재|정관|편관|정인|편인|비겁|식상|재성|"
    r"관성|인성|일간|일지|월지|월주|년주|일주|시주|대운|세운|용신|공망|"
    r"신살|절기|절입|지장간|통근|진태양시|양인|도화|역마|화개|괴강|백호)"
    r"\s*[^,.]{0,4}(이오|요|네|이네|쪽이오|자리요|것이오)")

#: 시킴 — 오늘 할 일.
DO = re.compile(r"(시오|하십시오|하세요|보세요|하시게|하게|보게)[.!]?\s*$")

#: 인과 — 「그래서 이렇게 꼬였다」. 원인과 결과를 잇는 말.
#
# ★ 이 집은 **까닭을 뒤에 대는** 꼴을 많이 씁니다 — 「~느라 품이 더
#   들었네」 「~것이 아니라 ~것이네」. 「때문」 같은 이음말만 찾으면 절반을
#   놓칩니다 (처음에 그래서 인과가 3%로 나왔습니다).
WHY = re.compile(
    r"^(그래서|그러니|그런데)\s"
    r"|(때문|까닭|탓|덕에|바람에|하니|느라|므로|기에)"
    r"|(것이 아니라|게 아니라|아니라\s).{0,30}(것이|거요|거네|이오|이네)"
    r"|(동안|사이에|뒤에|나서).{0,30}(미뤄|늦|막히|굳|새|남이|이미)")

#: 단정 — **이 사람이 어떤 사람인지 말하는** 줄. 「헉」이 여기서 납니다.
#
# ★ 주어가 **없는** 단정을 놓치고 있었습니다. 이 집은 하오체 한 벌로 쓰고
#   주어를 자주 생략합니다 — 「오래 버틴 것을 쉽게 버리지는 않지만, 지금의
#   비용을 따져야 다음으로 가는 사람이네」 에는 「그대」 가 없습니다.
#   주어를 요구하면 자가 제 집 글을 못 읽습니다.
#: ★ 「~했을 것이오」 도 단정입니다 (2026-09-25).
#
#   첫 화면을 대비 단정으로 고친 뒤 자가 그것을 「그밖」으로 셌습니다 —
#   「마음은 크게 썼을 것이오」 「다툰 뒤 먼저 손 내미는 쪽일 것이오」.
#   이 집이 일부러 쓰는 꼴이오: 단정이면서 손님이 아니라고 할 수 있는 말.
#   그걸 못 세면 고친 것이 안 보입니다.
VERDICT = re.compile(
    r"(사람이|쪽이|편이)[오네요]|(사람이네|사람이오|쪽이네|쪽이오|편이네|편이오)"
    # ★ 받침이 붙은 꼴을 놓치고 있었습니다 — 「컸을」 「썼을」 「갈」.
    #   한국말은 어간에 받침이 붙어 한 글자가 되니, 앞 글자를 지정하면
    #   반드시 새오 (`terms.WORD_START` 에서 겪은 그 자리요).
    r"|것이(오|네|요)[.!]?$"
    r"|(그대|자네|너|당신|그쪽)[는은가이]?\s.{0,40}"
    r"(이오|요|네|이네|하오|하네|드오|드네|보오|보네)$")

#: 셈 — 센 값을 대는 줄.
COUNT = re.compile(r"\d|하나|둘|셋|넷|다섯|여섯|일곱|여덟|아홉|열|없소|없네|비었")


def plain(html: str) -> str:
    return re.sub(r"\s+", " ", _html.unescape(TAG.sub(" ", html or ""))).strip()


def sentences(text: str) -> list:
    got = [s.strip() for s in SENT.findall(text)]
    tail = SENT.sub("", text).strip()
    if tail:
        got.append(tail)
    return [s for s in got if len(s) > 5]


KINDS = ("단정", "인과", "셈", "물음", "사전", "몸사림", "시킴", "그밖")


def kind_of(s: str) -> str:
    """한 줄의 일감. **센 것부터** 봅니다 — 앞의 것이 이깁니다."""
    if ASK.search(s):
        return "물음"
    if FLINCH.search(s):
        return "몸사림"
    if DICT_.match(s):
        return "사전"
    if DO.search(s):
        return "시킴"
    if WHY.search(s):
        return "인과"
    if VERDICT.search(s):
        return "단정"
    if COUNT.search(s):
        return "셈"
    return "그밖"


def _page(rng: random.Random) -> dict:
    y, mo, d = rng.randint(1960, 2007), rng.randint(1, 12), rng.randint(1, 28)
    h, mi = rng.randint(0, 23), rng.randint(0, 59)
    concern = rng.choice(CONCERNS)
    axis4 = rng.choice((None, "INFP", "ESTJ", "INTP", "ENFJ", "ISTP"))
    f = build_features(build_chart(y, mo, d, h, mi, rng.choice("MF"),
                                   hour_known=rng.random() > 0.15), as_of=AS_OF)
    segs = build_hook(f, concern, axis4)
    rep = build_report(f, "m", "nopa", "free", concern, axis4)
    return {"first": plain(segs[0]["html"]),
            "all": [plain(s["html"]) for s in segs]
                   + [plain(c["html"]) for c in rep["cuts"]]}


def audit(page: dict) -> dict:
    def mix(texts):
        bag = collections.Counter()
        for t in texts:
            for s in sentences(t):
                bag[kind_of(s)] += 1
        return bag

    first = mix([page["first"]])
    whole = mix(page["all"])
    return {"first": first, "whole": whole,
            "first_chars": len(page["first"]),
            "chars": sum(len(t) for t in page["all"]),
            # 첫 단정이 몇 번째 줄에 오는가 — 늦으면 손님은 그 앞에서 나갑니다
            "first_verdict_at": next(
                (i for i, s in enumerate(sentences(page["first"]), 1)
                 if kind_of(s) == "단정"), 0),
            "lines_first": len(sentences(page["first"]))}


def _pct(bag: collections.Counter) -> str:
    tot = max(1, sum(bag.values()))
    return " · ".join("%s %2.0f%%" % (k, 100 * bag[k] / tot)
                      for k in KINDS if bag[k])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--show", type=int, default=0)
    ap.add_argument("--seed", type=int, default=20260925)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    rows = [audit(_page(rng)) for _ in range(a.n)]

    def avg(fn):
        return statistics.mean(fn(r) for r in rows)

    print("\n무료 구간이 무엇으로 채워져 있나 (%d명)" % a.n)
    print("=" * 74)

    for name, key, extra in (("첫 화면", "first", True),
                             ("무료 전체", "whole", False)):
        bag = collections.Counter()
        for r in rows:
            bag.update(r[key])
        tot = max(1, sum(bag.values()))
        chars = avg(lambda r: r["first_chars" if key == "first" else "chars"])
        print("\n  %s — %d자 · 줄 %.0f개" % (name, chars, tot / len(rows)))
        for k in KINDS:
            if not bag[k]:
                continue
            n = bag[k] / len(rows)
            bar = "█" * int(round(28 * bag[k] / tot))
            print("    %-6s %-28s %4.1f줄  %2.0f%%"
                  % (k, bar, n, 100 * bag[k] / tot))
        if extra:
            late = [r["first_verdict_at"] for r in rows]
            none = sum(1 for x in late if x == 0)
            print("    ★ 첫 화면에 **단정이 한 줄도 없는 사람** %.0f%% (%d/%d)"
                  % (100 * none / len(rows), none, len(rows)))
            got = [x for x in late if x]
            if got:
                print("      있는 사람은 %.1f번째 줄에서 처음 만납니다"
                      % statistics.mean(got))

    if a.show:
        for r in rows[:a.show]:
            print("\n" + "-" * 74)
        rng2 = random.Random(a.seed)
        p = _page(rng2)
        print("  첫 화면을 줄마다 (%d자)" % len(p["first"]))
        for i, s in enumerate(sentences(p["first"]), 1):
            print("    %2d [%-4s] %s" % (i, kind_of(s), s[:62]))
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
