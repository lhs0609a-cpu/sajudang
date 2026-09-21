"""
내 자료 — 열람과 삭제 (개인정보보호법 제35조·제36조).

★ 여기서 지키는 것
    · 본인에게도 승인 키·카드 열쇠를 안 준다
    · 지우기 전에 무엇이 남는지 **먼저 말한다**
    · 거래 기록은 남기되 **세션을 뗀다** (전자상거래법 제6조)
    · 도는 구독이 있으면 안 지운다 (카드만 걸린 채 남으면 안 됨)
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("STORE_PATH", str(tmp_path / "s.sqlite"))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    for m in [k for k in list(sys.modules)
              if k in ("store", "payments", "db", "main", "analytics", "throttle")
              or k.startswith("routers")]:
        sys.modules.pop(m, None)
    from fastapi.testclient import TestClient
    import main
    return TestClient(main.app)


SID = "sess-privacy-abcdefgh"


def _uk(sid: str) -> str:
    return hashlib.sha256(sid.encode()).hexdigest()[:16]


def _seed(sid: str = SID) -> None:
    import store
    store.set_json("order:oid-1", {
        "order_id": "oid-1", "session_id": sid, "status": "paid",
        "amount": 9900, "tier": "one", "lens_id": "pungun",
        "payment_key": "TOSS_SECRET_KEY_VALUE"})
    store.set_json("orders:" + sid, ["oid-1"])
    store.set_json("seals:" + _uk(sid), ["pungun"])


def test_열람은_맡긴_것을_다_낸다(app):
    _seed()
    r = app.get("/v1/me/data", params={"session_id": SID})
    assert r.status_code == 200, r.text
    d = r.json()
    assert len(d["orders"]) == 1
    assert d["seals"] == ["pungun"]


def test_본인에게도_승인키를_안_준다(app):
    """승인 키는 그 사람 것이 아니라 **PG 와 우리 사이의 것**입니다."""
    _seed()
    body = app.get("/v1/me/data", params={"session_id": SID}).text
    assert "TOSS_SECRET_KEY_VALUE" not in body
    for banned in ("payment_key", "billing_key", "analytics_sid"):
        assert banned not in body, banned


def test_지우기_전에_무엇이_남는지_먼저_말한다(app):
    """되돌릴 수 없는 일이라 한 번 보여 줍니다 (§6-6)."""
    _seed()
    r = app.post("/v1/me/forget", json={"session_id": SID})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["done"] is False, "확인도 안 받고 지웠소"
    assert d["plan"]["removes"]["구매 목록"] == 1
    assert "전자상거래법" in d["plan"]["keeps"]["왜"]
    import store
    assert store.get_json("orders:" + SID), "예고만 했는데 벌써 지웠소"


def test_지우면_연결이_끊기고_거래기록은_남는다(app):
    _seed()
    r = app.post("/v1/me/forget", json={"session_id": SID, "confirm": True})
    assert r.status_code == 200 and r.json()["done"] is True

    import store
    assert store.get_json("orders:" + SID) is None, "연결이 안 끊겼소"
    assert store.get_json("seals:" + _uk(SID)) is None, "인장이 남았소"

    row = store.get_json("order:oid-1")
    assert row, "거래 기록까지 지웠소 — 법이 5년 보관하라 하오"
    assert row["session_id"] is None, "세션이 안 떨어졌소"
    assert row["amount"] == 9900, "거래 내용이 상했소"


def test_지운_뒤에는_되찾기로도_못_연다(app):
    """세션을 뗐으니 그 브라우저로 다시 붙을 수 없어야 합니다."""
    _seed()
    app.post("/v1/me/forget", json={"session_id": SID, "confirm": True})
    r = app.get("/v1/me/data", params={"session_id": SID})
    assert r.json()["orders"] == []


def test_도는_구독이_있으면_안_지운다(app):
    """지우면 카드는 걸린 채 남아 돈은 나가는데 볼 자리가 없어집니다."""
    import store
    sid = "sess-privacy-livesub"
    store.set_json("sub:" + _uk(sid), {
        "status": "live", "period_end": "2099-01-01T00:00:00+00:00"})
    r = app.post("/v1/me/forget", json={"session_id": sid, "confirm": True})
    assert r.status_code == 409, r.text
    assert "그만두" in r.json()["detail"]
    assert store.get_json("sub:" + _uk(sid)), "거절해 놓고 지웠소"


def test_명식_캐시는_안_지운다(app):
    """
    ★ `chart:{id}` 의 열쇠는 생년월일시의 해시라 **여럿이 같은 칸**을
      씁니다. 한 사람이 지운다고 지우면 남의 것을 지우는 것입니다.
    """
    import store
    _seed()
    store.set_json("chart:shared-key", {"pillars": []})
    app.post("/v1/me/forget", json={"session_id": SID, "confirm": True})
    assert store.get_json("chart:shared-key"), "남의 명식까지 지웠소"


def test_두드리는_횟수를_센다(app):
    _seed()
    codes = {app.post("/v1/me/forget", json={"session_id": SID}).status_code
             for _ in range(25)}
    assert 429 in codes, "몇 번이든 두드릴 수 있소"
