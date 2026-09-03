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


def test_beat_follows_reading_speed():
    """
    한 덩이는 **그 덩이를 읽을 만큼** 두고 다음으로 넘긴다.

    ★ 전에는 전체가 3.2초에서 멈췄다.

      그래서 스무 줄이든 두 줄이든 3.2초 뒤에는 화면이 통째로 차
      있었다. 그건 읽는 속도가 아니라 **뜨는 순서**다 — 손님이 첫 줄을
      읽기도 전에 마지막 줄과 버튼이 이미 거기 있다. 손님이 두 번
      말한 자리다: "사람이 읽는 속도가 있을 거 아냐."
    """
    src = (WEB / "components" / "Shell.tsx").read_text(encoding="utf-8")
    assert "const CPS" in src, "읽는 속도를 안 보고 있다"
    assert "textContent" in src, "길이를 안 보고 있다"
    assert 'classList.contains("say")' in src, "대사를 따로 안 본다"
    assert not re.search(r"Math\.min\(t \+ ", src), \
        "전체에 상한을 다시 걸었다 — 그러면 읽는 속도가 아니라 순서다"

    cps = float(re.search(r"const CPS = (\d+(?:\.\d+)?)", src).group(1))
    assert 7 <= cps <= 14, "읽는 속도가 사람 속도가 아니다: %s" % cps
    # 한 덩이는 상한을 둔다. 긴 문단은 다 읽을 때까지 안 기다린다.
    hi = float(re.search(r"const HOLD_MAX = (\d+(?:\.\d+)?)", src).group(1))
    assert hi <= 3.0, "한 덩이가 너무 오래 붙잡는다: %s" % hi


def test_slow_reveal_always_has_a_way_out():
    """
    늦추는 데는 **건너뛰는 길**이 있어야 한다.

    없으면 그건 연출이 아니라 지연이다. 특히 두 번째 오는 사람에게.
    """
    src = (WEB / "components" / "Shell.tsx").read_text(encoding="utf-8")
    css = (WEB / "styles" / "overrides.css").read_text(encoding="utf-8")

    # ① 손님이 서두르면 그 자리에서 다 편다
    assert "revealAll" in src, "다 펴는 길이 없다"
    for ev in ("pointerdown", "keydown", "wheel", "beforeprint"):
        assert '"%s"' % ev in src, "%s 로는 못 건너뛴다" % ev
    assert "beatskip" in css, "다 펴는 표에 CSS 가 없다"

    # ② 눌러도 된다는 걸 알아야 누른다
    assert "beatskip-hint" in src and "beatskip-hint" in css, \
        "건너뛸 수 있다는 표시가 없다"

    # ③ 두 번째 오는 사람에게 같은 뜸은 지연이다
    assert "seenBefore" in src and "sessionStorage" in src, \
        "본 화면을 기억하지 않는다"

    # ④ 안 뜬 것은 눌리지도 않아야 한다 — 안 보이는 버튼이 눌린다
    assert "pointer-events: none" in css.split("@keyframes beatIn")[1][:200], \
        "안 뜬 덩이가 클릭을 먹는다"


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
