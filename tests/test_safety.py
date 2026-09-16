# -*- coding: utf-8 -*-
"""
아프게 한 뒤의 책임 — 검사로 못박는다.

★ 손님이 시킨 것 (2026-09-16)

    "이거의 핵심은 정말 팩폭하면서도 동시에 위로를 줘야 한다는 거야.
     희망이 생겨야 해 삶에. 그로 인해서 자살하는 사람이 늘어나지
     않도록 설계해줘."

  이 집은 아픈 말을 **일부러** 합니다. 그건 그대로 둡니다 — 아프지
  않은 말은 아무것도 안 바꿉니다. 여기서 지키는 것은 하나요:

      아픈 말은 **혼자 다니지 않는다.**

  칼을 댄 자리에는 손잡이가 같이 옵니다. 이 검사가 그걸 셉니다.
  글을 고치다 손잡이를 떨어뜨리면 여기서 걸립니다.
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import care as care_mod              # noqa: E402
from engine import dramaturgy as D               # noqa: E402
from engine import guard                         # noqa: E402
from engine import heart as heart_mod            # noqa: E402
from engine import bank as bank_mod              # noqa: E402
from engine.calendar import build_chart          # noqa: E402
from engine.features import build_features       # noqa: E402
from engine.report import build_report           # noqa: E402

TODAY = date(2026, 9, 16)
CONCERNS = ("money", "work", "love", "people", "dir", "health")

# 집이 스스로 짚어 둔 아픈 자리 · 손잡이 자리
BLADE = re.compile(r'class="(?:blade|bite|stab)[" ]')
HOLD = re.compile(r'class="(?:bladerelief|hold)[" ]')
HOLD_WORD = re.compile(
    r"혼자가 아니|그대 탓이 아니|잘못이 아니|당연하오|게을러서가 아니|"
    r"여태 그 자리 없이|이미 쥐|이미 가진|처음부터 쥐")

# 몇 사람만 봅니다 — 구조를 보는 검사라 표본이 크지 않아도 됩니다.
BIRTHS = [
    (1993, 11, 25, 15, 55, "M", True),
    (1978, 2, 4, 0, 20, "F", True),
    (2001, 7, 17, 23, 10, "F", True),
    (1966, 12, 31, None, None, "M", False),
]


def _f(b):
    y, m, d, h, mi, sex, known = b
    return build_features(build_chart(y, m, d, h, mi, sex, known, "서울"),
                          as_of=TODAY)


def _holds(html: str) -> bool:
    return bool(HOLD.search(html or "")
                or HOLD_WORD.search(D.plain(html or "")))


@pytest.mark.parametrize("b", BIRTHS)
@pytest.mark.parametrize("concern", CONCERNS)
def test_아픈_컷에는_손잡이가_같이_온다(b, concern):
    f = _f(b)
    for tier in ("free", "one", "all"):
        rep = build_report(f, "t", "pungun", tier, concern, "INTJ")
        for c in rep["cuts"]:
            if not BLADE.search(c["html"] or ""):
                continue
            assert _holds(c["html"]), (
                "아프게만 하고 지나가오: %s · %s · %s" % (tier, concern, c["id"]))


@pytest.mark.parametrize("b", BIRTHS)
def test_훅은_찌르고_나서_받아_준다(b):
    """무료 구간에서 나가는 사람이 가장 많소. 그 사람들도 손잡이를 받아야 하오."""
    f = _f(b)
    for concern in CONCERNS:
        segs = bank_mod.build_hook(f, concern, "INTJ", "", "그대")
        for i, s in enumerate(segs):
            if BLADE.search(s["html"] or ""):
                assert _holds(s["html"]), (
                    "훅 %d마디가 아프게만 하오 (%s)" % (i + 1, concern))


@pytest.mark.parametrize("b", BIRTHS)
def test_끝은_앞을_보는_자리다(b):
    """기억은 마지막이 지배하오 — 마지막이 진단이면 그 장은 진단서요."""
    f = _f(b)
    forward = {"hope", "week", "closing_cut", "helper", "yongsin", "counter"}
    for concern in CONCERNS:
        for tier in ("free", "one", "all"):
            rep = build_report(f, "t", "pungun", tier, concern, "INTJ")
            ids = [c["id"] for c in rep["cuts"]]
            assert ids and ids[-1] in forward, (tier, concern, ids[-1])


@pytest.mark.parametrize("b", BIRTHS)
def test_모든_장에_알아주는_자리가_있다(b):
    f = _f(b)
    hold = {"solace", "hope", "helper"}
    for concern in CONCERNS:
        for tier in ("free", "one", "all"):
            rep = build_report(f, "t", "pungun", tier, concern, "INTJ")
            ids = {c["id"] for c in rep["cuts"]}
            assert ids & hold, (tier, concern, sorted(ids)[:6])


def test_손잡이는_가드를_통과한다():
    for cut, rows in heart_mod.HOLD_AT.items():
        for r in rows:
            ok, hits = guard.check(r)
            assert ok, (cut, hits, r[:40])


def test_문을_닫는_말은_막힌다():
    """이 집은 근거 대는 집이지 선고하는 집이 아니오."""
    for t in ("그대 팔자요", "어쩔 수 없소", "이미 늦었소", "가망이 없소",
              "끝났소", "바꿀 수 없소", "소용없소"):
        ok, _ = guard.check(t)
        assert not ok, "문을 닫는 말이 통과하오: %s" % t


def test_바뀌는_때를_세는_말은_안_막힌다():
    """막는 데 걸려 제 말까지 막으면 그건 고장이오."""
    for t in ("바뀌는 때가 오오", "대운은 10년 뒤 바뀌오",
              "팔자에 없는 것을 세오", "고칠 자리가 하나 있소"):
        ok, hits = guard.check(t)
        assert ok, (t, hits)


def test_쉬어_가는_자리는_신호가_겹칠_때만_연다():
    assert not care_mod.should_open(visits=1)
    assert not care_mod.should_open(visits=3)          # 하나로는 안 엽니다
    assert care_mod.should_open(visits=3, hook_misses=4)
    assert care_mod.should_open(visits=3, hour=2, returning=True)


def test_쉬어_가는_자리는_아무것도_안_판다():
    r = care_mod.rest("그대", ["되풀이"])
    t = " ".join([r["head"], r["body"], r["limit"]])
    for w in ("원", "결제", "값을 치르", "구매", "더 보"):
        assert w not in t, ("쉬어 가는 자리에서 파오: %s" % w)
    ok, hits = guard.check(t)
    assert ok, hits
    # 번호는 적어 두기만 하오
    assert [x["tel"] for x in r["lines"]] == ["109", "1577-0199", "1388"]


def test_도움_받을_곳은_화면에도_같은_번호다():
    """표를 두 벌 들면 한쪽만 고쳐져 틀린 번호가 나가오.

    화면은 `lib/care.ts` 한 벌에서 번호를 가져다 씁니다. 그 파일이
    엔진의 표와 같은지 여기서 셉니다 — 같은 값이 두 곳에 적혀 있으면
    언젠가 한쪽만 고쳐집니다.
    """
    ts = (ROOT / "apps" / "web" / "lib" / "care.ts").read_text(
        encoding="utf-8")
    for x in care_mod.LINES:
        assert ('"%s"' % x["tel"]) in ts, x["tel"]
        assert ('"%s"' % x["name"]) in ts, x["name"]
    # 문턱도 한 벌이라야 하오
    assert ("OPEN_AT = %d" % care_mod.OPEN_AT) in ts
    assert ("VISITS_AT = %d" % care_mod.VISITS_AT) in ts
    assert ("MISS_AT = %d" % care_mod.MISS_AT) in ts
    # 처마는 그 표를 쓰는가 (번호를 손으로 박아 두지 않았는가)
    shell = (ROOT / "apps" / "web" / "components" / "Shell.tsx").read_text(
        encoding="utf-8")
    assert "CARE_LINES" in shell
