# -*- coding: utf-8 -*-
"""
글자가 앉는 자리 — 줄길이와 읽는 시간.

★ 왜 이 자가 생겼나 (2026-09-03)

  손님이 시킨 것 — "심리학적, uxui, 스킬, 디자인, 폰트종류, 가독성,
  폰트크기 등등 … 읽기속도랑 줄길이도 넣어줘."

  여섯 축은 **무슨 말을 했는가**를 봅니다. 이 둘은 그 말이 **화면
  폭에 어떻게 앉는가**를 봅니다. 같은 문장도 한 줄에 마흔 자로 앉으면
  눈이 되돌아올 자리를 잃습니다.

★ 자가 하나여야 한다

  화면 폭·글자 크기·읽는 속도는 세 곳이 함께 알아야 합니다 —
  주인 화면의 점수(engine), 과부 줄 도구(tools/widow.py), 그리고
  손님에게 「읽는 데 약 N분」 이라 적는 자리(routers/pay.py).

  두 벌로 두면 화면 폭을 바꾸는 날 한쪽만 고칩니다. 여기서 잠급니다.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT / "tools"))

from engine import dramaturgy as D          # noqa: E402
from engine import typo as T                # noqa: E402


# ── 자가 하나인가 ─────────────────────────────────────────
def test_widow_tool_uses_the_engine_ruler():
    """도구가 제 나름의 폭을 또 들고 있으면 언젠가 갈린다."""
    import widow
    assert widow.WIDTH is T.WIDTH
    assert widow.SIZE is T.SIZE
    assert widow.wrap is T.wrap
    assert widow.width_of is T.width_of


def test_reading_speed_matches_what_we_tell_the_customer():
    """
    목패에 「읽는 데 약 N분」 이라 적을 때 쓰는 수와 같아야 한다.

    다르면 손님에게는 6분이라 적고 주인 화면에는 4분이라 뜬다.
    """
    src = (ROOT / "services" / "api" / "routers" / "pay.py").read_text(
        encoding="utf-8")
    m = re.search(r"^CHARS_PER_MINUTE\s*=\s*(\d+)", src, re.M)
    assert m, "routers/pay.py 에 CHARS_PER_MINUTE 가 없소"
    assert int(m.group(1)) == T.CHARS_PER_MINUTE, (
        "손님에게 말하는 속도와 점수의 속도가 다르오: 화면 %s · 점수 %s"
        % (m.group(1), T.CHARS_PER_MINUTE))


# ── 줄을 제대로 나누는가 ──────────────────────────────────
def test_wrap_breaks_only_at_spaces():
    """CSS 가 word-break: keep-all 이라 낱말 안에서는 안 끊긴다."""
    got = T.wrap("가나다라마바사아자차카타파하 " * 6)
    assert all(" " in ln or len(ln) <= 30 for ln in got)
    assert "".join(got).replace(" ", "") == ("가나다라마바사아자차카타파하" * 6)


def test_korean_is_wider_than_latin():
    assert T.width_of("가") == 1.0
    assert T.width_of("a") == 0.5


def test_paragraphs_split_on_breaks_and_newlines():
    """
    ★ 화면 글은 태그가 이미 걷힌 채로 옵니다 (screenscan._readable).
      거기서는 줄바꿈이 문단 경계입니다 — 안 그러면 화면 하나가
      통째로 한 문단이 되어 어느 화면이나 「벽으로 읽히오」 가 됩니다.
    """
    assert len(T.paragraphs("<p>하나</p><p>둘</p>")) == 2
    assert len(T.paragraphs("하나<br>둘")) == 2
    assert len(T.paragraphs("하나\n둘\n셋")) == 3


# ── 축이 무엇을 잡는가 ────────────────────────────────────
def _wall(n=400):
    return "가나다라 " * n


def test_a_wall_is_caught():
    """한 문단이 일곱 줄을 넘으면 벽으로 읽힌다."""
    got = D.score("t", "벽", "<p>%s</p>" % _wall(60), kind="read")
    assert got["measure"] < 100
    assert any("벽으로 읽히오" in m for m in got["missing"])


def test_broken_up_text_scores_better_than_one_block():
    """같은 글이라도 끊어 놓으면 낫다 — 이 집이 한 컷씩 띄우는 까닭."""
    body = "가나다라마바사아자차카타 " * 40
    one = D.score("t", "한덩이", "<p>%s</p>" % body, kind="read")
    many = D.score("t", "끊음",
                   "".join("<p>%s</p>" % ("가나다라마바사아자차카타 " * 4)
                           for _ in range(10)), kind="read")
    assert many["measure"] >= one["measure"]
    assert many["pace"] >= one["pace"]


def test_the_last_line_of_a_paragraph_may_be_short():
    """
    ★ 문단의 마지막 줄은 원래 짧다. 버튼 글자·라벨도 한 줄짜리다.
      그걸 다 세면 어느 화면이나 「조각 줄 스물다섯」 이 나오고,
      그 숫자는 고칠 데를 안 가리킨다.
    """
    got = D.score("t", "짧은끝",
                  "<p>가나다라마바사아자차카타파하 가나다라마바사.</p>"
                  "<p>예.</p>", kind="beat")
    assert not any("조각 줄" in m for m in got["missing"])


def test_pace_reads_the_screen_kind():
    """입력 화면에 리포트만큼 쏟으면 방해다. 읽는 자리는 길어도 된다."""
    long_ = "가나다라마바사아자차 " * 120
    body = "".join("<p>%s</p>" % ("가나다라마바사아자차 " * 4) for _ in range(30))
    assert D.score("t", "입력", body, kind="input")["pace"] < \
        D.score("t", "읽기", body, kind="read")["pace"]
    assert len(long_) > 0


def test_seconds_is_reported():
    got = D.score("t", "시간", "<p>%s</p>" % ("가나다 " * 100), kind="read")
    assert got["secs"] > 0
