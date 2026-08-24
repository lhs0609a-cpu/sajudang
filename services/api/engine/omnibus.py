"""
스무 사람 종합 — 한 명식을 스무 명이 각자 본 것을 한 권으로 묶는다.

왜 이게 있어야 하는가
    이 서비스의 한 줄은 "스무 명의 캐릭터가 같은 사주를 각자의 관점으로
    해석" 입니다. 그런데 사람은 한 자리에서 한 명씩만 만납니다. 스무 명을
    다 만나려면 릴레이를 열 번 넘게 돌아야 하고, 브레이크가 그걸 막습니다
    (세션당 2명). 그래서 **스무 관점을 한 번에 받아 보는 자리**가 필요합니다.

    이게 "여덟 글자 전부" 티어의 실체입니다. 컷 몇 개 더 여는 게 아니라
    스무 사람의 눈을 다 받는 것입니다.

무엇을 담는가
    ① 여덟 글자와 셈에 쓴 것            — 근거. 이게 먼저입니다.
    ② 스무 사람이 **한 목소리로** 짚는 것  — 겹치는 자리
    ③ 스무 사람이 **갈리는 자리**         — 안 겹치는 자리
    ④ 스무 사람 각각의 장                — 한 명씩, 제 관점으로
    ⑤ 안 한 말                        — 셈으로 알 수 없는 것

★ ②·③ 이 핵심입니다.
    스무 명이 다 같은 말을 하면 그건 그냥 한 명입니다. 겹치는 자리와
    갈리는 자리를 **세어서 보여주는 것**이 스무 명을 만나는 값입니다.
    "여덟 명이 같은 자리를 짚었다" 는 사실은 지어낸 게 아니라 센 것입니다.

★ 적중률이 아닙니다.
    "몇 명이 같은 자리를 짚었다" 는 우리 문장 뱅크 안에서의 겹침이지
    맞았다는 뜻이 아닙니다. 그렇게 읽히지 않게 문구를 답니다.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Optional

from . import guard
from . import lens as lens_mod
from . import report as report_mod
from . import summary as summary_mod

# 겹침을 셀 때 쓰는 자리. 컷 id 를 사람 말로 옮긴 것.
CUT_LABEL = {
    "chart": "여덟 글자",
    "lack": "없는 것",
    "why": "되풀이의 까닭",
    "place": "자리",
    "sinsal": "이름 붙은 자리",
    "helper": "곁에 서는 이",
    "ancestor": "뿌리",
    "daeun_now": "지금 서 있는 데",
    "daeun_map": "긴 길",
    "yongsin": "채울 것",
    "axis": "어긋난 자리",
}


def _plain(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", html or "")).strip()


def build_omnibus(f, chart_id: str, concern: str = "love",
                  axis4: Optional[str] = None,
                  display_name: str = "") -> dict:
    """
    스무 사람 종합. tier="all" 로 뽑습니다 — 이걸 받는 사람은 이미
    값을 치른 사람입니다.
    """
    lenses = [l for l in lens_mod.all_lenses() if l.get("released")]

    chapters = []
    lead_count = Counter()
    for l in lenses:
        r = report_mod.build_report(f, chart_id, l["id"], "all", concern, axis4)
        view = lens_mod.view(l["id"])

        # 명식 컷은 장마다 되풀이할 필요가 없습니다. 앞에 한 번 나옵니다.
        cuts = [c for c in r["cuts"] if c["id"] != "chart"]
        if cuts:
            lead_count[cuts[0]["id"]] += 1

        chapters.append({
            "lens_id": l["id"],
            "name": l["name"],
            "hanja": l.get("hanja"),
            "group": l.get("group"),
            "archetype": l.get("archetype"),
            "color": l.get("color"),
            "you": view["you"],
            "opening": r["opening"],
            "closing": r["closing"],
            "leads_with": CUT_LABEL.get(cuts[0]["id"], cuts[0]["id"]) if cuts else None,
            "cuts": cuts,
        })

    # ── ② 한 목소리로 짚는 것 ──────────────────────────────
    #
    # 몇 명이 그 자리를 **맨 앞에** 놓았는가로 셉니다. 컷이 있고 없고가
    # 아니라 무엇을 먼저 보았는가라야 뜻이 있습니다.
    agreed = [
        {"cut": cid, "label": CUT_LABEL.get(cid, cid), "n": n,
         "of": len(lenses)}
        for cid, n in lead_count.most_common()
    ]

    top = agreed[0] if agreed else None
    consensus_html = ""
    if top and top["n"] >= 2:
        consensus_html = (
            '<p class="tale">스무 사람 중 <b>%d 사람</b>이 이 명식에서 '
            '<b>%s</b>부터 보았소.</p>'
            '<p class="sm">같은 자리를 여럿이 먼저 본다는 것은, 그 자리가 '
            '이 여덟 글자에서 가장 눈에 띈다는 뜻이오. '
            '맞았다는 뜻이 아니라 <b>도드라진다</b>는 뜻이오.</p>'
            % (top["n"], top["label"])
        )
    else:
        consensus_html = (
            '<p class="tale">스무 사람이 저마다 다른 자리부터 보았소.</p>'
            '<p class="sm">한 자리로 모이지 않는 명식이오. '
            '치우친 데가 뚜렷하지 않다는 뜻이기도 하오.</p>'
        )

    # ── ③ 갈리는 자리 ────────────────────────────────────
    split = [a for a in agreed if a["n"] == 1]
    split_html = (
        '<p class="tale">%s</p>'
        '<p class="sm">한 사람만 먼저 본 자리요. 남들이 안 보는 것을 '
        '본 사람이 있다는 것이지, 그 사람이 틀렸다는 뜻은 아니오.</p>'
        % (" · ".join("<b>%s</b>" % a["label"] for a in split)
           if split else "갈리는 자리는 없었소.")
    )

    # ── 머리 ────────────────────────────────────────────
    sm = summary_mod.build_summary(None, f, concern, axis4,
                                   lens_id="pungun", display_name=display_name)

    who = display_name.strip() or "이 사람"
    head = {
        "title": "스무 사람의 눈",
        "subtitle": "%s의 여덟 글자를 스무 사람이 각자 본 것" % who,
        "headline": summary_mod.headline(f),
        "pillars": f.pillars,
        "hour_known": f.hour_known,
        "correction": f.correction,
        "lens_count": len(lenses),
    }

    return {
        "chart_id": chart_id,
        "concern": concern,
        "head": head,
        "summary_sections": sm["sections"],
        "consensus": {
            "html": guard.enforce(consensus_html, {"omnibus": "consensus"}),
            "counts": agreed,
        },
        "split": {"html": guard.enforce(split_html, {"omnibus": "split"})},
        "chapters": chapters,
        "caveats": sm.get("caveats", []),
    }
