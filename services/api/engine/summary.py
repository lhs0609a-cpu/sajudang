"""
종합 분석지 — 다 읽고 나서 한 장으로 받아보는 것.

★ 여기서도 새 점사 문장을 지어내지 않습니다.
  뱅크·신살표·Feature 에서만 조립합니다.

★ 공유용 payload 에는 **생년월일시·도시·보정 시각을 넣지 않습니다.**
  여덟 글자는 넣되(사주 문화상 명식 공유는 통상적), 그 외 개인정보는
  링크를 받은 사람에게 넘어가지 않습니다. (docs/11 §10)
"""
from __future__ import annotations

from typing import Optional

from . import bank as bank_mod
from . import guard
from . import lens as lens_mod
from . import rarity as rarity_mod
from .bank import element_word, josa
from .constants import ELEMENT_OF_GAN

ILGAN_ONE = {
    "甲": "방향을 정하면 되돌리지 않는 사람",
    "乙": "벽을 만나면 타고 오르는 사람",
    "丙": "숨기려 해도 표면으로 올라오는 사람",
    "丁": "넓게 대신 깊이 비추는 사람",
    "戊": "먼저 나서지 않고 끝까지 남는 사람",
    "己": "맡으면 결국 자라게 하는 사람",
    "庚": "애매한 상태를 못 견디는 사람",
    "辛": "남들이 넘기는 1mm가 보이는 사람",
    "壬": "흐르고 있을 때 가장 자기다운 사람",
    "癸": "알아챘을 땐 이미 안에 있는 사람",
}
ILGAN_NAME = {
    "甲": "거목의 수호기사", "乙": "덩굴의 책사", "丙": "태양의 성기사",
    "丁": "촛불의 마도사", "戊": "산의 방패병", "己": "대지의 정원사",
    "庚": "강철의 검사", "辛": "보석 세공사", "壬": "대양의 항해자",
    "癸": "빗물의 점성술사",
}


def headline(f) -> str:
    """한 줄 정의 — 카드 맨 위에 박히는 문장."""
    return ILGAN_ONE[f.day_gan]


def name_word(f) -> str:
    """
    훅 3단이 건네는 **이름** 한 마디. 카드의 주인공입니다.

    ★ 사람이 가장 오래 기억하는 한 줄이고, 남에게 옮길 때도 이 말이
      옮겨집니다. 훅과 카드가 **다른 이름**을 쓰면 안 되므로 여기서
      새로 만들지 않고 같은 표를 봅니다.
    """
    B = bank_mod.bank()
    return B["NAME2"].get(f.weak_el, {}).get(f.flow) or B["NAMEW"][f.weak_el]


def rarity_bit(f, reveal: str = "full") -> dict:
    """
    카드에 박을 희소도. 세는 값이라 지어낸 것이 아닙니다.

    ★ light 에는 일주 글자를 담지 않습니다. 여덟 글자를 감추기로 한
      공유에서 일주만 흘리면 감춘 뜻이 반쯤 없어집니다.
    """
    r = rarity_mod.look(f)
    out = {"words": r["words"], "band": r["band"], "sample": r["sample"]}
    if reveal == "full":
        out["ilju"] = {"gz": r["ilju"]["gz"], "words": r["ilju"]["words"]}
    return out


def three_lines(f, concern: str) -> list:
    """
    공유용 핵심 3줄. 뱅크에서 그대로 가져온다.
      ① 무엇이 없는가        RESULT[약오행]
      ② 힘이 어디로 나가는가   FLOW[흐름]
      ③ 그래서 붙는 이름      NAME2[약오행][흐름]
    """
    B = bank_mod.bank()
    rs = B["RESULT"][f.weak_el]
    fl = B["FLOW"][f.flow]
    name = B["NAME2"].get(f.weak_el, {}).get(f.flow) or B["NAMEW"][f.weak_el]
    return [
        "%s %s밖에 없소. %s." % (element_word(f.weak_el),
                              f.elements[f.weak_el], rs["t"]),
        "힘은 %s 쪽으로 나가오. %s." % (f.flow, fl["t"].rstrip(",")),
        name,
    ]


