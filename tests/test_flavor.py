"""
스무 명이 다르게 말하는가 — 잠금.

★ 어미만으로는 안 갈렸다

  말투 층은 이미 다섯 결로 어미를 갈아 끼우고 있었습니다. 그런데
  문장 뱅크가 **하오체 한 벌**로 쓰여 있어, 하오체를 쓰는 여섯은
  손댄 줄이 0% 였습니다.

★ 안 갈린 진짜 까닭은 **구조**였다

      적혈랑 4,900원   13컷 중 제 몫 **1컷**
      패선생 4,900원   13컷 중 제 몫 **1컷**

  열두 컷이 공통입니다. 공통 컷이 안 갈리면 값싼 캐릭터 둘은 서로
  같은 상품이 됩니다. 컷을 더 주면 값 사다리가 무너지므로
  (tests/test_lens_cuts.py), 대신 **같은 자리를 그 사람 눈으로**
  보게 합니다.

★ 여기서 지키는 것 셋

  ① 스무 명이 서로 다르게 묻는다 (ASK)
  ② 곁말이 그 캐릭터의 호칭을 쓴다 — 「그대」 가 자네 캐릭터에게
     그대로 나가던 자리
  ③ 말버릇이 드물다 — 문장마다 물으면 버릇이 아니라 고장이다
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import flavor                          # noqa: E402
from engine import lens as lens_mod                # noqa: E402
from engine import real                            # noqa: E402
from engine.calendar import build_chart            # noqa: E402
from engine.features import build_features         # noqa: E402
from engine.report import build_report             # noqa: E402

TAG = re.compile(r"<[^>]+>")


def _f():
    return build_features(build_chart(1993, 11, 25, 13, 0, "M", True, "서울"))


def test_스무_명이_서로_다르게_묻는다():
    ids = [l["id"] for l in lens_mod.released()]
    asks = [flavor.ASK.get(i) for i in ids]
    assert all(asks), "묻는 말이 없는 캐릭터: %s" % [
        i for i in ids if not flavor.ASK.get(i)]
    # 같은 말로 묻는 짝이 셋을 넘으면 사람이 안 갈립니다.
    dup = len(asks) - len(set(asks))
    assert dup <= 3, "같은 말로 묻는 캐릭터가 %d명 겹치오" % dup


def test_곁말이_그_캐릭터_호칭을_쓴다():
    """
    ★ 곁말을 「그대」 로 적어 두었더니 자네·아저씨 캐릭터에게 그대로
      나갔습니다. 호칭 층을 태워야 합니다.
    """
    f = _f()
    other = re.compile(r"그대(?!로)")
    for l in lens_mod.released():
        lid = l["id"]
        you = lens_mod.you_of(lid, "", "F")
        if you == "그대":
            continue
        r = build_report(f, "cid", lid, "one" if l.get("price") else "free",
                         "money", None)
        for c in r["cuts"]:
            for m in re.findall(r'<p class="side">(.*?)</p>', c["html"]):
                assert not other.search(TAG.sub("", m)), (lid, m)


def test_말버릇이_드물다():
    """문장마다 물으면 버릇이 아니라 고장입니다."""
    f = _f()
    for lid in ("pungun", "jeokhyeol", "eunbyeol"):
        r = build_report(f, "cid", lid, "all", "money", None)
        tail = flavor.ASK[lid]
        n = sum(c["html"].count(tail) for c in r["cuts"])
        assert n <= 4, "%s 가 한 장에 %d번 물었소" % (lid, n)


def test_곁말이_스무_명_다_있다():
    ids = [l["id"] for l in lens_mod.released()]
    miss = [i for i in ids if len(flavor.SIDE.get(i, ())) != 3]
    assert not miss, "곁말이 없는 캐릭터: %s" % miss


def test_살림의_말_표에_빠진_축값이_없다():
    """
    ★ 열쇠를 제가 지어낸 이름으로 적었더니 한 줄도 안 붙었습니다.

      씨앗이 쓰는 말과 글자 그대로 같아야 합니다. 다르면 조용히
      아무것도 안 나가므로 아무도 모릅니다.
    """
    import json
    d = json.loads((ROOT / "seed" / "lens_cuts.json").read_text("utf-8"))
    miss = {}
    for lid, lst in d["cuts"].items():
        for c in lst:
            for slot in ("a", "b", "c"):
                v = c.get(slot)
                if not isinstance(v, dict):
                    continue
                ax = v.get("axis")
                if ax not in real.TABLES:
                    continue
                for k in v.get("text", {}):
                    if not real.of(ax, k):
                        miss.setdefault(ax, set()).add(k)
    assert not miss, "살림의 말 표에 빠진 축값: %s" % {
        k: sorted(v) for k, v in miss.items()}


def test_별표가_곁말과_비유에_남지_않는다():
    """강조는 <b> 로 씁니다. 별표는 화면에 별표로 보입니다."""
    for rows in flavor.SIDE.values():
        for t in rows:
            assert "**" not in t, t
    for t in real.TEN_GOD.values():
        assert "**" not in t, t
