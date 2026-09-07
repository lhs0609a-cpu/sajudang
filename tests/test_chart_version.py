# -*- coding: utf-8 -*-
"""
엔진을 고치면 **저장된 명식이 다시 서는가.**

★ 어떻게 드러났나 (2026-09-07)

  홍염을 넣고 배포한 뒤 살아 있는 서비스에 물어보니 —

      1988년생 → 홍염 뜸        (처음 계산되는 사람)
      1993년생 → 홍염 안 뜸     (배포 전에 이미 계산된 사람)

  여덟 글자는 같은데 신살만 달랐습니다. 명식이 `chart_id` 로
  저장돼 있는데 그 열쇠에 **엔진 판이 없어서**입니다. 만기는
  90일이니, 고쳐도 이미 온 손님에게는 석 달 동안 안 닿습니다.

★ 「같은 입력이면 같은 결과」는 엔진이 안 바뀔 때만 참입니다

  이 집은 신살·용신·대운 정책을 고치는 집입니다. 그 전제를 적어
  두고 캐시하고 있었습니다.

★ 열쇠는 안 바꿉니다

  `chart_id` 를 바꾸면 이미 치른 주문과 리포트가 딴 명식을 가리
  킵니다. 대신 판을 따로 찍어 두고, **계산하는 자리에서** 판이
  다르면 다시 세웁니다. `load_features` 는 그대로 둡니다 — 거기는
  생년월일이 없어 다시 세울 수 없고, 없다고 404 를 내면 값을 치른
  사람이 리포트를 못 엽니다.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

import store                                    # noqa: E402
from routers import chart as chart_router       # noqa: E402
from schemas.api import ChartRequest            # noqa: E402
from version import ENGINE_VER                  # noqa: E402

REQ = dict(year=1993, month=11, day=25, hour=15, minute=55,
           hour_known=True, sex="M", birth_city="서울")


@pytest.fixture
def req():
    return ChartRequest(**REQ)


def test_판이_같으면_저장된_것을_쓴다(req):
    a = chart_router.post_chart(req)
    b = chart_router.post_chart(req)
    assert b.cached is True, "두 번째인데 다시 세웠소"
    assert a.chart_id == b.chart_id


def test_판이_달라지면_다시_세운다(req, monkeypatch):
    """
    ★ 이게 이번에 비어 있던 자리입니다. 여기가 없으면 신살을 넣어도
      이미 온 손님에게는 90일 동안 안 닿습니다.
    """
    chart_router.post_chart(req)                      # 한 번 세워 둡니다
    key = chart_router.chart_key(req)
    assert store.get_json(chart_router._k_ver(key)) == ENGINE_VER

    # 판을 올린 척합니다 — 저장된 명식은 그대로 두고요.
    monkeypatch.setattr(chart_router, "ENGINE_VER", ENGINE_VER + "-next")
    got = chart_router.post_chart(req)
    assert got.cached is False, "판이 달라졌는데 옛 명식을 냈소"
    assert store.get_json(chart_router._k_ver(key)) == ENGINE_VER + "-next"


def test_열쇠는_판이_달라져도_안_바뀐다(req, monkeypatch):
    """
    ★ `chart_id` 가 바뀌면 이미 치른 주문과 리포트가 **딴 명식**을
      가리킵니다. 값을 치른 사람이 제 리포트를 잃습니다.
    """
    before = chart_router.post_chart(req).chart_id
    monkeypatch.setattr(chart_router, "ENGINE_VER", ENGINE_VER + "-next")
    assert chart_router.post_chart(req).chart_id == before


def test_판은_한_자리에만_산다():
    """
    ★ `main.py` 에 두었더니 라우터가 그걸 쓰는 순간 돌아가는 임포트가
      생겼습니다. 판은 아무것도 안 부르는 자리에 있어야 합니다.
    """
    src = (ROOT / "services" / "api" / "main.py").read_text(encoding="utf-8")
    assert "from version import ENGINE_VER" in src
    assert 'ENGINE_VER = "' not in src, "판이 두 자리에 사오"
    ver = (ROOT / "services" / "api" / "version.py").read_text(encoding="utf-8")
    assert ver.count('ENGINE_VER = "') == 1


def test_판을_올렸는가():
    """
    신살이 하나 늘었으니(홍염) 판도 올라가 있어야 합니다. 안 올리면
    이미 온 손님은 그 신살을 못 봅니다.
    """
    assert ENGINE_VER != "0.2.0", "셈이 달라졌는데 판을 안 올렸소"
