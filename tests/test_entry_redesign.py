"""Entry content and all-character free/paid boundaries, using real chart calculations."""
import html
import json
import re
from pathlib import Path

import pytest

from engine import entry_hook, guard, reading_offer
from engine.calendar import build_chart
from engine.features import build_features
from engine.report import build_report

LENSES = json.loads((Path(__file__).resolve().parents[1] / "seed/lenses.json").read_text("utf-8"))


def _plain(markup: str) -> str:
    return re.sub("<[^>]+>", "", html.unescape(markup or ""))


@pytest.fixture(scope="module", params=[True, False])
def features(request):
    known = request.param
    return build_features(build_chart(1993, 5, 15, 10 if known else None, 20 if known else None, "F", hour_known=known))


@pytest.mark.parametrize("concern", entry_hook.CONCERNS)
def test_first_reading_has_complete_value_without_purchase(features, concern):
    chapters = entry_hook.build(features, concern)
    # 네 장이 **딛는 축이 다릅니다** — 셈 · 장면 · 때 · 처방 (docs/45 §6-1).
    assert [c["stage"] for c in chapters] == ["0", "2", "3", "4"]
    assert [c["response_mode"] for c in chapters] == [
        "continue", "experience", "continue", "continue"]
    assert not guard.scan(chapters)
    assert all(c["html"] and c["source"] and c["nav"] for c in chapters)
    assert entry_hook.CONCERNS[concern][2] in chapters[-1]["html"]
    if not features.hour_known:
        # 첫 출현에는 괄호 풀이가 끼어듭니다 — 태그를 걷고 봅니다.
        assert all("시주" in _plain(c["source"]) and "셈에서 뺐소" in c["source"]
                   for c in chapters)


@pytest.mark.parametrize("concern", entry_hook.CONCERNS)
def test_first_reading_counts_instead_of_asking(features, concern):
    """앞 판은 본문에 아라비아 숫자가 0개였고 장면이 전부 물음표였습니다."""
    chapters = entry_hook.build(features, concern)
    body = " ".join(re.sub("<[^>]+>", "", html.unescape(c["html"]))
                    for c in chapters)
    assert re.search(r"\d", body), "셀 수 있는 값이 한 자도 없소"
    assert f"{features.age}살" in body, "지금 나이를 안 댔소"
    # 해석을 스스로 깎는 말. 아니라고 답할 자리는 버튼이 따로 있습니다.
    for hedge in ("다르다면 다르다고", "내려놓아도 되오", "증명하는 값은 아니오"):
        assert hedge not in body


def test_evidence_differs_per_chapter(features):
    """같은 근거 413자를 세 장에 세 번 붙이던 자리입니다."""
    chapters = entry_hook.build(features, "work")
    assert len({c["source"] for c in chapters}) == len(chapters)


def test_tied_note_stays_out_of_the_body(features):
    """동률은 43%에서 참이오 — 본문에서 읽히면 첫 해석이 스스로를 깎소."""
    for concern in entry_hook.CONCERNS:
        for c in entry_hook.build(features, concern):
            assert "여러 관점 중" not in c["html"]
            assert "하나요" not in re.sub("<[^>]+>", "", html.unescape(c["html"]))


def test_every_scene_is_an_assertion():
    """서른 장면이 전부 「…하오?」 였습니다. 묻는 자리는 버튼입니다."""
    for group in entry_hook.SCENES.values():
        for scene, strength, boundary in group.values():
            assert not scene.rstrip().endswith("?")
            assert strength and boundary


def test_hour_unknown_drops_the_hour_palace(features):
    """시각을 모르면 궁위에서도 시주를 뺍니다 — 셈에서만 빼면 반만 뺀 것이오."""
    palace = entry_hook._palace_now(features)
    if palace and not features.hour_known:
        assert palace["pillar"] != "시주"


def test_concerns_are_not_just_renamed(features):
    """고민은 **장면부터** 갈립니다. 셈은 안 갈립니다.

    명식은 무엇을 물었든 같은 여덟 글자요 — 셈 장부에 고민을 들이면
    `test_concern_spread` 에 걸립니다 (CLAUDE.md).
    """
    ledger = {entry_hook.build(features, c)[0]["html"] for c in entry_hook.CONCERNS}
    assert len(ledger) == 1, "셈 장부가 고민 따라 갈렸소"
    for index in (1, 3):
        got = {entry_hook.build(features, c)[index]["html"]
               for c in entry_hook.CONCERNS}
        assert len(got) == 6, f"{index}번째 장이 고민 따라 안 갈리오"


def test_rejection_changes_later_chapters_not_the_seen_ones(features):
    """본 장은 그대로 두고 **뒤 장의 축**을 바꿉니다 (docs/45 §6-1).

    읽은 글이 몰래 갈리면 손님은 자기가 무엇에 아니라고 했는지 알 수
    없습니다. 그렇다고 그대로 밀고 가면 그 순간 이게 녹음인 줄 압니다.
    """
    before = entry_hook.build(features, "work")
    after = entry_hook.build(features, "work", misses=1)
    assert before[0] == after[0]          # 셈 — 아니라고 할 수 없는 자리
    assert before[1] == after[1]          # 방금 아니라고 답한 장면
    assert before[2]["html"] != after[2]["html"]
    assert before[3]["html"] != after[3]["html"]
    assert "성격을 정하지 않겠소" in after[2]["html"]


def test_alias_cannot_inject_markup(features):
    chapters = entry_hook.build(features, "work", name='<img src=x onerror="alert(1)">')
    # 별칭은 장면 장(두 번째)에서 부릅니다.
    assert "<img" not in chapters[1]["html"]
    assert "&lt;img" in chapters[1]["html"]


@pytest.mark.parametrize("lens", LENSES, ids=lambda row: row["id"])
def test_every_character_has_a_real_free_and_paid_contract(features, lens):
    concern = (lens.get("concerns") or ["work"])[0]
    free = build_report(features, "audit", lens["id"], "free", concern)
    offer = free["reading_offer"]
    assert offer["question"] == reading_offer.QUESTIONS[lens["id"]]
    if not lens["price"]:
        assert offer["free_only"] and offer["core_id"] is None and not free["locked"]
        return
    assert 1 < len(offer["free_ids"]) <= 3
    assert all(any(c["id"] == cid and c["html"] for c in free["cuts"]) for cid in offer["free_ids"])
    assert offer["core_id"] == f"lc_{lens['id']}_ask2"
    core = next(c for c in free["locked"] if c["id"] == offer["core_id"])
    assert "html" not in core
    assert core["need_tier"] == "one"
    assert all("html" not in c for c in free["locked"])
    paid = build_report(features, "audit", lens["id"], "one", concern)
    paid_core = next(c for c in paid["cuts"] if c["id"] == offer["core_id"])
    assert len(paid_core["html"]) > len(core["teaser"])
    assert set(offer["free_ids"]) <= {c["id"] for c in paid["cuts"]}
    assert paid["reading_offer"]["core_id"] is None


def test_schema_defaults_preserve_old_clients():
    from schemas.api import HookRequest, ReportResponse
    assert HookRequest(chart_id="x", concern="work").edition == "classic"
    assert HookRequest(chart_id="x", concern="work", edition="entry2").edition == "entry2"
