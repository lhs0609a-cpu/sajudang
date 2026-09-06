# -*- coding: utf-8 -*-
"""
스무 사람이 저마다 다르게 서 있는가.

★ 무엇이 틀려 있었나 (2026-09-06)

  이 집이 파는 것은 「같은 사주를 스무 사람이 저마다 다르게 읽는 것」
  입니다. 그런데 초상의 연출은 **한 벌을 스무 명이 나눠 쓰고**
  있었습니다.

    모션      "The character blinks once, slowly."      20명 중 서로 다른 것 1
    표정 짚는  "…He has just said something true…"      1
    표정 누그러 "…He is letting the viewer off…"          1
    첫 대면 인사  없음 — 코드에는 자리가 있는데 명령어가 없음

  스무 사람이 다 똑같이 눈을 깜빡이면 손님이 보는 것은 스무 사람이
  아니라 **옷을 갈아입은 한 사람**입니다. 게다가 그 한 벌은 「He」로
  쓰여 있어서 **여자 일곱**에게 그대로 나갔고, 열넷짜리 아이(청동자)도
  어른과 같은 몸짓을 했습니다.

★ 무엇을 지키나

  ① 스무 사람의 연출이 서로 다른가
  ② 그 사람의 성별과 대명사가 맞는가
  ③ 몸짓이 **그 사람이 이미 쥔 것**에서 나왔는가 (LOOK 과 겹치는가)
     — 지어내면 그림과 발주서가 갈립니다
  ④ 머리 잠금이 붙어 있는가 — 초상은 얼굴로 잘라 쓰므로(눈높이 37%를
     잡고 2.6배) 머리가 제자리를 뜨면 크롭이 깨집니다
  ⑤ 창이 그것을 **보여 주는가** — 묶음에만 있고 안 보이면 없는 것과
     같습니다. 실제로 표정 둘은 묶음에 있는데 창이 안 보여 줘서 한
     장도 안 들어왔습니다
"""
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
sys.path.insert(0, str(ROOT / "tools"))

import char_sheet as cs  # noqa: E402

BUNDLE = json.loads(
    (WEB / "public" / "asset-prompts.json").read_text(encoding="utf-8"))
LENSES = json.loads(
    (ROOT / "seed" / "lenses.json").read_text(encoding="utf-8"))
CHARS = BUNDLE.get("chars") or {}

# 사람을 가리키는 말이 아닌 흔한 낱말. 겹쳐도 「그 사람의 것」이 아닙니다.
STOP = {
    "with", "that", "from", "into", "over", "under", "like", "very",
    "korean", "hanbok", "hair", "eyes", "mouth", "face", "head", "hand",
    "hands", "robe", "light", "lighting", "small", "long", "dark", "pale",
    "young", "little", "loose", "single", "held", "back", "line", "lines",
    "faint", "soft", "high", "open", "down", "near", "half", "still",
    "man", "woman", "one", "two", "the", "and", "his", "her", "she",
}


def stage(lens_id):
    return cs.STAGE[lens_id]


def texts(lens_id):
    """그 사람에게 나가는 연출 글 전부."""
    e = CHARS[lens_id]
    return [e["motion"], e.get("greet") or ""] + [
        m["image"] for m in (e.get("moods") or {}).values()]


# ══════════════════════════════════════════════════════════
# ① 서로 다른가
# ══════════════════════════════════════════════════════════
def test_the_bundle_carries_all_twenty():
    missing = [l["id"] for l in LENSES if l["id"] not in CHARS]
    assert not missing, "묶음에 없는 사람: %s — python tools/char_sheet.py --json" % missing


def test_the_staging_table_covers_all_twenty():
    ids = {l["id"] for l in LENSES}
    assert set(cs.STAGE) == ids, (
        "연출 표와 사람이 안 맞소: 없는 사람 %s · 남는 사람 %s"
        % (sorted(ids - set(cs.STAGE)), sorted(set(cs.STAGE) - ids)))


