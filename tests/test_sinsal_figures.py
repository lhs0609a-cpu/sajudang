# -*- coding: utf-8 -*-
"""
귀인·살 자리에 **인물이 붙는가.**

★ 손님이 짚은 것 (2026-09-04)

  "금여 양인 문창귀인 태극귀인 이런거 다 이미지 넣어야한다니까 …
  여기에 이미지 명령프롬프트 넣으라니까 왜 안 붙여 화면에."

★ 무엇이 빠져 있었나

  서버는 이름마다 **빈 자리**를 남깁니다 —
  `<div class="ssfig" data-sinsal="taegeuk"></div>` (report.py).
  `SinsalSlots` 가 거기에 포털로 그림을 꽂고, 그림을 누르면 제작
  프롬프트가 뜹니다.

  그런데 **무료 6단(d0)만** 그 부품을 안 쓰고 `innerHTML` 로 부었습니다.
  빈 자리가 빈 채로 남아, 한자만 보였습니다.

  하필 신살은 **무료 컷**입니다. 값을 치르기 전에 태극귀인·문창귀인·
  금여·양인을 만나는 자리가 거기인데, 거기가 제일 허전했습니다.

★ 자리를 내는 곳과 채우는 곳이 갈리면 또 빠집니다

  서버가 자리를 내고 화면이 채웁니다. 둘 중 하나만 고치면 조용히
  빈 채로 나갑니다 — 아무도 안 죽고 화면만 허전합니다. 그래서
  **네 자리 전부**를 셉니다.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine.calendar import build_chart          # noqa: E402
from engine.features import build_features       # noqa: E402
from engine.report import build_report           # noqa: E402

# 신살 컷을 보여 주는 자리 — 전부 그림을 꽂아야 합니다
SHOWS_SINSAL = (
    "app/pay/page.tsx",             # d0 무료 6단  ← 여기가 빠져 있었다
    "app/report/[id]/page.tsx",     # c2 본문
)
# 컴포넌트로 직접 그리는 자리
DRAWS_DIRECT = (
    "app/summary/page.tsx",         # c7 분석지
    "app/s/[token]/SharedView.tsx",  # s1 건너오다
)


def _sinsal_html() -> str:
    f = build_features(build_chart(1993, 11, 25, 15, 55, "M", city="서울"),
                       as_of=date.today())
    rep = build_report(f, "t", "pungun", "free", "work", "INTJ")
    got = [c for c in rep["cuts"] if c["id"] == "sinsal"]
    assert got, "무료 구간에 신살 컷이 없소"
    return got[0]["html"]


def test_the_server_leaves_a_slot_for_every_name():
    """이름마다 빈 자리가 있어야 화면이 꽂을 데가 있다."""
    html = _sinsal_html()
    keys = re.findall(r'data-sinsal="([a-z]+)"', html)
    assert keys, "신살 컷에 인물 자리가 하나도 없소"
    # ★ 이름은 `<b>태극귀인</b>` 도 있고 `<b>양인<i class="gl">(…)</i></b>`
    #   처럼 풀이가 낀 것도 있습니다. 이름 글자로 세지 말고 **카드 수**를
    #   셉니다 — 자리 하나에 카드 하나입니다.
    cards = re.findall(r'<div class="ss ', html)
    assert len(keys) == len(cards), (
        "카드 %d개인데 자리는 %d개요" % (len(cards), len(keys)))


def test_every_slot_has_a_prompt_and_a_placeholder():
    """
    ★ 그림이 아직 없어도 **자리표시**는 떠야 하고, 관리자는 눌러서
      제작 프롬프트를 볼 수 있어야 합니다. 그게 없으면 그림을
      맡길 수가 없습니다.
    """
    keys = set(re.findall(r'data-sinsal="([a-z]+)"', _sinsal_html()))
    figs = json.loads(
        (WEB / "public" / "asset-prompts.json").read_text(encoding="utf-8")
    )["figures"]
    drawn = set(re.findall(
        r"^\s{2}(\w+):\s*\{",
        (WEB / "lib" / "sinsalFigures.ts").read_text(encoding="utf-8"), re.M))
    assert not (keys - set(figs)), "명령어가 없는 자리: %s" % (keys - set(figs))
    assert not (keys - drawn), "자리표시가 없는 자리: %s" % (keys - drawn)


def test_every_screen_that_shows_sinsal_fills_the_slots():
    """
    ★ 이게 이번에 빠졌던 자리입니다. 서버가 자리를 내도 화면이
      `innerHTML` 로만 부으면 빈 채로 남습니다 — 아무도 안 죽고
      화면만 허전합니다.
    """
    for rel in SHOWS_SINSAL:
        src = (WEB / rel).read_text(encoding="utf-8")
        assert "SinsalSlots" in src, "%s 가 인물 자리를 안 채우오" % rel
        assert 'c.id === "sinsal"' in src, "%s 가 신살 컷을 안 가르오" % rel


def test_the_other_screens_draw_the_figure_directly():
    for rel in DRAWS_DIRECT:
        src = (WEB / rel).read_text(encoding="utf-8")
        assert "SinsalFigure" in src, "%s 에 인물이 없소" % rel


def test_the_figure_opens_its_prompt_for_the_owner():
    """
    그림을 맡기려면 그 자리에서 바로 프롬프트가 나와야 합니다.
    도구를 따로 돌려 찾아야 하면 안 찾습니다.
    """
    src = (WEB / "components" / "scene" / "SinsalFigure.tsx").read_text(
        encoding="utf-8")
    assert "PromptModal" in src and 'kind="figure"' in src
