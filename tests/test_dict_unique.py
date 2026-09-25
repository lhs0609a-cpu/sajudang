# -*- coding: utf-8 -*-
"""
사주 사전 — 예순 장이 **한 장이 아닌가**, 그리고 지어낸 것이 없는가.

★ 이 검사가 지키는 것

  ① 계산은 이 집의 다른 자와 **같은 자**로 한다 (두 벌이 되면 리포트와
     사전이 다른 말을 합니다)
  ② 글은 틀 하나가 아니다 — 겹침이 **셈을 따라** 오른다
  ③ 자를 느슨하게 고치지 않았다 — 틀 하나로 만든 가짜 묶음은 여전히
     걸린다 (아래 `test_틀_하나면_자에_걸린다`)
  ④ 표가 없는 것은 안 낸다 (십이운성 · 십신 궁합표 따위)
  ⑤ 낱말 한가운데를 잇지 않는다

★ ③ 이 이 파일의 핵심입니다. 2026-09-24 에 문턱을 한 번 옮겼기 때문이오 —
  「어느 짝이든 35% 아래」에서 「사실이 안 겹치는 짝이 45% 아래 + 기울기」
  로. 옮긴 까닭은 `tools/dict_same.py` 머리말에 적혀 있고, 옮긴 자가 첫
  판(틀 하나)을 여전히 잡는지는 **여기서** 지킵니다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT))

from engine import constants as C                      # noqa: E402
from engine import dict as D                            # noqa: E402
from engine import guard, sinsal, terms                 # noqa: E402
from tools import dict_same as R                        # noqa: E402


@pytest.fixture(scope="module")
def pages():
    return [D.ilju_page(gz) for gz in D.sixty()]


@pytest.fixture(scope="module")
def measured(pages):
    return R.measure_pages(pages)


# ══════════════════════════════════════════════════════════
# ① 계산 — 같은 자로
# ══════════════════════════════════════════════════════════

def test_예순_갑자가_예순이고_겹치지_않는다():
    gz = D.sixty()
    assert len(gz) == 60 and len(set(gz)) == 60
    assert gz[0] == "甲子" and gz[-1] == "癸亥"


def test_일지_십신은_features_와_같은_자로_센다(pages):
    """지지 본기 = HIDDEN[ji][0][0]. 여기서 딴 자를 쓰면 두 벌이 됩니다."""
    for p in pages:
        f = p["facts"]
        bon = C.HIDDEN[f["ji"]][0][0]
        assert f["ji_hidden"] == bon
        assert f["ji_tengod"] == C.ten_god(bon, f["gan"])


def test_공망과_신살은_sinsal_표에서_받는다(pages):
    for p in pages:
        f = p["facts"]
        assert f["gongmang"] == sinsal.gongmang(f["gan"], f["ji"])
        assert f["samhap"] == sinsal.SAMHAP_OF[f["ji"]]
        assert f["wonjin"] == sinsal.WONJIN[f["ji"]]
        for m in f["marks"]:
            assert m in ("양인", "홍염", "괴강", "백호")
        if "괴강" in f["marks"]:
            assert f["gz"] in sinsal.GWAEGANG
        if "백호" in f["marks"]:
            assert f["gz"] in sinsal.BAEKHO


def test_인구는_표본에서_받고_순위는_한_자리에서_센다(pages):
    t = __import__("engine.rarity", fromlist=["table"]).table()
    ranks = sorted(p["facts"]["rank"] for p in pages)
    assert ranks == list(range(1, 61)), "순위가 예순 가지가 아니오"
    for p in pages:
        f = p["facts"]
        assert f["n"] == t["ilju"][f["gz"]]["n"]
        assert f["sample"] == t["sample"]


def test_없는_일주는_지어내지_않고_터뜨린다():
    for bad in ("甲丑", "乙子", "", "丙", "가나"):
        with pytest.raises(D.DictError):
            D.ilju_page(bad)


# ══════════════════════════════════════════════════════════
# ② 글이 틀 하나가 아니다
# ══════════════════════════════════════════════════════════

def test_짝_겹침_평균이_문턱_아래다(measured):
    assert measured["mean"] <= R.PAIR_MEAN_MAX, \
        "평균 %.1f%%" % (100 * measured["mean"])


def test_사실이_안_겹치는_짝은_닮지_않는다(measured):
    """틀이 하나인지 묻는 자리. 파생 사실이 0개 겹치는 짝이 닮으면 틀 탓이오."""
    assert measured["stranger_n"] >= 100, "남 짝이 너무 적어 재지 못하오"
    assert measured["stranger_worst"] <= R.STRANGER_MAX, \
        "남 짝 최악 %.1f%%" % (100 * measured["stranger_worst"])


def test_겹침이_셈을_따라_오른다(measured):
    assert R._slope_ok(measured["by"]), "겹침이 사실 수를 안 따르오 — 납작하오"


def test_이_장에만_있는_수가_넷_이상(measured):
    assert measured["own_min"] >= R.OWN_MIN, \
        "가장 적은 장이 %d개" % measured["own_min"]


def test_한_줄이_전부에_깔리지_않는다(measured):
    assert measured["top_share"] <= R.TOP_SHARE_MAX, \
        "%.2f%% — %s" % (100 * measured["top_share"], measured["top"][:50])


def test_센_값이_통째로_같은_장이_없다(measured):
    assert measured["dup_values"] == 0


# ══════════════════════════════════════════════════════════
# ③ 자가 느슨해지지 않았다
# ══════════════════════════════════════════════════════════

def test_틀_하나면_자에_걸린다():
    """
    첫 판처럼 **틀 하나에 값만 바꾼** 묶음을 지어 자에 댑니다.

    문턱을 옮긴 뒤에도 이것이 걸려야, 옮긴 것이 「재는 자리를 옮긴 것」이지
    「느슨하게 한 것」이 아닙니다.
    """
    fake = []
    for gz in D.sixty():
        f = D.ilju_facts(gz)
        html = (
            '<p>%s%s(%s)은 %s 일간이 %s 위에 앉은 자리요. 발밑 글자를 십신으로 '
            '셈하면 %s요. 일지는 여덟 글자에서 그대 곁자리라, 이 십신이 가장 '
            '가까운 데서 움직이오. 공망은 %s요. 옛사람은 이 두 글자를 비어 있는 '
            '자리로 읽었소. 이 일주로 태어난 사람은 1만 명에 %d명이오.</p>'
            % (f["gan_sound"], f["ji_sound"], gz,
               D.EL_WORD[f["gan_el"]], D.EL_WORD[f["ji_el"]],
               f["ji_tengod"], f["gongmang"], f["per10k"]))
        fake.append({"gz": gz, "html": html, "facts": f,
                     "own": [gz, f["ji_tengod"], str(f["per10k"])]})
    m = R.measure_pages(fake)
    assert m["mean"] > R.PAIR_MEAN_MAX, "틀 하나인데 평균이 통과하오"
    assert m["stranger_worst"] > R.STRANGER_MAX, "틀 하나인데 남 짝이 통과하오"
    assert m["own_min"] < R.OWN_MIN, "틀 하나인데 고유한 수가 통과하오"


# ══════════════════════════════════════════════════════════
# ④ 지어내지 않는다
# ══════════════════════════════════════════════════════════

#: 이 집이 표를 안 가진 것. 사전에 나오면 지어낸 것이오 (docs/44 §3 △).
NOT_OURS = ("십이운성", "장생", "제왕", "태지", "절지", "십이신살",
            "겁살", "천살", "지살", "납음", "공협", "당사주")


@pytest.mark.parametrize("gz", D.sixty())
def test_표가_없는_것은_안_낸다(gz):
    page = D.ilju_page(gz)
    body = page["html"] + page["title"] + page["lead"] + page["source"]
    for word in NOT_OURS:
        assert word not in body, "%s 에 %s 가 나오오 — 표가 없는 말이오" % (gz, word)


@pytest.mark.parametrize("gz", D.sixty())
def test_모든_장이_가드를_지난다(gz):
    page = D.ilju_page(gz)
    for text in (page["title"], page["lead"], page["source"],
                 R.plain(page["html"])):
        ok, hits = guard.check(text)
        assert ok, "%s: %s" % (gz, hits[:1])


@pytest.mark.parametrize("word", sorted(terms.MEANING))
def test_용어_항목도_가드를_지난다(word):
    page = D.term_page(word)
    ok, hits = guard.check(R.plain(page["html"]))
    assert ok, "%s: %s" % (word, hits[:1])


def test_그_해에_무슨_일이_생긴다고_말하지_않는다(pages):
    """바뀌는 때만 셉니다 — 사건을 적으면 점이 아니라 소설이오."""
    bad = re.compile(r"(생긴다|일어난다|하게 된다|될 것이오|하오리라|반드시)")
    for p in pages:
        hit = bad.search(R.plain(p["html"]))
        assert not hit, "%s: %s" % (p["gz"], hit.group(0))


# ══════════════════════════════════════════════════════════
# ⑤ 잇는 자리
# ══════════════════════════════════════════════════════════

def test_낱말_한가운데를_잇지_않는다():
    """`terms.link` 는 `gloss` 와 **같은 자**를 씁니다 (WORD_START)."""
    got = terms.link("아껴지지 않소. 따지지 마시오.", D.term_href)
    assert "<a" not in got, got


def test_이은_말은_한_장에_한_번이다(pages):
    for p in pages:
        for word in ("일간", "십신", "공망"):
            assert p["html"].count('>%s</a>' % word) <= 1, \
                "%s 에 %s 를 두 번 이었소" % (p["gz"], word)


def test_주소는_한_자리에서_온다(pages):
    src = (ROOT / "services" / "api" / "engine" / "dict.py").read_text("utf-8")
    assert src.count('BASE = "') == 1, "사전 주소가 두 벌이오"
    for p in pages:
        for href in re.findall(r'href="([^"]+)"', p["html"]):
            assert href.startswith(D.BASE + "/"), href


def test_안_연_말은_잇지_않는다():
    assert D.term_href("없는말") == ""
    # 낱말마다 장이 아니라 용어집 한 장의 앵커요 (docs/44 §2).
    assert D.term_href("공망") == D.BASE + "/용어#공망"


def test_형제_일주가_서로_이어진다(pages):
    """묶음 안을 돌아볼 길 — 없으면 잎이 고아가 되오."""
    for p in pages:
        f = p["facts"]
        for g in f["gan_kin"] + f["ji_kin"]:
            assert D.ilju_href(g) in p["html"], "%s 가 %s 를 안 잇소" % (f["gz"], g)
        assert D.ilju_href(f["gz"]) not in p["html"], "제 장을 제가 잇소"
