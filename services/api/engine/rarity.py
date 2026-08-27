"""
희소도 — 이 배치가 인구에서 몇 명인가.

★ 왜 생겼는가
  바깥에서 찾은 것 중 가장 큰 지렛대가 **반증 가능한 구체성**이었습니다.
  바넘 문장은 틀릴 수가 없어서 '맞다' 는 나와도 '소름 돋는다' 는 안 나옵니다.
  사주는 **셀 수 있는 물건**이라, 여덟 글자의 배치가 인구에서 몇 %인지를
  지어내지 않고 셀 수 있습니다. 그게 이 파일입니다.

★ 지어내지 않습니다 — 셉니다
  `tools/make_rarity.py` 가 인구 표본을 한 번 흘려보내 seed/rarity.json 을
  만듭니다. 요청 때 4만 명을 돌릴 수는 없으니 **미리 세어 표로 둡니다.**
  릴레이 재순위가 도달률을 미리 재 두는 것과 같은 방식입니다.

★ 골라 담지 않습니다
  사람마다 여러 자리를 재서 **가장 드문 것만 뽑아 말하면** 누구나 드물어
  집니다. 그건 거짓말입니다. 그래서 **축 넷을 미리 정해 놓고** 그 사람의
  값이 무엇이든 **그 칸의 비율을 그대로** 말합니다. 흔하면 흔하다고 합니다.
      빈 기운 · 힘 · 곁을 돕는 자리 · 곁자리
  이 넷은 이 집이 이미 말하던 것들입니다. 새로 만든 잣대가 아닙니다.

★ 적중률이 아닙니다
  '몇 %가 맞았다' 가 아니라 '이 배치가 몇 명이다' 입니다. 세는 값이라
  검증 가능하고, 그래서 절대 규칙 2 와 부딪히지 않습니다.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

SEED = Path(__file__).resolve().parents[3] / "seed"

# 표본에서 이만큼은 나와야 '1만 명에 몇 명' 으로 환산합니다.
# 그 아래는 환산하지 않고 **표본 그대로** 말합니다 — 적은 수를 늘려 잡으면
# 없는 정밀도를 지어내는 것이 됩니다.
MIN_FOR_SCALE = 40


class RarityError(KeyError):
    """표에 없는 배치. 지어내지 않고 터뜨린다."""


# ══════════════════════════════════════════════════════════
# 배치 열쇠 — 축 넷. 미리 정해 두고 바꾸지 않습니다.
# ══════════════════════════════════════════════════════════
def zero_band(f) -> str:
    n = sum(1 for v in f.elements.values() if v == 0)
    return {0: "없음", 1: "하나"}.get(n, "둘이상")


def helper_band(f) -> str:
    n = len({h["pillar"] for h in f.helpers})
    if n == 0:
        return "없음"
    return "하나둘" if n <= 2 else "셋이상"


def ilji_state(f) -> str:
    if f.ilji_chung and f.ilji_hap:
        return "충합"
    if f.ilji_chung:
        return "충"
    if f.ilji_hap:
        return "합"
    return "고요"


AXES = (
    ("zero", zero_band),
    ("strength", lambda f: f.strength),
    ("helper", helper_band),
    ("ilji", ilji_state),
)


def key_of(f) -> str:
    return "|".join(fn(f) for _, fn in AXES)


@lru_cache(maxsize=1)
def table() -> dict:
    raw = json.loads((SEED / "rarity.json").read_text("utf-8"))
    return {k: v for k, v in raw.items() if k != "_"}


def look(f) -> dict:
    """
    이 사람의 배치가 인구에서 얼마나 되는가.

    돌려주는 것
        key        배치 열쇠
        count      표본에서 나온 수
        sample     표본 크기
        share      비율
        per10k     1만 명당 (표본이 얇으면 None)
        band       "아주드묾" | "드묾" | "적잖음" | "흔함"
        words      사람이 읽는 말 (숫자를 부풀리지 않은 것)
    """
    t = table()
    key = key_of(f)
    total = t["sample"]
    cell = t["cells"].get(key)

    # ★ 표에 없는 배치는 **오류가 아닙니다.**
    #   축 넷을 곱하면 백여덟 칸이 나오는데 표본 4만에서 안 나오는 칸이
    #   있습니다. 그건 '모른다' 가 아니라 '4만을 흘려보내도 안 나왔다' 는
    #   뜻이고, 그 자체가 가장 드문 답입니다. 터뜨리지 않고 그대로 말합니다.
    #   (없다고 말하지는 않습니다 — 표본에 없었다고만 말합니다.)
    if cell is None:
        return {"key": key, "count": 0, "sample": total, "share": 0.0,
                "per10k": None, "band": "표본에없음",
                "words": "표본 %s명 가운데 한 명도" % format(total, ","),
                "parts": dict(zip((a for a, _ in AXES), key.split("|"))),
                "ilju": ilju(f)}

    n = cell["n"]
    share = n / total
    per10k = round(share * 10000) if n >= MIN_FOR_SCALE else None

    if share < 0.005:
        band = "아주드묾"
    elif share < 0.02:
        band = "드묾"
    elif share < 0.08:
        band = "적잖음"
    else:
        band = "흔함"

    if per10k is None:
        words = "표본 %s명 가운데 %d명" % (format(total, ","), n)
    else:
        words = "1만 명에 %s명" % format(per10k, ",")

    return {"key": key, "count": n, "sample": total, "share": share,
            "per10k": per10k, "band": band, "words": words,
            "parts": dict(zip((a for a, _ in AXES), key.split("|"))),
            "ilju": ilju(f)}


def ilju(f) -> dict:
    """
    일주 예순 갑자 가운데 하나. 누구나 하나씩 가집니다.

    ★ 배치가 흔한 사람에게도 **셀 수 있는 자리**를 하나 남깁니다.
      고르는 것이 아니라 그 사람의 일주를 그대로 세는 것이라,
      드문 쪽만 골라 담는 일이 생기지 않습니다.
    """
    gz = f.pillars[2]["gz"]
    t = table()
    cell = (t.get("ilju") or {}).get(gz)
    if cell is None:
        raise RarityError("표에 없는 일주입니다: %r" % (gz,))
    n, total = cell["n"], t["sample"]
    return {"gz": gz, "count": n, "sample": total, "share": n / total,
            "per10k": round(n / total * 10000),
            "words": "1만 명에 %s명" % format(round(n / total * 10000), ",")}


def is_stale() -> bool:
    """표가 지금 축과 안 맞으면 True. 축을 고치고 표를 안 다시 만든 경우."""
    return table().get("axes") != [a for a, _ in AXES]
