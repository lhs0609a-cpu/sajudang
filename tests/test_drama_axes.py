# -*- coding: utf-8 -*-
"""
연출 점수 — 손님이 이름 붙인 **여섯 축**이 다 있고, 보는 자리에 뜨는가.

★ 손님이 시킨 것 (2026-09-02 · 09-03, 두 번)

  "미드처럼 다음 무조건 보게 만들고, 팩폭하고, **감성적으로 눈물이 핑
  돌게** 하고, 명확하고, 쉽게 설명하고, **비유로** 설명하고, 이런 거
  점수로 만들어서 **각 페이지마다 몇 점인지 띄어놓으라고** 했잖아.
  **수정해도 점수가 연동되게끔.**"

★ 그때까지 있던 것

  넷이었습니다 — 당김 · 팩폭 · 충실 · 쉬움. 「눈물이 핑」 은 축이
  없어서 **아무도 안 재고 있었고**, 비유는 쉬움 안에 25점으로 얹혀
  있어서 스물두 컷짜리 리포트도 「셈이오」 한 번이면 만점이었습니다.

  그리고 점수는 `/admin` 안에만 있었습니다. 화면을 고치는 사람은 그
  화면을 **보면서** 고치는데, 점수를 보려면 다른 주소로 옮겨 가서 표를
  찾아야 했습니다. 그러면 안 봅니다.

  자를 여섯으로 늘리자마자 울림 52 · 비유 29 가 나왔습니다. 안 세던
  것이 못하던 것입니다.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import dramaturgy as D          # noqa: E402
from engine import screenscan as S          # noqa: E402

# 손님이 부른 이름 그대로
AXES = ("pull", "bite", "heart", "clear", "plain", "figure")
KO = ("당김", "팩폭", "울림", "명확", "쉬움", "비유")


def test_six_axes_exist():
    """넷으로 되돌아가면 「눈물이 핑」 은 다시 아무도 안 잰다."""
    got = D.score("t", "재보기", "<p>그대는 참아 왔소.</p>")
    for k in AXES:
        assert k in got, "%s 축이 없다" % k
        assert 0 <= got[k] <= 100, "%s 가 0~100 밖이다: %s" % (k, got[k])
    assert got["total"] == round(sum(got[k] for k in AXES) / 6), \
        "합이 여섯의 평균이 아니다"


def test_every_screen_carries_all_six():
    S._screens.cache_clear()
    rows = S.scan_all()
    assert rows, "잰 화면이 없다"
    for r in rows:
        for k in AXES:
            assert k in r, "%s 에 %s 가 없다" % (r["id"], k)
    s = S.summary(rows)
    for k in AXES:
        assert k in s, "요약에 %s 가 없다" % k


def test_heart_counts_something_countable():
    """
    감정은 못 세는 게 아니라 **세는 자리**를 정하면 된다.

    호명 · 겪은 마음의 말 · 지난 일을 짚는 말 · 짧게 끊는 줄.
    """
    warm = D.score("t", "", "<p>그대는 말 못 하고 미뤄 왔을 게요.</p>"
                            "<p>그건 게으름이 아니오.</p>")
    cold = D.score("t", "", "<p>이 구조는 식신이 강한 배치에 해당한다.</p>")
    assert warm["heart"] > cold["heart"], "울림이 아무것도 안 세고 있다"


def test_preaching_is_a_penalty():
    """울컥하는 건 알아준다고 느낄 때지, 훈계받을 때가 아니다."""
    plain = D.score("t", "", "<p>그대는 참아 왔을 게요.</p><p>그랬소.</p>")
    preach = D.score("t", "", "<p>그대는 참아 왔을 게요.</p>"
                              "<p>그랬소.</p><p>힘내시오.</p>")
    assert preach["heart"] < plain["heart"], "훈계에 감점이 없다"


def test_one_metaphor_no_longer_carries_a_long_report():
    """비유는 분량을 본다 — 스물두 컷에 「셈이오」 하나면 모자라다."""
    short = D.score("t", "", "<p>거울 두 장을 마주 세우는 셈이오.</p>")
    long_ = D.score("t", "", "<p>거울 두 장을 마주 세우는 셈이오.</p>"
                             + "<p>" + ("가" * 1400) + "</p>")
    assert short["figure"] == 100
    assert long_["figure"] < 60, "긴 글에 비유 하나로 만점이 나온다"


def test_the_score_is_shown_where_the_screen_is():
    """보는 자리에 있어야 본다 — 관리자 레일에 이 화면 점수가 뜬다."""
    rail = (WEB / "components" / "DevRail.tsx").read_text(encoding="utf-8")
    assert "RailScore" in rail, "레일에 점수판이 없다"
    assert "/v1/admin/screens" in rail, "레일이 점수를 안 받아 온다"
    for ko in KO:
        assert ko in rail, "레일에 %s 축이 없다" % ko
    # 모자란 것까지 내야 무엇을 고칠지 안다
    assert "missing" in rail, "무엇이 모자란지 안 보여 준다"

    # 화면이 제 이름을 알려야 그 화면 점수를 찾는다
    shell = (WEB / "components" / "Shell.tsx").read_text(encoding="utf-8")
    assert "setSession({ screen })" in shell, "화면 이름을 안 알린다"


def test_admin_table_shows_six_columns_too():
    """CLI · 레일 · 주인 자리가 **같은 것**을 봐야 한다."""
    src = (WEB / "app" / "admin" / "page.tsx").read_text(encoding="utf-8")
    for ko in KO:
        assert ko in src, "주인 자리 표에 %s 가 없다" % ko
    assert "depth" not in src, "옛 축(충실)이 남아 있다"
