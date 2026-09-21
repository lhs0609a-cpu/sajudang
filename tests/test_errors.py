"""
터진 자리 — 주인이 알 수 있는가, 그리고 **손님 것이 안 새는가**.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

KEY = "k" * 24


@pytest.fixture()
def mod(tmp_path, monkeypatch):
    monkeypatch.setenv("STORE_PATH", str(tmp_path / "s.sqlite"))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    for m in [k for k in list(sys.modules)
              if k in ("store", "errors", "db")]:
        sys.modules.pop(m, None)
    import errors
    return errors


def test_같은_버그가_한_자리로_모인다(mod):
    """
    ★ 길에 박힌 값을 안 지우면 같은 버그가 백 가지로 흩어져
      **한 번도 눈에 안 띕니다.**
    """
    a = mod.record("/v1/pay/order/sjd_aaaaaaaaaaaa", ValueError("터짐"))
    b = mod.record("/v1/pay/order/sjd_bbbbbbbbbbbb", ValueError("터짐"))
    assert a == b, "주문번호마다 다른 자리로 세오"
    rows = mod.recent()
    assert len(rows) == 1 and rows[0]["count"] == 2
    assert rows[0]["path"] == "/v1/pay/order/{id}"


def test_다른_예외는_따로_센다(mod):
    mod.record("/v1/chart", ValueError("가"))
    mod.record("/v1/chart", KeyError("나"))
    assert len(mod.recent()) == 2


def test_요청_본문과_스택을_안_남긴다(mod):
    """이 집의 요청 본문에는 생년월일시가 들어 있습니다."""
    try:
        raise RuntimeError("birth=1993-05-15 name=홍길동")
    except RuntimeError as e:
        mod.record("/v1/chart", e)
    row = mod.recent()[0]
    assert set(row) <= {"id", "path", "kind", "first", "last", "count", "message"}
    assert "stack" not in row and "traceback" not in row
    # 첫 줄은 남깁니다(찾을 만큼) — 다만 200자로 자릅니다.
    assert len(row["message"]) <= 200


def test_셈이_요약된다(mod):
    mod.record("/v1/chart", ValueError("가"))
    mod.record("/v1/chart", ValueError("가"))
    s = mod.summary()
    assert s["kinds"] == 1 and s["total"] == 2 and s["today"] == 2


def test_터지면_번호를_주고_주인이_본다(tmp_path, monkeypatch):
    """
    끝에서 끝까지 — 터진 자리가 손님에게는 번호로, 주인에게는 셈으로.
    """
    monkeypatch.setenv("STORE_PATH", str(tmp_path / "s.sqlite"))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    for m in [k for k in list(sys.modules)
              if k in ("store", "errors", "db", "main")
              or k.startswith("routers")]:
        sys.modules.pop(m, None)
    import keyguard
    monkeypatch.setattr(keyguard, "FUNNEL_KEY", KEY)
    from fastapi.testclient import TestClient
    import main

    @main.app.get("/v1/_boom_for_test")
    def _boom():                                   # pragma: no cover
        raise RuntimeError("일부러 터뜨림")

    c = TestClient(main.app, raise_server_exceptions=False)
    r = c.get("/v1/_boom_for_test")
    assert r.status_code == 500
    body = r.json()
    assert body["code"] == "INTERNAL"
    assert body["traceId"], "번호를 안 주오"
    assert "일부러 터뜨림" not in r.text, "속을 손님에게 보이오"

    seen = c.get("/v1/admin/errors", headers={"x-funnel-key": KEY}).json()
    assert seen["summary"]["total"] >= 1, "주인이 못 보오"
    assert any(row["id"] == body["traceId"] for row in seen["rows"]), \
        "손님이 든 번호로 주인이 못 찾소"


def test_오류_목록은_잠겨_있다(tmp_path, monkeypatch):
    monkeypatch.setenv("STORE_PATH", str(tmp_path / "s.sqlite"))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    for m in [k for k in list(sys.modules)
              if k in ("store", "errors", "db", "main")
              or k.startswith("routers")]:
        sys.modules.pop(m, None)
    import keyguard
    monkeypatch.setattr(keyguard, "FUNNEL_KEY", KEY)
    from fastapi.testclient import TestClient
    import main
    assert TestClient(main.app).get("/v1/admin/errors").status_code == 401


# ★ 검사 파일이 끝나면 **모듈을 치웁니다.**
#   `keyguard` 는 뜰 때 FUNNEL_KEY 를 한 번 읽어 박아 둡니다. 남겨 두면
#   다음 파일이 「열쇠 걸린 집」을 물려받아 엉뚱한 자리가 깨집니다.
@pytest.fixture(autouse=True)
def _evict_modules():
    yield
    for m in [k for k in list(sys.modules)
              if k in ("store", "payments", "db", "main", "analytics",
                       "throttle", "audit", "errors", "backup")
              or k.startswith("routers")]:
        sys.modules.pop(m, None)
