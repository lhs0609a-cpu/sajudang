"""도구들이 같은 인구를 보게 하는 자리.

★ 왜 한 곳으로 모으는가
  릴레이 도달률·조건 문턱·쏠림을 각각 다른 표본으로 재면 숫자를 나란히
  놓고 비교할 수 없습니다. 실제로 시각 미상 비율이 세 도구에 따로
  박혀 있었습니다.

★ 시각 미상 비율은 가정값이 아니라 실측이어야 합니다
  서역 별지기 규칙이 `hour_known == False` 를 보므로, 이 비율이 곧 그
  캐릭터의 도달률이고 추천 배분이 여기에 직접 걸립니다.
  charts 테이블이 쌓이면 실측으로 바뀝니다. **어느 쪽을 썼는지 반드시
  찍습니다** — 지어낸 값을 실측처럼 보이게 두면 안 됩니다.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "services" / "api") not in sys.path:
    sys.path.insert(0, str(ROOT / "services" / "api"))

from engine.calendar import build_chart          # noqa: E402
from engine.features import build_features       # noqa: E402

SEED = 20260826            # 값이 흔들리지 않게 시드를 박습니다

# 표본이 이만큼 쌓이기 전에는 실측이라 부르지 않습니다.
MIN_REAL_SAMPLE = 200

# 실데이터가 없을 때 쓰는 가정값.
HOUR_UNKNOWN_ASSUMED = 0.15

BIRTH_YEARS = (1955, 2010)


def hour_unknown_share() -> tuple[float, str]:
    """(비율, 출처). charts 테이블이 충분히 쌓였으면 실측, 아니면 가정값."""
    try:
        import db
        if not db.HAS_DB:
            return HOUR_UNKNOWN_ASSUMED, "가정값 (DB 없음)"
        import models
        from sqlalchemy import func, select
        with db.session() as ses:
            total = ses.scalar(
                select(func.count()).select_from(models.Chart)) or 0
            if total < MIN_REAL_SAMPLE:
                return (HOUR_UNKNOWN_ASSUMED,
                        "가정값 (실데이터 %d건뿐 · %d건부터 실측)"
                        % (total, MIN_REAL_SAMPLE))
            unknown = ses.scalar(
                select(func.count()).select_from(models.Chart)
                .where(models.Chart.hour_known.is_(False))) or 0
        return unknown / total, "실측 %d건" % total
    except Exception as e:            # DB 가 없거나 못 붙어도 도구는 계속 돕니다
        return HOUR_UNKNOWN_ASSUMED, "가정값 (%s)" % type(e).__name__


def sample(n: int, seed: int = SEED, share: float | None = None):
    """인구 표본을 Features 로 흘려보낸다. 도구 셋이 같은 것을 봅니다."""
    if share is None:
        share, _ = hour_unknown_share()
    rng = random.Random(seed)
    for _ in range(n):
        known = rng.random() >= share
        yield build_features(build_chart(
            rng.randint(*BIRTH_YEARS), rng.randint(1, 12), rng.randint(1, 28),
            rng.randint(0, 23) if known else None,
            rng.randint(0, 59) if known else None,
            rng.choice("FM"), known))


def banner(n: int) -> str:
    share, src = hour_unknown_share()
    return "표본 %d명 · 시각 미상 %.1f%% — %s" % (n, 100 * share, src)
