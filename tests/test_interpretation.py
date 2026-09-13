from copy import deepcopy
from dataclasses import replace
from datetime import date, timedelta
import pytest

from engine.calendar import build_chart
from engine.features import build_features
from engine import guard, interpretation as ip, solar_terms
from engine.report import build_report
from engine.omnibus import build_omnibus


@pytest.fixture
def f():
    return build_features(build_chart(1993, 11, 25, 15, 0, "F"), as_of=date(2026, 9, 13))


def test_all_domains_have_traceable_nonduplicate_claims(f):
    for concern in ip.content()["domains"]:
        plan = ip.build_plan(f, concern)
        assert ip.validate_plan(plan) == []
        assert len(plan["selected"]) <= 3
        for c in plan["selected"]:
            assert concern in c["focus"]
            assert len(c["evidence_ids"]) >= 2
            assert c["exception"] and c["trigger"] and c["action"]
        reading = ip.render(plan, f, "all", comprehensive=True)
        if not plan["selected"]:
            assert reading["empty_reason"]
        assert not guard.scan(reading)
        assert len([s for s in reading["sections"] if s["id"].startswith("domain_")]) == 5


def test_rejected_claim_is_removed_not_rephrased_in_another_domain(f):
    before = ip.build_plan(f, "work")
    claim = before["selected"][0]
    answers = {ip._answer_key(claim["id"], "work"): "no"}
    after = ip.build_plan(f, "work", {"consultation": {"concern": "work", "answers": answers}})
    assert claim["id"] not in [c["id"] for c in after["selected"]]
    assert after["rejected"][0]["id"] == claim["id"]
    assert before["facts"] == after["facts"]
    assert before["basis"] == after["basis"]
    assert before["fingerprint"] != after["fingerprint"]
    reading = ip.render(after, f, "all", comprehensive=True)
    for section in reading["summary"] + reading["sections"]:
        if section["id"] != "revised":
            assert claim["thesis"] not in section["html"]


def test_driver_and_stage_change_advice_without_changing_natal_facts(f):
    a = ip.build_plan(f, "work", {"consultation": {"concern": "work", "answers": {"driver": "role", "stage": "tried"}}})
    b = ip.build_plan(f, "work", {"consultation": {"concern": "work", "answers": {"driver": "reward", "stage": "constrained"}}})
    assert a["facts"] == b["facts"] and a["method"] == b["method"]
    assert ip.decision_html(a) != ip.decision_html(b)
    assert "이미 바꿔" in ip.decision_html(a)
    assert "당장 바꾸기" in ip.decision_html(b)


@pytest.mark.parametrize("raw", ["bad", {"concern": "love", "answers": {}},
    {"concern": "work", "answers": {"driver": "<script>alert(1)</script>"}},
    {"concern": "work", "answers": {"stage": []}}, {"concern": "work", "answers": {"unknown": "yes"}}])
def test_invalid_or_cross_concern_answers_never_enter_output(f, raw):
    plan = ip.build_plan(f, "work", {"consultation": raw})
    assert plan["input_error"] and plan["answers"] == {}
    assert "<script>" not in str(ip.render(plan, f))


def test_unknown_hour_has_no_invented_seats_and_has_explicit_limits():
    f = build_features(build_chart(1993, 11, 25, None, None, "F", hour_known=False))
    plan = ip.build_plan(f, "money")
    assert all(s["pillar"] != "시주" for g in ip.GROUPS for s in plan["facts"][f"group:{g}"]["seats"])
    assert all(any("출생 시각" in x for x in c["counterevidence"]) for c in plan["selected"])
    assert "시각 미상" in ip.method_html(f, plan)


def test_unsupported_and_duplicate_claims_fail_validation(f):
    plan = ip.build_plan(f, "work")
    broken = deepcopy(plan)
    broken["selected"].append(broken["selected"][0])
    assert "duplicate_claim" in ip.validate_plan(broken)
    broken = deepcopy(plan)
    broken["selected"][0]["evidence_ids"] = ["invented"]
    assert "missing_evidence" in ip.validate_plan(broken)


def test_free_projection_cannot_leak_paid_sections_or_candidate_bank(f):
    plan = ip.build_plan(f, "work")
    free = ip.render(plan, f, "free")
    assert len(free["summary"]) == 1
    assert [s["id"] for s in free["sections"]] == ["method"]
    assert "candidates" not in free and "facts" not in free
    report = build_report(f, "test", "pungun", "free", "work")
    assert report["reading"] == free


def test_old_snapshots_omit_calendar_without_guessing(f):
    text = ip.timing_html(replace(f, as_of=""), True)
    assert "기준일 기록이 없어" in text
    assert "세운·월운 기준" not in text


def test_calendar_uses_exact_ipchun_and_jie_times(f):
    at = solar_terms.ipchun_utc(2026) + timedelta(hours=9)
    before = replace(f, as_of=(at.date() - timedelta(days=1)).isoformat())
    after = replace(f, as_of=(at.date() + timedelta(days=1)).isoformat())
    assert "2025년 입춘부터" in ip.timing_html(before, True)
    assert "2025년 입춘부터" not in ip.timing_html(after, True)
    assert at.strftime("%Y-%m-%d %H:%M") in ip.timing_html(after, True)
    text = ip.timing_html(f, True)
    assert "백로부터" in text and "한로부터" in text and "입동부터" in text


def test_omnibus_integrates_domains_and_honors_subscription_depth(f):
    result = build_omnibus(f, "test", concern="work", tier="sub")
    assert result["reading"]["scope"] == "전체"
    assert result["consensus"]["unit"] == "영역"
    assert all(row["of"] == 6 for row in result["consensus"]["counts"])
    assert "독립된 전문가" in result["consensus"]["html"]
    assert "세운·월운 기준" not in str(result["reading"])
    assert not guard.scan(result)
    assert all(c["id"] != "chart" for chapter in result["chapters"] for c in chapter["cuts"])


def test_unknown_hour_comparison_preserves_actual_three_pillars():
    from engine.hour_sensitivity import compare
    f = build_features(build_chart(1993, 11, 25, None, None, "F", hour_known=False))
    original = deepcopy(f.pillars)
    f.hour_sensitivity = compare(1993, 11, 25, "F", "서울")
    result = f.hour_sensitivity
    assert result["checked_minutes"] + result["unsupported_minutes"] == 1440
    assert result["chart_variants"] >= 12
    assert len(result["day_pillars"]) > 1  # corrected midnight and early-zi boundaries
    assert f.pillars == original and len(f.pillars) == 3
    assert set(result["stable_rules"]).isdisjoint(result["variable_rules"])
    plan = ip.build_plan(f, "work")
    assert "1분 단위" in ip.method_html(f, plan)


def test_book_does_not_repeat_same_thesis_across_domains(f):
    reading = ip.render(ip.build_plan(f, "work"), f, "all", comprehensive=True)
    html = " ".join(c["html"] for c in reading["summary"] + reading["sections"])
    for rule in ip.content()["rules"]:
        assert html.count(rule["thesis"]) <= 1


def test_full_review_dataset_covers_all_rules_without_fallback():
    from engine.reading_quality import measure
    result = measure()
    assert result["cases"] == 30 and result["reports"] == 180
    assert result["passed"] and result["errors"] == []
    assert len(result["rules_covered"]) == result["rules_total"]
    assert result["rejection_passed"] == result["rejection_checks"] == 180 - result["empty_reports"]
    assert result["human_review"] is None and result["customer_value"] is None
