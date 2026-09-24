# -*- coding: utf-8 -*-
"""
가드가 **막을 것만** 막는가 — 낱말 경계까지.

★ 2026-09-24. 부동산을 고른 손님이 위로 자리에서 이 글을 받았습니다 —

      「이 부분은 말씀드릴 수 없소. 다른 자리를 보시겠소?」

  까닭은 바로 앞 문장이었습니다 —

      「이 말로 부동산 걱정이 **사라지는** 것은 아니오.」

  가드 패턴에 든 시킴꼴 「사라」 가 **「사라지는」 한가운데**에 걸린
  것입니다. `guard.enforce` 는 고칠 수 없으면 컷을 통째로 안전 문장으로
  바꾸니, 위로 컷 전문이 거절문으로 나갔습니다 — 명식 넷 × 캐릭터
  다섯을 재 보니 **20/20**이었고, 값을 치르기 전 무료 구간에서도 났습니다.

  한국말은 띄어쓰기로 낱말이 갈립니다. 뒤 글자가 한글이면 그건 다른
  낱말이오 — `engine/terms.WORD_START` 와 같은 규칙입니다.

★ 그리고 **안 하겠다는 말**까지 막으면 지키는 자가 제 집 글을 때립니다.
  「그 집을 사야 하는지는 내가 말하지 않소」 는 이 집이 선을 긋는
  문장인데 (집|땅) 패턴에 걸려 있었습니다.

★ 느슨하게 고치지 않았다는 것을 같이 못 박습니다 — 막아야 하는 열여섯
  줄이 그대로 막힙니다. 이 검사는 **두 쪽을 같이** 봅니다.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import guard                              # noqa: E402

# 막아야 하는 말 — 시점 지시 · 단정 · 검증 불가능한 주장 (docs/11)
BLOCK = [
    "지금 부동산을 사시오.",
    "전세를 빼고 아파트를 사야 하오.",
    "집을 파시오.",
    "땅을 사야 하오.",
    "이 주식을 사시오.",
    "코인에 들어가시오.",
    "올해가 좋으니 상가를 사라.",
    "주식 시기가 좋소.",
    "투자 종목이 유망하오.",
    "이 사주는 반드시 성공합니다.",
    "위암에 걸립니다.",
    "적중률 98%요.",
    "수명이 짧소.",
    "그 사람은 반드시 돌아오오.",
    "이미 다 늦었소.",
    "바꿀 수 없소.",
]

# 통과해야 하는 말 — 낱말 한가운데 · 선을 긋는 말 · 살림의 말
PASS = [
    "이 말로 부동산 걱정이 사라지는 것은 아니오.",
    "전세 걱정이 사라질 것이오.",
    "상가 이야기가 사라지오.",
    "그 집을 사야 하는지는 내가 말하지 않소.",
    "투자를 하는 사람에게도 같은 셈이 서오.",
    "월세로 사는 동안 모은 것이 있소.",
    "땅을 팔라고 한 적 없소.",
    "부동산에서 먼저 볼 것은 감당할 기간이오.",
    "이 집은 어느 자리가 오를지는 보지 않소.",
]


@pytest.mark.parametrize("line", BLOCK)
def test_막아야_하는_말은_막는다(line):
    ok, _ = guard.check(line)
    assert not ok, "가드가 놓쳤소: %s" % line


@pytest.mark.parametrize("line", PASS)
def test_낱말_한가운데와_선_긋는_말은_통과한다(line):
    ok, hits = guard.check(line)
    assert ok, "가드가 제 집 글을 때렸소: %s ← %s" % (line, hits[:1])


def test_위로_컷이_거절문으로_바뀌지_않는다():
    """부동산을 물은 손님의 위로 자리가 살아 있는가 — 컷 단위로."""
    from datetime import date
    import re
    from engine.calendar import build_chart
    from engine.features import build_features
    from engine.report import build_report

    f = build_features(build_chart(1993, 5, 15, 10, 20, "F", True, "서울"),
                       as_of=date(2026, 9, 24))
    for lens_id in ("pungun", "wolha", "haengsu"):
        rep = build_report(f, "guard-test", lens_id, "all", "real_estate", None)
        body = re.sub(r"<[^>]+>", "",
                      "".join(c.get("html", "") for c in rep["cuts"]))
        assert "말씀드릴 수 없" not in body, \
            "%s 의 부동산 리포트가 거절문으로 바뀌었소" % lens_id
