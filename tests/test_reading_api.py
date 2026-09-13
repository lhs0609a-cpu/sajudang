"""Exercise serialization, paid access and input isolation through the real API."""
from copy import deepcopy
from fastapi.testclient import TestClient
import pytest
import store
from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def chart(client):
    response = client.post("/v1/chart", json={"year": 1993, "month": 11, "day": 25,
        "hour": 15, "minute": 0, "hour_known": True, "sex": "F", "birth_city": "서울"})
    assert response.status_code == 200
    return response.json()["chart_id"]


def paid(session, tier):
    key = "reading-test:" + session
    store.set_json("order:" + key, {"session_id": session, "tier": tier, "status": "paid", "lens_id": "pungun"})
    store.set_json("orders:" + session, [key])


def test_client_tier_cannot_unlock_new_reading_sections(client, chart):
    response = client.post("/v1/report", json={"chart_id": chart, "lens_id": "pungun", "tier": "all", "session_id": "reading-unpaid", "concern": "work"})
    assert response.status_code == 200
    result = response.json()
    assert result["tier"] == "free" and len(result["reading"]["summary"]) <= 1
    assert not {"decision", "timing", "review"} & {s["id"] for s in result["reading"]["sections"]}
    denied = client.post("/v1/omnibus", json={"chart_id": chart, "session_id": "reading-unpaid"})
    assert denied.status_code == 402 and "reading" not in denied.json()


def test_paid_book_and_refunded_access(client, chart):
    session = "reading-paid-book"
    paid(session, "all")
    request = {"chart_id": chart, "session_id": session, "concern": "work"}
    response = client.post("/v1/omnibus", json=request)
    assert response.status_code == 200
    result = response.json()
    assert result["reading"]["scope"] == "전체"
    order = store.get_json("order:reading-test:" + session)
    assert order["opened_at"]
    order["status"] = "refunded"
    store.set_json("order:reading-test:" + session, order)
    assert client.post("/v1/omnibus", json=request).status_code == 402


def test_consultation_changes_rendered_result_without_persisting_answers(client, chart):
    request = {"chart_id": chart, "lens_id": "pungun", "session_id": "reading-input", "concern": "work"}
    original = deepcopy(store.get_json(store.k_chart(chart)))
    before = client.post("/v1/report", json=request).json()["reading"]
    question = next(q for q in before["consultation"]["questions"] if q["id"].startswith("claim:"))
    response = client.post("/v1/report", json={**request, "extras": {"consultation": {"concern": "work", "answers": {question["id"]: "no"}}}})
    assert response.status_code == 200
    after = response.json()["reading"]
    assert after["fingerprint"] != before["fingerprint"]
    assert before["summary"][0]["id"] not in {c["id"] for c in after["summary"]}
    assert store.get_json(store.k_chart(chart)) == original
    assert client.post("/v1/report", json=request).json()["reading"]["fingerprint"] == before["fingerprint"]
