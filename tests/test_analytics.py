"""
계측 — 개인정보가 안 새는가, 퍼널이 맞게 세는가.

여기가 무너지면 두 가지 중 하나가 일어납니다.
  · 개인정보가 이벤트에 실려 쌓입니다 (돌이킬 수 없습니다)
  · 숫자가 틀린 채로 초반을 고칩니다 (헛수고입니다)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))


@pytest.fixture()
def an(tmp_path, monkeypatch):
    """DB 없이 JSONL 경로로 돌린다."""
    import analytics
    monkeypatch.setattr(analytics, "EVENT_LOG_PATH", tmp_path / "events.jsonl")
    import db
    monkeypatch.setattr(db, "HAS_DB", False)
    return analytics


# ══════════════════════════════════════════════════════════
# ★ 개인정보 — 서버가 막는가
# ══════════════════════════════════════════════════════════
def test_unknown_event_name_is_dropped(an):
    assert an.record([{"name": "birth_leak", "screen": "a1", "sid": "s" * 20}]) == 0


def test_unknown_screen_is_dropped(an):
    """화면 이름 자리에 개인정보가 실려 와도 통과하지 못한다."""
    assert an.record([
        {"name": "screen", "screen": "이현석 1993-05-15", "sid": "s" * 20},
    ]) == 0


def test_bad_session_key_is_dropped(an):
    for sid in ["", "짧", "../../etc/passwd", "a" * 200,
            "1993-05-15",          # ★ 생년월일이 열쇠로 통과하면 안 된다
            "abcdefgh"]:           # 8자는 너무 짧다
        assert an.record([{"name": "screen", "screen": "a1", "sid": sid}]) == 0


def test_extra_fields_are_never_stored(an):
    """모르는 열쇠는 통째로 버린다 — 문자열 자리를 열어 두면 언젠가 샌다."""
    an.record([{
        "name": "screen", "screen": "a1", "sid": "sess1234567890ab",
        "name_text": "이현석", "birth": "1993-05-15", "chart_id": "abc",
        "ip": "1.2.3.4", "email": "a@b.c",
    }])
    raw = an.EVENT_LOG_PATH.read_text(encoding="utf-8")
    for leaked in ["이현석", "1993-05-15", "abc", "1.2.3.4", "a@b.c"]:
        assert leaked not in raw, leaked
    row = json.loads(raw.strip())
    assert set(row) <= {"name", "screen", "sid", "at", "stage", "ms", "n", "yes"}


def test_number_fields_must_be_numbers(an):
    an.record([{"name": "hook_answer", "screen": "a7", "sid": "sess1234567890ab",
                "stage": "이현석", "yes": 1}])
    row = json.loads(an.EVENT_LOG_PATH.read_text(encoding="utf-8").strip())
    assert "stage" not in row          # 숫자가 아니면 버린다
    assert row["yes"] == 1


def test_event_model_has_no_identifying_columns():
    """
    없는 컬럼이 곧 약속입니다. chart_id 도 없어야 합니다 —
    생년월일시 해시라서 같은 생일이면 같은 값이 나옵니다.
    """
    import models
    cols = {c.name for c in models.Event.__table__.columns}
    for banned in ["chart_id", "user_id", "ip", "email", "birth",
                   "birth_year", "city", "name_text", "phone"]:
        assert banned not in cols, banned


def test_batch_is_capped(an):
    many = [{"name": "screen", "screen": "a1", "sid": "sess1234567890ab"}] * 500
    assert an.record(many) == an.MAX_BATCH


def test_recording_never_raises(an, monkeypatch):
    """계측이 서비스를 멈추게 해서는 안 된다."""
    monkeypatch.setattr(an, "EVENT_LOG_PATH", Path("/뚫린/경로/없음/x.jsonl"))
    assert an.record([{"name": "screen", "screen": "a1", "sid": "sess1234567890ab"}]) == 0


# ══════════════════════════════════════════════════════════
# 퍼널 — 맞게 세는가
# ══════════════════════════════════════════════════════════
def _walk(an, sid, upto):
    order = [sc for sc, _ in an.FUNNEL]
    an.record([{"name": "screen", "screen": sc, "sid": sid}
               for sc in order[:upto]])


def test_funnel_counts_people_not_visits(an):
    """새로고침 100번이 숫자를 부풀리면 안 된다."""
    for _ in range(100):
        an.record([{"name": "screen", "screen": "a1", "sid": "sess0000000000a1"}])
    f = an.funnel()
    assert f["steps"][0]["sessions"] == 1


def test_funnel_drop_off(an):
    _walk(an, "sess0000000000a1", 11)      # 끝까지
    _walk(an, "sess0000000000a2", 3)       # a3 에서 멈춤
    _walk(an, "sess0000000000a3", 3)
    f = an.funnel()
    step = {s["screen"]: s for s in f["steps"]}
    assert step["a1"]["sessions"] == 3
    assert step["a3"]["sessions"] == 3
    assert step["a4"]["sessions"] == 1
    assert step["a4"]["lost"] == 2
    assert step["a4"]["from_prev"] == pytest.approx(33.3, abs=0.1)
    assert step["a1"]["from_top"] == 100.0


def test_funnel_is_empty_without_data(an):
    f = an.funnel()
    assert f["sessions"] == 0
    assert all(s["sessions"] == 0 for s in f["steps"])


def test_hook_stage_rates(an):
    an.record([
        {"name": "hook_shown", "screen": "a7", "sid": "sess0000000000a1", "stage": 0},
        {"name": "hook_answer", "screen": "a7", "sid": "sess0000000000a1", "stage": 0, "yes": 1},
        {"name": "hook_shown", "screen": "a7", "sid": "sess0000000000a2", "stage": 0},
        {"name": "hook_answer", "screen": "a7", "sid": "sess0000000000a2", "stage": 0, "yes": 0},
        {"name": "hook_shown", "screen": "a7", "sid": "sess0000000000a3", "stage": 0},
    ])
    h = {x["stage"]: x for x in an.funnel()["hook"]}
    assert h[0]["shown"] == 3
    assert h[0]["answered"] == 2
    assert h[0]["answer_rate"] == pytest.approx(66.7, abs=0.1)
    assert h[0]["yes_rate"] == 50.0


def test_funnel_order_matches_the_real_flow():
    """차례가 실제 화면 순서와 어긋나면 '어디서 새는지' 가 거짓이 된다."""
    import analytics
    assert [s for s, _ in analytics.FUNNEL] == [
        "a1", "a2", "a3", "a4", "a5", "a6", "a7", "d0", "d1", "d2", "d3"]
    assert set(s for s, _ in analytics.FUNNEL) <= analytics.SCREENS


# ══════════════════════════════════════════════════════════
# API
# ══════════════════════════════════════════════════════════
@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("EVENT_LOG_PATH", str(tmp_path / "e.jsonl"))
    monkeypatch.setenv("FUNNEL_KEY", "k" * 24)
    # routers 패키지가 events 를 속성으로 붙들고 있어 패키지째 비웁니다
    for m in [k for k in list(sys.modules)
              if k in ("analytics", "main") or k.startswith("routers")]:
        sys.modules.pop(m, None)
    from fastapi.testclient import TestClient
    import main
    return TestClient(main.app)


def test_post_events_filters_and_reports(client):
    r = client.post("/v1/events", json={"events": [
        {"name": "screen", "screen": "a1", "sid": "sess1234567890ab"},
        {"name": "screen", "screen": "비밀", "sid": "sess1234567890ab"},
    ]})
    assert r.status_code == 200
    assert r.json() == {"ok": True, "recorded": 1, "sent": 2}


def test_funnel_needs_the_key(client):
    assert client.get("/v1/funnel").status_code == 401
    assert client.get("/v1/funnel",
                      headers={"x-funnel-key": "wrong"}).status_code == 401
    assert client.get("/v1/funnel",
                      headers={"x-funnel-key": "k" * 24}).status_code == 200


def test_funnel_is_closed_when_no_key_is_set(tmp_path, monkeypatch):
    """열어 두는 쪽이 기본이면 언젠가 그대로 배포된다."""
    monkeypatch.setenv("EVENT_LOG_PATH", str(tmp_path / "e.jsonl"))
    monkeypatch.delenv("FUNNEL_KEY", raising=False)
    # routers 패키지가 events 를 속성으로 붙들고 있어 패키지째 비웁니다
    for m in [k for k in list(sys.modules)
              if k in ("analytics", "main") or k.startswith("routers")]:
        sys.modules.pop(m, None)
    from fastapi.testclient import TestClient
    import main
    assert TestClient(main.app).get("/v1/funnel").status_code == 503
