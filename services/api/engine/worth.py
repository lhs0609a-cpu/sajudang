# -*- coding: utf-8 -*-
"""
값값 점수 — **치른 값이 아깝지 않은가.** 100점 만점.

    from engine import worth
    worth.score()          # {"total": 78, "axes": [...], "at": ...}

★ 손님이 시킨 것 (2026-09-07)

  "실제 그 돈 써도 돈값한다, 진짜 감동이다, 이거 돈 써도 하나도
   안 아깝다, 오히려 돈 번 느낌이다 들 정도 퀄리티인지 종합점수
   파악해서 관리자페이지에 실시간 연동해놓고, 100점만점으로."

★ 지어낸 점수가 아닙니다

  연출 점수(`screenscan`)와 같은 규칙입니다 — **실제로 나가는 글**을
  그 자리에서 재서 냅니다. 표본 명식을 진짜로 돌려 리포트를 짓고,
  그 글을 셉니다. 그러니 뱅크를 고치면 이 숫자가 바로 움직입니다.

★ 배포본에서도 돌아야 합니다

  배포 이미지에는 `apps/web` 도 `tools` 도 없습니다 (Dockerfile 은
  `seed/` 와 `services/api/` 만 넣습니다). 그래서 여섯 축을 전부
  **seed + 엔진**만으로 잽니다. 화면 쪽 축(끌림)은 `screenscan` 이
  이미 찍어 둔 글(`seed/screen_text.json`)로 재는 그 길을 그대로 씁니다.

★ 왜 여섯인가 — 손님이 「돈값」이라 느끼는 자리

    나만의 것    남과 다른 글이 나오는가          25
    근거         왜 그렇게 말하는지 따라가는가     20
    아픈 정확도  뜬 말이 아니라 손에 잡히는가      20
    값만큼       값이 오르면 실제로 더 주는가      15
    읽힘         읽다가 막히지 않는가              10
    끌림         다음 화가 보고 싶어지는가         10

  가중치는 **바꿀 수 있게** 한자리에 둡니다. 다만 「나만의 것」이
  가장 큰 것은 이 집의 포지션이 그래서입니다 — 남과 같은 글이면
  값을 치를 까닭이 없습니다.

★ 점수를 올리려고 문장을 지우지 마세요

  「뜬 말」을 줄이려고 명리 용어를 빼면 근거가 사라집니다. 두 축이
  서로를 잡고 있으니 한쪽만 올리면 다른 쪽이 내려갑니다. 그게 이
  점수의 쓸모입니다.
"""
from __future__ import annotations

import itertools
import re
from datetime import datetime
from functools import lru_cache
from typing import Optional

# ══════════════════════════════════════════════════════════
# 표본 — 재는 데 쓰는 사람들
# ══════════════════════════════════════════════════════════
#
# ★ 고정입니다. 무작위로 뽑으면 새로 고칠 때마다 점수가 흔들려
#   «내가 고쳐서 오른 것인지» 를 못 봅니다.
PEOPLE = [
    (1993, 7, 14, 5, 20, "F"),
    (1988, 11, 2, 21, 40, "M"),
    (2001, 3, 19, 13, 5, "F"),
    (1975, 1, 28, 8, 10, "M"),
    (1996, 9, 30, 23, 50, "F"),
    (1969, 6, 5, 11, 35, "M"),
]
CONCERNS = ("money", "work", "love", "people", "dir", "health")
LENS = "wolha"

WEIGHT = {
    "own": 25,      # 나만의 것
    "ground": 20,   # 근거
    "sting": 20,    # 아픈 정확도
    "worth": 15,    # 값만큼
    "read": 10,     # 읽힘
    "pull": 10,     # 끌림
}

_TAG = re.compile(r"<[^>]+>")
_NUM = re.compile(r"\d")


def _flat(html: str) -> str:
    return re.sub(r"\s+", " ", _TAG.sub(" ", html or "")).strip()


