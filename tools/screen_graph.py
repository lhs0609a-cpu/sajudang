"""
화면 연결 그래프 — 고아 화면 · 막다른 화면 · 죽은 버튼 찾기.

    python tools/screen_graph.py

T4-3 의 통과 기준입니다.

    고아 화면   어디서도 갈 수 없는 화면
    막다른 화면  나갈 수 없는 화면
    죽은 버튼   onClick 도 href 도 없는 button

화면은 각 page.tsx 상단 주석의 `@screen a1 a2 ...` 태그로 셉니다.
docs/08 의 SCREEN_MAP 과 어긋나면 실패합니다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "web" / "app"

# docs/08 §1 의 화면 대장 — 라우트마다 어떤 화면이 들어 있어야 하는가
SCREEN_MAP = {
    "/": ["a1", "a2", "a3", "a4", "a4b", "a5", "a6", "a7"],
    "/lobby": ["b1", "b2", "b3", "b4"],
    "/report/[id]": ["c1", "c2", "c3", "c4", "c5", "c6"],
    "/pay": ["d0", "d1", "d2", "d3"],
    "/summary": ["c7", "c8"],
    "/s/[token]": ["s1", "s2"],
    "/relay": ["h1"],
    "/daily": ["g1", "g2", "g3"],
    "/me": ["f2", "r1"],
}
EXPECTED_SCREENS = [s for v in SCREEN_MAP.values() for s in v]


def normalize(target: str, routes) -> str:
    """"/report/" + id 처럼 이어붙인 경로를 실제 라우트로 맞춘다."""
    t = target.split("?")[0].rstrip("/") or "/"
    if t in routes:
        return t
    for r in routes:
        # /report/[id] ← /report
        if r.endswith("]") and r.rsplit("/", 1)[0] == t:
            return r
    return t


def route_of(page: Path) -> str:
    rel = page.relative_to(APP).parent.as_posix()
    rel = re.sub(r"\((.*?)\)/?", "", rel)          # (group) 은 URL 에 안 들어간다
    return "/" + ("" if rel in (".", "") else rel)


def scan() -> tuple[dict, list, list]:
    pages = sorted(APP.rglob("page.tsx"))
    routes = {route_of(p): p for p in pages}

    edges: dict[str, set] = {r: set() for r in routes}
    dead_buttons: list[str] = []
    tabs: dict[str, set] = {}

    for route, path in routes.items():
        # page.tsx 가 얇은 서버 껍데기이고 알맹이가 형제 파일에 있는 경우가 있다
        # (예: /s/[token] 의 SharedView.tsx). 같은 폴더의 .tsx 를 함께 본다.
        src = "\n".join(f.read_text(encoding="utf-8")
                        for f in sorted(path.parent.glob("*.tsx")))

        # 라우트 이동
        for pat in (r'router\.push\(\s*"([^"]+)"', r'href="([^"]+)"'):
            for m in re.finditer(pat, src):
                edges[route].add(normalize(m.group(1), routes))
        if "router.back()" in src:
            edges[route].add("__back__")

        # 그 파일이 스스로 밝힌 화면 (@screen 태그)
        m = re.search(r"@screen\s+([a-z0-9 ]+)", src)
        tabs[route] = set(m.group(1).split()) if m else set()

        # 죽은 버튼 — onClick 도 disabled 도 없는 button 태그
        for m in re.finditer(r"<button\b([^>]*)>", src, re.S):
            attrs = m.group(1)
            if "onClick" not in attrs and "disabled" not in attrs:
                line = src[:m.start()].count("\n") + 1
                dead_buttons.append("%s:%d" % (path.relative_to(ROOT), line))

    return edges, dead_buttons, sorted(tabs.items())


def main() -> int:
    if not APP.exists():
        print("apps/web/app 이 없습니다.")
        return 1

    edges, dead_buttons, tabs = scan()
    routes = set(edges)

    incoming: dict[str, int] = {r: 0 for r in routes}
    for src, dsts in edges.items():
        for d in dsts:
            if d in incoming and d != src:
                incoming[d] += 1

    # 바깥에서 링크로 바로 들어오는 화면은 고아가 아니다
    ENTRY_POINTS = {"/", "/s/[token]"}
    orphans = [r for r, n in incoming.items() if n == 0 and r not in ENTRY_POINTS]
    dead_ends = [r for r, d in edges.items() if not (d - {r})]

    print("라우트 %d개" % len(routes))
    for r in sorted(routes):
        out = sorted(x for x in edges[r] if x != r)
        print("  %-16s → %s" % (r, ", ".join(out) or "(없음)"))

    print("\n화면 (@screen 태그)")
    total_tabs = 0
    for r, names in tabs:
        got = sorted(names)
        total_tabs += len(got)
        print("  %-16s %s" % (r, " ".join(got)))

    print("\n화면 수  %d / %d (docs/08 §1)" % (total_tabs, len(EXPECTED_SCREENS)))

    fail = False
    print("\n검사")
    if orphans:
        print("  [FAIL] 고아 화면: %s" % ", ".join(sorted(orphans)))
        fail = True
    else:
        print("  [OK] 고아 화면 0")

    if dead_ends:
        print("  [FAIL] 막다른 화면: %s" % ", ".join(sorted(dead_ends)))
        fail = True
    else:
        print("  [OK] 막다른 화면 0")

    if dead_buttons:
        print("  [FAIL] 죽은 버튼 %d개" % len(dead_buttons))
        for b in dead_buttons:
            print("        %s" % b)
        fail = True
    else:
        print("  [OK] 죽은 버튼 0")

    covered = set()
    for _, names in tabs:
        covered |= names
    missing = [x for x in EXPECTED_SCREENS if x not in covered]
    if missing:
        print("  [FAIL] 구현이 확인되지 않은 화면: %s" % ", ".join(missing))
        fail = True
    else:
        print("  [OK] docs/08 의 %d개 화면 전부 확인" % len(EXPECTED_SCREENS))

    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
