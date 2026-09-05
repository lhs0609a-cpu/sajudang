# -*- coding: utf-8 -*-
"""
초상 스무 장의 **머리가 같은 높이에 앉았는가.**

★ 손님이 짚은 것 (2026-09-05)
  "초상화도 전부 다 알맞게 수정해줘, 전체 페이지 모두"

★ 무엇이 어긋나 있었나

  스무 장이 다 768×1024 투명이고 규격은 맞았습니다. 그런데 **머리가
  앉은 높이가 제각각**이었습니다 —

      머리 위 여백   청암거사 10px  …  시계장이 80px

  화면은 상자 넷에 담고(chip · talk · card · full), 작은 상자에서는
  한 벌의 잣대로 당겨 씁니다 (`overrides.css` 의 transform-origin ·
  scale). 그러니 머리가 높이 앉은 사람은 상투와 관이 잘려 나가고,
  낮게 앉은 사람은 머리 위가 휑했습니다.

  **CSS 한 벌로는 스무 장을 다 맞출 수 없습니다.** 맞춰야 하는 것은
  초상 쪽입니다 (tools/bust_align.py).

★ 왜 검사로 잠그나

  초상은 한 장씩 들어옵니다. 스물한 번째가 딴 높이로 들어오면 그
  사람만 조용히 잘립니다 — 아무도 안 죽고 화면만 어긋나서 잘 안
  잡힙니다.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHAR = ROOT / "apps" / "web" / "public" / "char"
sys.path.insert(0, str(ROOT))

W, H = 768, 1024
TOP = 30            # tools/bust_align.TOP 와 같은 값
SLACK = 6           # 다시 저장하며 알파 가장자리가 한두 줄 흔들립니다
MAX_KB = 300

Image = pytest.importorskip("PIL.Image", reason="PIL 이 없소")


def busts():
    if not CHAR.exists():
        return []
    out = []
    for d in sorted(CHAR.iterdir()):
        for name in ("bust.webp", "bust.png"):
            p = d / name
            if p.exists():
                out.append(p)
                break
    return out


pytestmark = pytest.mark.skipif(not busts(), reason="아직 들어온 초상이 없습니다")


def _measure(p):
    im = Image.open(p).convert("RGBA")
    bb = im.getchannel("A").getbbox()
    return im.size, bb


def test_규격과_용량():
    bad = []
    for p in busts():
        size, _ = _measure(p)
        if size != (W, H):
            bad.append("%s — %d×%d" % (p.parent.name, *size))
        kb = p.stat().st_size // 1024
        if kb > MAX_KB:
            bad.append("%s — %dKB" % (p.parent.name, kb))
    assert not bad, "초상 규격:\n  " + "\n  ".join(bad)


def test_머리가_같은_높이에_앉았다():
    """
    ★ 이게 이번에 어긋났던 자리입니다. 화면은 한 벌의 잣대로 당기니
      초상이 저마다 다른 높이면 사람마다 다르게 잘립니다.
    """
    bad = []
    for p in busts():
        _, bb = _measure(p)
        if not bb:
            bad.append("%s — 그린 데가 없소" % p.parent.name)
            continue
        if abs(bb[1] - TOP) > SLACK:
            bad.append("%s — 머리 위 %dpx (%dpx 라야 하오)"
                       % (p.parent.name, bb[1], TOP))
    assert not bad, ("머리 높이가 어긋났소 — python tools/bust_align.py --write\n  "
                     + "\n  ".join(bad))


def test_가운데에_섰다():
    """좌우로 치우치면 당겼을 때 얼굴이 한쪽으로 쏠리오."""
    bad = []
    for p in busts():
        _, bb = _measure(p)
        if not bb:
            continue
        off = (bb[0] + bb[2]) // 2 - W // 2
        if abs(off) > 12:
            bad.append("%s — %+dpx 치우쳤소" % (p.parent.name, off))
    assert not bad, "\n  ".join(bad)


def test_머리_위가_비어_있다():
    """
    ★ 알파 상단이 0 이면 머리가 **잘린 채로** 들어온 것이오.
      맞추기 도구는 옮길 뿐이라, 잘린 것은 못 되살리오.
    """
    bad = [p.parent.name for p in busts() if (_measure(p)[1] or (0, 0))[1] == 0]
    assert not bad, "머리가 잘린 초상: %s" % bad


def test_맞추는_도구가_할_일이_없다():
    """도구를 다시 돌려도 옮길 것이 없어야 하오 — 이미 맞았다는 뜻이오."""
    from tools.bust_align import TOP as T, measure
    assert T == TOP, "검사와 도구의 눈금이 갈렸소"
    for p in busts():
        im = Image.open(p).convert("RGBA")
        top, cx = measure(im)
        assert abs(top - T) <= SLACK, (p.parent.name, top)
        assert abs(cx - W // 2) <= 12, (p.parent.name, cx)
