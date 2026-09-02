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
    """
    ★ 열쇠를 **문지기 자리**에 꽂습니다.

      전에는 `routers.admin.FUNNEL_KEY` 에 꽂았습니다. 그런데 지키는
      코드가 keyguard 한 자리로 모이면서 그 이름이 없어졌고, 검사가
      503(열쇠 미설정)을 받았습니다.

      검사가 **어디에 있는지**를 못 박아 두면, 옮기는 순간 뜻이 그대로
      인데도 빨개집니다. 뜻으로 씁니다 — 「틀린 열쇠는 막고 맞는
      열쇠는 연다」.
    """
    import keyguard
    keyguard.FUNNEL_KEY = "right"
    try:
        c = _client()
        assert c.get("/v1/admin/overview",
                     headers={"x-funnel-key": "wrong"}).status_code == 401
        assert c.get("/v1/admin/overview",
                     headers={"x-funnel-key": "right"}).status_code == 200
    finally:
        keyguard.FUNNEL_KEY = ""


def test_admin_uses_the_same_key_as_funnel():
    """
    열쇠가 둘이면 하나만 걸어 두는 날이 온다.

    ★ 이제 **같은 문지기를 부르는가**로 봅니다. 전에는 admin.py 안에
      `os.getenv("FUNNEL_KEY"` 가 있는지 봤는데, 그건 「같은 열쇠를
      쓴다」 가 아니라 「같은 코드를 베껴 뒀다」 를 지키는 것이었습니다.
      베낀 코드는 한쪽만 고쳐집니다.
    """
    api = ROOT / "services" / "api"
    for fn in ("routers/admin.py", "routers/events.py"):
        src = (api / fn).read_text(encoding="utf-8")
        assert "from keyguard import" in src, fn
        # 제 나름의 열쇠를 또 읽으면 안 됩니다 — 그 순간 둘이 갈립니다.
        assert 'os.getenv("FUNNEL_KEY"' not in src, fn


def test_모든_조회문에_문지기가_붙어_있다():
    """
    ★ 문이 하나 늘 때 지킴을 빠뜨리는 것이 이 자리의 사고입니다.

      영업 정보를 내는 파일에서는 `@router.get` 마다 `_guard(` 가
      있어야 합니다. 손님이 쓰는 수집 문(post)은 안 잠급니다.
    """
    api = ROOT / "services" / "api" / "routers"
    for fn in ("admin.py", "events.py"):
        src = (api / fn).read_text(encoding="utf-8")
        gets = len(re.findall(r"@router\.get", src))
        guards = len(re.findall(r"_guard\(", src))
        assert guards >= gets, "%s — 조회문 %d개 중 지킴 %d개" % (
            fn, gets, guards)


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
