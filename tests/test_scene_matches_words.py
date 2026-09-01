# -*- coding: utf-8 -*-
"""
그림과 글이 어긋나지 않는가.

★ 왜 지키나

  a4b 의 그림은 목패와 종이쪽만 있고 프롬프트에 「No hands, no faces」가
  박혀 있었는데, 바로 아래 글은 「그가 종이 한 장을 더 꺼냈다」였다.
  a5 는 밤 들판의 갈림길인데 글은 「붓을 내려놓고, 그가 물었다」였다.

  손님은 둘 중 무엇을 믿을지 몰라 한다. 그리고 이런 어긋남은 **그림이
  들어온 뒤에야** 드러난다 — 자리표시 SVG 위에서는 무슨 글을 적어도
  안 어색하다.

★ 얼굴은 그림에 안 넣는다

  도령 얼굴은 초상(CharArt · Meet)으로 따로 나온다. 배경에 또 그리면
  같은 사람이 둘이 된다. 손목까지만 그린다.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
BUNDLE = json.loads(
    (WEB / "public" / "asset-prompts.json").read_text(encoding="utf-8"))

# 사람의 몸짓을 말하는 글
ACT = re.compile(r"(꺼냈|들었|내려놓|펼쳤|접었|건넸|짚었|따랐)")

# ★ 손을 찾을 때 「hand-less」 「handle」 을 손으로 세면 안 됩니다.
#   실제로 handle 장면(문고리)이 그래서 잘못 걸렸습니다 —
#   프롬프트 첫 줄이 "hand-less wooden lattice door" 입니다.
HAND = re.compile(r"\bhands?\b(?!-)")


def draws_a_hand(img: str) -> bool:
    """
    그림에 **손이 있는가**.

    ★ 「No hands, no text」 의 hands 를 손으로 세면 안 됩니다. 손을
      그리지 말라는 말인데 그리라는 말로 읽습니다 — 실제로 여덟 장면이
      그래서 잘못 걸렸습니다. 부정문을 먼저 걷어냅니다.
    """
    return bool(HAND.search(re.sub(r"[Nn]o hands?", " ", img)))


def _pairs():
    """장면과 그 바로 아래 나레이션. 초상이 붙었는지도 함께 봅니다."""
    for p in sorted((WEB / "app").rglob("*.tsx")):
        code = re.sub(r"/\*.*?\*/", " ", p.read_text(encoding="utf-8"),
                      flags=re.S)
        code = re.sub(r"//[^\n]*", " ", code)
        for m in re.finditer(
                r'<Scene id="(\w+)"[^>]*/>(.{0,320}?)<(?:Say|button)',
                code, re.S):
            block = m.group(2)
            yield (m.group(1), re.findall(r'"([^"]{4,60})"', block),
                   "<Meet" in block)


def test_a_scene_with_a_gesture_line_shows_a_hand():
    """몸짓을 말했으면 그림에 손이 있어야 한다."""
    bad = []
    for sid, lines, has_meet in _pairs():
        act = [l for l in lines if ACT.search(l)]
        if not act:
            continue
        # ★ 첫 대면(<Meet>)이 바로 아래 붙어 있으면 그 사람이 이미
        #   화면에 있습니다. a4 의 「도령이 고개를 들었다」가 그렇습니다 —
        #   고개는 그림이 아니라 초상이 듭니다.
        if has_meet:
            continue
        img = (BUNDLE["scenes"].get(sid) or {}).get("image") or ""
        if re.search(r"[Nn]o hands", img) or not draws_a_hand(img):
            bad.append("%s — 글 「%s」 인데 그림에 손이 없다" % (sid, act[0]))
    assert not bad, "글과 그림이 어긋난다:\n  " + "\n  ".join(bad)


def test_scene_art_never_draws_the_character_face():
    """얼굴은 초상으로 따로 나온다. 배경에 또 그리면 둘이 된다."""
    bad = []
    for sid, e in BUNDLE["scenes"].items():
        img = e.get("image") or ""
        if draws_a_hand(img) and not re.search(
                r"[Nn]o faces?|face is not visible", img):
            bad.append(sid)
    assert not bad, "손을 그리면서 얼굴을 막지 않았다: %s" % bad