@pytest.mark.parametrize("field", ["motion", "greet"])
def test_no_two_people_move_the_same_way(field):
    vals = [CHARS[l["id"]].get(field) for l in LENSES]
    assert all(vals), "%s 가 빈 사람이 있소" % field
    dup = {v for v in vals if vals.count(v) > 1}
    assert not dup, (
        "%s 를 여럿이 나눠 쓰오 (%d명이 %d가지) — 스무 사람이 아니라 "
        "옷 갈아입은 한 사람이 되오" % (field, len(vals), len(set(vals))))


@pytest.mark.parametrize("mood", ["cut", "soft"])
def test_no_two_people_wear_the_same_face(mood):
    vals = [(CHARS[l["id"]].get("moods") or {}).get(mood, {}).get("image")
            for l in LENSES]
    assert all(vals), "%s 표정이 빈 사람이 있소" % mood
    assert len(set(vals)) == len(vals), (
        "%s 표정을 여럿이 나눠 쓰오 (%d가지)" % (mood, len(set(vals))))


# ══════════════════════════════════════════════════════════
# ② 성별과 대명사
# ══════════════════════════════════════════════════════════
@pytest.mark.parametrize("lens", LENSES, ids=lambda l: l["id"])
def test_the_pronouns_match_the_person(lens):
    wrong = (r"\b(she|her|hers)\b" if lens["sex"] == "M"
             else r"\b(he|his|him)\b")
    hit = sorted({w.lower() for t in texts(lens["id"])
                  for w in re.findall(wrong, t, re.I)})
    assert not hit, (
        "%s(%s) 의 연출에 %s 가 섞였소" % (lens["name"], lens["sex"], hit))


# ══════════════════════════════════════════════════════════
# ③ 그 사람이 이미 쥔 것으로 하는가
# ══════════════════════════════════════════════════════════
@pytest.mark.parametrize("lens", LENSES, ids=lambda l: l["id"])
def test_the_gesture_uses_what_the_person_already_holds(lens):
    """
    ★ 지어내지 않습니다. 담뱃대·패·붉은 실·염주·회초리·해시계는
      LOOK 이 이미 그 사람에게 쥐여 준 것입니다. 없는 소품을 새로
      붙이면 그리는 사람이 두 글을 받고 어느 쪽을 그릴지 모릅니다.
    """
    look = cs.LOOK.get(lens["archetype"]) or ""
    have = {w for w in re.findall(r"[a-z]{3,}", look.lower())
            if w not in STOP}
    st = cs.STAGE[lens["id"]]
    body = " ".join([st["beat"], st["greet"]]).lower()
    shared = sorted(w for w in have if re.search(r"\b%s" % re.escape(w), body))
    assert shared, (
        "%s 의 몸짓이 그 사람 생김새와 한 낱말도 안 겹치오 — "
        "LOOK 에 있는 것으로 하시오" % lens["name"])


# ══════════════════════════════════════════════════════════
# ④ 머리는 제자리
# ══════════════════════════════════════════════════════════
@pytest.mark.parametrize("lens", LENSES, ids=lambda l: l["id"])
def test_the_head_is_pinned(lens):
    """초상은 얼굴로 잘라 씁니다. 머리가 움직이면 크롭이 깨집니다."""
    e = CHARS[lens["id"]]
    for field, text in (("motion", e["motion"]), ("greet", e["greet"])):
        assert "head stays" in text, "%s %s 에 머리 잠금이 없소" % (
            lens["name"], field)
    assert "2D hand-drawn animation" in e["motion"], "영상 앵커가 없소"
    assert "2D hand-drawn animation" in e["greet"], "영상 앵커가 없소"
    assert "loopable" in e["motion"], "도는 초상인데 이음새 말이 없소"


# ══════════════════════════════════════════════════════════
# ⑤ 창이 보여 주는가
# ══════════════════════════════════════════════════════════
def test_the_window_shows_the_faces_and_the_greeting():
    src = ((WEB / "components" / "scene" / "PromptModal.tsx")
           .read_text(encoding="utf-8"))
    assert "e.moods" in src, "표정 둘을 안 보여 주오 — 묶음에만 있으면 없는 것이오"
    assert "e.greet" in src, "첫 대면 인사를 안 보여 주오"
    lib = (WEB / "lib" / "prompts.ts").read_text(encoding="utf-8")
    for f in ("moods", "greet"):
        assert f in lib, "PromptEntry 에 %s 가 없소" % f
