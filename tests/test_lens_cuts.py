"""
관점 컷 — 값이 오르면 실제로 더 주는가.

★ 이 파일이 지키는 것
  1만 명 시험에서 **값 ↔ 컷수 상관이 −0.419** 였습니다. 4,900원짜리가
  19,900원짜리보다 더 주고 있었습니다. 컷을 늘리는 장치가 '추가 입력'
  하나뿐인데 비싼 캐릭터들이 그걸 안 받았기 때문입니다.

  값을 캐릭터 값으로 받기로 했으니(payments.price_of) **비싼 쪽이 실제로
  더 줘야** 합니다. 아래 검사가 그 약속입니다. 캐릭터 값을 바꾸거나
  관점 컷을 지우면 여기가 붉어집니다.
"""
from __future__ import annotations

import re
from datetime import date

import pytest

from engine import lens as lens_mod
from engine import lens_cuts as lens_cuts_mod
from engine.calendar import build_chart
from engine.features import build_features
from engine.report import build_report

TAG = re.compile(r"<[^>]+>")

# 값 등급 → 자기 몫 컷이 적어도 몇 개여야 하는가.
# 자기 몫 = 추가 입력 컷 + 관점 컷.
OWN_FLOOR = [(19900, 3), (15900, 2), (4900, 1), (0, 0)]

# 추가 입력을 채워 넣는 값. extras 는 저장되지 않습니다.
FILL = {
    "blood": {"blood": {"type": "A"}},
    "image": {"image": {"pick": "door"}},
    "cards": {"cards": {"picks": ["gil", "mun", "san"]}},
    "partner": {"partner": {"year": 1990, "month": 4, "day": 11, "hour": 9,
                            "minute": 0, "sex": "M", "hour_known": True}},
    "context": {"context": {"situation": "start", "stance": "hold",
                            "months": 8}},
}


def _people():
    """서로 다른 명식 몇 개. 한 사람만 보면 우연에 속습니다."""
    for spec in ((1993, 7, 14, 5, 20, "F"), (1978, 11, 3, 21, 40, "M"),
                 (2001, 2, 19, 8, 5, "F"), (1966, 6, 30, 14, 55, "M")):
        yield build_features(build_chart(*spec), as_of=date(2026, 8, 27))


def _fill_for(lens_id):
    need = lens_mod.required_input(lens_id)
    return FILL.get(need)


def own_floor(price: int) -> int:
    for threshold, n in OWN_FLOOR:
        if price >= threshold:
            return n
    return 0


def test_axes_are_known():
    """표가 부르는 축이 전부 엔진에 있는가."""
    for lens_id, cuts in lens_cuts_mod._table()["cuts"].items():
        for c in cuts:
            for side in ("a", "b", "c"):
                assert c[side]["axis"] in lens_cuts_mod.AXES, \
                    (lens_id, c["id"], c[side]["axis"])


def test_three_axes_multiply():
    """
    ★ 축 둘로는 모자랐습니다.
      가짓수는 나왔는데 축이 **고르지 않아** 본문 최다 점유가 17%까지
      올라갔습니다(deuk 38% · score_band 48% · ilji_state 58%).
      세 번째로 고른 축을 곱해 200가지 이상을 만듭니다.
      실제 쏠림은 tools/dup_rate.py 가 본문만 따로 재서 봅니다.
    """
    for lens_id, cuts in lens_cuts_mod._table()["cuts"].items():
        for c in cuts:
            axes = [c[k]["axis"] for k in ("a", "b", "c")]
            assert len(set(axes)) == 3, (lens_id, c["id"], axes)
            card = (len(c["a"]["text"]) * len(c["b"]["text"])
                    * len(c["c"]["text"]))
            assert card >= 200, (lens_id, c["id"], card)


