"""
그림의 가장자리가 배경에 녹는가 — 전수조사.

    python tools/edge_audit.py

★ 손님이 짚은 것

  "이런 이미지가 들어가는 건 자연스럽게 배경이랑 어울리도록
  페이드아웃 적용해서 자연스럽게 해. 경계선이 너무 뚜렷하잖아.
  항상 경계선은 그라데이션으로 페이드아웃 느낌 나도록. 추상화 빼고."

  어두운 배경 위에 **잘라 붙인 네모**가 그대로 보이면 합성한 티가
  납니다. 이 집은 배경 **안에** 사람을 넣는 설계라(docs/16),
  경계가 보이면 설계가 무너집니다.

★ 무엇이 하드 컷을 만드나

  ① 마스크가 없다        가장자리가 그냥 잘립니다
  ② 테두리를 그렸다      border 는 경계를 **일부러** 긋는 것입니다
  ③ 배경색이 있다        상자가 배경과 다른 색이면 네모가 보입니다
  ④ overflow: hidden 만  잘라만 놓고 녹이지 않았습니다

★ 추상화는 예외

  추상화는 그 자체가 판이라 경계가 있어도 됩니다. 사람·장면 그림만
  봅니다.

★ 이 도구가 못 보는 것

  실제로 그려진 화면은 브라우저에서 눈으로 봐야 합니다. 여기서는
  **녹일 장치가 붙어 있는가**만 봅니다.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "apps" / "web" / "styles"

# 그림·영상이 들어가는 자리
ART = (".charart", ".sayface", ".meetart", ".hookface", ".scenefig",
       ".sinsalart", ".bust", ".scene img", ".scene video")

# 추상화 — 그 자체가 판이라 경계가 있어도 됩니다
ABSTRACT = (".abs", ".pattern", ".texture")

# 녹이는 장치 — **마스크만** 셉니다.
#
# ★ 처음엔 ::after 도 녹임으로 셌습니다. 그래서 .meetart 가 통과했는데,
#   실제 배포본을 열어 보니 **아래만** 녹고 옆·위는 잘린 채였습니다.
#   덮개(::after 에 바탕색 그라데이션)는 한 변밖에 못 덮고, 바탕색이
#   무엇인지도 알아야 합니다. 마스크는 네 변을 다 녹이고 무엇 위에
#   놓이든 녹습니다.
#
#   도구가 헐거우면 고쳤다고 착각합니다. 그게 제일 나쁩니다.
SOFT = ("mask-image",)


def rules(text: str):
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", text):
        sel = " ".join(m.group(1).split())
        if sel.startswith("@") or not sel:
            continue
        yield sel, " ".join(m.group(2).split())


def main() -> int:
    print("=" * 76)
    print("  그림의 가장자리가 배경에 녹는가")
    print("=" * 76)

    # 자리마다 선언을 모읍니다 — ::after 같은 짝꿍도 같은 자리로 봅니다
    merged: dict = {}
    for f in sorted(CSS.glob("*.css")):
        for sel, body in rules(f.read_text(encoding="utf-8")):
            for art in ART:
                if art in sel and not any(a in sel for a in ABSTRACT):
                    merged.setdefault(art, {"body": "", "sels": []})
                    merged[art]["body"] += " " + sel + " {" + body + "}"
                    merged[art]["sels"].append(sel)

    hard = []
    for art in ART:
        got = merged.get(art)
        if not got:
            continue
        body = got["body"]
        soft = any(k in body for k in SOFT)
        border = re.search(r"border:\s*(?!none)(?!0)", body)
        bg = re.search(r"background:\s*(?!none)(?!transparent)", body)
        why = []
        if not soft:
            why.append("녹이는 장치 없음")
        if border:
            why.append("테두리를 그림")
        if bg and not soft:
            why.append("배경색이 있음")
        print("\n  %-12s 규칙 %d개  %s"
              % (art, len(got["sels"]), "녹음" if not why else "★ " + " · ".join(why)))
        if why:
            hard.append((art, why))

    print("\n" + "-" * 76)
    if not hard:
        print("  [OK] 그림이 다 배경에 녹소")
    else:
        print("  하드 컷 %d자리" % len(hard))
        print("  ※ mask-image 의 그라데이션으로 가장자리를 녹이세요.")
        print("    테두리는 경계를 **일부러** 긋는 것이라 같이 걷어야")
        print("    합니다 — 마스크를 붙여도 border 는 그대로 보입니다.")
    print("-" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
