"""
리포트 조립 — 무료 6단 + 유료 컷. docs/03 · docs/06

★ 여기서 **새 점사 문장을 지어내지 않습니다.**
  전부 seed/bank.json 의 표와 Feature Store 값에서만 조립합니다.
  없는 조합은 BankError 로 터뜨리고, 채우려면 뱅크에 문장을 추가합니다.

tier
    free  무료 구간만 (1~4컷)
    one   고른 영역 하나 — 시기(대운)와 용신까지
    all   여덟 글자 전부 — 대운 맵·성향 대조까지
    sub   구독 — all 과 동일 범위
"""
from __future__ import annotations

import hashlib
from typing import Optional

from . import bank as bank_mod
from . import calendar as cal_mod
from . import extras as extras_mod
from . import guard
from . import lens as lens_mod
from . import lens_cuts as lens_cuts_mod
from . import rarity as rarity_mod
from . import why as _why
from . import sinsal as sinsal_mod
from . import terms as terms_mod
from . import voice as voice_mod
from .bank import (amount_adj, amount_word, count_word,
                   element_word, josa)

import json as _json
import re as _re
from functools import lru_cache as _lru
from pathlib import Path as _Path

# ── 태그를 걷어 사람이 읽는 글로 ──────────────────────────
#
# ★ 인라인과 블록을 갈라야 합니다.
#   전부 공백으로 바꾸면 <b>쇠</b>이오 가 "쇠 이오" 가 되고,
#   전부 빈칸으로 바꾸면 </p><p> 가 붙어 두 문장이 한 덩어리가 됩니다.
_BLOCK_TAG = _re.compile(
    r"</?(?:p|div|br|li|ul|ol|tr|td|th|table|h[1-6]|section)\b[^>]*>",
    _re.I)
_TAG = _re.compile(r"<[^>]+>")


def _plain(html: str) -> str:
    """컷 본문의 글자만. 분량을 세거나 맛보기를 뽑을 때 씁니다."""
    text = _BLOCK_TAG.sub(" ", html or "")   # 블록은 띄운다
    text = _TAG.sub("", text)                # 인라인은 붙인다
    return _re.sub(r"\s+", " ", text).strip()


@_lru(maxsize=1)
def _sinsal_text() -> dict:
    p = _Path(__file__).resolve().parents[3] / "seed" / "sinsal.json"
    return _json.loads(p.read_text("utf-8"))


@_lru(maxsize=1)
def _rarity_text() -> dict:
    p = _Path(__file__).resolve().parents[3] / "seed" / "rarity_text.json"
    return {k: v for k, v in _json.loads(p.read_text("utf-8")).items()
            if k != "_"}
from .constants import ELEMENT_OF_GAN, ten_god

TIERS = ("free", "one", "all", "sub")
# ★ sub 이 all 과 같은 층(2)이었습니다. 그래서 9,900원/월이 24,900원과
#   똑같은 것을 열었고, 「이 자리 하나」까지 덮었습니다.
#   sub 은 **넓이**를 팝니다 — 스무 사람을 기본 층(1)으로.
#   깊이(대운 맵 · 성향 대조)는 one 의 값 사다리와 all 의 몫입니다.
TIER_LEVEL = {"free": 0, "one": 1, "all": 2, "sub": 1}

# ══════════════════════════════════════════════════════════
# 값이 여는 층 — 「이 자리 하나」 안에서
# ══════════════════════════════════════════════════════════
#
# ★ 왜 필요했나
#   「이 자리 하나」의 값은 캐릭터마다 4,900~19,900원인데 **여는 것이
#   전부 같았습니다.** 재보니 4,900원과 19,900원이 둘 다 10컷이었고,
#   12,900 · 9,900 · 6,900 · 4,900 **네 등급이 전부 같은 상품**이었습니다.
#   등급이 넷인데 상품이 하나면 그건 값이 아니라 이름표입니다.
#
# ★ 위로만 쌓습니다 — 아무도 잃지 않게
#   싼 등급에서 무언가를 빼는 방법도 있지만 쓰지 않았습니다. 이미 그
#   값을 치르고 받아 본 사람이 있습니다. 그래서 **지금 열리는 것은
#   그대로 두고**, `all` 에서만 열리던 두 컷을 위쪽 등급에 얹었습니다.
#   `all` · `sub` 은 여전히 전부 봅니다 — 잃는 쪽이 없습니다.
#
# ★ 값을 여기 적지 않습니다
#   문턱만 적습니다. 캐릭터 값은 seed/lenses.json 한 곳에 있고
#   payments.price_of 가 그걸 청구합니다. 값이 두 벌이 되면 또
#   어긋납니다 — 그 사고가 실제로 있었습니다.
PRICE_RUNGS = ((12900, "daeun_map"), (15900, "axis"))


def rungs_at(price: int) -> set:
    """이 값이 「이 자리 하나」에서 더 여는 컷."""
    return {cid for threshold, cid in PRICE_RUNGS if price >= threshold}


# ══════════════════════════════════════════════════════════
# 잠긴 컷의 첫 줄 — 궁금증은 구체적일 때만 생긴다
# ══════════════════════════════════════════════════════════
#
# ★ 여기가 비어 있었습니다.
#   페이월(c4)이 잠긴 컷마다 `가가가가 가가가가가 가가가` 를 그리고
#   있었습니다. 자리표시 문자열이 그대로 배포된 것입니다.
#
#   정보 격차는 **구체적인 것에만** 생깁니다. 무엇을 놓치는지 모르면
#   아쉽지도 않습니다. 제목만으로는 약합니다.
#
# ★ 본문을 주는 것이 아닙니다.
#   첫 문장 하나를, 그것도 **끝까지 주지 않고** 자릅니다. 그 한 줄에
#   이 명식에만 해당하는 것(나이·연도·글자·개수)이 들어 있으면
#   손님은 무엇이 잠겼는지 압니다. 나머지는 여전히 안 내려갑니다.
#
# ★ 자르는 자리를 고릅니다.
#   조사에서 자르면 ("그대의 대운이") 문장이 끊긴 게 아니라 망가진
#   것처럼 보입니다. **명사 뒤**에서 자릅니다.
TEASER_MAX = 44
TEASER_MIN = 12
# 본문의 이만큼을 넘겨주지 않습니다. 짧은 컷에서 맛보기가 본문이 되는
# 것을 막습니다 — 100자짜리 대운 맵에 44자를 주면 그건 맛보기가 아닙니다.
TEASER_SHARE = 0.4

# 이 뒤에서 자르면 어색한 글자들 — 조사·어미의 첫 글자
_BAD_TAIL = "은는이가을를의에서도만과와로으며고나지야한할하며되"


