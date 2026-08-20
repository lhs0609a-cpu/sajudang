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
from . import guard
from . import lens as lens_mod
from .bank import element_word, josa
from .constants import ELEMENT_OF_GAN

TIERS = ("free", "one", "all", "sub")
TIER_LEVEL = {"free": 0, "one": 1, "all": 2, "sub": 2}


def _cut(cid, title, source, body, min_level, sid=None):
    return {
        "id": cid,
        "title": title,
        "source": source,
        "html": guard.enforce(body, {"cut": cid}),
        "min_level": min_level,
        "statement_id": sid,
    }


def _all_cuts(f, concern: str, you: str, axis4: Optional[str]) -> list:
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
        "chart", "명식", "여덟 글자" if f.hour_known else "여섯 글자",
        ('<div class="pillars">%s</div><div class="calc">%s</div>%s'
         % ("".join('<div class="p"><span class="lb">%s</span><b>%s</b></div>'
                    % (p["label"], p["gz"]) for p in f.pillars),
            "".join('<div class="r"><span class="k">%s</span>'
                    '<span class="v">%s</span></div>' % kv for kv in rows),
            ('<p class="note">%s</p>' % c["boundary_note"])
            if c["boundary_note"] else "")),
        0))

    # ── 2 · 없는 것부터 ──────────────────────────────────
    cuts.append(_cut(
        "lack", "1 · 없는 것부터",
        "%s %s" % (element_word(weak), f.elements[weak]),
        ('<p class="tale">눈에 띄는 건 %s %s인 게 아니오. '
         '<b>%s %s밖에 없는 것</b>이지.</p>'
         '<p class="tale">%s <b>%s</b>이오. 그게 없이 살아온 것이오.</p>'
         % (josa(element_word(strong), "이", "가"), f.elements[strong],
            josa(element_word(weak), "이", "가"), f.elements[weak],
            josa(element_word(weak), "은", "는"), lack["w"])),
        0, sid="lack:%s" % weak))

    # ── 3 · 왜 반복되나 ──────────────────────────────────
    st_line = {
        "신강": "게다가 신강이오. 쏟을 힘은 넘치는데 받을 그릇이 없지.",
        "신약": "게다가 신약이오. 채워야 하는데 채울 그릇도 없소.",
        "중화": "중화라 크게 티는 안 났을 게요. 그래서 더 오래 몰랐지.",
    }[f.strength]
    cuts.append(_cut(
        "why", "2 · 왜 반복되나",
        "%s %d · %s" % (top, f.ten_gods[top], f.strength),
        ('<p class="tale">%s. 그리고 %s.</p><p class="tale">%s</p>'
         '<p class="tale">그래서 끝에서 <b>%s</b>.</p>'
         % (bank_mod._pick("IGNITE", top, concern), patt["b"], st_line,
            bank_mod._pick("BLAME", top, f.strength))),
        0, sid="why:%s:%s:%s" % (top, concern, f.strength)))

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
    cuts.append(_cut(
        "place", "3 · 어느 자리에서",
        "일지 %s%s" % (f.day_ji, " 충" if f.ilji_chung else ""),
        '<p class="tale">%s</p><p class="tale">%s</p>' % (place, lean),
        0, sid="place:%s:%s" % (f.day_ji, "chung" if f.ilji_chung else "-")))

    # ── 5 · 지금 어디에 (대운) ───────────────────────────
    heavy = daeun["ten_god"] in ("편관", "상관", "겁재")
    cuts.append(_cut(
        "daeun_now", "4 · 지금 어디에",
        "대운 %s · %s" % (daeun["gz"], f.daeun_ten_god),
        ('<p class="tale">지금은 <b>%s</b> 대운이오. %d세부터.</p>'
         '<p class="tale">이 구간의 성격은 <b>%s</b>. %s</p>'
         % (daeun["gz"], daeun["start_age"], f.daeun_ten_god,
            "조용히 지나가지 않는 구간이오." if heavy
            else "크게 흔들리진 않소. 다지는 구간이지.")),
        1, sid="daeun:%s" % f.daeun_ten_god))

    # ── 6 · 필요한 것 (용신 + 다과상) ────────────────────
    tea = bank_mod.tea(f)
    cuts.append(_cut(
        "yongsin", "5 · 필요한 것", "용신 %s" % f.yongsin,
        ('<p class="tale">그대에게 필요한 건 <b>%s</b>이오.</p>'
         '<p class="tale">%s 사람에게서 그걸 구하면 그 사람이 지치오. '
         '<b>먼저 그대 안에 두시오.</b></p>'
         '<div class="tea"><b>%s</b><p>%s</p></div>'
         % (element_word(f.yongsin),
            "남는 힘을 빼내 방향을 잡아줄 것." if f.strength == "신강"
            else "모자란 힘을 채워줄 것.",
            tea["name"], tea["text"])),
        1, sid="yongsin:%s:%s" % (f.yongsin, f.strength)))

    # ── 7 · 대운 맵 ─────────────────────────────────────
    cuts.append(_cut(
        "daeun_map", "6 · 대운 맵",
        "대운수 %d · %s" % (f.daeun[0]["start_age"],
                          "순행" if f.daeun[1]["start_age"] > f.daeun[0]["start_age"] else "역행"),
        ('<div class="dmap">%s</div>'
         '<p class="note">대운수는 절입일까지의 실제 일수 ÷ 3 으로 셈했소.</p>'
         % "".join(
             '<div class="d%s"><span class="age">%d</span>'
             '<b>%s</b><span class="tg">%s</span></div>'
             % (" now" if d["index"] == f.daeun_now else "",
                d["start_age"], d["gz"], d["ten_god"])
             for d in f.daeun)),
        2))

    # ── 8 · 성향 4글자 대조 (입력했을 때만) ───────────────
    gaps = bank_mod.gap_list(f, axis4)
    if axis4:
        if gaps:
            body = ('<p class="tale">여덟 글자에서 나온 넉 자는 <b>%s</b>. '
                    '그대가 적은 건 <b>%s</b>. %d군데 어긋나오.</p>%s'
                    % (bank_mod.axis_string(f), axis4.upper(), len(gaps),
                       "".join('<p class="gp"><b>%s → %s</b><br>%s<br>'
                               '<span class="w">%s</span></p>'
                               % (g["from"], g["to"], g["t"], g["w"])
                               for g in gaps)))
        else:
            body = ('<p class="tale">여덟 글자에서 나온 넉 자와 그대가 적은 넉 자가 '
                    '<b>%s</b> 로 같소. 흔치 않은 일이오.</p>'
                    % bank_mod.axis_string(f))
        cuts.append(_cut(
            "axis", "7 · 어긋난 자리",
            "사주 %s ↔ 입력 %s" % (bank_mod.axis_string(f), axis4.upper()),
            body, 2,
            sid="gap:%s" % ",".join(g["pair"] for g in gaps) if gaps else "gap:none"))

    return cuts


