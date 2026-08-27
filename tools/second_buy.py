"""두 번째 결제가 '진짜 다른 상품' 인지 잰다.

    python tools/second_buy.py

★ 무엇을 보는가
  같은 사람이 캐릭터를 바꿔 또 샀을 때 **새로 보는 문장이 몇 개인가.**

  전에는 순서만 100% 달라지고 새 문장은 평균 +0.29개였습니다.
  추천을 아무리 손봐도 그랬습니다 — 여덟 글자는 하나뿐이라
  **입력이 같으면 리포트는 순서만 바뀝니다.**

  docs/07 §결합 축이 이미 적어 둔 대로:
      입력 데이터가 다를 때만 진짜 다른 상품입니다.

  그래서 추가 입력을 붙였습니다. 이 도구가 그게 실제로 값을 하는지
  봅니다 — 추가 입력 없이 vs 있이.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import lens as LENS                  # noqa: E402
from engine.report import build_report           # noqa: E402
from tools import population as POP              # noqa: E402

_tag = re.compile(r"<[^>]*>")

# 화면이 실제로 받아 넣을 법한 값. 캐릭터마다 다른 것을 받습니다.
SAMPLE_EXTRAS = {
    "partner": {"year": 1990, "month": 8, "day": 3, "hour": 14,
                "minute": 0, "sex": "M", "hour_known": True},
    "context": {"situation": "job", "stance": "hold", "since_months": 8},
    "blood": {"type": "A"},
    "image": {"pick": "door"},
    "cards": {"picks": ["gil", "mun", "san"]},
}


def sentences(rep) -> set:
    out = set()
    for c in rep["cuts"]:
        for line in _tag.sub("\n", c["html"]).split("\n"):
            line = line.strip()
            if len(line) > 8:
                out.add(line)
    return out


def run(n: int = 300) -> int:
    lenses = [l["id"] for l in LENS.all_lenses()]
    first = "pungun"                      # 첫 캐릭터는 늘 같다고 두고
    others = [l for l in lenses if l != first]

    print(POP.banner(n))
    print("첫 캐릭터 %s → 두 번째 캐릭터 %d명\n" % (first, len(others)))

    tot_plain = tot_extra = pairs = 0
    order_changed = 0
    for f in POP.sample(n):
        base = build_report(f, "cid", first, "all", "love", "INFP")
        base_s = sentences(base)
        base_order = [c["id"] for c in base["cuts"]]
        for lid in others:
            need = LENS.required_input(lid)
            plain = build_report(f, "cid", lid, "all", "love", "INFP")
            tot_plain += len(sentences(plain) - base_s)
            payload = ({need: SAMPLE_EXTRAS[need]}
                       if need in SAMPLE_EXTRAS else None)
            withx = build_report(f, "cid", lid, "all", "love", "INFP", payload)
            tot_extra += len(sentences(withx) - base_s)
            if [c["id"] for c in plain["cuts"]] != base_order:
                order_changed += 1
            pairs += 1

    print("두 번째 리포트에서 **새로 보는 문장** (첫 리포트에 없던 것)")
    print("  추가 입력 없이   평균 %5.2f개" % (tot_plain / pairs))
    print("  추가 입력 있이   평균 %5.2f개" % (tot_extra / pairs))
    print("  차이            %+5.2f개" % ((tot_extra - tot_plain) / pairs))
    print()
    print("순서가 바뀐 비율  %.1f%%" % (100 * order_changed / pairs))
    print()
    missing = LENS.missing_inputs()
    print("추가 입력이 아직 없는 캐릭터 %d명" % len(missing))
    for m in missing:
        print("  %-11s %-10s %s" % (m["lens_id"], m["input"], m["reason"]))
    return 0


if __name__ == "__main__":
    N = 300
    if "-n" in sys.argv:
        N = int(sys.argv[sys.argv.index("-n") + 1])
    sys.exit(run(N))
