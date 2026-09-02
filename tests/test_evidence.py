# -*- coding: utf-8 -*-
"""
근거가 근거 노릇을 하는가.

★ 「과학적으로 입증」 은 못 쓴다

  사주는 과학적으로 검증된 적이 없다. 그렇게 쓰면 거짓말이고 이 집이
  금지한 것이다 (docs/11). 적중률·통계도 마찬가지다.

  회의적인 독자를 설득하는 것은 그 말이 아니라 **따라갈 수 있는
  논증**이다 — 무엇을 보고(관측), 어떤 이치로(규칙), 그래서 이렇게
  (결론), 그 이치는 어디서 왔는가(출처).

  넷이 다 있으면 독자는 **어디가 틀렸는지 짚을 수 있다.**
  짚을 수 있는 말이라야 믿을 수 있는 말이다.

★ 세어 보니 이랬다 (tools/evidence_audit.py)

    전   관측 87.6% · 이치  0.0% · 결론 17.6% · 출처  9.2%
    후   관측 86.7% · 이치 47.0% · 결론 55.3% · 출처 58.8%
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "services" / "api"))

import evidence_audit as ea  # noqa: E402

MIN_RULE = 0.35      # 이치가 붙은 몫의 하한
MIN_SRC = 0.45       # 출처가 붙은 몫의 하한


def _score(n=25):
    lines = ea.sample(n)
    tot = len(lines) or 1
    have = {"이치": 0, "출처": 0}
    for txt in lines:
        if ea.RULE.search(txt):
            have["이치"] += 1
        if ea.SRC.search(txt):
            have["출처"] += 1
    return {k: v / tot for k, v in have.items()}, lines


def test_evidence_carries_a_rule_not_just_a_reading():
    """관측만 대면 그건 근거가 아니라 자료다."""
    s, _ = _score()
    assert s["이치"] >= MIN_RULE, \
        "이치가 붙은 근거가 %.0f%% 뿐이다 (하한 %.0f%%)" % (
            s["이치"] * 100, MIN_RULE * 100)


def test_evidence_says_where_the_rule_came_from():
    s, _ = _score()
    assert s["출처"] >= MIN_SRC, \
        "출처가 붙은 근거가 %.0f%% 뿐이다" % (s["출처"] * 100)


def test_no_science_claim_anywhere_in_evidence():
    """
    ★ 이게 가장 중요한 검사다.

      근거를 세게 만들려다 「과학적으로」 를 쓰면 그 순간 이 집은
      거짓말하는 집이 된다. 세다는 것과 참이라는 것은 다르다.
    """
    _, lines = _score()
    banned = ("과학", "통계", "적중률", "입증", "증명", "확률적으로",
              "반드시", "무조건", "100%")
    bad = [t for t in lines if any(b in t for b in banned)]
    assert not bad, "근거에 못 쓰는 말이 있다: %s" % bad[:5]


def test_citations_are_not_invented():
    """
    확인할 수 없는 인용은 거짓과 같다. 갈래 이름까지만 댄다.
    「자평진전 42쪽」 같은 것은 안 쓴다.
    """
    from engine import why
    import re
    for v in why.SCHOOL.values():
        assert not re.search(r"\d+\s*(쪽|페이지|p\.)", v), \
            "지어낸 인용: %s" % v


def test_rules_are_one_line_each():
    """길면 아무도 안 읽고, 짧으면 이치가 안 보인다."""
    from engine import why
    for table in (why.TEN_GOD, why.GROUP, why.RULE):
        for k, v in table.items():
            assert 10 <= len(v) <= 90, "%s 의 이치가 %d자다" % (k, len(v))
