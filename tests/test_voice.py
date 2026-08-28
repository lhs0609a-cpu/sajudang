"""
말투 — 캐릭터마다 다른 목소리인가.

★ 여기가 통째로 없었습니다.
  docs/07 은 스무 명의 말투를 이미 정해 놓았는데(은별 "…어긋나네요",
  홍매파 "…대봐", 훈장 "…골랐어", 노파 "…듣게", 연담 "…보겠습니다",
  청동자 "괜찮아요") **엔진이 그걸 무시하고 전부 하오체로 통일**해
  버렸습니다. 스무 명 중 열여섯이 똑같이 "그대" 라 부르고 어미도
  한 결이라, 두 사람을 이어 읽으면 중앙 56%가 글자 그대로 같은
  글이었습니다.
"""
from __future__ import annotations

import itertools
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

import pytest                                          # noqa: E402

from engine import lens as lens_mod                    # noqa: E402
from engine import voice as V                          # noqa: E402
from engine import guard                               # noqa: E402
from engine.calendar import build_chart                # noqa: E402
from engine.features import build_features             # noqa: E402
from engine.report import build_report, _plain         # noqa: E402


@pytest.fixture(scope="module")
def f():
    return build_features(build_chart(1997, 3, 22, 14, 10, "F", True, "서울"))


@pytest.fixture(scope="module")
def reports(f):
    return {l["id"]: build_report(f, "t", l["id"], "all", "love", "INFP")
            for l in lens_mod.released()}


# ══════════════════════════════════════════════════════════
# 어미 변환이 문장을 깨지 않는가
# ══════════════════════════════════════════════════════════
#
# ★ 불규칙 활용을 건드리면 한 글자 차이로 문장이 깨집니다.
#   「쉽소 → 쉬워요」(ㅂ), 「그렇소 → 그래요」(ㅎ), 「다르오 → 달라요」(르).
#   그래서 **어간을 그대로 두고 붙이기만 하는 어미**로만 짰습니다.
@pytest.mark.parametrize("word,want", [
    ("있소", {"hapsyo": "있습니다", "hage": "있네", "banmal": "있지", "haeyo": "있네요"}),
    ("하오", {"hapsyo": "합니다", "hage": "하네", "banmal": "하지", "haeyo": "하네요"}),
    ("쉽소", {"hapsyo": "쉽습니다", "hage": "쉽네", "banmal": "쉽지", "haeyo": "쉽네요"}),
    ("그렇소", {"hapsyo": "그렇습니다", "hage": "그렇네", "banmal": "그렇지", "haeyo": "그렇네요"}),
    ("다르오", {"hapsyo": "다릅니다", "hage": "다르네", "banmal": "다르지", "haeyo": "다르네요"}),
    ("것이오", {"hapsyo": "것입니다", "hage": "것이네", "banmal": "것이지", "haeyo": "것이네요"}),
    ("보겠소", {"hapsyo": "보겠습니다", "hage": "보겠네", "banmal": "보겠지", "haeyo": "보겠네요"}),
    ("않았소", {"hapsyo": "않았습니다", "hage": "않았네", "banmal": "않았지", "haeyo": "않았네요"}),
])
def test_endings_do_not_touch_the_stem(word, want):
    for v, expect in want.items():
        assert V._word(word, v) == expect, (word, v)
    assert V._word(word, V.HAO) == word, "하오체는 원문 그대로여야 합니다"


def test_the_informal_voices_drop_the_honorific(f):
    """
    ★ 「정하시지」는 반말이라면서 존대가 섞인 말입니다.
      반말·하게체는 '시' 를 뗍니다.
    """
    assert V._word("정하시오", V.BANMAL) == "정하지"
    assert V._word("정하시오", V.HAGE) == "정하게"
    assert V._word("정하시오", V.HAPSYO) == "정하십시오"
    assert V._word("정하시오", V.HAEYO) == "정하세요"


def test_tags_and_attributes_are_never_touched():
    """속성값에 손대면 화면이 깨집니다."""
    h = '<p class="tale" data-x="보오">여덟 글자가 <b>이렇소</b>.</p>'
    out = V.speak(h, V.HAPSYO)
    assert 'class="tale"' in out and 'data-x="보오"' in out
    assert "<b>이렇습니다</b>" in out


def test_the_word_geudaero_is_not_a_pronoun():
    """
    ★ 「그대로」는 호칭이 아닙니다. 한 글자 차이로 "자네로 도오" 가 됩니다.
    """
    assert V.address("여덟 글자가 그대로 도오.", "자네") == "여덟 글자가 그대로 도오."
    assert V.address("그대에게 필요한 건", "자네") == "자네에게 필요한 건"


# ══════════════════════════════════════════════════════════
# 스무 명이 실제로 다르게 말하는가
# ══════════════════════════════════════════════════════════
def test_every_character_has_a_voice():
    missing = [l["id"] for l in lens_mod.all_lenses()
               if lens_mod.view(l["id"]).get("voice") not in V.VOICES]
    assert not missing, missing


def test_more_than_one_voice_is_actually_used():
    used = {lens_mod.view(l["id"])["voice"] for l in lens_mod.released()}
    assert len(used) >= 4, ("말투가 %d 가지뿐입니다: %s" % (len(used), used))


def test_the_pronoun_matches_the_character(reports):
    """
    ★ 컷 여러 곳이 호칭을 "그대" 로 박아 두고 있었습니다. 관점에는
      자네·아저씨라고 적혀 있는데 본문은 전부 "그대에게" 였습니다.
    """
    other = re.compile(r"그대(?!로)")
    for lid, rep in reports.items():
        you = lens_mod.view(lid)["you"]
        if you == "그대":
            continue
        for c in rep["cuts"]:
            assert not other.search(_plain(c["html"])), (lid, c["id"])


def test_two_characters_no_longer_read_as_the_same_text(reports):
    """
    ★ 전에는 아무 두 사람을 나란히 놓으면 **중앙 56%** 가 글자 그대로
      같은 글이었습니다(최고 88.9%). 관점은 스무 개 다 다른데 목소리가
      하나여서입니다.
    """
    ids = sorted(reports)
    share = []
    for a, b in itertools.combinations(ids, 2):
        ta = {c["id"]: _plain(c["html"]) for c in reports[a]["cuts"]}
        tb = {c["id"]: _plain(c["html"]) for c in reports[b]["cuts"]}
        same = sum(len(v) for k, v in ta.items() if tb.get(k) == v)
        share.append(100 * same / sum(len(v) for v in ta.values()))
    assert statistics.median(share) < 20, (
        "두 사람이 중앙 %.1f%% 같은 글입니다" % statistics.median(share))


def test_the_voice_layer_never_slips_past_the_guard(reports):
    """어미를 바꿔도 금지어가 생기면 안 됩니다."""
    for lid, rep in reports.items():
        for c in rep["cuts"]:
            ok, hits = guard.check(_plain(c["html"]))
            assert ok, (lid, c["id"], hits)


def test_the_evidence_line_keeps_its_own_voice(reports):
    """
    ★ 근거는 캐릭터가 바꾸지 않습니다. 여덟 글자는 하나입니다 —
      말하는 순서와 어조만 다릅니다. (seed/lens_view.json 의 머리말)
    """
    base = {c["id"]: c["source"] for c in reports["pungun"]["cuts"]}
    for lid, rep in reports.items():
        for c in rep["cuts"]:
            if c["id"] in base and not c["id"].startswith("lc_"):
                assert c["source"] == base[c["id"]], (lid, c["id"])
