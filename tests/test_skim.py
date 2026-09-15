"""
훑어읽기 — 강조만 읽어도 말이 되는가 (engine/skim.py)

★ 이 파일이 지키는 것

  손님이 짚었습니다 — "전체 글 다 안 읽을거니까 … 그것만 읽어도
  다 이해되게." 19,900원짜리 한 장이 29컷 12,582자입니다.

  강조 넷을 얹었는데, 강조는 **틀리면 안 하느니만 못합니다.**
  결론이 아닌 줄에 형광펜이 가면 훑어읽는 손님은 결론이 아닌 것을
  결론으로 읽습니다. 그래서 여기서 지키는 것은 「많이 칠했나」가
  아니라 **「맞는 데 칠했나」** 입니다.

      · 글자를 안 바꾼다 — 태그만 단다
      · 한 컷에 형광펜은 하나
      · 뜻이 다른 표시가 한 문장에 겹치지 않는다
      · 조용한 자리(비유·풀이·근거)에는 안 칠한다
      · 값이 오르면 훑어읽기도 는다
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import lens as lens_mod                      # noqa: E402
from engine import skim as skim_mod                      # noqa: E402
from engine.calendar import build_chart                  # noqa: E402
from engine.features import build_features               # noqa: E402
from engine.report import build_report                   # noqa: E402

TAG = re.compile(r"<[^>]+>")
MARK = re.compile(r"<mark>", re.S)
U = re.compile(r"<u>(.*?)</u>", re.S)
CONCERNS = ("money", "work", "love", "people", "dir", "health")


def _people():
    for spec in ((1993, 11, 25, 15, 55, "M"), (1978, 3, 3, 21, 40, "F"),
                 (2001, 7, 19, 8, 5, "F")):
        yield build_features(build_chart(*spec), as_of=date(2026, 9, 7))


def _reports():
    people = list(_people())
    for i, lens in enumerate(lens_mod.released()):
        f = people[i % len(people)]
        concern = CONCERNS[i % len(CONCERNS)]
        yield lens, build_report(f, "t", lens["id"], "one", concern, "INFP")


# ══════════════════════════════════════════════════════════
# 글자를 안 바꾼다 — 이게 첫째입니다
# ══════════════════════════════════════════════════════════
def test_marking_never_changes_a_single_letter():
    """
    ★ 강조는 **태그만** 답니다.

      글자가 바뀌면 분량·중복률·주어 감사·연출 점수가 전부 어긋납니다.
      그 값들은 이 집이 값을 매기고 쏠림을 재는 근거입니다.
    """
    samples = [
        '<p class="tale">그대는 신강이오. <b>쓸 힘이 남소.</b></p>',
        '<p class="bite">벌인 건 많은데 끝낸 건 적소. 그렇지 않소?</p>',
        '<p class="tale">이번 주에 하나만 끝내시오. 나머지는 다음에.</p>',
        '<p class="tale key">그대 힘은 <b>만드는 쪽</b>이오. 내놓고 나면 빈자리가 크오.</p>',
        '<p class="fig">우물을 한 삽씩 파듯 하시오.</p>',
        '<p class="tale">지금 33살이오. 다음 대운은 36살이오.</p>',
    ]
    for h in samples:
        got = skim_mod.mark(h, skim_mod.find_do(h))
        assert TAG.sub("", got) == TAG.sub("", h), h


def test_marking_is_idempotent():
    """두 번 얹어도 두 번 안 칠한다 — 층은 여러 번 돌 수 있습니다."""
    h = '<p class="bite">벌인 건 많은데 끝낸 건 적소. 그렇지 않소?</p>'
    once = skim_mod.mark(h)
    assert skim_mod.mark(once) == once


# ══════════════════════════════════════════════════════════
# 형광펜 — 한 컷에 하나. 결론에만
# ══════════════════════════════════════════════════════════
def test_one_highlight_per_cut():
    """
    ★ 둘이면 그건 요약이 아니라 또 본문입니다.
      형광펜만 읽는 손님에게 결론이 둘이면 어느 쪽도 결론이 아닙니다.
    """
    for lens, rep in _reports():
        for c in rep["cuts"]:
            n = len(MARK.findall(c["html"] or ""))
            assert n <= 1, (lens["id"], c["id"], n)


def test_highlight_is_never_a_fragment():
    """
    ★ 문장 조각에 칠하지 않는다.
      「혼자 지던 것을 나눌지」 가 형광펜으로 나간 적이 있습니다.
      이어 읽으면 말이 끊깁니다.
    """
    for lens, rep in _reports():
        for c in rep["cuts"]:
            for line in skim_mod.pen_lines(c["html"]):
                assert len(line) >= skim_mod.PEN_MIN, (lens["id"], c["id"], line)
                assert line.rstrip()[-1] in ".!?…", (lens["id"], c["id"], line)


def test_nothing_is_marked_in_the_quiet_boxes():
    """
    비유·풀이·근거는 조용해야 합니다. 그림에 형광펜을 치면 그림이
    결론이 되고, 낱말 뜻에 밑줄을 치면 뜻이 처방으로 보입니다.
    """
    box = re.compile(
        r'<(p|div) class="[^"]*\b(fig|gls|ev|src|cnt)\b[^"]*">(.*?)</\1>', re.S)
    for lens, rep in _reports():
        for c in rep["cuts"]:
            for m in box.finditer(c["html"] or ""):
                inner = m.group(3)
                assert "<mark>" not in inner, (lens["id"], c["id"], m.group(2))
                assert "<u>" not in inner, (lens["id"], c["id"], m.group(2))
                assert 'class="nu"' not in inner, (lens["id"], c["id"],
                                                   m.group(2))


# ══════════════════════════════════════════════════════════
# 겹치지 않는다 — 뜻이 같은 표시가 둘이면 둘 다 무시됩니다
# ══════════════════════════════════════════════════════════
def test_highlight_and_underline_never_share_a_sentence():
    for lens, rep in _reports():
        for c in rep["cuts"]:
            h = c["html"] or ""
            for u in U.findall(h):
                assert "<mark>" not in u, (lens["id"], c["id"], u[:40])


def test_numbers_are_not_marked_inside_bold():
    """굵게 + 수는 표시 둘에 뜻 하나입니다. 둘 다 힘을 잃습니다."""
    b = re.compile(r"<b>(.*?)</b>", re.S)
    for lens, rep in _reports():
        for c in rep["cuts"]:
            for inner in b.findall(c["html"] or ""):
                assert 'class="nu"' not in inner, (lens["id"], c["id"])


# ══════════════════════════════════════════════════════════
# 밑줄 — 손님이 할 것에만
# ══════════════════════════════════════════════════════════
def test_underline_is_only_a_prescription():
    """
    ★ 어미를 **말투 층 앞에서** 봐야 합니다.
      뒤에서 보면 하게체·반말은 서술과 명령이 같은 꼴이라
      「나는 뿌리부터 보오」 같은 소개말에 밑줄이 갔습니다.

      말투 층을 지난 뒤라 어미는 캐릭터마다 다릅니다. 그래서 여기서는
      **시키는 말의 꼴**만 봅니다 — 어느 말투든 이 중 하나로 끝납니다.
    """
    ok = ("시오", "십시오", "세요", "게", "지", "게나", "거라", "오")
    for lens, rep in _reports():
        for c in rep["cuts"]:
            for u in U.findall(c["html"] or ""):
                body = TAG.sub("", u).strip().rstrip(".!? ")
                assert body.endswith(ok), (lens["id"], c["id"], body[-14:])


def test_at_most_one_underline_per_cut():
    for lens, rep in _reports():
        for c in rep["cuts"]:
            assert len(U.findall(c["html"] or "")) <= 1, (lens["id"], c["id"])


# ══════════════════════════════════════════════════════════
# 값이 오르면 훑어읽기도 는다
# ══════════════════════════════════════════════════════════
def test_a_dearer_seat_skims_longer():
    """
    ★ 이 검사가 이 파일의 값어치 자리입니다.

      처음 얹었을 때 19,900원(29컷)과 0원(17컷)이 형광펜 줄 수가
      **똑같았습니다**(7.8줄). 값이 여는 것은 관점 컷인데 거기에
      결론 줄이 하나도 없었기 때문입니다. 값을 두 배 받으면서
      훑어읽는 손님에게는 같은 것을 주고 있었습니다.
    """
    f = next(_people())
    by_price = {}
    for lens in lens_mod.released():
        n = sum(len(skim_mod.pen_lines(c["html"]))
                for c in build_report(f, "t", lens["id"], "one", "work",
                                      "INFP")["cuts"])
        by_price.setdefault(int(lens["price"]), []).append(n)
    worst = {p: min(v) for p, v in by_price.items()}
    prices = sorted(worst)
    for lo, hi in zip(prices, prices[1:]):
        assert worst[hi] >= worst[lo], (lo, worst[lo], hi, worst[hi])
    assert worst[max(prices)] > worst[min(prices)], worst


@pytest.mark.parametrize("lens", [l for l in lens_mod.released()],
                         ids=lambda l: l["id"])
def test_every_report_can_be_skimmed(lens):
    """한 장에 형광펜이 이만큼은 있어야 훑어읽기가 됩니다."""
    f = next(_people())
    for concern in CONCERNS:
        rep = build_report(f, "t", lens["id"], "one", concern, "INFP")
        n = sum(len(skim_mod.pen_lines(c["html"])) for c in rep["cuts"])
        assert n >= 8, (lens["id"], concern, n)