def _teaser(html: str) -> Optional[str]:
    """잠긴 컷의 첫 줄. 본문이 아니라 **맛보기**입니다."""
    text = _plain(html)
    if len(text) < TEASER_MIN:
        return None

    limit = min(TEASER_MAX, int(len(text) * TEASER_SHARE))
    if limit < TEASER_MIN:
        return None

    # 첫 문장이 한도 안에 끝나면 문장째로 줍니다.
    m = _re.search(r"[.!?…]", text[:limit + 6])
    if m and m.end() >= TEASER_MIN and m.end() <= limit + 6:
        return text[:m.end()].strip()

    head = text[:limit].rstrip()
    # 명사 뒤로 물러섭니다. 조사에서 끊긴 채로 내보내지 않습니다.
    while len(head) > TEASER_MIN and head[-1] in _BAD_TAIL:
        head = head[:-1].rstrip()
    if len(head) < TEASER_MIN:
        head = text[:limit].rstrip()
    return head + " —"


def _cut(cid, title, source, body, min_level, sid=None):
    return {
        "id": cid,
        "title": title,
        "source": source,
        "html": guard.enforce(body, {"cut": cid}),
        "min_level": min_level,
        "statement_id": sid,
    }


def _all_cuts(f, concern: str, you: str, axis4: Optional[str],
              lens_id: Optional[str] = None,
              extras: Optional[dict] = None) -> tuple[list, Optional[str]]:
    """돌려주는 것: (컷 목록, 추가 입력이 틀렸으면 그 사유)"""
    B = bank_mod.bank()
    top, weak, strong = f.top_ten_god, f.weak_el, f.strong_el
    lack = B["LACK"][weak]
    patt = B["PATT"][top]
    daeun = f.daeun[f.daeun_now]
    cuts = []

    # ── 1 · 명식과 셈에 쓴 것 ─────────────────────────────
    c = f.correction
    rows = [
        ("표준시", c["std_label"]),
        ("서머타임", "적용 · 1시간 되돌림" if c["dst"] else "해당 없음"),
        ("진태양시", "%s → %+.1f분" % (c["city"], c["lon_min"])),
        ("보정", "%s → %s%s" % (c["before"], c["after"],
                              " (%s일)" % ("익" if c["day_shift"] > 0 else "전")
                              if c["day_shift"] else "")),
        ("절기", "%s 절입 %s 기준" % (c["jieqi_name"], c["jieqi_at_kst"])),
        ("시주", "산출됨" if c["hour_used"] else "제외 — 세 기둥으로 계산"),
    ]
    cuts.append(_cut(
        "chart", "명식",
        _why.line("여덟 글자" if f.hour_known else "여섯 글자",
                  "월지", "강약"),
        ('<div class="pillars">%s</div><div class="calc">%s</div>%s'
         % ("".join('<div class="p"><span class="lb">%s</span><b>%s</b></div>'
                    % (p["label"], p["gz"]) for p in f.pillars),
            "".join('<div class="r"><span class="k">%s</span>'
                    '<span class="v">%s</span></div>' % kv for kv in rows),
            ('<p class="note">%s</p>' % c["boundary_note"])
            if c["boundary_note"] else "")),
        0))

    # ── 2 · 없는 것부터 ──────────────────────────────────
    if len(f.weak_els) > 1:
        also = ("<p class=\"tale\">%s 도 같이 바닥이오. 둘 다 없는 자리요.</p>"
                % " · ".join(element_word(x) for x in f.weak_els if x != weak))
    else:
        also = ""
    # ★ 곱하는 축: 약오행(5) × 강오행(5) × 동률 × **주도십신(10)**
    #   전에는 마지막 축이 없어 52가지였고, 한 문장이 8.6%를 가져갔습니다.
    cuts.append(_cut(
        "lack", "1 · 없는 것부터",
        # ★ 원점수(`불 0.3`)를 그대로 내면 그건 근거가 아니라 계기판입니다.
        #   손님은 0.3 이 큰지 작은지 모릅니다. 사람 말로 냅니다.
        _why.line(
            "%s %s%s" % (element_word(weak), amount_word(f.elements[weak]),
                         " (동률 %d)" % len(f.weak_els)
                         if len(f.weak_els) > 1 else ""),
            "용신", "용신"),
        # ★ 세는 수를 **되돌려** 놓습니다.
        #
        #   원점수(`물 4.0`)를 걷어 냈더니 이 컷에 확인할 수 있는 수가
        #   하나도 안 남아, 어떤 사람이 읽어도 맞는 말이 됐습니다
        #   (tests/test_falsifiable.py 가 잡았습니다). 대신 **겉에
        #   보이는 글자 수**를 냅니다 — 손님이 만세력을 펴고 세면
        #   같은 수가 나와야 하는, 틀릴 수 있는 수입니다.
        ('<p class="tale">눈에 띄는 건 %s %s 게 아니오. '
         '<b>%s %s 것</b>이지.</p>'
         '<p class="tale">여덟 글자 겉에 %s <b>%s</b>, '
         '%s <b>%s</b>. 세어 보시오.</p>'
         '<p class="tale">%s <b>%s</b>이오. 그게 없이 살아온 것이오.</p>'
         '<p class="tale">%s</p>'
         % (josa(element_word(strong), "이", "가"),
            amount_adj(f.elements[strong]),
            josa(element_word(weak), "이", "가"),
            amount_adj(f.elements[weak]),
            josa(element_word(strong), "은", "는"),
            _how_many(f, strong),
            josa(element_word(weak), "은", "는"),
            _how_many(f, weak),
            josa(element_word(weak), "은", "는"), lack["w"],
            B["LACK_LIVED"][top]) + also),
        0, sid="lack:%s:%s" % (weak, top)))

    # ── 2b · 몇이나 되는가 (희소도) ───────────────────────
    #
    # ★ 무료입니다. 여기가 공유를 만드는 자리라 값 뒤에 두면 뜻이 없습니다.
    #
    # ★ 왜 넣었나
    #   바깥에서 찾은 것 중 가장 큰 지렛대가 **반증 가능한 구체성**이었습니다.
    #   바넘 문장은 틀릴 수가 없어 '맞다' 는 나와도 '소름 돋는다' 는 안 나옵니다.
    #   사주는 세는 물건이라 이 자리에서 **지어내지 않고 셀 수** 있습니다.
    #
    # ★ 골라 담지 않습니다. 축 넷을 미리 정해 두고 그 칸의 비율을 그대로
    #   말합니다. 흔하면 흔하다고 합니다 — 드문 쪽만 말하면 화면에 남는
    #   숫자가 전부 드물어 보입니다.
    R = _rarity_text()
    rr = rarity_mod.look(f)
    band = R["band"][rr["band"]]
    parts = rr["parts"]
    cuts.append(_cut(
        "rarity", "몇이나 되는가",
        ("표본 %s명 — 인구에서 몇 명인지를 센 것이오. "
         "맞힌다는 말이 아니라 세었다는 말이오 〔희소도 · 표본 계수〕"
         % format(rr["sample"], ",")),
        ('<p class="tale">%s</p>'
         '<p class="tale">%s %s %s %s</p>'
         '<p class="tale">%s</p><p class="tale">%s</p>'
         '<p class="tale">%s</p><p class="sm">%s</p>'
         % (R["lead"],
            R["zero"][parts["zero"]], R["strength"][parts["strength"]],
            R["helper"][parts["helper"]], R["ilji"][parts["ilji"]],
            band["line"].format(words=rr["words"]), band["tail"],
            R["ilju"].format(gz=rr["ilju"]["gz"], words=rr["ilju"]["words"]),
            R["note"].format(sample=format(rr["sample"], ",")))),
        0, sid="rarity:%s:%s" % (rr["key"], rr["ilju"]["gz"])))

    # ── 3 · 왜 반복되나 ──────────────────────────────────
    st_line = {
        "신강": "게다가 신강이오. 쏟을 힘은 넘치는데 받을 그릇이 없지.",
        "신약": "게다가 신약이오. 채워야 하는데 채울 그릇도 없소.",
        "중화": "중화라 크게 티는 안 났을 게요. 그래서 더 오래 몰랐지.",
    }[f.strength]
    # ★ 곱하는 축에 **흐름(5)** 을 더했습니다.
    cuts.append(_cut(
        "why", "2 · 왜 반복되나",
        _why.line("%s %d · %s · %s 흐름"
                  % (top, f.ten_gods[top], f.strength, f.flow), top, "십신"),
        ('<p class="tale">%s. 그리고 %s.</p><p class="tale">%s</p>'
         '<p class="tale">그래서 끝에서 <b>%s</b>.</p>'
         '<p class="tale">%s</p>'
         % (bank_mod._pick("IGNITE", top, concern), patt["b"], st_line,
            bank_mod._pick("BLAME", top, f.strength),
            B["WHY_TAIL"][f.flow])),
        0, sid="why:%s:%s:%s:%s" % (top, concern, f.strength, f.flow)))

    # ── 4 · 어느 자리에서 ────────────────────────────────
    if f.ilji_chung:
        place = ('일지 <b>%s</b>가 부딪히고 있소. 사람 자리가 조용할 수 없는 배치요.'
                 % f.day_ji)
    else:
        place = '일지 <b>%s</b>는 조용한 편이오. 대신 밖에서 흔들리지.' % f.day_ji
    if f.gwan >= 2:
        lean = "관이 둘이라 책임이 앞장서오."
    elif f.jae >= 2:
        lean = "재가 둘이라 손이 크오."
    elif f.sik >= 2:
        lean = "식상이 둘이라 만드는 데 힘이 쏠리오."
    else:
        lean = "어느 한쪽으로 크게 기울지 않았소."
    # ★ 곱하는 축에 **일간(10)** 을 더했습니다.
    cuts.append(_cut(
        "place", "3 · 어느 자리에서",
        _why.line("일지 %s%s · %s일간"
                  % (f.day_ji, " 충" if f.ilji_chung else "", f.day_gan),
                  "일지", "십신"),
        # ★ 셀 수 있는 줄. 이 컷은 일지·일간을 보면서 **개수를 안 냈습니다** —
        #   그래서 틀릴 수가 없었습니다. 관·재·식상을 세어 박습니다.
        ('<p class="cnt"><b>관성 %d · 재성 %d · 식상 %d.</b></p>'
         '<p class="tale">%s</p><p class="tale">%s</p><p class="tale">%s</p>')
        % (f.gwan, f.jae, f.sik, place, lean, B["PLACE_NOTE"][f.day_gan]),
        0, sid="place:%s:%s:%s" % (f.day_ji, "chung" if f.ilji_chung else "-",
                                   f.day_gan)))

    # ── 5 · 지금 어디에 (대운 + 세운) ─────────────────────
    #
    # ★ 여기를 **틀릴 수 있는 말**로 고쳤습니다.
    #   바넘 문장은 어떤 관찰에서도 살아남아서 '맞다' 는 나와도 '소름 돋는다'
    #   는 안 나옵니다. 놀라움은 **틀릴 수도 있었는데 맞았을 때**만 옵니다.
    #   대운수는 절입일까지의 실제 일수로 이미 정확히 세어 두었는데, 문장은
    #   '지금은 정재 대운이오' 로만 말하고 있었습니다 — 가진 숫자를 안 썼습니다.
    #
    # ★ 연 나이 기준입니다. features 의 age 와 daeun.start_age 가 모두
    #   `올해 - 태어난 해` 라, `saju_year + start_age` 가 곧 그 해입니다.
    #   두 기준을 섞으면 한 해가 어긋나므로 여기서 다시 세지 않습니다.
    #
    # ★ 그 해에 무슨 일이 생긴다고 말하지 않습니다. 바뀌는 때만 셉니다.
    heavy = daeun["ten_god"] in ("편관", "상관", "겁재")
    this_year = f.saju_year + f.age
    start_year = f.saju_year + daeun["start_age"]

    if f.daeun_started:
        lead = ('<p class="tale">지금은 <b>%s</b> 대운이오. '
                '<b>%d세</b>—<b>%d년</b>부터 들어와 있소.</p>'
                % (daeun["gz"], daeun["start_age"], start_year))
    else:
        # 아직 첫 대운에 들지 않았다. 들어갔다고 말하지 않는다.
        lead = ('<p class="tale">아직 첫 대운에 들지 않았소. '
                '<b>%s</b> 대운은 <b>%d세</b>—<b>%d년</b>부터요. '
                '그때까지는 대운이 아니라 여덟 글자가 그대로 도오.</p>'
                % (daeun["gz"], daeun["start_age"], start_year))

    # 다음 마디가 언제인가 — 이게 이 컷에서 가장 틀릴 수 있는 말입니다.
    nxt = f.daeun[f.daeun_now + 1] if f.daeun_now + 1 < len(f.daeun) else None
    if nxt and f.daeun_started:
        end_year = f.saju_year + nxt["start_age"]
        left = end_year - this_year
        if left <= 0:
            when = ('<p class="tale">그리고 <b>올해</b> 이 결이 끝나오. '
                    '<b>%s</b> 대운으로 넘어가는 해요.</p>' % nxt["gz"])
        elif left == 1:
            when = ('<p class="tale">이 결은 <b>내년 %d년</b>에 끝나오. '
                    '<b>%d세</b>부터 <b>%s</b> 대운이오. 한 해 남았소.</p>'
                    % (end_year, nxt["start_age"], nxt["gz"]))
        else:
            when = ('<p class="tale">이 결은 <b>%d세</b>—<b>%d년</b>에 끝나오. '
                    '<b>%d해</b> 남았고, 그 다음은 <b>%s</b> 대운이오.</p>'
                    % (nxt["start_age"], end_year, left, nxt["gz"]))
        when += ('<p class="sm">해가 바뀌는 자리는 설이 아니라 <b>입춘</b>이오. '
                 '그 언저리에 난 사람은 한 해가 앞뒤로 갈리오.</p>')
    else:
        when = ""

    # 세운 — 올해와 내년. 명식의 년주를 세는 그 식으로 셉니다.
    sun_g, sun_j = cal_mod.year_ganji(this_year)
    nxt_g, nxt_j = cal_mod.year_ganji(this_year + 1)
    sun_tg = ten_god(sun_g, f.day_gan)
    nxt_tg = ten_god(nxt_g, f.day_gan)
    # 십신은 대개 받침이 있소 — 비견·식신·상관·편관·정관·편인·정인.
    # 조사를 안 보고 붙이면 "상관요" 가 나옵니다. (bank.josa)
    sewoon = ('<p class="tale">해로 좁혀 보면 <b>%d년은 %s%s</b> — '
              '<b>%s</b>의 해요. 내년 %d년은 <b>%s%s</b>, <b>%s</b></p>'
              % (this_year, sun_g, sun_j, sun_tg,
                 this_year + 1, nxt_g, nxt_j,
                 josa(nxt_tg, "이오.", "요.")))

    cuts.append(_cut(
        "daeun_now", "4 · 지금 어디에",
        _why.line("대운 %s · %s%s · 세운 %s%s" % (
            daeun["gz"], f.daeun_ten_god,
            "" if f.daeun_started else " · 진입 전", sun_g, sun_j),
            "대운", ""),
        (lead + '<p class="tale">이 구간의 성격은 <b>%s</b>. %s</p>%s%s'
         % (f.daeun_ten_god,
            "조용히 지나가지 않는 구간이오." if heavy
            else "크게 흔들리진 않소. 다지는 구간이지.",
            when, sewoon)),
        1, sid="daeun:%s:%s" % (f.daeun_ten_god, sun_tg)))

    # ── 6 · 필요한 것 (용신 + 다과상) ────────────────────
    # ★ 여기가 가장 심하게 겹치던 자리입니다.
    #   용신(5) × 신강여부(2) = **10가지가 상한**이라 문장을 더 써도
    #   늘지 않았습니다. 3,000명 중 415명이 같은 문장을 받았습니다(11%).
    #   유료 리포트가 무료 훅보다 더 겹치고 있었습니다.
    #   그래서 **계절(4)** 과 **주도십신(10)** 을 곱합니다 → 상한 400가지.
    tea = bank_mod.tea(f)
    season = bank_mod.born_season(f)
    cuts.append(_cut(
        "yongsin", "5 · 필요한 것",
        _why.line("용신 %s · %s생 · %s" % (f.yongsin, season, top),
                  "용신", "용신"),
        ('<p class="tale">그대에게 필요한 건 <b>%s</b>이오.</p>'
         '<p class="tale">%s</p>'
         '<p class="tale">%s 사람에게서 그걸 구하면 그 사람이 지치오. '
         '<b>먼저 그대 안에 두시오.</b></p>'
         '<p class="tale">%s</p>'
         '<div class="tea"><b>%s</b><p>%s</p></div>'
         % (element_word(f.yongsin),
            B["YONGSIN_SEASON"][season],
            "남는 힘을 빼내 방향을 잡아줄 것." if f.strength == "신강"
            else "모자란 힘을 채워줄 것.",
            B["YONGSIN_WHERE"][top],
            tea["name"], tea["text"])),
        1, sid="yongsin:%s:%s:%s:%s" % (f.yongsin, f.strength, season, top)))

    # ── 7 · 대운 맵 ─────────────────────────────────────
    cuts.append(_cut(
        "daeun_map", "6 · 대운 맵",
        _why.line("대운수 %d · %s" % (f.daeun[0]["start_age"],
                                    "순행" if f.forward else "역행"),
                  "대운", ""),
        ('<div class="dmap">%s</div>'
         '<p class="note">대운수는 절입일까지의 실제 일수 ÷ 3 으로 셈했소.</p>'
         % "".join(
             '<div class="d%s"><span class="age">%d</span>'
             '<b>%s</b><span class="tg">%s</span></div>'
             % (" now" if d["index"] == f.daeun_now else "",
                d["start_age"], d["gz"], d["ten_god"])
             for d in f.daeun)),
        2))

    # ── 7b · 이름 붙은 자리 (신살) ─────────────────────────
    T = _sinsal_text()
    if f.sinsal:
        rows = []
        for sv in f.sinsal:
            m = T["meaning"].get(sv["key"], {})
            rows.append(
                '<div class="ss %s"><div class="hd"><b>%s</b>'
                '<span class="hj">%s</span><span class="tag">%s</span></div>'
                '<div class="at">%s · %s</div><p>%s</p>%s</div>'
                % ("good" if sv["kind"] == "길신" else "warn",
                   sv["name"], sv["hanja"], sv["kind"],
                   " · ".join(sv["at"]), sv["target"],
                   m.get("text", ""),
                   ('<p class="sm">%s</p>' % m["caution"]) if m.get("caution") else ""))
        body = "".join(rows)
    else:
        body = '<p class="tale">%s</p>' % T["none"]["sinsal"]
    cuts.append(_cut(
        "sinsal", "이름 붙은 자리",
        _why.line("신살 %d · 공망 %s" % (len(f.sinsal), f.gongmang),
                  "신살", "신살"),
        body + '<p class="sm">신살 표는 유파마다 다르오. 우리가 쓰는 표를 '
               '문서에 적어 두었소.</p>',
        0, sid="sinsal:%s" % ",".join(x["key"] for x in f.sinsal)))

    # ── 7c · 누가 돕는가 ──────────────────────────────────
    if f.helpers:
        seen_p = []
        rows = []
        for h in f.helpers:
            if h["pillar"] in seen_p:
                continue
            seen_p.append(h["pillar"])
            names = [x["sinsal"] for x in f.helpers if x["pillar"] == h["pillar"]]
            rows.append(
                '<div class="hp"><div class="hd"><b>%s</b>'
                '<span class="tag">%s</span></div>'
                '<p>%s</p><p class="sm">%s</p></div>'
                % (" · ".join(names), h["pillar"],
                   T["helper_lead"][h["pillar"]], h["kind"]))
        body = ('<p class="tale">길신이 앉은 자리를 궁위로 읽은 것이오. '
                '누가 도울 사람인지 그 방향만 짚소.</p>' + "".join(rows))
    else:
        # ★ 여기가 '가짓수는 많은데 쏠린' 자리였습니다.
        #   helper 컷 전체는 1,334가지였는데, 길신이 하나도 없는 사람
        #   10.3%가 **전부 같은 한 문장**을 받고 있었습니다.
        #   가짓수만 보면 안 보이고, 최다 점유를 봐야 보입니다.
        body = ('<p class="tale">%s</p><p class="tale">%s</p>'
                % (B["HELPER_NONE_LEAD"][f.strength],
                   B["HELPER_NONE_WAY"][f.yongsin]))
    cuts.append(_cut(
        "helper", "누가 돕는가",
        _why.line("길신 %d자리" % len({h["pillar"] for h in f.helpers}),
                  "신살", "신살"),
        body, 1, sid=("helper:%s" % ",".join(
            sorted({h["sinsal"] + ":" + h["pillar"] for h in f.helpers}))
            if f.helpers else "helper:none:%s:%s" % (f.strength, f.yongsin))))

    # ── 7d · 뿌리 (조상 자리) ─────────────────────────────
    a = f.ancestor
    stance_text = T["ancestor_stance"][a["stance"]]
    good = ("<p class=\"sm\">이 자리에 %s 이 함께 앉았소.</p>"
            % " · ".join(a["good_sinsal"])) if a["good_sinsal"] else ""
    bad = ("<p class=\"sm\">이 자리에 %s 도 함께 있소.</p>"
           % " · ".join(a["bad_sinsal"])) if a["bad_sinsal"] else ""
    cuts.append(_cut(
        "ancestor", "뿌리 · 조상 자리",
        _why.line("년주 %s · %s / %s"
                  % (a["pillar"], a["gan_ten_god"], a["ji_ten_god"]),
                  "궁위", "신살"),
        # ★ 조상 자리도 셀 수 있는 것이 하나도 없었습니다.
        #   년주는 **몇 살까지 크게 작용하는 자리**인지 이 집이 이미
        #   압니다(궁위). 나이를 박으면 틀릴 수 있는 말이 됩니다.
        ('<p class="tale">%s</p>'
         '<p class="cnt"><b>년주는 대개 열다섯 안쪽을 비추는 자리요. '
         '그대는 지금 %d살이니, 여기 적힌 건 이미 지나온 자리요.</b></p>'
         '<p class="tale">그대 년주는 <b>%s</b>. 위는 %s, 아래는 %s요.</p>'
         '<p class="tale">%s</p>%s%s'
         '<p class="sm">물려받은 결이라 보던 것은 <b>%s</b> 쪽이오. '
         '무엇을 준다고 정해 말하지는 않겠소.</p>'
         % (T["palace_lead"]["년주"], int(f.age), a["pillar"],
            a["gan_ten_god"], a["ji_ten_god"], stance_text, good, bad,
            a["inherited"])),
        1, sid="ancestor:%s:%s" % (a["gan_ten_god"], a["stance"])))

    # ── 8 · 성향 4글자 대조 (입력했을 때만) ───────────────
    #
    # ★ 훅과 같은 규칙을 씁니다 — 겹친 자리를 먼저, 깊은 해석은
    #   셋 이상 어긋난 사람에게만. (engine/bank.axis_compare)
    cmp = bank_mod.axis_compare(f, axis4)
    if cmp["usable"]:
        note = ('<p class="sm">여덟 자는 바뀌지 않소. 그대가 적은 넉 자는 '
                '다시 재면 달라지기도 하오 — 그건 그 검사의 성질이오.</p>')
        cuts.append(_cut(
            "axis", "7 · 겹친 자리와 어긋난 자리",
            _why.line("사주 %s ↔ 입력 %s"
                      % (bank_mod.axis_string(f), axis4.upper()),
                      "대조", ""),
            ('<p class="tale">여덟 글자에서 나온 넉 자는 <b>%s</b>. '
             '그대가 적은 건 <b>%s</b>.</p>%s%s'
             % (bank_mod.axis_string(f), axis4.upper(),
                bank_mod.axis_block(cmp, f.strength), note)),
            2, sid=bank_mod.axis_sid(cmp, f.strength)))

    else:
        # ── 7 대체 · 물은 자리와 글자가 센 자리 ───────────
        #
        # ★ 이 컷이 넉 자를 안 적은 사람에게는 **아예 안 생겼습니다.**
        #   재보니 45.1%입니다. 그것도 15,900원 이상에서만 열리는
        #   자리라, **값을 치른 사람이 잃고 있었습니다.**
        #   훅 2.5단은 대체 단을 넣어 메웠는데 리포트는 그대로였습니다.
        #
        # ★ 같은 자리(id "axis")에 넣습니다. 그래야 값 사다리가
        #   여는 층이 비지 않습니다. 손님이 낸 것이 하나 더 있습니다 —
        #   **고민**입니다. 물으러 온 자리와 글자가 센 자리를 맞붙입니다.
        grp = bank_mod.concern_group(concern, f.sex)
        asked = getattr(f, bank_mod.GROUP_TOTAL[grp])
        loud = f.flow
        row = bank_mod.bank()["CONCERN_AXIS"][concern]
        word = row["w"]
        B2 = bank_mod.bank()

        lead = ('<p class="tale">%s 물으러 오신 자리는 <b>%s</b>이오. '
                '여덟 글자에서는 <b>%s</b>으로 보오 — 그대의 %s은 <b>%d</b>이오. '
                '글자가 가장 센 자리는 <b>%s</b>이오.</p>'
                % (you, word, grp, grp, asked, loud))
        if asked == 0:
            body = lead + '<p class="tale">%s</p>' % (B2["CONCERN_EMPTY"] % grp)
        elif grp == loud:
            body = lead + '<p class="tale">%s</p>' % B2["CONCERN_SAME"][grp]
        else:
            body = (lead
                    + '<p class="tale">헌데 %s</p>' % B2["CONCERN_ELSE"][loud]
                    + '<p class="tale">%s</p>' % B2["WHY_TAIL"][loud])
        body += ('<p class="tale">%s</p>' % B2["MATCH_TAIL"][f.strength])
        body += ('<p class="sm">넉 자를 적으셨으면 이 자리에 '
                 '<b>사주와 검사가 어긋난 데</b>를 놓았을 것이오. '
                 '안 적으셨으니 그대가 낸 것으로 대신 보았소.</p>')

        cuts.append(_cut(
            "axis", "7 · 물은 자리와 센 자리",
            # 훅 2.5단과 **같은 말꼴**로 냅니다 — 「관성 3」이 아니라
            # 「관성이 셋」. 표가 아니라 말이라야 근거로 읽힙니다.
            _why.line("%s → %s %s · 가장 센 자리 %s · %s"
                      % (word, josa(grp, "이", "가"), count_word(asked),
                         loud, f.strength), grp, "십신"),
            body, 2,
            sid="rcax:%s:%s:%d:%s:%s"
                % (concern, grp, min(asked, 4), loud, f.strength)))

    # ── 9 · 이 캐릭터가 따로 받는 것 ──────────────────────
    #
    # ★ 여기가 두 번째 결제를 진짜 다른 상품으로 만드는 자리입니다.
    #   여덟 글자는 하나뿐이라, 이 컷이 없으면 캐릭터를 바꿔도 순서만
    #   바뀝니다. (engine/lens.py §결합 축)
    #
    # ★ 여기서 터져도 리포트 전체를 죽이지 않습니다.
    #   추가 입력은 **컷 하나**를 여는 선택 입력입니다. 상대 생년월일 하나가
    #   틀렸다고 값을 치른 사람의 명식·용신·대운까지 못 보게 할 이유가
    #   없습니다. 그 컷만 접고 무엇이 틀렸는지 말해 줍니다.
    #   (1만 명 시험에서 이 자리가 422 로 리포트를 통째로 막고 있었습니다)
    # ── 9a · 이 캐릭터만 보는 자리 (관점 컷) ────────────────
    #
    # ★ 값이 캐릭터마다 다른데 받는 것이 값을 안 따라가고 있었습니다.
    #   1만 명 시험에서 값 ↔ 컷수 상관 −0.419 — 4,900원짜리가
    #   19,900원짜리보다 더 줬습니다. 자기 몫 컷을 여기서 채웁니다.
    for lc in lens_cuts_mod.build(f, lens_id):
        cuts.append(_cut(lc["id"], lc["title"], lc["source"], lc["html"],
                         lc["min_level"], sid=lc["statement_id"]))

    need = lens_mod.required_input(lens_id) if lens_id else None
    extra_error = None
    try:
        extra = extras_mod.build(f, need, extras)
    except extras_mod.ExtraInputError as e:
        extra, extra_error = None, str(e)
    if extra:
        cuts.append(_cut(extra["id"], extra["title"], extra["source"],
                         extra["html"], extra["min_level"],
                         sid=extra["statement_id"]))

    # ── 9b · 이번 주 한 가지 ──────────────────────────────
    #
    # ★ 쓸모 있는 것이 옮겨집니다(Berger, 실용가치). 그런데 이 리포트는
    #   '필요한 건 쇠요' 로 끝나고 있었습니다 — 내일 무엇을 하라는 말이
    #   아닙니다. 다과상이 유일하게 실행 가능한 자리였는데 곁가지였습니다.
    #
    # ★ **셀 수 있는 한 가지**여야 합니다. '기운을 채우시오' 는 실행이
    #   아닙니다. 다음에 왔을 때 했는지 물어볼 수 있어야 회고가 됩니다.
    #
    # ★ 무료입니다. 값을 치르지 않은 사람도 손에 쥐고 나가야 다시 옵니다.
    #
    # ★ 축 셋을 곱합니다. 용신(5) × 계절(4) 둘로 뒀더니 한 문장이 9.4%를
    #   먹었습니다 — 20가지가 상한이라 문장을 더 써도 안 늘어납니다.
    #   셋째는 **고른 축**인 일간(최다 10.7%)이고, 앞의 둘과 서로
    #   무관합니다. (docs/18 §3 이 이미 적어 둔 자리입니다)
    season = bank_mod.born_season(f)
    cuts.append(_cut(
        "week", "이번 주 한 가지",
        _why.line("%s · %s생 · %s일간"
                  % (element_word(f.yongsin), season, f.day_gan),
                  "용신", "용신"),
        ('<p class="tale">%s</p><p class="tale">%s</p>'
         '<p class="tale">%s</p>'
         '<p class="sm">다음에 오시거든 <b>했는지만</b> 말해 주시오. '
         '했는지 안 했는지 셀 수 없는 말은 처방이 아니라 덕담이오.</p>'
         % (B["WEEK_DO"][f.yongsin][season], B["WEEK_WHY"][f.yongsin],
            B["WEEK_HOW"][f.day_gan])),
        0, sid="week:%s:%s:%s" % (f.yongsin, season, f.day_gan)))

    # ── 10 · 덮는 말 ─────────────────────────────────────
    #
    # ★ 끝이 설계돼 있지 않았습니다.
    #   기억은 **가장 센 순간과 마지막**이 지배하고 길이는 무시됩니다
    #   (Kahneman, peak-end). 그런데 apply_view 가 정렬하면 맨 뒤에 오는 것이
    #   그 캐릭터가 **덜 본다고 미뤄 둔 컷**(mute) 이었습니다. 가장 안 중요한
    #   말로 끝나고 있었습니다. 컷을 아무리 늘려도 이 구조면 기억에 안 남습니다.
    #
    # ★ 그래서 마지막 한 컷을 **자리로 고정**합니다 (apply_view 의 정렬 키).
    #   여는 말·닫는 말은 이미 있으나 한 줄짜리라 끝의 무게를 못 집니다.
    #
    # ★ 새 점사를 하지 않습니다. 오늘 한 말을 **되짚고 닫습니다** —
    #   무엇을 보았는지, 무엇은 안 보았는지.
    B_ = bank_mod.bank()
    close_bits = [
        '<p class="tale">오늘 본 것은 <b>%s</b> 여덟 글자 하나요. '
        '거기서 <b>%s</b> 세고, <b>%s</b> 짚었소.</p>'
        % (" ".join(p["gz"] for p in f.pillars),
           josa(element_word(weak), "을", "를"), josa(top, "을", "를")),
        '<p class="tale">%s</p>' % B_["CLOSE_KEEP"][f.strength],
        # ★ 기억은 마지막이 지배하는데, 그 마지막이 셀 수 있는 것을
        #   하나도 안 담고 있었습니다. 다음에 무엇이 바뀌는지 못 박습니다 —
        #   나이는 틀릴 수 있는 말이고, 그래서 맞으면 남습니다.
        _close_turn(f),
        '<p class="sm">여덟 자는 안 바뀌오. 바뀌는 것은 <b>쓰는 법</b>과 '
        '<b>때</b>요. 오늘 못 본 것도 적어 두겠소 — '
        '그대가 겪은 일, 곁의 사람, 그대가 고른 것. '
        '그건 글자에 없소.</p>',
    ]
    cuts.append(_cut(
        "closing_cut", "덮으며", _why.line("여덟 글자 하나", "명식", ""),
        "".join(close_bits), 0,
        sid="close:%s:%s" % (f.strength, weak)))

    return cuts, extra_error


