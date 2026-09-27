# -*- coding: utf-8 -*-
"""
같은 말을 몇 번 하나 — **뜻**으로 세는 자. 그리고 설득이 서는가.

    python tools/same_point.py             200명
    python tools/same_point.py --show 1    한 사람 몫을 펴 본다

★ 왜 또 자를 만드나 (2026-09-25 · 두 번째)

  글자 중복을 걷고 나서도 손님이 말했습니다 —
  「퀄리티 너무 떨어져 중복내용도 많고, 여기서 진짜 설득당해서 결제하게
  만들어야하는데 어떻게 된거야.」

  `dull_audit` 은 **글자**가 겹치는 자리를 셉니다. 그걸 0으로 만들었는데도
  중복이 남은 까닭은, 이 집이 같은 셈을 **다른 문장으로** 여러 번 말하기
  때문입니다. 한 사람 몫을 펴 보니 —

      중화(치우치지 않음)   다섯 번   「크게 넘치지도 크게 모자라지도」
                                     「크게 안 기울었소」
                                     「어느 쪽으로도 크게 안 치우친」
                                     「크게 늘리지도 크게 잃지도 않은」
                                     「한쪽으로 크게 치우치지 않은」
      없는 쇠                다섯 번
      식상 흐름              네 번

  글자는 다 다릅니다. 그래서 `dup_rate` 도 `dull_audit` 도 통과합니다.
  손님 눈에는 **같은 얘기**입니다.

★ 그리고 설득을 셉니다

  무료 구간은 값이 오가는 자리 앞입니다. 그런데 세어 보니 무료가 하는 일이
  「그대는 이렇다」 를 여러 번 되풀이하는 것뿐이고, 「그래서 어떻게」 는
  전부 잠겨 있었습니다. 게다가 **못 한다는 말**이 여러 번 섭니다 —
  「판단할 수 없소」 「세어서 나오지 않소」 「내가 맡은 일이 아니네」.

  신뢰를 지키려는 줄입니다(이 집의 규칙이오). 다만 한 장에 여섯 번이면
  손님은 「이 집은 아무것도 안 말해 주는구나」 로 읽습니다.

  이 자는 그 둘을 셉니다 —
      진단 줄 : 처방 줄 의 비
      「못 한다」 가 몇 번
      무료가 손님에게 준 **새 사실**이 몇 가지
"""
from __future__ import annotations

import argparse
import collections
import html as _html
import random
import re
import statistics
import sys
from pathlib import Path
from typing import get_args

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "services" / "api", ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

#: 손님이 **실제로 받는 글**은 `tools/seen_page` 한 자리에서 받습니다.
#
# ★ 이 자는 `bank.build_hook` 을 부르고 있었습니다 (2026-09-27에 고침).
#   그건 분석지(`engine/summary`)와 도구(`engine/screenscan`)만 쓰는
#   자리요. 손님 훅은 `routers/hook` 이 만들고, 그 라우터는 네 층을 더
#   얹습니다 — portrait · topic · specialist · 말투.
#
#   그래서 이 자가 낸 훅 수치는 **다른 물건의 것**이었습니다. 자를
#   제품보다 좁게 두는 것보다 나쁩니다 — 좁으면 못 보고 끝나지만, 다른
#   것을 재면 **고친 줄 알고 넘어갑니다.** 실제로 그렇게 됐습니다:
#   씨앗 55줄을 고쳐 배포했는데 손님 화면에는 안 닿았고 자는 「고쳤다」
#   고 찍었습니다.
#
#   조립을 자마다 흉내 내지 않습니다 — 라우터가 층을 하나 더 얹는 날
#   자들이 조용히 옛 물건을 재기 시작하오.
#   `tests/test_seen_page.py` 가 그 어긋남을 셉니다.
from tools.seen_page import free_page as _free_page   # noqa: E402
from tools.seen_page import sample as _sample         # noqa: E402
from schemas.api import Concern                     # noqa: E402

TAG = re.compile(r"<[^>]+>")
SENT = re.compile(r"[^.?!]+[.?!]")
CONCERNS = get_args(Concern)

