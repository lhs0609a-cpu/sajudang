# -*- coding: utf-8 -*-
"""
초상 영상의 **누끼를 뜬다** — 바탕을 걷어 투명으로.

★ 손님이 시킨 것 (2026-09-05)
  "풍운도령 누끼 따줘 깨끗하게."

★ 색 하나로 자르면 얼굴이 뚫리오

  처음엔 `colorkey` 로 잘라 봤소. 그런데 바탕이 크림색(253,248,240)
  이고 살빛·흰 깃도 밝아서, 문턱을 올리면 **이마와 뺨이 뚫리고**
  내리면 바탕이 남았소. 색 거리 하나로는 못 가르오.

★ **바깥에서 자라나는 매트**로 뜨오

  바탕은 네 변에서 이어져 있소. 그러니 「바탕색과 가까운가」만 보지
  말고 **가장자리에서 이어져 닿는가**를 같이 보오 (flood fill).
  얼굴 한복판이 바탕색과 비슷해도 바깥과 안 이어져 있으면 안 뚫리오.

  가장자리는 살짝 무르게 남기오 — 딱 자르면 톱니가 서오.

★ 투명은 못 담소 — **바탕을 갈아** 굽소

  VP9 는 알파를 담을 수 있다고 적혀 있으나, 이 자리의 ffmpeg 은
  실제로 알파 층을 안 실었소 (두 번 시험해 되읽어 확인했소 —
  투명해야 할 자리가 도로 크림색으로 나왔소). H.264 는 애초에 못 담소.

  그래서 **걷어낸 자리를 화면의 어두운 바탕으로 갈아** 굽소.
  초상은 `.charart` 안에서 그 색 위에 앉고, 네 변은 마스크가 녹이니
  눈에는 투명과 같소. 언젠가 알파를 담을 수 있게 되면 이 함수의
  `BAKE` 만 끄면 되오.

    python tools/bust_matte.py pungun            재 보기 (첫 프레임만)
    python tools/bust_matte.py pungun --write    영상째 떠서 넣기
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "apps" / "web" / "public" / "char"

# 바탕으로 볼 색 거리. 이보다 가까우면서 **가장자리와 이어진** 화소만 걷습니다.
TOL = 26.0
# 가장자리 무르기(px). 0 이면 톱니가 섭니다.
SOFT = 2.0
# mp4 에 구워 넣을 바탕 — styles/tokens.css 의 --bg 와 같은 값이오.
BAKE = (12, 10, 18)


def _ff(*args) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def sample_bg(im):
    """네 모서리에서 바탕색을 잰다."""
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    cs = [px[1, 1], px[w - 2, 1], px[1, h - 2], px[w - 2, h - 2]]
    return tuple(sum(c[i] for c in cs) // 4 for i in range(3))


def cut(im, bg=None):
    """
    (누끼 뜬 그림, 바탕색, 걷어낸 화소 수).

    ★ 바탕색은 **밖에서 정해 넘깁니다** (2026-09-05).

      첫 프레임이 페이드인 중이면 모서리가 크림색이 아니라 잿빛으로
      잡혀서 아무것도 안 걷힙니다. 프레임마다 다시 재면 페이드 구간
      에서 걷는 자리가 달라져 **깜빡입니다.** 가운데 프레임에서 한 번
      재고 그 값을 끝까지 씁니다.
    """
    from PIL import Image, ImageDraw, ImageFilter

    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    if bg is None:
        bg = sample_bg(im)

    # ① 바탕색과 가까운 화소 (아직 **이어짐은 안 봄**)
    near = Image.new("L", (w, h), 0)
    np_ = near.load()
    t2 = TOL * TOL
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            d = ((c[0] - bg[0]) ** 2 + (c[1] - bg[1]) ** 2
                 + (c[2] - bg[2]) ** 2)
            if d <= t2:
                np_[x, y] = 255

    # ② 네 모서리에서 **이어진 것만** 바탕으로 봅니다.
    #    얼굴 한복판이 밝아도 바깥과 안 이어져 있으면 안 뚫립니다.
    mark = 128
    for seed in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        if np_[seed] == 255:
            ImageDraw.floodfill(near, seed, mark, thresh=0)
    a = Image.new("L", (w, h), 255)
    ap = a.load()
    for y in range(h):
        for x in range(w):
            if np_[x, y] == mark:
                ap[x, y] = 0
    gone = sum(1 for y in range(0, h, 4) for x in range(0, w, 4)
               if ap[x, y] == 0) * 16

    if SOFT:
        a = a.filter(ImageFilter.GaussianBlur(SOFT))
    out = rgb.convert("RGBA")
    out.putalpha(a)
    return out, bg, gone


def main(argv=None) -> int:
    from PIL import Image

    ap = argparse.ArgumentParser()
    ap.add_argument("lens", help="캐릭터 id (보기: pungun)")
    ap.add_argument("--name", default="greet", help="영상 이름 (기본 greet)")
    ap.add_argument("--write", action="store_true", help="영상째 떠서 넣습니다")
    a = ap.parse_args(argv)

    d = ROOT / a.lens
    src = d / ("%s.mp4" % a.name)
    if not src.exists():
        src = d / ("%s.webm" % a.name)
    if not src.exists():
        print("영상이 없소: %s" % d)
        return 1

    tmp = Path(tempfile.mkdtemp(prefix="matte-"))
    try:
        _ff("-i", str(src), "-fps_mode", "passthrough",
            str(tmp / "f%04d.png"))
        frames = sorted(tmp.glob("f*.png"))
        if not frames:
            print("프레임을 못 뽑았소")
            return 1
        # ★ 바탕은 **가운데 프레임**에서 잽니다 — 페이드가 끝난 자리요.
        bg = sample_bg(Image.open(frames[len(frames) // 2]))
        im, _, gone = cut(Image.open(frames[len(frames) // 2]), bg)
        w, h = im.size
        print("%s · 프레임 %d장 · 바탕 %s · 걷어낼 몫 %.1f%%"
              % (a.lens, len(frames), bg, 100.0 * gone / (w * h)))
        if not a.write:
            look = tmp.parent / ("matte_%s.png" % a.lens)
            flat = Image.new("RGB", im.size, BAKE)
            flat.paste(im, (0, 0), im)
            flat.save(look)
            print("첫 프레임을 붙여 봤소: %s" % look)
            print("넣으려면: python tools/bust_matte.py %s --write" % a.lens)
            return 0

        cutd = tmp / "cut"
        cutd.mkdir()
        # ★ 걷어낸 자리를 **어두운 바탕으로 갈아** 둡니다.
        #   안 갈면 알파 밑에 크림색이 그대로 남아, 알파를 못 담는
        #   인코더가 그걸 도로 꺼내 옵니다.
        for i, f in enumerate(frames):
            got, _, _ = cut(Image.open(f), bg)
            flat = Image.new("RGB", got.size, BAKE)
            flat.paste(got, (0, 0), got)
            flat.save(cutd / f.name)
            if i % 20 == 0:
                print("  뜨는 중 %d/%d" % (i, len(frames)))

        fps = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0",
             str(src)], capture_output=True, text=True).stdout.strip()

        # ── webm — 알파를 담소 ──────────────────────────
        _ff("-framerate", fps, "-i", str(cutd / "f%04d.png"),
            "-i", str(src),
            "-map", "0:v", "-map", "1:a?",
            "-c:v", "libvpx-vp9", "-pix_fmt", "yuv420p",
            "-crf", "32", "-b:v", "0", "-row-mt", "1",
            "-c:a", "libopus", "-b:a", "96k",
            str(tmp / "out.webm"))

        # ── mp4 — 알파를 못 담으니 어두운 바탕을 구워 넣소 ──
        _ff("-framerate", fps, "-i", str(cutd / "f%04d.png"),
            "-i", str(src),
            "-map", "0:v", "-map", "1:a?",
            "-c:v", "libx264", "-crf", "20", "-preset", "slow",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-c:a", "aac", "-b:a", "128k",
            str(tmp / "out.mp4"))

        # ★ 임시 자리에 만들고 **그다음에** 옮깁니다.
        #   읽으면서 같은 파일에 쓰면 ffmpeg 이 터집니다.
        shutil.move(str(tmp / "out.webm"), str(d / ("%s.webm" % a.name)))
        shutil.move(str(tmp / "out.mp4"), str(d / ("%s.mp4" % a.name)))

        # 포스터도 누끼 뜬 것으로 (webp — jpg 는 투명을 못 담소)
        first, _, _ = cut(Image.open(frames[len(frames) // 2]), bg)
        first.save(d / ("%s.webp" % a.name), "WEBP", quality=92, exact=True)
        print("넣었소 — %s.webm(투명) · %s.mp4(구움) · %s.webp"
              % (a.name, a.name, a.name))
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
