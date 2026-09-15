"""Recheck the obsolete STAB_GAN assertion, preserving original audit evidence."""
import json
from datetime import date
from pathlib import Path
import journey_sim as J

out = Path(__file__).resolve().parents[1] / "out/audit-20260909/hook-branch-10000.json"
pop = J.people(10000, seed=20260909)
result = dict(samples=10000, blade_branch=0, fallback_branch=0, failures=0)
for i, p in enumerate(pop):
    concern = J.CONCERNS[(i // 20) % len(J.CONCERNS)]
    chart = J.build_chart(p["year"], p["month"], p["day"], p["hour"], p["minute"], p["sex"], p["hour_known"], p["city"])
    f = J.build_features(chart, as_of=date(2026, 9, 9))
    hook = J.bank_mod.build_hook(f, concern, p["axis4"], "", "그대")
    blade = J.bank_mod.count_blade(f, concern)
    result["blade_branch" if blade else "fallback_branch"] += 1
    expected = "<b>%s</b> 일간" % f.day_gan if blade else J.bank_mod.bank()["STAB_GAN"][f.day_gan]
    result["failures"] += expected not in hook[0]["html"]
out.write_text(json.dumps(result, indent=2), encoding="utf8")
print(json.dumps(result))
