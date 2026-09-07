# -*- coding: utf-8 -*-
"""
제작 명령어는 **주인만** 보는가.

★ 손님이 물은 것 (2026-09-07)
  "그림파일은 없고 명령어는 다 클릭하면 보이게 했어?"

  열넷 다 보였습니다 — 그림·모션 둘 다 빠진 것이 없었습니다.
  그런데 재 보니 **손님에게도 보였습니다.**

★ 무엇이 새고 있었나

  장면(Scene)과 캐릭터(CharArt)는 `admin` 을 보고 막아 두었는데
  **신살 인물만 안 막혀 있었습니다.** 손님이 카드를 누르면 영어
  제작 명령어가 그대로 떴습니다 — 사주를 보러 온 사람에게 집의
  작업 지시서가 열리는 셈입니다.

★ 왜 검사로 잠그나

  명령어를 여는 자리가 넷입니다(장면·캐릭터·신살 인물·자산 판).
  하나만 빠져도 조용히 샙니다 — 아무도 안 죽고 손님만 봅니다.
  다섯 번째 자리가 생겨도 여기서 걸립니다.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"

# 명령어를 여는 자리와, 그 자리가 주인을 어떻게 보는가
GATES = {
    "components/scene/Scene.tsx": "scene",
    "components/CharArt.tsx": "char",
    "components/scene/SinsalFigure.tsx": "figure",
}
# 자산 판은 주인 화면(/admin) 안에서만 그려집니다 — 거기서 또 막을
# 까닭이 없습니다. 대신 **주인 화면 밖에 안 걸렸는지**를 봅니다.
BOARD = "components/AssetBoard.tsx"


def _src(rel: str) -> str:
    return (WEB / rel).read_text(encoding="utf-8")


def _bare(src: str) -> str:
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    return re.sub(r"//[^\n]*", " ", src)


@pytest.mark.parametrize("rel,kind", sorted(GATES.items()))
def test_명령어는_주인만_연다(rel, kind):
    src = _bare(_src(rel))
    assert "useSession" in src and "st.admin" in src, (
        "%s 가 주인인지 안 보오" % rel)
    # ★ **창 바로 앞**에 빗장이 있어야 하오.
    #
    #   여는 손잡이만 막으면 다음 사람이 손잡이를 하나 더 달 때
    #   조용히 새오. 창 자체가 주인을 봐야 하오.
    i = src.find("<PromptModal")
    assert i > 0, "%s 에 명령어 창이 없소" % rel
    head = re.sub(r"\s+", " ", src[max(0, i - 90):i])
    assert re.search(r"\{\s*admin\s*&&", head), (
        "%s 가 창에 빗장을 안 걸었소: …%s" % (rel, head[-70:]))


@pytest.mark.parametrize("rel", sorted(GATES))
def test_손님에게는_누를_수_있다는_표도_안_낸다(rel):
    """
    ★ 표를 내면 손님은 누릅니다. 누르면 아무 일도 안 일어나고,
      그건 죽은 버튼입니다 — 이 집이 안 두는 것이오.
    """
    src = _bare(_src(rel))
    for attr in ('role="button"', "tabIndex={0}"):
        if attr in src:
            i = src.find(attr)
            head = src[max(0, i - 260):i]
            assert "admin" in head, "%s 의 %s 가 손님에게도 보이오" % (rel, attr)


def test_자산_판은_주인_화면_안에서만_그린다():
    hits = []
    for p in (WEB / "app").rglob("*.tsx"):
        if "AssetBoard" in p.read_text(encoding="utf-8"):
            hits.append(p.relative_to(WEB).as_posix())
    assert hits == ["app/admin/page.tsx"], "자산 판이 딴 데도 걸렸소: %s" % hits


def test_모든_신살에_명령어가_있다():
    """
    ★ 하나라도 비면 그 카드만 눌러도 빈 창이 뜹니다.
      그림 파일은 아직 없어도 **명령어는 다 있어야** 그림을 맡길 수
      있습니다.
    """
    import json

    figs = json.loads(
        (WEB / "public" / "asset-prompts.json").read_text(encoding="utf-8")
    )["figures"]
    drawn = set(re.findall(
        r"^\s{2}(\w+):\s*\{",
        (WEB / "lib" / "sinsalFigures.ts").read_text(encoding="utf-8"), re.M))
    assert drawn, "자리표시가 하나도 없소"
    missing = sorted(drawn - set(figs))
    assert not missing, "명령어가 없는 신살: %s" % missing
    empty = sorted(k for k in drawn
                   if not (figs[k].get("image") or "").strip()
                   or not (figs[k].get("motion") or "").strip())
    assert not empty, "명령어가 빈 신살: %s" % empty
