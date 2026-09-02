# -*- coding: utf-8 -*-
"""
다른 만세력과 갈리는 자리를 **우리가 먼저** 말하는가.

★ 왜 지키나

  손님은 다른 만세력과 대 본다. 백 명 중 넷다섯이 다르게 나온다
  (tools/divergence.py — 밤 11시대 4.4명, 절입 언저리 0.1명).

  그때 「우리가 맞소」 도 「그쪽이 맞소」 도 답이 아니다. 갈리는 자리는
  **계산이 아니라 선택**이기 때문이다 — 조자시로 볼지 야자시로 볼지,
  절입을 진태양시와 견줄지 표준시와 견줄지. 둘 다 명리에서 쓰는 정식
  유파라 어느 쪽도 상대를 못 이긴다.

  발견당하면 「틀린 집」이 되고, 먼저 말하면 「아는 집」이 된다.
  같은 사실인데 순서가 다르다.
"""
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))
warnings.filterwarnings("ignore")


def _post(body):
    from fastapi.testclient import TestClient
    import main
    return TestClient(main.app).post("/v1/chart", json=body).json()


BASE = {"year": 1993, "month": 11, "day": 25, "minute": 45,
        "sex": "M", "hour_known": True, "birth_city": "서울"}


def test_a_late_night_birth_is_flagged():
    """밤 11시대는 조자시·야자시로 갈린다 — 반드시 말해야 한다."""
    d = _post({**BASE, "hour": 23})
    dv = d.get("divergence")
    assert dv and dv.get("cases"), "갈리는 자리인데 아무 말이 없다"
    c = dv["cases"][0]
    for k in ("why", "ours", "theirs", "moved", "mine", "alt"):
        assert c.get(k), "%s 가 비었다" % k
    assert c["mine"] != c["alt"], "두 답이 같으면 갈린 게 아니다"
    assert c["moved"], "어느 기둥이 달라지는지 안 말한다"


def test_an_ordinary_birth_is_not_flagged():
    """안 걸리는 사람에게 겁을 주면 안 된다."""
    d = _post({**BASE, "hour": 13, "minute": 0})
    assert not (d.get("divergence") or {}).get("cases"), \
        "안 갈리는데 갈린다고 한다"


def test_the_other_answer_is_shown_too():
    """감추면 숨긴 것이 된다 — 저쪽 답까지 낸다."""
    src = (ROOT / "apps" / "web" / "app" / "page.tsx").read_text(
        encoding="utf-8")
    assert "divergence" in src, "화면이 안 받는다"
    assert "c.alt" in src, "저쪽 답을 안 보여 준다"
    assert "이 집은 위엣것으로 봅니다" in src, "어느 쪽을 쓰는지 안 밝힌다"


def test_doubts_has_an_answer_ready():
    """명식까지 안 온 사람에게도 답이 있어야 한다."""
    src = (ROOT / "apps" / "web" / "components" / "Doubts.tsx").read_text(
        encoding="utf-8")
    assert "다른 만세력과 다르게 나오면" in src, "물음이 없다"
    assert "조자시" in src and "야자시" in src, "무엇이 갈리는지 안 말한다"


def test_we_never_claim_the_other_house_is_wrong():
    """어느 쪽도 상대를 못 이긴다. 틀렸다고 하면 그건 거짓이다."""
    for f in ("apps/web/app/page.tsx", "apps/web/components/Doubts.tsx"):
        src = (ROOT / f).read_text(encoding="utf-8")
        i = src.find("만세력")
        if i < 0:
            continue
        near = src[max(0, i - 1500):i + 3000]
        for bad in ("틀린 곳", "잘못된 만세력", "그쪽이 틀"):
            assert bad not in near, "%s 에서 상대를 틀렸다고 한다" % f
