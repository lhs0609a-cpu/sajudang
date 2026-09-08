"""
초상 한 장을 규격에 맞춰 넣는다.

    python tools/make_bust.py <원본.png> <캐릭터id> [--eye 825]

★ 무엇을 하나

  1. 흰 배경만 지운다 (가장자리에서 번지는 방식)
  2. 눈이 정해진 자리(y=380)에 오도록 앉힌다
  3. 768×1024 투명 PNG 로 `apps/web/public/char/{id}/bust.png`

★ 왜 색으로 지우면 안 되나

  처음에는 ffmpeg 의 colorkey 로 흰색을 통째로 지웠습니다. 그랬더니
  **얼굴의 밝은 부분까지 뚫렸습니다** — 이마와 뺨의 하이라이트가
  배경만큼 밝기 때문입니다. 흰 옷깃과 은실 자수도 같은 위험이 있습니다.

  색은 「어디에 있는지」를 모릅니다. 배경은 **가장자리에서 이어진 흰색**
  이고, 뺨의 하이라이트는 사람에 둘러싸인 흰색입니다. 그래서 네 모서리
  에서 시작해 이웃으로만 번져 나갑니다(flood fill). 사람 안쪽은 바깥과
  이어져 있지 않으니 안 지워집니다.

★ 눈높이를 맞추는 까닭

  스무 장이 각기 다른 자리에 눈이 있으면, 대사 옆 작은 칸에서 어떤
  사람은 이마만 보이고 어떤 사람은 턱만 보입니다. 발주서(docs/10 §7)가
  y=380 을 정한 이유입니다.
"""
from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT_W, OUT_H = 768, 1024
EYE_Y = 380          # 결과물에서 눈이 와야 하는 자리
TOL = 26             # 배경으로 볼 흰색의 너그러움 (0~255)
FEATHER = 1          # 가장자리 한 겹을 반투명으로 — 톱니를 줄입니다


def cut_background(im: Image.Image, colors=None, tol: int = TOL) -> Image.Image:
    """
    네 모서리에서 번져 나가며 배경만 지운다.

    ★ 사람 안쪽의 흰색은 바깥과 이어져 있지 않아 안 지워집니다.
      이게 색으로 지우는 것과의 차이입니다.

    ★ colors — 바탕이 흰색 하나가 아닐 때 (2026-09-08)

      신살 인물 몇 장은 바탕이 **격자무늬로 그려져** 왔습니다.
      투명인 척 그린 것이라 알파는 전부 255이고, 흰 칸과 잿빛 칸이
      번갈아 있습니다. 흰색만 보면 잿빛 칸이 통째로 남습니다.
      바탕색을 여럿 받으면 그중 아무 것과 가까워도 바탕으로 봅니다.
      안 주면 예전과 똑같이 흰색 하나입니다.

    ★ tol — 너그러움을 좁혀야 할 때가 있습니다 (2026-09-08)

      선이 아주 옅게 그려진 장이 있습니다. 26으로 보면 인물 둘레의
      옅은 빛무리가 바탕으로 잡히고, 그 빛무리를 **다리 삼아** 흰
      도포 안으로 번져 들어갑니다 — 태극귀인과 문창귀인이 그렇게
      속옷까지 뚫렸습니다. 좁히면 빛무리에서 걸음이 멈춥니다.

    ★ **줄이기 전에** 부르시오. 먼저 줄이면 선이 물러져, 그 물러진
      자리를 타고 흰 도포·흰 소매 **안으로 새어 들어갑니다.**
      2026-09-08 에 열한 장이 그렇게 속옷까지 뚫렸습니다.
    """
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    assert px is not None
    bgs = list(colors) if colors else [(255, 255, 255)]

    def bright(t) -> bool:
        return any(abs(t[0] - b[0]) <= tol and abs(t[1] - b[1]) <= tol
                   and abs(t[2] - b[2]) <= tol for b in bgs)

    seen = bytearray(w * h)
    q: deque = deque()
    for x in range(w):
        for y in (0, h - 1):
            if bright(px[x, y]):
                q.append((x, y))
                seen[y * w + x] = 1
    for y in range(h):
        for x in (0, w - 1):
            if bright(px[x, y]) and not seen[y * w + x]:
                q.append((x, y))
                seen[y * w + x] = 1

    while q:
        x, y = q.popleft()
        px[x, y] = (255, 255, 255, 0)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx]:
                if bright(px[nx, ny]):
                    seen[ny * w + nx] = 1
                    q.append((nx, ny))

    # 가장자리 한 겹을 반투명으로 — 그냥 자르면 톱니가 보입니다
    if FEATHER:
        edge = []
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                if px[x, y][3] != 0:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if px[x + dx, y + dy][3] == 255:
                        edge.append((x + dx, y + dy))
                        break
        for x, y in edge:
            r, g, b, _ = px[x, y]
            px[x, y] = (r, g, b, 150)
    return im


def place(im: Image.Image, eye: int) -> Image.Image:
    """눈이 EYE_Y 에 오도록 앉히고 768×1024 로."""
    w, h = im.size
    scale = OUT_W / w                       # 폭을 맞춘다 (가로 잘림 없음)
    top = int(round(eye - EYE_Y / scale))   # 이만큼 위를 버리거나(양수) 채운다
    box_h = int(round(OUT_H / scale))

    out = Image.new("RGBA", (w, box_h), (255, 255, 255, 0))
    out.paste(im, (0, -top), im)
    return out.resize((OUT_W, OUT_H), Image.LANCZOS)


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        print(__doc__.strip().splitlines()[2])
        return 1
    src, lid = Path(args[0]), args[1]

    eye = None
    if "--eye" in sys.argv:
        eye = int(sys.argv[sys.argv.index("--eye") + 1])

    im = Image.open(src)
    print("  원본        %d×%d" % im.size)
    if eye is None:
        # 안 주면 흔한 자리로 본다 — 얼굴 그림에서 눈은 대개 위 1/3 쯤
        eye = int(im.size[1] * 0.34)
        print("  ★ --eye 를 안 주셨소. %d 으로 봅니다" % eye)

    im = cut_background(im)
    im = place(im, eye)

    out = ROOT / "apps" / "web" / "public" / "char" / lid
    out.mkdir(parents=True, exist_ok=True)
    p = out / "bust.png"

    # ★ 색을 256가지로 줄인다 — 736KB → 130KB.
    #
    #   대사마다 뜨는 그림이라 무게가 그대로 값입니다. 스무 명이 다
    #   들어오면 14MB 가 됩니다. 그림이 셀 셰이딩(면으로 칠한 그림)이라
    #   256가지로도 눈에 띄는 손해가 없습니다 — 사진이었으면 못 합니다.
    #
    #   투명도는 살립니다 (FASTOCTREE 는 알파를 지킵니다).
    small = im.quantize(colors=256, method=Image.FASTOCTREE)
    small.save(p, optimize=True)
    print("  넣었습니다  %s  (%d KB)" % (p.relative_to(ROOT),
                                     p.stat().st_size // 1024))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