@lru_cache(maxsize=1)
def _samples() -> list:
    """(features, {고민: 컷들}) — 한 번만 짓고 돌려 씁니다."""
    from .calendar import build_chart
    from .features import build_features
    from .report import build_report

    out = []
    for y, m, d, h, mi, sx in PEOPLE:
        try:
            f = build_features(build_chart(y, m, d, h, mi, sx, city="서울"))
        except Exception:
            continue
        per = {}
        for c in CONCERNS:
            try:
                per[c] = build_report(f, "worth", LENS, "all", c,
                                      axis4="INFP")["cuts"]
            except Exception:
                pass
        if per:
            out.append((f, per))
    return out


def _band(value: float, good: float, bad: float) -> int:
    """
    잰 값을 0~100 으로. `good` 이면 100, `bad` 면 0, 사이는 곧게.

    ★ 문턱을 여기 한자리에 둡니다. 축마다 흩어 두면 나중에
      «이 점수가 왜 이런가» 를 못 따라갑니다.
    """
    if good == bad:
        return 100
    t = (value - bad) / (good - bad)
    return max(0, min(100, int(round(t * 100))))


# ══════════════════════════════════════════════════════════
# ① 나만의 것 — 남과 다른 글이 나오는가
# ══════════════════════════════════════════════════════════
def axis_own() -> dict:
    """
    두 가지를 봅니다 —
      · 같은 사람이 **다른 고민**을 물으면 글이 갈리는가
      · 다른 사람끼리 **같은 문장**을 받지는 않는가
    """
    rows = _samples()
    if not rows:
        return {"score": 0, "why": "표본을 못 지었소"}

    # 고민 쌍 겹침
    laps = []
    for _f, per in rows:
        got = [c for c in CONCERNS if c in per]
        for a, b in itertools.combinations(got, 2):
            ta = " ".join(_flat(x["html"]) for x in per[a])
            tb = " ".join(_flat(x["html"]) for x in per[b])
            A, B = set(ta.split()), set(tb.split())
            laps.append(len(A & B) / max(1, len(A | B)))
    lap = sum(laps) / max(1, len(laps))

    # 사람 사이 같은 문장 — 같은 고민에서 남과 겹치는 비율
    cross = []
    for a, b in itertools.combinations(range(len(rows)), 2):
        for c in CONCERNS:
            if c not in rows[a][1] or c not in rows[b][1]:
                continue
            ta = " ".join(_flat(x["html"]) for x in rows[a][1][c])
            tb = " ".join(_flat(x["html"]) for x in rows[b][1][c])
            A, B = set(ta.split()), set(tb.split())
            cross.append(len(A & B) / max(1, len(A | B)))
    xl = sum(cross) / max(1, len(cross))

    # 고민이 갈리는 컷 비율
    moved = total = 0
    for _f, per in rows:
        ids = [x["id"] for x in per.get("love", [])]
        for cid in ids:
            texts = {_flat(x["html"]) for c in CONCERNS if c in per
                     for x in per[c] if x["id"] == cid}
            total += 1
            if len(texts) > 1:
                moved += 1
    mv = moved / max(1, total)

    s = round(0.40 * _band(lap, 0.45, 0.90)
              + 0.35 * _band(xl, 0.35, 0.80)
              + 0.25 * _band(mv, 0.85, 0.30))
    return {
        "score": int(s),
        "parts": [
            {"k": "고민을 바꾸면 갈리는가", "v": "%.0f%% 겹침" % (100 * lap),
             "s": _band(lap, 0.45, 0.90)},
            {"k": "남과 다른 글인가", "v": "%.0f%% 겹침" % (100 * xl),
             "s": _band(xl, 0.35, 0.80)},
            {"k": "물음 따라 움직이는 컷", "v": "%.0f%%" % (100 * mv),
             "s": _band(mv, 0.85, 0.30)},
        ],
    }


