# -*- coding: utf-8 -*-
"""
고민축 — **물으면 그 자리를 세는가.** docs/20_고민축_설계.md

★ 손님이 짚은 것 (2026-09-06)

  "돈에 대해 물었는데 돈 관련 이야기는 전혀 구현이 안 되어 있어."

★ 무엇이 어긋났나

  09-05 에 고친 것은 「여섯 칸에서 **낱말**이 갈리는가」였습니다.
  훅 다섯 단과 리포트 한 컷이 고민마다 다른 낱말을 골라 썼습니다.
  그런데 **세는 값**은 그대로였습니다 —

      돈을 물어도  재성을 「개수 하나」로만 보고
      몸을 물어도  오행을 「많다·적다」로만 보고

  실무가 돈에서 세는 것은 갈래(정재·편재)·투출·궁위·재고·공망이고,
  그걸 한 줄도 안 세고 있었습니다.

★ 이 검사가 지키는 것

  ① 고민마다 **다른 것을 센다** (낱말만 다른 게 아니라)
  ② 조건이 안 맞으면 **안 낸다** (바넘 금지)
  ③ 때는 **달력**이지 예언이 아니다
  ④ 넉 자는 **축 둘만** — 넷을 다 말하면 성격검사다
  ⑤ 물음은 고를 것만, 답은 저장하지 않는다
  ⑥ 표는 하오체 한 벌 · 호칭 「그대」 한 벌
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import guard                            # noqa: E402
from engine import pattern as pattern_mod           # noqa: E402
from engine import topic as topic_mod               # noqa: E402
from engine.bank import build_hook                  # noqa: E402
from engine.calendar import build_chart             # noqa: E402
from engine.features import build_features          # noqa: E402
from engine.report import build_report, _plain      # noqa: E402

CONCERNS = topic_mod.CONCERNS
CHARTS = [(1997, 3, 22, 14, 10, "F"), (1985, 11, 3, 7, 40, "M"),
          (1972, 9, 9, 3, 25, "M"), (2001, 6, 1, 21, 5, "F")]


@pytest.fixture(scope="module")
def people():
    return [build_features(build_chart(y, m, d, h, mi, sx, True, "서울"))
            for y, m, d, h, mi, sx in CHARTS]


def _flat(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html or "")).strip()


def _scale_text(f, concern: str) -> str:
    return " ".join(r["say"] for r in topic_mod.scale(f, concern))


# ══════════════════════════════════════════════════════════
# ① 고민마다 다른 것을 센다
# ══════════════════════════════════════════════════════════
def test_여섯_칸이_서로_다른_것을_센다(people):
    """같은 사람인데 여섯 칸의 저울이 겹치면 「다 똑같아」가 맞습니다."""
    for f in people:
        seen = {}
        for c in CONCERNS:
            body = _flat(_scale_text(f, c))
            assert body, "%s 에서 저울이 비었소" % c
            assert body not in seen, (
                "%s 와 %s 의 저울이 글자 그대로 같소" % (c, seen[body]))
            seen[body] = c


def test_돈은_재성을_갈래까지_센다(people):
    """「재성 1개」가 아니라 정재·편재·투출·궁위까지 봅니다."""
    for f in people:
        keys = [r["k"] for r in topic_mod.scale(f, "money")]
        assert "hold" in keys, "쥐는 자리를 안 세고 있소"
        assert "lift" in keys, "드는 힘을 안 세고 있소"
        if f.jae:
            assert "show" in keys, "투출을 안 보고 있소"


def test_몸은_장부를_인용하되_단정하지_않는다(people):
    """옛 표가 어디에 붙여 읽었는지는 사실이오. 진단은 금지요."""
    for f in people:
        body = _flat(_scale_text(f, "health"))
        assert "옛 표는" in body, "인용 없이 장부를 말하고 있소"
        for word in ("진단", "치료", "처방", "완치", "낫소"):
            assert word not in body, "몸 축에서 %s 가 나왔소" % word


def test_저울은_다섯_칸을_안_넘는다(people):
    for f in people:
        for c in CONCERNS:
            rows = topic_mod.scale(f, c)
            assert 1 <= len(rows) <= topic_mod.MAX_ROWS, (c, len(rows))


def test_저울의_근거에는_센_수가_있다(people):
    """근거는 **틀릴 수 있는 말**이라야 하오. 손님이 세면 같은 수요."""
    for f in people:
        for c in CONCERNS:
            for r in topic_mod.scale(f, c):
                assert any(ch.isdigit() for ch in r["ev"]), (c, r["k"], r["ev"])


def test_내부_척도가_새지_않는다(people):
    """`f.elements` 는 가중치를 더한 분기표요. 밖으로 안 내오."""
    for f in people:
        for c in CONCERNS:
            for r in topic_mod.scale(f, c):
                assert not re.search(r"\d+\.\d", r["ev"] + _flat(r["say"])), (
                    c, r["k"], r["ev"])


# ══════════════════════════════════════════════════════════
# ② 조건이 안 맞으면 안 낸다
# ══════════════════════════════════════════════════════════
def test_짜임은_조건이_맞을_때만_나온다(people):
    """억지로 붙이면 누구에게나 맞는 말이 되어 바넘이 되오."""
    table = {p["key"]: p for p in pattern_mod.all_patterns()}
    for f in people:
        for c in CONCERNS:
            for got in pattern_mod.read(f, c, limit=99):
                spec = table[got["key"]]
                assert spec["test"](f), "%s 가 조건 없이 나왔소" % got["key"]
                assert c in spec["at"], "%s 는 %s 자리가 아니오" % (got["key"], c)


def test_돈_짜임이_넷보다_많다():
    """군겁쟁재·재다신약·식상생재·재성없음 넷뿐이던 자리요."""
    money = [p for p in pattern_mod.all_patterns() if "money" in p["at"]]
    assert len(money) >= 10, "돈에 걸리는 짜임이 %d개뿐이오" % len(money)


def test_격은_열_가지_안에서만_선다(people):
    """
    격은 **월지에서 무엇으로 서는가**를 한 낱말로 잡는 자리요.
    비견격·겁재격은 격 이름으로 안 씁니다 — 건록격·양인격으로 부릅니다.
    """
    ok = {"건록격", "양인격", "정관격", "편관격", "식신격", "상관격",
          "정재격", "편재격", "정인격", "편인격"}
    import random
    rng = random.Random(20260906)
    seen = set()
    for _ in range(60):
        f = build_features(build_chart(
            rng.randint(1940, 2010), rng.randint(1, 12), rng.randint(1, 28),
            rng.randint(0, 23), 0, rng.choice("FM"), True))
        g = topic_mod.gyeok(f)
        assert g in ok, "모르는 격: %s" % g
        seen.add(g)
    assert len(seen) >= 6, "격이 %d가지밖에 안 나왔소 — 판정이 굳었소" % len(seen)


def test_형과_무리는_지지로만_판정한다(people):
    """형·삼합·방합은 표와 지지를 맞춰 보면 끝이오. 지어내지 않소."""
    for f in people:
        hy = topic_mod.hyeong(f)
        assert hy in ("", "삼형", "상형", "자형", "반형"), hy
        kind, el = topic_mod.hap_group(f)
        assert kind in ("", "삼합", "방합", "반합"), kind
        if kind:
            assert el in ("목", "화", "토", "금", "수"), el
        # 걸렸다면 그 지지가 실제로 명식에 있어야 하오
        jis = [p["ji"] for p in f.pillars]
        for j in topic_mod.hyeong_at(f):
            assert j in jis, j


def test_나머지_넷도_다섯_칸을_채운다(people):
    """
    돈·몸만 깊고 나머지가 얕으면 「다 똑같아」가 다시 돌아오오.
    """
    import random
    rng = random.Random(2026)
    thin = []
    for _ in range(40):
        f = build_features(build_chart(
            rng.randint(1950, 2008), rng.randint(1, 12), rng.randint(1, 28),
            rng.randint(0, 23), 0, rng.choice("FM"), True))
        for c in ("work", "love", "people", "dir"):
            if len(topic_mod.scale(f, c)) < 4:
                thin.append((c, len(topic_mod.scale(f, c))))
    # 성별을 안 적은 사람의 사랑만 예외요 — 지어내지 않고 비웁니다
    assert not thin, "칸이 넷도 안 되는 자리: %s" % thin[:5]


# ══════════════════════════════════════════════════════════
# ③ 때는 달력이다
# ══════════════════════════════════════════════════════════
def test_때는_나이와_해를_대되_사건을_말하지_않는다(people):
    for f in people:
        for c in CONCERNS:
            t = topic_mod.turn(f, c)
            if t is None:
                continue
            body = _flat(t["say"])
            assert any(ch.isdigit() for ch in body), "때에 수가 없소: %s" % body
            for word in ("돈이 들어오오", "성공하", "실패하", "사시오", "파시오"):
                assert word not in body, "때가 사건을 말했소: %s" % word
            ok, hits = guard.check(body)
            assert ok, hits


# ══════════════════════════════════════════════════════════
# ④ 넉 자는 축 둘만
# ══════════════════════════════════════════════════════════
def test_얼굴은_축_둘만_말한다(people):
    """넷을 다 말하면 그건 성격검사지 사주가 아니오."""
    axes = topic_mod.table()["AXIS_OF"]
    for f in people:
        for c in CONCERNS:
            fc = topic_mod.face(f, c, "ENFP")
            assert fc, c
            assert len(axes[c]) == 2, c
            # 그 두 축의 글자만 나옵니다
            letters = fc["sid"].split(":")[2]
            assert len(letters) == 2, fc["sid"]


def test_넉_자를_안_적어도_그_자리가_비지_않는다(people):
    """안 적은 사람에게 침묵하면 45%가 그 자리를 잃소."""
    for f in people:
        fc = topic_mod.face(f, "money", None)
        assert fc and not fc["from_input"]
        assert "안 적으셨소" in _flat(fc["say"])


def test_어긋나면_고민의_말로_옮긴다(people):
    """「J인데 글자는 P요」 가 아니라 「예산은 늘 서고…」 라야 하오."""
    found = False
    for f in people:
        for a4 in ("ENTJ", "ISFP", "INTP", "ESFJ"):
            fc = topic_mod.face(f, "money", a4)
            if "헌데 여덟 글자는" in _flat(fc["say"]):
                found = True
                body = _flat(fc["say"])
                assert ("돈" in body or "값" in body or "예산" in body
                        or "벌" in body), body
    assert found, "어긋난 자리를 한 번도 못 만들었소"


def test_얼굴은_뽑은_셈을_같이_낸다(people):
    """축이 무엇을 세어 나왔는지 안 대면 그건 근거가 아니라 선언이오."""
    for f in people:
        body = _flat(topic_mod.face(f, "work", None)["say"])
        assert "힘이" in body and ("하나" in body or "둘" in body
                                  or "셋" in body or "넷" in body
                                  or "없음" in body), body


# ══════════════════════════════════════════════════════════
# ⑤ 물음
# ══════════════════════════════════════════════════════════
def test_물음은_고를_것만_낸다():
    for c in CONCERNS:
        spec = topic_mod.ask_spec(c)
        if spec is None:          # 사랑은 상대·만남 물음이 따로 있소
            continue
        assert spec["options"], c
        assert all(o["id"] and o["label"] for o in spec["options"]), c


def test_목록_밖은_거절한다(people):
    with pytest.raises(topic_mod.TopicInputError):
        topic_mod.ask_cut(people[0], "money", {"choice": "없는것"})


def test_모르겠소는_판정하지_않는다(people):
    """그렇소·아니오 둘만 두면 거짓 답이 공감률을 오염시키오."""
    cut = topic_mod.ask_cut(people[0], "money",
                            {"choice": "pay", "choice2": "dunno"})
    assert cut["statement_id"].endswith("u"), cut["statement_id"]
    assert "판정 안 함" in cut["source"]


def test_물음의_답이_리포트에_컷으로_선다(people):
    rep = build_report(people[0], "cid", "pungun", "one", "money", None,
                       {"topic": {"choice": "biz", "choice2": "people"}})
    ids = [c["id"] for c in rep["cuts"]]
    assert "topic_ask" in ids, ids


def test_틀린_답이_리포트를_안_죽인다(people):
    """값을 치른 사람이오. 그 컷만 접고 무엇이 틀렸는지 말하오."""
    rep = build_report(people[0], "cid", "pungun", "one", "money", None,
                       {"topic": {"choice": "말도_안_되는_것"}})
    assert rep["cuts"], "리포트가 통째로 죽었소"
    assert rep["extra_error"], "무엇이 틀렸는지 말하지 않았소"


def test_안_물었으면_무엇을_묻는지_알려준다(people):
    rep = build_report(people[0], "cid", "pungun", "one", "money", None)
    assert rep["asks"] and rep["asks"]["id"] == "money"
    rep2 = build_report(people[0], "cid", "pungun", "one", "money", None,
                        {"topic": {"choice": "biz"}})
    assert rep2["asks"] is None, "답했는데 또 묻고 있소"


# ══════════════════════════════════════════════════════════
# 리포트·훅에 실제로 서는가
# ══════════════════════════════════════════════════════════
def test_리포트에_고민_컷이_선다(people):
    for f in people:
        for c in CONCERNS:
            rep = build_report(f, "cid", "pungun", "one", c, None)
            ids = [x["id"] for x in rep["cuts"]]
            for want in ("concern", "concern_scale", "concern_turn",
                         "concern_face"):
                assert want in ids, "%s 에 %s 가 없소 — %s" % (c, want, ids)


def test_무료에는_본문이_안_내려간다(people):
    """잠긴 컷은 블러가 아니라 **서버가 안 주는** 것이오."""
    rep = build_report(people[0], "cid", "pungun", "free", "money", None)
    ids = [x["id"] for x in rep["cuts"]]
    locked = [x["id"] for x in rep["locked"]]
    for cid in ("concern_scale", "concern_turn", "concern_face"):
        assert cid not in ids, "%s 가 무료로 나갔소" % cid
        assert cid in locked, "%s 가 잠긴 목록에도 없소" % cid


def test_훅_마감에_저울_한_줄이_선다(people):
    """값을 치르기 전에도 세고 있다는 것이 보여야 하오."""
    for f in people:
        for c in CONCERNS:
            segs = build_hook(f, c, axis4=None)
            end = [s for s in segs if s["stage"] == "3"][0]
            body = _flat(end["html"])
            assert "셈은 값을 치르기 전에도 하오" in body, c
            assert any(ch.isdigit() for ch in body), c


def test_훅_마감의_셈이_고민마다_갈린다(people):
    for f in people:
        seen = set()
        for c in CONCERNS:
            segs = build_hook(f, c, axis4=None)
            end = [s for s in segs if s["stage"] == "3"][0]
            seen.add(end["statement_id"])
        assert len(seen) == len(CONCERNS), "마감이 여섯 칸에서 %d가지요" % len(seen)


# ══════════════════════════════════════════════════════════
# ⑥ 표 자체 — 말투 · 가드 · 빠진 갈래
# ══════════════════════════════════════════════════════════
def _table_strings():
    raw = json.loads((ROOT / "seed" / "topic.json").read_text("utf-8"))

    def walk(node, path=""):
        if isinstance(node, dict):
            for k, v in node.items():
                yield from walk(v, path + "/" + str(k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from walk(v, "%s/%d" % (path, i))
        elif isinstance(node, str):
            yield path, node

    return [(p, s) for p, s in walk(raw) if not p.startswith("/_")]


def test_표가_가드를_지난다():
    for path, text in _table_strings():
        ok, hits = guard.check(text)
        assert ok, "%s — %s" % (path, hits)


def test_표는_하오체_한_벌이다():
    """
    한다체·해요체로 쓰면 `voice.speak` 가 손댈 자리가 없어, 그 문장만
    스무 명에게 똑같이 나가오.
    """
    bad = re.compile(r"(에요|예요|해요|네요|습니다|입니다|합니다)[.!?\"']")
    hanta = re.compile(r"(?<![가-힣])(한다|이다|했다|된다|간다)[.!?]")
    for path, text in _table_strings():
        assert not bad.search(text), "%s — 다른 말투가 섞였소: %s" % (path, text[:40])
        assert not hanta.search(text), "%s — 한다체요: %s" % (path, text[:40])


def test_호칭은_그대_한_벌이다():
    for path, text in _table_strings():
        for w in ("자네", "아저씨", "당신", "너는"):
            assert w not in text, "%s — 호칭이 섞였소(%s)" % (path, w)


def test_모든_갈래에_문장이_있다(people):
    """
    표에 없는 갈래가 나오면 **터집니다.** 조용히 빈칸을 두지 않소 —
    여기서 잡히면 손님 화면에서 안 잡히오.
    """
    import random
    rng = random.Random(20260906)
    for _ in range(120):
        f = build_features(build_chart(
            rng.randint(1930, 2015), rng.randint(1, 12), rng.randint(1, 28),
            rng.randint(0, 23), rng.randint(0, 59), rng.choice("FM"),
            rng.random() > 0.15))
        for c in CONCERNS:
            rows = topic_mod.scale(f, c)          # 갈래가 없으면 TopicError
            assert rows
            topic_mod.turn(f, c)
            topic_mod.face(f, c, rng.choice([None, "INFJ", "ESTP"]))


def test_고민_컷의_글이_가드를_지난다(people):
    for f in people:
        for c in CONCERNS:
            rep = build_report(f, "cid", "hunjang", "all", c, "INFP")
            for cut in rep["cuts"]:
                ok, hits = guard.check(_plain(cut["html"]))
                assert ok, "%s / %s — %s" % (c, cut["id"], hits)
