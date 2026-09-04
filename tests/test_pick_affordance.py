# -*- coding: utf-8 -*-
"""
고를 칸이 **고르라고 말하는가.**

★ 손님이 짚은 것 (2026-09-04)

  "이런 버튼들 클릭하라고 유도해야지. 저게 선택되어 있으니까 유저는
  모르잖아 다음 액션을 뭘 해야할지. 전부 바꿔."

  고민 여섯 칸에 「돈」이, 성별 두 칸에 「여인」이, 목패 세 장 중
  하나가 **이미 켜진 채** 서 있었습니다. 기본값이 있어야 셈이
  도니까요. 그런데 화면이 그걸 「고른 것」처럼 그리면, 손님은 고른
  적이 없는데 골라져 있는 것을 봅니다.

★ 성별은 UX 가 아니라 **셈이 틀어지는 자리**였습니다

  대운은 `forward = (양간) == (사내)` 로 방향이 정해집니다
  (engine/calendar.py). 「여인」이 켜진 채라 **사내는 아무것도 안
  누르고 지나갔고**, 그러면 열 칸이 통째로 반대로 섭니다.

★ 값과 «고른 사실» 을 나눕니다

  값은 그대로 둡니다 — 레일이 중간으로 뛰어드는 자리가 있습니다.
  다만 `concernSet` · `sexSet` 으로 사람이 골랐는지를 따로 적고,
  그 전에는 아무 칸도 안 켜고 다음으로도 안 보냅니다.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"


def _src(rel: str) -> str:
    return (WEB / rel).read_text(encoding="utf-8")


# ── 켜진 채로 서 있지 않는가 ──────────────────────────────
def test_no_option_is_lit_before_the_customer_picks():
    """
    `op ... on` 을 켜는 조건이 **값만** 보고 있으면 안 된다.

    기본값이 있는 칸(고민·성별)은 「고른 사실」을 함께 봐야 한다.
    """
    src = _src("app/page.tsx")
    lit = re.findall(r'`op \$\{([^}]+)\}`', src)
    assert lit, "고를 칸을 못 찾았소"
    for cond in lit:
        if "s.concern ===" in cond:
            assert "concernSet" in cond, \
                "고민 칸이 고른 사실을 안 보오 — 기본값이 켜진 채로 뜨오"
        if "s.sex ===" in cond:
            assert "sexSet" in cond, \
                "성별 칸이 고른 사실을 안 보오 — 사내가 안 누르고 지나가오"


def test_the_tier_is_not_chosen_for_the_customer():
    """값을 치르는 자리에서 대신 골라 주지 않는다."""
    src = _src("app/pay/page.tsx")
    assert "useState<Tier | null>(null)" in src, \
        "목패가 기본값으로 켜진 채 시작하오"
    assert "setPick(null)" in src, \
        "이 캐릭터에 없는 목패를 골라 둔 채로 두오"


# ── 무엇을 눌러야 하는지 말하는가 ────────────────────────
def test_every_choice_says_press_me():
    """
    칸이 예쁘게 늘어서 있으면 **읽는 것**처럼 보인다. 누르는 것이라고
    말해 줘야 누른다.
    """
    for rel, n in (("app/page.tsx", 4), ("app/pay/page.tsx", 1)):
        got = _src(rel).count("pickme")
        assert got >= n, "%s 에 「누르시오」 줄이 모자라오 (%d/%d)" % (rel, got, n)


def test_the_gate_says_what_is_missing():
    """
    「날을 다 적어야 가오」 라고만 하면, 성별을 안 고른 사람은
    날짜만 들여다본다. 무엇이 비었는지 말해야 한다.
    """
    src = _src("app/page.tsx")
    assert "여인·사내 중 하나를 누르시오" in src, \
        "성별이 비었을 때 그 말을 안 하오"


def test_a_dead_button_looks_dead():
    """
    눌리는 줄 알고 누르면 그게 고장으로 읽힌다.
    """
    css = _src("styles/overrides.css")
    assert ".btn:disabled" in css, "못 누르는 버튼이 눌리는 것처럼 보이오"
    assert "cursor: not-allowed" in css


def test_the_breathing_stops_for_reduced_motion():
    """
    ★ 안 고른 칸이 숨을 쉬게 했습니다. 동작 줄이기를 켠 사람에게는
      멈춰 있어야 합니다 — 이 집이 다른 자리에서 지키는 규칙입니다.
    """
    css = _src("styles/overrides.css")
    i = css.index("pickbreath")
    head = css[max(0, i - 400):i]
    assert "prefers-reduced-motion: no-preference" in head, \
        "동작 줄이기를 켠 사람에게도 칸이 움직이오"
