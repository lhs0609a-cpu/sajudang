# -*- coding: utf-8 -*-
"""
사전이 유사문서인가 — 열기 **전에** 재는 자 (docs/44 §2).

    python tools/dict_same.py            일주 60장 · 용어집 항목 56
    python tools/dict_same.py --show 3   가장 닮은 짝을 펴 본다
    python tools/dict_same.py --slope    겹친 사실 수별로 펴 본다

★ 왜 열기 전에 재나

  대량 콘텐츠가 유사문서로 잡히는 까닭은 늘 같습니다 — 틀이 하나고 값만
  바뀝니다. 그건 다 올린 뒤에는 되돌리기 어렵습니다(색인이 이미 집 전체를
  낮게 봅니다). 그래서 **한 클래스를 열기 전에** 이 자를 댑니다.

  첫 판이 바로 그 꼴이었고 여기서 걸렸습니다 — 짝 겹침 평균 76.5% · 최악
  91.7% · 이 장에만 있는 수 1.1개. 문장 다섯 줄이 예순 장에 한 벌이었소.

★ 무엇을 재는가 — 여섯

  ① 짝 겹침 평균      네 글자 창으로 잰다 (문턱 35%)
  ② **남 짝의 최악**  파생 사실이 하나도 안 겹치는 짝 (문턱 45%)
  ③ 기울기           겹친 사실이 늘면 겹침도 늘어야 한다
  ④ 이 장에만 있는 수 (문턱 4)
  ⑤ 최다 점유         한 문장이 그 클래스에서 먹는 몫 (문턱 2%)
  ⑥ 값 묶음           센 값이 통째로 같은 두 장이 있으면 안 된다

★ ②③ 은 ① 만으로는 못 잡는 것을 잡습니다. 그리고 ① 만으로 **잡을 수 없는
  것을 잡았다고 하지도** 않습니다.

  처음에는 「어느 짝이든 35% 아래」로 두었습니다. 여섯 판을 고쳐 평균을
  76.5% → 29.0% 로 내렸는데 최악은 55.6% 에서 더 안 내려갔습니다. 열어
  보니 그 짝들은 **일주가 정하는 여섯 사실 가운데 셋넷이 진짜로 같은**
  짝이었습니다 — 戊辰 과 戊戌 은 일간도 십신도 앉은 결도 뿌리도 같고,
  다른 것은 공망·지장간·충·인구뿐이오.

  그런 짝을 더 갈라 놓으려면 없는 사실을 지어내거나 빈말로 늘려야 합니다.
  둘 다 이 집이 금한 것입니다. 그래서 자를 이렇게 고쳤습니다 —

      틀이 하나인가       → 사실이 안 겹치는 짝이 닮는가 (②)
      글이 셈을 따르는가  → 사실이 겹칠수록 닮아지는가 (③)

  ②③ 은 첫 판을 그대로 잡습니다 — 같은 자로 재 보니 첫 판은 사실이 하나도
  안 겹치는 짝조차 **85.1%**(평균 77.6%)였고, 기울기는 77.6 → 84.5 로
  밑값에 대면 납작했습니다. 지금은 39.7%(평균 24.9%) · 24.9 → 46.1 이오.
  자를 느슨하게 한 것이 아니라 **재는 자리를 옮긴 것**입니다.

★ 용어는 장이 아니라 **한 장의 항목**입니다.

  쉰여섯 낱말을 각자 한 장으로 열면 한 장이 평균 69자요. 그건 유사문서가
  아니라 **얄팍한 장** 문제고, 쉰여섯 개의 빈 장은 집 전체를 낮춥니다.
  그래서 용어집 한 장에 모읍니다 (docs/44 §11). 여기서는 항목끼리 겹치지
  않는지와 항목이 몇 자인지를 찍어, 그 판단의 근거를 남깁니다.
"""
from __future__ import annotations

import argparse
import collections
import html as _html
import itertools
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "services" / "api", ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine import dict as D                    # noqa: E402

TAG = re.compile(r"<[^>]+>")
SENT = re.compile(r"[^.?!]+[.?!]")

PAIR_MEAN_MAX = 0.35     # ① 짝 겹침 평균
# ② 사실이 안 겹치는 짝의 최악.
#
#   ★ 이 수는 **재서** 정했습니다 (2026-09-24). 틀 하나로 지은 첫 판과
#     지금 글을 같은 자로 재니 이 칸이 이렇게 갈립니다 —
#
#         틀 하나(첫 판)   남 짝 최악 85.1% · 평균 77.6%
#         지금             남 짝 최악 39.7% · 평균 24.9%
#
#     둘 사이가 마흔 눈금 넘게 벌어지니 문턱은 그 사이에 둡니다. 45%면
#     글을 한 줄 고칠 여유가 있고, 틀 하나는 마흔 눈금 밖에서 걸립니다.
#     `tests/test_dict_unique.py::test_틀_하나면_자에_걸린다` 가 지킵니다.
STRANGER_MAX = 0.45
OWN_MIN = 4              # ④ 이 장에만 있는 수
TOP_SHARE_MAX = 0.02     # ⑤ 한 문장의 최다 점유
THIN_MIN = 300           # 장으로 열 만한 길이 — 이보다 얄팍하면 한 장에 모은다

