"""
명식 축 · MBTI 축 감사 — **그 사람 것**으로 쓰였는가.

    python tools/person_axis.py             둘 다
    python tools/person_axis.py --person    명식 축만
    python tools/person_axis.py --mbti      MBTI 축만
    python tools/person_axis.py --show <컷id>   그 컷이 어떻게 겹치나

★ 왜 또 만드는가

  `tools/same_audit.py` 는 축 둘을 잽니다 — **사람 축(스무 캐릭터)** 과
  **고민 축(여섯 칸)**. 둘 다 명식 **하나**를 고정해 놓고 잽니다.

  그래서 이 집에서 가장 기본인 물음이 한 번도 안 세어졌습니다 —
  **손님이 바뀌면 글이 바뀌는가.** 겹침이 아무리 낮아도 그게 전부
  「그대」 「여덟 글자」 같은 틀이면, 스무 캐릭터가 다 달라도 손님
  열 명은 같은 리포트를 받습니다.

  MBTI 도 같습니다. 화면(a4b)은 열여섯 칸을 내놓고 「어긋난 데가
  여태 그대를 지치게 한 곳이오」 라고 약속하는데, 그 넉 자가 실제로
  몇 컷을 바꾸는지는 아무도 안 셌습니다.

★ 무엇을 세는가

    명식 축   같은 캐릭터·같은 고민·같은 넉 자를 **다른 사람**이
              받았을 때 글자 그대로 같은 몫
    MBTI 축   같은 사람·같은 캐릭터·같은 고민에서 넉 자만 갈았을 때
              (16칸 + 안 적음) 글자 그대로 같은 몫

  명식 축이 높은 컷은 **누구에게나 같은 글**입니다. 고민이 갈려도,
  캐릭터가 갈려도, 그 손님은 옆 사람과 같은 종이를 받습니다.
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
os.environ.setdefault("STORE_PATH", os.path.join(ROOT, ".person.sqlite"))

from engine import bank as bank_mod                       # noqa: E402
from engine.calendar import build_chart                   # noqa: E402
from engine.features import build_features                # noqa: E402
from engine.report import build_report                    # noqa: E402

TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")

AXIS4 = ("INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
         "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP")

# 명식이 서로 멀도록 고릅니다 — 해·달·날·시·성별이 다 갈리게.
PEOPLE = (
    (1993, 11, 25, 15, 55, "M"),
    (1978, 3, 3, 21, 40, "F"),
    (2001, 7, 19, 8, 5, "F"),
    (1966, 1, 9, 2, 30, "M"),
    (1988, 6, 30, 11, 15, "F"),
    (1974, 9, 14, 19, 0, "M"),
    (2005, 12, 2, 5, 45, "F"),
    (1959, 4, 21, 23, 20, "M"),
)

# 같아야 맞는 자리는 없습니다 — 명식 축에서는 **명식조차 달라야** 맞습니다.
# 희소도만 뺍니다. 인구를 세는 자리는 축이 같으면 같은 칸이 나옵니다.
SHARED: set = set()


def _flat(html: str) -> str:
    return WS.sub(" ", TAG.sub("", html or "")).strip()


def _same(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def _seg(s: dict) -> str:
    """훅 한 단이 손님 눈에 닿는 글 전부 — 본문 · 묻는 말 · 그렇소 · 아니오."""
    return _flat(" ".join(str(s.get(k, "")) for k in
                          ("html", "question", "yes", "no")))


def _f(spec):
    return build_features(build_chart(*spec), as_of=date(2026, 9, 7))


def _cuts(f, lens_id, concern, axis4, tier="one"):
    return build_report(f, "t", lens_id, tier, concern, axis4)["cuts"]


def _by_person(lens_id="pungun", concern="money", axis4="INFP"):
    """{컷id: {사람: 글}}"""
    out: dict = {}
    for i, spec in enumerate(PEOPLE):
        for c in _cuts(_f(spec), lens_id, concern, axis4):
            out.setdefault(c["id"], {})[i] = _flat(c["html"])
    return out


def _by_mbti(spec=PEOPLE[0], lens_id="pungun", concern="money"):
    """{컷id: {넉자: 글}} — 16칸 + 안 적음"""
    out: dict = {}
    f = _f(spec)
    for a in AXIS4 + (None,):
        for c in _cuts(f, lens_id, concern, a):
            out.setdefault(c["id"], {})[a or "(안 적음)"] = _flat(c["html"])
    return out


def _hook_by_person(concern="money", axis4="INFP", lens_id="pungun"):
    out: dict = {}
    for i, spec in enumerate(PEOPLE):
        segs = bank_mod.build_hook(_f(spec), concern, axis4)
        for s in segs:
            out.setdefault("훅 %s단" % s.get("stage", "?"), {})[i] = _seg(s)
    return out


def _hook_by_mbti(spec=PEOPLE[0], concern="money", lens_id="pungun"):
    out: dict = {}
    f = _f(spec)
    for a in AXIS4 + (None,):
        for s in bank_mod.build_hook(f, concern, a):
            out.setdefault("훅 %s단" % s.get("stage", "?"), {})[a or "(안 적음)"] = _seg(s)
    return out


def _score(table: dict) -> list:
    """[(컷id, 글자수, 겹친 몫, 낭비 글자, 가짓수, 칸수)] — 낭비 큰 순."""
    rows = []
    for cid, per in table.items():
        vals = [v for v in per.values() if v]
        if len(vals) < 2:
            continue
        base = vals[0]
        laps = [_same(base, v) for v in vals[1:]]
        lap = sum(laps) / len(laps)
        n = sum(len(v) for v in vals) / len(vals)
        rows.append((cid, int(n), lap, int(n * lap), len(set(vals)), len(vals)))
    rows.sort(key=lambda r: -r[3])
    return rows


def _table(title: str, rows: list, limit: int = 24) -> tuple:
    print()
    print(title)
    print("  %-22s %6s %8s %9s %8s" % ("컷", "글자", "겹친 몫", "낭비 글자", "가짓수"))
    print("  " + "-" * 62)
    waste = dead = 0
    for cid, n, lap, w, kinds, axis_n in rows[:limit]:
        if cid in SHARED:
            continue
        waste += w
        flag = ""
        if kinds == 1:
            flag = "  ←── 한 글자도 안 갈림"
            dead += 1
        elif lap > 0.9:
            flag = "  ←── 다시 쓸 자리"
        print("  %-22s %6d %7.0f%% %9d %6d/%d%s"
              % (cid, n, 100 * lap, w, kinds, axis_n, flag))
    return waste, dead


def _show(cid: str, table: dict) -> None:
    per = table.get(cid)
    if not per:
        print("그런 컷이 없소: %s" % cid)
        return
    for k, v in per.items():
        print("\n── %s ──\n%s" % (k, v))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--person", action="store_true")
    ap.add_argument("--mbti", action="store_true")
    ap.add_argument("--concern", default="money")
    ap.add_argument("--lens", default="pungun")
    ap.add_argument("--show")
    a = ap.parse_args()
    both = not (a.person or a.mbti)

    print("명식 축 · MBTI 축 감사 — 그 사람 것으로 쓰였는가")
    print("=" * 74)
    print("고민 %s · 캐릭터 %s · 사람 %d명 · 넉 자 %d칸"
          % (a.concern, a.lens, len(PEOPLE), len(AXIS4) + 1))

    if a.show:
        t = _by_person(a.lens, a.concern)
        if a.show not in t:
            t = _by_mbti(lens_id=a.lens, concern=a.concern)
        _show(a.show, t)
        return 0

    if both or a.person:
        hk = _hook_by_person(a.concern, "INFP", a.lens)
        _table("훅 축 — 사람이 바뀌면 훅이 바뀌는가 (무료 구간)", _score(hk))
        t = _by_person(a.lens, a.concern)
        w, dead = _table("명식 축 — 다른 사람이 같은 글을 받는가", _score(t))
        print("\n  낭비된 글자 합계  %s자 · 한 글자도 안 갈리는 컷 %d개" % (f"{w:,}", dead))

    if both or a.mbti:
        hk = _hook_by_mbti(concern=a.concern, lens_id=a.lens)
        _table("훅 × MBTI — 넉 자를 갈면 훅이 갈리는가", _score(hk))
        t = _by_mbti(lens_id=a.lens, concern=a.concern)
        rows = _score(t)
        moved = [r for r in rows if r[4] > 1]
        print()
        print("MBTI 축 — 넉 자가 실제로 바꾸는 컷")
        print("  전체 %d컷 중 **%d컷**만 갈립니다 (%.0f%%)."
              % (len(rows), len(moved), 100 * len(moved) / max(1, len(rows))))
        for cid, n, lap, w, kinds, axis_n in moved:
            print("  %-22s %6d자 %7.0f%% 겹침 %4d/%d 가지" % (cid, n, 100 * lap, kinds, axis_n))
        if not moved:
            print("  없음 — 넉 자를 갈아도 리포트가 한 글자도 안 바뀌오.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