# ══════════════════════════════════════════════════════════
# ② 근거 — 왜 그렇게 말하는지 따라가는가
# ══════════════════════════════════════════════════════════
def axis_ground() -> dict:
    """
    컷마다 근거 줄이 있는가 · 그 줄에 **셀 수 있는 수**가 있는가 ·
    출처(유파)를 대는가.
    """
    rows = _samples()
    if not rows:
        return {"score": 0, "why": "표본을 못 지었소"}
    cuts = [x for _f, per in rows for c in per for x in per[c]]
    n = max(1, len(cuts))
    has = sum(1 for x in cuts if (x.get("source") or "").strip())
    num = sum(1 for x in cuts if _NUM.search(x.get("source") or ""))
    src = sum(1 for x in cuts if "〔" in (x.get("source") or "")
              or "·" in (x.get("source") or ""))
    a, b, c = has / n, num / n, src / n
    s = round(0.34 * _band(a, 1.0, 0.6)
              + 0.40 * _band(b, 0.80, 0.20)
              + 0.26 * _band(c, 0.95, 0.5))
    return {
        "score": int(s),
        "parts": [
            {"k": "근거 줄이 붙은 컷", "v": "%.0f%%" % (100 * a),
             "s": _band(a, 1.0, 0.6)},
            {"k": "셀 수 있는 수를 댄 컷", "v": "%.0f%%" % (100 * b),
             "s": _band(b, 0.80, 0.20)},
            {"k": "무엇을 읽었는지 적은 컷", "v": "%.0f%%" % (100 * c),
             "s": _band(c, 0.95, 0.5)},
        ],
    }


# ══════════════════════════════════════════════════════════
# ③ 아픈 정확도 — 뜬 말이 아니라 손에 잡히는가
# ══════════════════════════════════════════════════════════
#
# ★ 「빈자리가 크오」 는 안 아프고 「그래서 아직 혼자 하오」 는 아픕니다.
#   아픈 것은 세기가 아니라 **정확도**입니다 (tools/blunt_audit.py).
LIVE = ("했소", "하오", "했을", "던 ", "적이 있", "밤", "말", "돈", "사람",
        "전화", "연락", "혼자", "먼저", "늦", "미루", "참", "그만",
        "통장", "잠", "새벽", "집", "일", "짝", "곁")
VAGUE = ("기운", "자리요", "결이오", "경향", "성향", "편이오", "쪽이오")


def axis_sting() -> dict:
    rows = _samples()
    if not rows:
        return {"score": 0, "why": "표본을 못 지었소"}
    sents, hard, soft, counted = [], 0, 0, 0
    for _f, per in rows:
        for c in per:
            for x in per[c]:
                for t in re.split(r"(?<=[.!?오요다])\s+", _flat(x["html"])):
                    t = t.strip()
                    if len(t) < 8:
                        continue
                    sents.append(t)
                    if any(w in t for w in LIVE):
                        hard += 1
                    elif any(w in t for w in VAGUE):
                        soft += 1
                    if _NUM.search(t):
                        counted += 1
    n = max(1, len(sents))
    a, b, c = hard / n, soft / n, counted / n
    s = round(0.45 * _band(a, 0.55, 0.15)
              + 0.30 * _band(b, 0.05, 0.35)
              + 0.25 * _band(c, 0.25, 0.05))
    return {
        "score": int(s),
        "parts": [
            {"k": "손에 잡히는 줄", "v": "%.0f%%" % (100 * a),
             "s": _band(a, 0.55, 0.15)},
            {"k": "뜬 말만 있는 줄", "v": "%.0f%%" % (100 * b),
             "s": _band(b, 0.05, 0.35)},
            {"k": "수를 댄 줄", "v": "%.0f%%" % (100 * c),
             "s": _band(c, 0.25, 0.05)},
        ],
    }


