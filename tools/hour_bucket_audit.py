"""
때 칸 감사 — **네 시간짜리 칸이 시주를 얼마나 틀리게 하는가.**

    python tools/hour_bucket_audit.py

★ 무슨 일이 있었나

  손님이 1993-11-25 15시 55분생인데 화면이 **13시**로 셈했습니다.

      15:55 로 세우면   癸酉 癸亥 庚戌 甲申    나무 1 · 불 0
      13:00 으로 세우면 癸酉 癸亥 庚戌 壬午    나무 0 · 불 1

  여덟 글자 중 둘이 다릅니다. 그래서 **없던 불이 생기고 있던 나무가
  사라졌습니다.** 손님이 쓰던 만세력과 안 맞은 것은 계산이 아니라
  입력이었습니다.

  까닭은 a4 화면의 여섯 칸입니다. 「한낮 11–15」 같은 네 시간짜리
  칸을 고르면 한복판 시각(13시)이 적혔습니다. 시주는 두 시간마다
  바뀌므로 네 시간 칸은 **두 시주에 걸칩니다.**

★ 이 도구가 세는 것

  각 칸의 범위를 5분 간격으로 훑어, 한복판 시각으로 셈한 시주와
  실제 시주가 다른 비율을 냅니다. 진태양시 보정 뒤 기준입니다 —
  서울은 약 32분 뒤로 밀리므로 경계가 칸과 어긋납니다.

★ 왜 남겨 두나

  칸을 아주 없애지는 않았습니다. 정말 대강만 아는 사람이 있고,
  그 사람에게는 여섯 칸이 「모르오」보다 낫습니다. 다만 **얼마나
  틀리는지를 알고 두는 것**과 모르고 두는 것은 다릅니다.
  이 숫자가 화면 문구의 근거입니다.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine.calendar import build_chart          # noqa: E402

# apps/web/app/page.tsx 의 HOURS 와 같아야 합니다.
BUCKETS = [
    ("새벽", "03–07", 5, 3, 7),
    ("아침", "07–11", 9, 7, 11),
    ("한낮", "11–15", 13, 11, 15),
    ("저녁", "15–19", 17, 15, 19),
    ("밤", "19–23", 21, 19, 23),
    ("자정 무렵", "23–03", 0, 23, 27),
]

# 서로 다른 날 몇 개를 봅니다. 시두법은 일간에 따라 달라지므로
# 한 날만 보면 우연에 속습니다.
DAYS = [(1993, 11, 25), (1997, 3, 22), (1982, 7, 8), (2003, 9, 17),
        (1966, 5, 5)]
CITY = "서울"
STEP_MIN = 5


def hour_gz(y, m, d, h, mi):
    return build_chart(y, m, d, h % 24, mi, "M",
                       hour_known=True, city=CITY).pillars[3].gz


def main() -> int:
    print("때 칸 감사 — 네 시간 칸을 한복판 시각으로 뭉갤 때")
    print("날 %d개 · 고을 %s · %d분 간격 · 진태양시 보정 뒤 기준"
          % (len(DAYS), CITY, STEP_MIN))
    print("=" * 68)

    tot_bad = tot = 0
    rows = []
    for name, rng, mid, a, b in BUCKETS:
        bad = n = 0
        for (y, m, d) in DAYS:
            want = hour_gz(y, m, d, mid, 0)
            for t in range(a * 60, b * 60, STEP_MIN):
                n += 1
                if hour_gz(y, m, d, t // 60, t % 60) != want:
                    bad += 1
        tot_bad += bad
        tot += n
        rows.append((name, rng, mid, bad * 100.0 / n))

    for name, rng, mid, pct in rows:
        bar = "█" * int(pct / 4)
        print("  %-8s %-7s → %02d시   틀림 %5.1f%%  %s" % (name, rng, mid, pct, bar))

    rate = tot_bad * 100.0 / tot
    print("-" * 68)
    print("  칸을 고른 사람이 틀린 시주를 받을 확률   %.1f%%" % rate)
    print("""
  시주가 틀리면 여덟 글자 중 **둘**이 틀립니다. 오행 개수가 바뀌고,
  없던 기운이 생기거나 있던 기운이 사라집니다. 그러면 용신도 신강약도
  달라집니다 — 리포트 전체가 다른 사람 것이 됩니다.

  그래서 a4 는 **시·분을 먼저** 묻습니다. 칸은 접어 두고, 펼치면
  이 숫자를 그 자리에 적습니다.""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
