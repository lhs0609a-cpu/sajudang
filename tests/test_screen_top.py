# -*- coding: utf-8 -*-
"""
다음 화면은 **맨 위부터** 뜨는가.

★ 손님이 짚은 것 (2026-09-07)

  "「이 이름으로 하겠습니다」 하면 다음 페이지가 중간부터 떠.
   모든 버튼은 다음 단계 첫 화면부터 떠야 해. 전수점검해 봐."

★ 왜 그랬나

  한 주소 위에 여러 화면이 있는 자리가 여섯입니다 —

      /         a1~a7   `go()`
      /lobby    b1~b4   `setTab`
      /report   c1~c7   `setTab`
      /pay      d0~d3   `step`
      /me       r1·f2   `setTab`
      /legal    약관 셋  `setTab`

  이런 자리는 주소가 안 바뀌니 브라우저가 스크롤을 안 되돌립니다.
  긴 화면을 끝까지 내려 버튼을 누르면 다음 화면이 **그 높이에서**
  시작합니다.

★ 낱개로 안 고칩니다

  여섯 파일에 흩어져 있고 버튼은 계속 늘어납니다. 모든 화면이
  `Shell` 을 지나고 `Shell` 은 그 화면의 **이름**을 들고 있으니,
  이름이 바뀔 때 한 자리에서 올립니다.

  그러니 이 검사가 볼 것은 둘입니다 —
    ① `Shell` 이 정말 올리는가
    ② 화면마다 **이름을 달았는가** (안 달면 안 걸립니다)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"

# 한 주소 위에 여러 화면이 있는 자리
MULTI = (
    "app/page.tsx",
    "app/lobby/page.tsx",
    "app/report/[id]/page.tsx",
    "app/pay/page.tsx",
    "app/me/page.tsx",
)


def _src(rel: str) -> str:
    return (WEB / rel).read_text(encoding="utf-8")


def _bare(src: str) -> str:
    """주석을 걷습니다 — 주석에 적힌 말은 코드가 아닙니다."""
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    return re.sub(r"//[^\n]*", " ", src)


def test_shell_이_화면_이름이_바뀌면_맨_위로_올린다():
    """
    ★ 이게 이번에 비어 있던 자리입니다. 여기가 없으면 여섯 자리가
      전부 중간부터 뜹니다.
    """
    src = _bare(_src("components/Shell.tsx"))
    got = re.search(
        r"useEffect\(\(\)\s*=>\s*\{[^}]*window\.scrollTo\([^)]*\)[^}]*\}"
        r"\s*,\s*\[\s*screen\s*\]\s*\)", src, re.S)
    assert got, "Shell 이 화면 이름이 바뀔 때 맨 위로 안 올리오"
    assert "behavior: \"auto\"" in got.group(0), (
        "부드럽게 올리면 긴 리포트를 거슬러 오르며 어지럽소")


@pytest.mark.parametrize("rel", MULTI)
def test_한_주소_위의_화면은_다_이름을_달았다(rel):
    """
    ★ 이름이 없으면 `Shell` 이 못 알아보고 안 올립니다.

      로딩·오류 자리(Suspense fallback 과 「읽다」)는 뺍니다 — 손님이
      머무는 화면이 아니라 스쳐 가는 자리요.
    """
    src = _src(rel)
    bad = []
    for m in re.finditer(r"<Shell\b([^>]*)>", src):
        attrs = m.group(1)
        if "screen=" in attrs:
            continue
        head = src[:m.start()]
        # Suspense 의 임시 화면과 오류·로딩 자리는 셈에서 뺍니다
        if "fallback={" in src[max(0, m.start() - 80):m.start()]:
            continue
        if '"읽다"' in attrs or "대문을 여는 중" in src[m.end():m.end() + 120]:
            continue
        bad.append(attrs.strip()[:60])
    assert not bad, "%s 에 이름 없는 화면: %s" % (rel, bad)


def test_약관_세_칸은_제_손으로_올린다():
    """
    약관은 연출 자가 세는 화면이 아니라 이름이 없소. 그러니 여기만은
    제 손으로 올려야 하오 — 세 칸이 길어서 아래까지 읽고 다른 칸을
    누르면 그 높이에서 시작했소.
    """
    src = _bare(_src("app/legal/page.tsx"))
    i = src.find("setTab(t)")
    assert i > 0, "약관에 칸을 바꾸는 자리가 없소"
    assert "window.scrollTo" in src[i:i + 300], "약관이 맨 위로 안 올리오"


def test_진입_흐름은_두_번_뛰지_않는다():
    """
    ★ `go()` 가 `scroll: false` 로 두는 까닭을 지킵니다.

      여기서도 올리면 주소가 바뀔 때 브라우저가 한 번, `Shell` 이
      또 한 번 올려 **두 번 뜁니다.** 올리는 일은 한 자리가 맡습니다.
    """
    src = _bare(_src("app/page.tsx"))
    i = src.find('router.replace("/?step="')
    assert i > 0, "진입 흐름에 주소를 따라가는 자리가 없소"
    assert "scroll: false" in src[i:i + 120], (
        "진입 흐름이 스크롤을 또 건드리오 — Shell 과 두 번 뛰오")