# ── 뜻으로 묶는 자 ────────────────────────────────────────────
#
# ★ 낱말이 아니라 **그 셈**으로 묶습니다. 「중화」 를 말하는 길이 여럿이라
#   낱말로 세면 못 잡습니다 — 손님이 읽는 것은 낱말이 아니라 뜻이오.
POINTS = {
    "치우치지 않음(중화)": (
        r"크게 넘치지도|크게 안 기울|크게 안 치우친|크게 치우치지 않|"
        r"크게 늘리지도|넘치지도 모자라지도|어느 쪽으로도 크게 안|"
        r"무엇이든 그럭저럭"),
    "없는 기운": (
        r"(하나뿐|바닥이|한 자도 없|거의 없|없는 (쇠|불|물|흙|나무))|"
        r"(끊고 정리하는|아니라고 말하는 힘|잘라 낼 칼|붙잡아 줄 것이 없)"),
    "흐름이 새는 자리": (
        r"먼저 베푸|내놓은 것이 부족|만드는 데 먼저|힘이 .{1,3} 쪽으로 빠져|"
        r"손보는 힘만 크고|값을 부르는 힘이 없"),
    "쥐는 힘이 얇다": (
        r"쥐는 (글자|힘)|손이 굳|한 번에 큰 잔금|쥔 것을 지키는|"
        r"재성(이|은)? (하나|둘|1자|없)"),
    "때가 바뀐다": r"살에 사주를 읽는 법|다음 대운|보는 글자가 바뀐|해 뒤네|해 뒤요",
    "겪은 일이 있었을 것": r"있었을 것이|해 왔을 것이|왔을 것이|들었을 것이|못 했을 것이",
}

#: **못 한다**는 말. 하나는 정직이고 여섯은 변명입니다.
CANT = re.compile(
    r"판단할 수 (는 )?없|정할 수 없|세어서 나오지 않|안 말해 주|"
    r"말하지 않소|말하지 않네|알 수 없|가를 일이 아니|"
    r"짐작하지 않았")

#: ★ **지켜야 하는 고백**은 셈에서 가릅니다 (2026-09-25).
#
#   처음에는 이 둘도 「못 한다」 로 셌습니다. 그러면 자가 **고칠 수 없는
#   데를 가리킵니다** —
#
#     ① 「그대가 물은 것은 내가 맡은 일이 아니오」 — 손님이 고른 고민을
#        조용히 갈아치우지 않고 **아니라고 말하는** 줄이오. 2026-09-24에
#        일부러 세운 자리요 (`topic.LENS_OFF` · CLAUDE.md 「캐릭터의
#        전문은 없애지 않습니다 — 아니라고 말합니다」).
#     ② 「사주는 매수·매도의 안전을 보증하지 않소」 — 법무 문구요
#        (docs/11). 손대면 안 됩니다.
#
#   둘은 변명이 아니라 **약속**입니다. 자는 고칠 것만 세야 하오.
KEEP = re.compile(r"맡은 일이 아니|보증하지 않|전문가와 확인|의료|진단을 대신")

#: 처방 — 손님이 **오늘 할 수 있는** 말. 진단과 짝이 맞아야 합니다.
CURE = re.compile(
    r"(시오|하세요|하시게|하게|보게)[.!]?$|"
    r"(적으|정하|펴 보|물으|말하|끊으|세우|잡으|재 보|나누)")

#: 되묻는 꼬리. 말투인데, 잦으면 확신이 없어 보입니다.
ASKBACK = re.compile(r"(안 그런가|그렇지 않소|아니오|아시오|묻겠네|묻겠소)[?？]")


def plain(html: str) -> str:
    return re.sub(r"\s+", " ", _html.unescape(TAG.sub(" ", html or ""))).strip()


def sentences(text: str) -> list:
    got = [s.strip() for s in SENT.findall(text)]
    tail = SENT.sub("", text).strip()
    if tail:
        got.append(tail)
    return [s for s in got if len(s) > 6]


def _page(rng: random.Random) -> dict:
    """손님이 받는 글 한 벌. 조립은 `tools/seen_page` 한 자리에서."""
    concern = rng.choice(CONCERNS)
    axis4 = rng.choice((None, "INFP", "ESTJ", "INTP", "ENFJ", "ISTP"))
    pg = _free_page(_sample(rng), concern, axis4, lens_id="nopa")
    return {"blocks": [{"id": b["where"], "html": b["html"]}
                       for b in pg["blocks"]],
            "locked": pg["locked"], "concern": concern}


