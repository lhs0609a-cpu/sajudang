# -*- coding: utf-8 -*-
"""
화면이 제 이름을 적는가 — 연출 자가 화면을 안 헷갈리게.

★ 무슨 일이 있었나 (2026-09-03)

  연출 점수는 화면을 `step === "a7"` 같은 **조건문**으로 갈랐다.
  그런데 마지막 return 으로 떨어지는 화면 — a7 훅 · b1 진열대 ·
  c2 본문 · d1 어디까지 — 은 그런 조건문이 없다. 그래서

    · a7 의 막 끝(`ActOut`)이 **a6 의 점수로** 올라갔고
    · 진열대와 「어디까지」와 인장첩은 **아예 안 재지고** 있었다.

  진열대는 값이 붙은 목패가 늘어선 자리고 「어디까지」는 값을 고르는
  자리다. 장사가 일어나는 두 화면을 자가 한 번도 안 본 것이다.

  화면이 `<Shell screen="a7">` 로 제 이름을 적으면 그건 **있는 것**이다.
  액트아웃을 `<ActOut kind="딜레마">` 선언으로 받은 것과 같은 까닭이다 —
  말뭉치로 찾으면 글을 고칠 때마다 자를 고치게 된다.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import screenscan as S  # noqa: E402

# 장사가 일어나는 자리 — 여기가 빠지면 자가 눈을 감은 것이다
MUST = ("a7", "b1", "c2", "d1", "d0", "c4")


def test_every_screen_file_declares_names():
    """화면 파일마다 <Shell screen="…"> 이 하나 이상 있다."""
    for rel in S.PAGES:
        p = WEB / rel
        if not p.exists():
            continue
        got = S.SCREEN_DECL.findall(p.read_text(encoding="utf-8"))
        assert got, "%s 가 화면 이름을 안 적는다 — 자에서 사라진다" % rel


def test_declared_names_are_known_screens():
    """docs/08 §1 에 없는 이름을 적지 않는다."""
    for rel in S.PAGES:
        p = WEB / rel
        if not p.exists():
            continue
        for sid in S.SCREEN_DECL.findall(p.read_text(encoding="utf-8")):
            assert sid in S.KO, "%s 의 screen=\"%s\" 는 모르는 이름이다" % (rel, sid)


def test_fallthrough_screens_are_measured():
    """마지막 return 으로 떨어지는 화면도 제 글로 재진다."""
    S._screens.cache_clear()
    rows = {r["id"]: r for r in S.scan_all()}
    for sid in MUST:
        assert sid in rows, "%s(%s) 가 안 재지고 있다" % (sid, S.KO[sid])
        assert rows[sid]["chars"] > 0, "%s 가 0자로 잡힌다" % sid


def test_actout_belongs_to_its_own_screen():
    """a7 의 막 끝이 a6 의 점수로 올라가지 않는다."""
    S._screens.cache_clear()
    pairs = S._screens()
    src = (WEB / "app" / "page.tsx").read_text(encoding="utf-8")
    # a7 의 액트아웃은 「없는 것부터」 를 이름으로 부른다
    assert 'next="없는 것부터"' in src
    assert pairs["a7"][2] == "없는 것부터", "a7 이 제 예고를 못 든다"
    assert pairs["a6"][2] != "없는 것부터", "a6 가 a7 의 예고를 훔쳤다"


def test_ruler_reads_the_declaration_not_the_wording():
    """예고는 **선언**으로 읽는다 — 글자를 바꿔도 점수가 안 흔들린다."""
    src = (WEB / "components" / "ActOut.tsx").read_text(encoding="utf-8")
    assert re.search(r"next\?:\s*string", src), "예고가 선언이 아니다"
    assert S.ACT_NEXT.search('<ActOut kind="딜레마" next="본문">')
    assert S.ACT_NEXT.search('<ActOut kind="밝힘" next={cut?.title}>')
