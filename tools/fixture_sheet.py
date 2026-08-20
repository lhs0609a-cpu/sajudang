"""
회귀 케이스 대조표 — 기존 만세력 앱과 눈으로 맞춰 보기 위한 표.

    python tools/fixture_sheet.py            # 화면에 출력
    python tools/fixture_sheet.py sheet.md   # 파일로 저장

'우리 산출' 열은 참고용입니다. 그대로 베껴 넣지 마세요.
기대값은 **기존 만세력 앱 2종 이상**에서 직접 읽어 채워야 의미가 있습니다.
그러라고 이 표는 입력 조건을 앱에 그대로 넣기 좋은 형태로 뽑습니다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine.calendar import build_chart      # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "charts.json"


def main() -> int:
    if not FIXTURES.exists():
        print("charts.json 이 없습니다. python tools/make_fixtures.py 먼저 실행하세요.")
        return 1
    cases = json.loads(FIXTURES.read_text(encoding="utf-8"))

    lines = [
        "# 회귀 케이스 대조표",
        "",
        "`기대값` 열을 기존 만세력 앱 2종 이상에서 읽어 채우고,",
        "`tests/fixtures/charts.json` 의 `expected` 에 옮겨 적으세요.",
        "",
        "| id | 설명 | 입력 | 우리 산출 | 대운수 | 기대값 |",
        "|---|---|---|---|---|---|",
    ]
    for c in cases:
        i = c["input"]
        when = ("%04d-%02d-%02d %s · %s · %s"
                % (i["year"], i["month"], i["day"],
                   ("%02d:%02d" % (i["hour"], i["minute"]))
                   if i.get("hour_known", True) else "시각미상",
                   "여" if i["sex"] == "F" else "남",
                   i.get("city", "서울")))
        try:
            ch = build_chart(i["year"], i["month"], i["day"], i["hour"],
                             i["minute"], i["sex"],
                             hour_known=i.get("hour_known", True),
                             city=i.get("city", "서울"))
            got = " ".join(p.gz for p in ch.pillars)
            if not ch.hour_known:
                got += " ◇◇"
            daeun = str(ch.daeun[0].start_age)
        except Exception as e:                       # noqa: BLE001
            got, daeun = "ERROR: %s" % e, "-"
        lines.append("| %s | %s | %s | %s | %s | |"
                     % (c["id"], c["note"], when, got, daeun))

    out = "\n".join(lines)
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(out, encoding="utf-8")
        print("저장: %s" % sys.argv[1])
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
