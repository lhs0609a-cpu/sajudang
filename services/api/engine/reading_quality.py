"""Structural quality gates, intentionally separate from customer satisfaction."""
from collections import Counter
from datetime import date
from functools import lru_cache
import json
from pathlib import Path

from . import interpretation as ip, guard
from .calendar import build_chart
from .features import build_features


def cases():
    return json.loads((Path(__file__).resolve().parents[3] / "seed" / "reading_cases.json").read_text("utf-8"))


def features(case, as_of):
    y, m, d, h, minute, sex = case["birth"]
    f = build_features(build_chart(y, m, d, h, minute, sex, hour_known=h is not None, city=case["city"]), as_of=date.fromisoformat(as_of))
    if h is None:
        from .hour_sensitivity import compare
        f.hour_sensitivity = compare(y, m, d, sex, case["city"])
    return f


@lru_cache(maxsize=1)
def measure():
    dataset = cases()
    result = {"version": ip.VERSION, "as_of": dataset["as_of"], "cases": len(dataset["cases"]),
        "reports": 0, "claims": 0, "empty_reports": 0, "rejection_checks": 0, "rejection_passed": 0,
        "errors": [], "rules_covered": [], "human_review": None, "customer_value": None,
        "note": "자동 검사는 근거 연결·중복·답변 반영을 확인합니다. 전문가 검토와 실제 고객의 가격 대비 만족도는 아직 집계되지 않았습니다."}
    rules = Counter()
    for case in dataset["cases"]:
        try:
            f = features(case, dataset["as_of"])
            for concern in ip.content()["domains"]:
                plan = ip.build_plan(f, concern)
                reading = ip.render(plan, f, "all")
                result["reports"] += 1
                result["claims"] += len(plan["selected"])
                result["empty_reports"] += int(not plan["selected"])
                rules.update(c["id"] for c in plan["selected"])
                if guard.scan(reading):
                    result["errors"].append({"case": case["id"], "concern": concern, "error": "guard"})
                if guard.SAFE_FALLBACK in str(reading):
                    result["errors"].append({"case": case["id"], "concern": concern, "error": "fallback"})
                if plan["selected"]:
                    first = plan["selected"][0]
                    changed = ip.build_plan(f, concern, {"consultation": {"concern": concern,
                        "answers": {ip._answer_key(first["id"], concern): "no"}}})
                    result["rejection_checks"] += 1
                    passed = first["id"] not in {c["id"] for c in changed["selected"]} and changed["facts"] == plan["facts"]
                    result["rejection_passed"] += int(passed)
                    if not passed:
                        result["errors"].append({"case": case["id"], "concern": concern, "error": "rejection"})
        except (ValueError, KeyError, TypeError) as exc:
            result["errors"].append({"case": case["id"], "error": type(exc).__name__ + ": " + str(exc)})
    result["rules_covered"] = sorted(rules)
    result["rules_total"] = len(ip.content()["rules"])
    result["passed"] = not result["errors"] and result["reports"] == result["cases"] * len(ip.content()["domains"])
    return result
