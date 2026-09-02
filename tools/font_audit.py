"""
글꼴이 제자리에 있는가 — 전수조사.

    python tools/font_audit.py

★ 손님이 본 것

  본문이 **넓적한 고정폭**으로 그려졌습니다. 사주 보는 집인데 글씨가
  터미널처럼 보였습니다.

★ 까닭 둘

  ① 웹폰트를 **아예 안 불러왔습니다.**
     tokens.css 는 "Gowun Batang" · "Noto Sans KR" · "IBM Plex Mono"
     라고 이름만 적어 뒀고, 문서 어디에도 그걸 받아 오는 자리가
     없었습니다. 손님 기기에 그 글꼴이 있을 리 없으니 전부 **시스템
     대체 글꼴**로 떨어졌습니다.

  ② 고정폭 글꼴에는 **한글이 없습니다.**
     IBM Plex Mono 는 라틴 문자 글꼴입니다. 한글은 한 자도 없어서
     브라우저가 시스템 고정폭으로 떨어뜨립니다 — 자간이 벌어지고
     획이 뭉갭니다. 그 토큰이 화면 곳곳에 쓰이고 있었습니다.

★ 이 도구가 세는 것

  ① 토큰이 이름 붙인 글꼴을 문서가 실제로 **받아 오는가**
  ② 한글이 들어가는 자리에 고정폭 토큰이 걸려 있는가
  ③ 한자를 크게 그리는 자리의 **굵기**
     — 명조는 400 으로 크게 뽑으면 획이 죽습니다
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
CSS = WEB / "styles"

# 라틴 전용 글꼴 — 한글이 한 자도 없습니다
LATIN_ONLY = ("IBM Plex Mono", "JetBrains Mono", "Roboto Mono",
              "Source Code Pro", "Fira Code", "Courier")

# 한글이 실제로 들어가는 자리. 여기에 고정폭이 걸리면 사고입니다.
#   딱지·숫자만 담는 자리는 고정폭이 맞습니다 — 자리를 맞춰야 하니까.
KOREAN_TEXT = re.compile(
    r"\.tale|\.say|\.note|\.lead|\.q\b|\.body|\.desc|\.sub|"
    r"\.hint|\.warn|\.err|\.teaser|\.cut|\.doubt|\.copy|p\b")


def decls(text: str):
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", text):
        sel = " ".join(m.group(1).split())
        if sel.startswith("@") or not sel:
            continue
        yield sel, " ".join(m.group(2).split())


def main() -> int:
    print("=" * 76)
    print("  글꼴이 제자리에 있는가")
    print("=" * 76)

    tokens = (CSS / "tokens.css").read_text(encoding="utf-8")
    named = dict(re.findall(r"--(serif|sans|mono|hanja):\s*([^;]+);", tokens))

    # ① 받아 오는가
    # ★ 토큰 파일 자신을 세면 안 됩니다.
    #
    #   처음 판은 CSS 까지 긁어 모아 놓고 "글꼴 이름이 어딘가 있으면
    #   받아 온 것" 으로 봤습니다. 그런데 그 이름이 있는 자리가 바로
    #   tokens.css 입니다 — **이름만 적어 둔 것을 받아 왔다고** 읽었고,
    #   그건 이 도구가 잡으려던 바로 그 사고입니다.
    #
    #   실제로 받아 오는 자리만 봅니다: 구글 css2 의 family= 질의와
    #   손으로 적은 @font-face.
    loaded = ""
    for f in list(WEB.glob("app/**/*.tsx")) + list(CSS.glob("*.css")):
        txt = f.read_text(encoding="utf-8")
        loaded += " ".join(re.findall(r"family=[^\"'&\s]+", txt))
        loaded += " ".join(re.findall(r"@font-face[^}]*}", txt))
    print("\n  ① 이름 붙인 글꼴을 문서가 받아 오는가")
    miss = []
    for tok, val in sorted(named.items()):
        for fam in re.findall(r'"([^"]+)"', val):
            got = fam.replace(" ", "+") in loaded or fam in loaded
            print("     --%-6s %-18s %s" % (tok, fam, "받아옴" if got else "★ 없음"))
            if not got:
                miss.append(fam)

    # ② 한글 자리에 걸린 고정폭
    print("\n  ② 한글이 들어가는 자리에 걸린 고정폭")
    # ★ 라틴 글꼴이 **앞에** 있는 건 사고가 아닙니다.
    #
    #   글꼴 대체는 글자 하나씩 일어납니다. 숫자는 앞의 고정폭으로
    #   자리를 맞추고, 한글은 그 글꼴에 없으니 뒤로 넘어갑니다.
    #   그러니 **뒤에 한글 글꼴이 받추어 있는가**만 보면 됩니다.
    #   앞자리만 보고 걸면, 고친 뒤에도 도구가 계속 시끄럽습니다.
    mono_val = named.get("mono", "")
    KOREAN_OK = ("Noto Sans KR", "Noto Serif KR", "Nanum", "Gowun",
                 "Pretendard", "Spoqa")
    mono_latin = (any(f in mono_val for f in LATIN_ONLY)
                  and not any(f in mono_val for f in KOREAN_OK))
    korean_hits = []
    for f in sorted(CSS.glob("*.css")):
        for sel, body in decls(f.read_text(encoding="utf-8")):
            if "var(--mono)" in body and KOREAN_TEXT.search(sel):
                korean_hits.append((f.name, sel))
    if mono_latin:
        print("     --mono 가 라틴 전용입니다: %s" % mono_val.strip())
        print("     → 한글은 시스템 고정폭으로 떨어집니다 (넓적해집니다)")
    print("     한글 자리에 걸린 곳 %d" % len(korean_hits))
    for n, s in korean_hits[:8]:
        print("       %-16s %s" % (n[:16], s[:44]))

    # ③ 한자 자리의 굵기
    #
    #   ★ 한글 제목까지 세면 안 됩니다.
    #
    #     처음 판은 「--serif 인데 크고 얇은 곳」을 전부 걸었습니다.
    #     그랬더니 `.say` `.nr` 같은 **한글 본문**이 열넷 걸렸습니다.
    #     명조 400 으로 뽑은 한글은 얇은 게 아니라 그게 맞습니다 —
    #     획이 죽는 건 한자입니다. 한자를 그리는 자리만 봅니다.
    print("\n  ③ 한자 자리의 굵기")
    thin = []
    for f in sorted(CSS.glob("*.css")):
        for sel, body in decls(f.read_text(encoding="utf-8")):
            if "var(--hanja)" not in body:
                continue
            fw = re.search(r"font-weight:\s*(\d+)", body)
            if not fw or int(fw.group(1)) < 500:
                thin.append((f.name, sel, fw.group(1) if fw else "기본"))
    print("     한자 자리 중 획이 죽는 곳 %d" % len(thin))
    for n, s, w in thin[:8]:
        print("       %-16s %-38s 굵기 %s" % (n[:16], s[:38], w))

    tot = len(miss) + (len(korean_hits) if mono_latin else 0) + len(thin)
    print("\n" + "-" * 76)
    print("  [OK] 글꼴이 제자리에 있소" if tot == 0 else "  걸린 자리 %d" % tot)
    print("-" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
