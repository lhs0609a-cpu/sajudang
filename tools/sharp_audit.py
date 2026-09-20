"""
날카로움 감사 — **아무 사주나** 넣었을 때 한 사람 얘기로 날카롭게 나오는가.

    python tools/sharp_audit.py            # 200명
    python tools/sharp_audit.py -n 500 --show 3

★ 손님이 한 말 (2026-09-11)

  "어떤 사주를 넣더라도 내가 준 지피티 수준 이상으로 날카롭게 나와야 해."

  한 사람(이현석)으로 좋았다고 모두에게 좋은 것이 아닙니다. 그 한 건은
  척추 한 줄이 우연히 맞은 경우일 수 있습니다. 그래서 **여럿을 뽑아
  같은 잣대로** 잽니다. 감으로 말하지 않습니다.

★ 잣대 — 바깥 글이 날카로웠던 까닭을 셀 수 있는 것으로 옮겼습니다

  척추     명식 바로 뒤에 「이 사람은 무엇을 하는 사람인가」 한 줄이 섰는가
  근거     셀 수 있는 문장(숫자·한자) 비율 ≥ 25%   — 대 볼 수 있는가
  반증     틀릴 수 있는 문장 비율 ≥ 60%              — 바넘이 아닌가
  흐림     흐릿한 문장 비율 ≤ 12%                    — 알아듣는가 (easy_audit)
  대조     「남들은 … / 그대는 …」 ≥ 2                — 남과 갈리는가
  뒤집기   강점 ↔ 같은 힘의 그림자 짝 ≥ 3            — 칭찬만 하지 않는가
  행동     확인 문항을 맞댄 컷이 섰는가              — 행동 증거가 있는가
  고유     척추 글이 표본에서 겹치는 최대 비율        — 한 줄이 흔하지 않은가

  문항 답은 **무작위로** 고릅니다. 사주가 가리키는 쪽만 고르면 늘
  「다 같다」 가 나와 좋아 보입니다 — 그건 재는 것이 아닙니다.
"""
from __future__ import annotations

import argparse
import html as _html
import random
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT / "tools"))

import population                                   # noqa: E402
from easy_audit import vague_of                     # noqa: E402
from engine import probe as probe_mod               # noqa: E402
from engine.report import build_report              # noqa: E402

TAG = re.compile(r"<[^>]+>")
GLOSS = re.compile(r'<i class="gl">.*?</i>', re.S)
SENT = re.compile(r"[^.?!]+[.?!]")
COUNTED = re.compile(r"\d|[一-鿿]")
NUM = re.compile(r"\d|(?:하나|둘|셋|넷|다섯|여섯|일곱|여덟|아홉|열)(?=이오|뿐|밖에|째)|하나도 없")
WHEN = re.compile(r"올해|내년|작년|이번 주|다음 달|스물|서른|마흔|쉰|예순")
ACT = re.compile(r"(본다|한다|간다|산다|온다|미룬다|고른다|버린다|남긴다|묻는다|적는다|"
                 r"보오|하오|가오|접소|미루오|고치오|묻소|적소|셌소|끊소)")
CONCERNS = ["money", "work", "love", "people", "dir", "health"]
LENSES = ["pungun", "baegun", "wolha", "cheongam", "sigye", "eunbyeol"]
T16 = [a + b + c + d for a in "IE" for b in "NS" for c in "TF" for d in "JP"]

PASS = {"근거": 0.25, "반증": 0.60, "흐림": 0.12, "대조": 2, "뒤집기": 3}


def sentences(h: str) -> list:
    t = _html.unescape(TAG.sub(" ", GLOSS.sub("", h.replace("<br />", " "))))
    return [s.strip() for s in SENT.findall(re.sub(r"\s+", " ", t)) if len(s.strip()) > 6]


