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


# ══════════════════════════════════════════════════════════
# 반쪽 점수를 멀쩡한 점수처럼 내지 않는가
# ══════════════════════════════════════════════════════════
#
# ★ 무슨 일이 있었나 (2026-09-03)
#
#   연출 점수는 화면 글이 코드에 박혀 있어서 `apps/web/**/page.tsx` 를
#   **소스째 읽어서** 셉니다. 그런데 배포 이미지(Dockerfile)에는
#   `seed/` 와 `services/api/` 만 들어갑니다 — `apps/web` 이 없습니다.
#
#   그러면 스물일곱 화면이 **엔진이 짓는 여섯**으로 줄고, 그런데도
#   합계는 그럴듯하게 나옵니다. 실제로 배포본 관리자 화면에
#   「합 63 · 화면 6」 이 아무 표시 없이 떠 있었습니다.
#
#   `screenscan.has_source()` 가 그 사실을 이미 들고 있었습니다.
#   **아무도 안 읽고 있었을 뿐입니다** — 화면도, 도구도.
#
#   틀린 숫자를 내느니 못 잰다고 말합니다.
def test_summary_carries_has_source():
    rows = S.scan_all()
    assert S.summary(rows).get("has_source") is True, \
        "저장소에서 돌리는데 화면 소스를 못 읽었소"


def test_summary_says_it_cannot_measure_without_sources(monkeypatch, tmp_path):
    """
    화면 소스도 찍어 둔 글도 없으면 깃발이 내려가야 한다 — 숫자가 나와도.

    ★ 2026-09-03 부터 소스가 없어도 **찍어 둔 글**(seed/screen_text.json)
      이 있으면 잽니다 — 배포본이 그 길로 점수를 냅니다. 그러니 여기서는
      둘 다 없는 자리를 흉내 냅니다. 찍어 둔 글이 있는 쪽은
      tests/test_screen_snapshot.py 가 봅니다.
    """
    monkeypatch.setattr(S, "WEB", tmp_path / "없는자리")
    monkeypatch.setattr(S, "SNAP", tmp_path / "없는_스냅.json")
    S._screens.cache_clear()
    try:
        sm = S.summary(S.scan_all())
        assert sm["has_source"] is False
        assert sm["source"] == "none"
        # 엔진 글은 여전히 잡히므로 숫자 자체는 나옵니다. 그래서 더
        # 위험합니다 — 읽는 쪽이 깃발을 봐야 합니다.
        assert sm["screens"] < 10, "소스 없이 스물일곱이 잡힐 리 없소"
    finally:
        S._screens.cache_clear()


def _admin_page() -> str:
    return (WEB / "app" / "admin" / "page.tsx").read_text(encoding="utf-8")


def test_admin_screen_reads_the_flag():
    """관리자 화면이 깃발을 보고 갈라야 한다."""
    src = _admin_page()
    assert "has_source" in src, \
        "/admin 이 has_source 를 안 보오 — 반쪽 점수가 그대로 뜨오"


def test_cli_reads_the_flag():
    src = (ROOT / "tools" / "drama_audit.py").read_text(encoding="utf-8")
    assert "has_source" in src, \
        "drama_audit 이 has_source 를 안 보오"


# ══════════════════════════════════════════════════════════
# 재는 화면이 지도와 같은가 — 조용히 빠뜨리지 않는가
# ══════════════════════════════════════════════════════════
#
# ★ 무슨 일이 있었나 (2026-09-03)
#
#   `tools/screen_graph.py` 는 「화면 32 / 32」 라 적고, 연출 자는
#   스물일곱만 쟀습니다. **아무도 그 다섯을 안 물었습니다.**
#
#   빠진 다섯 중 s1·s2 는 `app/s/[token]/SharedView.tsx` 였습니다 —
#   남이 보낸 링크로 **이 집을 처음 보는 사람**이 서는 자리입니다
#   (docs/15). 그 화면이 점수 밖에 있었고, 넣어 보니 45점으로
#   스물여덟 중 꼴찌였습니다.
#
#   나머지 셋(c8 내보내기 · g2 되짚기 · g3 차 한 잔)은 다른 화면
#   **안의 구역**이라 따로 안 섭니다. 그건 빠진 게 아니라 없는
#   것이라, 여기 적어 두고 셈에서 뺍니다.
SECTIONS = {"c8", "g2", "g3", "s2"}   # 다른 화면 안의 구역


def test_every_named_screen_is_measured():
    S._screens.cache_clear()
    got = set(S._screens())
    want = set(S.KO) - SECTIONS
    missing = sorted(want - got)
    assert not missing, (
        "이름은 있는데 점수를 안 재는 화면: %s\n"
        "  `<Shell screen=\"…\">` 선언이 없거나 screenscan.PAGES 에 "
        "그 파일이 없소." % missing)


def test_share_entry_is_measured():
    """공유로 건너오는 자리는 **처음 오는 사람**이 서는 곳이다."""
    S._screens.cache_clear()
    assert "s1" in S._screens(), \
        "공유 유입 화면(s1)이 점수 밖에 있소 — 처음 오는 사람이 서는 자리요"


# ══════════════════════════════════════════════════════════
# 점수표가 **실시간**으로 붙어 있는가
# ══════════════════════════════════════════════════════════
#
# ★ 손님이 시킨 것 (2026-09-03)
#
#   "성신당 연출감사표는 항상 관리자페이지에서 실시간으로 연동되어
#   있는 점수표 볼 수 있게해줘. 수정하면 또 수정한거 파악해서 점수가
#   매번 실시간으로 연동되어야해."
#
#   서버는 캐시를 안 겁니다 — `/v1/admin/screens` 가 부를 때마다
#   `_screens.cache_clear()` 하고 다시 읽습니다. 그런데 **화면이 처음
#   한 번만 물어봤습니다.** 글을 고치고 돌아와도 옛 점수가 그대로
#   떠 있었고, 그러면 도구를 안 믿게 됩니다.
def test_admin_screen_polls_for_fresh_scores():
    src = _admin_page()
    assert "setInterval" in src, "주인 화면이 되풀이해 안 묻소 — 실시간이 아니오"
    assert "visibilitychange" in src, \
        "안 보는 탭에도 계속 묻소 — 보고 있을 때만 물어야 하오"


def test_screens_endpoint_clears_its_cache():
    src = (ROOT / "services" / "api" / "routers" / "admin.py").read_text(
        encoding="utf-8")
    assert "cache_clear()" in src, \
        "점수를 캐시한 채로 내면 고쳐도 안 움직이오"
