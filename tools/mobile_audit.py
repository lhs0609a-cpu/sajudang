"""
모바일에서 깨지는 자리 — 좁은 화면을 못 견디는 규칙을 찾는다.

    python tools/mobile_audit.py           표
    python tools/mobile_audit.py --show    자리마다 줄 번호

★ 왜 이 도구가 생겼는가 (2026-09-04)

  손님이 "모바일로 최적화해야한다" 고 했습니다. 그런데 무엇이 안 되어
  있는지는 눈으로는 잘 안 보입니다 — 노트북에서는 다 멀쩡해 보입니다.

★ 무엇을 재는가 — 좁은 화면에서 **실제로 깨지는 것**만

    ① 가로 넘침    글 폭(360px)보다 넓게 못 박은 자리
    ② 손가락       누르는 것이 44px 아래인가 (애플·구글 다 44)
    ③ 안 끊기는 줄  nowrap 을 건 글 — 좁아지면 화면 밖으로 나갑니다
    ④ 붙박이       fixed 로 세워 둔 것이 좁은 화면을 덮는가

  ★ 기준 폭은 **360px** 입니다. 갤럭시 S 계열의 논리 폭이고, 이보다
    좁은 폰은 드뭅니다. 이 폭에서 안 깨지면 나머지는 다 됩니다.

★ 재지 않는 것

  글자 크기와 여백은 여기서 안 봅니다 — 그건 취향이 아니라 **눈으로
  볼 것**이고, 자로 재면 아는 척이 됩니다. 여기 있는 넷은 재면 답이
  하나로 나오는 것들입니다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "apps" / "web" / "styles"

# 이 폭에서 안 깨져야 합니다
NARROW = 360
# 손가락이 닿는 최소 — 애플 HIG · 구글 머티리얼 둘 다 44
TAP = 44

RULE = re.compile(r"([^{}]+)\{([^{}]*)\}", re.S)
MEDIA = re.compile(r"@media([^{]*)\{", re.S)
PX = re.compile(r"(-?[\d.]+)px")


# @keyframes 안쪽은 규칙이 아닙니다 — `to { width: 540px }` 은 화면 폭이
# 아니라 움직임의 끝입니다. 이걸 안 빼면 자가 첫 줄부터 헛짖습니다.
KEYFRAMES = re.compile(r"@keyframes[^{]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", re.S)


def rules(css: str):
    """(선택자, 속성들, 줄번호, 감싼 미디어질의) 를 차례로."""
    # 미디어 질의 안쪽인지 알기 위해 여는 중괄호를 셉니다
    depth_media = []
    i, line = 0, 1
    while i < len(css):
        m = MEDIA.search(css, i)
        r = RULE.search(css, i)
        if m and (not r or m.start() < r.start()):
            depth_media.append((m.group(1).strip(), css.count("{", 0, m.end())))
            i = m.end()
            continue
        if not r:
            return
        sel = r.group(1).strip().split("\n")[-1].strip()
        body = r.group(2)
        line = css.count("\n", 0, r.start()) + 1
        inside = depth_media[-1][0] if depth_media else ""
        if sel and not sel.startswith("@") and not sel.startswith("/*"):
            yield sel, body, line, inside
        i = r.end()


def r_end(css: str, line: int) -> int:
    """그 줄 뒤부터 — 뒤에서 뒤집었는지 보려고."""
    at = 0
    for _ in range(line):
        nxt = css.find(chr(10), at)
        if nxt < 0:
            return len(css)
        at = nxt + 1
    return at


def narrow_ok(media: str) -> bool:
    """이 규칙이 **좁은 화면에도** 걸리는가."""
    if not media:
        return True
    m = re.search(r"max-width:\s*(\d+)", media)
    if m:
        return int(m.group(1)) >= NARROW
    m = re.search(r"min-width:\s*(\d+)", media)
    if m:
        return int(m.group(1)) <= NARROW
    return "print" not in media and "reduced-motion" not in media


def main() -> int:
    show = "--show" in sys.argv
    over, tap, nowrap, fixed = [], [], [], []

    for p in sorted(CSS.glob("*.css")):
        css = p.read_text(encoding="utf-8")
        # 키프레임은 자리를 두고 지웁니다 — 줄 번호가 어긋나지 않게.
        css = KEYFRAMES.sub(
            lambda m: "".join(c if c == chr(10) else " " for c in m.group(0)),
            css)
        for sel, body, line, media in rules(css):
            if not narrow_ok(media):
                continue
            where = "%s:%d" % (p.name, line)

            # ① 가로 넘침 — 못 박은 폭이 좁은 화면보다 넓다
            for prop in ("width", "min-width", "flex-basis"):
                m = re.search(r"(?<![-\w])%s:\s*([^;]+)" % prop, body)
                if not m or "%" in m.group(1) or "auto" in m.group(1):
                    continue
                for v in PX.findall(m.group(1)):
                    if float(v) > NARROW:
                        over.append((where, sel, "%s: %spx" % (prop, v)))

            # 격자 칸이 좁은 화면보다 넓으면 한 칸도 못 들어갑니다
            for v in re.findall(r"minmax\((\d+)px", body):
                if int(v) > NARROW - 24:
                    over.append((where, sel, "minmax(%spx…)" % v))

            # ② 손가락 — 누르는 것의 높이
            if re.search(r"\.(btn|op|lk|abbtn|beatskip-hint)\b", sel) \
                    or sel.startswith("button"):
                h = re.search(r"(?<![-\w])height:\s*([\d.]+)px", body)
                if h and float(h.group(1)) < TAP:
                    tap.append((where, sel, "height %spx" % h.group(1)))
                pad = re.search(r"padding:\s*([\d.]+)px", body)
                fs = re.search(r"font-size:\s*([\d.]+)px", body)
                if pad and fs:
                    got = float(pad.group(1)) * 2 + float(fs.group(1)) * 1.4
                    if got < TAP:
                        tap.append((where, sel, "높이 ≈%dpx" % got))

            # ③ 안 끊기는 줄 — 글에 nowrap 을 걸면 밖으로 나갑니다
            #
            # ★ 셋은 빼야 합니다. 안 빼면 여섯 자리가 다 헛짚습니다 —
            #   그러면 아무도 이 표를 안 봅니다.
            #     · 말줄임이 붙은 것 (…으로 잘리니 안 넘칩니다)
            #     · 뒤에서 `white-space: normal` 로 뒤집은 것 (.gl 이 그렇소)
            #     · 딱지·버튼처럼 **본디 짧은 것**
            if ("white-space: nowrap" in body or "white-space:nowrap" in body):
                ellipsis = "text-overflow" in body or "overflow: hidden" in body
                later = re.search(
                    re.escape(sel) + r"\s*\{[^{}]*white-space:\s*normal",
                    css[r_end(css, line):], re.S)
                chip = re.search(r"\b(tag|tagfree|chip|badge|btn|button|lab|pill|fork)\b",
                                 sel)
                if not (ellipsis or later or chip):
                    nowrap.append((where, sel, "nowrap"))

            # ④ 붙박이 — 좁은 화면을 덮는가
            if re.search(r"position:\s*fixed", body):
                w = re.search(r"(?<![-\w])width:\s*([\d.]+)px", body)
                if w and float(w.group(1)) > NARROW * 0.6:
                    fixed.append((where, sel, "fixed %spx" % w.group(1)))

    print("=" * 76)
    print("  모바일 감사 — 폭 %dpx 에서 깨지는 자리" % NARROW)
    print("=" * 76)
    print()
    for name, rows, hint in (
            ("① 가로 넘침", over, "좁은 화면보다 넓게 못 박은 자리"),
            ("② 손가락", tap, "누르는 것이 %dpx 아래" % TAP),
            ("③ 안 끊기는 줄", nowrap, "글에 nowrap — 밖으로 나갑니다"),
            ("④ 붙박이", fixed, "좁은 화면을 덮는 자리")):
        print("  %-12s %d" % (name, len(rows)))
        for where, sel, why in (rows if show else rows[:6]):
            print("       %-22s %-34s %s" % (where, sel[:34], why))
        if not show and len(rows) > 6:
            print("       … 그 밖 %d (--show)" % (len(rows) - 6))
        print()

    bad = len(over) + len(tap) + len(nowrap) + len(fixed)
    print("-" * 76)
    if bad:
        print("  좁은 화면에서 걸리는 자리 %d" % bad)
    else:
        print("  [OK] 폭 %dpx 에서 깨지는 자리 없음" % NARROW)
    print("-" * 76)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
