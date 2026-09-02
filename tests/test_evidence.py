"""
근거가 근거 노릇을 하는가 — 잠금.

★ 왜 세는 자리가 여기인가

  근거 줄을 처음 재었을 때 이랬습니다 —

      관측  87.6%    여덟 글자에서 무엇을 읽었는지
      이치   0.0%    그것을 **어떤 규칙**으로 읽었는지
      출처   9.2%

  열에 여덟이 읽은 것을 나열했을 뿐이라, 손님은 「그래서 뭐」 라고
  물었습니다. 관측만 대면 그건 근거가 아니라 **자료**입니다.

★ 가짓수 말고 **뜨는 횟수**로 셉니다

  가짓수로 재면 한 번 나오는 긴 줄과 백 번 나오는 짧은 줄이 같은
  한 표입니다. 그렇게 재어 「47% 붙었다」 고 했는데, 손님 눈에 뜨는
  횟수로 다시 재니 **52%가 이치 없이** 나가고 있었습니다.
  남은 것이 짧고 자주 나오는 줄에 몰려 있었기 때문입니다.

★ 「과학적으로 입증」 은 못 씁니다

  사주는 검증된 적이 없습니다. 그렇게 쓰면 거짓말이고 이 집이
  금지한 것입니다 (docs/11). 회의적인 손님을 설득하는 것은 그 말이
  아니라 **따라갈 수 있는 논증**입니다 — 무엇을 보고, 어떤 이치로,
  그 이치는 어디서 왔는가. 셋이 다 있어야 **어디가 틀렸는지 짚을
  수** 있고, 짚을 수 있는 말이라야 믿을 수 있는 말입니다.
"""
from __future__ import annotations

import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine.bank import build_hook              # noqa: E402
from engine.calendar import build_chart         # noqa: E402
from engine.features import build_features      # noqa: E402
from engine.report import build_report          # noqa: E402

CONCERNS = ["money", "work", "love", "people", "dir", "health"]

# 이치는 **짜임**으로 봅니다 — 관측 뒤에 줄표가 오고 규칙이 옵니다.
# 어미 목록으로 찾으면 「나이대를 가르오」 같은 줄을 놓칩니다.
RULE = re.compile(r"—\s*\S")
SRC = re.compile(r"〔")

# 안에서 쓰는 점수 (`불 0.3`). 손님은 0.3 이 큰지 작은지 모릅니다.
RAW = re.compile(r"\d+\.\d")


def _seen(n: int = 12):
    """실제로 만들어지는 근거 줄을 **뜨는 횟수대로** 모은다."""
    rng = random.Random(20260902)
    out = []
    for _ in range(n):
        f = build_features(build_chart(
            rng.randint(1960, 2006), rng.randint(1, 12), rng.randint(1, 28),
            rng.randint(0, 23), 0, rng.choice("FM"), True))
        concern = rng.choice(CONCERNS)
        out += [s["source"] for s in build_hook(f, concern) if s.get("source")]
        try:
            r = build_report(f, "cid", "pungun", "all", concern, None)
        except Exception:                        # noqa: BLE001
            continue
        out += [c["source"] for c in r.get("cuts", []) if c.get("source")]
    assert out, "근거 줄이 하나도 안 나왔소"
    return out


def test_모든_근거에_이치가_있다():
    """관측만 있는 줄은 「그래서 뭐」 를 부릅니다."""
    bare = [s for s in _seen() if not RULE.search(s)]
    assert not bare, "이치 없는 근거 %d회 — 예: %s" % (
        len(bare), bare[:3])


def test_모든_근거에_출처가_있다():
    """어느 갈래에서 온 규칙인지 댑니다. 쪽수는 지어내지 않습니다."""
    bare = [s for s in _seen() if not SRC.search(s)]
    assert not bare, "출처 없는 근거 %d회 — 예: %s" % (
        len(bare), bare[:3])


def test_원점수가_새지_않는다():
    """`f.elements` 는 가중치를 더한 **분기표**입니다. 밖으로 안 냅니다."""
    leak = [s for s in _seen() if RAW.search(s)]
    assert not leak, "원점수가 샌 근거 %d회 — 예: %s" % (
        len(leak), leak[:3])


def test_출처를_지어내지_않는다():
    """「자평진전 42쪽」 같은 확인 못 할 인용은 거짓과 같습니다."""
    for s in _seen():
        assert not re.search(r"\d+\s*쪽|p\.\s*\d+", s), s


def test_적중률_같은_말을_쓰지_않는다():
    """docs/11 · CLAUDE.md 가 금한 말입니다."""
    for s in _seen():
        for w in ("적중률", "과학적으로", "통계학", "입증"):
            assert w not in s, "%s — %s" % (w, s)
