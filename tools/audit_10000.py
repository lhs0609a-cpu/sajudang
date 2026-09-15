"""Reproducible engine audit. Synthetic people are not buyers or concurrent browsers."""
import collections
import hashlib
import json
import sys
import time
from datetime import date
from pathlib import Path

import journey_sim as J


class CompactCounter(collections.Counter):
    def __getitem__(self, key):
        return super().__getitem__(self.compact(key))

    def __setitem__(self, key, value):
        super().__setitem__(self.compact(key), value)

    @staticmethod
    def compact(key):
        return hashlib.sha256(key.encode()).hexdigest() if isinstance(key, str) and len(key) > 256 else key


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    n = 10000
    today = date(2026, 9, 9)
    pop = J.people(n, seed=20260909)
    tally = J.Tally()
    tally.uniq = collections.defaultdict(CompactCounter)
    lenses = J.lens_mod.released()
    coverage, selected_errors = collections.Counter(), collections.Counter()
    started = time.perf_counter()
    for i, person in enumerate(pop):
        person["concern"] = J.CONCERNS[(i // len(lenses)) % len(J.CONCERNS)]
        J.run_one(person, tally, today, include_omnibus=i % 20 == 0)
        selected = lenses[i % len(lenses)]["id"]
        coverage[selected + ":" + person["concern"]] += 1
        try:
            chart = J.build_chart(person["year"], person["month"], person["day"], person["hour"],
                                  person["minute"], person["sex"], person["hour_known"], person["city"])
            features = J.build_features(chart, as_of=today)
            report = J.build_report(features, "synthetic-audit", selected, "one", person["concern"], person["axis4"])
            if not report.get("cuts"):
                selected_errors[selected + ":empty_cuts"] += 1
        except Exception as exc:
            selected_errors[selected + ":" + type(exc).__name__] += 1
        if (i + 1) % 250 == 0:
            progress = {"completed": i + 1, "total": n, "elapsed_seconds": round(time.perf_counter() - started, 1)}
            (out / "progress.json").write_text(json.dumps(progress), encoding="utf8")
            print(json.dumps(progress), flush=True)
    result = {"synthetic_people": n, "as_of": str(today), "seed": 20260909,
              "scope": "10000 sequential journeys, 500 omnibus reports; no browser behavior or actual payment gateway",
              "elapsed_seconds": round(time.perf_counter() - started, 1),
              "reached": dict(tally.reached), "failures": dict(tally.fail), "failure_examples": tally.sample,
              "structural_observations": dict(tally.stop), "notes": dict(tally.notes),
              "consistency_checks": dict(tally.fit_run), "consistency_failures": dict(tally.fit_bad),
              "consistency_examples": tally.fit_bad_ex, "guard_hits": dict(tally.guard_hit),
              "selected_reader_coverage": dict(coverage), "selected_reader_errors": dict(selected_errors),
              "unknown_hour": sum(not p["hour_known"] for p in pop),
              "uniqueness": {k: {"distinct": len(v), "samples": sum(v.values()),
                                 "largest_group": max(v.values(), default=0)} for k, v in tally.uniq.items()}}
    (out / "engine-10000.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    J.report(tally, n)
    return 1 if tally.fail or tally.fit_bad or tally.guard_hit or selected_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