# ══════════════════════════════════════════════════════════
# ④ 값만큼 — 값이 오르면 실제로 더 주는가
# ══════════════════════════════════════════════════════════
def axis_worth() -> dict:
    """
    값 ↔ 컷수·글자 상관과 **옆 등급과의 폭**. 상관은 순서를 보지
    폭을 안 봅니다 — 넷이 같은 분량이면 그건 값이 아니라 이름표입니다.
    """
    import payments
    from .lens import all_lenses
    from .report import build_report

    rows = _samples()
    if not rows:
        return {"score": 0, "why": "표본을 못 지었소"}
    f = rows[0][0]

    got = []
    for l in all_lenses():
        price = int(l.get("price") or 0)
        if price <= 0:
            continue
        try:
            cuts = build_report(f, "worth", l["id"], "all", "love",
                                axis4="INFP")["cuts"]
        except Exception:
            continue
        chars = sum(len(_flat(x["html"])) for x in cuts)
        got.append((price, len(cuts), chars))
    if len(got) < 3:
        return {"score": 0, "why": "잴 상품이 모자라오"}

    def corr(xs, ys):
        n = len(xs)
        mx, my = sum(xs) / n, sum(ys) / n
        cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        dx = sum((x - mx) ** 2 for x in xs) ** 0.5
        dy = sum((y - my) ** 2 for y in ys) ** 0.5
        return cov / (dx * dy) if dx and dy else 0.0

    price = [g[0] for g in got]
    rc = corr(price, [g[1] for g in got])
    rh = corr(price, [g[2] for g in got])

    # 등급별 최다 컷수 — 옆 등급과 몇 컷 차이인가
    by = {}
    for p, k, _ in got:
        by[p] = max(by.get(p, 0), k)
    steps = sorted(by.items())
    gaps = [steps[i + 1][1] - steps[i][1] for i in range(len(steps) - 1)]
    flat0 = sum(1 for g in gaps if g <= 0)
    tight = flat0 / max(1, len(gaps))

    s = round(0.40 * _band(rc, 0.95, 0.30)
              + 0.30 * _band(rh, 0.95, 0.30)
              + 0.30 * _band(tight, 0.0, 0.5))
    return {
        "score": int(s),
        "parts": [
            {"k": "값 ↔ 컷수", "v": "%+.3f" % rc, "s": _band(rc, 0.95, 0.30)},
            {"k": "값 ↔ 글자", "v": "%+.3f" % rh, "s": _band(rh, 0.95, 0.30)},
            {"k": "옆 등급과 안 벌어진 칸", "v": "%d / %d" % (flat0, len(gaps)),
             "s": _band(tight, 0.0, 0.5)},
        ],
    }


# ══════════════════════════════════════════════════════════
# ⑤ 읽힘 — 읽다가 막히지 않는가
# ══════════════════════════════════════════════════════════
def axis_read() -> dict:
    from . import terms as terms_mod

    rows = _samples()
    if not rows:
        return {"score": 0, "why": "표본을 못 지었소"}

    long_p = total_p = 0
    bare = seen_terms = 0
    for _f, per in rows:
        for c in per:
            # ★ 풀이는 **한 벌에 한 번**만 붙습니다 (`terms.gloss` 의 seen).
            #   컷마다 세면 두 번째부터 전부 「안 풀렸다」로 잡혀,
            #   제대로 도는 층을 고장 난 것으로 읽습니다.
            whole = " ".join(_flat(x["html"]) for x in per[c])
            tight = whole.replace(" ", "")
            for term in terms_mod.MEANING:
                if term in whole:
                    seen_terms += 1
                    if term + "(" not in tight:
                        bare += 1
            for x in per[c]:
                for para in re.split(r"</p>|<br\s*/?>", x["html"] or ""):
                    t = _flat(para)
                    if len(t) < 4:
                        continue
                    total_p += 1
                    if len(t) > 120:
                        long_p += 1
    lp = long_p / max(1, total_p)
    br = bare / max(1, seen_terms)
    s = round(0.55 * _band(lp, 0.05, 0.40) + 0.45 * _band(br, 0.55, 0.95))
    return {
        "score": int(s),
        "parts": [
            {"k": "긴 문단(120자 넘음)", "v": "%.0f%%" % (100 * lp),
             "s": _band(lp, 0.05, 0.40)},
            {"k": "풀이 없이 나온 어려운 말", "v": "%.0f%%" % (100 * br),
             "s": _band(br, 0.55, 0.95)},
        ],
    }