def _close_turn(f) -> str:
    """
    덮으며 — **다음에 바뀌는 때**를 못 박는다.

    ★ 마지막 컷이 셀 수 있는 것을 하나도 안 담고 있었습니다.
      기억은 마지막이 지배하는데, 거기가 틀릴 수 없는 말로 닫히면
      아무것도 안 남습니다. 대운수는 절입까지의 실제 일수로 이미
      정확히 세어 뒀습니다 — 안 쓰고 있었을 뿐입니다.

    ★ 그 해에 무슨 일이 생긴다고는 말하지 않습니다. **바뀌는 때만** 셉니다.
    """
    nxt = f.daeun_now + 1
    if nxt >= len(f.daeun):
        return ('<p class="cnt"><b>지금 %d살, 마지막 대운이오.</b> '
                '더 바뀔 칸은 없소.</p>' % int(f.age))
    age = int(f.daeun[nxt]["start_age"])
    left = max(0, age - int(f.age))
    if left == 0:
        return ('<p class="cnt"><b>올해 %d살, 대운이 바로 지금 바뀌오.</b></p>'
                % int(f.age))
    return ('<p class="cnt"><b>지금 %d살. 다음 대운은 %d살 — %d해 뒤요.</b> '
            '그때 무슨 일이 생긴다는 말이 아니라, 읽는 자리가 바뀐다는 말이오.</p>'
            % (int(f.age), age, left))


