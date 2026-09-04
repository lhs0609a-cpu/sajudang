# -*- coding: utf-8 -*-
"""
명령어에 **그 화면에서 어떻게 쓰이는지**를 박아 넣는다.

    python tools/prompt_use.py            대조만
    python tools/prompt_use.py --write    asset-prompts.json 에 써넣음

★ 왜 필요한가 (2026-09-04)

  손님이 시킨 것 — "지금 전체 이미지 명령어랑 힉스필드 명령어 더
  디테일하고 완벽하게 **그 화면에 딱 맞게** 설계되어있는지 전수점검."

  명령어는 그림을 잘 적고 있었습니다. 그런데 **그 그림이 어디에
  걸리는지**는 한 줄도 없었습니다 —

    · 원본은 전부 9:16 세로인데, 인라인 장면은 **4:3 상자**로 잘라
      씁니다. 세로의 **42%만** 보입니다. 위아래 29%씩은 안 보입니다.
      그걸 모르고 그리면 주제가 잘려 나갑니다.
    · 대문(fill)은 그림 **위에 글이 얹힙니다.** 가운데가 비어야 합니다.
    · 머리그림(hero)은 9:16 그대로 보여 주되 58vh 에서 잘립니다.

  이 셋은 코드가 정합니다. 그러니 코드에서 읽어 박습니다 — 손으로
  적으면 화면을 옮길 때마다 갈립니다.

★ 통째로 다시 뽑지 않습니다

  `chars` 20종과 `mirror` 는 참조 구현체에 없고 이 파일에만 삽니다
  (CLAUDE.md). 그래서 **`use` 칸만** 갈아 끼웁니다. 나머지는 안 건드립니다.
"""
from __future__ import annotations

import argparse
import io
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
PROMPTS = WEB / "public" / "asset-prompts.json"

# 화면 폭 — 틀 440 · .scr 좌우 22 (engine/typo.WIDTH 와 같은 자)
WIDTH = 396
SRC_RATIO = 9 / 16          # 들어오는 영상은 전부 세로 9:16


def _box_of(class_attr: str, spec_box: str | None) -> tuple[str, str]:
    """이 자리에서 어떤 상자로 보여 주는가 → (자리 이름, 상자 비율)."""
    if "fill" in class_attr:
        return "fill", "부모 전체"
    if "hero" in class_attr:
        return "hero", "9:16"
    return "inline", spec_box or "4:3"


def _visible_pct(box: str) -> int | None:
    """9:16 원본을 그 상자에 cover 로 채웠을 때 **세로 몇 %가 보이는가**."""
    m = re.fullmatch(r"(\d+):(\d+)", box)
    if not m:
        return None
    bw, bh = int(m.group(1)), int(m.group(2))
    box_ratio = bw / bh
    if box_ratio <= SRC_RATIO:          # 상자가 원본보다 세로로 길다 — 다 보임
        return 100
    return round(100 * SRC_RATIO / box_ratio)


def usage() -> dict:
    """<Scene id="..."> 를 부르는 자리를 전부 긁는다."""
    out: dict[str, list] = {}
    for p in sorted(WEB.rglob("*.tsx")):
        if "node_modules" in p.parts:
            continue
        src = p.read_text(encoding="utf-8")
        for m in re.finditer(r'<Scene\s+id="(\w+)"([^/>]*)', src):
            sid, rest = m.group(1), m.group(2)
            rel = p.relative_to(WEB).as_posix()
            out.setdefault(sid, []).append((rel, rest))
    return out


def manifest() -> dict:
    src = (WEB / "components" / "scene" / "manifest.ts").read_text(
        encoding="utf-8")
    out = {}
    for m in re.finditer(r'\{ id: "(\w+)", (.*?) \},', src):
        row = dict(re.findall(r'(\w+): "([^"]*)"', m.group(2)))
        row.update({k: v == "true" for k, v in
                    re.findall(r'(\w+): (true|false)', m.group(2))})
        num = dict(re.findall(r'(\w+): (\d+)', m.group(2)))
        row.update({k: int(v) for k, v in num.items()})
        out[m.group(1)] = row
    return out


SCREEN_KO = {
    "app/page.tsx": "들어오다",
    "app/lobby/page.tsx": "둘러보다",
    "app/report/[id]/page.tsx": "읽다",
    "app/pay/page.tsx": "값을 치르다",
    "app/relay/page.tsx": "이어지다",
    "app/daily/page.tsx": "오늘",
    "app/me/page.tsx": "인장첩",
    "app/summary/page.tsx": "분석지",
    "app/s/[token]/SharedView.tsx": "건너오다",
}


def line_for(sid: str, uses: list, spec: dict) -> str:
    """그 장면 하나의 「이 화면에서 이렇게 쓰이오」 한 덩이."""
    parts = []
    seen = set()
    for rel, rest in uses:
        where, box = _box_of(rest, spec.get("box"))
        key = (rel, where, box)
        if key in seen:
            continue
        seen.add(key)
        ko = SCREEN_KO.get(rel, rel)
        vis = _visible_pct(box)
        if where == "fill":
            parts.append(
                "%s — 화면을 통째로 덮고 **그 위에 글이 얹히오.** "
                "가운데 세로 절반은 비워 두시오." % ko)
        elif where == "hero":
            parts.append(
                "%s — 머리그림. 9:16 그대로 보이나 화면 높이의 58%% 에서 "
                "아래가 잘리오." % ko)
        else:
            parts.append(
                "%s — 글 위 띠. **%s 상자로 잘라 씁니다 — 세로의 %d%% 만 "
                "보이오.** 주제를 세로 한가운데에 두시오."
                % (ko, box, vis if vis else 0))
    focus = spec.get("focus")
    if focus:
        parts.append("초점은 %s 로 잡혀 있소 (가운데가 답이 아닌 장면)." % focus)
    return " / ".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    data = json.loads(PROMPTS.read_text(encoding="utf-8"))
    man, use = manifest(), usage()
    scenes = data.get("scenes", {})

    changed, orphan, unused = [], [], []
    for sid, spec in man.items():
        if sid not in scenes:
            orphan.append(sid)
            continue
        got = use.get(sid)
        if not got:
            unused.append(sid)
            continue
        want = line_for(sid, got, spec)
        if scenes[sid].get("use") != want:
            changed.append(sid)
            scenes[sid]["use"] = want

    print("장면 %d · 쓰임을 적을 것 %d" % (len(scenes), len(changed)))
    if orphan:
        print("  manifest 에 있는데 명령어가 없소: %s" % " ".join(orphan))
    if unused:
        print("  아무 화면도 안 부르오: %s" % " ".join(unused))
    for sid in changed:
        print("  · %-9s %s" % (sid, scenes[sid]["use"][:88]))

    if a.write and changed:
        PROMPTS.write_text(
            json.dumps(data, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8")
        print("\n%d 곳에 써넣었소 — %s" % (len(changed), PROMPTS.name))
    elif not a.write:
        print("\n(써넣으려면 --write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
