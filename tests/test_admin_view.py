# -*- coding: utf-8 -*-
"""
주인 자리로 들어오면 값으로 잠긴 것이 다 열리는가.

★ 여기서 지키는 것

    · 주인 쪽지가 있으면 유료 컷이 다 열린다 (치른 주문이 없어도)
    · 쪽지가 없거나 틀리면 **아무것도 달라지지 않는다** — 손님은 손님
    · 화면이 `tier="all"` 이라 말하는 것만으로는 안 열린다 (그건 가림)
    · 주인도 손님 눈으로 볼 수 있다 (`x-admin-view: guest`)

★ 왜 이 검사가 필요한가

  자격을 여는 자리는 「열려 있는 편이 편해서」 넣은 것이라, 한 번
  느슨해지면 아무도 안 죽고 숫자만 틀립니다. 여는 근거가 **서버에서
  맞은 쪽지**여야 한다는 것을 못 박아 둡니다.
"""
from __future__ import annotations

import os
import sys
import tempfile
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))
os.environ.setdefault("STATEMENT_LOG_PATH",
                      os.path.join(tempfile.gettempdir(),
                                   "sajudang_adminview_log.jsonl"))
warnings.filterwarnings("ignore")

EMAIL = "owner@sajudang.test"
PW = "열어라-참깨-9900"
BIRTH = {"year": 1993, "month": 5, "day": 15, "hour": 10, "minute": 20,
         "hour_known": True, "sex": "F", "birth_city": "서울"}
LENS = "pungun"


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


@pytest.fixture()
def chart_id(client):
    return client.post("/v1/chart", json=BIRTH).json()["chart_id"]


@pytest.fixture()
def token(monkeypatch):
    """주인 문을 걸고 한 번 들어갑니다 — 비밀번호는 여기서만 오갑니다."""
    import adminauth
    monkeypatch.setattr(adminauth, "ADMIN_EMAIL", EMAIL)
    monkeypatch.setattr(adminauth, "ADMIN_PASSWORD_HASH",
                        adminauth.make_hash(PW, rounds=1000))
    return adminauth.login(EMAIL, PW)


def _report(client, chart_id, headers=None, tier="free"):
    return client.post("/v1/report", headers=headers or {}, json={
        "chart_id": chart_id, "lens_id": LENS, "tier": tier,
        "session_id": "adminview-test", "concern": "money"})


# ── 손님은 손님 ───────────────────────────────────────────
def test_guest_still_pays(client, chart_id):
    """쪽지가 없으면 달라지는 것이 하나도 없다."""
    r = _report(client, chart_id, tier="all")
    assert r.status_code == 200
    body = r.json()
    assert body["tier"] == "free"
    assert body["locked"], "값을 안 치렀는데 잠긴 자리가 없습니다"


def test_a_wrong_note_opens_nothing(client, chart_id, token):
    """쪽지가 틀리면 손님입니다 — 아무 값이나 실어 보내도."""
    r = _report(client, chart_id, headers={"x-admin-token": token + "x"})
    assert r.json()["tier"] == "free"


# ── 주인은 다 본다 ────────────────────────────────────────
def test_the_owner_opens_everything(client, chart_id, token):
    """치른 주문이 없어도 주인은 다 본다."""
    guest = _report(client, chart_id).json()
    owner = _report(client, chart_id, headers={"x-admin-token": token}).json()
    assert owner["tier"] == "all"
    assert owner["locked"] == [], "주인 자리인데 잠긴 컷이 남았습니다"
    assert len(owner["cuts"]) > len(guest["cuts"])


def test_the_owner_opens_the_twenty(client, chart_id, token):
    """스무 사람 종합도 같은 쪽지로 열린다."""
    body = {"chart_id": chart_id, "session_id": "adminview-test",
            "concern": "money"}
    assert client.post("/v1/omnibus", json=body).status_code == 402
    assert client.post("/v1/omnibus", json=body,
                       headers={"x-admin-token": token}).status_code == 200


def test_the_owner_can_look_like_a_guest(client, chart_id, token):
    """주인도 무료 구간이 어떻게 보이는지 봐야 한다."""
    r = _report(client, chart_id, headers={"x-admin-token": token,
                                           "x-admin-view": "guest"})
    assert r.json()["tier"] == "free"


def test_the_machine_key_also_opens(client, chart_id):
    """기계 문(FUNNEL_KEY)으로도 열린다 — 지키는 자리는 한 곳이다."""
    import keyguard
    keyguard.FUNNEL_KEY = "right-key"
    try:
        assert _report(client, chart_id,
                       headers={"x-funnel-key": "wrong"}).json()["tier"] == "free"
        assert _report(client, chart_id,
                       headers={"x-funnel-key": "right-key"}).json()["tier"] == "all"
    finally:
        keyguard.FUNNEL_KEY = ""


# ── 브레이크는 그대로 ─────────────────────────────────────
def test_brakes_stay_on_for_the_owner(client, token):
    """
    값으로 잠긴 것만 엽니다. 릴레이 상한은 손님을 지키는 자리라
    주인에게도 그대로 돕니다 (CLAUDE.md 절대 규칙 4).
    """
    import adminview
    src = Path(ROOT / "services" / "api" / "adminview.py").read_text(encoding="utf-8")
    assert "relay" not in src.lower(), "브레이크를 이 자리에서 건드리고 있습니다"
    assert adminview.on() is False, "요청이 끝난 뒤에도 주인 자리가 켜져 있습니다"
