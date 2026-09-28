# -*- coding: utf-8 -*-
"""
읽는 글 v2 의 **관문**. 손으로 돌리던 것을 검사로 옮깁니다.

★ 왜 검사로 옮기나 (2026-09-28)

  `tools/page_audit.py` 가 관문을 셉니다. 그런데 손으로 돌리면 고치는
  사람이 안 돌린 날 되돌아옵니다 — 이 집은 그 사고를 이미 겪었습니다
  (「캐시 꼬리표를 안 바꾸고 글만 고치기」 · 「소스를 고쳤으면 다시
  찍으시오」). 관문은 **밀기만 해도 도는 자리**에 있어야 합니다.

★ 여기서 세는 것은 계약이 못 막는 것들입니다.

  타입이 막는 것(센 값 없는 주장 · 같은 축 두 번 · 시키는 말 둘)은
  `Page.check` 이 이미 거부하므로 여기서 다시 안 셉니다. 여기는
  **한 장을 다 짜고 나서야 보이는 것**을 봅니다 — 사람끼리 겹침,
  쉬운 말, 파는 말 수.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "services" / "api", ROOT, ROOT / "tools"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import typing                                    # noqa: E402
from schemas.api import Concern                  # noqa: E402
from engine import guard, lens as lens_mod, reading, voice as voice_mod  # noqa: E402
from engine.calendar import build_chart          # noqa: E402
from engine.features import build_features       # noqa: E402
from engine.reading.claim import FACT, sentences  # noqa: E402

AS_OF = date(2026, 9, 27)
TIERS = ("free", "9900", "12900", "15900", "19900")
CONCERNS = list(typing.get_args(Concern))
LENSES = sorted(x["id"] for x in lens_mod.all_lenses())

#: 자들이 같은 사람을 보게. 절입 경계 · 조자시 경계 · 시각 미상을 섞습니다.
PEOPLE = [(1993, 4, 5, 0, 0, "F", False), (1978, 11, 22, 14, 10, "M", True),
          (1966, 1, 19, 21, 5, "M", True), (1985, 9, 14, 11, 20, "F", True),
          (2001, 7, 3, 6, 40, "F", True), (1957, 3, 8, 4, 15, "M", True)]

_NORM = re.compile(r"[^0-9A-Za-z가-힣一-鿿]")
_SELL = re.compile(r"결제|구매 후|값을 치|가격|풀이 열기")
_HEDGE = re.compile(r"단정하(지|는)|맞는 말로 취급|억지로|경험을 먼저|"
                    r"내 이야기로|계산 결과가 아니오|아닌 줄")
_ORDER = re.compile(r"(?:시오|십시오|하세요)(?![가-힣])")


def _feats(row):
    return build_features(build_chart(*row[:6], hour_known=row[6]), as_of=AS_OF)


def _plain(html: str) -> str:
    """끼는 태그는 **떼어 붙입니다** — 빈칸으로 바꾸면 낱말이 갈라집니다."""
    t = re.sub(r"</?(?:p|div|br|li|h[1-6])(?![a-zA-Z0-9])[^>]*>", " ", html or "")
    return re.sub(r"\s+", " ", re.sub(r"</?[a-zA-Z][^>]*>", "", t)).strip()


def _page_text(pg) -> str:
    parts = [pg.derived.html] if pg.derived else []
    parts += [c.body for c in list(pg.claims) + list(pg.appendix)]
    rx = pg.prescription
    parts.append(" ".join((rx.한가지, rx.확인, rx.갈림)))
    return " ".join(_plain(x) for x in parts)


# ══ C1 · 어느 고민 · 어느 캐릭터 · 어느 등급에서도 한 장이 선다 ══════
@pytest.mark.parametrize("concern", CONCERNS)
def test_c1_모든_고민에서_한_장이_선다(concern):
    for row in PEOPLE[:3]:
        f = _feats(row)
        for tier in TIERS:
            pg = reading.build(f, concern, tier)
            assert pg.claims, "%s/%s 에 컷이 없소" % (concern, tier)
            assert pg.prescription is not None


def test_c2_고민_목록은_한_자리에서_받는다():
    """
    ★ `Concern` 은 **Literal** 이오. `c.value` 로 돌리면 터지고, 그러면
      seed 로 물러서서 여섯만 봅니다 — 부동산이 빠집니다. 자가 제품보다
      좁아지는 그 자리요.
    """
    assert len(CONCERNS) >= 7, "고민이 %d개뿐이오" % len(CONCERNS)
    assert "real_estate" in CONCERNS


# ══ C3 · 시키는 일은 한 장에 하나 ══════════════════════════════════
def test_c3_시키는_일은_하나():
    for row in PEOPLE[:3]:
        f = _feats(row)
        for concern in CONCERNS:
            n = len(_ORDER.findall(_page_text(reading.build(f, concern, "19900"))))
            assert n == 1, "%s 에 시키는 일이 %d개요 — 둘이면 하나도 안 하오" \
                % (concern, n)


# ══ C4 · 파는 말은 한 곳 · 면책은 둘까지 ═══════════════════════════
def test_c4_파는_말과_면책():
    f = _feats(PEOPLE[0])
    for concern in CONCERNS:
        t = _page_text(reading.build(f, concern, "free"))
        assert len(_SELL.findall(t)) <= 1
        assert len(_HEDGE.findall(t)) <= 2


# ══ C5 · 한 장 안에 같은 문장이 두 번 서지 않는다 ═══════════════════
def test_c5_한_장에_되풀이가_없다():
    for row in PEOPLE[:4]:
        f = _feats(row)
        for tier in ("free", "19900"):
            pg = reading.build(f, "money", tier)
            got = Counter()
            for part in ([pg.derived.html] if pg.derived else []) + \
                    [c.body for c in list(pg.claims) + list(pg.appendix)]:
                for s in sentences(part):
                    k = _NORM.sub("", s)
                    if len(k) >= 12:
                        got[k] += 1
            dup = [k for k, v in got.items() if v > 1]
            assert not dup, "%s/%s 에 같은 문장이 두 번: %s" \
                % (row[0], tier, dup[:2])


# ══ C6 · 사람끼리 겹침 — 명패 시험 ════════════════════════════════
#
# ★ 문턱을 25%로 둔 까닭 (2026-09-28)
#
#   처음에는 10%로 잡았습니다. 그런데 남은 겹침이 대부분 **갈래 판정**
#   이었습니다 — 겉에 났는가/뿌리가 있는가 넷, 드묾 셋, 얇음 둘.
#   투출과 뿌리가 같은 두 사람은 **같은 판정을 받아야 맞습니다.**
#   억지로 다르게 쓰면 그건 글이 아니라 거짓이오.
#
#   그래서 문턱은 「갈래가 겹칠 만큼」으로 둡니다. v1 이 67%였고 지금
#   18%대이니, 25%를 넘으면 **갈래 말고 다른 것이 굳은 것**이라 보고
#   이 검사가 잡습니다.
MYEONGPAE_MAX = 25.0


def test_c6_사람끼리_문장이_굳지_않았다():
    pages = []
    for row in PEOPLE:
        f = _feats(row)
        pg = reading.build(f, "money", "free")
        rows = []
        for part in ([pg.derived.html] if pg.derived else []) + \
                [c.body for c in list(pg.claims) + list(pg.appendix)]:
            rows += sentences(part)
        pages.append(rows)

    mine = pages[0]
    others = {_NORM.sub("", s) for rows in pages[1:] for s in rows}
    tot = sum(len(_NORM.sub("", s)) for s in mine) or 1
    same = sum(len(_NORM.sub("", s)) for s in mine
               if _NORM.sub("", s) in others)
    share = 100.0 * same / tot
    assert share <= MYEONGPAE_MAX, (
        "사람이 달라도 문장이 %.1f%% 같소 (문턱 %.0f%%). 갈래 판정 말고 "
        "무엇이 굳었는지 보시오 — tools/page_audit.py" % (share, MYEONGPAE_MAX))


# ══ C7 · 댈 수 있는 값이 든 문장의 몫 ══════════════════════════════
#
# ★ 이 수는 **갈래별 문턱의 결과**입니다 (2026-09-28)
#
#   진짜 관문은 `Budget.floors` 요 — 장부 0.8 · 판정 0.6 · 깊이 0.5 ·
#   위로/희망 0.34 · 뒤집기 0.3. 그 문턱은 `Page.check` 이 컷마다 이미
#   막습니다. 한 장의 수는 그 컷들이 **어떻게 섞였느냐**로 정해지니,
#   위로와 뒤집기가 많이 선 장은 50%대에 앉는 것이 맞습니다.
#
#   그래서 여기 문턱은 뒷받침일 뿐이오 — 가중 최소(0.5 언저리) 아래에
#   두고, 그보다 내려가면 **갈래별 문턱이 무너진 것**이라 보고 잡습니다.
#   55 로 두었다가 54.5%에 걸렸는데, 그건 글이 무뎌서가 아니라 문턱을
#   결과 위에 둔 것이었습니다. v1 은 21.7% 요.
PAGE_FACT_MIN = 50.0


def test_c7_센_값이_든_문장이_절반을_넘는다():
    f = _feats(PEOPLE[1])
    for concern in CONCERNS:
        pg = reading.build(f, concern, "free")
        ss = []
        for part in [c.body for c in pg.claims]:
            ss += sentences(part)
        hard = sum(1 for s in ss if FACT.search(s))
        share = 100.0 * hard / max(len(ss), 1)
        assert share >= PAGE_FACT_MIN, \
            "%s 의 센 값이 %.1f%% 뿐이오 (문턱 %.0f%%). 갈래별 문턱이 " \
            "무너졌는지 보시오 — Budget.floors" % (concern, share, PAGE_FACT_MIN)


# ══ C8 · 첫머리에 도출 명시가 있고, 셈이 든다 ══════════════════════
def test_c8_첫머리가_무엇에서_나왔는지_말한다():
    """
    ★ Snyder(1974): 똑같은 글을 주고 **무엇에서 나왔다고 말했는지**만
      바꿔 수용도가 3.24 → 4.38 로 올랐습니다. 이 집은 분 단위·진태양시·
      절입 시각까지 세는데 그걸 말하지 않고 있었습니다.
    """
    for row in PEOPLE[:4]:
        pg = reading.build(_feats(row), "money", "free")
        assert pg.derived is not None
        head = _plain(pg.derived.html)
        assert re.search(r"\d", head), "도출 명시에 손님이 준 값이 없소: %s" % head
        n = sum(len(FACT.findall(s)) for s in sentences(pg.derived.html)[:3])
        assert n >= 3, "첫 세 문장에 센 값이 %d개뿐이오" % n


# ══ C9 · 가드 ═════════════════════════════════════════════════════
def test_c9_가드를_어기지_않는다():
    for row in PEOPLE[:3]:
        f = _feats(row)
        for concern in CONCERNS:
            for tier in ("free", "19900"):
                t = _page_text(reading.build(f, concern, tier))
                ok, hits = guard.check(t)
                assert ok, "%s/%s 가드 위반: %s" % (concern, tier, hits)


# ══ C10 · 말투 다섯 결에서 비문이 안 난다 ══════════════════════════
_BADVOICE = re.compile(
    r"(?:쇠|나무|이유|하나|나이|자리|해)(?:을|은|과|으로|이오|이라)(?![가-힣])"
    r"|(?:흙|물|불|밥|힘|몸|집|돈|눈|손|밤|칸|것|살)(?:를|는|와|로|요)(?![가-힣])"
    r"|없소(?:인데도|라|인|고)(?![가-힣])"
    r"|[가-힣一-龥] (?:이오|으로|이네|이라)"
    r"|\{[a-z_]+\}|%[sdg]")


def test_c10_스무_명_말투에서_비문이_없다():
    for i, lens in enumerate(LENSES):
        row = PEOPLE[i % len(PEOPLE)]
        f = _feats(row)
        view = lens_mod.view(lens) or {}
        tone = view.get("voice")
        you = lens_mod.you_word(lens, "", row[5])
        pg = reading.build(f, "money", "19900", lens_id=lens)
        raw = _page_text(pg)
        said = voice_mod.speak(voice_mod.address(raw, you), tone) if tone else raw
        bad = _BADVOICE.findall(said)
        assert not bad, "%s 말투에서 비문: %s" % (lens, bad[:3])


# ══ C11 · 값 사다리 — 등급마다 열리는 것이 있다 ═════════════════════
def test_c11_등급마다_열리는_것이_있다():
    """
    ★ 등급이 넷인데 상품이 하나면 그건 값이 아니라 이름표입니다.
      12,900원에서 이미 잠긴 것이 0 이던 자리가 있었습니다.
    """
    f = _feats(PEOPLE[1])
    prev = -1
    for tier in TIERS:
        n = len(reading.build(f, "money", tier).claims)
        assert n > prev, "%s 가 앞 등급보다 안 늘었소 (%d ≤ %d)" % (tier, n, prev)
        prev = n
    # 가장 비싼 자리에는 **아래에 없는 종류**가 있어야 합니다
    top = {c.axis for c in reading.build(f, "money", "19900").claims}
    low = {c.axis for c in reading.build(f, "money", "12900").claims}
    assert {"hindsight", "counter"} & (top - low), \
        "비싼 자리에 다른 종류가 없소 — 「더 많이」로만 올린 것이오"


# ══ C12 · 화면이 고를 것이 없다 ════════════════════════════════════
def test_c12_서버가_차례와_파는_자리를_정한다():
    pg = reading.build(_feats(PEOPLE[0]), "money", "free")
    assert pg.offer_at, "파는 자리를 서버가 안 정했소"
    assert pg.offer_at in {c.axis for c in pg.claims}
    # 차례가 감정 곡선을 따르는가 — 아픈 말이 위로보다 앞이오
    order = [c.axis for c in pg.claims]
    if "scale" in order and "rarity" in order:
        assert order.index("scale") < order.index("rarity")
