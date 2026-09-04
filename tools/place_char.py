"""
초상 한 장을 자리에 넣는다 — 워터마크를 지우고, 규격에 맞추고, 바탕을 뺀다.

    .\\dev.ps1 face pungun "C:\\...\\Gemini_....png"
    python tools/place_char.py pungun <파일>            캐릭터 초상
    python tools/place_char.py --sinsal taegeuk <파일>   신살 인물

★ 왜 도구로 만드는가 (2026-09-04)

  초상은 스무 장이고 신살 인물이 열셋입니다. 한 장씩 손으로 자르고
  줄이면 서른세 번 다르게 자릅니다 — 눈높이가 제각각이면 대사 옆에서
  얼굴이 위아래로 튑니다.

★ 하는 일 넷

    ① 제미나이 ✦ 를 지운다   오른쪽 아래에 박혀 나옵니다. 그대로 두면
                            「AI 로 찍어낸 집」이 되고, 이 집은 근거 대는
                            집이라 신뢰가 곧 매출입니다.
    ② 바탕을 뺀다            발주서가 **투명 PNG** 를 시킵니다. 흰 바탕
                            채로 넣으면 어두운 화면에 흰 네모가 뜹니다.
    ③ 규격에 맞춘다          768×1024 (3:4). 잘라 맞추지 않고 **담아**
                            맞춥니다 — 얼굴을 자르면 안 됩니다.
    ④ 자리에 넣는다          public/char/{id}/bust.png

★ 지어내지 않습니다

  ✦ 자리의 무늬가 복잡하면 **덮지 않고 멈춥니다.** 얼굴이나 무늬 위에
  뭉갠 자국을 남기느니 사람이 보는 편이 낫습니다.

  바탕도 흰 바탕이 아니면 안 뺍니다. 억지로 빼면 흰 옷깃과 흰 머리가
  같이 뚫립니다.
"""
from __future__ import annotations

import shutil
import sys
from collections import deque
from pathlib import Path

from PIL import Image, ImageFilter, ImageStat

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "apps" / "web" / "public"

# 발주서 §7 — 초상 규격
SIZE = (768, 1024)

# 제미나이 ✦ 가 앉는 자리 (가로·세로 비율). 넉넉히 잡습니다.
MARK = (0.836, 0.845, 0.935, 0.935)

# 바탕으로 볼 밝기 — 이보다 밝고 색이 옅으면 바탕입니다
BG_MIN = 232
BG_SAT = 18


