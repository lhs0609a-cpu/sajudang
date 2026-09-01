# -*- coding: utf-8 -*-
"""
서버와 화면이 같은 사람을 말하는가.

★ 왜 지키나

  스무 사람의 정보가 두 곳에 있다 — `seed/lenses.json`(서버)과
  `apps/web/lib/lenses.ts`(화면). 둘이 갈리면 서버가 판단한 것과
  손님이 본 것이 다르다.

  실제로 **스무 명 중 열여덟 명**이 `archetype` 이 달랐다. 까닭은
  이름 하나에 다른 것 둘을 담았기 때문이다 —

      seed   archetype "위험한 매력"   ← 원형. 그림을 그릴 때 쓴다
      화면   archetype "붉은 눈"      ← 별칭. 카드에 적히는 짧은 말

  같은 이름에 다른 것을 담으면 언젠가 하나를 보고 다른 하나를 고친다.
  이름을 갈랐고(epithet · archetype), 여기서 다시 안 갈리게 지킨다.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seed" / "lenses.json"
TS = ROOT / "apps" / "web" / "lib" / "lenses.ts"


def _seed() -> dict:
    return {l["id"]: l for l in json.loads(SEED.read_text(encoding="utf-8"))}


def _ts() -> dict:
    src = TS.read_text(encoding="utf-8")
    out = {}
    for line in src.splitlines():
        m = re.search(r'\{ id: "(\w+)",', line)
        if not m:
            continue
        row = dict(re.findall(r'(\w+): "([^"]*)"', line))
        num = dict(re.findall(r'(\w+): (\d+)', line))
        row.update({k: int(v) for k, v in num.items()})
        out[m.group(1)] = row
    return out


# 두 곳이 **반드시** 같아야 하는 것
MUST_MATCH = ("name", "hanja", "group", "price", "specialty", "archetype")


def test_both_sources_list_the_same_people():
    a, b = set(_seed()), set(_ts())
    assert a == b, "한쪽에만 있는 사람: %s" % sorted(a ^ b)


def test_fields_agree():
    seed, ts = _seed(), _ts()
    bad = []
    for k, s in seed.items():
        t = ts[k]
        for f in MUST_MATCH:
            if f not in s or f not in t:
                bad.append("%s.%s 가 한쪽에 없다" % (k, f))
            elif str(s[f]) != str(t[f]):
                bad.append("%s.%s  seed=%s  화면=%s" % (k, f, s[f], t[f]))
    assert not bad, "서버와 화면이 다르다:\n  " + "\n  ".join(bad)


def test_epithet_and_archetype_are_different_things():
    """
    별칭과 원형은 다른 것이다. 화면에는 별칭이, 그림 발주에는 원형이
    간다. 하나로 합치면 다시 갈린다.
    """
    ts = _ts()
    for k, t in ts.items():
        assert "epithet" in t, "%s 에 별칭이 없다" % k
        assert "archetype" in t, "%s 에 원형이 없다" % k
    same = [k for k, t in ts.items() if t["epithet"] == t["archetype"]]
    # 우연히 같은 사람이 한둘 있을 수는 있지만 전부 같으면 안 갈린 것이다
    assert len(same) < len(ts) // 2, "별칭과 원형이 사실상 같다: %s" % same


def test_every_archetype_has_art_direction():
    """원형마다 그림 말이 있어야 초상을 발주할 수 있다."""
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    import char_sheet

    missing = sorted({l["archetype"] for l in _seed().values()
                      if l["archetype"] not in char_sheet.LOOK})
    assert not missing, "그림 말이 없는 원형: %s" % missing