def _lens_price(lens_id: Optional[str]) -> int:
    """캐릭터 값. 모르면 0 — 없는 값으로 층을 열지 않습니다."""
    if not lens_id:
        return 0
    try:
        return int(lens_mod.get(lens_id).get("price") or 0)
    except lens_mod.LensError:
        return 0


def report_id(chart_id: str, lens_id: str, tier: str, concern: str) -> str:
    raw = "|".join([chart_id, lens_id, tier, concern])
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def apply_view(cuts: list, view: dict) -> list:
    """
    캐릭터의 관점을 얹는다 — **순서와 어조만**.

    ★ 근거는 건드리지 않습니다. 여덟 글자는 하나입니다.
      같은 사람을 다르게 읽는 것이지 다른 사주를 만드는 게 아닙니다.

      lead  맨 앞으로 (그 사람이 '먼저 보는 것')
      mute  뒤로 (덜 보는 것 — 지우지는 않습니다)
      notes 그 컷에 그 사람의 한 마디를 덧붙임

    명식(chart)은 셈의 근거라 늘 맨 앞입니다. 일관만 이걸 lead 로
    삼는데, 그 사람은 셈 자체를 보는 사람이라 뜻이 맞습니다.
    """
    lead = view.get("lead")
    mute = set(view.get("mute") or ())
    notes = view.get("notes") or {}

    out = []
    for c in cuts:
        c = dict(c)
        note = notes.get(c["id"])
        if note:
            c["html"] = c["html"] + (
                '<p class="lensnote">%s</p>' % guard.enforce(note, {"cut": c["id"]}))
            c["lens_note"] = True
        out.append(c)

    def key(c):
        if c["id"] == "chart":
            return (0, 0)            # 셈의 근거는 늘 먼저
        # ★ 끝은 자리로 고정합니다. 캐릭터가 무엇을 미뤄 두든 마지막 말은
        #   이것입니다 — 기억은 마지막이 지배하기 때문입니다(peak-end).
        if c["id"] == "closing_cut":
            return (4, 0)
        if c["id"] == lead:
            return (1, 0)
        # ★ 그 캐릭터만 보는 자리는 앞쪽에 둡니다. 값을 치르고 이 사람을
        #   고른 까닭이 이 컷이라, 뒤에 묻히면 고른 뜻이 없어집니다.
        if c["id"].startswith("lc_"):
            return (1, 1)
        if c["id"] in mute:
            return (3, 0)
        return (2, 0)

    return sorted(out, key=key)


