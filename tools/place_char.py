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
    ④ 자리에 넣는다          public/char/{id}/bust.webp

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

from PIL import Image, ImageChops, ImageFilter, ImageStat

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "apps" / "web" / "public"

# 발주서 §7 — 초상 규격
SIZE = (768, 1024)

# 제미나이 ✦ 가 앉는 자리 (가로·세로 비율). 넉넉히 잡습니다.
MARK = (0.837, 0.871, 0.897, 0.931)

# 바탕으로 볼 밝기 — 이보다 밝고 색이 옅으면 바탕입니다
BG_MIN = 232
BG_SAT = 18


# 초상 한 장의 무게. ★ 이 얼굴은 **첫 화면 대사 옆**에 뜹니다 (2026-09-04).
#
#   768x1024 RGBA 를 그대로 쓰면 800KB 입니다. 스무 사람이면 16MB 이고,
#   그 중 첫 장은 손님이 도령의 첫 마디를 읽기도 전에 받습니다. 발주서는
#   클립만 600KB 로 묶어 두었고 초상에는 한도가 없었습니다.
# ★ 초상은 **웹피**로 냅니다 (2026-09-04).
#
#   PNG 로는 768×1024 짜리 그림 한 장이 800KB 입니다. 스무 명이면
#   16MB 이고, 그 중 첫 장은 손님이 도령의 첫 마디를 읽기도 전에
#   받습니다. 발주서의 300KB 한도(tests/test_bust_assets)를 넉넉히
#   넘습니다.
#
#   팔레트로 줄이는 길은 재 보고 접었습니다 — 넷을 눈으로 대 보니
#   볼의 홍조가 사라지고 이마에 띠가 생겼습니다(slim 의 주석).
#   꼴을 바꾸면 같은 그림이 **80~110KB** 로 가고, 넓게 평평해지는
#   흠(큰결)이 0.5 로 팔레트의 1/4 입니다. 투명도 그대로 갑니다.
#
#   ★ 화면은 웹피를 먼저 찾고 없으면 PNG 로 물러섭니다
#     (components/CharArt · scene/Scene). 옛 그림이 그대로 삽니다.
WEBP_Q = 92

SLIM_KB = 320

# 팔레트로 줄인 뒤 얼마나 어긋나도 되는가 (0~255 자).
#
# ★ 자가 둘입니다 (2026-09-04에 넷을 눈으로 대 보고 고쳤습니다).
#
#   처음에는 **잔결**(화소마다의 어긋남)만 쟀고 5.0 을 문턱으로 뒀습니다.
#   그 자로는 청암거사가 4.75 로 통과했는데, 확대해 보니 **이마에 띠**가
#   생겨 있었습니다. 풍운도령도 4.93 으로 통과했고 같은 자리에 옅은 띠가
#   있었습니다. 잔결은 화소 단위 어긋남이라, 넓은 자리가 통째로 한 색으로
#   평평해지는 것 — 볼의 홍조가 사라지고 이마가 판판해지는 것 — 을 못
#   잡습니다. 그건 화소마다는 작고 **넓게** 어긋나는 흠입니다.
#
#   그래서 뭉갠 그림끼리 한 번 더 잽니다(큰결). 넷을 재 보니
#       풍운 1.96 · 시계 2.06 · 청암 2.31 · 백운 3.28
#   이고 넷 다 눈에 잡혔습니다. 문턱을 1.2 로 둡니다 — 지금 그림들은
#   전부 안 줄어듭니다. 그게 맞습니다. 얼굴이 이 집의 상품입니다.
#
#   대신 무게가 800KB 씩 갑니다. 이걸 줄이려면 팔레트가 아니라 **다른
#   그림 꼴**(webp)로 가야 하고, 그건 CharArt 와 에셋 감사가 같이
#   움직여야 하는 일이라 따로 잡아야 합니다.
SLIM_RMS = 5.0
SLIM_SOFT = 1.2


