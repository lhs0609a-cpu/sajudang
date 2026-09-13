"""Unknown birth time: compare every supported clock minute without filling the natal hour.

Scenarios are never returned as the person's chart. The result records which
rule conditions survive all minutes, not a probability over birth times.
"""
from functools import lru_cache

from .calendar import build_chart
from .features import _element_table, _strength, _ten_gods, _yongsin
from .constants import TEN_GOD_GROUP
from .interpretation import content


@lru_cache(maxsize=128)
def compare(year, month, day, sex, city):
    stable, possible, strengths, yongsins, day_pillars = None, set(), set(), set(), set()
    variants, unsupported = set(), 0
    for minute in range(24 * 60):
        try:
            chart = build_chart(year, month, day, minute // 60, minute % 60, sex, city=city)
        except ValueError:
            unsupported += 1
            continue
        signature = tuple(p.gz for p in chart.pillars)
        if signature in variants:
            continue
        variants.add(signature)
        el = _element_table(chart.pillars)
        strength = _strength(el, chart.day_gan, chart.month_pillar.ji, chart.day_ji)[0]
        gods, _ = _ten_gods(chart.pillars, chart.day_gan)
        groups = {TEN_GOD_GROUP[god] for god, count in gods.items() if count}
        rules = {rule["id"] for rule in content()["rules"] if set(rule["groups"]) <= groups}
        stable = rules if stable is None else stable & rules
        possible |= rules
        strengths.add(strength)
        yongsins.add(_yongsin(el, chart.day_gan, strength))
        day_pillars.add(chart.day_pillar.gz)
    return {"version": 1, "basis": "입력 날짜의 시계 시각 00:00~23:59를 1분 단위로 비교",
        "checked_minutes": 1440 - unsupported, "unsupported_minutes": unsupported,
        "chart_variants": len(variants), "stable_rules": sorted(stable or []),
        "variable_rules": sorted(possible - (stable or set())), "strengths": sorted(strengths),
        "yongsins": sorted(yongsins), "day_pillars": sorted(day_pillars),
        "note": "가능한 시각에서 규칙의 성립 여부만 비교했습니다. 실제 시주를 채우거나 출생 시각의 확률을 추정하지 않습니다."}
