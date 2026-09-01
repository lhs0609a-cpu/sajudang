# -*- coding: utf-8 -*-
"""
근거 줄이 규칙을 흘리지 않는가.

★ 왜 지키나

  근거는 보이되 **규칙은 감춥니다** (CLAUDE.md). 그런데 훅 근거 줄에

      근거 · 庚일간 · 불 0.2 · 상관
      근거 · 상관 2 · 신강

  처럼 나가고 있었습니다. `f.elements` 는 가중치를 매겨 더한 **안에서
  쓰는 점수**라 사람이 읽을 수 있는 수가 아닙니다. 0.2 를 보면 1.0 은
  뭔지, 몇부터 많은 건지 묻게 되는데 그건 우리 분기표입니다.

  개수(십신이 둘)는 셀 수 있는 사실이라 냅니다. 다만 「상관 2」는
  분기표처럼 보이고 「상관이 둘」은 근거로 읽힙니다.
"""
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine.bank import build_hook            # noqa: E402
from engine.calendar import build_chart       # noqa: E402
from engine.features import build_features    # noqa: E402

CONCERNS = ["money", "work", "love", "people", "dir", "health"]


def _sources(n=200):
    rng = random.Random(20260901)
    for _ in range(n):
        c = build_chart(rng.randint(1960, 2006), rng.randint(1, 12),
                        rng.randint(1, 28), rng.randint(0, 23), 0,
                        rng.choice("FM"), True)
        f = build_features(c)
        for seg in build_hook(f, rng.choice(CONCERNS)):
            s = seg.get("source")
            if s:
                yield s


def test_no_number_in_source():
    """점수도 개수도 숫자로는 안 나간다."""
    bad = sorted({s for s in _sources() if re.search(r"[0-9]", s)})
    assert not bad, "근거 줄에 숫자가 있다:\n  " + "\n  ".join(bad[:8])


def test_no_operator_or_threshold():
    """연산자·문턱값은 분기표다."""
    bad = sorted({s for s in _sources()
                  if re.search(r"[<>≤≥=]|이상|이하|미만|초과", s)})
    assert not bad, "근거 줄에 규칙이 있다:\n  " + "\n  ".join(bad[:8])


def test_particles_are_right():
    """「이(가)」 같은 표기가 그대로 나가지 않는다."""
    bad = sorted({s for s in _sources() if "(가)" in s or "(이)" in s})
    assert not bad, "조사가 안 붙었다:\n  " + "\n  ".join(bad[:8])
