# -*- coding: utf-8 -*-
"""
자들이 **손님이 받는 것과 같은 글**을 재는가.

★ 왜 이 검사를 세우나 (2026-09-27)

  새 자 셋(`dull_audit` · `same_point` · `verdict_mix`)이 훅을
  `bank.build_hook` 으로 재고 있었습니다. 그런데 손님이 보는 훅은
  `routers/hook` 이 만들고, 그 라우터는 네 층을 더 얹습니다 —
  `portrait` · `topic` · `specialist` · 말투.

  `build_hook` 은 분석지(`engine/summary`)와 도구(`engine/screenscan`)만
  쓰는 자리요. 그래서 자가 낸 훅 수치는 **다른 물건의 것**이었고, 씨앗
  55줄을 고쳐 **배포까지 했는데** 손님 화면에는 안 닿았습니다. 그 사이
  자는 「고쳤다」 고 찍었습니다.

  자를 제품보다 좁게 두는 것보다 나쁩니다 — 좁으면 못 보고 끝나지만,
  다른 것을 재면 **고친 줄 알고 넘어갑니다.**

★ 이 검사가 지키는 것

  ① 자들이 `tools/seen_page` 한 자리에서 글을 받는다
  ② 그 조립이 `routers/hook` 과 **같은 함수를 같은 차례로** 부른다
  ③ 라우터가 층을 하나 더 얹으면 여기서 걸린다
"""
from __future__ import annotations

import random
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "services" / "api", ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from tools import seen_page                          # noqa: E402

ROUTER = (ROOT / "services" / "api" / "routers" / "hook.py").read_text("utf-8")
SHARED = (ROOT / "tools" / "seen_page.py").read_text("utf-8")
RULERS = ("dull_audit", "same_point", "verdict_mix")


def _code(src: str) -> str:
    """주석을 걷은 코드만 — 머리말은 옛 이름을 **역사로** 적습니다."""
    src = re.sub(r'"' * 3 + r".*?" + r'"' * 3, "", src, flags=re.S)
    src = re.sub(r"'" * 3 + r".*?" + r"'" * 3, "", src, flags=re.S)
    return re.sub(r"(?m)^\s*#.*$", "", src)


# ══════════════════════════════════════════════════════════
# ① 자들이 한 자리에서 받는가
# ══════════════════════════════════════════════════════════

@pytest.mark.parametrize("name", RULERS)
def test_자는_손님이_보는_글을_잰다(name):
    src = _code((ROOT / "tools" / ("%s.py" % name)).read_text("utf-8"))
    assert "build_hook" not in src, (
        "%s 가 `bank.build_hook` 을 부르오 — 그건 분석지와 도구만 쓰는 "
        "자리요. 손님 훅은 `first_reading` 이오" % name)
    assert "build_first_reading" in src or "seen_page" in src, (
        "%s 가 손님이 보는 훅을 안 부르오" % name)


# ══════════════════════════════════════════════════════════
# ② 조립이 라우터와 같은가
# ══════════════════════════════════════════════════════════

#: 라우터가 훅에 얹는 층. 하나라도 빠지면 자가 다른 물건을 잽니다.
LAYERS = ("build_first_reading", "portrait_mod.build", "topic_mod.ask_cut",
          "voice_mod.speak", "voice_mod.address")


@pytest.mark.parametrize("call", LAYERS)
def test_라우터가_얹는_층을_다_얹는다(call):
    assert call in _code(ROUTER), "라우터가 %s 를 안 부르오 — 검사를 고치시오" % call
    assert call in _code(SHARED), (
        "`tools/seen_page` 가 %s 를 안 얹소 — 자가 손님보다 적게 봅니다" % call)


def test_전문_판단도_얹는다():
    """캐릭터별 전문 판단(`character_consultation.brief`)이오."""
    assert "character_consultation_mod.brief" in _code(ROUTER)
    assert "_cc.brief" in _code(SHARED) or "character_consultation" in _code(SHARED)


