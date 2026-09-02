"""
손님이 알아들을 수 있는가 — 잠금.

★ 손님이 한 말

  "너무 단어들이 추상적이라 이해가 안돼. 비유를 해서 다 쉽게 풀이해야
  한다. 모든 페이지 모든 캐릭터 전부."

★ 뜻만 바꿔 말한 것은 푼 게 아니다

  풀이 층은 이미 있었는데 적힌 것이 이랬습니다 —

      겁재 = 나와 겨루는 힘
      용신 = 모자란 것을 채워 줄 기운

  쉰넷 중 그림이 그려지는 것은 둘(4%)뿐이었습니다. 「힘」 「기운」
  「자리」 는 명리의 말이지 살림의 말이 아닙니다. 모르는 말을 모르는
  말로 바꾸면 손님은 읽고 나서도 여전히 모릅니다.

★ 비유는 구체적이되 단정하지 않는다

  「양인이 있으니 다치오」 는 신살로 사고를 단정하는 말이라 금지입니다
  (docs/14 §7 · docs/11). 「날이 선 자리요 — 벨 힘이 있는 만큼 제 손도
  베오」 는 자리를 가리키는 말이라 됩니다. 쉽게 만들다가 이 선을 넘는
  것이 가장 흔한 사고라, 여기서 셉니다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import lens as lens_mod                # noqa: E402
from engine import terms                           # noqa: E402
from engine.calendar import build_chart            # noqa: E402
from engine.features import build_features         # noqa: E402
from engine.report import build_report             # noqa: E402

TAG = re.compile(r"<[^>]+>")

# 손에 잡히는 말 — 살림에서 쓰는 것
HAND = re.compile(
    r"솥|밥|삯|장터|마감|어머니|나무|바람|뿌리|쇠|불|물|겨울|연장|"
    r"그릇|골방|또래|동무|감투|살림|눈|손|발밑|계절|해|시계|판|눈금")

# 단정하는 말 — 어떤 비유에도 못 들어갑니다
BANNED = re.compile(r"다치|병들|앓|죽|이혼|헤어지|사고|망하|대박|사라|팔라")


def test_어려운_말에_전부_비유가_붙는다():
    """뜻만 있고 그림이 없으면 푼 게 아닙니다."""
    bare = [k for k in terms.MEANING if not terms.PICTURE.get(k)]
    assert not bare, "비유 없는 말 %d가지: %s" % (len(bare), bare[:8])


def test_비유가_단정하지_않는다():
    """docs/14 §7 · docs/11 — 병·사고·이혼·투자를 단정하지 않습니다."""
    for k, v in terms.PICTURE.items():
        m = BANNED.search(v)
        assert not m, "%s — 단정하는 말 「%s」: %s" % (k, m.group(0), v)


def test_비유의_절반은_손에_잡히는_말이다():
    """
    「힘」 「기운」 「자리」 만으로 된 비유는 그림을 못 그립니다.

    전부를 요구하지는 않습니다 — 「순행: 앞으로 나아가며 도는 것」
    처럼 살림의 말이 필요 없는 것도 있습니다.
    """
    hand = sum(1 for v in terms.PICTURE.values() if HAND.search(v))
    ratio = hand / len(terms.PICTURE)
    assert ratio >= 0.5, "손에 잡히는 비유가 %.0f%% 뿐이오" % (100 * ratio)


def test_비유가_화면에_실제로_붙는다():
    """표에만 있고 화면에 안 나오면 없는 것과 같습니다."""
    f = build_features(build_chart(1993, 11, 25, 13, 0, "M", True, "서울"))
    r = build_report(f, "cid", "pungun", "all", "money", None)
    boxed = [c for c in r["cuts"] if 'class="gls"' in c["html"]]
    assert boxed, "비유 상자가 한 컷에도 안 붙었소"


def test_비유가_그_캐릭터_목소리로_말한다():
    """
    ★ 상자만 하오체로 남던 자리입니다.

      말투를 갈아 끼운 **뒤에** 붙였더니 합쇼체 캐릭터의 리포트에서
      이 줄만 하오체로 남아, 한 화면 안에서 말투가 갈렸습니다.
    """
    f = build_features(build_chart(1993, 11, 25, 13, 0, "M", True, "서울"))
    for lid in ("sigye", "yeondam", "haengsu"):    # 합쇼체 셋
        assert lens_mod.view(lid)["voice"] == "hapsyo"
        r = build_report(f, "cid", lid, "all", "money", None)
        for c in r["cuts"]:
            m = re.search(r'<div class="gls">.*?</div>', c["html"], re.S)
            if not m:
                continue
            plain = TAG.sub(" ", m.group(0))
            left = re.findall(r"[가-힣]{2,}(?<!십시)[오소](?=[\s.,!?…—·]|$)",
                              plain)
            assert not left, "%s 의 비유가 하오체로 남았소: %s" % (lid, left[:3])


def test_별표가_글로_새지_않는다():
    """
    ★ 근거 줄은 **글자 그대로** 그려집니다.

      `<span className="src">{seg.source}</span>` 이라 React 가
      이스케이프합니다. 강조하려고 별표를 쓰면 별표가 그대로 보입니다 —
      「인구에서 몇 명인지를 **센** 것이오」 가 화면에 그렇게 나갔습니다.
    """
    f = build_features(build_chart(1993, 11, 25, 13, 0, "M", True, "서울"))
    for lid in ("pungun", "sigye"):
        r = build_report(f, "cid", lid, "all", "money", None)
        for c in r["cuts"]:
            assert "**" not in (c.get("source") or ""), c["source"]
