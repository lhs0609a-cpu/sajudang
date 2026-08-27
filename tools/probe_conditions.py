"""후보 조건이 인구의 몇 %에 걸리는지 재본다 — 규칙을 정하기 **전에**.

    python tools/probe_conditions.py

★ 왜 필요한가
  규칙을 감으로 쓰면 문턱이 넓어집니다. `가장 약한 오행 <= 1.0` 은
  인구의 88%에 걸렸고, 그래서 삼거리 노파 한 사람이 1순위의 86%를
  가져갔습니다. 재순위(λ)로 덮기 전에 **규칙 자체를 좁혀야** 합니다.

  이 도구는 규칙 파일을 고치지 않습니다. 문턱을 고를 때만 씁니다.
  고른 뒤에는 tools/relay_reach.py 가 확정 도달률을 기록합니다.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine.relay import _fields                 # noqa: E402
from tools import population as POP              # noqa: E402

# (이름, 필드, 연산, 값)
CANDIDATES = [
    ("nopa     약오행 없음",   "el[weak_el]", "==", 0.0),
    ("nopa     약오행 ≤1",     "el[weak_el]", "<=", 1.0),
    ("dongja   길신 0",        "sinsal_good", "==", 0),
    ("yakcho   편차 ≥3.5",     "gap", ">=", 3.5),
    ("yakcho   편차 ≥4.0",     "gap", ">=", 4.0),
    ("wolha    일지충",        "ilji_chung", "==", True),
    ("hunjang  관 ≥2",         "gwan", ">=", 2),
    ("haengsu  재 ≥2",         "jae", ">=", 2),
    ("hongmae  관·재 ≥1",      "gwan_and_jae", ">=", 1),
    ("eunbyeol 중화 아님",     "strength", "!=", "중화"),
    ("hwagyeong 중화",         "strength", "==", "중화"),
    ("paeseon  주도십신 동률", "top_ten_god_tied", "==", True),
    ("jeokhyeol 비겁 ≥2",      "bi", ">=", 2),
    ("jeokhyeol 비겁 ≥3",      "bi", ">=", 3),
    ("monghwa  인성 ≥2",       "inn", ">=", 2),
    ("monghwa  인성 ≥3",       "inn", ">=", 3),
    ("pungun   득령",          "deuk_ryeong", "==", True),
    ("baegun   여름·겨울",     "season", "in", ["여름", "겨울"]),
    ("cheongam 오행 0개 ≥2",   "zero_els", ">=", 2),
    ("cheongam 오행 0개 ≥1",   "zero_els", ">=", 1),
    ("seoyeok  시각 미상",     "hour_known", "==", False),
    ("myeonsang 강오행 ≥4",    "el[strong_el]", ">=", 4.0),
    ("myeonsang 강오행 ≥3",    "el[strong_el]", ">=", 3.0),
    ("yeondam  일지합 ≥1",     "ilji_hap", ">=", 1),
    ("ilgwan   살 ≥1",         "sinsal_bad", ">=", 1),
    ("ilgwan   살 ≥2",         "sinsal_bad", ">=", 2),
    ("sigye    대운 편관/상관/겁재", "daeun_ten_god", "in", ["편관", "상관", "겁재"]),
    ("sigye    대운 미진입",   "daeun_started", "==", False),
    # ── 2차 ──────────────────────────────────────────────
    ("baegun   온도차 ≥3",     "temp_gap", ">=", 3),
    ("baegun   온도차 ≥4",     "temp_gap", ">=", 4),
    ("cheongam 길신 2자리",    "helper_pillars", ">=", 2),
    ("cheongam 길신 3자리",    "helper_pillars", ">=", 3),
    ("pungun   득령+득지",     "deuk_both", "==", True),
    ("ilgwan   대운 2년내",    "daeun_years_left", "<=", 2),
    ("ilgwan   대운 1년내",    "daeun_years_left", "<=", 1),
    ("eunbyeol 신강",          "strength", "==", "신강"),
    ("eunbyeol 신약",          "strength", "==", "신약"),
    ("hongmae  관·재 ≥2",      "gwan_and_jae", ">=", 2),
    ("hunjang  관 ≥3",         "gwan", ">=", 3),
    ("haengsu  재 ≥3",         "jae", ">=", 3),
]

OPS = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    "in": lambda a, b: a in b,
}


def main(n: int = 4000) -> int:
    hit = Counter()
    for f in POP.sample(n):
        v = _fields(f)
        for name, field, op, want in CANDIDATES:
            if OPS[op](v[field], want):
                hit[name] += 1
    print(POP.banner(n) + "\n")
    for name, _, _, _ in CANDIDATES:
        share = hit[name] / n
        bar = "█" * int(share * 40)
        print("%-26s %5.1f%%  %s" % (name, 100 * share, bar))
    return 0


if __name__ == "__main__":
    sys.exit(main())