def test_사람_그리기가_맨_앞이다():
    """
    ★ `portrait` 은 **맨 앞**입니다 (라우터 `segs.insert(0, …)`).

      손님이 먼저 바라는 것은 판정이 아니라 **알아봐 주는 것**이오
      (2026-09-24). 차례가 바뀌면 첫 화면이 다른 글이 되니, 자가 재는
      「첫 화면」 도 딴것이 됩니다.
    """
    rng = random.Random(20260927)
    f = seen_page.sample(rng, hour_known=True)
    for concern in ("money", "love", "real_estate"):
        stages = seen_page.free_page(f, concern, "ESTJ",
                                     lens_id="nopa")["hook_stages"]
        assert stages[0] == "portrait", (concern, stages)
        # 판정 마디는 그 뒤에 섭니다.
        assert "0" in stages, stages


def test_말투가_마지막_층이다():
    """
    ★ 말투는 **맨 끝**입니다. 그 앞에서 자가 글을 집으면 하오체만 봅니다 —
      스무 명이 다 다른 말을 하는데 자는 한 벌만 재게 되오.
    """
    rng = random.Random(7)
    f = seen_page.sample(rng, hour_known=True)
    hao = seen_page.free_page(f, "money", None, lens_id="nopa")
    hae = seen_page.free_page(f, "money", None, lens_id="eunbyeol")
    a = seen_page.plain(hao["blocks"][0]["html"])
    b = seen_page.plain(hae["blocks"][0]["html"])
    assert a != b, "말투 층이 안 걸렸소 — 두 캐릭터가 글자 그대로 같소"


# ══════════════════════════════════════════════════════════
# ③ 받는 글이 멀쩡한가
# ══════════════════════════════════════════════════════════

def test_손님이_받는_글이_비지_않는다():
    rng = random.Random(11)
    from typing import get_args

    from schemas.api import Concern
    for concern in get_args(Concern):
        f = seen_page.sample(rng, hour_known=True)
        pg = seen_page.free_page(f, concern, "ESTJ", lens_id="nopa")
        assert pg["blocks"], concern
        assert pg["locked"], "%s — 잠긴 컷이 하나도 없소" % concern
        for b in pg["blocks"]:
            assert seen_page.plain(b["html"]), (concern, b["where"])


def test_받는_글이_가드를_지난다():
    """
    ★ 자를 제품에 맞추자마자 `first_reading` 의 **가드 위반 한 줄**이
      드러났습니다 — 금지어 「끝났다」에 걸려 그 컷이 통째로 안전
      문장으로 바뀌고 있었습니다 (일지가 충인 사람의 사랑·사람 고민).
      자가 그 글을 한 번도 안 봤기 때문이오.
    """
    from engine import guard
    rng = random.Random(20260927)
    bad = []
    for _ in range(12):
        f = seen_page.sample(rng)
        for concern in ("love", "people"):
            pg = seen_page.free_page(f, concern, None, lens_id="nopa")
            for b in pg["blocks"]:
                ok, hits = guard.check(seen_page.plain(b["html"]))
                if not ok:
                    bad.append((concern, b["where"], hits[:1]))
    assert not bad, "손님이 받는 글이 가드에 걸리오: %s" % bad[:3]


# ══════════════════════════════════════════════════════════
# ④ 첫 화면과 풀이가 같은 글을 두 번 내지 않는가
# ══════════════════════════════════════════════════════════

