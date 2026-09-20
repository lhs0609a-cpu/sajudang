# -*- coding: utf-8 -*-
"""
갈래마다 **사실 셋**을 세어 팩폭하는가 (docs/40 §10).

★ 왜 지키나

  되물음의 판정이 **갈래마다 사실 하나, 문장 하나**였습니다.

      방향 · 옮긴다   → 역마가 있나?           사실 하나 → 문장 하나
      돈 · 주식·코인  → 편재가 있나?           사실 하나 → 문장 하나

  여덟 글자는 고민마다 수백 갈래(실효 379~1,149)를 가를 줄 아는데
  판정은 한 자릿수만 썼습니다. 그리고 한 문장이라 팩폭 점수가
  29~57점이었습니다 — 셀 수 있는 값이 적고 겪은 일을 안 짚어서요.

  고친 뒤로 갈래마다 **그 갈래에 걸린 사실 셋**을 셉니다. 사실마다
  「센 것(숫자·간지)」 + 「살림의 말로 짚는 한 줄」.

★ 팩폭은 센 말이지 단정이 아닙니다 (tools/blunt_audit.py)

  아프게 하려면 **구체적**이어야 합니다 — 「빈자리가 크오」 는 안 아프고
  「그래서 아직 혼자 하오」 는 아픕니다. 그리고 질병·수명·이혼·투자
  시점은 세게 말하는 것과 상관없이 금지입니다.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import dramaturgy as D             # noqa: E402
from engine import guard                       # noqa: E402
from engine import topic as T                  # noqa: E402
from engine.calendar import build_chart        # noqa: E402
from engine.features import build_features     # noqa: E402

AS_OF = date(2026, 9, 10)
TAG = re.compile(r"<[^>]+>")

# 물러서는 말 — 팩폭을 깎습니다 (engine/dramaturgy.HEDGE 와 같은 말뭉치)
HEDGE = re.compile(r"게요|쯤|아마|조금|약간|다소|수도 있|편이|듯|"
                   r"경향|하기도|그럴 수|정도")
# 선을 넘는 말 — 세게 말하는 것과 다릅니다 (tools/blunt_audit.BANNED)
BANNED = re.compile(r"다치|병들|앓|죽|이혼|헤어지|사고 나|망하|대박|"
                    r"낫는다|고친다")
# 하오체 한 벌 (tests/test_topic.py 와 같은 자)
HAEYO = re.compile(r"(에요|예요|해요|네요|습니다|입니다|합니다)[.!?\"']")
HANDA = re.compile(r"(?<![가-힣])(한다|이다|했다|된다|간다)[.!?]")

CHARTS = [
    (1988, 5, 17, 15, 55, "F"),
    (1995, 11, 2, 8, 10, "M"),
    (1979, 3, 28, 6, 40, "F"),
    (2001, 6, 18, 21, 5, "M"),
    (1964, 12, 3, 23, 30, "M"),
    (1999, 7, 21, 11, 0, "F"),
]


def _table():
    return json.loads((ROOT / "seed" / "topic.json").read_text(encoding="utf-8"))


def _feats(y, m, d, h, mi, sx, known=True):
    return build_features(build_chart(y, m, d, h, mi, sx, known, "서울"),
                          as_of=AS_OF)


def _sentences():
    for c, subs in _table()["FACTS"].items():
        if c.startswith("_"):
            continue
        for ch, facts in subs.items():
            for fx in facts:
                for k in ("hit", "miss", "unk"):
                    if fx.get(k):
                        yield "%s/%s/%s/%s" % (c, ch, fx["id"], k), fx[k]


def _sub(c, ch):
    q2 = list((_table()["ASK"][c].get("options2") or {}).keys())
    return dict({"choice": ch}, **({"choice2": q2[0]} if q2 else {}))


# ── 모양 ─────────────────────────────────────────────────
def test_갈래마다_사실_셋():
    t = _table()
    for c, spec in t["ASK"].items():
        for ch in spec["options"]:
            facts = t["FACTS"].get(c, {}).get(ch)
            assert facts and len(facts) == 3, \
                "%s/%s 에 사실이 셋이 아니오 (%s)" % (c, ch, facts and len(facts))


def test_사실_이름은_엔진에_있다():
    for c, subs in _table()["FACTS"].items():
        if c.startswith("_"):
            continue
        for ch, facts in subs.items():
            for fx in facts:
                assert fx["id"] in T._FACTS, "%s/%s 의 %r 을 셀 자가 없소" % (c, ch, fx["id"])
                assert fx.get("label") and fx.get("hit") and fx.get("miss"), \
                    "%s/%s/%s 에 이름·문장이 비었소" % (c, ch, fx["id"])


# ── 말 ───────────────────────────────────────────────────
def test_새_문장은_가드를_통과한다():
    bad = [p for p, t in _sentences() if guard.enforce(t, {}) != t]
    assert not bad, "가드에 걸린 문장:\n  " + "\n  ".join(bad)


def test_물러서지_않는다():
    """팩폭은 「게요·아마·쯤·편이」 로 물러서지 않습니다."""
    bad = ["%s — %s" % (p, HEDGE.search(t).group(0))
           for p, t in _sentences() if HEDGE.search(t)]
    assert not bad, "물러서는 말:\n  " + "\n  ".join(bad)


def test_선을_넘지_않는다():
    """센 말과 단정은 다릅니다. 질병·수명·이혼·재물 단정은 금지."""
    bad = ["%s — %s" % (p, BANNED.search(t).group(0))
           for p, t in _sentences() if BANNED.search(t)]
    assert not bad, "선을 넘는 말:\n  " + "\n  ".join(bad)


def test_하오체_한_벌이다():
    bad = [p for p, t in _sentences() if HAEYO.search(t) or HANDA.search(t)]
    assert not bad, "다른 말투가 섞였소:\n  " + "\n  ".join(bad)


# ── 셈 ───────────────────────────────────────────────────
def test_사실은_그_사람_글자에서_나온다():
    """같은 갈래라도 사람마다 겹침/어긋남이 갈려야 합니다 — 누구나 같으면 셈이 아니오."""
    t = _table()
    fs = [_feats(*c) for c in CHARTS]
    for c, subs in t["FACTS"].items():
        if c.startswith("_"):
            continue
        for ch, facts in subs.items():
            if ch not in t["ASK"][c]["options"]:
                continue
            for fx in facts:
                got = {T._FACTS[fx["id"]](f, T._fact_ctx(c, _sub(c, ch)))[0]
                       for f in fs}
                got.discard(None)
                # 여섯 명이 다 같을 수는 있으나, 그 자가 **늘** 한쪽이면 셈이 아니오.
                assert got, "%s/%s/%s 가 아무에게도 안 서오" % (c, ch, fx["id"])


def test_시각_미상이면_시주_자리를_모른다고_한다():
    """없는 시주를 지어내지 않습니다 — 새 사람(시주) 갈래는 「모르오」."""
    f = _feats(1988, 5, 17, None, None, "F", known=False)
    k = T.ask_cut(f, "people", {"choice": "new"})
    text = TAG.sub("", k["html"])
    assert "모르" in text or "세지 않" in text, text[:200]


def test_팩폭_점수가_칠십을_넘는다():
    """
    판정 컷의 팩폭 점수 — 고민마다 평균 70 이상.

    고치기 전 기준선은 29~57점이었습니다(방향 29 · 일 33 · 사랑 36).
    모자라면 문턱을 낮추지 말고 **문장을 고치시오.**
    """
    t = _table()
    fs = [_feats(*c) for c in CHARTS]
    low = []
    for c, spec in t["ASK"].items():
        scores = []
        for ch in spec["options"]:
            for f in fs:
                k = T.ask_cut(f, c, _sub(c, ch))
                html = '<span class="src">근거 · %s</span>%s' % (k["source"], k["html"])
                scores.append(D.score("c2", "판정", html, "read")["bite"])
        avg = sum(scores) / len(scores)
        if avg < 70:
            low.append("%s %.0f" % (c, avg))
    assert not low, "팩폭 점수가 70 아래인 고민: " + " · ".join(low)