def _sec(sid, title, source, html):
    return {"id": sid, "title": title, "source": source,
            "html": guard.enforce(html, {"summary": sid})}


def build_summary(chart, f, concern: str = "love",
                  axis4: Optional[str] = None,
                  lens_id: str = "pungun",
                  display_name: str = "") -> dict:
    """분석지 한 장. 화면·공유·PDF 가 전부 이걸 씁니다."""
    lens = lens_mod.public(lens_id)
    lines = three_lines(f, concern)
    secs = []

    # ① 여덟 글자
    secs.append(_sec(
        "pillars", "여덟 글자",
        "%s일간 · %s" % (f.day_gan, f.strength),
        '<div class="pillars">%s</div>%s' % (
            "".join('<div class="p"><span class="lb">%s</span><b>%s</b></div>'
                    % (p["label"], p["gz"]) for p in f.pillars),
            "" if f.hour_known else
            '<p class="sm">때를 모르셔서 세 기둥으로 셈했소. 시주는 비워 두었소.</p>')))

    # ② 저울 — 오행
    order = sorted(f.elements.items(), key=lambda x: -x[1])
    secs.append(_sec(
        "balance", "저울",
        "가장 강한 것 %s · 가장 약한 것 %s"
        % (element_word(f.strong_el), " · ".join(element_word(x) for x in f.weak_els)),
        '<div class="scale">%s</div><p class="tale">%s</p>' % (
            "".join('<div><span class="k">%s</span><i style="--w:%d%%"></i>'
                    '<span class="v">%s</span></div>'
                    % (element_word(k), min(100, int(v / max(1.0, order[0][1]) * 100)), v)
                    for k, v in order),
            "%s %s밖에 없는 것이 이 사주의 중심이오."
            % (josa(element_word(f.weak_el), "이", "가"), f.elements[f.weak_el]))))

    # ③ 순서 — 훅 2단을 그대로
    hook = bank_mod.build_hook(f, concern, axis4,
                              you=lens_mod.you_word(lens_id))
    seq = next((s for s in hook if s["stage"] == "2"), None)
    if seq:
        secs.append(_sec("sequence", "늘 이 순서요", seq["source"], seq["html"]))

    # ④ 지금 어디에 — 대운
    d = f.daeun[f.daeun_now]
    lead = ("지금은 <b>%s</b> 대운이오. %d세부터." % (d["gz"], d["start_age"])
            if f.daeun_started else
            "아직 첫 대운에 들지 않았소. <b>%s</b> 대운은 %d세부터요."
            % (d["gz"], d["start_age"]))
    secs.append(_sec(
        "when", "지금 어디에",
        "대운 %s · %s · %s" % (d["gz"], f.daeun_ten_god,
                             "순행" if f.forward else "역행"),
        '<p class="tale">%s</p><div class="dmap">%s</div>' % (
            lead,
            "".join('<div class="d%s"><span class="age">%d</span><b>%s</b>'
                    '<span class="tg">%s</span></div>'
                    % (" now" if x["index"] == f.daeun_now else "",
                       x["start_age"], x["gz"], x["ten_god"])
                    for x in f.daeun))))

    # ⑤ 누가 돕는가 — 신살·궁위
    if f.helpers:
        seen, rows = [], []
        for h in f.helpers:
            if h["pillar"] in seen:
                continue
            seen.append(h["pillar"])
            names = [x["sinsal"] for x in f.helpers if x["pillar"] == h["pillar"]]
            rows.append('<div class="hp"><b>%s</b><span class="tag">%s</span>'
                        '<p class="sm">%s · %s</p></div>'
                        % (" · ".join(names), h["pillar"], h["who"], h["kind"]))
        body = "".join(rows)
    else:
        body = '<p class="tale">길신이 앉은 자리가 없소. 사람 손을 덜 타는 배치요.</p>'
    secs.append(_sec("helper", "누가 돕는가",
                     "신살 %d · 공망 %s" % (len(f.sinsal), f.gongmang), body))

    # ⑥ 뿌리 — 조상 자리
    a = f.ancestor
    secs.append(_sec(
        "root", "뿌리",
        "년주 %s · %s" % (a["pillar"], a["stance"]),
        '<p class="tale">년주 <b>%s</b> — 위는 %s, 아래는 %s요.</p>'
        '<p class="tale">물려받은 결이라 보던 것은 <b>%s</b> 쪽이오.</p>'
        % (a["pillar"], a["gan_ten_god"], a["ji_ten_god"], a["inherited"])))

    # ⑦ 필요한 것
    tea = bank_mod.tea(f)
    secs.append(_sec(
        "need", "필요한 것", "용신 %s" % f.yongsin,
        '<p class="tale">그대에게 필요한 건 <b>%s</b>요.</p>'
        '<div class="tea"><b>%s</b><p>%s</p></div>'
        % (element_word(f.yongsin), tea["name"], tea["text"])))

    return {
        "name": display_name or None,
        "lens": lens,
        "concern": concern,
        "day_gan": f.day_gan,
        "ilgan_name": ILGAN_NAME[f.day_gan],
        "element": ELEMENT_OF_GAN[f.day_gan],
        "headline": headline(f),
        # ★ 카드가 들고 나가는 두 가지 — 이름과 셈한 수.
        #   이름은 사람이 기억하는 한 줄이고, 수는 남에게 옮길 거리입니다.
        "name_word": name_word(f),
        "rarity": rarity_bit(f, "full"),
        "three_lines": lines,
        "strength": f.strength,
        "flow": f.flow,
        "weak_el": f.weak_el,
        "yongsin": f.yongsin,
        "pillars": f.pillars,
        "hour_known": f.hour_known,
        "sections": secs,
        "sinsal": [{"key": s["key"], "name": s["name"], "hanja": s["hanja"],
                    "kind": s["kind"], "at": s["at"]} for s in f.sinsal],
        "caveats": _caveats(f),
    }


