"""
관리자 레일 — 기본값 스위치가 살아 있는가, 사람이 끈 것이 되살아나지 않는가.

이 셋 중 하나라도 무너지면 조용히 망가집니다.
  · 기본값이 코드에 박히면  → 출시 때 끌 방법이 없습니다.
  · adminSet 이 없어지면    → 껐던 레일이 다음 방문에 도로 켜집니다.
  · adminSet 이 저장 안 되면 → 새로고침마다 도로 켜집니다.

docs/17 §4
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAIL = ROOT / "apps" / "web" / "components" / "DevRail.tsx"
STORE = ROOT / "apps" / "web" / "lib" / "store.ts"
ENVEX = ROOT / "apps" / "web" / ".env.example"
DOC = ROOT / "docs" / "17_배포_운영_설계.md"

ENV = "NEXT_PUBLIC_ADMIN_DEFAULT"


def rail() -> str:
    return RAIL.read_text(encoding="utf-8")


def store() -> str:
    return STORE.read_text(encoding="utf-8")


# ── 출시 때 끌 수 있는가 ────────────────────────────────
def test_default_comes_from_the_build_not_from_code():
    assert ENV in rail(), "기본값이 코드에 박혀 있으면 출시 때 끌 수 없습니다"


def test_default_is_on_until_someone_sets_zero():
    """값이 없으면 켜짐이어야 합니다 — 아직 출시 전입니다."""
    assert 'process.env.%s !== "0"' % ENV in rail()


def test_the_switch_is_written_down():
    assert ENV in ENVEX.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")
    assert ENV in doc
    assert "vercel env add %s production" % ENV in doc


# ── 사람이 정한 것이 기본값을 이기는가 ──────────────────
def test_store_remembers_that_a_person_chose():
    s = store()
    assert "adminSet: boolean;" in s, "사람이 정했는지 기억할 자리가 없습니다"
    assert "adminSet: false," in s


def test_the_choice_survives_a_reload():
    """partialize 에 없으면 새로고침마다 기본값이 도로 켭니다."""
    s = store()
    part = s[s.index("partialize:"):]
    part = part[:part.index("}),")]
    assert "adminSet: s.adminSet" in part


def test_explicit_choice_is_recorded_both_ways():
    r = rail()
    assert 's.set({ admin: true, adminSet: true })' in r
    assert 's.set({ admin: false, adminSet: true })' in r


def test_default_only_applies_when_nobody_chose():
    """이 조건이 빠지면 ?admin=0 으로 끈 레일이 다음 방문에 되살아납니다."""
    assert "!s.adminSet && ADMIN_DEFAULT" in rail()


def test_the_effect_reruns_when_the_choice_changes():
    r = rail()
    assert "[params, s.adminSet]" in r, "adminSet 이 의존성에 없으면 즉시 반영되지 않습니다"


# ── 끄는 방법이 화면 안에 있는가 ────────────────────────
def test_there_is_a_way_to_turn_it_off_without_the_url():
    r = rail()
    assert 'className="railoff"' in r
    assert "숨기기" in r
    css = (ROOT / "apps" / "web" / "styles" / "overrides.css").read_text(encoding="utf-8")
    assert ".railoff {" in css


def test_the_rail_is_never_in_the_server_html():
    """
    첫 그림에 레일이 있으면 하이드레이션이 어긋납니다. 초기값은 항상 꺼짐이고
    켜는 일은 DevRail 의 effect 가 합니다.
    """
    s = store()
    head = s[s.index("admin: false,"):]
    assert head.startswith("admin: false,")
