# -*- coding: utf-8 -*-
"""
되물음의 답이 **처방까지 흘러가는가** (docs/40 §9).

★ 왜 지키나

  답이 처방에 거의 안 닿고 있었습니다. 사랑에서 「혼자 마음만」과
  「끝나는 중」을 골랐을 때 유료 31컷 중 **달라진 컷이 하나**였습니다.
  짝사랑이든 이별이든 저울·짜임·때가 글자 하나 안 달랐습니다.

  고친 뒤로 답은 **어느 칸·어느 짜임을 먼저 볼지**를 고릅니다. 새로
  세지 않습니다. 그리고 답 안 한 사람은 **예전과 같은 글**을 받아야
  합니다 — 기존 손님의 결과를 흔들면 안 됩니다.

★ 여기서 지키는 것 여섯

  ① 답 안 하면 예전과 같다
  ② 답이 여러 컷을 바꾼다 (한 컷이 아니라)
  ③ 조용한 칸을 끌어올리지 않는다 — 끌어올렸더니 쏠림이 뛰었습니다
  ④ 몸에는 세운 줄을 안 단다 — 건강을 해로 못 박으면 예언이오
  ⑤ 두 번째 물음은 **셈이 갈리는 자리에만** 둔다
  ⑥ 대운 칸이 드는 해는 **양력 생년 + 나이**다 — 1·2월생이 한 해
     어긋나던 자리
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import bank as bank_mod            # noqa: E402
from engine import pattern as P                # noqa: E402
from engine import topic as T                  # noqa: E402
from engine.bite import GROUP_OF               # noqa: E402
from engine.calendar import build_chart        # noqa: E402
from engine.features import build_features     # noqa: E402
from engine.report import build_report         # noqa: E402

TAG = re.compile(r"<[^>]+>")
AS_OF = date(2026, 9, 10)
CONCERNS = ("money", "work", "love", "people", "dir", "health")
LENS = {"money": "haengsu", "work": "hunjang", "love": "wolha",
        "people": "hwagyeong", "dir": "nopa", "health": "yakcho"}

CHARTS = [
    (1988, 5, 17, 15, 55, "F"),
    (1995, 11, 2, 8, 10, "M"),
    (1979, 3, 28, 6, 40, "F"),
    (2001, 6, 18, 21, 5, "M"),
]


def _ask():
    return json.loads((ROOT / "seed" / "topic.json").read_text(
        encoding="utf-8"))["ASK"]


def _feats(y, m, d, h, mi, sx, known=True):
    return build_features(build_chart(y, m, d, h, mi, sx, known, "서울"),
                          as_of=AS_OF)


def _sub(concern, choice):
    q2 = list((_ask()[concern].get("options2") or {}).keys())
    return dict({"choice": choice}, **({"choice2": q2[0]} if q2 else {}))


def _cuts(f, concern, extras=None):
    r = build_report(f, "s", LENS[concern], "all", concern, None, extras)
    return {c["id"]: TAG.sub("", c["html"]) for c in r["cuts"]}


# ① ───────────────────────────────────────────────────────
def test_답_안_하면_예전과_같다():
    """새 인자에 아무것도 안 넘기면 예전 함수와 **글자 하나 안 다르다**."""
    for spec in CHARTS:
        f = _feats(*spec)
        for c in CONCERNS:
            assert T.scale(f, c) == T.scale(f, c, None), c
            assert T.turn(f, c) == T.turn(f, c, None), c
            assert (P.read(f, c, limit=3)
                    == P.read(f, c, limit=3, focus=None)), c


def test_건너뛴_답은_답_안_한_것과_같다():
    """「잘 모르겠습니다」로 넘긴 것(choice "")은 판정도 순서도 안 바꾼다."""
    f = _feats(*CHARTS[0])
    for c in CONCERNS:
        assert T.scale(f, c, {"choice": ""}) == T.scale(f, c), c
        assert T.focus_pats(c, {"choice": ""}) is None, c


# ② ───────────────────────────────────────────────────────
def test_답이_여러_컷을_바꾼다():
    """
    답 하나가 유료 전부에서 **평균 두 컷 넘게** 바꾼다.

    전에는 한 컷(topic_ask)뿐이었습니다. 그건 물어 놓고 처방은 그대로라는
    뜻입니다. 몸은 세운 줄을 일부러 안 달아 조금 적습니다.
    """
    ask = _ask()
    changed = []
    for spec in CHARTS[:2]:
        f = _feats(*spec)
        for c in CONCERNS:
            base = _cuts(f, c)
            for ch in ask[c]["options"]:
                got = _cuts(f, c, {"topic": _sub(c, ch)})
                changed.append(sum(1 for k in set(base) | set(got)
                                   if base.get(k) != got.get(k)))
    avg = sum(changed) / len(changed)
    assert avg > 2.0, "답 하나가 평균 %.2f컷만 바꾸오 — 처방에 안 닿소" % avg


# ③ ───────────────────────────────────────────────────────
def test_조용한_칸을_끌어올리지_않는다():
    """
    소리 나는 칸이 다섯 넘게 있으면 **조용한 칸은 하나도 안 선다.**

    처음에는 답이 가리키면 조용한 칸이라도 세웠습니다. 그랬더니 돈 저울의
    최다 점유가 문턱 아래에서 4.29%로 뛰었습니다 — 조용한 칸은 누구에게나
    같은 말이 나오는 칸이라, 답한 사람일수록 남과 같은 글을 받았습니다.
    """
    ask = _ask()
    for spec in CHARTS:
        f = _feats(*spec)
        for c in CONCERNS:
            rows = T._ROWS[c](f)
            loud = {r["k"] for r in rows if not r["quiet"]}
            if len(loud) < T.MAX_ROWS:
                continue
            for ch in ask[c]["options"]:
                got = [r["k"] for r in T.scale(f, c, _sub(c, ch))]
                assert all(k in loud for k in got), (c, ch, got)


# ④ ───────────────────────────────────────────────────────
def test_몸에는_세운_줄을_안_단다():
    """건강을 해로 못 박으면 그건 예언이오. 몸 고민의 때에는 세운 줄이 없다."""
    ask = _ask()
    for spec in CHARTS:
        f = _feats(*spec)
        for ch in ask["health"]["options"]:
            t = T.turn(f, "health", _sub("health", ch))
            assert t is None or "세운" not in TAG.sub("", t["say"]), ch
            assert t is None or ":yr=" not in t["sid"], ch


def test_다른_고민에는_세운_줄이_붙는다():
    f = _feats(*CHARTS[0])
    t = T.turn(f, "love", _sub("love", "alone"))
    assert t and "세운" in TAG.sub("", t["say"])
    assert f.year_gz in TAG.sub("", t["say"])


# ⑤ ───────────────────────────────────────────────────────
def test_두번째_물음은_셈이_갈리는_자리에만():
    """
    일은 두 번째 물음을 둔다 — 자리·벌이·사람·버팀이 관성·재성·비겁·인성으로
    실제로 갈린다. 사랑은 안 둔다 — 「누가 끝냈소」는 여덟 글자가 모른다.
    """
    ask = _ask()
    assert ask["work"].get("options2"), "일에 두 번째 물음이 없소"
    assert not ask["love"].get("options2"), \
        "사랑에 두 번째 물음이 생겼소 — 여덟 글자가 가를 수 있는 것인지 먼저 보시오"
    f = _feats(*CHARTS[0])
    for k in ("rise", "pay", "people", "hold"):
        assert T._ask_hit(f, "work", "leak", k) in (True, False), k
    assert T._ask_hit(f, "work", "leak", "dunno") is None


def test_먼저_볼_자리는_있는_칸과_있는_짜임만():
    """표에 적힌 칸·짜임 이름이 엔진에 **실제로 있는** 것이어야 한다."""
    focus = json.loads((ROOT / "seed" / "topic.json").read_text(
        encoding="utf-8"))["SUB_FOCUS"]
    keys = {p["key"] for p in P.all_patterns()}
    for c, subs in focus.items():
        if c.startswith("_"):
            continue
        for ch, fx in subs.items():
            for k in fx.get("pats") or []:
                assert k in keys, "%s/%s 짜임 %r 이 엔진에 없소" % (c, ch, k)


# ⑥ ───────────────────────────────────────────────────────
def test_대운_해는_양력_생년에_나이를_더한다():
    """
    1·2월생도 대운 칸이 드는 해가 맞아야 한다.

    `saju_year`(입춘)에 `나이`(양력)를 더하면 1·2월생이 한 해 어긋납니다.
    1995-01-10 생에게 「2062년에 드오」(바른 해 2063)가 나갔습니다.
    """
    for y, m, d in ((1995, 1, 10), (1988, 1, 31), (1995, 11, 2)):
        ch = build_chart(y, m, d, 8, 10, "M", True, "서울")
        f = build_features(ch, as_of=AS_OF)
        assert f.birth_year == y
        grp = bank_mod.concern_group("money", f.sex)
        hit = next((x for x in f.daeun[f.daeun_now + 1:]
                    if GROUP_OF.get(x["ten_god"]) == grp), None)
        if hit:
            said = re.findall(r"(\d{4})년", TAG.sub("", T.turn(f, "money")["say"]))
            assert said and int(said[0]) == y + int(hit["start_age"]), (y, m, d)
        r = build_report(f, "s", "pungun", "one", "money", None)
        dn = TAG.sub("", next(c for c in r["cuts"] if c["id"] == "daeun_now")["html"])
        m2 = re.search(r"(\d+)세—(\d{4})년", dn)
        assert m2 and int(m2.group(2)) == y + int(m2.group(1)), (y, m, d)