def cover(im: Image.Image, size) -> Image.Image:
    """잘라 맞추지 않고 **담아** 맞춥니다 — 얼굴을 자르면 안 됩니다."""
    w, h = size
    src = im.copy()
    src.thumbnail((w, h), Image.LANCZOS)
    out = Image.new("RGBA", size, (255, 255, 255, 0))
    out.paste(src, ((w - src.width) // 2, (h - src.height) // 2))
    return out


def wipe_mark(im: Image.Image) -> tuple:
    """
    ✦ 를 둘레 색으로 덮는다. 둘레가 고르지 않으면 손대지 않는다.

    돌려주는 것 — (그림, 무슨 일이 있었는지)
    """
    w, h = im.size
    box = (int(MARK[0] * w), int(MARK[1] * h),
           int(MARK[2] * w), int(MARK[3] * h))
    pad = max(6, (box[2] - box[0]) // 3)
    ring = (max(0, box[0] - pad), max(0, box[1] - pad),
            min(w, box[2] + pad), min(h, box[3] + pad))

    # 둘레(테두리 띠)의 고름을 봅니다 — 얼룩덜룩하면 덮으면 티가 납니다.
    band = im.crop(ring).convert("RGB")
    inner = Image.new("L", band.size, 255)
    ix0, iy0 = box[0] - ring[0], box[1] - ring[1]
    inner.paste(0, (ix0, iy0, ix0 + (box[2] - box[0]),
                    iy0 + (box[3] - box[1])))
    st = ImageStat.Stat(band, inner)
    spread = max(st.stddev)
    if spread > 26:
        return im, "✦ 자리 둘레가 고르지 않소(편차 %.0f) — 안 덮었소" % spread

    fill = tuple(int(v) for v in st.median)
    patch = Image.new("RGB", (box[2] - box[0], box[3] - box[1]), fill)
    out = im.convert("RGBA")
    out.paste(patch, box[:2])
    # 이음매를 눅입니다
    soft = out.crop(ring).filter(ImageFilter.GaussianBlur(2.2))
    out.paste(soft, ring[:2])
    return out, "✦ 를 둘레 색 %s 로 덮었소" % (fill,)


def drop_bg(im: Image.Image) -> tuple:
    """
    가장자리에 이어진 **흰 바탕만** 뺀다.

    ★ 「흰 것을 다 빼기」 가 아닙니다. 그러면 흰 옷깃과 흰 머리가 같이
      뚫립니다. 네 귀퉁이에서 번져 나가며, 이어진 것만 뺍니다.
    """
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()

    def bg_like(x, y):
        r, g, b, a = px[x, y]
        if a == 0:
            return True
        return (min(r, g, b) >= BG_MIN
                and max(r, g, b) - min(r, g, b) <= BG_SAT)

    corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    if not any(bg_like(x, y) for x, y in corners):
        return im, "귀퉁이가 흰 바탕이 아니오 — 바탕은 그대로 두었소"

    seen = bytearray(w * h)
    q = deque()
    for x, y in corners:
        if bg_like(x, y) and not seen[y * w + x]:
            seen[y * w + x] = 1
            q.append((x, y))
    n = 0
    while q:
        x, y = q.popleft()
        px[x, y] = (255, 255, 255, 0)
        n += 1
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx]:
                if bg_like(nx, ny):
                    seen[ny * w + nx] = 1
                    q.append((nx, ny))
    return im, "바탕 %d%% 를 뺐소" % round(100 * n / (w * h))


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sinsal = "--sinsal" in sys.argv
    if len(args) < 2:
        print(__doc__)
        return 2
    cid, src = args[0], Path(args[1])
    if not src.exists():
        print("그 파일이 없소: %s" % src)
        return 1

    where = PUB / ("sinsal" if sinsal else "char") / cid
    name = "figure.png" if sinsal else "bust.png"
    where.mkdir(parents=True, exist_ok=True)
    out = where / name

    im = Image.open(src)
    print("=" * 70)
    print("  %s ← %s" % (out.relative_to(PUB), src.name))
    print("=" * 70)
    print("  원본 %dx%d %s" % (im.width, im.height, im.mode))

    im, why = wipe_mark(im)
    print("  ①  %s" % why)

    im = cover(im, SIZE)
    print("  ③  %dx%d 로 담았소" % SIZE)

    im, why = drop_bg(im)
    print("  ②  %s" % why)

    # 있던 것은 밀어 두고 넣습니다 — 되돌릴 수 있게.
    if out.exists():
        keep = out.with_suffix(".png.bak")
        shutil.copy2(out, keep)
        print("  ★  있던 것은 %s 로 밀어 두었소" % keep.name)
    im.save(out, "PNG", optimize=True)
    print("  ④  넣었소 — %d KB" % (out.stat().st_size // 1024))

    # 큰 초상은 영상을 씁니다. 그게 낡았으면 얼굴이 둘이 됩니다.
    clip = where / "clip.webm"
    if clip.exists() and clip.stat().st_mtime < out.stat().st_mtime - 3600:
        print()
        print("  ※ 이 사람의 **영상이 더 오래되었소**(clip.webm).")
        print("    대사 옆 얼굴은 이제 새 그림을 쓰지만, 첫 대면·진열대·")
        print("    릴레이의 큰 초상은 영상을 쓰오. 지우거나 다시 뽑으시오.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