#: 일주 한 자리를 정하는 파생 사실. ③ 의 가로축이오.
AXES = ("gan", "ji", "seat", "ji_tengod", "root", "gongmang", "samhap",
        "tg_group")


def plain(html: str) -> str:
    return re.sub(r"\s+", " ", _html.unescape(TAG.sub(" ", html or ""))).strip()


def sentences(html: str) -> list:
    t = plain(html)
    got = [s.strip() for s in SENT.findall(t)]
    tail = SENT.sub("", t).strip()
    if tail:
        got.append(tail)
    return [s for s in got if len(s) > 8]


def overlap(a: str, b: str) -> float:
    """
    두 장이 **글자로** 얼마나 겹치는가.

    ★ 문장 단위로 세면 한 글자만 달라도 「갈렸다」가 됩니다 — 이 집이
      훅에서 겪은 그 자리요 (CLAUDE.md 「갈래로 재고 갈렸다고 하기」).
      그래서 네 글자 창으로 잘라 겹치는 몫을 셉니다.
    """
    def grams(s: str) -> collections.Counter:
        s = re.sub(r"\s+", "", s)
        return collections.Counter(s[i:i + 4] for i in range(max(0, len(s) - 3)))

    ga, gb = grams(a), grams(b)
    if not ga or not gb:
        return 0.0
    return sum((ga & gb).values()) / max(sum(ga.values()), sum(gb.values()))


def _shared_facts(a: dict, b: dict) -> int:
    return sum(1 for k in AXES if a.get(k) == b.get(k))


def _own_min(pages: list) -> tuple:
    seen: collections.Counter = collections.Counter()
    for p in pages:
        for v in set(p.get("own") or []):
            seen[v] += 1
    counts = [sum(1 for v in set(p.get("own") or []) if seen[v] == 1)
              for p in pages]
    return (min(counts) if counts else 0,
            sum(counts) / max(1, len(counts)))


def _top_share(texts: list) -> tuple:
    bag: collections.Counter = collections.Counter()
    total = 0
    for t in texts:
        for s in sentences(t):
            bag[s] += 1
            total += 1
    if not bag:
        return "", 0.0
    top, n = bag.most_common(1)[0]
    return top, n / max(1, total)


def _value_sets(pages: list) -> int:
    """센 값이 통째로 같은 두 장이 있는가 — 있으면 그 둘은 같은 장이오."""
    sets = [tuple(sorted(p.get("own") or [])) for p in pages]
    return len(sets) - len(set(sets))


def measure_pages(pages: list) -> dict:
    texts = [plain(p["html"]) for p in pages]
    n = len(pages)
    facts = [p.get("facts") or {} for p in pages]
    rows = []
    for i, j in itertools.combinations(range(n), 2):
        rows.append((overlap(texts[i], texts[j]), _shared_facts(facts[i], facts[j]),
                     i, j))
    by = collections.defaultdict(list)
    for s, k, _, _ in rows:
        by[k].append(s)
    om, oa = _own_min(pages)
    top, share = _top_share(texts)
    stranger = by.get(0) or [0.0]
    return {"n": n, "rows": rows, "by": dict(by), "texts": texts,
            "pages": pages,
            "mean": statistics.mean([s for s, _, _, _ in rows]) if rows else 0.0,
            "worst": max(rows)[0] if rows else 0.0,
            "over": (sum(1 for s, _, _, _ in rows if s > PAIR_MEAN_MAX)
                     / max(1, len(rows))),
            "stranger_n": len(by.get(0) or []),
            "stranger_worst": max(stranger),
            "stranger_mean": statistics.mean(stranger),
            "own_min": om, "own_mean": oa,
            "top": top, "top_share": share,
            "dup_values": _value_sets(pages),
            "chars": sum(len(t) for t in texts) / max(1, n)}


