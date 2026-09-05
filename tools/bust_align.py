# -*- coding: utf-8 -*-
"""
초상 스무 장의 **머리 높이를 맞춘다.**

★ 손님이 짚은 것 (2026-09-05)
  "초상화도 전부 다 알맞게 수정해줘, 전체 페이지 모두"

★ 무엇이 어긋나 있었나

  스무 장이 다 768×1024 투명이고 규격은 맞았습니다. 그런데 **머리가
  앉은 높이가 제각각**이었습니다 —

      머리 위 여백   청암거사 10px  …  시계장이 80px

  화면은 상자 넷에 담고(chip · talk · card · full), 작은 상자에서는
  한 벌의 잣대로 당겨 씁니다(`overrides.css` 의 transform-origin ·
  scale). 그러니 머리가 높이 앉은 사람은 상투와 관이 잘려 나가고,
  낮게 앉은 사람은 머리 위가 휑했습니다. **CSS 한 벌로는 스무 장을
  다 맞출 수 없습니다** — 맞춰야 하는 것은 초상 쪽입니다.

★ 어떻게 맞추나

  세로로만 옮깁니다. 크기는 안 건드립니다 — 키우면 어깨가 잘리고
  줄이면 얼굴이 작아지는데, 둘 다 그림을 상하게 합니다.

      머리 위를 %d px 로 맞추고, 좌우는 그린 데의 한가운데로.

  낮은 쪽(10px)에 가깝게 잡아 **아래로 내리는 폭을 작게** 둡니다.
  내려가면 바닥에 틈이 생기는데, `.charart` 가 네 변을 마스크로
  녹이니 그 안에 묻힙니다. 올라가는 쪽은 옷자락이 조금 잘릴 뿐이오.

★ 그림을 새로 그리지 않습니다

  자르고 옮길 뿐입니다. 얼굴에는 손대지 않습니다.

    python tools/bust_align.py            재 보기만
    python tools/bust_align.py --write    맞춰 넣기
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "apps" / "web" / "public" / "char"
W, H = 768, 1024

# 머리 위에 둘 여백. 낮은 쪽(가장 높이 앉은 초상)에 가깝게 잡아
# 아래로 내리는 폭을 작게 둡니다.
TOP = 30
# 이보다 많이 옮겨야 하면 초상 자체가 딴판이라는 뜻이오 — 짚고 넘어갑니다.
MOVE_WARN = 60


def _load(d: Path):
    for name in ("bust.webp", "bust.png"):
        p = d / name
        if p.exists():
            return p
    return None


def measure(im):
    """(머리 위, 그린 데의 가로 한가운데). 알파로만 봅니다."""
    bb = im.getchannel("A").getbbox()
    if not bb:
        return 0, W // 2
    return bb[1], (bb[0] + bb[2]) // 2


def aligned(im):
    """맞춘 그림과 (세로 옮김, 가로 옮김)."""
    from PIL import Image

    top, cx = measure(im)
    dy = TOP - top
    dx = W // 2 - cx
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(im, (dx, dy))
    return out, dy, dx


def main(argv=None) -> int:
    from PIL import Image

    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="맞춰 넣습니다")
    a = ap.parse_args(argv)

    if not ROOT.exists():
        print("초상 자리가 없소: %s" % ROOT)
        return 1

    print("초상 머리 맞추기 — 머리 위 %dpx 로" % TOP)
    print("%-11s %7s %7s %7s  %s" % ("id", "머리위", "세로옮김", "가로옮김", ""))
    n = moved = 0
    for d in sorted(ROOT.iterdir()):
        p = _load(d)
        if not p:
            continue
        im = Image.open(p).convert("RGBA")
        if im.size != (W, H):
            print("%-11s  규격이 %d×%d 요 — 건너뛰오" % (d.name, *im.size))
            continue
        top, cx = measure(im)
        dy, dx = TOP - top, W // 2 - cx
        n += 1
        flag = ""
        if abs(dy) >= MOVE_WARN:
            flag = "  ← 많이 옮기오"
        if dy or dx:
            moved += 1
        print("%-11s %7d %+7d %+7d%s" % (d.name, top, dy, dx, flag))
        if a.write and (dy or dx):
            out, _, _ = aligned(im)
            # 원본이 webp 면 webp 로, png 면 png 로 되돌려 넣습니다.
            if p.suffix == ".webp":
                out.save(p, "WEBP", quality=92, method=6, exact=True)
            else:
                out.save(p, "PNG", optimize=True)

    print()
    print("초상 %d장 · 옮길 것 %d장%s"
          % (n, moved, " — 넣었소" if a.write else " (재 보기만 했소)"))
    if not a.write and moved:
        print("넣으려면: python tools/bust_align.py --write")
    return 0


if __name__ == "__main__":
    sys.exit(main())
