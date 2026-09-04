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
    for ev in ("click", "keydown", "beforeprint"):
        assert '"%s"' % ev in src, "%s 로는 못 건너뛴다" % ev
    assert "beatskip" in css, "다 펴는 표에 CSS 가 없다"

    # ★ 다만 **굴림은 건너뛰기가 아니다** (2026-09-04)
    #
    #   전에는 `wheel` 과 `touchmove` 도 다 펴는 손잡이였다. 그런데 이제
    #   굴림이 **글을 띄우는 손잡이**다. 둘을 같이 걸면 굴리는 순간
    #   통째로 펴져서, 손님은 늘 다 떠 있는 화면만 본다. 모바일은 더하다 —
    #   손가락을 대는 순간 `pointerdown` 이 먼저 울려, 굴리려던 사람이
    #   건너뛰기를 누른 셈이 된다.
    #
    #   손님이 말했다 — "사용자가 화면 내리는거에 맞춰서 글을 띄워줘.
    #   미리 다 띄우면 안돼. 전체적으로 다."
    for ev in ("wheel", "touchmove", "pointerdown"):
        assert 'addEventListener("%s"' % ev not in src, (
            "%s 로 건너뛰고 있다 — 굴림은 글을 띄우는 손잡이지 "
            "건너뛰는 손잡이가 아니다" % ev)

    # ② 눌러도 된다는 걸 알아야 누른다
    assert "beatskip-hint" in src and "beatskip-hint" in css, \
        "건너뛸 수 있다는 표시가 없다"

    # ③ 두 번째 오는 사람에게 같은 뜸은 지연이다
    assert "seenBefore" in src and "sessionStorage" in src, \
        "본 화면을 기억하지 않는다"


def test_reveal_follows_the_scroll():
    """
    글은 **굴리는 대로** 뜬다 — 미리 띄우는 자리는 없다.

    ★ 전에는 첫 화면 안을 시계로 다 띄웠다. 손 하나 안 대도 몇 초 만에
      다 떠 버리니, 손님에게는 「미리 다 띄운 것」과 같다.
    """
    src = (WEB / "components" / "Shell.tsx").read_text(encoding="utf-8")
    css = (WEB / "styles" / "overrides.css").read_text(encoding="utf-8")

    assert "IntersectionObserver" in src, "굴림을 안 보고 있다"
    # 눈에 들어오기 전까지는 안 보이는 표
    assert "beatwait" in src, "기다리는 자리에 표가 없다"

    # ★ 굴릴 수 없는 화면에는 문턱을 안 건다 — 안 그러면 영영 안 뜬다
    assert "canScroll" in src, "굴릴 수 없는 화면을 안 가린다"

    # ★ 누르는 것은 굴림에 안 맡긴다 — 대문의 버튼이 안 뜬다
    assert "eyeUiRef" in src, \
        "버튼에도 같은 문턱을 걸고 있다 — 굴려야 누를 것이 나타난다"

    # ★ 바닥에서는 남은 것을 낸다 — 더 굴릴 데가 없다는 뜻
    assert "scrollHeight" in src, "바닥에 닿아도 안 띄운다"

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
