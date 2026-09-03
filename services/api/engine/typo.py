"""
글자가 앉는 자리 — 줄길이와 읽는 시간.

★ 왜 엔진에 두는가

  이 셈은 `tools/widow.py` 가 들고 있었습니다. 그런데 `tools/` 는
  배포 이미지에 안 들어갑니다(.dockerignore). 그래서 주인 화면이
  줄길이를 재려면 이 계산이 **엔진 쪽에** 있어야 합니다.

  두 벌로 나눠 두면 언젠가 한쪽만 고칩니다 — 화면 폭을 440 에서
  바꾸는 날, 도구는 알고 점수는 모르는 일이 생깁니다. 여기 한 벌만
  두고 `tools/widow.py` 가 이걸 씁니다.

★ 무엇을 아는가

    WIDTH   글자가 앉는 폭(px). 틀 440 · .scr 좌우 22 → 396.
    SIZE    클래스별 글자 크기. `styles/tokens.css` 의 사다리와 짝.
    wrap    띄어쓰기에서만 끊습니다 (CSS 의 word-break: keep-all).

★ 읽는 속도는 **이 집이 이미 쓰는 수**입니다

  목패에 「읽는 데 약 N분」 이라 적을 때 쓰는 값이 분당 550 자입니다
  (`routers/pay.CHARS_PER_MINUTE`). 여기서 다른 수를 쓰면, 손님에게는
  6분이라 적어 놓고 주인 화면에는 4분이라 뜨게 됩니다.

  같은 자를 씁니다. 그 수를 고치는 날 두 곳이 함께 움직이게
  `tests/test_typo.py` 가 지킵니다.
"""
from __future__ import annotations

import re

# 틀 440 · .scr 좌우 22 → 396. 가운데 정렬 글(.gatecopy)은 26 을 더 먹는다.
WIDTH = 396
GATE_WIDTH = 388

# 클래스 → 글자 크기(px). tokens.css 의 사다리와 짝입니다.
SIZE = {
    "nr": 16.0,        # --fs-5  나레이션
    "say": 17.5,       # --fs-6  도령의 말
    "promise": 16.0,   # --fs-5
    "sm": 14.0,        # --fs-3  부가 설명
    "btn": 15.0,       # --fs-4  버튼
    "lab": 13.0,       # --fs-2
    "cut": 16.0,       # --fs-5  리포트 본문
}

# 본문 기준 크기 — 화면을 통째로 잴 때 쓰는 눈금
BODY_PX = 16.0

# 과부로 보는 길이 — 마지막 줄이 이보다 짧으면 짚습니다
WIDOW = 4

# 한글 묵독 — 분당 글자 수. routers/pay.CHARS_PER_MINUTE 와 같아야 합니다.
CHARS_PER_MINUTE = 550
CHARS_PER_SEC = CHARS_PER_MINUTE / 60.0

# 한 줄이 편안한 구간 (글자 수).
#
# ★ 라틴 활자는 한 줄 45~75 자가 편하다고 합니다. 한글은 한 글자가
#   거의 1em 이라 같은 폭에 절반쯤 들어갑니다 — 396px 에 16px 이면
#   스물넉 자 남짓입니다. 그래서 눈금을 따로 둡니다.
#
# ★ 아래로도 재는 까닭: 조각 문장만 이어지면 눈이 계속 되돌아옵니다.
#   너무 긴 줄만 나쁜 게 아닙니다.
LINE_MIN = 14
LINE_MAX = 34

# 한 문단이 이보다 길면 벽으로 읽힙니다
PARA_MAX_LINES = 7

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def width_of(ch: str) -> float:
    """한글·한자는 거의 1em, 나머지는 절반쯤."""
    return 1.0 if "가" <= ch <= "힣" or "一" <= ch <= "鿿" else 0.5


def wrap(text: str, px: float = BODY_PX, box: int = WIDTH) -> list:
    """띄어쓰기에서만 끊습니다 (word-break: keep-all)."""
    cap = box / px
    lines, cur, w = [], "", 0.0
    for word in text.split(" "):
        ww = sum(width_of(c) for c in word)
        if cur and w + 0.5 + ww > cap:
            lines.append(cur)
            cur, w = word, ww
        else:
            if cur:
                cur += " "
                w += 0.5
            cur += word
            w += ww
    if cur:
        lines.append(cur)
    return lines


def paragraphs(html: str) -> list:
    """
    문단으로 가릅니다.

    ★ `<br>` 과 문단 태그가 곧 손님이 보는 줄바꿈입니다. 태그를 먼저
      다 지우고 나면 한 덩이가 되어, 벽처럼 선 문단을 못 찾습니다.
    """
    if not html:
        return []
    t = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</h\d>", "\n", html, flags=re.I)
    t = _TAG.sub(" ", t)
    # ★ 화면 글은 태그가 이미 걷힌 채로 옵니다 (screenscan._readable).
    #   거기서는 **줄바꿈이 문단 경계**입니다 — 안 그러면 화면 하나가
    #   통째로 한 문단이 되어, 어느 화면이나 「벽으로 읽히오」 가 됩니다.
    out = []
    for chunk in t.split("\n"):
        chunk = _WS.sub(" ", chunk).strip()
        if chunk:
            out.append(chunk)
    return out


def seconds(chars: int) -> float:
    """이만큼을 읽는 데 걸리는 초."""
    return chars / CHARS_PER_SEC
