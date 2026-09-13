"""Versioned interpretation plans: facts -> candidates -> selection -> prose.

Birth calculations retain their existing policy. A rule match is a traditional
reading hypothesis, never evidence that an event or behaviour actually occurred.
Only allowlisted answers affect advice; they never mutate natal facts.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from functools import lru_cache
from hashlib import sha256
from html import escape
import json
from pathlib import Path

from . import guard, solar_terms, topic, pattern
from .calendar import year_ganji
from .constants import (CHUNG, HAP, HIDDEN, GAN, JI, OHO, ELEMENT_OF_GAN,
                        GENERATED_BY, GENERATES, CONTROLS, CONTROLLED_BY,
                        TEN_GOD_GROUP, ten_god)

VERSION = 1
GROUPS = {"비겁": "bi", "식상": "sik", "재성": "jae", "관성": "gwan", "인성": "inn"}
STAGES = {"exploring": "아직 비교하는 중", "tried": "이미 바꿔 보았음", "constrained": "당장 바꾸기 어려움"}
RESPONSES = {"yes": "비슷한 경험이 있음", "no": "내 경험과 다름", "mixed": "상황에 따라 다름", "unknown": "아직 판단하기 어려움"}
PATTERN_LINKS = {
    "output_value": ("siksang_jae", "jaeda_sinyak", "sinwang_jaewang", "jae_hidden"),
    "autonomy_standards": ("bigyeop_many", "gwan_many"),
    "pressure_learning": ("gwan_in", "sal_in", "gwan_many"),
    "shared_reward": ("gunggeop", "jae_hidden"),
    "expression_rules": ("sanggwan_gwan", "siksin_jesal", "gwan_many"),
    "learning_output": ("dosik", "in_many"),
    "resources_support": ("tamjae", "jaeda_sinyak"),
    "reward_responsibility": ("jae_saeng_gwan",),
    "independent_support": ("in_many", "bigyeop_many"),
    "initiative_expression": ("sik_many", "ilji_chung", "ilji_hap"),
}


@lru_cache(maxsize=1)
def content():
    return json.loads((Path(__file__).resolve().parents[3] / "seed" / "interpretation.json").read_text("utf-8"))


def fingerprint(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:20]


def structure(f):
    """Keep position, visibility and hidden stems distinct; do not recount them as votes."""
    facts = {}
    seats = {g: [] for g in GROUPS}
    roots = []
    for p in f.pillars:
        label = p["label"]
        for index, (gan, weight) in enumerate(HIDDEN[p["ji"]]):
            god = ten_god(gan, f.day_gan)
            group = TEN_GOD_GROUP[god]
            seats[group].append({"pillar": label, "gan": gan, "god": god,
                                 "position": "본기" if index == 0 else "지장간", "weight": weight})
            if ELEMENT_OF_GAN[gan] == ELEMENT_OF_GAN[f.day_gan]:
                roots.append(f"{label} {p['ji']} 속 {gan} ({'본기' if index == 0 else '지장간'})")
        if label != "일주":
            god = ten_god(p["gan"], f.day_gan)
            seats[TEN_GOD_GROUP[god]].append({"pillar": label, "gan": p["gan"],
                                           "god": god, "position": "천간", "weight": 1})
    for group, attr in GROUPS.items():
        counted = [s for s in seats[group] if s["position"] != "지장간"]
        text = " · ".join(f"{s['pillar']} {s['position']} {s['gan']}({s['god']})" for s in counted)
        facts[f"group:{group}"] = {"id": f"group:{group}", "kind": "computed",
            "label": f"{group} {getattr(f, attr)}개", "text": text or "천간(일간 제외)과 지지 본기 집계에서 0개입니다.",
            "value": getattr(f, attr), "seats": seats[group]}
    relations = []
    for i, left in enumerate(f.pillars):
        for right in f.pillars[i + 1:]:
            kind = "충" if CHUNG.get(left["ji"]) == right["ji"] else "합" if HAP.get(left["ji"]) == right["ji"] else None
            if kind:
                relations.append(f"{left['label']} {left['ji']} · {right['label']} {right['ji']} — {kind}")
    month = next(p for p in f.pillars if p["label"] == "월주")
    facts["structure"] = {"id": "structure", "kind": "computed", "label": f"{f.strength} · {topic.gyeok(f)}",
        "text": f"월지 {month['ji']} · 득령 {'있음' if f.deuk_ryeong else '없음'} · 득지 {'있음' if f.deuk_ji else '없음'} · 기존 강약 점수 {f.strength_score}",
        "roots": roots, "relations": relations, "hyeong": topic.hyeong(f), "hap_group": list(topic.hap_group(f))}
    return facts


def yongsin_review(f):
    me = ELEMENT_OF_GAN[f.day_gan]
    candidates = [CONTROLS[me], GENERATES[me], CONTROLLED_BY[me]] if f.strength == "신강" else [me, GENERATED_BY[me]]
    ordered = sorted(candidates, key=lambda el: f.elements[el])
    tied = [el for el in ordered if f.elements[el] == f.elements[ordered[0]]]
    return {"selected": f.yongsin, "candidates": [{"element": el, "weight": f.elements[el]} for el in ordered],
        "tied": tied, "method": "기존 억부 기준 · 후보 중 오행 가중치가 가장 작은 값",
        "limit": "조후·격의 성패·합화까지 종합한 최종 판정은 아닙니다. 오행이 적다는 사실만으로 필요한 행동을 결정하지 않습니다.",
        "status": "복수 후보" if len(tied) > 1 or f.strength == "중화" or not f.hour_known else "기존 기준의 후보"}


def _answer_key(rule_id, concern):
    return f"claim:{concern}:{rule_id}"


def parse_answers(extras, concern):
    raw = (extras or {}).get("consultation")
    if raw is None:
        return {}, None
    if not isinstance(raw, dict) or set(raw) - {"concern", "answers"} or raw.get("concern") != concern:
        return {}, "지금 고민에 맞는 질문으로 다시 골라 주세요. 기존 명식 풀이는 그대로 볼 수 있습니다."
    answers = raw.get("answers", {})
    if not isinstance(answers, dict) or len(answers) > len(content()["rules"]) + 2:
        return {}, "답변 형식을 확인해 주세요."
    allowed = {_answer_key(r["id"], concern): set(RESPONSES) for r in content()["rules"]}
    allowed["driver"] = {d["id"] for d in content()["domains"][concern]["drivers"]}
    allowed["stage"] = set(STAGES)
    for key, value in answers.items():
        if key not in allowed or not isinstance(value, str) or value not in allowed[key]:
            return {}, "선택 목록에 없는 답변이 있어 반영하지 않았습니다. 다시 골라 주세요."
    return dict(answers), None


def build_plan(f, concern="love", extras=None):
    if concern not in content()["domains"]:
        raise ValueError("지원하지 않는 고민입니다.")
    facts = structure(f)
    patterns = {row["key"]: row for row in pattern.read(f, concern, limit=99)}
    # Pattern facts cite the existing engine's actual conditions, not its
    # historical-event prose. They refine relevance without independent votes.
    for key, row in patterns.items():
        facts["pattern:" + key] = {"id": "pattern:" + key, "kind": "rule_match",
            "label": row["name"], "text": row["why"], "value": 1}
    answers, error = parse_answers(extras, concern)
    candidates = []
    for rule in content()["rules"]:
        if concern not in rule["focus"]:
            continue
        groups = rule["groups"]
        if not all(facts[f"group:{g}"]["value"] > 0 for g in groups):
            continue
        evidence = [f"group:{g}" for g in groups]
        matched = [key for key in PATTERN_LINKS.get(rule["id"], ()) if key in patterns]
        evidence.extend("pattern:" + key for key in matched)
        visible = [g for g in groups if any(s["position"] == "천간" for s in facts[f"group:{g}"]["seats"])]
        counter = []
        if len(visible) < len(groups):
            counter.append("두 축이 모두 천간에 드러난 배치는 아닙니다. 개수만으로 행동의 강도를 정하지 않습니다.")
        if f.top_ten_god_tied:
            counter.append("최다 십신이 동률이라 하나의 성향으로 압축하지 않습니다.")
        if not f.hour_known:
            sensitivity = getattr(f, "hour_sensitivity", {})
            stable = rule["id"] in sensitivity.get("stable_rules", [])
            counter.append("출생 시각이 없어 실제 명식에서 시주는 제외했습니다.")
            counter.append("비교한 모든 시각에서 두 축의 공존 조건은 유지됐습니다. 실제 행동까지 확인한 것은 아닙니다." if stable else
                           "시각에 따라 이 관계나 우선순위가 달라질 수 있어 잠정적으로 읽습니다.")
        if f.correction.get("boundary_note"):
            counter.append(f.correction["boundary_note"])
        # Strength qualifies the same relationship rather than generating opposing advice.
        qualifier = {
            "신강": "기존 기준에서는 신강입니다. 감당할 여지가 있다는 해석과 실제로 더 맡아도 된다는 판단은 구분합니다.",
            "신약": "기존 기준에서는 신약입니다. 부족하다는 성격 평가 대신 지원과 부담의 조건을 먼저 살펴봅니다.",
            "중화": "기존 기준에서는 중화입니다. 한 방향으로 몰기보다 상황에 따른 차이를 먼저 확인합니다.",
        }[f.strength]
        answer = answers.get(_answer_key(rule["id"], concern), "unknown")
        status = {"yes": "경험과 연결", "no": "이번 결론에서 제외", "mixed": "조건부 검토", "unknown": "경험 확인 전"}[answer]
        rank_reasons = ["두 십신 묶음이 함께 집계됨"]
        score = 20 + min(*(facts[f"group:{g}"]["value"] for g in groups), 3)
        if concern in rule["focus"]:
            score += 12
            rank_reasons.append("선택한 고민과 직접 관련된 관계")
        if len(visible) == 2:
            score += 3
            rank_reasons.append("두 축이 모두 천간에 드러남")
        if matched:
            score += 4
            rank_reasons.append("기존 관계 규칙의 구체적 조건과 연결됨 — 같은 근거를 중복 득표로 세지 않음")
        if not f.hour_known and getattr(f, "hour_sensitivity", {}) and not stable:
            score -= 6
            rank_reasons.append("출생 시각에 따라 성립 여부가 달라질 수 있어 우선순위를 낮춤")
        if answer == "yes":
            score += 8
            rank_reasons.append("사용자가 관련 경험을 선택함 — 명식의 증거와 별도")
        elif answer == "mixed":
            score -= 3
            counter.append("사용자가 상황에 따라 다르다고 답했습니다. 모든 관계와 환경에 일반화하지 않습니다.")
        elif answer == "no":
            counter.append("사용자가 경험과 다르다고 답해 이번 핵심 결론에서 제외했습니다. 다른 말로 되살리지 않습니다.")
        candidates.append({**rule, "claim_id": f"{rule['id']}@{concern}", "concern": concern,
            "evidence_ids": evidence, "counterevidence": counter, "qualifier": qualifier,
            "rank": score, "rank_reasons": rank_reasons, "status": status, "answer": answer,
            "source_kind": "traditional_hypothesis", "semantic_key": rule["id"]})
    candidates.sort(key=lambda c: (-c["rank"], c["id"]))
    eligible = [c for c in candidates if c["answer"] != "no"]
    selected = []
    # Diversify actual relationships; renaming the same rule never creates a new claim.
    while eligible and len(selected) < 3:
        used = Counter(g for c in selected for g in c["groups"])
        winner = max(eligible, key=lambda c: (c["rank"] - sum(used[g] * 4 for g in c["groups"]), -candidates.index(c)))
        selected.append(winner)
        eligible.remove(winner)
    plan = {"version": VERSION, "concern": concern, "facts": facts, "candidates": candidates,
        "selected": selected, "rejected": [c for c in candidates if c["answer"] == "no"],
        "answers": answers, "input_error": error, "method": yongsin_review(f),
        "basis": fingerprint({"pillars": f.pillars, "strength": f.strength, "version": VERSION})}
    plan["fingerprint"] = fingerprint({"basis": plan["basis"], "concern": concern, "answers": answers})
    violations = validate_plan(plan)
    if violations:
        raise ValueError("해석 근거 연결을 확인하지 못했습니다: " + ", ".join(violations))
    return plan


def validate_plan(plan):
    errors, seen = [], set()
    for claim in plan["selected"]:
        if claim["semantic_key"] in seen:
            errors.append("duplicate_claim")
        seen.add(claim["semantic_key"])
        if claim["answer"] == "no":
            errors.append("rejected_claim_selected")
        if not claim["evidence_ids"] or any(e not in plan["facts"] for e in claim["evidence_ids"]):
            errors.append("missing_evidence")
        if any(plan["facts"].get(e, {}).get("value", 0) <= 0 for e in claim["evidence_ids"]):
            errors.append("unsupported_relationship")
        if not claim.get("exception") or not claim.get("action"):
            errors.append("missing_boundary_or_action")
    return errors


def questions(plan):
    domain = content()["domains"][plan["concern"]]
    first = next((c for c in plan["selected"] if _answer_key(c["id"], plan["concern"]) not in plan["answers"]), None)
    rows = []
    if first:
        rows.append({"id": _answer_key(first["id"], plan["concern"]), "question": first["question"],
            "reason": "답변에 따라 이 해석을 유지하거나 조건을 좁히거나 제외합니다."})
        rows[-1]["options"] = [{"id": k, "label": v} for k, v in RESPONSES.items()]
    rows.extend([
        {"id": "driver", "question": domain["driver_question"], "reason": "먼저 다룰 현실 문제와 행동을 정합니다.",
         "options": [{"id": d["id"], "label": d["label"]} for d in domain["drivers"]]},
        {"id": "stage", "question": "지금 어느 단계에 있나요?", "reason": "이미 해본 조언을 반복하지 않도록 실행 순서를 바꿉니다.",
         "options": [{"id": k, "label": v} for k, v in STAGES.items()]},
    ])
    return {"concern": plan["concern"], "title": "내 상황에 맞춰 더 좁혀 보기", "questions": rows,
        "answers": plan["answers"], "note": "고른 경험은 사주로 알아낸 사실과 구분해 반영합니다. 이 답변은 서버에 저장하지 않습니다."}


def p(text, css=""):
    attr = f' class="{escape(css, quote=True)}"' if css else ""
    return f'<p{attr}>{escape(str(text))}</p>'


def claim_html(claim, plan):
    domain = content()["domains"][plan["concern"]]
    html = p(claim["thesis"], "reading-thesis")
    html += p("강점으로 쓰는 조건 · " + claim["benefit"])
    html += p("확인할 장면 · " + domain["scene"] + ". " + claim["trigger"] + "인지 살펴보세요.")
    html += p("반복되면 치르는 비용 · " + claim["cost"])
    if claim["answer"] != "unknown":
        html += p("직접 고른 경험 · " + RESPONSES[claim["answer"]], "reading-origin")
    html += p("다르게 읽어야 할 때 · " + claim["exception"])
    if plan["answers"].get("stage") == "tried":
        html += p("이미 바꿔 보았다면 · 위의 예외 조건에 해당했는지 먼저 확인하세요. 같은 행동을 더 반복하는 것으로 해결되지 않을 수 있습니다.", "reading-action")
    else:
        html += p("해볼 일 · " + claim["action"], "reading-action")
    html += '<details><summary>읽은 근거와 해석의 범위</summary>'
    html += p("먼저 고른 이유 · " + " · ".join(claim["rank_reasons"]))
    for ref in claim["evidence_ids"]:
        fact = plan["facts"][ref]
        html += p(fact["label"] + " — " + fact["text"])
    html += p(claim["qualifier"])
    for line in claim["counterevidence"]:
        html += p(line)
    html += p("두 축의 공존을 전통 해석의 질문으로 옮긴 것입니다. 실제 행동이나 사건을 입증하는 근거는 아닙니다.")
    return guard.enforce(html + "</details>")


def decision_html(plan):
    domain, answers = content()["domains"][plan["concern"]], plan["answers"]
    stage = answers.get("stage")
    driver = next((d for d in domain["drivers"] if d["id"] == answers.get("driver")), None)
    html = p("선택을 대신 결정하기보다, 두 방법의 조건을 비교합니다.")
    if driver:
        html += p("직접 고른 우선 문제 · " + driver["label"], "reading-origin") + p(driver["action"], "reading-action")
    if stage == "tried":
        html += p("이미 바꿔 보았다고 답했습니다. 같은 시도를 반복하기 전에, 실제로 바꾼 조건과 그대로였던 조건을 비교해 보세요.")
        a, b = "이전 시도에서 바뀌지 않았던 조건을 합의할 수 있을 때", "같은 시도가 막혔던 이유를 작은 다른 방식으로 확인할 수 있을 때"
    elif stage == "constrained":
        html += p("당장 바꾸기 어렵다고 답했습니다. 큰 결정을 서두르기보다 현재 범위에서 줄일 부담과 요청할 지원부터 찾습니다.")
        a, b = "현재 자리에서 한 가지 조건은 조정할 수 있을 때", "시간과 자원의 상한을 정하고 부담 없이 멈출 수 있을 때"
    else:
        html += p("아직 확인할 조건이 남아 있다면, 결정을 바꿀 수 있는 사실 하나부터 확인해 보세요.")
        a, b = "문제가 특정 조건에 집중되어 있고 상대와 다시 합의할 수 있을 때", "대안에 대한 정보가 부족하지만 되돌릴 수 있는 시험은 가능할 때"
    for title, condition in zip(domain["choices"], (a, b)):
        html += '<h3>' + escape(title) + '</h3>' + p("검토할 조건 · " + condition)
    html += p("멈추고 다시 볼 때 · 합의한 범위를 넘거나, 시험 전에 정한 부담의 상한을 넘을 때는 조건부터 다시 정합니다.")
    return guard.enforce(html)


def next_action(plan):
    domain, answers = content()["domains"][plan["concern"]], plan["answers"]
    driver = next((d for d in domain["drivers"] if d["id"] == answers.get("driver")), None)
    if answers.get("stage") == "tried":
        return "이미 시도한 장면에서 " + domain["record"] + "을 나눠 적고, 실제로 바뀌지 않은 조건 하나부터 확인해 보세요."
    action = driver["action"] if driver else plan["selected"][0]["action"] if plan["selected"] else "최근 장면 하나의 실제 사실과 내 해석을 따로 적어 보세요."
    if answers.get("stage") == "constrained":
        return "큰 결정보다 지금 조정할 수 있는 범위부터 살펴봅니다. " + action
    return action


def domain_html(claim, plan, explained):
    """Explain a natal relationship once; subsequent domains add only application."""
    domain = content()["domains"][plan["concern"]]
    if not claim:
        return p("이 영역에서는 근거가 충분한 핵심 결론을 더 붙이지 않았습니다.")
    if claim["semantic_key"] in explained:
        html = p("앞에서 읽은 관계를 이 영역에 연결합니다 · " + claim["title"])
        html += p("별개의 성향을 하나 더 발견했다는 뜻이 아닙니다. 적용할 장면과 확인할 조건을 바꿔 봅니다.")
    else:
        html = claim_html(claim, plan)
        explained.add(claim["semantic_key"])
    html += p("이 영역의 장면 · " + domain["scene"]) + p("확인할 기록 · " + domain["record"])
    html += "<h3>지금 걸린 문제에 따라</h3>"
    for driver in domain["drivers"]:
        html += p(driver["label"] + "이 고민이라면 · " + driver["action"])
    return guard.enforce(html)


def _transit(f, gan, ji):
    god = ten_god(gan, f.day_gan)
    group = TEN_GOD_GROUP[god]
    links = []
    for pillar in f.pillars:
        if CHUNG.get(ji) == pillar["ji"]:
            links.append(f"{pillar['label']} {pillar['ji']}와 충")
        elif HAP.get(ji) == pillar["ji"]:
            links.append(f"{pillar['label']} {pillar['ji']}와 합")
        elif ji == pillar["ji"]:
            links.append(f"{pillar['label']} {pillar['ji']}와 같은 지지")
    prompt = {"비겁": "직접 정할 일과 함께 나눌 몫", "식상": "내놓을 결과와 전달할 방식", "재성": "쓰는 자원과 남는 결과",
              "관성": "맡는 책임과 합의할 기준", "인성": "필요한 배움과 도움받을 통로"}[group]
    return f"{gan}{ji} · 천간 {god} · 원국 {group} {getattr(f, GROUPS[group])}개와 함께 읽음", links, prompt


def timing_html(f, include_calendar=False):
    html = p("대운은 기존 계산의 연 나이를 사용합니다. 아래 날짜는 사건이 일어나는 때가 아니라 해석에 쓰는 간지가 바뀌는 경계입니다.")
    now = f.daeun_now
    indices = ([now - 1] if now > 0 else []) + [now] + ([now + 1] if now + 1 < len(f.daeun) else [])
    for index in indices:
        d = f.daeun[index]
        start = int(d["start_age"])
        end = int(f.daeun[index + 1]["start_age"]) if index + 1 < len(f.daeun) else start + 10
        label = "이전" if index < now else "현재" if index == now and f.daeun_started else "다음"
        if index == now and f.age >= end:
            label = "마지막으로 계산된"
        fact, links, prompt = _transit(f, d["gan"], d["ji"])
        html += f'<h3>{label} 대운 · 연 나이 {start}~{end - 1}세</h3>' + p(fact)
        html += p("원국과 만나는 자리 · " + (" · ".join(links) or "이번 비교에서 같은 지지·육합·충이 잡히지 않습니다."))
        html += p(("지나온 경험에서 확인할 것 · " if index < now else "이 구간을 돌아볼 질문 · ") + prompt)
    if not f.daeun_started:
        html += p("아직 첫 대운 시작 전입니다. 첫 칸을 현재 대운으로 해석하지 않습니다.")
    if f.daeun and f.age >= int(f.daeun[-1]["start_age"]) + 10:
        html += p("현재 나이가 계산된 대운 목록의 범위를 지났습니다. 마지막 칸을 현재 대운으로 연장해서 해석하지 않습니다.")
    if not include_calendar:
        return guard.enforce(html)
    snapshot = getattr(f, "as_of", "")
    if not snapshot:
        return guard.enforce(html + p("이 명식의 기준일 기록이 없어 세운·월운은 붙이지 않았습니다. 명식을 다시 계산하면 기준일과 함께 볼 수 있습니다."))
    # The snapshot date is evaluated at 00:00 KST, explicitly displayed. This is
    # a calendar reference instant, not an invented birth time.
    utc = datetime.fromisoformat(snapshot) - timedelta(hours=9)
    sy = solar_terms.saju_year_of(utc)
    html += p(f"세운·월운 기준 · {snapshot} 00:00 한국 표준시. 출생지 보정을 현재 달력에 다시 적용하지 않습니다.", "reading-origin")
    for year in (sy, sy + 1):
        if year > solar_terms.MAX_YEAR or year < solar_terms.MIN_YEAR:
            continue
        gan, ji = year_ganji(year)
        fact, links, prompt = _transit(f, gan, ji)
        start = solar_terms.ipchun_utc(year) + timedelta(hours=9)
        html += f'<h3>{year}년 입춘부터 · {start:%Y-%m-%d %H:%M}</h3>' + p(fact) + p("함께 볼 조건 · " + prompt)
        if links:
            html += p(" · ".join(links))
    current = solar_terms.current_jie(utc)[1]
    seq = [(y, idx, at) for y in (sy, sy + 1) if solar_terms.MIN_YEAR <= y <= solar_terms.MAX_YEAR
           for idx, at in solar_terms.jie_terms(y) if at >= current]
    for year, idx, at in sorted(seq, key=lambda x: x[2])[:3]:
        ji = solar_terms.JIE_TO_JI[idx]
        year_gan = year_ganji(year)[0]
        gan = GAN[(GAN.index(OHO[year_gan]) + (JI.index(ji) - JI.index("寅")) % 12) % 10]
        fact, links, prompt = _transit(f, gan, ji)
        start = at + timedelta(hours=9)
        html += f'<h3>{solar_terms.term_name(idx)}부터 · {start:%Y-%m-%d %H:%M}</h3>' + p(fact) + p("확인할 질문 · " + prompt)
        if links:
            html += p(" · ".join(links))
    return guard.enforce(html)


def method_html(f, plan):
    facts, method = plan["facts"], plan["method"]
    html = p(facts["structure"]["label"] + " — " + facts["structure"]["text"])
    html += p("명식 · " + " · ".join(pillar["label"] + " " + pillar["gz"] for pillar in f.pillars))
    html += p("일간과 같은 오행의 뿌리 · " + (" · ".join(facts["structure"]["roots"]) or "집계한 지장간에서 확인되지 않습니다."))
    html += p("기둥 사이 관계 · " + (" · ".join(facts["structure"]["relations"]) or "이번 육합·충 비교에서 해당 관계가 없습니다."))
    if facts["structure"]["hyeong"]:
        html += p("기존 형 분류 · " + facts["structure"]["hyeong"] + ". 이 분류로 실제 다툼이나 사건을 판단하지 않습니다.")
    html += p("용신 검토 · " + method["selected"] + " / " + method["status"])
    html += p(method["method"] + " — " + " · ".join(f"{r['element']} {r['weight']:g}" for r in method["candidates"]))
    html += p(method["limit"])
    if len(method["tied"]) > 1:
        html += p("가장 작은 값이 같은 후보 · " + " · ".join(method["tied"]) + ". 기존 표시값 하나를 독점적인 정답으로 해석하지 않습니다.")
    html += p("시각을 알고 있는 명식입니다." if f.hour_known else "시각 미상: 시주를 제외한 세 기둥의 잠정 해석입니다. 시각을 알면 강약·용신·우선 결론이 달라질 수 있습니다.")
    correction = f.correction
    html += '<details><summary>계산에 쓴 시각과 절기</summary>'
    html += p("표준시 · " + correction.get("std_label", "기록 없음"))
    if correction.get("lon_min") is not None:
        html += p("출생지 보정 · " + correction.get("city", "기록 없음") + f" / {correction['lon_min']:+.1f}분")
    if f.hour_known:
        html += p("입력 시각 → 보정 시각 · " + correction.get("before", "미상") + " → " + correction.get("after", "미상"))
    else:
        html += p("출생 시각이 없어 실제 보정 시각은 확정하지 않았습니다. 절입 근처라면 년·월주도 시각에 따라 달라질 수 있습니다.")
    html += p("절기 · " + correction.get("jieqi_name", "기록 없음") + " / " + correction.get("jieqi_at_kst", "기록 없음"))
    basis_label = {"corrected": "출생지 경도 보정 후 비교", "standard": "표준시 기준 비교"}.get(correction.get("jieqi_basis"), "기록 없음")
    html += p("자시 정책 · " + correction.get("zi_policy", "기록 없음") + " / 절입 비교 · " + basis_label)
    html += p("서머타임 · " + ("입력 시각에서 반영해 계산했습니다." if correction.get("dst") else "해당하지 않습니다.")) + "</details>"
    if f.correction.get("boundary_note"):
        html += p(f.correction["boundary_note"])
    sensitivity = getattr(f, "hour_sensitivity", {})
    if not f.hour_known and sensitivity:
        html += '<h3>출생 시각을 달리 놓고 비교한 범위</h3>'
        html += p(sensitivity["basis"] + f" · 계산 가능한 {sensitivity['checked_minutes']}분 · 서로 다른 명식 {sensitivity['chart_variants']}종")
        html += p("달라질 수 있는 강약 분류 · " + " · ".join(sensitivity["strengths"]))
        html += p("달라질 수 있는 용신 후보 · " + " · ".join(sensitivity["yongsins"]))
        html += p("가능한 일주 · " + " · ".join(sensitivity["day_pillars"]))
        if sensitivity["unsupported_minutes"]:
            html += p(f"계산하지 못한 시각 {sensitivity['unsupported_minutes']}분은 비교에서 제외했습니다. 모든 시각을 확인한 결과로 일반화하지 않습니다.")
        html += p(sensitivity["note"])
    return guard.enforce(html)


def render(plan, f, tier="free", comprehensive=False):
    """Project only entitled prose; the full candidate ledger stays on the server."""
    paid = tier != "free"
    shown = plan["selected"][:3 if paid else 1]
    summary = [{"id": c["claim_id"], "title": c["title"], "status": c["status"],
                "html": claim_html(c, plan)} for c in shown]
    sections = []
    if paid:
        sections.append({"id": "decision", "title": "지금 고민의 두 선택", "html": decision_html(plan)})
        sections.append({"id": "timing", "title": "지나온 흐름과 다음 구간", "html": timing_html(f, tier == "all")})
        if comprehensive:
            explained = {claim["semantic_key"] for claim in shown}
            for concern, domain in content()["domains"].items():
                if concern == plan["concern"]:
                    continue
                # Reuse the same natal hypotheses, with no unrelated context answers.
                domain_plan = build_plan(f, concern)
                rejected = {c["id"] for c in plan["rejected"]}
                claim = next((c for c in domain_plan["selected"] if c["id"] not in rejected), None)
                html = domain_html(claim, domain_plan, explained)
                sections.append({"id": "domain_" + concern, "title": domain["label"] + "에서 살펴볼 것", "html": html})
    sections.append({"id": "method", "title": "명식 구조와 다르게 읽힐 여지", "html": method_html(f, plan)})
    if plan["rejected"]:
        sections.append({"id": "revised", "title": "답변을 듣고 제외한 해석", "html": "".join(
            p(c["title"]) + p("경험과 다르다고 답해 이번 결론에서 제외했습니다.") for c in plan["rejected"])})
    if paid:
        domain = content()["domains"][plan["concern"]]
        html = p("이번에 살펴볼 장면 · " + domain["scene"]) + p("기록할 세 가지 · " + domain["record"])
        html += p("한 가지 실행 · " + next_action(plan))
        html += p("다음에 비슷한 장면이 생기면, 행동을 바꿨는지와 상대·환경의 조건이 달라졌는지를 따로 확인해 보세요. 맞지 않은 해석은 유지할 필요가 없습니다.")
        sections.append({"id": "review", "title": "한 가지 실행하고 다시 보기", "html": html})
    result = {"version": VERSION, "fingerprint": plan["fingerprint"], "basis": plan["basis"],
        "headline": shown[0]["title"] if shown else "한 가지 성향으로 압축하기보다 실제 상황부터 확인합니다.",
        "summary": summary, "sections": sections, "consultation": questions(plan), "input_error": plan["input_error"],
        "scope": "전체" if comprehensive else "선택한 고민", "as_of": getattr(f, "as_of", ""),
        "boundary": "계산된 배치를 전통 해석의 질문으로 옮겼습니다. 실제 경험은 고른 답변으로만 확인하며, 사건이나 상대의 마음을 단정하지 않습니다.",
        "empty_reason": None if shown else "이번 근거와 답변에서 유지할 수 있는 관계 해석이 부족해 결론 수를 억지로 채우지 않았습니다."}
    return guard.enforce_deep(result)
