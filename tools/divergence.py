"""
만세력 앱과 갈리는 자리 — 얼마나 자주, 왜.

    python tools/divergence.py [표본수]

★ 왜 세나

  손님이 다른 만세력과 대 보고 「다르다」 고 할 것입니다. 그때
  「우리가 맞소」 도 「그쪽이 맞소」 도 답이 아닙니다. 갈리는 자리는
  **계산이 아니라 선택**이기 때문입니다.

  답을 하려면 두 가지를 알아야 합니다 —
    ① 어디서 갈리는가 (무엇을 다르게 정했는가)
    ② 얼마나 자주 걸리는가 (백 명 중 몇인가)

  ②를 모르면 「드물다」 고도 「흔하다」 고도 말할 수 없습니다.

★ 우리가 고른 것 (engine/calendar.py)

    ZI_POLICY   = 조자시     밤 11시 이후는 **다음 날**로 넘긴다
    JIEQI_BASIS = corrected  절입은 **진태양시로 고친 시각**과 견준다

  둘 다 명리에서 쓰는 정식 유파입니다. 다르게 정한 집도 정식입니다.
  그래서 「틀렸다」 가 아니라 「다르게 골랐다」 입니다.
"""
from __future__ import annotations

import random
import sys
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import calendar as cal               # noqa: E402
from engine.calendar import build_chart          # noqa: E402


def _flip(fn, **kw):
    """상수를 잠깐 바꿔 다시 세운다 — 무엇이 달라지는지 보려고."""
    old = {k: getattr(cal, k) for k in kw}
    for k, v in kw.items():
        setattr(cal, k, v)
    try:
        return fn()
    finally:
        for k, v in old.items():
            setattr(cal, k, v)


def main() -> int:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    rng = random.Random(20260902)

    zi_hit = 0          # 조자시/야자시로 갈리는 사람
    jq_hit = 0          # 절입 기준으로 갈리는 사람
    # ★ 여태 안 세던 자리. 셋 중 **가장 흔합니다.**
    #   서울은 해가 남중하는 때가 표준시보다 32분 늦고, 시지 경계는 두
    #   시간마다 옵니다. 그래서 경계 뒤 32분 안에 난 사람은 보정을 쓰는
    #   집과 안 쓰는 집이 갈립니다.
    lon_hit = 0         # 고을 보정(진태양시)으로 갈리는 사람
    both = Counter()
    made = 0

    for _ in range(n):
        y = rng.randint(1950, 2010)
        m = rng.randint(1, 12)
        d = rng.randint(1, 28)
        h = rng.randint(0, 23)
        mi = rng.randint(0, 59)
        sex = rng.choice("FM")
        try:
            base = build_chart(y, m, d, h, mi, sex, True)
        except Exception:                        # noqa: BLE001
            continue
        made += 1
        key = lambda c: " ".join(p.gz for p in c.pillars)   # noqa: E731

        try:
            other_zi = _flip(lambda: build_chart(y, m, d, h, mi, sex, True),
                             ZI_POLICY="야자시")
            if key(other_zi) != key(base):
                zi_hit += 1
                both["조자시"] += 1
        except Exception:                        # noqa: BLE001
            pass

        try:
            other_jq = _flip(lambda: build_chart(y, m, d, h, mi, sex, True),
                             JIEQI_BASIS="standard")
            if key(other_jq) != key(base):
                jq_hit += 1
                both["절입기준"] += 1
        except Exception:                        # noqa: BLE001
            pass

        try:
            other_lon = _flip(lambda: build_chart(y, m, d, h, mi, sex, True),
                              HOUR_BASIS="standard")
            if key(other_lon) != key(base):
                lon_hit += 1
                both["고을보정"] += 1
        except Exception:                        # noqa: BLE001
            pass

    print("=" * 76)
    print("  만세력 앱과 갈릴 수 있는 자리 — 표본 %d명" % made)
    print("=" * 76)
    print()
    print("  우리가 고른 것")
    print("    ZI_POLICY   = %s" % cal.ZI_POLICY)
    print("    JIEQI_BASIS = %s" % cal.JIEQI_BASIS)
    print("    HOUR_BASIS  = %s" % cal.HOUR_BASIS)
    print()
    print("  %-14s %6s   %s" % ("갈리는 까닭", "사람", "백 명 중"))
    print("  " + "-" * 52)
    if made:
        print("  %-14s %6d   %.1f명" % ("밤 11시대 출생", zi_hit,
                                       100.0 * zi_hit / made))
        print("  %-14s %6d   %.1f명" % ("절입 언저리 출생", jq_hit,
                                       100.0 * jq_hit / made))
        print("  %-14s %6d   %.1f명" % ("고을 보정 언저리", lon_hit,
                                       100.0 * lon_hit / made))
        tot = zi_hit + jq_hit + lon_hit
        print("  " + "-" * 52)
        print("  %-14s %6d   %.1f명" % ("합계(겹칠 수 있음)", tot,
                                       100.0 * tot / made))
    print()
    print("  ※ 「틀렸다」 가 아니라 「다르게 골랐다」 입니다. 둘 다")
    print("    명리에서 쓰는 정식 유파라, 어느 쪽도 상대를 못 이깁니다.")
    print("-" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
