"""
희소도 · 틀릴 수 있는 말 · 끝 — 이번에 새로 세운 자리들.

★ 이 파일이 지키는 것
  바깥에서 찾은 것 중 가장 큰 지렛대가 **반증 가능한 구체성**이었습니다.
  바넘 문장은 어떤 관찰에서도 살아남아 '맞다' 는 나와도 '소름 돋는다' 는
  안 나옵니다. 그래서 셋을 넣었습니다 —
      셀 수 있는 수(희소도) · 연도가 박힌 때(대운·세운) · 설계된 끝.
  각각이 조용히 도로 물러나지 않게 여기서 셉니다.
"""
from __future__ import annotations

import re
from datetime import date

import pytest

from engine import rarity as rarity_mod
from engine import summary as summary_mod
from engine.calendar import build_chart, year_ganji
from engine.features import build_features
from engine.report import build_report

TAG = re.compile(r"<[^>]+>")
AS_OF = date(2026, 8, 27)


def _people():
    for spec in ((1997, 3, 22, 14, 10, "F"), (1982, 11, 8, 3, 40, "M"),
                 (2003, 9, 17, 7, 55, "F"), (1966, 5, 5, 12, 30, "M"),
                 (2007, 12, 2, 9, 0, "F")):
        yield build_features(build_chart(*spec), as_of=AS_OF)


def _report(f, tier="all"):
    return build_report(f, "t", "nopa", tier, "work", None)


# ══════════════════════════════════════════════════════════
# 희소도 — 지어내지 않고 센다
# ══════════════════════════════════════════════════════════
def test_table_matches_the_axes():
    """
    축을 고치고 표를 다시 안 만들면 숫자가 딴 축의 것이 됩니다.
    조용히 어긋나는 것이 가장 나쁘므로 여기서 셉니다.
    """
    assert not rarity_mod.is_stale(), \
        "축이 바뀌었습니다. python tools/make_rarity.py 를 다시 도세요"


def test_every_person_gets_a_counted_number():
    for f in _people():
        r = rarity_mod.look(f)
        assert r["sample"] > 0
        assert 0.0 <= r["share"] <= 1.0
        assert r["band"] in ("표본에없음", "아주드묾", "드묾", "적잖음", "흔함")


def test_thin_cells_are_not_scaled_up():
    """
    표본에 몇 안 되는 칸을 '1만 명에 몇 명' 으로 환산하면 **없는 정밀도**를
    지어내는 것이 됩니다. 그런 칸은 표본 그대로 말합니다.
    """
    t = rarity_mod.table()
    for key, cell in t["cells"].items():
        if cell["n"] < rarity_mod.MIN_FOR_SCALE:
            assert "표본" in _words_for(t, key)


def _words_for(t, key):
    n, total = t["cells"][key]["n"], t["sample"]
    if n >= rarity_mod.MIN_FOR_SCALE:
        return "1만 명에 %d명" % round(n / total * 10000)
    return "표본 %s명 가운데 %d명" % (format(total, ","), n)


def test_common_people_are_told_they_are_common():
    """
    드문 쪽만 말하고 흔한 쪽을 감추면 화면에 남는 숫자가 전부 드물어
    보입니다. 공감률을 하한으로 내는 것과 같은 이치입니다.
    """
    t = rarity_mod.table()
    bands = set()
    for cell in t["cells"].values():
        share = cell["n"] / t["sample"]
        bands.add("흔함" if share >= 0.08 else "드묾")
    assert "흔함" in bands, "아무도 흔하지 않다면 그건 세는 게 아닙니다"


def test_rarity_cut_is_free():
    """공유를 만드는 자리라 값 뒤에 두면 뜻이 없습니다."""
    for f in _people():
        ids = {c["id"] for c in _report(f, "free")["cuts"]}
        assert "rarity" in ids


def test_rarity_never_claims_a_hit_rate():
    """'몇 %가 맞았다' 가 아니라 '이 배치가 몇 명' 입니다."""
    for f in _people():
        cut = next(c for c in _report(f)["cuts"] if c["id"] == "rarity")
        body = TAG.sub("", cut["html"])
        for bad in ("적중", "확률", "맞을", "과학", "통계"):
            assert bad not in body, (bad, body[:120])


# ══════════════════════════════════════════════════════════
# 틀릴 수 있는 말 — 때에 숫자를 박는다
# ══════════════════════════════════════════════════════════
def test_year_ganji_matches_the_chart():
    """세운을 세는 식이 명식의 년주와 한 벌이라야 합니다."""
    for f in _people():
        g, j = year_ganji(f.saju_year)
        assert g + j == f.pillars[0]["gz"], f.saju_year