def slim(im: Image.Image) -> tuple:
    """
    팔레트로 줄인다. ★ 얼굴이 상하면 **안 줄인다.**

    ✦ 를 덮을 때와 같은 규칙입니다 — 재 보고, 나쁘면 손대지 않습니다.
    줄여서 띠가 생긴 얼굴은 무거운 얼굴보다 나쁩니다.
    """
    from io import BytesIO

    def blob(x, **kw):
        b = BytesIO()
        x.save(b, "PNG", optimize=True, **kw)
        return b.getvalue()

    full = blob(im)
    if len(full) <= SLIM_KB * 1024:
        return im, "%d KB — 줄일 것 없소" % (len(full) // 1024)

    # FASTOCTREE 만 알파를 함께 셉니다 (MEDIANCUT 은 알파를 버립니다)
    q = im.quantize(colors=255, method=Image.FASTOCTREE)
    small = blob(q)
    if len(small) >= len(full):
        return im, "줄여도 안 줄어드오 — 그대로 두오"

    # 보이는 데(알파 있는 자리)만 재 봅니다. 투명한 데는 눈에 안 띕니다.
    a, b = im.convert("RGB"), q.convert("RGBA").convert("RGB")
    diff = ImageChops.difference(a, b)
    mask = im.split()[3].point(lambda v: 255 if v > 128 else 0)
    st = ImageStat.Stat(diff, mask=mask)
    rms = (sum(v * v for v in st.rms) / 3.0) ** 0.5
    if rms > SLIM_RMS:
        return im, "줄이면 얼굴이 상하오 (잔결 %.1f) — 그대로 두오" % rms

    # 넓게 평평해지는 흠 — 볼의 홍조가 사라지고 이마가 판판해지는 것.
    soft = ImageChops.difference(a.filter(ImageFilter.GaussianBlur(8)),
                                 b.filter(ImageFilter.GaussianBlur(8)))
    ss = ImageStat.Stat(soft, mask=mask)
    low = (sum(v * v for v in ss.rms) / 3.0) ** 0.5
    if low > SLIM_SOFT:
        return im, "줄이면 얼굴이 평평해지오 (큰결 %.1f) — 그대로 두오" % low

    return q, "%d KB 를 %d KB 로 줄였소 (잔결 %.1f · 큰결 %.1f)" % (
        len(full) // 1024, len(small) // 1024, rms, low)


def cover(im: Image.Image, size) -> Image.Image:
    """잘라 맞추지 않고 **담아** 맞춥니다 — 얼굴을 자르면 안 됩니다."""
    w, h = size
    src = im.copy()
    src.thumbnail((w, h), Image.LANCZOS)
    out = Image.new("RGBA", size, (255, 255, 255, 0))
    out.paste(src, ((w - src.width) // 2, (h - src.height) // 2))
    return out


def _fill_in(px, mask, W, H):
    """
    표 안쪽을 **위아래에서 끌어와** 채운다.

    ★ 둘레에서 고르게 번지게 두면 얼룩이 남습니다 (2026-09-04).

      처음에는 여덟 이웃의 평균이 안으로 스며들게 했습니다. 그러면
      지운 자리가 둘레의 **평균 한 색**으로 수렴해서, 밝은 삼베옷
      위에서는 동그란 얼룩이 되고 그 자리를 지나가던 옷선이 끊깁니다.
      백운선사가 그랬습니다.

      이 그림들에서 옷 주름과 머리카락은 **세로로** 흐릅니다. 그래서
      같은 칸(세로줄)의 위·아래에서 성한 화소를 찾아 거리로 섞습니다.
      지나가던 세로선이 그대로 이어지고, 결도 남습니다.
      세로로 못 찾으면 가로로 물러섭니다.

    돌려주는 것 — 다 채웠는가
    """
    bad = set(mask)
    cols: dict = {}
    for (x, y) in bad:
        cols.setdefault(x, []).append(y)

    left = []
    for x, ys in cols.items():
        top, bot = min(ys), max(ys)
        a = top - 1
        while a >= 0 and (x, a) in bad:
            a -= 1
        b = bot + 1
        while b < H and (x, b) in bad:
            b += 1
        up = px[x, a] if a >= 0 else None
        dn = px[x, b] if b < H else None
        if up is None and dn is None:
            left.extend((x, y) for y in ys)
            continue
        for y in ys:
            if up is None:
                px[x, y] = dn
            elif dn is None:
                px[x, y] = up
            else:
                t = (y - a) / float(b - a)
                px[x, y] = tuple(
                    int(up[k] + (dn[k] - up[k]) * t) for k in range(len(up)))

    # 세로로 못 찾은 칸은 가로로 — 그림 맨 위나 맨 아래에 닿은 자리요
    for (x, y) in left:
        a = x - 1
        while a >= 0 and (a, y) in bad:
            a -= 1
        b = x + 1
        while b < W and (b, y) in bad:
            b += 1
        lf = px[a, y] if a >= 0 else None
        rt = px[b, y] if b < W else None
        if lf is None and rt is None:
            return False
        px[x, y] = lf or rt
    return True


def wipe_mark(im: Image.Image) -> tuple:
    """
    ✦ 를 찾아 **그 모양만** 지운다. 못 찾으면 손대지 않는다.

    ★ 어디를 보는가 (2026-09-04에 다시 쟀습니다)

      전에는 (0.836, 0.845)~(0.935, 0.935) 을 봤습니다. 실제 ✦ 는
      셋을 재 보니 세 장 다 같은 자리였습니다 —
          가운데 (0.867, 0.901) · 크기 그림의 4.5% 남짓
      옛 네모는 **오른쪽으로 치우쳐** 있어서 별은 절반만 걸치고 대신
      옆의 머리카락·옷선을 한가득 품었습니다. 그래서 「둘레가 고르지
      않다」로 멈췄고, ✦ 는 백운선사 옷 위에 그대로 남았습니다.

    ★ 어떻게 지우는가

      네모를 한 색으로 덮지 않습니다. 덮으면 그 자리를 지나가는 옷
      주름이 끊깁니다 — 시계장이는 별이 **주머니 접힌 선 위**에
      앉아 있습니다. 별 모양만 따서 지우고 둘레에서 번져 들어오게
      두면 지나가던 선이 이어집니다.

    ★ 지어내지 않습니다

      가운데가 둘레보다 밝지 않으면(=별이 없으면) 손대지 않습니다.
      딴 그림에서 잘못 지우느니 남기는 편이 낫습니다.

    돌려주는 것 — (그림, 무슨 일이 있었는지)
    """
    w, h = im.size
    box = (int(MARK[0] * w), int(MARK[1] * h),
           int(MARK[2] * w), int(MARK[3] * h))
    x0, y0, x1, y1 = box
    pad = max(12, (x1 - x0) // 2)
    ring = (max(0, x0 - pad), max(0, y0 - pad),
            min(w, x1 + pad), min(h, y1 + pad))

    # ★ 가운데에서 번져 나가는 것으로는 못 잡습니다 (2026-09-04).
    #
    #   화경은 ✦ 가 **붓집 위**에 앉아 있습니다. 붓집은 금테와 검은
    #   나무가 맞닿은 자리라, 별 한가운데서 번지면 금테를 못 넘어
    #   위쪽 절반만 지워지고 아래 절반이 삼각형으로 남았습니다.
    #   청동자·월하는 별이 둘레보다 **어두워** 아예 못 찾았습니다.
    #
    #   별은 둘레보다 밝은 것도 어두운 것도 아니고, **그 자리에 없어야
    #   할 것**입니다. 뭉갠 그림과 견줘 어긋나는 화소를 별로 봅니다 —
    #   바탕이 무엇이든(흰 저고리든 금테든) 같은 자로 잡힙니다.
    #   이어짐은 안 따집니다. 별은 자리가 정해져 있으니 그 안에서만 봅니다.
    g = im.convert("L")
    pad = max(10, (x1 - x0) // 3)
    ring = (max(0, x0 - pad), max(0, y0 - pad),
            min(w, x1 + pad), min(h, y1 + pad))
    crop = g.crop(ring)
    med = crop.filter(ImageFilter.MedianFilter(21))
    cp, mp = crop.load(), med.load()

    ox, oy = x0 - ring[0], y0 - ring[1]
    bw, bh = x1 - x0, y1 - y0
    rx, ry = bw / 2.0, bh / 2.0
    diffs = []
    for yy in range(bh):
        for xx in range(bw):
            # 별이 앉는 자리는 타원 안입니다 — 모서리는 안 봅니다
            if ((xx - rx) / rx) ** 2 + ((yy - ry) / ry) ** 2 > 1.0:
                continue
            d = abs(cp[ox + xx, oy + yy] - mp[ox + xx, oy + yy])
            diffs.append((d, xx, yy))
    if not diffs:
        return im, "✦ 자리를 못 잡았소 — 손대지 않았소"

    top = max(d for d, _, _ in diffs)
    if top < 12:
        return im, "✦ 가 안 보이오 (가장 어긋난 데가 %d) — 손대지 않았소" % top
    # ★ 문턱은 **낮게** 잡습니다. 가장 어긋난 데(top)는 별의 테두리라
    #   크게 나오고, 거기에 비례해 자르면 별의 **속살**이 남습니다 —
    #   시계장이가 271화소만 잡혀 손을 못 댔습니다. 별은 자리가
    #   정해져 있어(타원 안) 조금 넉넉히 잡아도 얼굴에 안 닿습니다.
    cut = 10
    star = {(x0 + xx, y0 + yy) for d, xx, yy in diffs if d >= cut}

    # ★ 별의 **속을 메웁니다** (2026-09-04).
    #
    #   어긋남으로 잡으면 별의 테두리는 잡히는데 한가운데는 뭉갠
    #   그림과 값이 비슷해 구멍으로 남습니다. 그 구멍은 표가 아니니
    #   채우는 자가 그걸 **성한 화소**로 알고 거기서 색을 끌어옵니다 —
    #   별빛으로 별 자리를 칠하는 셈이라, 지운 자리에 밝은 마름모가
    #   그대로 남았습니다. 열아홉이 다 그랬습니다.
    #
    #   별은 한 덩이니 칸(세로줄)마다 위끝과 아래끝 사이를 다 표로 봅니다.
    cols: dict = {}
    for (px_, py_) in star:
        lo, hi = cols.get(px_, (py_, py_))
        cols[px_] = (min(lo, py_), max(hi, py_))
    star = {(px_, yy) for px_, (lo, hi) in cols.items()
            for yy in range(lo, hi + 1)}

    area = bw * bh
    if len(star) < 300:
        return im, "✦ 가 너무 작소 (%d화소) — 손대지 않았소" % len(star)
    # ★ 속을 메우면 표가 넓어집니다. 그게 정상입니다 (2026-09-04).
    #
    #   0.55 로 묶었더니 청암(삼베 결) · 행수(주판알) · 화경(금실 자수)
    #   셋이 「통째로 얼룩졌소」로 걸려 ✦ 를 달고 나갔습니다. 결이 고운
    #   옷일수록 어긋나는 화소가 많아, 결 있는 옷만 골라 못 지운 셈입니다.
    #   자리가 이미 별 크기로 좁으니(그림의 6%) 넉넉히 둡니다 — 채우는
    #   것은 그 칸 위아래의 제 색이라 넓어도 티가 안 납니다.
    if len(star) > area * 0.88:
        return im, "✦ 자리가 통째로 얼룩졌소 — 손대지 않았소"

    # 흐린 테두리까지 몇 겹 넓혀 잡습니다
    grow = set(star)
    for _ in range(4):
        grow |= {(x + dx, y + dy) for (x, y) in grow
                 for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    grow = {(x, y) for (x, y) in grow if 0 <= x < w and 0 <= y < h}

    out = im.convert("RGBA")
    px = out.load()
    if not _fill_in(px, sorted(grow), w, h):
        return im, "✦ 를 다 못 채웠소 — 손대지 않았소"

    xs = [p[0] for p in grow]
    ys = [p[1] for p in grow]
    sx0, sy0 = max(0, min(xs) - 4), max(0, min(ys) - 4)
    sx1, sy1 = min(w, max(xs) + 5), min(h, max(ys) + 5)
    soft = out.crop((sx0, sy0, sx1, sy1)).filter(ImageFilter.GaussianBlur(1.4))
    out.paste(soft, (sx0, sy0))
    return out, "✦ 를 지웠소 (%d화소 · 어긋남 %d)" % (len(star), top)


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
    name = "figure.png" if sinsal else "bust.webp"
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
    # ★ 팔레트로는 못 줄입니다 — 얼굴이 평평해집니다 (slim 참고).
    #   대신 **꼴을 바꿉니다.** 같은 그림이 5분의 1로 갑니다.
    im.save(out, "WEBP", quality=WEBP_Q, method=6)
    print("  ④  넣었소 — %d KB" % (out.stat().st_size // 1024))

    # 전에 넣어 둔 PNG 가 있으면 걷어냅니다 — 둘이 남으면 무거운 쪽이 갑니다.
    old = out.with_suffix(".png")
    if old != out and old.exists():
        old.unlink()
        print("  ★  묵은 %s 는 걷었소" % old.name)

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
