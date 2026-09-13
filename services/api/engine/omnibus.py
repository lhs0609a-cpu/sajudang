"""
종합 해석을 먼저 편집하고 캐릭터별 관점을 부록으로 붙인다.

reading: 근거를 연결한 핵심 결론, 선택 비교, 시기, 영역별 적용, 재점검.
consensus/split: 같은 관계 규칙이 선택된 영역 수. 캐릭터의 순서나
독립된 전문가들의 합의를 세는 것이 아니다. 키는 이전 API와 호환된다.
chapters: 중복되는 공통 컷을 제외한 캐릭터별 관점과 추가 입력.
권한은 라우터가 확인하며 구독의 깊이는 기존 sub 층을 따른다.
"""
from __future__ import annotations

from collections import Counter
from typing import Optional

from . import guard
from . import lens as lens_mod
from . import report as report_mod
from . import summary as summary_mod
from . import interpretation

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


def build_omnibus(f, chart_id: str, concern: str = "love",
                  axis4: Optional[str] = None,
                  display_name: str = "",
                  extras: Optional[dict] = None, tier: str = "all") -> dict:
    """
    라우터에서 확인한 tier로 읽을 수 있는 범위만 조립합니다.

    extras 를 주면 그걸 받는 캐릭터의 장이 그만큼 두꺼워집니다.
    안 줘도 됩니다 — 그 장은 추가 입력 없이 쓰이고, `needs_input` 이
    무엇을 더 주면 되는지 알려 줍니다.
    """
    lenses = [l for l in lens_mod.all_lenses() if l.get("released")]
    plan = interpretation.build_plan(f, concern, extras)
    reading = interpretation.render(plan, f, tier, comprehensive=True)

    chapters = []
    lead_count = Counter()
    for l in lenses:
        r = report_mod.build_report(f, chart_id, l["id"], tier, concern,
                                    axis4, extras, display_name)
        view = lens_mod.view(l["id"])

        # 명식 컷은 장마다 되풀이할 필요가 없습니다. 앞에 한 번 나옵니다.
        # Shared natal material is explained once in the integrated reading.
        # The appendix contains only the character's own perspective/input.
        cuts = [c for c in r["cuts"] if c["id"].startswith("lc_") or
                c["id"] in ("partner", "context", "blood", "image", "cards", "meet", "face", "body")]

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
            # 이 장을 더 두껍게 만들려면 무엇을 더 주면 되는가
            "needs_input": r.get("needs_input"),
            "leads_with": CUT_LABEL.get(cuts[0]["id"], cuts[0]["id"]) if cuts else None,
            "cuts": cuts,
        })

    # ── ② 한 목소리로 짚는 것 ──────────────────────────────
    #
    # 같은 주장이 연결되는 영역을 센다. 캐릭터 순서와 무관하다.
    # Count the same semantic claim across domains, never character ordering.
    rejected = {c["id"] for c in plan["rejected"]}
    domain_plans = [plan if key == concern else interpretation.build_plan(f, key)
                    for key in interpretation.content()["domains"]]
    claim_labels = {}
    for domain in domain_plans:
        for claim in domain["selected"]:
            if claim["id"] not in rejected:
                lead_count[claim["id"]] += 1
                claim_labels[claim["id"]] = claim["title"]
    agreed = [{"cut": cid, "label": claim_labels[cid], "n": n, "of": len(domain_plans)}
              for cid, n in lead_count.most_common()]

    top = agreed[0] if agreed else None
    consensus_html = ""
    if top and top["n"] >= 2:
        consensus_html = (
            '<p class="tale"><b>%d개 영역</b>에서 함께 살펴볼 관계는 '
            '<b>%s</b>입니다.</p>'
            '<p class="sm">같은 명식과 규칙에서 나온 해석을 영역별로 연결한 것입니다. '
            '독립된 전문가들의 합의나 예측의 확률을 뜻하지 않습니다.</p>'
            % (top["n"], top["label"])
        )
    else:
        consensus_html = (
            '<p class="tale">각 영역에서 확인할 관계를 따로 정리했습니다.</p>'
            '<p class="sm">여러 영역에 반복되는 해석이 적다는 이유로 명식의 성향을 단정하지 않습니다.</p>'
        )

    # ── ③ 갈리는 자리 ────────────────────────────────────
    split = [a for a in agreed if a["n"] == 1]
    split_html = (
        '<p class="tale">%s</p>'
        '<p class="sm">한 영역에서 우선 선택된 해석입니다. 다른 영역의 결론과 서로 반대라는 뜻은 아닙니다.</p>'
        % (" · ".join("<b>%s</b>" % a["label"] for a in split)
           if split else "한 영역에만 우선 선택된 해석은 없습니다.")
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
        "reading": reading,
        "tier": tier,
        "chart_id": chart_id,
        "concern": concern,
        "head": head,
        "summary_sections": sm["sections"],
        "consensus": {
            "html": guard.enforce(consensus_html, {"omnibus": "consensus"}),
            "counts": agreed,
            "unit": "영역",
        },
        "split": {"html": guard.enforce(split_html, {"omnibus": "split"})},
        "chapters": chapters,
        "caveats": sm.get("caveats", []),
    }