def test_daeun_cut_carries_a_year_that_can_be_wrong():
    """
    '지금은 정재 대운이오' 는 틀릴 수가 없습니다. 나이와 연도가 박혀야
    틀릴 수 있고, 틀릴 수 있어야 맞았을 때 놀랍습니다.
    """
    for f in _people():
        cut = next(c for c in _report(f)["cuts"] if c["id"] == "daeun_now")
        body = TAG.sub("", cut["html"])
        assert re.search(r"\d{4}년", body), body[:160]
        assert "세" in body
        # 연도는 태어난 해 + 대운수 기준이라야 합니다. 두 기준을 섞으면
        # 한 해가 어긋납니다.
        start_year = f.saju_year + f.daeun[f.daeun_now]["start_age"]
        assert str(start_year) in body, (start_year, body[:160])


def test_sewoon_names_this_year_and_next():
    for f in _people():
        cut = next(c for c in _report(f)["cuts"] if c["id"] == "daeun_now")
        body = TAG.sub("", cut["html"])
        this_year = f.saju_year + f.age
        assert str(this_year) in body
        assert str(this_year + 1) in body


def test_no_broken_particle_in_the_name_stage():
    """
    '재성 하는데' 는 비문이었습니다. 십신 이름에 '하다' 가 안 붙습니다.
    이름을 건네는 가장 뜨거운 순간이라 여기가 어색하면 몰입이 끊깁니다.
    """
    from engine.bank import build_hook
    for f in _people():
        for seg in build_hook(f, "work"):
            body = TAG.sub("", seg["html"])
            for tg in ("재성", "관성", "인성", "식상", "비겁"):
                assert (tg + " 하는데") not in body, body[:160]


def test_hook_evidence_hides_the_internal_score():
    """
    근거는 보이되 규칙은 감춥니다. 신강약 **점수**는 사람이 읽을 수 있는
    값이 아닙니다 — '중화 16' 이 그대로 나가고 있었습니다.
    """
    from engine.bank import build_hook
    for f in _people():
        for seg in build_hook(f, "work"):
            src = seg.get("source") or ""
            assert str(f.strength_score) not in src.replace(
                str(f.ten_gods[f.top_ten_god]), "", 1), (src, f.strength_score)


# ══════════════════════════════════════════════════════════
# 끝 — 기억은 마지막이 지배한다
# ══════════════════════════════════════════════════════════
@pytest.mark.parametrize("lens_id", ["nopa", "pungun", "sigye", "hongmae"])
def test_the_last_cut_is_always_the_closing(lens_id):
    """
    전에는 그 캐릭터가 **덜 본다고 미뤄 둔 컷**으로 끝났습니다.
    가장 안 중요한 말로 끝나면 컷을 아무리 늘려도 기억에 안 남습니다.
    """
    for f in _people():
        rep = build_report(f, "t", lens_id, "all", "work", None)
        assert rep["cuts"][-1]["id"] == "closing_cut", \
            (lens_id, [c["id"] for c in rep["cuts"]][-3:])


def test_closing_makes_no_new_claim():
    """덮는 말은 오늘 한 말을 되짚습니다. 새 점사를 하지 않습니다."""
    for f in _people():
        cut = next(c for c in _report(f)["cuts"] if c["id"] == "closing_cut")
        body = TAG.sub("", cut["html"])
        assert "글자에 없소" in body          # 못 본 것을 밝힌다
        assert " ".join(p["gz"] for p in f.pillars) in body


def test_week_is_countable_and_free():
    """했는지 셀 수 없는 말은 처방이 아니라 덕담입니다."""
    for f in _people():
        ids = {c["id"] for c in _report(f, "free")["cuts"]}
        assert "week" in ids
        cut = next(c for c in _report(f)["cuts"] if c["id"] == "week")
        body = TAG.sub("", cut["html"])
        assert "이번 주" in body


# ══════════════════════════════════════════════════════════
# 공유 카드
# ══════════════════════════════════════════════════════════
def test_share_card_carries_the_name_and_the_count():
    for f in _people():
        chart = build_chart(1997, 3, 22, 14, 10, "F")
        s = summary_mod.build_summary(chart, f, "love", lens_id="nopa")
        assert s["name_word"]
        assert s["rarity"]["words"]
        for reveal in ("full", "light"):
            pay = summary_mod.share_payload(s, reveal)
            assert pay["name_word"] == s["name_word"]
            assert pay["rarity"]["words"]


def test_light_share_hides_the_day_pillar():
    """여덟 글자를 감추기로 한 공유에서 일주만 흘리면 감춘 뜻이 없어집니다."""
    for f in _people():
        chart = build_chart(1997, 3, 22, 14, 10, "F")
        s = summary_mod.build_summary(chart, f, "love", lens_id="nopa")
        light = summary_mod.share_payload(s, "light")
        assert "ilju" not in light["rarity"]
        assert "pillars" not in light
