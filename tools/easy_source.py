# -*- coding: utf-8 -*-
"""흐릿한 문장이 **어느 틀에서** 나왔나 — 많이 나오는 순서로.

    python tools/easy_source.py [인원수]

★ 낱개로 고치면 4,285줄입니다

  `tools/easy_all.py` 로 재니 29,208문장 중 4,285가 흐릿했습니다.
  그런데 그 문장들은 사람마다 새로 지어진 게 아니라 **뱅크의 틀
  몇 개**에서 나옵니다. `engine/real` 이 634줄을 축 열넷으로 덮은
  것과 같은 자리요 — 틀을 고치면 수천 줄이 한꺼번에 고쳐집니다.

  그래서 이 자는 **틀별로** 셉니다.

★ 지문과 코드 조각은 안 셉니다

  「큰 방에 스무 자리가 놓여 있다」 는 지문이오 — 장면을 그리는
  말이지 풀이가 아닙니다. 한다체(「…있다」)로 끝나면 뺍니다.
  화면 글에서 새 나온 코드 조각(`▮` · `&&`)도 뺍니다.
"""
from __future__ import annotations

import argparse
import collections
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT / "tools"))

import easy_audit as EA                                # noqa: E402
from engine import bank as bank_mod                    # noqa: E402
from engine import lens as lens_mod                    # noqa: E402
from engine import screenscan as SS                    # noqa: E402
from engine.calendar import build_chart                # noqa: E402
from engine.features import build_features             # noqa: E402
from engine.report import build_report                 # noqa: E402

TODAY = date(2026, 9, 17)
CONCERNS = ("money", "work", "love", "people", "dir", "health")
BIRTHS = [(1993, 11, 25, 15, 55, "M", True),
          (1978, 2, 4, 0, 20, "F", True)]

# 지문 — 장면을 그리는 말. 풀이가 아니오.
NARRATION = re.compile(r"(있다|었다|았다|한다|onda|보았다|섰다|놓였다)[.!?]?$")
# 화면에서 새 나온 코드 조각
CODEY = re.compile(r"▮|&&|\{|\}|=>|className")
# 자리표시가 든 자리는 사람마다 값이 갈리니, 그 값을 지우고 묶습니다.
NUM = re.compile(r"\d+")


def key_of(s: str) -> str:
    """사람마다 갈리는 값(수·한자·괄호 풀이)을 지운 **틀**."""
    t = EA.GLOSS.sub("", s)
    t = NUM.sub("N", t)
    t = re.sub(r"[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]", "干", t)
    return re.sub(r"\s+", " ", t).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("n", nargs="?", type=int, default=2)
    a = ap.parse_args()
    lenses = [l["id"] for l in lens_mod.released()]
    cnt = collections.Counter()
    src = {}
    tot = 0

    def look(html, where):
        nonlocal tot
        for s in EA.sentences(html):
            if NARRATION.search(s) or CODEY.search(s):
                continue
            tot += 1
            n, fig = EA.vague_of(s)
            if n >= 2 or fig:
                k = key_of(s)
                cnt[k] += 1
                src.setdefault(k, where)

    for b in BIRTHS[:a.n]:
        y, m, d, h, mi, sex, known = b
        f = build_features(build_chart(y, m, d, h, mi, sex, known, "서울"),
                           as_of=TODAY)
        for concern in CONCERNS:
            look(SS.hook_html(bank_mod.build_hook(f, concern, "INTJ", "", "그대")),
                 "훅")
            for lid in lenses:
                for c in build_report(f, "e", lid, "free", concern, "INTJ")["cuts"]:
                    look(c["html"], c["id"])
    for sid, txt in ((k, v[0]) for k, v in SS._screens().items()):
        if sid in SS.KO:
            look(txt, "화면 " + sid)

    bad = sum(cnt.values())
    print("=" * 76)
    print("  흐릿한 틀 — 많이 나오는 순 (지문·코드 뺀 %d문장 중 %d · %.0f%%)"
          % (tot, bad, 100.0 * bad / max(1, tot)))
    print("=" * 76)
    top = cnt.most_common(60)
    cover = sum(v for _, v in top)
    for k, v in top:
        print("  %5d회 [%-14s] %s" % (v, src.get(k, "?")[:14], k[:58]))
    print()
    print("  위 %d틀이 흐릿한 문장의 %.0f%% 를 덮소 — 낱개로 고칠 것이 아니오."
          % (len(top), 100.0 * cover / max(1, bad)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
