# -*- coding: utf-8 -*-
"""
들어온 초상이 규격을 지키는가.

★ 왜 지키나

  스무 장이 각기 다른 자리에 눈이 있으면, 대사 옆 작은 칸에서 어떤
  사람은 이마만 보이고 어떤 사람은 턱만 보인다. 발주서(docs/10 §7)가
  768×1024 · 눈높이 y=380 을 정한 이유다.

  그리고 배경이 남아 있으면 안 된다. 초상은 대사 옆·진열대·첫 대면
  **세 가지 다른 바탕** 위에 얹힌다. 흰 네모가 남으면 스티커가 된다.

  무게도 규격이다. 대사마다 뜨는 그림이라 스무 명이 다 들어오면
  그 합이 그대로 손님이 기다리는 시간이 된다.
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHAR = ROOT / "apps" / "web" / "public" / "char"

W, H = 768, 1024
MAX_KB = 300


def busts():
    if not CHAR.is_dir():
        return []
    return sorted(CHAR.glob("*/bust.png"))


@pytest.mark.skipif(not busts(), reason="아직 들어온 초상이 없습니다")
def test_size_and_transparency():
    from PIL import Image
    bad = []
    for p in busts():
        im = Image.open(p)
        if im.size != (W, H):
            bad.append("%s — %d×%d (768×1024 이라야 하오)"
                       % (p.parent.name, *im.size))
            continue
        im = im.convert("RGBA")
        # 네 모서리가 다 비어 있어야 배경이 지워진 것이다
        w, h = im.size
        corners = [im.getpixel(xy) for xy in
                   ((2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3))]
        solid = [c for c in corners if c[3] > 40]
        if solid:
            bad.append("%s — 배경이 남아 있소 (모서리 %d곳)"
                       % (p.parent.name, len(solid)))
        kb = p.stat().st_size // 1024
        if kb > MAX_KB:
            bad.append("%s — %dKB (%dKB 이하라야 하오)"
                       % (p.parent.name, kb, MAX_KB))
    assert not bad, "초상 규격:\n  " + "\n  ".join(bad)


@pytest.mark.skipif(not busts(), reason="아직 들어온 초상이 없습니다")
def test_the_face_is_not_punched_through():
    """
    ★ 얼굴 한가운데가 비면 배경을 색으로 지운 것이다.

      처음에 colorkey 로 흰색을 통째로 지웠더니 이마와 뺨의 하이라이트가
      배경만큼 밝아서 **얼굴이 뚫렸다.** 눈높이 언저리 한가운데는 반드시
      차 있어야 한다.
    """
    from PIL import Image
    bad = []
    for p in busts():
        im = Image.open(p).convert("RGBA")
        w, _ = im.size
        empty = 0
        for x in range(w // 2 - 60, w // 2 + 60, 6):
            for y in range(340, 460, 6):
                if im.getpixel((x, y))[3] < 40:
                    empty += 1
        if empty > 4:
            bad.append("%s — 얼굴 가운데가 %d곳 비었소" % (p.parent.name, empty))
    assert not bad, "얼굴이 뚫렸소:\n  " + "\n  ".join(bad)
