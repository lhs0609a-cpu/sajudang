# -*- coding: utf-8 -*-
"""
검색엔진에 내놓는 자리 — 주소가 한 벌인가, 닫은 자리를 내놓지 않는가.

★ 2026-09-24. 고유 도메인으로 들어온 손님의 페이지가 **정본은 저쪽이라고**
  말하고 있었습니다 —

      saju.megaload.co.kr 의 canonical → sajudang-three.vercel.app
      saju.megaload.co.kr/sitemap.xml  → vercel.app 주소만 나열
      robots.txt 의 Host·Sitemap      → vercel.app

  같은 예비 주소가 세 파일에 박혀 있었고 `NEXT_PUBLIC_SITE_URL` 이 배포에
  안 걸려 있었습니다. 검색엔진은 그걸 「이 주소는 사본이오」 로 읽습니다 —
  소유 확인을 해도 색인은 저쪽으로 갑니다.

★ 그리고 다섯 화면의 제목이 전부 같았습니다(「성신당 星辰堂」 한 줄).
  사이트맵과 RSS 를 내도 중복으로 접힙니다 — 지도를 그려 놓고 자리마다
  같은 이름을 붙인 셈이오.

여기서 지키는 것
    ① 주소는 `lib/site.ts` 한 자리에서만 온다
    ② 피드·지도는 그 한 벌(`PUBLIC_PAGES`)을 본다
    ③ robots 가 닫은 자리를 지도·피드에 적지 않는다
    ④ 화면마다 제목이 다르다
    ⑤ 피드에 나가는 글도 이 집의 가드를 지난다 (docs/15)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import guard                                # noqa: E402

SITE_TS = (WEB / "lib" / "site.ts").read_text(encoding="utf-8")
FILES = {
    "layout": WEB / "app" / "layout.tsx",
    "robots": WEB / "app" / "robots.ts",
    "sitemap": WEB / "app" / "sitemap.ts",
    "rss": WEB / "app" / "rss.xml" / "route.ts",
}


def _code(src: str) -> str:
    """주석을 걷은 코드만. 머리말은 옛 주소를 **역사로** 적으니 셈에서 뺍니다."""
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", "", src)


#: 이 집의 주소 — 코드에서 이 둘을 손으로 들면 두 벌이 됩니다.
OURS = re.compile(r"vercel\.app|megaload\.co\.kr")


def _pages() -> list:
    """`lib/site.ts` 의 PUBLIC_PAGES 를 읽는다 — 자가 제품 표를 본다."""
    body = SITE_TS.split("PUBLIC_PAGES", 1)[1]
    out = []
    for block in re.finditer(r"\{(.*?)\},", body, re.S):
        chunk = block.group(1)
        path = re.search(r'path:\s*"([^"]+)"', chunk)
        title = re.search(r'title:\s*"([^"]+)"', chunk)
        desc = re.search(r'desc:\s*(?:"([^"]*)"|SITE_DESC)', chunk)
        in_map = re.search(r"inSitemap:\s*(true|false)", chunk)
        if not (path and title):
            continue
        out.append({
            "path": path.group(1),
            "title": title.group(1),
            "desc": (desc.group(1) if desc and desc.group(1) else ""),
            "inSitemap": bool(in_map and in_map.group(1) == "true"),
        })
    assert out, "PUBLIC_PAGES 를 못 읽었소"
    return out


def test_주소는_한_자리에서만_온다():
    """예비 주소 리터럴은 `lib/site.ts` 에만 있어야 하오."""
    bad = []
    for name, path in FILES.items():
        code = _code(path.read_text(encoding="utf-8"))
        if OURS.search(code):
            bad.append(name)
        if "NEXT_PUBLIC_SITE_URL" in code:
            bad.append(name + "(환경변수 직접 읽음)")
        assert "@/lib/site" in code, "%s 가 한 자리에서 안 받소" % name
    assert not bad, "주소를 제 손으로 든 파일: %s" % bad


def test_정본은_고유_도메인이다():
    m = re.search(r'NEXT_PUBLIC_SITE_URL \?\? "([^"]+)"', SITE_TS)
    assert m, "예비 주소를 못 찾겠소"
    assert m.group(1) == "https://saju.megaload.co.kr", m.group(1)
    assert "vercel.app" not in _code(SITE_TS), "예비값이 미리보기 주소요"


def test_지도와_피드가_같은_표를_본다():
    for name in ("sitemap", "rss"):
        src = FILES[name].read_text(encoding="utf-8")
        assert "PUBLIC_PAGES" in src, "%s 가 목록을 제 손으로 적소" % name


def test_닫은_자리를_내놓지_않는다():
    """robots 가 막은 자리가 지도·피드에 있으면 닫아 놓고 안내판을 세운 것이오."""
    robots = FILES["robots"].read_text(encoding="utf-8")
    shut = re.findall(r'"(/[^"]*)"', robots.split("disallow", 1)[1].split("]", 1)[0])
    for page in _pages():
        for closed in shut:
            base = closed.rstrip("/")
            assert not (page["path"] == base or page["path"].startswith(base + "/")), \
                "%s 는 robots 에서 막아 둔 자리요" % page["path"]


def test_화면마다_제목이_다르다():
    titles = [p["title"] for p in _pages()]
    assert len(set(titles)) == len(titles), "제목이 겹치오: %s" % titles
    for p in _pages():
        assert len(p["title"]) >= 4, p
        assert p["desc"] == "" or len(p["desc"]) >= 20, "한 줄이 너무 짧소: %s" % p


@pytest.mark.parametrize("page", _pages(), ids=lambda p: p["path"])
def test_공개_화면에_제목을_다는_자리가_있다(page):
    """`"use client"` 화면은 metadata 를 못 내놓으니 라우트 layout 이 있어야 하오."""
    if page["path"] == "/":
        assert (WEB / "app" / "layout.tsx").exists()
        return
    folder = WEB / "app" / page["path"].strip("/")
    assert (folder / "layout.tsx").exists(), "%s 에 제목을 달 자리가 없소" % page["path"]
    src = (folder / "layout.tsx").read_text(encoding="utf-8")
    assert "export const metadata" in src and "PUBLIC_PAGES" in src


@pytest.mark.parametrize("page", _pages(), ids=lambda p: p["path"])
def test_피드에_나가는_글도_가드를_지난다(page):
    """유입 화면에서 적중률·과학·통계 같은 말을 쓰지 않습니다 (docs/15)."""
    for text in (page["title"], page["desc"]):
        ok, hits = guard.check(text)
        assert ok, "%s: %s ← %s" % (page["path"], text, hits[:1])


def test_피드가_RSS_규격을_갖춘다():
    src = FILES["rss"].read_text(encoding="utf-8")
    for need in ('<rss version="2.0"', "<channel>", "<title>", "<link>",
                 "<description>", "<pubDate>", "<guid", "lastBuildDate",
                 "application/rss+xml"):
        assert need in src, "피드에 %s 가 없소" % need
    assert "esc(" in src, "XML 을 안 감싸면 & 하나에 피드가 깨지오"
