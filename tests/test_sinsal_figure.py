"""
신살 인물 — 엔진이 내는 신살과 화면에 그리는 인물이 어긋나지 않는가,
그리고 신화의 어법이 예언의 어법으로 미끄러지지 않는가.

docs/16_신살인물_에셋발주서.md
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from engine import guard, sinsal

ROOT = Path(__file__).resolve().parents[1]
FIG_TS = ROOT / "apps" / "web" / "lib" / "sinsalFigures.ts"
COMP = ROOT / "apps" / "web" / "components" / "scene" / "SinsalFigure.tsx"


def figures() -> dict:
    """TS 파일에서 인물 항목을 읽는다 (그림 정보는 클라이언트에 있다)."""
    src = FIG_TS.read_text(encoding="utf-8")
    body = src[src.index("export const FIGURES"):]
    out = {}
    for m in re.finditer(
            r"(\w+):\s*\{\s*key:\s*\"(\w+)\",\s*title:\s*\"([^\"]+)\",\s*"
            r"who:\s*\"([^\"]+)\",\s*beside:\s*((?:\"[^\"]*\"\s*\+?\s*)+),",
            body):
        key = m.group(2)
        beside = " ".join(re.findall(r'"([^"]*)"', m.group(5)))
        out[key] = {"prop_name": m.group(1), "title": m.group(3),
                    "who": m.group(4), "beside": beside}
    return out


ALL_KEYS = [
    "cheoneul", "taegeuk", "munchang", "geumyeo", "amrok",
    "yangin", "baekho", "wonjin",
    "dohwa", "yeokma", "hwagae", "gwaegang", "gongmang",
]


# ══════════════════════════════════════════════════════════
# 엔진 ↔ 그림 데이터가 맞물리는가
# ══════════════════════════════════════════════════════════
def test_figure_file_parses():
    f = figures()
    assert len(f) == len(ALL_KEYS), sorted(f)


@pytest.mark.parametrize("key", ALL_KEYS)
def test_every_sinsal_has_a_figure(key):
    f = figures()
    assert key in f, "%s 에 인물이 없습니다 — 화면에 이름만 뜹니다" % key
    assert f[key]["prop_name"] == key
    assert f[key]["title"] and f[key]["beside"]


def test_engine_keys_and_figure_keys_match():
    """엔진이 낼 수 있는 신살 key 가 전부 그림에 있어야 한다."""
    import random
    from engine.calendar import build_chart

    rnd = random.Random(9)
    seen = set()
    for _ in range(600):
        c = build_chart(rnd.randint(1930, 2060), rnd.randint(1, 12),
                        rnd.randint(1, 28), rnd.randint(0, 23), 0,
                        rnd.choice("FM"))
        seen |= {s["key"] for s in sinsal.find(c)}
    missing = seen - set(figures())
    assert not missing, "그림 없는 신살: %s" % sorted(missing)


def test_summary_exposes_the_figure_key():
    from engine.calendar import build_chart
    from engine.features import build_features
    from engine.summary import build_summary

    f = build_features(build_chart(1993, 5, 15, 10, 20, "F"))
    sm = build_summary(None, f, "love")
    assert sm["sinsal"], "이 명식에는 신살이 있어야 합니다"
    for s in sm["sinsal"]:
        assert s["key"] in figures()


# ══════════════════════════════════════════════════════════
# 신화의 어법인가, 예언의 어법인가
# ══════════════════════════════════════════════════════════
BANNED = ["반드시", "보장", "틀림없", "확실히", "적중", "지켜준다", "지켜줍니다",
          "생깁니다", "일어납니다", "됩니다"]


@pytest.mark.parametrize("key", ALL_KEYS)
def test_figure_copy_does_not_predict(key):
    beside = figures()[key]["beside"]
    for b in BANNED:
        assert b not in beside, "%s: '%s' 는 단정입니다 — %s" % (key, b, beside)


@pytest.mark.parametrize("key", ALL_KEYS)
def test_figure_copy_passes_guard(key):
    f = figures()[key]
    ok, hits = guard.check(f["beside"] + " " + f["title"] + " " + f["who"])
    assert ok, (key, hits)


def test_figure_copy_uses_the_traditional_framing():
    """단정 대신 '옛사람들이 그렇게 그렸다' 는 어법이 실제로 쓰이는가."""
    joined = " ".join(v["beside"] for v in figures().values())
    marks = ["그렸소", "했소", "읽는", "썼소", "보던", "라 했소"]
    assert sum(joined.count(m) for m in marks) >= 8


# ══════════════════════════════════════════════════════════
# 특히 조심할 셋 — docs/16 §3
# ══════════════════════════════════════════════════════════
def test_dohwa_is_not_sexualised():
    beside = figures()["dohwa"]["beside"]
    for banned in ["유혹", "색기", "바람", "이성이 꼬", "몸"]:
        assert banned not in beside, beside
    assert "매력" in beside or "눈이 모이" in beside


def test_baekho_does_not_foretell_harm():
    beside = figures()["baekho"]["beside"]
    for banned in ["사고", "다친", "수술", "피를", "죽"]:
        assert banned not in beside, beside
    assert "쓰지 않소" in beside or "뜻으로 쓰지" in beside


def test_gongmang_draws_no_person():
    """공망은 사람을 그리지 않는다. 그리면 뜻이 반대가 된다."""
    fig = figures()["gongmang"]
    assert "빈 자리" in fig["title"]
    src = FIG_TS.read_text(encoding="utf-8")
    block = src[src.index("gongmang:"):]
    block = block[:block.index("};")]
    assert 'aura: "absent"' in block
    assert "human: false" in block
    # 컴포넌트가 absent 를 사람 없이 그리는가
    comp = COMP.read_text(encoding="utf-8")
    assert 'f.aura === "absent"' in comp
    assert "아무도 앉지 않았다" in comp


# ══════════════════════════════════════════════════════════
# 접근성 · 에셋 폴백
# ══════════════════════════════════════════════════════════
def test_component_respects_reduced_motion():
    comp = COMP.read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in comp
    css = (ROOT / "apps" / "web" / "styles" / "tokens.css").read_text(encoding="utf-8")
    block = css[css.index(".sfig {"):]
    assert "prefers-reduced-motion" in block
    assert "animation: none !important" in block


def test_component_falls_back_to_svg_without_assets():
    comp = COMP.read_text(encoding="utf-8")
    assert "/sinsal/${sinsalKey}/poster.jpg" in comp
    assert "clip.webm" in comp and "clip.mp4" in comp
    assert "Silhouette" in comp


def test_figure_has_an_accessible_label():
    comp = COMP.read_text(encoding="utf-8")
    assert 'role="img"' in comp
    assert "aria-label" in comp