def test_사람_그리기가_두_번_안_나온다():
    """
    ★ 훅의 `portrait` 과 풀이의 `portrait` 이 **앞 세 면을 겹쳐** 냈습니다
      (2026-09-27). 제목도 근거 줄도 같았습니다 — 손님이 첫 화면에서 읽은
      364자를 일곱째 컷에서 다시 읽었습니다.

      라우터에는 「값을 치르기 전에 세 면을 보여 줍니다. **나머지는
      풀이에 있소**」 라고 적혀 있었습니다. 뜻은 맞는데 수가 두 벌
      (훅 3 · 풀이 6)이라 지켜지지 않았습니다. 이제 `HOOK_FACES` 하나요.
    """
    from engine import portrait as P
    rng = random.Random(20260927)
    for lens_id in ("nopa", "eunbyeol", "dongja", "pungun"):
        f = seen_page.sample(rng, hour_known=True)
        front = P.build(f, lens_id, P.HOOK_FACES)
        rest = P.build(f, lens_id, 5, skip=P.HOOK_FACES)
        assert front and rest, lens_id
        both = set(front["facets"]) & set(rest["facets"])
        assert not both, "%s — 같은 면을 두 번 그리오: %s" % (lens_id, both)
        assert len(rest["facets"]) >= 3, (
            "%s — 풀이가 펼 면이 %d개뿐이오. `VIEW` 꼬리가 안 붙었소"
            % (lens_id, len(rest["facets"])))


def test_손님이_받는_글에_같은_면이_두_번_안_선다():
    """조립된 한 장에서 실제로 재 봅니다 — 면 머리말이 두 번 서는가."""
    from engine import portrait as P
    rng = random.Random(5)
    for concern in ("money", "love", "work"):
        f = seen_page.sample(rng, hour_known=True)
        pg = seen_page.free_page(f, concern, "ESTJ", lens_id="nopa")
        whole = " ".join(seen_page.plain(b["html"]) for b in pg["blocks"])
        twice = [h for h in P.HEAD.values() if whole.count(h) > 1]
        assert not twice, "%s — 같은 면 머리말이 두 번 서오: %s" % (concern, twice)


# ══════════════════════════════════════════════════════════
# ⑤ 말투를 끈 글이 **어미만** 다른가
# ══════════════════════════════════════════════════════════

def test_말투를_끈_글이_어미만_다르다():
    """
    ★ `verdict_mix` 는 갈래를 **하오체 한 벌**로 셉니다 (`hao_only`).
      그 문이 어미 말고 다른 것까지 바꾸면, 자는 다시 딴 물건을 잽니다 —
      이 집이 오늘 고친 그 사고요.

      그래서 여기서 셋을 봅니다 — 컷 수 · 컷 차례 · 글자 수(±3%).
    """
    rng = random.Random(20260927)
    for lens_id in ("nopa", "eunbyeol", "dongja"):
        f = seen_page.sample(rng, hour_known=True)
        on = seen_page.free_page(f, "money", "ESTJ", lens_id=lens_id)
        off = seen_page.free_page(f, "money", "ESTJ", lens_id=lens_id,
                                  voice_on=False)
        assert [b["where"] for b in on["blocks"]] == \
               [b["where"] for b in off["blocks"]], lens_id
        # 잠긴 목록도 맛보기·근거 줄이 말투를 탑니다 — **고른 컷**만 댑니다.
        key = lambda ls: [(l["id"], l["need_tier"], l["chars"]) for l in ls]
        assert key(on["locked"]) == key(off["locked"]), lens_id
        a = sum(len(seen_page.plain(b["html"])) for b in on["blocks"])
        c = sum(len(seen_page.plain(b["html"])) for b in off["blocks"])
        assert abs(a - c) <= a * 0.03, (
            "%s — 말투를 끄니 글자가 %d → %d 로 움직였소. 어미보다 "
            "많이 바뀌었소" % (lens_id, a, c))


def test_말투_층은_기본으로_걸린다():
    """★ `voice_on` 의 기본값이 True 여야 하오. 꺼진 채로 두면 자가 늘 하오체만 봅니다."""
    rng = random.Random(1)
    f = seen_page.sample(rng, hour_known=True)
    on = seen_page.free_page(f, "money", None, lens_id="nopa")
    off = seen_page.free_page(f, "money", None, lens_id="nopa", voice_on=False)
    assert seen_page.plain(on["blocks"][0]["html"]) != \
        seen_page.plain(off["blocks"][0]["html"]), "말투 층이 기본으로 안 걸리오"
