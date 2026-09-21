"""
문의 창구 — 양쪽으로 흐르는가.

★ 한쪽으로만 흐르면 그건 창구가 아니라 **건의함**입니다.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

KEY = "k" * 24
SID = "sess-support-abcdefgh"


# ★ `keyguard` 와 `adminauth` 는 **치우지 않습니다.**
#
#   둘은 서로를 붙들고 있습니다 — `keyguard.require_admin` 은 부를 때마다
#   `import adminauth` 로 **그때의** 모듈을 찾고, `adminauth` 는 뜰 때
#   붙잡은 `store` 로 쪽지를 적습니다. 여기서 둘 중 하나만 새로 띄우면
#   쪽지를 적은 자리와 찾는 자리가 갈립니다. 그러면 멀쩡한 로그인이
#   401 이 되고, 깨지는 곳은 이 파일이 아니라 **다음 파일**입니다.
#
#   열쇠는 모듈에 직접 꽂습니다. monkeypatch 가 끝나고 되돌려 줍니다.
DIRTY = ("store", "payments", "db", "main", "analytics",
         "throttle", "audit", "errors", "backup")


def _evict():
    for m in [k for k in list(sys.modules)
              if k in DIRTY or k.startswith("routers")]:
        sys.modules.pop(m, None)


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("STORE_PATH", str(tmp_path / "s.sqlite"))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    _evict()
    import keyguard
    monkeypatch.setattr(keyguard, "FUNNEL_KEY", KEY)
    from fastapi.testclient import TestClient
    import main
    yield TestClient(main.app)
    _evict()


H = {"x-funnel-key": KEY}


def _ask(app, body="값을 치렀는데 리포트가 안 열리오.", topic="unlock"):
    return app.post("/v1/support",
                    json={"session_id": SID, "topic": topic, "body": body})


def test_갈래는_서버가_준다(app):
    """화면이 제 손으로 적으면 두 벌이 되어 어긋납니다."""
    d = app.get("/v1/support/topics").json()
    ids = {t["id"] for t in d["topics"]}
    assert {"unlock", "calc", "billing", "privacy", "other"} <= ids


def test_모르는_갈래는_안_받는다(app):
    """갈래가 자유 낱말이면 거기에도 사연이 실립니다."""
    r = app.post("/v1/support", json={"session_id": SID,
                                      "topic": "아무거나", "body": "어쩌고저쩌고"})
    assert r.status_code == 422


def test_걸고_받고_답하고_본다(app):
    r = _ask(app)
    assert r.status_code == 200, r.text
    tid = r.json()["id"]

    mine = app.get("/v1/support/mine", params={"session_id": SID}).json()
    assert mine["threads"][0]["id"] == tid
    assert mine["threads"][0]["status"] == "open"

    queue = app.get("/v1/admin/support", headers=H).json()["threads"]
    assert any(t["id"] == tid for t in queue)

    r = app.post("/v1/admin/support", headers=H,
                 json={"id": tid, "reply": "바로 열어 드리겠소."})
    assert r.status_code == 200, r.text

    # ★ 답이 손님에게 돌아와야 창구입니다.
    back = app.get("/v1/support/mine", params={"session_id": SID}).json()
    assert back["threads"][0]["reply"] == "바로 열어 드리겠소."
    assert back["threads"][0]["status"] == "closed"


def test_주인_큐에_누구인지_안_싣는다(app):
    _ask(app)
    body = app.get("/v1/admin/support", headers=H).text
    assert "user_key" not in body
    assert SID not in body


def test_문의_큐는_잠겨_있다(app):
    _ask(app)
    assert app.get("/v1/admin/support").status_code == 401
    assert app.post("/v1/admin/support",
                    json={"id": "x", "reply": "여보시오"}).status_code == 401


def test_답한_것이_감사기록에_남는다(app):
    tid = _ask(app).json()["id"]
    app.post("/v1/admin/support", headers=H, json={"id": tid, "reply": "곧 보겠소."})
    rows = app.get("/v1/admin/audit", headers=H).json()["rows"]
    assert any(r["type"] == "support.reply" and r["target"] == tid for r in rows)


def test_긴_글은_안_받는다(app):
    """긴 글은 사연이 되고 사연에는 남의 개인정보가 섞입니다."""
    assert _ask(app, body="가" * 1001).status_code == 422


def test_너무_자주_걸면_막는다(app):
    codes = {_ask(app).status_code for _ in range(9)}
    assert 429 in codes
