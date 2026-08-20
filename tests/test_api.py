"""
API 계층 테스트 — docs/02 §5

여기서 지키는 것
    · 문장 원문·뱅크 키·조건식이 응답에 새지 않는다
    · 계산할 수 없으면 지어내지 않고 거절한다
    · 브레이크가 실제로 막는다
    · 공감률은 100건 전에는 숫자를 주지 않는다
"""
from __future__ import annotations

import os
import tempfile

import pytest

os.environ.setdefault("STATEMENT_LOG_PATH",
                      os.path.join(tempfile.gettempdir(), "sajudang_test_log.jsonl"))

from fastapi.testclient import TestClient          # noqa: E402

import store                                       # noqa: E402
from main import app                               # noqa: E402

BIRTH = {"year": 1993, "month": 5, "day": 15, "hour": 10, "minute": 20,
         "hour_known": True, "sex": "F", "birth_city": "서울"}


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def chart_id(client):
    return client.post("/v1/chart", json=BIRTH).json()["chart_id"]


# ── /health ────────────────────────────────────────────────
def test_health(client):
    r = client.get("/health").json()
    assert r["ok"] is True
    assert r["tz_source"].startswith("tzdata"), "tzdata 없이 돌고 있습니다"


# ── /v1/chart ──────────────────────────────────────────────
def test_chart_returns_features(client):
    r = client.post("/v1/chart", json=BIRTH)
    assert r.status_code == 200
    f = r.json()["features"]
    assert [p["gz"] for p in f["pillars"]] == ["癸酉", "丁巳", "丙申", "癸巳"]


def test_chart_is_cached(client):
    client.post("/v1/chart", json=BIRTH)
    assert client.post("/v1/chart", json=BIRTH).json()["cached"] is True


def test_chart_rejects_hour_known_without_hour(client):
    bad = dict(BIRTH, hour=None, minute=None, hour_known=True)
    assert client.post("/v1/chart", json=bad).status_code == 422


def test_chart_rejects_out_of_range_year(client):
    assert client.post("/v1/chart", json=dict(BIRTH, year=1850)).status_code == 422


def test_chart_without_hour_returns_three_pillars(client):
    r = client.post("/v1/chart",
                    json=dict(BIRTH, hour=None, minute=None, hour_known=False))
    f = r.json()["features"]
    assert len(f["pillars"]) == 3
    assert f["correction"]["hour_used"] is False


# ── /v1/hook ───────────────────────────────────────────────
def test_hook_returns_segments(client, chart_id):
    r = client.post("/v1/hook", json={"chart_id": chart_id, "concern": "love",
                                      "axis4": "INFP", "lens_id": "pungun"})
    assert r.status_code == 200
    segs = r.json()["segments"]
    assert [s["stage"] for s in segs] == ["0", "1", "2", "2.5", "3"]
    assert all(s["statement_id"] for s in segs)


def test_hook_unknown_chart_id(client):
    r = client.post("/v1/hook", json={"chart_id": "nope", "concern": "love"})
    assert r.status_code == 404


def test_hook_response_carries_no_bank_internals(client, chart_id):
    """뱅크 표 이름·조건식이 응답에 새면 안 된다."""
    raw = client.post("/v1/hook",
                      json={"chart_id": chart_id, "concern": "love"}).text
    for leak in ("STAB", "IGNITE", "BLAME", "NAME2", "MYTH_TG", "IGKEY",
                 "priority", "condition"):
        assert leak not in raw, leak


# ── /v1/report ─────────────────────────────────────────────
def test_report_tier_gating(client, chart_id):
    free = client.post("/v1/report", json={
        "chart_id": chart_id, "lens_id": "pungun", "tier": "free",
        "concern": "love"}).json()
    all_ = client.post("/v1/report", json={
        "chart_id": chart_id, "lens_id": "pungun", "tier": "all",
        "concern": "love"}).json()
    assert free["locked"] and not all_["locked"]
    assert len(all_["cuts"]) > len(free["cuts"])


def test_report_unknown_lens(client, chart_id):
    r = client.post("/v1/report", json={
        "chart_id": chart_id, "lens_id": "없는캐릭터", "tier": "free",
        "concern": "love"})
    assert r.status_code == 404


# ── /v1/relay ──────────────────────────────────────────────
def test_relay_recommends_and_blocks(client, chart_id):
    store.clear_all()
    cid = client.post("/v1/chart", json=BIRTH).json()["chart_id"]
    body = {"chart_id": cid, "session_id": "t-block", "read": ["pungun"]}

    first = client.post("/v1/relay", json=body).json()
    assert first["blocked"] is False
    assert 1 <= len(first["recommend"]) <= 3

    limit = first["breaks"]["per_session_relay"]
    for _ in range(limit):
        client.post("/v1/relay/consume", params={"session_id": "t-block"})

    after = client.post("/v1/relay", json=body).json()
    assert after["blocked"] is True
    assert after["recommend"] == []
    assert after["block_reason"]


def test_relay_response_carries_no_condition(client, chart_id):
    raw = client.post("/v1/relay", json={"chart_id": chart_id,
                                         "session_id": "t-leak"}).text
    assert '"condition"' not in raw
    assert '"op"' not in raw


# ── /v1/feedback · /v1/agreement ───────────────────────────
def test_feedback_records(client, chart_id):
    r = client.post("/v1/feedback", json={
        "statement_id": "stab:love:목", "chart_id": chart_id,
        "answer": 1, "stage": "0", "concern": "love"})
    assert r.status_code == 200 and r.json()["ok"] is True


def test_agreement_hidden_below_threshold(client, chart_id):
    r = client.get("/v1/agreement", params={"statement_id": "seed:none"}).json()
    assert r["shown"] is False
    assert "rate" not in r
    assert r["min_responses"] >= 100


def test_feedback_rejects_bad_answer(client, chart_id):
    r = client.post("/v1/feedback", json={
        "statement_id": "x", "chart_id": chart_id, "answer": 7})
    assert r.status_code == 422


# ── /v1/daily ──────────────────────────────────────────────
def test_daily(client, chart_id):
    r = client.get("/v1/daily", params={"chart_id": chart_id}).json()
    assert len(r["gz"]) == 2
    assert 12 <= r["score"] <= 96
    assert r["text"]


# ── 가드 미들웨어 ───────────────────────────────────────────
def test_guard_middleware_catches_a_leaking_route(client):
    """새 라우터가 enforce 를 빠뜨려도 미들웨어가 잡는다."""
    from fastapi import APIRouter

    r = APIRouter()

    @r.get("/_test/leak")
    def leak() -> dict:
        return {"text": "적중률 92% 입니다"}

    app.include_router(r)
    try:
        got = client.get("/_test/leak").json()
        assert "적중률 92%" not in got["text"]
    finally:
        app.router.routes = [
            x for x in app.router.routes
            if getattr(x, "path", None) != "/_test/leak"]
