# -*- coding: utf-8 -*-
"""
고민 칸을 열었으면 **표를 다 채웠는가**.

★ 2026-09-24. 화면에 일곱째 칸(부동산)을 열어 두고 표를 안 채웠습니다.
  그래서 그 칸을 고른 손님만 조용히 다른 글을 받았습니다 —

      훅 다섯 마디가 돈과 **글자 그대로** 같았고 (587·654·574·586·766자)
      되물음 컷은 `KeyError: 'lead'` 로 터졌고
      무료 구간은 `TypeError` 로 터졌고 (free_depth 칸이 넷이 아니라 셋)
      「사실 셋」 은 네 갈래 중 셋이 **0개**였고
      스무 명의 물음이 **한 문장**이었습니다 (말투 층이 다섯으로 보이게 함)

  하나만 비어도 그 칸을 고른 손님에게만 납니다. 아무도 안 죽고 그 사람의
  글만 남의 글이 됩니다. 그래서 **표마다** 셉니다.

★ 칸이 있는지만 보지 않고 **글자가 다른지**도 봅니다. 재물 행을 그대로
  베껴 두면 칸은 차 있어도 손님 눈에는 같은 글이오.
"""
from __future__ import annotations

import json
import sys
import typing
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from schemas.api import Concern                       # noqa: E402

CONCERNS = tuple(typing.get_args(Concern))
NEW = tuple(c for c in CONCERNS
            if c not in ("money", "work", "love", "people", "dir", "health"))


def test_고민_칸이_한_자리에서_온다():
    """화면·서버가 같은 목록을 봅니다 — 한쪽만 열면 그 칸이 빕니다."""
    import re
    src = (ROOT / "apps/web/lib/store.ts").read_text("utf-8")
    m = re.search(r'export type Concern =([^;]+);', src)
    assert m, "화면에서 고민 목록을 못 찾겠소"
    web = set(re.findall(r'"([a-z_]+)"', m.group(1)))
    assert web == set(CONCERNS), (sorted(web), sorted(CONCERNS))


@pytest.mark.parametrize("concern", CONCERNS)
def test_뱅크와_토픽_표에_칸이_있다(concern):
    from engine import bank as B
    from engine import topic as T
    for name, table in (("bank", B.bank()), ("topic", T.table())):
        missing = []

        def walk(node, path="$"):
            if isinstance(node, dict):
                keys = set(node)
                # ★ `LENS_ON` 은 **그 캐릭터가 제 자리라 하는 고민**만 담는
                #   표라, 빈 칸이 뜻입니다 (없으면 LENS_OFF 가 나갑니다).
                if "money" in keys and keys <= set(CONCERNS) | {"_"}                         and ".LENS_ON." not in path + ".":
                    if concern not in node:
                        missing.append(path)
                for k, v in node.items():
                    walk(v, "%s.%s" % (path, k))
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    walk(v, "%s[%d]" % (path, i))

        walk(table)
        assert not missing, "%s 에서 %s 칸이 빈 표: %s" % (
            name, concern, missing[:5])


@pytest.mark.parametrize("concern", NEW or ("money",))
def test_새_칸이_재물_행을_그대로_베끼지_않는다(concern):
    """칸이 차 있어도 글자가 같으면 손님 눈에는 같은 글이오."""
    from engine import bank as B
    from engine import topic as T
    same = []

    def walk(node, path="$"):
        if isinstance(node, dict):
            if ("money" in node and concern in node
                    and set(node) <= set(CONCERNS) | {"_"}
                    and ".LENS_ON." not in path + "."):
                a = json.dumps(node["money"], ensure_ascii=False)
                b = json.dumps(node[concern], ensure_ascii=False)
                if a == b and "돈" in a:
                    same.append(path)
            for k, v in node.items():
                walk(v, "%s.%s" % (path, k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, "%s[%d]" % (path, i))

    for table in (B.bank(), T.table()):
        walk(table)
    assert not same, "%s 이 돈 행을 그대로 쓰는 자리: %s" % (concern, same[:6])


@pytest.mark.parametrize("concern", CONCERNS)
def test_엔진_표들이_그_칸을_안다(concern):
    from engine import free_depth, reading_workbook, sinsal_read
    from engine import real as real_mod
    from engine.editorial import CONCERNS as ED_CONCERNS
    from engine.editorial_questions import CONCERN_ORDER, QUESTIONS

    assert concern in free_depth.CONCERNS, "free_depth 에 %s 가 없소" % concern
    assert len(free_depth.CONCERNS[concern]) == len(free_depth.CONCERNS["money"]), \
        "free_depth 의 %s 칸 수가 다르오" % concern
    assert concern in reading_workbook.GUIDES, "워크북에 %s 가 없소" % concern
    assert set(reading_workbook.GUIDES[concern]) == \
        set(reading_workbook.GUIDES["money"]), "워크북 %s 칸이 모자라오" % concern
    assert concern in sinsal_read.FOCUS, "신살 펴는 자리에 %s 가 없소" % concern
    assert concern in ED_CONCERNS, "첫 해석에 %s 가 없소" % concern
    assert concern in CONCERN_ORDER, "물음 표에 %s 가 없소" % concern
    for lens_id, row in QUESTIONS.items():
        assert len(row) == len(CONCERN_ORDER), "%s 의 물음이 모자라오" % lens_id
    for name, table in real_mod.TOPIC_TABLES.items():
        for key, row in table.items():
            assert concern in row, "real.%s[%s] 에 %s 가 없소" % (name, key, concern)


def test_스무_명의_물음이_고민마다_다_다르다():
    from engine.editorial_questions import CONCERN_ORDER, QUESTIONS
    flat = [q for row in QUESTIONS.values() for q in row]
    want = len(QUESTIONS) * len(CONCERN_ORDER)
    assert len(flat) == want and len(set(flat)) == want, \
        "물음 %d개 중 서로 다른 것 %d개" % (len(flat), len(set(flat)))


@pytest.mark.parametrize("concern", CONCERNS)
def test_갈래마다_사실_셋이_선다(concern):
    from engine import topic as T
    spec = (T.table().get("ASK") or {}).get(concern) or {}
    facts = (T.table().get("FACTS") or {}).get(concern) or {}
    for pick in (spec.get("options") or {}):
        rows = facts.get(pick)
        assert rows and len(rows) == 3, \
            "%s/%s 의 사실이 셋이 아니오 (%s)" % (concern, pick,
                                            rows and len(rows))
