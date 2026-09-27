# -*- coding: utf-8 -*-
"""
컷 제목이 **범주가 아니라 주장**인가 · 그리고 어미를 달지 않았는가.

★ 왜 이 검사를 세우나 (2026-09-27 · docs/45 §9 ⑦)

  잠긴 컷 일곱의 제목이 「1 · 없는 것부터」 「4 · 지금 어디에」 였습니다.
  그건 **값을 부르는 표면**이오 — 손님이 값을 치를지 정할 때 읽는 것이
  제목과 맛보기 한 줄뿐인데, 제목이 목차였습니다.

★ 그리고 제목은 **표지판**이라 `voice` 층을 안 탑니다 (`report` 가
  `html` 과 `source` 만 갈아 끼웁니다). 「…굳소」 라 적으면 스무 명이
  전부 하오체로 그 한 줄을 말하게 되오 — 반말 캐릭터에게서도요.
  이 집이 「이게 무슨 말이네요」 로 한 번 겪은 자리입니다.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "services" / "api", ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine import claim as C                        # noqa: E402
from tools import seen_page                          # noqa: E402

#: 주장 제목을 다는 잠긴 컷. 여기 든 것은 **목차로 돌아가면 안 됩니다.**
CLAIMED = ("lack", "why", "place", "daeun_now", "yongsin", "daeun_map",
           "concern", "rarity", "sinsal", "helper", "ancestor")

#: 말의 어미. 표지판에 붙으면 스무 명이 한 목소리로 그 줄을 말합니다.
TAIL = ("시오", "하오", "이오", "소.", "네.", "요.", "습니다", "세요",
        "보오", "보게", "보지", "해요", "이야", "거야")


def _people(n: int = 8):
    rng = random.Random(20260927)
    return [seen_page.sample(rng, hour_known=True) for _ in range(n)]


@pytest.mark.parametrize("cut_id", CLAIMED)
def test_제목에_말의_어미가_없다(cut_id):
    for f in _people():
        t = (C.rarity(f, "드묾", 120) if cut_id == "rarity"
             else C.title(cut_id, f, "", "money"))
        if not t:
            continue
        assert not t.rstrip().endswith(TAIL), (cut_id, t)


@pytest.mark.parametrize("cut_id", CLAIMED)
def test_제목에_번호가_안_붙는다(cut_id):
    """「1 · 」 「4 · 」 같은 목차 번호요."""
    import re
    for f in _people():
        t = (C.rarity(f, "흔함", 1200) if cut_id == "rarity"
             else C.title(cut_id, f, "", "money"))
        if t:
            assert not re.match(r"^\d+\s*·", t), (cut_id, t)


def test_세는_값이_든다():
    """
    ★ 「없는 것부터」 는 틀릴 수가 없소. 제목에서 이미 대 볼 수 있어야
      그 아래 글도 대 볼 수 있다고 믿습니다.
    """
    import re
    need = ("lack", "why", "place", "daeun_now", "daeun_map", "sinsal",
            "helper", "ancestor")
    for f in _people(6):
        for cut_id in need:
            t = C.title(cut_id, f, "", "money")
            if not t:
                continue
            # 「안 보임」 도 셈이오 — 0 은 빈칸이 아니라 값입니다.
            # 간지 글자도 **대 볼 수 있는 것**이오 (「년주 乙卯」).
            assert re.search(r"\d|[한두세네] 자|안 보임|없음|없는|하나도"
                             r"|[一-鿿]", t), (cut_id, t)


def test_표에_칸이_없으면_옛_제목을_낸다():
    """★ 칸을 지어내는 것보다 목차가 낫소."""
    class Bare:
        pass
    assert C.title("lack", Bare(), "1 · 없는 것부터") == "1 · 없는 것부터"
    assert C.title("없는컷", Bare(), "그대로") == "그대로"


def test_희소도는_띠를_그대로_말한다():
    """
    ★ 골라 담지 않습니다 — 흔하면 흔하다고. 드문 쪽만 말하면 화면에
      남는 숫자가 전부 드물어 보이오.
    ★ 열쇠는 `engine/rarity` 가 내는 그 띠 이름이오. 처음에 영어로
      적었더니 한 칸도 안 걸려 옛 제목이 그대로 나갔습니다.
    """
    from engine import rarity as R
    bands = set()
    rng = random.Random(3)
    for _ in range(60):
        f = seen_page.sample(rng)
        bands.add(R.look(f).get("band"))
    assert bands, "띠가 하나도 안 나왔소"
    for b in bands:
        assert b in C.RARITY, "띠 「%s」 가 제목 표에 없소" % b
    # 표본에 수가 없으면 띠만 냅니다 — 지어내지 않소.
    assert C.rarity(None, "드묾", None) == "같은 배치가 드문 자리"
    assert C.rarity(None, "", None) == ""


def test_조사를_손으로_박지_않는다():
    """
    ★ 처음에 「받침이 돈·일·몸이면 을」 이라 적었는데 **사람 · 부동산 ·
      갈 곳**이 다 받침이오 — 「사람를」 이 나갈 자리였습니다.
    """
    for f in _people(3):
        for cid in C.CONCERN_WORD:
            t = C.concern(f, cid)
            if t:
                assert "를 물었을" not in t or t.startswith("사랑를") is False
                assert "사람를" not in t and "부동산를" not in t, t


# ══════════════════════════════════════════════════════════
# 일곱 갈래의 **꼴**이 같은가 (워크북)
# ══════════════════════════════════════════════════════════

def test_워크북_일곱_갈래가_같은_꼴이다():
    """
    ★ 부동산 줄만 꼴이 달랐습니다 (2026-09-27) —

        제목    여섯은 **장면**이오 (「일은 끝났는데, … 바빠지는 날」).
                부동산만 시킴이었습니다 (「… 분리해 보시오」).
        꺼낼 말  여섯은 **그대로 쓸 수 있는 따온 말**이오.
                부동산만 숙제였습니다 (「… 하나를 적으시오」).

      그러니 부동산을 고른 손님만 장면 없이 시작해 할 말도 못 받았습니다.
      일곱째 칸을 열고 표를 안 채운 그 자리요.
    """
    from engine.reading_precision import CASES
    from typing import get_args

    from schemas.api import Concern
    assert set(CASES) == set(get_args(Concern)), set(CASES) ^ set(get_args(Concern))
    assert len({len(r) for r in CASES.values()}) == 1
    for c, row in CASES.items():
        title, _, _, _, words, _ = row
        assert not title.rstrip(".").endswith(("보시오", "하시오", "적으시오",
                                               "마시오")), \
            "%s 제목이 장면이 아니라 시킴이오: %s" % (c, title)
        assert words.lstrip().startswith("“"), \
            "%s 의 「꺼낼 말」 이 따온 말이 아니오: %s" % (c, words[:40])


def test_워크북_표지판에_어미가_없다():
    """
    ★ `<h3>` 여덟 가운데 셋이 「…보시오」 였고, 그것이 `voice` 층을 타서
      합쇼체 캐릭터에게서 「대조하십시오」 가 됐습니다. 표지판은 말이
      아니니 어느 말투에도 안 걸리는 꼴이어야 하오.
    """
    import re
    src = (ROOT / "services" / "api" / "engine"
           / "reading_precision.py").read_text("utf-8")
    heads = re.findall(r"\(\s*'([^']{2,40})',\s*(?:distinction|diagnosis|a|b"
                       r"|words|review|facts)", src)
    assert heads, "표지판을 못 찾았소 — 검사를 고치시오"
    for h in heads:
        assert not h.endswith(("시오", "하오", "이오", "보오")), h