# ══════════════════════════════════════════════════════════
# ⑥ 끌림 — 다음 화가 보고 싶어지는가
# ══════════════════════════════════════════════════════════
def axis_pull() -> dict:
    """연출 점수를 그대로 씁니다 — 이미 화면마다 재고 있습니다."""
    from . import screenscan
    try:
        sm = screenscan.summary()
    except Exception:
        return {"score": 0, "why": "화면 글을 못 읽었소"}
    if not sm.get("screens"):
        return {"score": 0, "why": "찍어 둔 화면 글이 없소 — .\\dev.ps1 drama"}
    keys = ("pull", "bite", "heart", "clear", "plain")
    vals = [sm.get(k) or 0 for k in keys]
    s = round(sum(vals) / len(vals))
    return {
        "score": int(s),
        "source": sm.get("source"),
        "parts": [{"k": k, "v": "%d" % (sm.get(k) or 0), "s": sm.get(k) or 0}
                  for k in keys],
    }


# ══════════════════════════════════════════════════════════
# 합
# ══════════════════════════════════════════════════════════
NAMES = {
    "own": "나만의 것",
    "ground": "근거",
    "sting": "아픈 정확도",
    "worth": "값만큼",
    "read": "읽힘",
    "pull": "끌림",
}
ASK = {
    "own": "남과 다른 글이 나오는가",
    "ground": "왜 그렇게 말하는지 따라가는가",
    "sting": "뜬 말이 아니라 손에 잡히는가",
    "worth": "값이 오르면 실제로 더 주는가",
    "read": "읽다가 막히지 않는가",
    "pull": "다음 화가 보고 싶어지는가",
}
GRADE = [
    (90, "돈 번 느낌", "값을 치르고 더 얻었다고 느낄 자리요."),
    (80, "안 아깝다", "값값은 하오. 감동까지는 한 걸음 남았소."),
    (70, "돈값은 한다", "손해는 아니오. 다만 남에게 권할 만큼은 아니오."),
    (55, "아깝다", "치른 값이 아깝소. 고칠 데가 뚜렷하오."),
    (0, "못 판다", "이 상태로 값을 받으면 안 되오."),
]


def score() -> dict:
    """값값 점수 한 벌. 관리자 화면이 이걸 그대로 그립니다."""
    axes = {
        "own": axis_own(), "ground": axis_ground(), "sting": axis_sting(),
        "worth": axis_worth(), "read": axis_read(), "pull": axis_pull(),
    }
    total = sum(axes[k]["score"] * WEIGHT[k] for k in WEIGHT) / sum(WEIGHT.values())
    total = int(round(total))
    grade, say = next((g, s) for cut, g, s in GRADE if total >= cut)
    weak = sorted(axes.items(), key=lambda kv: kv[1]["score"])[:2]
    return {
        "at": datetime.now().isoformat(timespec="seconds"),
        "total": total,
        "grade": grade,
        "say": say,
        "weakest": [{"key": k, "name": NAMES[k], "score": v["score"]}
                    for k, v in weak],
        "axes": [
            {"key": k, "name": NAMES[k], "ask": ASK[k],
             "weight": WEIGHT[k], **axes[k]}
            for k in ("own", "ground", "sting", "worth", "read", "pull")
        ],
    }


def clear() -> None:
    """표본을 다시 짓게 합니다 — 고치고 새로 고치면 바로 움직여야 하오."""
    _samples.cache_clear()
