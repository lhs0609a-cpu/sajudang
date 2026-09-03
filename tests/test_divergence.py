# -*- coding: utf-8 -*-
"""
다른 만세력과 갈리는 자리를 **우리가 먼저** 말하는가.

★ 왜 지키나

  손님은 다른 만세력과 대 본다. 백 명 중 **스물여덟**이 다르게 나온다
  (tools/divergence.py — 고을 보정 23.7명 · 밤 11시대 4.4명 ·
  절입 언저리 0.1명).

  ★ 여기 「넷다섯」 이라 적혀 있었다. 셋 중 **가장 흔한** 고을 보정을
    아예 안 세고 있었기 때문이다. 2026-09-03 에 손님이 1993-11-25
    13:00 서울로 들고 와서 알았다.

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


def test_a_longitude_boundary_birth_is_flagged():
    """
    고을 보정으로 시지가 갈리는 자리 — **셋 중 가장 흔하다.**

    ★ 실제로 났던 일 (2026-09-03)

      손님이 1993-11-25 13:00 서울을 넣고 「만세력이랑 다르다」 고 했다.
      우리는 시주가 壬午, 저쪽은 癸未다. 까닭은 셈이 아니라 선택이다 —
      서울은 해가 가장 높이 뜨는 때가 시계보다 32분 늦어서, 13:00 은
      진태양시로 12:28 이라 아직 午시다. 보정을 안 쓰는 집에서는
      13:00 이 그대로 未시다.

      그런데 화면은 **「갈리는 자리 없음」 이라 잠자코 있었다.** 갈림을
      먼저 말하기로 해 놓고 조자시(4.4%)와 절입(0.1%)만 보고 있었다.
      정작 **23.7%** 가 걸리는 이 자리를 안 보고 있었다. 게다가 이
      13:00 이 「안 걸리는 사람」 의 본보기로 테스트에 박혀 있었다.
    """
    d = _post({**BASE, "hour": 13, "minute": 0})
    cases = (d.get("divergence") or {}).get("cases") or []
    got = [c for c in cases if "고을" in c["why"]]
    assert got, "고을 보정으로 갈리는데 아무 말이 없다"
    c = got[0]
    assert c["moved"] == ["시주"], "무엇이 달라지는지 잘못 짚는다: %s" % c["moved"]
    assert c["mine"].endswith("壬午"), c["mine"]
    assert c["alt"].endswith("癸未"), c["alt"]


def test_an_ordinary_birth_is_not_flagged():
    """
    안 걸리는 사람에게 겁을 주면 안 된다.

    ★ 12:00 은 보정해도(11:28) 午시 안에 남고, 밤도 절입 언저리도 아니다.
    """
    d = _post({**BASE, "hour": 12, "minute": 0})
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