def score(rep: dict) -> dict:
    # ★ 본문만 잽니다 (2026-09-11). 셈 장부 · 그 캐릭터의 눈은 **접힌 자리**라
    #   손님이 먼저 읽는 글이 아닙니다 (engine/report.fold_of).
    allcuts = rep["cuts"]
    cuts = [c for c in allcuts if not c.get("fold")]
    ids = [c["id"] for c in allcuts if c["id"] == "chart"] + [c["id"] for c in cuts]
    sents = [s for c in cuts for s in sentences(c["html"])]
    n = max(len(sents), 1)
    vague = sum(1 for s in sents if (lambda v: v[0] >= 2 or v[1])(vague_of(s)))
    depth = next((c["html"] for c in cuts if c["id"] == "spine_depth"), "")
    return {
        "척추": ids[:2] == ["chart", "spine"],
        "근거": sum(1 for s in sents if COUNTED.search(s)) / n,
        "반증": sum(1 for s in sents if NUM.search(s) or WHEN.search(s) or ACT.search(s)) / n,
        "흐림": vague / n,
        "대조": depth.count('class="vs"'),
        "뒤집기": depth.count('class="pair"'),
        "행동": "probe" in ids,
        "문장": n,
    }


def passes(s: dict) -> bool:
    return (s["척추"] and s["행동"] and s["근거"] >= PASS["근거"]
            and s["반증"] >= PASS["반증"] and s["흐림"] <= PASS["흐림"]
            and s["대조"] >= PASS["대조"] and s["뒤집기"] >= PASS["뒤집기"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=200)
    ap.add_argument("--show", type=int, default=0, help="떨어진 사람 몇 명의 사유를 보일까")
    a = ap.parse_args()
    rng = random.Random(20260911)
    rows, spines, fails = [], Counter(), []
    for i, f in enumerate(population.sample(a.n, seed=20260911)):
        spec = probe_mod.spec(f)      # 공통 셋 + 그 사람 척추 전용 셋
        answers = {it["id"]: rng.choice(it["options"])["id"] for it in spec["items"]}
        rep = build_report(f, "sharp", rng.choice(LENSES), "one", rng.choice(CONCERNS),
                           rng.choice(T16 + [None]), extras={"probe": {"answers": answers}})
        s = score(rep)
        rows.append(s)
        sp = next((c for c in rep["cuts"] if c["id"] == "spine"), None)
        if sp:
            spines[re.sub(r"<[^>]+>|\d", "", sp["html"].split('<div class="chain">')[0])] += 1
        if not passes(s):
            fails.append((i, s))
    N = len(rows)
    ok = sum(1 for s in rows if passes(s))

    def avg(k):
        return sum(s[k] for s in rows) / N

    def worst(k, low=True):
        return (min if low else max)(s[k] for s in rows)

    print(population.banner(N))
    print("잣대를 다 넘은 사람  %d / %d  (%.0f%%)" % (ok, N, 100 * ok / N))
    print("  척추 한 줄      %5.0f%%" % (100 * sum(s["척추"] for s in rows) / N))
    print("  행동 맞대기      %5.0f%%" % (100 * sum(s["행동"] for s in rows) / N))
    print("  근거 문장 비율   평균 %4.0f%%  최저 %4.0f%%  (문턱 %d%%)"
          % (100 * avg("근거"), 100 * worst("근거"), 100 * PASS["근거"]))
    print("  반증 문장 비율   평균 %4.0f%%  최저 %4.0f%%  (문턱 %d%%)"
          % (100 * avg("반증"), 100 * worst("반증"), 100 * PASS["반증"]))
    print("  흐린 문장 비율   평균 %4.0f%%  최고 %4.0f%%  (문턱 %d%%)"
          % (100 * avg("흐림"), 100 * worst("흐림", low=False), 100 * PASS["흐림"]))
    print("  대조 · 뒤집기    최저 %d · %d" % (worst("대조"), worst("뒤집기")))
    top = spines.most_common(1)[0][1] if spines else 0
    print("  척추 글 겹침     %d가지 · 한 글을 받는 최대 %.1f%%" % (len(spines), 100 * top / N))
    why = Counter()
    for _, s in fails:
        for k, bad in (("척추", not s["척추"]), ("행동", not s["행동"]),
                       ("근거", s["근거"] < PASS["근거"]), ("반증", s["반증"] < PASS["반증"]),
                       ("흐림", s["흐림"] > PASS["흐림"]), ("대조", s["대조"] < PASS["대조"]),
                       ("뒤집기", s["뒤집기"] < PASS["뒤집기"])):
            if bad:
                why[k] += 1
    if why:
        print("  떨어진 까닭      " + " · ".join("%s %d" % kv for kv in why.most_common()))
    for i, s in fails[:a.show]:
        print("   #%d %s" % (i, {k: (round(v, 2) if isinstance(v, float) else v) for k, v in s.items()}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