def _caveats(f) -> list:
    """
    분석지 아래에 붙는 단서. 이걸 숨기면 '맞히는 집' 이 됩니다.
    """
    out = []
    if not f.hour_known:
        out.append("때를 몰라 세 기둥으로 셈했소. 시주가 들어가면 결과가 달라지오.")
    if f.top_ten_god_tied:
        out.append("주도 십신이 다른 것과 개수가 같았소. 월지에 뿌리를 둔 쪽으로 잡았소.")
    if len(f.weak_els) > 1:
        out.append("가장 약한 오행이 둘이오: %s."
                   % " · ".join(element_word(x) for x in f.weak_els))
    if f.correction.get("boundary_note"):
        out.append(f.correction["boundary_note"])
    out.append("이 글은 전통 명리 해석에 기반한 자기이해용이오. "
               "무엇이 일어난다고 말하지 않소.")
    return out


def share_payload(summary: dict, reveal: str = "full") -> dict:
    """
    공유 링크에 담을 것.

    reveal="full"  여덟 글자 + 해석 전부
    reveal="light" 일간과 핵심 3줄만

    ★ 어느 쪽이든 생년월일시·도시·보정 시각은 담지 않습니다.
      링크를 받은 사람이 원본 생일을 알 수 없어야 합니다.
    """
    base = {
        "headline": summary["headline"],
        # ★ 이름과 셈한 수는 light 에도 담습니다. 이 둘이 없으면 카드가
        #   '내 이야기' 가 아니라 그냥 사주 소개가 됩니다.
        "name_word": summary["name_word"],
        "rarity": {k: v for k, v in summary["rarity"].items()
                   if reveal == "full" or k != "ilju"},
        "three_lines": summary["three_lines"],
        "day_gan": summary["day_gan"],
        "ilgan_name": summary["ilgan_name"],
        "element": summary["element"],
        "strength": summary["strength"],
        "flow": summary["flow"],
        "weak_el": summary["weak_el"],
        "yongsin": summary["yongsin"],
        "lens": summary["lens"],
        "name": summary["name"],
        "reveal": reveal,
        "caveats": summary["caveats"],
    }
    if reveal == "full":
        base["pillars"] = summary["pillars"]
        base["hour_known"] = summary["hour_known"]
        base["sinsal"] = summary["sinsal"]
        base["sections"] = summary["sections"]
    return base