def _slope_ok(by: dict) -> bool:
    """
    겹친 사실이 늘면 겹침도 늘어야 한다 — 납작하면 글이 셈을 안 따르오.

    ★ 오름폭을 **밑값에 대서** 봅니다. 눈금으로만 보면(「5점 이상 오르면
      통과」) 틀 하나로 지은 첫 판이 통과합니다 — 77.6% 에서 84.5% 로
      6.9점 오르니까요. 밑이 이미 77.6% 인데 7점 오른 것은 오른 것이
      아니라 **전부가 같다**는 말이오. 그래서 밑값의 3할을 요구합니다.
    """
    ks = sorted(k for k in by if len(by[k]) >= 20)
    if len(ks) < 3:
        return True
    means = [statistics.mean(by[k]) for k in ks]
    rise = means[-1] - means[0]
    return rise >= max(0.05, 0.3 * means[0])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", type=int, default=0)
    ap.add_argument("--slope", action="store_true")
    a = ap.parse_args()

    print("\n사전이 유사문서인가 — 열기 전에 재는 자")
    print("=" * 72)

    bad = 0
    m = measure_pages([D.ilju_page(gz) for gz in D.sixty()])
    ok = {
        "mean": m["mean"] <= PAIR_MEAN_MAX,
        "stranger": m["stranger_worst"] <= STRANGER_MAX,
        "slope": _slope_ok(m["by"]),
        "own": m["own_min"] >= OWN_MIN,
        "top": m["top_share"] <= TOP_SHARE_MAX,
        "values": m["dup_values"] == 0,
    }
    bad += sum(1 for v in ok.values() if not v)
    mark = lambda k: "OK" if ok[k] else "✗"      # noqa: E731

    print("\n  일주 60 — %d장 · 한 장 평균 %d자 · 짝 %d개"
          % (m["n"], m["chars"], len(m["rows"])))
    print("    ① 짝 겹침 평균     %5.1f%%                   문턱 %d%%   %s"
          % (100 * m["mean"], 100 * PAIR_MEAN_MAX, mark("mean")))
    print("    ② 남 짝의 최악     %5.1f%%  (사실 0개 겹침 · %d짝)  문턱 %d%%   %s"
          % (100 * m["stranger_worst"], m["stranger_n"],
             100 * STRANGER_MAX, mark("stranger")))
    print("    ③ 기울기           사실 0개 %.1f%% → 많이 겹친 짝 %.1f%%        %s"
          % (100 * m["stranger_mean"],
             100 * statistics.mean(m["by"][max(m["by"])]), mark("slope")))
    print("    ④ 이 장에만 있는 수 최소 %d개 · 평균 %.1f개      문턱 %d개  %s"
          % (m["own_min"], m["own_mean"], OWN_MIN, mark("own")))
    print("    ⑤ 최다 점유        %5.2f%%                   문턱 %.0f%%    %s"
          % (100 * m["top_share"], 100 * TOP_SHARE_MAX, mark("top")))
    print("    ⑥ 값 묶음이 같은 장 %d개                              %s"
          % (m["dup_values"], mark("values")))
    if not ok["top"]:
        print("       가장 많이 깔린 줄: %s" % m["top"][:70])
    print("    · 참고 — 어느 짝이든 최악은 %.1f%%. 35%%를 넘는 짝이 %.1f%%."
          % (100 * m["worst"], 100 * m["over"]))
    print("      그 짝들은 여덟 사실 가운데 셋넷이 **진짜로 같은** 짝이오 —")
    print("      머리말 ②③ 을 보시오. 여기서 더 가르려면 없는 사실을 지어내야 하오.")

    if a.slope:
        print("\n      겹친 사실  짝 수   평균 겹침   최악")
        for k in sorted(m["by"]):
            print("        %d/%d      %4d    %5.1f%%    %5.1f%%"
                  % (k, len(AXES), len(m["by"][k]),
                     100 * statistics.mean(m["by"][k]), 100 * max(m["by"][k])))
    if a.show:
        for s, k, i, j in sorted(m["rows"], reverse=True)[:a.show]:
            print("      닮은 짝 %5.1f%% (사실 %d개 같음)  %s ↔ %s"
                  % (100 * s, k, m["pages"][i]["gz"], m["pages"][j]["gz"]))

    # ── 용어 — 장이 아니라 한 장의 항목 ─────────────────────────────
    terms = [D.term_page(w) for w in sorted(D.terms_mod.MEANING)]
    t = measure_pages(terms)
    thin = t["chars"] < THIN_MIN
    print("\n  용어 %d — 한 항목 평균 %d자" % (t["n"], t["chars"]))
    print("    항목끼리 겹침      평균 %5.1f%%  최악 %5.1f%%        문턱 %d%%   %s"
          % (100 * t["mean"], 100 * t["worst"], 100 * PAIR_MEAN_MAX,
             "OK" if t["mean"] <= PAIR_MEAN_MAX else "✗"))
    print("    최다 점유          %5.2f%%                       문턱 %.0f%%    %s"
          % (100 * t["top_share"], 100 * TOP_SHARE_MAX,
             "OK" if t["top_share"] <= TOP_SHARE_MAX else "✗"))
    if thin:
        print("    ★ 한 항목이 %d자 — %d자 문턱 아래요. **각자 한 장으로 열지"
              " 않습니다.**" % (t["chars"], THIN_MIN))
        print("      용어집 한 장에 모아 앵커로 잇습니다 (docs/44 §11). 낱말이")
        print("      제 셈을 들고 설 만큼 자라면 그때 장으로 올립니다.")
    if t["mean"] > PAIR_MEAN_MAX or t["top_share"] > TOP_SHARE_MAX:
        bad += 1

    print("\n" + "-" * 72)
    if bad:
        print("  문턱을 못 넘은 자리 %d — **열지 않소.** 축을 더 걸어야 하오." % bad)
        return 1
    print("  [OK] 열어도 되오 — 틀이 하나가 아니고, 글이 셈을 따르오.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
