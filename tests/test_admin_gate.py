# -*- coding: utf-8 -*-
"""
주인 자리가 잠겨 있는가.

★ 왜 지키나

  전에는 손님 화면 주소 뒤에 `?admin=1` 만 붙이면 레일이 열렸다.
  그건 잠금이 아니라 **가림**이다 — 아무나 붙일 수 있고, 실수로 그
  주소를 공유하면 그대로 열린다.

  매출·이탈은 영업 정보다. 퍼널과 **같은 열쇠**를 쓴다 — 둘을 따로
  두면 하나만 걸어 두고 다른 하나는 열린 채 배포되는 날이 온다.
"""
import re
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))
warnings.filterwarnings("ignore")


def _client():
    from fastapi.testclient import TestClient
    import main
    return TestClient(main.app)


def test_admin_is_closed_without_a_key(monkeypatch):
    """열쇠를 안 정해 두면 아예 닫는다 — 열린 쪽이 기본이면 안 된다."""
    c = _client()
    for path in ("/v1/admin/overview", "/v1/admin/ping"):
        r = c.get(path)
        assert r.status_code in (401, 503), path


def test_admin_refuses_a_wrong_key():
    import routers.admin as adm
    adm.FUNNEL_KEY = "right"
    try:
        c = _client()
        assert c.get("/v1/admin/overview",
                     headers={"x-funnel-key": "wrong"}).status_code == 401
        assert c.get("/v1/admin/overview",
                     headers={"x-funnel-key": "right"}).status_code == 200
    finally:
        adm.FUNNEL_KEY = ""


def test_admin_uses_the_same_key_as_funnel():
    """열쇠가 둘이면 하나만 걸어 두는 날이 온다."""
    src = (ROOT / "services" / "api" / "routers" / "admin.py").read_text(
        encoding="utf-8")
    assert 'os.getenv("FUNNEL_KEY"' in src


def test_admin_screen_is_not_counted_in_the_funnel():
    """주인이 화면을 훑는 것이 손님 퍼널을 오염시키면 안 된다."""
    src = (ROOT / "apps" / "web" / "lib" / "track.ts").read_text(encoding="utf-8")
    assert '"/admin"' in src, "주인 화면을 계측에서 안 뺐다"


def test_admin_overview_carries_no_personal_data():
    """생년월일·이름·chart_id 는 준식별자다."""
    src = (ROOT / "services" / "api" / "routers" / "admin.py").read_text(
        encoding="utf-8")
    # ★ 주석은 걷고 봅니다. "chart_id 는 준식별자다" 라고 **적어 둔 말**을
    #   개인정보로 세면, 규칙을 설명한 죄로 검사가 깨집니다.
    code = re.sub(chr(34) * 3 + "(?:.|" + chr(92) + "n)*?" + chr(34) * 3,
                  " ", src)
    code = re.sub("#[^" + chr(92) + "n]*", " ", code)
    for bad in ("chart_id", "birth", "sex", "day_gan"):
        assert bad not in code, "개인정보를 싣고 있다: %s" % bad
