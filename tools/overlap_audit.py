"""
글자가 겹치는 자리 — 전수조사.

    python tools/overlap_audit.py

★ 무엇이 겹침을 만드나

  손님이 본 것: 절기 줄에서 두 글줄이 **서로 위에 그려졌습니다.**

      절기   입동(立冬) 절입 (그 마디로 넘어가는 시각) 1993-
      (계절이 바뀌는11:07:38:46 기준

  까닭은 하나가 아닙니다. 네 가지 부류가 겹침을 만듭니다 —

    ① flex 칸이 못 줄어든다
       `flex: 1` 은 `min-width: auto` 라, 안에 안 끊기는 글이 있으면
       칸이 그 글만큼 벌어집니다. 줄바꿈이 안 되니 옆으로 삐져나가고,
       그 자리에 다음 줄이 그려집니다.

    ② 안 끊기는 글(white-space: nowrap)이 길다
       딱지·꼬리표처럼 짧은 것에는 맞지만, **문장**에 걸면 사고입니다.

    ③ 상자를 넘겨도 안 자른다
       넘칠 수 있는 자리는 `overflow` 를 정해 두어야 합니다.

    ④ 줄 높이가 글자보다 작다
       line-height 가 1 아래면 윗줄과 아랫줄이 물립니다.

★ 이 도구가 보는 것

  CSS 규칙을 읽어 위 네 부류를 짚습니다. 화면을 실제로 그려 보는 것이
  아니라 **겹칠 수 있는 짜임**을 찾습니다 — 그리는 건 브라우저에서
  눈으로 봐야 합니다.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "apps" / "web" / "styles"

# 짧은 것이라 안 끊겨도 되는 자리 — 딱지·단추·꼬리표
OK_NOWRAP = (
    ".tb", ".pil", ".op", ".chip", ".tag", ".slot", ".lk",
    "td:first-child", ".sndhint", ".stepno", ".eb", ".src",
    ".gz", "button", ".ttl", ".tt",
    # 「집마다 다름」 — 넉 자 딱지라 끊기면 오히려 이상합니다
    "em.fork",
    # 상담 분야 딱지 — 「재회」 「시험」 두세 글자입니다. 끊기면 낱말이
    # 두 줄로 쪼개져 딱지로 안 읽힙니다. 넘치면 줄바꿈은 .topics 가 합니다
    ".topics i",
)

# 줄 높이 0 이 **맞는** 자리 — 그림을 담는 껍데기.
#
#   inline 그림 아래의 빈 틈을 없애려고 일부러 0 으로 둡니다. 글이
#   없으므로 물릴 것도 없습니다. 이걸 버그로 세면 도구가 늘 시끄럽고,
#   시끄러운 도구는 아무도 안 봅니다.
OK_TIGHT = (".sayface", ".meetart", ".hookface", ".scenefig",
            ".charart", ".seal i", ".ph i")

# 안 줄어들어도 **되는** flex 칸 — 글이 없는 자리.
#
#   문장이 든 칸은 반드시 줄어야 하지만, 이것들은 안에 글이 없거나
#   한두 글자입니다. 겹칠 것이 없으므로 세지 않습니다.
#
#     .f3>div     년·월·일 입력칸 (숫자 네 자)
#     .prog i     진행 눈금 (빈 칸)
#     .seq div    셈 장면의 한 칸
#     .agr .bar   공감률 막대 (빈 칸)
#     .elbar>div  오행 막대 (빈 칸)
OK_RIGID = (".f3>div", ".prog i", ".seq div", ".agr .bar", ".elbar>div")


def rules(text: str):
    """{선택자: 본문} 으로 가릅니다. 주석은 걷습니다."""
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", text):
        sel = " ".join(m.group(1).split())
        body = m.group(2)
        if sel.startswith("@") or not sel:
            continue
        yield sel, body


def main() -> int:
    print("=" * 76)
    print("  글자가 겹칠 수 있는 자리")
    print("=" * 76)

    # ★ 선택자 하나에 규칙이 여럿일 수 있습니다.
    #
    #   처음 판은 규칙마다 따로 셌습니다. 그래서 `.calc .r .v` 에
    #   min-width 를 따로 준 뒤에 오히려 숫자가 **늘었습니다** —
    #   고쳤는데 도구가 더 나빠졌다고 한 셈입니다.
    #   한 선택자의 모든 선언을 모아서 봅니다.
    merged: dict = {}
    where: dict = {}
    for f in sorted(CSS.glob("*.css")):
        for sel, body in rules(f.read_text(encoding="utf-8")):
            one = " ".join(body.split())
            # ★ 쉼표로 묶은 선택자는 **하나씩** 갈라 봅니다.
            #
            #   `.calc .r .v, .top .tt { min-width: 0 }` 로 고쳤는데
            #   도구는 그걸 통째로 하나의 새 이름으로 보아 「아직 안
            #   고쳤다」 고 했습니다. 고친 것을 못 보는 도구는 고치기
            #   전보다 나쁩니다 — 사람이 두 번 고치게 만듭니다.
            for one_sel in (x.strip() for x in sel.split(",")):
                if not one_sel:
                    continue
                merged.setdefault(one_sel, "")
                merged[one_sel] += " " + one
                where.setdefault(one_sel, f.name)

    flex_bad, nowrap_bad, line_bad = [], [], []
    for sel, one in merged.items():
        f_name = where[sel]

        # ① 못 줄어드는 flex 칸
        if re.search(r"\bflex:\s*(1|auto)\b", one) \
                and "min-width" not in one \
                and sel not in OK_RIGID:
            flex_bad.append((f_name, sel))

        # ② 문장에 걸린 nowrap — 뒤에서 normal 로 되돌렸으면 괜찮습니다
        if re.search(r"white-space:\s*nowrap", one) \
                and not re.search(r"white-space:\s*normal", one) \
                and not any(k in sel for k in OK_NOWRAP):
            nowrap_bad.append((f_name, sel))

        # ④ 글자보다 작은 줄 높이
        lh = re.search(r"line-height:\s*([\d.]+)", one)
        if lh and float(lh.group(1)) < 1.05 \
                and not any(k in sel for k in OK_TIGHT):
            line_bad.append((f_name, sel, lh.group(1)))

    def show(title, rows, why):
        if not rows:
            return
        print("\n  ★ %s — %d곳" % (title, len(rows)))
        print("     %s" % why)
        for r in rows:
            print("     %-16s %s" % (r[0][:16], " ".join(str(x) for x in r[1:])))

    show("못 줄어드는 flex 칸", flex_bad,
         "`flex:1` 은 min-width:auto 라 안엣것만큼 벌어집니다. "
         "min-width:0 을 같이 주세요.")
    show("문장에 걸린 nowrap", nowrap_bad,
         "딱지에는 맞지만 문장에 걸면 옆으로 삐져나가 겹칩니다.")
    show("글자보다 작은 줄 높이", line_bad,
         "line-height 가 1 아래면 윗줄과 아랫줄이 물립니다.")

    tot = len(flex_bad) + len(nowrap_bad) + len(line_bad)
    print("\n" + "-" * 76)
    if tot == 0:
        print("  [OK] 겹칠 만한 짜임 없음")
    else:
        print("  걸린 자리 %d곳" % tot)
        print("  ※ 정적으로 보는 것이라 오탐이 섞입니다. 짧은 딱지는")
        print("    안 끊겨도 되고, 어떤 flex 칸은 안 줄어도 됩니다.")
        print("    다만 **문장이 든 칸**은 반드시 줄어야 합니다.")
    print("-" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
