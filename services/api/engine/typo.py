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

# ══════════════════════════════════════════════════════════
# 한 화면 — 스크롤 없이 한 번에 보이는 만큼
# ══════════════════════════════════════════════════════════
#
# ★ 손님이 정한 것 (2026-09-04)
#
#   "페이지가 길면 괜찮은데 한 화면에 글자 꽉 채우면 안 돼."
#
#   길이는 죄가 아닙니다. 스크롤은 손님이 이미 아는 동작이고, 긴
#   페이지는 내려가며 읽으면 그만입니다. 못 견디는 것은 **한 번에
#   보이는 화면이 글자로만 가득한 것**입니다. 그때는 읽는 게 아니라
#   훑게 되고, 훑으면 아무것도 안 남습니다.
#
# ★ 몇 줄인가
#
#   글이 앉는 폭은 396px 이고 본문은 16px 입니다(WIDTH · BODY_PX).
#   줄높이 1.7 이면 한 줄이 27.2px 이오. 손 안에서 흔한 화면 높이가
#   700px 남짓인데, 거기서 머리(제목·되돌아가기)와 발(버튼)이
#   차지하는 몫을 빼면 글이 앉는 자리는 600px 쯤입니다.
#
#       600 / 27.2 ≒ 22
#
#   그래서 스물두 줄입니다. 한 상자가 이보다 길면 그 상자 하나로
#   화면이 꽉 찹니다 — 위아래로 숨 쉴 데가 없습니다.
LINE_PX = 27.2                     # 16px × 줄높이 1.7
VIEW_PX = 600.0                    # 머리와 발을 뺀 글 자리
VIEW_LINES = int(VIEW_PX / LINE_PX)  # 22


# 눈이 쉬는 자리 — 여기서 글줄이 끊깁니다.
#
# ★ 문단(`<p>` · `<br>`)은 **안 칩니다.** 문단 사이 여백은 한 줄
#   남짓이라, 열 문단이 이어지면 눈에는 여전히 글자 벽입니다.
#   쉼이 되는 것은 **그림 · 테두리 친 카드 · 제목 · 표**처럼
#   글이 아닌 것이 사이에 서는 자리입니다.
_BREAK = re.compile(
    r"</div>"
    r"|<(?:img|video|table|hr|h\d)\b[^>]*>"
    r"|<div[^>]*class=\"[^\"]*(?:ssfig|hd|seq|ph|gls|scene)[^\"]*\"[^>]*>"
    r"|<p[^>]*class=\"[^\"]*(?:ev|bite|side|fig|gp)[^\"]*\"[^>]*>"
    r"|<span[^>]*class=\"[^\"]*src[^\"]*\"[^>]*>",
    re.I)


def boxes(text: str) -> list:
    """
    **상자**로 가릅니다 — 문단이 아니라.

    ★ 문단(paragraphs)과 무엇이 다른가

      문단은 `<br>` 과 `</p>` 에서도 갈립니다. 그런데 문단 사이
      여백은 한 줄 남짓이라, 열 문단이 이어지면 눈에는 여전히
      **글자 벽**입니다. 문단이 많다고 화면이 트이지 않습니다.

      쉼이 되는 것은 글이 아닌 것이 사이에 서는 자리입니다 —
      그림 · 제목 · 표 · 근거 딱지, 그리고 **테두리나 줄이 그어진
      상자**입니다. 이 집에서는 넷이오 —
        .ev    점선 테두리 · 근거 줄
        .bite  왼쪽 금줄 · 팩폭
        .side  윗줄 · 곁말
        .gls   왼쪽 줄 · 「이게 무슨 말인가」
        .fig   비유 한 줄
        .scene 테두리 + 색 띠 · 장면 상자
        .gp    점선 · 어긋난 칸 하나 신살 컷이
      그 예입니다: 쉰여덟 줄이지만 일곱 장의 카드로 갈려 있고
      카드마다 인물 그림이 한 장씩 서니, 눈은 일곱 번 쉽니다.

      화면 글은 상자 사이가 **줄바꿈**으로 이어져 옵니다
      (screenscan._readable · _engine_text). 그것도 경계입니다.
    """
    if not text:
        return []
    out = []
    for chunk in _BREAK.sub("\n", text).split("\n"):
        chunk = _WS.sub(" ", _TAG.sub(" ", chunk)).strip()
        if chunk:
            out.append(chunk)
    return out


def screens_of(text: str) -> float:
    """이 글이 한 화면의 몇 배인가. 1.0 이면 딱 한 화면입니다."""
    return len(wrap(text)) / float(VIEW_LINES)

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
