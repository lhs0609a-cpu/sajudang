"""
척추 — 이 사람을 한 줄로 세우는 자리 (engine/spine.py · seed/spine.json).

★ 지키는 것
  · 열 칸이 다 있고, 강점과 그림자가 짝으로 셋씩이다
  · 표의 모든 글이 가드를 그대로 통과한다 (고쳐 쓰이면 표가 틀린 것)
  · 흐름 세 단은 **셈**이다 — 글자와 자리를 짚는다
  · 넉 자를 적은 손님에게 「안 적으셨으니」 가 안 나간다 (2026-09-11)
"""
from datetime import date

from engine import guard, spine
from engine.calendar import build_chart
from engine.features import build_features
from engine.report import build_report

KEYS = [f"{a}>{b}" for a, b in spine.NEXT.items()] + \
       [f"{a}>끊김" for a in spine.NEXT]


def _f(y=1993, m=11, d=25, h=15, mi=50, sex="M", city="수원"):
    ch = build_chart(y, m, d, h, mi, sex, True, city)
    return build_features(ch, as_of=date(2026, 9, 11))


def test_열_칸이_다_있다():
    T = spine.table()
    assert sorted(T["spines"]) == sorted(KEYS)
    for k, e in T["spines"].items():
        assert len(e["strengths"]) == len(e["shadows"]) == 3, k
        assert len(e["contrast"]) == 2, k
        assert len(e["probes"]) == 3, k
        for p in e["probes"]:
            assert p["hit"] and all(0 <= i < len(p["opts"]) for i in p["hit"]), k
    assert set(T["strength"]) == {"신강", "중화", "신약"}
    assert set(T["empty"]) == set(spine.NEXT)


def test_표의_글이_가드를_통과한다():
    T = spine.table()
    texts = list(T["strength"].values()) + list(T["empty"].values())
    for e in T["spines"].values():
        texts += [e["line"], e["risk"], e["fit"]] + e["strengths"] + e["shadows"]
        texts += [c["most"] for c in e["contrast"]] + [c["you"] for c in e["contrast"]]
    for t in texts:
        ok, hits = guard.check(t)
        assert ok, (t, hits)


def test_흐름_세_단은_셈이다():
    f = _f()
    assert [p["gz"] for p in f.pillars] == ["癸酉", "癸亥", "庚戌", "甲申"]
    sp = spine.read(f)
    assert sp["key"] == "식상>재성"
    assert sp["pattern"].startswith("식상생재")
    # 庚 → 癸·癸·亥(년간·월간·월지) → 甲(시간)
    assert [c for c, _, _ in spine.seats(f, "식상")] == ["癸", "癸", "亥"]
    assert [s for _, s, _ in spine.seats(f, "재성")] == ["시간"]
    assert "金生水" in sp["chain_html"] and "水生木" in sp["chain_html"]
    # 굽히는 자리는 고리를 따라가다 처음 만나는 0 — 관성
    assert sp["empty"] == "관성"


def test_끊긴_자리는_두_번_말하지_않는다():
    # 흐름이 다음 자리에 안 닿은 사람 — 그 자리를 굽히는 자리로 또 말하면 안 된다
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    import population
    seen = 0
    for f in population.sample(400, share=0.15):
        if not spine.reaches(f):
            seen += 1
            assert spine.empty_group(f) != spine.NEXT[f.flow]
    assert seen


def test_넉_자를_적은_손님에게_안_적었다고_안_한다():
    f = _f()
    rep = build_report(f, "t", "baegun", "one", "work", "INTJ")
    body = "".join(c["html"] for c in rep["cuts"])
    assert "안 적으셨으니" not in body
    rep = build_report(f, "t", "baegun", "one", "work", None)
    body = "".join(c["html"] for c in rep["cuts"])
    assert "안 적으셨으니" in body


def test_庚은_한_가지로_부른다():
    f = _f()
    rep = build_report(f, "t", "baegun", "one", "work", "INTJ")
    body = "".join(c["html"] for c in rep["cuts"])
    assert "벼려진 쇠" not in body and "무른 쇠" not in body
