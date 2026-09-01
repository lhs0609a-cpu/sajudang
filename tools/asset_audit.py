"""
에셋 전수조사 — 만들기 전에, 붙일 자리가 있는지부터 본다.

    python tools/asset_audit.py

★ 왜 이걸 먼저 하나

  에셋은 만들고 나면 되돌리기 가장 비싼 것입니다. 그런데 지금까지
  검사가 하나도 없었습니다 — 화면 그래프(screen_graph)는 화면과
  버튼을 보지만 **에셋은 안 봅니다.**

  그래서 이런 일이 생깁니다:
    · 발주서에 있는데 화면이 안 부르는 장면 (만들어도 안 나옴)
    · 화면이 부르는데 발주서에 없는 장면 (만들 목록에서 빠짐)
    · 만들어도 **붙일 코드가 없는** 에셋
    · 화면이 쓰는 자리와 비율이 안 맞는 장면

  이 도구는 넷을 다 봅니다.

★ 대조하는 네 벌
    manifest.ts     선언된 장면 24종과 그 규격
    화면 코드        <Scene id="..."> 로 실제 부르는 것
    public/scene/   실제로 들어와 있는 파일
    docs/10         발주서가 요구하는 규격
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
MANIFEST = WEB / "components" / "scene" / "manifest.ts"
PUBLIC = WEB / "public"

# ★ 원본은 전부 9:16 세로입니다 (2026-09-01 부터).
#
#   그래서 비율 문제가 뒤집혔습니다. 예전에는 「가로 원본을 세로 자리에
#   넣으면 가로가 잘린다」 였는데, 이제는 **세로 원본을 가로 띠에 넣어
#   위아래가 잘립니다.**
#
#   왜 띠로 보여 주는가 — 세로를 그대로 흘리면 폭의 178% 높이가 됩니다.
#   440px 화면에서 782px 입니다. a5 의 고민 여섯 칸이 그 아래로 통째로
#   밀립니다. 그래서 상자를 장면이 정한 비율로 잡고 cover 로 채웁니다.
#
#   여기서 찍는 것은 **원본의 몇 %가 실제로 보이는가** 입니다. 그림을
#   맡기기 전에 알아야 하는 값입니다 — 16:9 자리에 세로 그림을 그리면
#   가운데 32%만 나갑니다. 중요한 것을 위나 아래 끝에 두면 안 보입니다.
SOURCE_RATIO = "9:16"


def shown_pct(box: str) -> int:
    """9:16 원본을 box 에 cover 로 넣으면 세로 몇 %가 보이는가."""
    try:
        bw, bh = (float(x) for x in box.split(":"))
    except ValueError:
        return 100
    sw, sh = 9.0, 16.0
    if bw <= 0 or bh <= 0:
        return 100
    # 폭을 맞춘 뒤 보이는 높이
    vis = (bh / bw) * sw
    return max(1, min(100, round(vis / sh * 100)))


# 세로가 통째로 쓰이는 자리 — 잘리는 것이 없습니다
FULL_HEIGHT = {"hero", "fill"}


def read_manifest() -> dict:
    # ★ 주석 처리한 줄은 발주 목록이 아닙니다. 빼고 읽습니다 —
    #   안 그러면 지운 장면이 계속 목록에 남습니다.
    src = chr(10).join(
        l for l in MANIFEST.read_text(encoding="utf-8").splitlines()
        if not l.lstrip().startswith("//"))
    out = {}
    for m in re.finditer(
            r'\{\s*id:\s*"([^"]+)",\s*name:\s*"([^"]+)",\s*preset:\s*"([^"]+)",'
            r'\s*ratio:\s*"([^"]+)",\s*seconds:\s*(\d+),\s*loop:\s*(true|false)'
            r'(?:,\s*tint:\s*"([^"]+)")?(?:,\s*seasonal:\s*(true|false))?'
            r'(?:,\s*focus:\s*"([^"]+)")?(?:,\s*box:\s*"([^"]+)")?', src):
        out[m.group(1)] = {
            "name": m.group(2), "preset": m.group(3), "ratio": m.group(4),
            "seconds": int(m.group(5)), "loop": m.group(6) == "true",
            "tint": m.group(7), "seasonal": m.group(8) == "true",
            "focus": m.group(9),
            "box": m.group(10),
        }
    return out


def read_usage() -> dict:
    """어느 화면이 어떤 장면을 어떤 자리에 부르는가."""
    used = {}
    for p in list((WEB / "app").rglob("*.tsx")) + \
             list((WEB / "components").rglob("*.tsx")):
        if p.name in ("Scene.tsx", "manifest.ts"):
            continue
        src = p.read_text(encoding="utf-8")
        for m in re.finditer(r'<Scene\s+id="([a-z]+)"([^/>]*)', src):
            sid, rest = m.group(1), m.group(2)
            where = "inline"
            if "fill" in rest:
                where = "fill"
            elif "hero" in rest:
                where = "hero"
            used.setdefault(sid, []).append(
                (str(p.relative_to(WEB)), where))
    return used


def _screen(path: str) -> str:
    """파일 경로에서 화면 이름만. app/pay/page.tsx → pay"""
    parts = [x for x in path.replace("\\", "/").split("/")
             if x not in ("app", "components", "page.tsx", "scene")]
    return parts[0] if parts else path


def have(sid: str) -> dict:
    d = PUBLIC / "scene" / sid
    got = {}
    for f in ("clip.webm", "clip.mp4", "poster.jpg", "still.png"):
        got[f] = (d / f).exists()
    # 계절 폴더도 봅니다
    got["seasons"] = sorted(x.name for x in d.glob("*") if x.is_dir()) if d.exists() else []
    return got


def main() -> int:
    man = read_manifest()
    used = read_usage()
    print("=" * 76)
    print("  에셋 전수조사 — 만들기 전에 붙일 자리가 있는지부터")
    print("=" * 76)

    # ── 1. 장면 ────────────────────────────────────────
    print("\n[1] 장면 — 선언 · 쓰임 · 파일")
    print("  %-10s %-6s %-11s %-5s %-7s %s"
          % ("장면", "비율", "쓰는 화면", "자리", "파일", "볼 것"))
    print("  " + "─" * 72)
    orphan, missing, ratio_bad, no_file = [], [], [], []
    for sid, spec in man.items():
        u = used.get(sid, [])
        where = ",".join(sorted({w for _, w in u})) or "—"
        files = have(sid)
        has_clip = files["clip.webm"] or files["clip.mp4"] or files["seasons"]
        note = []
        if not u:
            orphan.append(sid); note.append("아무도 안 부름")
        seen_slots = {w for _, w in u}
        if seen_slots and not (seen_slots & FULL_HEIGHT):
            box = spec.get("box") or ("1:1" if spec["ratio"] == "1:1" else "4:3")
            pct = shown_pct(box)
            if pct < 60:
                key = (sid, box)
                if key not in {(a, b) for a, b, _, _, _ in ratio_bad}:
                    ratio_bad.append((sid, box, SOURCE_RATIO,
                                      pct, 100 - pct))
                note.append("세로 %d%%만 보임" % pct)
        if not has_clip:
            no_file.append(sid)
        print("  %-10s %-6s %-11s %-5s %-7s %s"
              % (sid, spec["ratio"],
                 (_screen(u[0][0]) if u else "—")[:11],
                 where[:5], "있음" if has_clip else "없음",
                 " · ".join(dict.fromkeys(note))))

    for sid in used:
        if sid not in man:
            missing.append(sid)

    # ── 2. 캐릭터 ──────────────────────────────────────
    print("\n[2] 캐릭터 20인 — 붙일 자리가 있는가")
    lenses = (WEB / "lib" / "lenses.ts").read_text(encoding="utf-8")
    fields = re.search(r"export interface LensInfo \{(.*?)\}", lenses, re.S)
    keys = re.findall(r"^\s*(\w+)[?]?:", fields.group(1), re.M) if fields else []
    art = [k for k in keys if k in ("bust", "image", "art", "portrait", "clip")]
    ids = re.findall(r'\{ id: "([a-z]+)"', lenses)
    print("  LensInfo 필드      %s" % ", ".join(keys))
    print("  그림을 가리키는 필드 %s" % (", ".join(art) if art else "**없음**"))
    print("  캐릭터 수          %d" % len(ids))
    chdir = PUBLIC / "char"
    print("  /public/char/      %s"
          % ("있음 — " + ", ".join(sorted(x.name for x in chdir.glob("*")))
             if chdir.exists() else "**없음**"))
    # 초상을 그리는 코드가 어디 있는가 — app 과 components 를 다 봅니다.
    drawers = [str(f.relative_to(WEB)) for f in
               list((WEB / "app").rglob("*.tsx")) +
               list((WEB / "components").rglob("*.tsx"))
               if re.search(r'char/\{|/char/|bust\.png', f.read_text(encoding="utf-8"))]
    draws = bool(drawers)
    print("  초상을 그리는 코드   %s"
          % (", ".join(drawers) if draws else "**없음**"))
    # 어느 화면이 실제로 그 컴포넌트를 붙였는가
    users = [str(f.relative_to(WEB)) for f in (WEB / "app").rglob("*.tsx")
             if "<CharArt" in f.read_text(encoding="utf-8")]
    print("  초상이 나오는 화면   %s"
          % (", ".join(users) if users else "**없음 — 컴포넌트만 있고 안 붙였습니다**"))

    # ── 2b. 파일 규격 ──────────────────────────────────
    print("")
    print("[3] 들어온 파일 — 규격을 지키는가  (docs/10 §7)")
    print("     클립 600KB 이하 · poster.jpg 필수 · cardbg 는 still.png 도")
    spec_bad = []
    any_file = False
    for sid in man:
        d = PUBLIC / "scene" / sid
        for base in [d] + [x for x in d.glob("*") if x.is_dir()]:
            clips = [f for f in ("clip.webm", "clip.mp4") if (base / f).exists()]
            if not clips:
                continue
            any_file = True
            where = base.relative_to(PUBLIC)
            for f in clips:
                kb = (base / f).stat().st_size / 1024
                mark = "" if kb <= 600 else "  ← 600KB 넘음"
                if kb > 600:
                    spec_bad.append("%s/%s %.0fKB" % (where, f, kb))
                print("     %-22s %-10s %6.0f KB%s" % (where, f, kb, mark))
            if not (base / "poster.jpg").exists():
                spec_bad.append("%s poster.jpg 없음" % where)
                print("     %-22s poster.jpg **없음** — reduced-motion 대체본"
                      % where)
            if sid == "cardbg" and not (base / "still.png").exists():
                spec_bad.append("cardbg still.png 없음")
    if not any_file:
        print("     들어온 클립이 없습니다.")

    # ── 4. 1차 출시 최소분 ─────────────────────────────
    FIRST = ["gate", "handle", "altar", "banner", "cardbg"]
    print("")
    print("[4] 1차 출시 최소분  (docs/10 §8 — 장면 5 · 캐릭터 5 · 일간 1)")
    for sid in FIRST:
        f = have(sid)
        ok = f["clip.webm"] or f["clip.mp4"] or f["seasons"]
        print("     %-10s %s" % (sid, "들어옴" if ok else "아직"))
    print("     캐릭터 5장 · 일간 1장 — 붙일 자리부터 (아래 참고)")

    # ── 3. 요약 ────────────────────────────────────────
    print("\n" + "─" * 76)
    print("  선언된 장면 %d · 화면이 부르는 장면 %d · 파일이 있는 장면 %d"
          % (len(man), len(used), len(man) - len(no_file)))
    bad = False
    if orphan:
        bad = True
        print("  ★ 발주서에 있는데 **아무 화면도 안 부르는** 장면: %s"
              % ", ".join(orphan))
        print("     만들어도 안 나옵니다. 지우든지 붙이든지 정해야 합니다.")
    if missing:
        bad = True
        print("  ★ 화면이 부르는데 **선언에 없는** 장면: %s" % ", ".join(missing))
    if ratio_bad:
        # ★ 이건 버그가 아니라 **발주 정보**입니다. 원본은 전부 9:16 인데
        #   글 위 장면은 띠로 보여 주므로 세로가 잘립니다. 그림을 그리기
        #   전에 「어디가 보이는가」를 알아야 합니다.
        print("  ※ 9:16 원본 중 실제로 보이는 세로 (상자에 cover):")
        for sid, box, src, pct, cut in sorted(ratio_bad, key=lambda r: r[3]):
            focus = man[sid].get("focus") or "가운데"
            print("     %-10s %-5s 상자  →  세로 %2d%% 보임 (%d%% 잘림) · 초점 %s"
                  % (sid, box, pct, cut, focus))
        print("     중요한 것을 위아래 끝에 두지 마세요 — 안 보입니다.")
        print("     가운데가 답이 아니면 manifest 의 focus 로 옮깁니다.")
    if not draws or not users:
        bad = True
        print("  ★ 캐릭터 초상이 갈 자리가 없습니다.")
        print("     발주서 §7 은 /char/{id}/bust.png 768×1024 를 요구합니다.")
        print("     지금 만들면 스무 장이 갈 데가 없습니다.")
    if not bad:
        print("  [OK] 어긋난 자리 없음")
    print("─" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
