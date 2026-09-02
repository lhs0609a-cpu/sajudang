# -*- coding: utf-8 -*-
"""
화면이 대화처럼 한 줄씩 뜨는가 — 모든 화면.

★ 왜 이걸 지키나

  나레이션은 줄 간격이 있었는데 그건 **그 블록 안에서만** 먹혔다.
  그래서 「붓을 내려놓고, 그가 물었다」와 「무엇이 걸려서 예까지
  왔소?」와 고민 여섯 칸이 한꺼번에 떴다. 물음과 답이 같이 뜨면
  그건 대화가 아니라 게시물이다.

  그리고 첫 판은 Shell **바로 밑**만 봤다. 재 보니 56개 중 12개가
  한 겹 안에 들어 있어 그 화면들만 통째로 떴다. 그래서 알갱이는
  깊이와 무관하게 줍는다.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"


def test_shell_sequences_atoms_at_any_depth():
    """대화 알갱이는 한 겹 안에 있어도 따로 뜬다."""
    src = (WEB / "components" / "Shell.tsx").read_text(encoding="utf-8")
    assert '".nr > .l, .say"' in src, "알갱이를 깊이와 무관하게 줍지 않는다"
    assert ":scope > *" not in src, "바로 밑만 보면 한 겹 안이 통째로 뜬다"
    assert "compareDocumentPosition" in src, "보이는 순서대로 매기지 않는다"


def test_beat_is_fast_enough_to_not_be_a_wait():
    """느리면 연출이 아니라 지연이다."""
    src = (WEB / "components" / "Shell.tsx").read_text(encoding="utf-8")
    # ★ 간격은 방금 뜬 것의 **길이**를 따릅니다. 고정 간격이 아니라
    #   글자 수로 정하므로, 상한 둘만 봅니다.
    # ★ 간격은 **무엇인지**와 **길이**를 함께 봅니다.
    #   대사는 잠깐 두고, 서술은 흐르고, 버튼은 곧바로 옵니다.
    cap = re.search(r"Math\.min\(t \+ gap, (\d+(?:\.\d+)?)\)", src)
    assert cap and float(cap.group(1)) <= 3.6, "마지막 것이 너무 늦게 뜬다"
    assert "textContent" in src, "길이를 안 보고 있다"
    assert 'classList.contains("say")' in src, "대사를 따로 안 본다"
    for cap_s in re.findall(r"Math\.min\((\d\.\d+), Math\.max", src):
        assert float(cap_s) <= 1.2, "한 칸이 너무 늦다: %s" % cap_s


def test_background_does_not_wait():
    """장면·진행 막대는 배경이라 처음부터 있어야 한다."""
    src = (WEB / "components" / "Shell.tsx").read_text(encoding="utf-8")
    for c in ("prog", "sceneart"):
        assert 'contains("%s")' % c in src, "%s 를 안 뺐다" % c


def test_reduced_motion_turns_it_off():
    src = (WEB / "components" / "Shell.tsx").read_text(encoding="utf-8")
    css = (WEB / "styles" / "overrides.css").read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in src, "스크립트가 설정을 안 본다"
    assert "prefers-reduced-motion" in css, "CSS 가 설정을 안 본다"


def test_every_screen_goes_through_shell():
    """한 화면이라도 Shell 을 안 거치면 그 화면만 대화가 아니다."""
    bad = []
    for p in (WEB / "app").rglob("page.tsx"):
        # ★ 주인 자리(/admin)는 손님 화면이 아닙니다. 틀도 장면도 없고
        #   대화로 뜨지도 않습니다 — 읽고 판단하는 자리라 한눈에
        #   보이는 것이 먼저입니다. 여기만 예외로 둡니다.
        if "admin" in p.parts:
            continue
        src = p.read_text(encoding="utf-8")
        if "<Shell" in src:
            continue
        # Shell 을 쓰는 것을 그리기만 하는 껍데기는 봐준다
        if re.search(r"<\w+View\b|return <\w+ ", src):
            continue
        bad.append(str(p.relative_to(WEB)))
    assert not bad, "Shell 밖에서 그리는 화면: %s" % bad
