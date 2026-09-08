# -*- coding: utf-8 -*-
"""
신살 인물 한 장을 자리에 넣는다.

    python tools/make_figure.py <원본.png> <신살키>        재 보기
    python tools/make_figure.py <원본.png> <신살키> --write  넣기

넣는 자리: `apps/web/public/sinsal/{키}/figure.png`
화면은 그 파일이 있으면 그림을 쓰고, 없으면 SVG 실루엣으로 버팁니다
(`components/scene/SinsalFigure.tsx`).

★ 캐릭터 초상(make_bust)과 무엇이 다른가

  초상은 스무 장이 **눈높이를 맞춰야** 합니다 — 작은 칸에서 어떤 이는
  이마만, 어떤 이는 턱만 보이면 안 되기 때문입니다. 신살 인물은 글 옆에
  서 있는 그림이라 눈높이를 맞출 것이 없고, 대신 **둘레의 빈 자리를
  잘라내야** 칸 안에서 사람이 작게 앉지 않습니다.

★ 누끼는 make_bust 의 것을 그대로 씁니다

  같은 것을 두 군데서 하면 한쪽만 고쳐집니다. 가장자리에서 번져 나가는
  방식이라 흰 도포 안쪽은 안 뚫립니다.

  ★ **줄이기 전에** 걷습니다. 먼저 줄이면 선이 물러져 그 자리로 새어
    들어갑니다 — 2026-09-08 에 열한 장이 옷 속까지 뚫렸습니다.

★ 바탕이 격자무늬로 그려져 온 장이 있습니다

  투명인 척 그린 것이라 알파는 전부 255입니다. 가장자리에서 색을
  주워 와 흰 칸과 잿빛 칸을 **둘 다** 바탕으로 봅니다.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))

from make_bust import cut_background          # noqa: E402  같은 누끼를 씁니다

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "apps" / "web" / "public" / "sinsal"
TALL = 1000          # 세로 (화면에서는 104px 로 보이지만 인쇄가 있습니다)
PAD = 0.02           # 잘라낸 뒤 둘레에 남기는 여백
SAMPLE = 60          # 가장자리에서 색을 몇 자리나 주워 볼 것인가
NEAR = 12            # 같은 바탕색으로 볼 너그러움
# ★ 26이 아니라 12인 까닭 — 인물 둘레의 옅은 빛무리가 26에서는
#   바탕으로 잡히고, 그 빛무리를 다리 삼아 흰 도포 **안으로** 번집니다.
LIGHT = 170          # 바탕색으로 받아 줄 밝기 하한


def border_colors(im: Image.Image) -> list:
    """가장자리에서 바탕색을 주워 온다. 격자무늬면 둘이 잡힌다."""
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    step = max(w // SAMPLE, 1)
    pts = ([(x, 0) for x in range(0, w, step)]
           + [(x, h - 1) for x in range(0, w, step)]
           + [(0, y) for y in range(0, h, step)]
           + [(w - 1, y) for y in range(0, h, step)])
    out: list = []
    for p in pts:
        c = px[p]
        # ★ 인물이 가장자리에 닿아 있으면 그 옷 색이 바탕으로 뽑힙니다.
        #   암록의 잿빛 도포가 그렇게 통째로 걷혔습니다. 바탕은 밝습니다.
        if min(c[:3]) < LIGHT:
            continue
        if not any(all(abs(c[i] - s[i]) <= NEAR for i in (0, 1, 2))
                   for s in out):
            out.append(c)
    return out[:6]


def trim(im: Image.Image) -> Image.Image:
    """빈 둘레를 잘라낸다 — 여백째 넣으면 칸 안에서 사람이 작아진다."""
    box = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    if not box:
        return im
    mx, my = int(im.width * PAD), int(im.height * PAD)
    return im.crop((max(box[0] - mx, 0), max(box[1] - my, 0),
                    min(box[2] + mx, im.width), min(box[3] + my, im.height)))


TILE = 48            # 격자를 알아볼 때 들여다보는 칸 크기
GREY = 10            # 이 안쪽이면 무채색 (격자는 완전히 무채색입니다)


def checker_alpha(im: Image.Image):
    """
    **격자무늬로 그려진 바탕**을 걷는다. 없으면 None.

    ★ 가장자리 번짐으로는 못 걷습니다 (2026-09-08)

      투명인 척 그린 격자라 흰 칸과 잿빛 칸이 번갈아 있고, 칸과 칸
      사이에는 중간값이 한 줄 낍니다. 너그러움을 좁히면 그 줄에서
      걸음이 멈춰 잿빛 칸이 점점이 남고, 넓히면 인물 둘레의 빛무리를
      타고 **흰 도포 안으로** 번집니다. 게다가 태극귀인과 문창귀인은
      흰 옷자락이 화면 아래 끝에 **닿아** 있어, 아래에서 번지면 옷이
      통째로 걷힙니다.

    ★ 그래서 색이 아니라 **무늬**로 가릅니다

      격자는 한 칸 안에 밝은 칸과 잿빛 칸이 **같이** 있습니다. 흰
      도포는 한 칸이 죄 밝습니다. 무채색이면서 제 칸에 두 결이 같이
      있는 자리만 바탕으로 봅니다 — 옷자락이 끝에 닿아 있어도
      안 걷힙니다.
    """
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()

    cells, checker = {}, 0
    for ty in range(0, h, TILE):
        for tx in range(0, w, TILE):
            lo, hi, flat, n = 255, 0, True, 0
            for y in range(ty, min(ty + TILE, h), 6):
                for x in range(tx, min(tx + TILE, w), 6):
                    c = px[x, y]
                    if max(c) - min(c) > GREY:
                        flat = False
                        break
                    lo, hi, n = min(lo, c[0]), max(hi, c[0]), n + 1
                if not flat:
                    break
            hit = bool(flat and n and hi > 240 and lo < 215)
            cells[(tx // TILE, ty // TILE)] = hit
            checker += hit
    if checker < 12:
        return None                      # 격자가 아닙니다

    a = Image.new("L", (w, h), 255)
    ap = a.load()
    for y in range(h):
        row = cells.get
        for x in range(w):
            if not row((x // TILE, y // TILE)):
                continue
            c = px[x, y]
            if max(c) - min(c) <= GREY and min(c) >= LIGHT:
                ap[x, y] = 0

    # ★ 여기서 멈춥니다 — 인물에 닿은 칸 한 겹은 남습니다.
    #
    #   이미 걷은 자리에서 이어 나가며 마저 걷어 봤습니다. 그랬더니
    #   흰 도포가 격자와 같은 무채색이라 **옷 속으로 뚫고 들어가**
    #   가슴에 검은 구멍이 났습니다 (2026-09-08). 남은 한 겹은
    #   화면에서 1px 남짓이고, 옷에 구멍이 나는 것보다 낫습니다.
    #
    #   ★ 제대로 하려면 **원본을 순백 바탕으로 다시 받으시오.**
    #     격자는 투명인 척 그려진 그림이지 투명이 아닙니다
    #     (알파가 전부 255였습니다). 발주서도 순백을 적어 두었습니다.
    out = rgb.convert("RGBA")
    out.putalpha(a.filter(ImageFilter.GaussianBlur(1.2)))
    return out


def build(src: Path) -> Image.Image:
    im = Image.open(src)
    grid = checker_alpha(im)
    if grid is not None:
        im = grid
    else:
        bgs = border_colors(im)
        im = cut_background(im, bgs, NEAR)   # ★ 원본 해상도에서 먼저 걷는다
    im = trim(im)
    return im.resize((max(int(im.width * TALL / im.height), 1), TALL),
                     Image.LANCZOS)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    write = "--write" in argv
    args = [a for a in argv if not a.startswith("--")]
    if len(args) < 2:
        print("python tools/make_figure.py <원본.png> <신살키> [--write]")
        return 1

    src, key = Path(args[0]), args[1]
    out = build(src)
    gone = sum(out.getchannel("A").histogram()[:9]) / float(
        out.width * out.height) * 100

    dst = OUT / key / "figure.png"
    if write:
        dst.parent.mkdir(parents=True, exist_ok=True)
        out.save(dst, "PNG", optimize=True)
        print("  %-10s %d×%d · 걷어낸 자리 %.0f%% · %.0fKB → %s"
              % (key, out.width, out.height, gone,
                 dst.stat().st_size / 1024, dst.relative_to(ROOT)))
    else:
        tmp = Path(src).with_name("_%s_figure.png" % key)
        out.save(tmp, "PNG", optimize=True)
        print("  %-10s %d×%d · 걷어낸 자리 %.0f%% · 재 보기 %s"
              % (key, out.width, out.height, gone, tmp))
        print("  넣으려면 --write 를 주시오.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