def test_no_numbers_in_perspective_text():
    """
    근거는 보이되 규칙은 감춥니다. 관점 컷 문장에 **내부 척도**를
    쓰지 않습니다 — 소수와 음수는 사람이 읽을 수 없는 값입니다.
    """
    bad = []
    for lens_id, cuts in lens_cuts_mod._table()["cuts"].items():
        for c in cuts:
            texts = [c["lead"]] + list(c["a"]["text"].values()) \
                + list(c["b"]["text"].values())
            for t in texts:
                # 태그를 걷고 봅니다 — <b> 의 꺾쇠는 연산자가 아닙니다.
                plain = TAG.sub("", t)
                if re.search(r"\d+\.\d|(?<![\w가-힣])-\d|[<>≤≥]", plain):
                    bad.append((lens_id, c["id"], plain[:50]))
    assert not bad, bad


@pytest.mark.parametrize("lens", [l for l in lens_mod.all_lenses()
                                  if l.get("released")],
                         ids=lambda l: l["id"])
def test_every_person_gets_every_perspective_cut(lens):
    """
    표에 없는 조합이 있으면 여기서 터집니다. 관점 컷은 **비지 않습니다** —
    빈칸을 두느니 터뜨립니다.
    """
    for f in _people():
        cuts = lens_cuts_mod.build(f, lens["id"])
        assert len(cuts) == lens_cuts_mod.owned(lens["id"])
        for c in cuts:
            body = TAG.sub("", c["html"]).strip()
            assert len(body) > 60, (lens["id"], c["id"], body)
            assert "{" not in body, (lens["id"], c["id"], body)


@pytest.mark.parametrize("lens", [l for l in lens_mod.all_lenses()
                                  if l.get("released")],
                         ids=lambda l: l["id"])
def test_price_buys_its_own_cuts(lens):
    """값 등급이 요구하는 만큼 자기 몫 컷이 있는가."""
    want = own_floor(int(lens["price"]))
    extras = _fill_for(lens["id"])
    for f in _people():
        rep = build_report(f, "t", lens["id"], "one", "love", "INFP", extras)
        own = [c for c in rep["cuts"]
               if c["id"].startswith("lc_") or c["id"] in FILL
               or c["id"] in ("blood", "image", "cards", "partner", "context")]
        assert len(own) >= want, (lens["id"], lens["price"], want,
                                  [c["id"] for c in own])


def test_more_money_is_never_less_report():
    """
    ★ 이 검사가 이 파일의 핵심입니다.
      값이 더 비싼 캐릭터가 값이 더 싼 캐릭터보다 **적게 주면 안 됩니다.**
      전에는 19,900원 풍운도령이 9.0컷, 4,900원 적혈랑이 10.0컷이었습니다.
    """
    rows = []
    for lens in lens_mod.all_lenses():
        if not lens.get("released") or int(lens["price"]) <= 0:
            continue
        extras = _fill_for(lens["id"])
        n = []
        for f in _people():
            rep = build_report(f, "t", lens["id"], "one", "love", "INFP",
                               extras)
            n.append(len(rep["cuts"]))
        rows.append((int(lens["price"]), lens["id"], min(n)))

    rows.sort()
    # 값이 오르는 순서로 훑으며 컷 수가 **줄지 않는지** 본다.
    worst_by_price = {}
    for price, _lid, cuts in rows:
        worst_by_price[price] = min(worst_by_price.get(price, cuts), cuts)
    prices = sorted(worst_by_price)
    for lo, hi in zip(prices, prices[1:]):
        assert worst_by_price[hi] >= worst_by_price[lo], \
            (lo, worst_by_price[lo], hi, worst_by_price[hi], rows)


def test_free_character_is_never_charged():
    """값 없는 캐릭터를 결제로 보내지 않는다. 그건 강매입니다."""
    import payments
    with pytest.raises(payments.PaymentError):
        payments.price_of("one", "dongja")


def test_card_price_equals_charged_price():
    """
    ★ 릴레이 카드에 보인 값이 그대로 청구되는가.
      전에는 카드가 캐릭터 값을 보여 주고 결제는 티어 값(3,900원)을
      물렸습니다. 스무 캐릭터의 값이 한 번도 청구되지 않았습니다.
    """
    import payments
    for lens in lens_mod.all_lenses():
        if not lens.get("released") or int(lens["price"]) <= 0:
            continue
        shown = int(lens["price"])
        charged = payments.price_of("one", lens["id"])
        assert shown == charged, (lens["id"], shown, charged)
