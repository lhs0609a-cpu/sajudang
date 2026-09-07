# -*- coding: utf-8 -*-
"""
**고민이 다르면 리포트도 달라지는가.**

★ 손님이 짚은 것 (2026-09-07)

  "고민이 다른데 왜 정답이 다 똑같아."
  "전부 다 고쳐."

★ 무엇이 어긋났나

  고민 전용 컷(`concern_scale` `concern_pattern` `concern_turn`
  `concern_face`)은 갈리는데 **척추 열 컷이 안 갈렸습니다** —
  없는 것 · 희소도 · 지금 어디에 · 필요한 것 · 대운 맵 · 신살 ·
  귀인 · 조상 · 이번 주 · 마감. 그 열이 분량의 절반이라, 여섯 칸 중
  무엇을 골라도 리포트 절반이 **글자까지 같았습니다.**

  잰 값 (표본 5명 × 고민 쌍 15조합)
      고친 전   같은 컷 17/27 · 평균 겹침 94.4%
      고친 뒤   같은 컷  6/27 · 평균 겹침 81.7%

★ 안 갈려야 하는 자리도 있습니다

  · `chart` 는 명식과 보정 내역이오. 물음에 따라 바뀌면 그건 계산이
    아니라 장사요.
  · 관점 컷(`lc_*`)은 그 사람의 **고정된 눈**이오. 월하선녀가 돈
    얘기를 하면 그건 월하선녀가 아닙니다. 대신 그 사람이 **제 자리인지
    아닌지**를 말하게 했습니다 (`topic.lens_line`).
"""
from __future__ import annotations

import itertools
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import topic                                   # noqa: E402
from engine.calendar import build_chart                    # noqa: E402
from engine.features import build_features                 # noqa: E402
from engine.report import build_report                     # noqa: E402

CONCERNS = ("money", "work", "love", "people", "dir", "health")

# 물음에 따라 바뀌면 **안 되는** 컷
FIXED = {"chart"}

PEOPLE = [
    ((1993, 7, 14, 5, 20), "F"),
    ((1988, 11, 2, 21, 40), "M"),
    ((2001, 3, 19, 13, 5), "F"),
]


def _flat(h):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h or "")).strip()


@pytest.fixture(scope="module")
def reports():
    out = []
    for birth, sex in PEOPLE:
        f = build_features(build_chart(*birth, sex, city="서울"))
        out.append((f, {c: build_report(f, "cid", "wolha", "all", c,
                                        axis4="INFP")["cuts"]
                        for c in CONCERNS}))
    return out


def test_the_spine_cuts_all_move_with_the_question(reports):
    """
    ★ 이 검사가 손님이 짚은 그 자리입니다.
      척추 열 컷이 고민을 안 보면 여기서 터집니다.
    """
    spine = ("lack", "rarity", "daeun_now", "yongsin", "daeun_map",
             "sinsal", "helper", "ancestor", "week", "closing_cut")
    for f, rep in reports:
        for cid in spine:
            texts = set()
            for c in CONCERNS:
                got = [x for x in rep[c] if x["id"] == cid]
                if got:
                    texts.add(_flat(got[0]["html"]))
            if not texts:
                continue
            assert len(texts) >= 5, (
                "%s 컷이 고민 여섯에서 %d가지뿐이오" % (cid, len(texts)))


def test_the_chart_cut_never_moves(reports):
    """명식과 보정은 물음이 바꿀 것이 아니오 — 바뀌면 계산이 아니라 장사요."""
    for f, rep in reports:
        for cid in FIXED:
            texts = {_flat(x["html"]) for c in CONCERNS for x in rep[c]
                     if x["id"] == cid}
            assert len(texts) == 1, "%s 가 물음에 따라 흔들리오" % cid


def test_most_of_the_report_moves_with_the_question(reports):
    """컷 스물일곱 중 대부분이 갈려야 합니다."""
    for f, rep in reports:
        ids = [x["id"] for x in rep["love"]]
        same = 0
        for cid in ids:
            texts = {_flat(x["html"]) for c in CONCERNS for x in rep[c]
                     if x["id"] == cid}
            if len(texts) == 1:
                same += 1
        assert same <= 8, "고민을 무시하는 컷이 %d개요 (전체 %d)" % (same, len(ids))


def test_statement_ids_split_when_the_words_split(reports):
    """
    문장이 갈렸으면 **집계도 갈려야** 합니다.
    안 그러면 돈에서 받은 「그렇소」가 사랑 문장의 공감률로 섞입니다.
    """
    for f, rep in reports:
        for cid in ("lack", "yongsin", "closing_cut"):
            sids, texts = set(), set()
            for c in CONCERNS:
                for x in rep[c]:
                    if x["id"] == cid:
                        sids.add(x["statement_id"])
                        texts.add(_flat(x["html"]))
            assert len(sids) >= len(texts), (
                "%s — 문장은 %d가지인데 열쇠는 %d가지요"
                % (cid, len(texts), len(sids)))


# ══════════════════════════════════════════════════════════
# 캐릭터가 제 자리인지 말하는가
# ══════════════════════════════════════════════════════════
def test_every_lens_says_whether_it_is_their_seat():
    """스무 명 전부 «내 자리가 아니오» 를 말할 줄 알아야 합니다."""
    import json
    lenses = json.loads((ROOT / "seed" / "lenses.json").read_text("utf-8"))
    lenses = lenses["lenses"] if isinstance(lenses, dict) else lenses
    lenses = lenses if isinstance(lenses, list) else list(lenses.values())
    for l in lenses:
        for c in CONCERNS:
            assert topic.lens_line(l["id"], c), (
                "%s 가 %s 에 대해 아무 말도 못 하오" % (l["id"], c))


def test_a_lens_speaks_differently_on_and_off_its_seat():
    """제 자리일 때와 아닐 때가 같은 말이면 밝히는 뜻이 없소."""
    on = topic.lens_line("wolha", "love")
    off = topic.lens_line("wolha", "money")
    assert on != off
    assert "내 자리가 아니" in off, off
    assert "내 자리가 아니" not in on, on


def test_the_lens_line_never_opens_with_self_introduction():
    """
    ★ 엿보기가 앞머리를 고를 때 화자의 자기 소개로 열리면 안 됩니다
      (tests/test_peek.py 가 잡는 자리). 표에서 미리 막습니다.
    """
    bad = re.compile(r"^(나는|내가|나도|저는|제가)\b")
    t = topic.table()
    for lid, say in t["LENS_OFF"].items():
        assert not bad.match(re.sub(r"<[^>]+>", "", say)), (lid, say)
    for lid, rows in t["LENS_ON"].items():
        for c, say in rows.items():
            assert not bad.match(re.sub(r"<[^>]+>", "", say)), (lid, c, say)


def test_cut_lines_exist_for_every_concern():
    """열 컷 × 여섯 칸이 다 차 있어야 합니다 — 빈 칸은 조용히 안 갈립니다."""
    t = topic.table()["CUT_AT"]
    for cid, rows in t.items():
        missing = [c for c in CONCERNS if not rows.get(c)]
        assert not missing, "%s 에 %s 칸이 비었소" % (cid, missing)
