"""
그림에 박힌 표식을 지운다 — 제미나이 ✦.

    python tools/wipe_mark.py <그림> <x,y,w,h> [--from dx,dy] [--out 파일]

★ 왜 잘라 내지 않고 지우나

  장면 영상은 표식이 가장자리에 있어서 **창을 옮겨 잘라** 냈습니다.
  그런데 초상은 다릅니다 — 표식이 **옷 한가운데**에 박혀 있어서,
  잘라 내면 사람이 잘립니다.

  대신 옆에서 깨끗한 자리를 떠다 덮습니다. 한복 주름은 세로로 흐르니
  **바로 위**에서 떠 오면 결이 이어집니다. 가장자리는 부드럽게 섞어
  네모 자국이 안 남게 합니다.

★ 색으로 지우면 안 되는 까닭은 여기도 같습니다

  ✦ 는 흰색인데 옷깃과 자수도 흰색입니다. 색으로 고르면 그것들이
  같이 지워집니다. 그래서 **자리**를 손으로 짚습니다.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageFilter


def wipe(im: Image.Image, box: tuple, src_off: tuple) -> Image.Image:
    """box 자리를 src_off 만큼 떨어진 곳의 그림으로 덮는다."""
    x, y, w, h = box
    dx, dy = src_off
    pad = max(6, min(w, h) // 5)          # 가장자리를 섞을 폭

    X, Y = x - pad, y - pad
    W, H = w + pad * 2, h + pad * 2

    patch = im.crop((X + dx, Y + dy, X + dx + W, Y + dy + H)).convert("RGBA")

    # 가운데는 그대로, 가장자리로 갈수록 원래 그림이 비치게
    mask = Image.new("L", (W, H), 0)
    inner = Image.new("L", (w, h), 255)
    mask.paste(inner, (pad, pad))
    mask = mask.filter(ImageFilter.GaussianBlur(pad * 0.7))

    out = im.convert("RGBA")
    out.paste(patch, (X, Y), mask)
    return out


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        print(__doc__.strip().splitlines()[2])
        return 1

    src = Path(args[0])
    box = tuple(int(v) for v in args[1].split(","))
    if len(box) != 4:
        print("자리는 x,y,w,h 넷이오.")
        return 1

    off = (0, -260)
    if "--from" in sys.argv:
        off = tuple(int(v) for v in sys.argv[sys.argv.index("--from") + 1].split(","))

    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else src

    im = Image.open(src)
    print("  원본   %d×%d" % im.size)
    print("  지울 곳 x=%d y=%d %d×%d  ←  %+d,%+d 에서 떠 옴"
          % (*box, *off))
    wipe(im, box, off).save(out)
    print("  적었소  %s" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
