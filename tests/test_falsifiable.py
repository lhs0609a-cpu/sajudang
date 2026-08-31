"""
틀릴 수 있는 말인가 — 문장이 무언가를 **금지**하는가.

★ "당신은 때때로 외롭다" 는 아무 관찰도 금지하지 않습니다. 어떤 결과가
  나와도 살아남으니 틀릴 수가 없고, 그래서 '맞다' 는 나와도 '소름 돋는다'
  는 안 나옵니다. 놀라움은 **틀릴 수도 있었는데 맞았을 때**만 옵니다.
  값을 치르는 순간이 그 순간입니다. (CLAUDE.md — 틀릴 수 없는 말 금지)

★ 재보니 리포트 컷 **쉰 개가 금지하는 문장을 하나도 안 담고** 있었습니다.
  관점 컷 대부분이 거기 있었습니다 — 값을 치른 사람이 읽는 자기 몫입니다.
  이 집은 셀 수 있는 것을 이미 갖고 있었습니다: 대운이 바뀌는 나이(절입
  까지의 실제 일수로 계산) · 십신 개수 · 오행 개수. 안 쓰고 있었을 뿐입니다.

  tools/falsifiable.py 가 같은 것을 잽니다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

import pytest                                       # noqa: E402

from engine import lens as lens_mod                 # noqa: E402
from engine.calendar import build_chart             # noqa: E402
from engine.features import build_features          # noqa: E402
from engine.report import build_report, _plain      # noqa: E402

CHARTS = [(1997, 3, 22, 14, 10, "F"), (1985, 11, 3, 7, 40, "M"),
          (1972, 9, 9, 3, 25, "M")]

NUM = re.compile(r"\d")
WHEN = re.compile(r"올해|내년|작년|이번 주|다음 달|스물|서른|마흔|쉰|예순")
ACT = re.compile(r"(본다|한다|간다|산다|온다|미룬다|고른다|버린다|남긴다|"
                 r"묻는다|적는다|센다|멈춘다|끊는다|참는다|미뤄|끊지|참고|"
                 r"보오|하오|가오|접소|미루오|고치오|묻소|적소|셌소|끊소)")


def _hard(text: str) -> int:
    return sum(1 for s in re.split(r"[.!?…]", text)
               if len(s.strip()) > 4
               and (NUM.search(s) or WHEN.search(s) or ACT.search(s)))


@pytest.fixture(scope="module")
def reports():
    out = []
    for y, m, d, h, mi, sx in CHARTS:
        f = build_features(build_chart(y, m, d, h, mi, sx, True, "서울"))
        for l in lens_mod.released():
            tier = "one" if l.get("price") else "free"
            out.append((l["id"], f,
                        build_report(f, "t", l["id"], tier, "love", "INFP",
                                     name="가은")))
    return out


def test_no_cut_is_impossible_to_be_wrong_about(reports):
    """
    ★ 어떤 컷도 **금지하는 문장이 하나도 없어서는** 안 된다.

      쉰 개가 그랬습니다. 그 컷들은 어떤 사람이 읽어도 "맞다" 가 나오고,
      그래서 아무에게도 안 남습니다.
    """
    dead = {}
    for lid, f, rep in reports:
        for c in rep["cuts"]:
            key = c["id"]
            dead.setdefault(key, 0)
            dead[key] += _hard(_plain(c["html"]))
    empty = sorted(k for k, v in dead.items() if v == 0)
    assert not empty, ("금지하는 문장이 하나도 없는 컷 %d개: %s"
                       % (len(empty), empty[:8]))


def test_every_perspective_cut_counts_something(reports):
    """
    관점 컷은 값을 치른 사람이 읽는 **자기 몫**입니다. 거기가 물러지면
    값을 치를 이유가 사라집니다. 셈한 줄이 하나는 있어야 합니다.
    """
    for lid, f, rep in reports:
        for c in rep["cuts"]:
            if not c["id"].startswith("lc_"):
                continue
            body = _plain(c["html"])
            assert any(ch.isdigit() for ch in body), (lid, c["id"])


def test_the_last_cut_names_a_year(reports):
    """
    ★ 기억은 마지막이 지배하는데, 그 마지막이 셀 수 있는 것을 하나도
      안 담고 있었습니다. 대운이 바뀌는 나이는 이미 정확히 세어 뒀습니다.
    """
    for lid, f, rep in reports:
        last = next((c for c in rep["cuts"] if c["id"] == "closing_cut"), None)
        if not last:
            continue
        assert any(ch.isdigit() for ch in _plain(last["html"])), lid


def test_the_counted_line_never_predicts_an_event(reports):
    """
    ★ 때를 세는 것과 그 해에 무슨 일이 생긴다고 말하는 것은 다릅니다.
      바뀌는 때만 셉니다 (CLAUDE.md).
    """
    banned = ("반드시", "틀림없이", "확실히", "그해에 생기", "일이 터지")
    for lid, f, rep in reports:
        for c in rep["cuts"]:
            body = _plain(c["html"])
            for w in banned:
                assert w not in body, (lid, c["id"], w)