def report_id(chart_id: str, lens_id: str, tier: str, concern: str) -> str:
    raw = "|".join([chart_id, lens_id, tier, concern])
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def build_report(f, chart_id: str, lens_id: str, tier: str, concern: str,
                 axis4: Optional[str] = None) -> dict:
    """
    tier 별 잠금 차등. 잠긴 컷은 **본문을 내려보내지 않습니다.**
    제목과 근거만 보여 무엇이 잠겼는지 알 수 있게 합니다.
    """
    if tier not in TIERS:
        raise ValueError("모르는 tier: %r" % (tier,))
    level = TIER_LEVEL[tier]
    you = lens_mod.you_word(lens_id)

    cuts, locked = [], []
    for c in _all_cuts(f, concern, you, axis4):
        if c["min_level"] <= level:
            cuts.append({k: v for k, v in c.items() if k != "min_level"})
        else:
            locked.append({"id": c["id"], "title": c["title"],
                           "source": c["source"],
                           "need_tier": "one" if c["min_level"] == 1 else "all"})

    return {
        "report_id": report_id(chart_id, lens_id, tier, concern),
        "chart_id": chart_id,
        "lens": lens_mod.public(lens_id),
        "tier": tier,
        "concern": concern,
        "cuts": cuts,
        "locked": locked,
    }