def _visible(f, el: str) -> int:
    """
    여덟 글자 **겉에 보이는** 그 기운의 개수.

    ★ `f.elements` 와 다릅니다. 저건 지장간까지 가중치를 매겨 더한
      점수라 손님이 확인할 수 없습니다. 이건 손님이 만세력을 펴고
      **직접 세면 같은 수가 나오는** 값입니다.

      틀릴 수 있는 말이라야 근거입니다 — 손님이 세어 보고 다르면
      우리가 진 것입니다. 그 자리를 남겨 둡니다.
    """
    from .constants import ELEMENT_OF_GAN, ELEMENT_OF_JI
    n = 0
    for p in f.pillars:
        if ELEMENT_OF_GAN.get(p["gan"]) == el:
            n += 1
        if ELEMENT_OF_JI.get(p["ji"]) == el:
            n += 1
    return n


def _how_many(f, el: str) -> str:
    """센 것을 말로. 0은 「하나도 없소」 — 「없음 자」 는 말이 아니오."""
    n = _visible(f, el)
    # 「넷 자요」 는 말이 아니오. 수사는 그대로 두고 세는 말은 뺍니다.
    return "하나도 없소" if n == 0 else "%s이오" % count_word(n)


def build_report(f, chart_id: str, lens_id: str, tier: str, concern: str,
                 axis4: Optional[str] = None,
                 extras: Optional[dict] = None,
                 name: str = "") -> dict:
    """
    tier 별 잠금 차등. 잠긴 컷은 **본문을 내려보내지 않습니다.**
    제목과 근거만 보여 무엇이 잠겼는지 알 수 있게 합니다.

    ★ 캐릭터마다 순서와 어조가 다릅니다 (engine/lens.view).
      전에는 렌즈가 이름·색만 바꾸고 본문은 20명이 똑같았습니다.
    """
    if tier not in TIERS:
        raise ValueError("모르는 tier: %r" % (tier,))
    level = TIER_LEVEL[tier]
    view = lens_mod.view(lens_id)
    # ★ 부르는 말은 캐릭터마다 다르고, 어떤 캐릭터는 **손님 이름**으로
    #   부릅니다. 이름을 안 적었으면 그 캐릭터의 대신 부르는 말로
    #   물러섭니다 — 「이름」이라고 부르지 않습니다.
    you = lens_mod.you_of(lens_id, name, getattr(f, "sex", None))

    # 「이 자리 하나」는 캐릭터 값으로 받으므로 값이 층을 엽니다.
    # 다른 티어는 값이 하나뿐이라 층이 없습니다.
    opened = rungs_at(_lens_price(lens_id)) if tier == "one" else set()

    # ★ 값이 없는 캐릭터는 **이 자리에서 팔지 않습니다.**
    #
    #   청동자는 브레이크입니다 — 무거운 리포트 뒤에 강제로 붙는
    #   안전망이고(relay.FALLBACK_LENS · forced), 값이 붙어 있지 않습니다.
    #   그런데 그 자리에 잠긴 컷 여섯이 서 있었고, 「이 자리 하나」 목패는
    #   값이 없어 안 뜨니 **살 수 있는 것이 9,900원/월뿐**이었습니다.
    #   방금 무거운 것을 읽고 온 사람에게 그 자리에서 파는 셈입니다.
    #
    #   여기서는 잠긴 것을 **내보이지 않습니다.** 열리는 만큼만 주고,
    #   무엇이 더 있다고 말하지 않습니다. 브레이크는 매출보다 앞섭니다.
    sells = _lens_price(lens_id) > 0

    cuts, locked = [], []
    all_cuts, extra_error = _all_cuts(f, concern, you, axis4, lens_id, extras)
    for c in all_cuts:
        if c["min_level"] <= level or c["id"] in opened:
            cuts.append({k: v for k, v in c.items() if k != "min_level"})
        else:
            # ★ 본문은 여전히 안 내려갑니다. 첫 줄만, 그것도 잘라서.
            #   무엇이 잠겼는지 알 수 있어야 값을 치를지 정할 수 있습니다.
            #   분량도 같이 냅니다 — '컷' 은 손님의 말이 아닙니다.
            body_len = len(_plain(c["html"]))
            locked.append({"id": c["id"], "title": c["title"],
                           "source": c["source"],
                           "teaser": _teaser(c["html"]),
                           "chars": body_len,
                           "need_tier": "one" if c["min_level"] == 1 else "all"})

    # 안 파는 자리에서는 잠긴 목록을 안 냅니다 — 값을 권하지 않습니다.
    if not sells:
        locked = []

    cuts = apply_view(cuts, view)

    # ★ 마지막에 말투를 입힙니다.
    #
    #   뱅크는 하오체 한 벌로 둡니다. 스무 벌로 쓰지 않습니다.
    #   여기서 **문장 끝 어미만** 갈아 끼우면 공통 컷(리포트의 60~90%)까지
    #   그 사람 목소리로 나갑니다.
    #
    #   전에는 스무 명이 전부 하오체였습니다. 관점은 스무 개 다 다른데
    #   (여는 말 20/20) 목소리가 하나라, 두 사람을 이어 읽으면 중앙값
    #   56%가 글자 그대로 같은 글로 읽혔습니다.
    #
    #   ★ 근거 줄(source)은 안 건드립니다. 근거는 캐릭터가 바꾸지
    #     않습니다 — 여덟 글자는 하나입니다.
    # ★ 어려운 말을 **리포트 한 장에 한 번씩** 풉니다.
    #
    #   재보니 어려운 말 41가지 중 40가지가 풀이 없이 나오고 있었습니다.
    #   「상관」이 무엇인지 아는 손님은 거의 없습니다. 이 집은 근거 대는
    #   집인데, 근거를 모르는 말로 대면 그건 근거가 아니라 주문입니다.
    #
    #   `seen` 을 컷들이 나눠 씁니다 — 한 장 안에서 같은 말을 열 번
    #   풀면 읽기를 방해합니다. 처음 만나는 자리에서만 답니다.
    # ★ 뜻만 바꿔 말한 것은 푼 게 아닙니다.
    #
    #   괄호는 「상관(밖으로 내지르는 힘)」 처럼 **뜻**을 답니다. 그런데
    #   재보니 쉰넷 중 그림이 그려지는 것은 둘뿐이었습니다 — 모르는
    #   말을 모르는 말로 바꾼 셈이라 손님은 읽고도 여전히 모릅니다.
    #
    #   그래서 그 말이 **처음 나온 컷 밑에** 비유를 한 줄 답니다.
    #   리포트 끝에 몰아 두지 않습니다 — 모르는 말을 만난 그 자리에
    #   있어야 봅니다.
    seen: set = set()
    tone = view.get("voice")
    for c in cuts:
        before = set(seen)
        c["html"] = terms_mod.gloss(
            voice_mod.speak(voice_mod.address(c["html"], you), tone), seen)
        # ★ 비유 상자도 **그 사람 목소리로** 말해야 합니다.
        #
        #   처음엔 말투를 갈아 끼운 **뒤에** 붙였습니다. 그랬더니
        #   합쇼체 캐릭터의 리포트에서 이 줄만 하오체로 남아, 한 화면
        #   안에서 말투가 갈렸습니다 — 스무 명에서 464군데였습니다
        #   (tests/test_voice.py 가 잡았습니다). 같은 층을 태웁니다.
        c["html"] += voice_mod.speak(
            voice_mod.address(terms_mod.picture_box(seen - before), you),
            tone)
    for l in locked:
        if l.get("teaser"):
            # 맛보기도 손님이 읽는 글입니다. 같은 층을 태웁니다.
            # ★ seen 을 나눠 쓰지 않습니다 — 페이월은 본문과 따로
            #   읽히는 자리라, 거기서 처음 만나는 말이면 풀어 줘야 합니다.
            l["teaser"] = terms_mod.gloss(voice_mod.speak(
                voice_mod.address(l["teaser"], you), tone))

    # 이 캐릭터가 더 받아야 하는 것. 안 받았으면 화면이 물어볼 수 있게
    # 알려 줍니다. **무엇을 받는지만** 내려보내고 문장은 안 보냅니다.
    need = lens_mod.required_input(lens_id)
    needs_input = None
    if need and need in extras_mod.BUILDERS and not (extras or {}).get(need):
        needs_input = need

    return {
        "report_id": report_id(chart_id, lens_id, tier, concern),
        "chart_id": chart_id,
        "lens": lens_mod.public(lens_id),
        "tier": tier,
        "concern": concern,
        "needs_input": needs_input,
        # 이 자리에서 값을 권해도 되는가. 값이 없는 캐릭터(브레이크)는 거짓.
        "sells": sells,
        # 추가 입력이 틀렸을 때. 그 컷만 접고 나머지는 그대로 내려갑니다.
        "extra_error": extra_error,
        "opening": (guard.enforce(voice_mod.speak(view["open"], view.get("voice")),
                                  {"cut": "open"}) if view.get("open") else None),
        "closing": (guard.enforce(voice_mod.speak(view["close"], view.get("voice")),
                                  {"cut": "close"}) if view.get("close") else None),
        "cuts": cuts,
        "locked": locked,
    }
