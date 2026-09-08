"""
이름 붙은 자리를 **읽는** 법 (engine/sinsal_read.py)

★ 왜 고쳤나 (2026-09-07 · tools/same_audit.py)

      sinsal  1,651자   사람 축 94% 겹침 · 고민 축 98% 겹침

  리포트 한 장 14,661자 중 이 컷 하나가 **11%** 인데, 스무 사람에게
  여섯 고민에 글자 그대로 같은 글이 나갔습니다. 여덟 개를 **전부 펴
  놓고** 맨 끝에 「이 가운데 일에서 보던 것은 셋이오」 라 적고 있었으니,
  순서가 거꾸로였습니다.

★ 이 파일이 지키는 것

      ① 물으신 자리로 갈라 세운다 — 걸리는 것만 펴고 나머지는 접는다
      ② 접은 것을 **지우지 않는다** — 이름은 남긴다
      ③ 걸리는 것이 없으면 **접지 않는다** — 빈 컷을 내지 않는다
      ④ 신살이 하나도 없는 명식에서도 선다  ← 실제로 터졌던 자리
      ⑤ 궁위에 **나이**를 박는다 (docs/14 §6)
      ⑥ 표가 두 벌이 안 되게 — seed/topic.json 과 열쇠가 맞는가
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import sinsal_read as sr                     # noqa: E402
from engine.calendar import build_chart                  # noqa: E402
from engine.features import build_features               # noqa: E402
from engine.report import build_report                   # noqa: E402

TAG = re.compile(r"<[^>]+>")
CONCERNS = ("money", "work", "love", "people", "dir", "health")


def _f(spec=(1993, 11, 25, 15, 55, "M")):
    return build_features(build_chart(*spec), as_of=date(2026, 9, 7))


def _cut(f, concern="work", lens="pungun"):
    rep = build_report(f, "t", lens, "one", concern, "INFP")
    return next((c for c in rep["cuts"] if c["id"] == "sinsal"), None)


# ══════════════════════════════════════════════════════════
# ① 물으신 자리로 갈라 세운다
# ══════════════════════════════════════════════════════════
def test_the_question_decides_which_names_are_opened():
    f = _f()
    seen = {}
    for concern in CONCERNS:
        c = _cut(f, concern)
        assert c, concern
        seen[concern] = TAG.sub("", c["html"])
    # 여섯 칸이 서로 다른 글이라야 합니다. 하나라도 같으면 안 갈린 것입니다.
    assert len(set(seen.values())) >= 4, \
        "여섯 고민이 %d가지로만 갈리오" % len(set(seen.values()))


def test_folding_never_deletes_a_name():
    """
    ★ 접는 것과 지우는 것은 다릅니다.
      여덟 중 셋만 폈다고 나머지를 없애면 「내 신살이 몇 갠지」를
      손님이 못 셉니다. 이름은 남깁니다.
    """
    f = _f()
    all_names = {s["name"] for s in f.sinsal}
    assert all_names, "표본에 신살이 없소 — 다른 명식을 고르시오"
    body = TAG.sub("", _cut(f, "work")["html"])
    for name in all_names:
        assert name in body, name


def test_nothing_is_folded_when_nothing_is_focused():
    """
    ★ 물은 자리에서 볼 것이 하나도 없으면 **전부 폅니다.**
      여덟을 다 접으면 손님은 값을 치르고 빈 컷을 받습니다.
    """
    fake = [{"key": "hongyeom", "name": "홍염", "at": ["일주"]}]
    on, off = sr.split(fake, "work")          # work 에 홍염은 안 걸림
    assert on == fake and off == []


def test_a_chart_with_no_names_still_stands():
    """
    ★ 실제로 터졌던 자리입니다.
      신살이 하나도 없는 명식에서 `on` 이 안 만들어진 채 열쇠에
      쓰여 `UnboundLocalError` 가 났습니다. 표본에 그런 사람이
      없어서 검사 1,201개가 다 통과했습니다.
    """
    class Empty:
        sinsal = []
    on, off = sr.split(list(Empty.sinsal), "money")
    assert on == [] and off == []


# ══════════════════════════════════════════════════════════
# ② 궁위에 나이를 박는다 — docs/14 §6
# ══════════════════════════════════════════════════════════
def test_the_palace_carries_an_age():
    """
    ★ 나이가 박혀야 **대 볼 수 있는 말**이 됩니다.
      「년주에 앉았소」 는 틀릴 수가 없고, 「열다섯 안쪽 얘기라 이미
      지나온 자리요」 는 손님이 그 자리에서 압니다.
    """
    sv = {"key": "yangin", "name": "양인", "at": ["년주"]}
    assert "열다섯 안쪽" in sr.when_line(sv, 33)
    assert "지나온" in sr.when_line(sv, 33)
    # 아홉 살은 년주(0~15) **안**이라 「지금 선 자리」요.
    assert "지금 선 자리" in sr.when_line(sv, 9)
    # 아직 안 온 자리는 시주(46~)를 서른셋이 볼 때요.
    later = {"key": "hwagae", "name": "화개", "at": ["시주"]}
    assert "아직" in sr.when_line(later, 33)
    now = {"key": "geumyeo", "name": "금여", "at": ["일주"]}
    assert "지금 선 자리" in sr.when_line(now, 33)


def test_every_palace_in_the_doc_has_an_age():
    """docs/14 §6 의 네 기둥이 다 있어야 합니다."""
    for p in ("년주", "월주", "일주", "시주"):
        assert p in sr.PALACE_AGE and p in sr.PALACE_WHEN, p


def test_the_ages_never_overlap_or_leave_a_hole():
    rows = sorted(sr.PALACE_AGE.values())
    for (a_lo, a_hi), (b_lo, _b_hi) in zip(rows, rows[1:]):
        assert b_lo == a_hi + 1, (a_lo, a_hi, b_lo)


# ══════════════════════════════════════════════════════════
# ③ 표가 두 벌이 되지 않게
# ══════════════════════════════════════════════════════════
def test_the_focus_table_agrees_with_the_seed_prose():
    """
    ★ 열쇠는 여기 있고 손님이 읽는 **글**은 seed 에 있습니다.
      두 벌이 되면 갈립니다 — 글은 「돈에서는 금여를 보오」 라 적고
      기계는 금여를 안 펴는 자리가 생깁니다.

      seed 쪽 글은 이 집의 **선을 긋는 말**로 바뀌었으므로(신살로
      액수를 말하지 않소 …) 이름을 대조하지는 못합니다. 대신 여섯
      칸이 다 있고, 각 칸이 아는 이름만 가리키는지를 봅니다.
    """
    seed = json.loads((ROOT / "seed" / "sinsal.json").read_text("utf-8"))
    known = set(seed["meaning"])
    topic = json.loads((ROOT / "seed" / "topic.json").read_text("utf-8"))
    assert set(topic["CUT_AT"]["sinsal"]) == set(CONCERNS)
    for concern in CONCERNS:
        keys = sr.FOCUS[concern]
        assert keys, concern
        assert keys <= known, (concern, keys - known)


def test_every_opened_name_can_be_checked_against_a_life():
    """
    ★ 펴는 것에는 **대 볼 수 있는 한 줄**이 붙어야 합니다.
      「이동·출장이 잦다」 는 사전입니다. 「지난 십 년에 몇 번
      옮겼소」 라야 손님이 그 자리에서 압니다.
    """
    seed = json.loads((ROOT / "seed" / "sinsal.json").read_text("utf-8"))
    for concern, keys in sr.FOCUS.items():
        for k in keys:
            assert k in sr.CHECK, (concern, k)
    # 표에 있는 이름은 다 아는 이름이라야 합니다.
    assert set(sr.CHECK) <= set(seed["meaning"])


@pytest.mark.parametrize("concern", CONCERNS)
def test_the_cut_never_says_a_name_causes_illness(concern):
    """docs/14 §7 — 신살로 질병·사고·재물을 단정하지 않습니다."""
    banned = ("병이 오", "죽", "암", "사고가 나", "부자가 되", "망하")
    body = TAG.sub("", _cut(_f(), concern)["html"])
    for w in banned:
        assert w not in body, (concern, w)
