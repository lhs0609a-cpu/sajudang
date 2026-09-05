# -*- coding: utf-8 -*-
"""
한 화면에 **두 사람이 서 있지 않은가.**

★ 손님이 짚은 것 (2026-09-05)

  "풍운도령이 나와야 하는데 백운선사가 왜 나와"

★ 무엇이 어긋났나

  `Meet` 은 `lens` 를 안 받으면 세션의 `cur` 를 씁니다. 그런데 `cur`
  는 **저장되는 값**입니다 (lib/store 의 persist). 그러니 —

      처음 온 사람   cur = DEFAULT_LENS = pungun  → 도령이 맞이함
      다시 온 사람   cur = 지난번에 읽은 사람      → 그 사람이 맞이함

  a2 화면은 바로 아래 대사가 `<Say who="도령" lens="pungun">` 이라,
  **얼굴은 백운선사인데 말은 도령**이 하고 있었습니다. 한 화면에 두
  사람이 선 셈입니다.

★ A 구간은 도령의 자리입니다

  손님은 b2 진열대에 가서야 사람을 고릅니다. 그 전까지는 도령이
  안내합니다. 그러니 A 구간의 얼굴은 세션에서 읽지 않고 **못박습니다.**

★ 왜 검사로 잠그나

  이 자리는 **조용히 틀립니다.** 아무도 안 죽고 화면만 어긋나서,
  처음 오는 사람으로 눌러 보면 멀쩡해 보입니다. 다시 온 사람에게만
  틀리니 손으로는 잘 안 잡힙니다.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"

# 손님이 아직 아무도 안 고른 구간. 여기 서는 사람은 도령 하나입니다.
GUIDE = "pungun"


def _page() -> str:
    return (WEB / "app" / "page.tsx").read_text(encoding="utf-8")


def test_얼굴을_세션에서_읽지_않는다():
    """
    `<Meet>` 에 `lens` 가 없으면 저장된 `cur` 를 씁니다 — 다시 온
    사람에게 지난번 사람이 나옵니다.
    """
    bad = [m.group(0) for m in re.finditer(r"<Meet\b[^>]*/>", _page())
           if "lens=" not in m.group(0)]
    assert not bad, "얼굴을 세션에서 읽고 있소: %s" % bad


def test_A구간의_얼굴은_도령이다():
    for m in re.finditer(r"<Meet\b[^>]*/>", _page()):
        got = re.search(r'lens="(\w+)"', m.group(0))
        assert got and got.group(1) == GUIDE, m.group(0)


def test_얼굴과_말이_같은_사람이다():
    """
    ★ 이게 실제로 틀렸던 자리입니다. 얼굴은 세션에서 오고 말은
      박혀 있어, 둘이 갈렸습니다.

      `<Meet>` 바로 뒤에 오는 `<Say>` 가 다른 사람이면 한 화면에
      두 사람이 서 있는 것입니다.
    """
    src = _page()
    for m in re.finditer(r"<Meet\b[^>]*/>", src):
        face = re.search(r'lens="(\w+)"', m.group(0))
        after = src[m.end():m.end() + 600]
        said = re.search(r'<Say\b[^>]*lens="(\w+)"', after)
        if not said:
            continue
        assert face and face.group(1) == said.group(1), (
            "얼굴은 %s 인데 말은 %s 가 하오"
            % (face.group(1) if face else "세션", said.group(1)))


def test_소리는_도령_자리에만_난다():
    """
    첫 인사(greet)는 도령이 처음 고개를 드는 자리 하나뿐입니다.
    뒤에 또 나면 인사가 아니라 배경음입니다.
    """
    got = re.findall(r"<Meet\b[^>]*\bgreet\b[^>]*/>", _page())
    assert len(got) == 1, "첫 인사가 %d 자리에 있소" % len(got)
    assert 'lens="%s"' % GUIDE in got[0], got[0]
