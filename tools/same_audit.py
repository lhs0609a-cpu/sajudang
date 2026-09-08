"""
같은 글 감사 — **어느 자리**가 겹치는가

    python tools/same_audit.py            자리별로 낭비된 글자를 센다
    python tools/same_audit.py --lens     사람 축만
    python tools/same_audit.py --concern  고민 축만
    python tools/same_audit.py --show <컷id>   그 컷이 실제로 어떻게 겹치나

★ 왜 따로 만드는가

  `engine/worth.axis_own` 이 겹침을 **낱말 집합**으로 잽니다. 한 장을
  통째로 놓고 재는 값이라 「62% 겹침」 이라는 수는 나오는데, **어느
  자리를 고쳐야 하는지**는 안 나옵니다. 조사와 명리 용어와 「그대」가
  다 같이 세어지기 때문입니다.

  고칠 데를 정하려면 **컷마다** 봐야 합니다. 그리고 겹친 글자 수로
  줄을 세워야 합니다 — 200자짜리가 100% 같은 것보다 1,600자짜리가
  70% 같은 것이 먼저입니다.

★ 무엇을 세는가

      사람 축   같은 명식·같은 고민을 스무 사람이 읽었을 때
                **글자 그대로 같은** 몫
      고민 축   같은 명식·같은 사람이 여섯 고민을 물었을 때
                **글자 그대로 같은** 몫

  「낭비된 글자」 = 그 컷 글자수 × 겹친 몫. 이 수가 큰 자리부터
  고치면 값이 가장 빨리 오릅니다.

★ 겹치는 게 늘 흠은 아닙니다

  명식(chart)은 여덟 글자를 적는 자리라 스무 사람이 같아야 맞습니다.
  희소도도 인구를 세는 자리라 같습니다. 그런 자리는 아래 `SHARED` 에
  적어 두고 셈에서 뺍니다 — 안 그러면 고칠 수 없는 것이 늘 1등으로
  올라와 표를 못 읽습니다.
"""
from __future__ import annotations

import argparse
import difflib
import os
import re
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "services", "api"))
os.environ.setdefault("STORE_PATH", os.path.join(ROOT, ".same.sqlite"))

from engine import lens as lens_mod                      # noqa: E402
from engine.calendar import build_chart                  # noqa: E402
from engine.features import build_features               # noqa: E402
from engine.report import build_report                   # noqa: E402

TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")
CONCERNS = ("money", "work", "love", "people", "dir", "health")

# ★ 같아야 맞는 자리 — 셈에서 뺍니다.
#   여덟 글자를 적는 자리와 인구를 세는 자리는 스무 사람이 같아야
#   합니다. 여기를 갈라 놓으면 그건 사람마다 다른 명식을 내는 것입니다.
SHARED = {"chart", "rarity"}

PEOPLE = ((1993, 11, 25, 15, 55, "M"), (1978, 3, 3, 21, 40, "F"),
          (2001, 7, 19, 8, 5, "F"))


def _flat(html: str) -> str:
    return WS.sub(" ", TAG.sub("", html or "")).strip()


def _same(a: str, b: str) -> float:
    """두 글이 **글자 그대로** 얼마나 같은가 (0~1)."""
    if not a and not b:
        return 1.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def _people():
    for spec in PEOPLE:
        yield build_features(build_chart(*spec), as_of=date(2026, 9, 7))


def _by_lens(f, concern="work"):
    """{컷id: {사람: 글}}"""
    out: dict = {}
    for l in lens_mod.released():
        tier = "one" if l.get("price") else "free"
        for c in build_report(f, "t", l["id"], tier, concern, "INFP")["cuts"]:
            out.setdefault(c["id"], {})[l["id"]] = _flat(c["html"])
    return out


def _by_concern(f, lens_id="pungun"):
    """{컷id: {고민: 글}}"""
    out: dict = {}
    for concern in CONCERNS:
        for c in build_report(f, "t", lens_id, "one", concern, "INFP")["cuts"]:
            out.setdefault(c["id"], {})[concern] = _flat(c["html"])
    return out


def _score(table: dict) -> list:
    """[(컷id, 글자수, 겹친 몫, 낭비된 글자, 가짓수)] — 낭비 큰 순."""
    rows = []
    for cid, per in table.items():
        vals = [v for v in per.values() if v]
        if len(vals) < 2:
            continue
        base = vals[0]
        laps = [_same(base, v) for v in vals[1:]]
        lap = sum(laps) / len(laps)
        n = sum(len(v) for v in vals) / len(vals)
        rows.append((cid, int(n), lap, int(n * lap), len(set(vals))))
    rows.sort(key=lambda r: -r[3])
    return rows


def _table(title: str, rows: list, axis_n: int, limit: int = 18) -> int:
    print()
    print(title)
    print("  %-22s %6s %8s %9s %7s" % ("컷", "글자", "겹친 몫", "낭비 글자", "가짓수"))
    print("  " + "-" * 60)
    waste = 0
    for cid, n, lap, w, kinds in rows[:limit]:
        if cid in SHARED:
            continue
        waste += w
        flag = "  ←── 다시 쓸 자리" if lap > 0.9 else ""
        print("  %-22s %6d %7.0f%% %9d %5d/%d%s"
              % (cid, n, 100 * lap, w, kinds, axis_n, flag))
    return waste


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lens", action="store_true")
    ap.add_argument("--concern", action="store_true")
    ap.add_argument("--show", default=None, help="이 컷이 실제로 어떻게 겹치나")
    args = ap.parse_args()

    f = next(_people())
    print("같은 글 감사 — 어느 자리가 겹치는가")
    print("=" * 74)
    print("명식 하나로 잽니다. 사람 축은 스무 명 · 고민 축은 여섯 칸.")

    if args.show:
        per = _by_lens(f).get(args.show, {})
        if not per:
            print("그런 컷이 없소: %s" % args.show)
            return 1
        vals = list(per.values())
        print()
        print("[%s] 스무 사람이 받는 글" % args.show)
        for lid, v in list(per.items())[:4]:
            print("  · %-11s %s" % (lens_mod.get(lid)["name"], v[:150]))
        print()
        print("  글자 그대로 다른 것: %d가지 / %d명" % (len(set(vals)), len(vals)))
        return 0

    both = not (args.lens or args.concern)
    total = 0
    if args.lens or both:
        rows = _score(_by_lens(f))
        total += _table("사람 축 — 스무 사람이 같은 글을 받는가", rows, 20)
    if args.concern or both:
        rows = _score(_by_concern(f))
        total += _table("고민 축 — 여섯 칸이 같은 글을 받는가", rows, 6)

    print()
    print("  낭비된 글자 합계  %s자" % format(total, ","))
    print()
    print("  ★ 겹친 몫이 90%% 를 넘는 자리가 **다시 쓸 자리**입니다.")
    print("    거기는 축이 아예 안 걸려 있다는 뜻이오 — 문장을 늘리지 말고")
    print("    **무엇을 세는지**를 축으로 다시 거시오.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
