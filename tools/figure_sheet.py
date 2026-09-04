"""
신살 인물 발주서 — 열셋을 한 장에.

    python tools/figure_sheet.py            화면에
    python tools/figure_sheet.py --write    신살인물_발주서.txt 로

★ 왜 따로 뽑는가 (2026-09-04)

  프롬프트는 열셋 다 있었습니다. `에셋_프롬프트_전체.txt` 8부에도
  실려 있고 관리자 화면에서 카드를 눌러도 뜹니다. 그런데 손님이
  말했습니다 — "화개던 괴강이던 다 명령프롬프트 만들어줘. 저거
  소개할때 이미지 같이 넣게."

  스물다섯 장면 사이에 섞여 있으면 **열셋을 이어서 뽑을 수가 없습니다.**
  캐릭터 초상을 따로 뽑아 놓은 것과 같은 까닭입니다. 한 자리에 모읍니다.

★ 인물은 **움직이지 않습니다**

  글 옆에 서 있는 초상이라 스물여섯이 한꺼번에 움직이면 글을 못 읽습니다.
  그림 한 장이면 됩니다 — 힉스필드에 올릴 일이 없습니다.

★ 넣는 자리

      apps/web/public/sinsal/{key}/figure.png

  넣기만 하면 코드를 안 고치고 바뀝니다. 자리표시 SVG 가 그때부터
  물러납니다 (components/scene/SinsalFigure.tsx).

  도구로 넣으면 ✦ 를 지우고 규격에 맞춰 줍니다 —
      .\\dev.ps1 face --sinsal taegeuk "C:\\...\\받은파일.png"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "apps" / "web" / "public" / "asset-prompts.json"
SINSAL = ROOT / "seed" / "sinsal.json"

# 손님이 리포트에서 만나는 차례 — 길신 먼저, 살, 특수
ORDER = ["cheoneul", "taegeuk", "munchang", "geumyeo", "amrok",
         "yangin", "baekho", "wonjin", "dohwa",
         "yeokma", "hwagae", "gwaegang", "gongmang"]

BAR = "=" * 74
DASH = "-" * 74


def main() -> int:
    d = json.loads(PROMPTS.read_text(encoding="utf-8"))
    figs = d["figures"]
    mean = json.loads(SINSAL.read_text(encoding="utf-8")).get("meaning", {})

    missing = [k for k in ORDER if k not in figs]
    if missing:
        print("프롬프트가 없는 인물: %s" % ", ".join(missing))
        return 1

    L = []
    P = L.append
    P(BAR)
    P("  신살 인물 발주서 — %d명" % len(ORDER))
    P(BAR)
    P("")
    P("  ★ 그림 한 장이면 되오. 영상은 안 쓰오 —")
    P("    글 옆에 서 있는 초상이라 여럿이 움직이면 글을 못 읽소.")
    P("")
    P("  ① 제미나이에 아래 ② 프롬프트를 그대로 넣으시오 (3:4 세로)")
    P("  ② 받은 파일을 이 자리에 넣으시오")
    P("       apps/web/public/sinsal/{이름}/figure.png")
    P("     또는 도구로 (✦ 를 지우고 규격까지 맞춰 주오)")
    P("       .\\dev.ps1 face --sinsal {이름} \"C:\\...\\받은파일.png\"")
    P("")
    P("  차례")
    for i, k in enumerate(ORDER, 1):
        P("    %2d  %-10s %s" % (i, k, figs[k].get("title", "")))
    P("")

    for i, k in enumerate(ORDER, 1):
        f = figs[k]
        m = mean.get(k, {})
        P("")
        P(BAR)
        P("  %02d / %d   %s" % (i, len(ORDER), f.get("title", k)))
        P(BAR)
        P("  이름   %s" % k)
        P("  폴더   apps/web/public/sinsal/%s/figure.png" % k)
        if f.get("who"):
            P("  누구   %s" % f["who"])
        if m.get("one"):
            P("  뜻     %s" % m["one"])
        P("  규격   3:4 세로 · 그림 한 장 · 영상 안 씀")
        P("")
        P(DASH)
        P("  프롬프트 · 제미나이")
        P(DASH)
        P("")
        P((f.get("image") or "").rstrip())
        P("")

    text = "\n".join(L)
    if "--write" in sys.argv:
        out = ROOT / "신살인물_발주서.txt"
        out.write_text(text + "\n", encoding="utf-8")
        print("%d명을 적었습니다 — %s" % (len(ORDER), out.name))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