def audit(page: dict) -> dict:
    bodies = [(b["id"], plain(b["html"])) for b in page["blocks"]]
    whole = " ".join(t for _, t in bodies)
    lines = [(cid, s) for cid, t in bodies for s in sentences(t)]

    # ① 같은 뜻을 몇 번 — 어느 컷에서인지도 같이 셉니다
    hits: dict = {}
    for name, pat in POINTS.items():
        rx = re.compile(pat)
        where = [cid for cid, s in lines if rx.search(s)]
        if where:
            hits[name] = where

    # ② 「못 한다」
    cant = [s for _, s in lines
            if CANT.search(s) and not KEEP.search(s)]
    keep = [s for _, s in lines if KEEP.search(s)]

    # ③ 진단 : 처방
    cure = [s for _, s in lines if CURE.search(s)]

    # ④ 되묻는 꼬리
    back = ASKBACK.findall(whole)

    # ⑤ 잠긴 컷이 **맛보기 한 줄**을 들고 있나.
    #
    # ★ 값 이름(`need_tier_name`)은 여기서 세지 않습니다 — 그건 엔진이 아니라
    #   라우터가 답니다(`routers/report` 180). 엔진만 불러 세었다가 「전부
    #   비었다」 고 잘못 읽었습니다. 자가 제품의 한쪽만 보면 없는 사고를
    #   만들어 냅니다.
    no_teaser = [l["title"] for l in page["locked"]
                 if not (l.get("teaser") or "").strip()]

    return {"chars": len(whole), "cuts": len(bodies),
            "hits": hits,
            "worst": max((len(v) for v in hits.values()), default=0),
            "said_twice": sum(1 for v in hits.values() if len(v) > 1),
            "cant": cant, "keep": keep, "cure": cure, "lines": len(lines),
            "askback": back, "locked": len(page["locked"]),
            "no_teaser": no_teaser}


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

    print("\n같은 말을 몇 번 하나 · 설득이 서는가 (%d명)" % a.n)
    print("=" * 74)
    print("\n  한 장 %d자 · 컷 %.1f개 · 문장 %.0f개"
          % (avg(lambda r: r["chars"]), avg(lambda r: r["cuts"]),
             avg(lambda r: r["lines"])))

    print("\n  ① 같은 뜻을 되풀이 — 두 번 넘게 말한 자리 %.1f가지 · 최다 %.1f번"
          % (avg(lambda r: r["said_twice"]), avg(lambda r: r["worst"])))
    tally = collections.Counter()
    tot = collections.Counter()
    for r in rows:
        for name, where in r["hits"].items():
            tot[name] += len(where)
            if len(where) > 1:
                tally[name] += 1
    for name in POINTS:
        n = tot[name] / max(1, len(rows))
        print("      %-20s 한 장에 %4.1f번   두 번 넘는 사람 %3.0f%%"
              % (name, n, 100 * tally[name] / max(1, len(rows))))

    print("\n  ② 「못 한다」는 말 — 한 장에 %.1f번"
          % avg(lambda r: len(r["cant"])))
    print("      (지켜야 하는 고백 %.1f번은 따로 셉니다 — 약속이오)"
          % avg(lambda r: len(r["keep"])))
    print("  ③ 진단 대 처방 — 처방 %.1f줄 / 전체 %.0f줄 (%.0f%%)"
          % (avg(lambda r: len(r["cure"])), avg(lambda r: r["lines"]),
             100 * avg(lambda r: len(r["cure"])) / max(1, avg(lambda r: r["lines"]))))
    print("  ④ 되묻는 꼬리 — 한 장에 %.1f번" % avg(lambda r: len(r["askback"])))
    print("  ⑤ 잠긴 컷 %.1f개 · 맛보기 한 줄이 없는 컷 %.1f개"
          % (avg(lambda r: r["locked"]), avg(lambda r: len(r["no_teaser"]))))

    if a.show:
        for r in rows[:a.show]:
            print("\n" + "-" * 74)
            print("  한 사람 몫")
            for name, where in sorted(r["hits"].items(),
                                      key=lambda x: -len(x[1])):
                if len(where) > 1:
                    print("    %-20s %d번 ← %s" % (name, len(where),
                                                  " · ".join(where)))
            print("\n    「못 한다」 %d번:" % len(r["cant"]))
            for s in r["cant"][:6]:
                print("      · %s" % s[:66])
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
