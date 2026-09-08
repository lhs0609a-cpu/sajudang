"""
훑어읽기 — 강조만 읽어도 말이 되게

★ 손님이 한 말

  "사람들이 전체 글 다 안 읽을거니까 중요한 워딩이나 그런것들 밑줄치고,
   강조표시해주고 그것만 읽어도 전체적으로 다 이해가 되게끔 해."

  맞습니다. 19,900원짜리 한 장이 **29컷 12,582자**입니다. 다 읽는
  손님은 드뭅니다. 그런데 지금 이 글에는 **크기가 하나**뿐입니다 —
  굵게 하나. 그것도 절반은 낱말(용어·글자·수)에 붙어 있어, 굵은 데만
  이어 읽으면 「癸酉 · 일 · 관성 · 戌 · ENFP」 같은 목록이 나옵니다.
  그건 요약이 아니라 색인입니다.

★ 넷으로 칠합니다. 뜻이 다 다릅니다.

      굵게   <b>          센 사실           지금 있는 것. 안 건드림
      형광펜 <mark>       그 컷의 결론      이것만 이으면 요약이 된다
      밑줄   <u>          손님이 할 것      처방·고를 것
      수     <span.nu>    나이·해·갯수      틀릴 수 없는 말을 피한 자리

  뜻이 같은 표시가 둘이면 **둘 다 무시됩니다.** 그래서 넷의 뜻이
  겹치지 않게 두고, 한 컷에 형광펜은 **하나**만 칠합니다. 둘이면
  그건 요약이 아니라 또 본문입니다.

★ 지어내지 않습니다 — 이게 이 파일의 핵심입니다.

  형광펜은 **이미 짚어 둔 자리**에만 칠합니다.

      ① `.bite` 단락       뱅크 저자가 "여기가 팩폭"이라 적어 둔 자리
      ② 문장 꼴 `<b>`      "여기가 핵심"이라 굵게 해 둔 자리

  재보니 컷 2,964개 중 ①이 20.2%, ②가 37.2%, 둘 중 하나라도 있는
  것이 **47.2%** 였습니다. 나머지 절반은 낱말만 굵습니다.

  ★ 그 절반에는 **안 칠합니다.**
    컷마다 하나씩 채우려고 아무 줄에나 칠하면, 형광펜만 읽는 손님이
    결론이 아닌 것을 결론으로 읽습니다. 그건 강조가 아니라 거짓말
    표시입니다. 없는 데는 비워 둡니다 — 계산이 없으면 "모른다"고
    쓰는 것과 같은 규칙입니다.

  덕분에 리포트 한 장에 형광펜이 열둘~열여덟 줄쯤 남습니다.
  `.\\dev.ps1 skim` 이 그 줄만 뽑아 이어 붙여 줍니다 — 사람이 읽어
  보고 말이 되는지 봅니다.

★ 어디에는 안 칠하는가

      .fig   비유입니다. 그림에 형광펜을 치면 그림이 결론이 됩니다
      .gls   풀이입니다. 낱말 뜻에 밑줄을 치면 뜻이 처방으로 보입니다
      .ev    근거입니다. 근거는 **보이되 조용해야** 합니다

★ 왜 층으로 두는가

  뱅크 문장마다 손으로 칠하면 다음에 문장을 넣을 때 또 빠집니다.
  가드·그림·말투·풀이와 **같은 자리**에 얹습니다. 그러면 스무 캐릭터
  전부, 132개 관점 컷 전부, 화면 스물여덟 곳 전부에 한 번에 붙습니다.

★ 맨 끝에 얹습니다.
  말투 층보다 뒤입니다 — 어미를 갈아 끼우면 문장 끝이 바뀌는데,
  「…하시오」를 찾는 밑줄 규칙이 그 앞에서 돌면 갈아 끼운 뒤의
  어미(「…하세요」)를 못 봅니다. 줄표에서 한 번 겪은 자리입니다.
"""
from __future__ import annotations

import re
from typing import Optional

# ══════════════════════════════════════════════════════════
# HTML 을 태그와 글로 가른다
# ══════════════════════════════════════════════════════════
#
# ★ 정규식으로 본문만 골라 바꾸려면 **태그 안**을 절대 건드리면
#   안 됩니다. `class="bite"` 의 숫자나 낱말을 칠하면 화면이 깨집니다.
#   그래서 태그와 글을 갈라 놓고 글에만 손댑니다.
_TOKEN = re.compile(r"(<[^>]+>)")
_TAG = re.compile(r"<[^>]+>")
_OPEN = re.compile(r"<\s*([a-zA-Z][\w-]*)([^>]*)>")
_CLOSE = re.compile(r"<\s*/\s*([a-zA-Z][\w-]*)\s*>")
_CLASS = re.compile(r'class\s*=\s*"([^"]*)"')

# 이 안에서는 아무것도 안 칠합니다.
QUIET = ("fig", "gls", "ev", "src", "cnt")


def _walk(html: str):
    """(글조각, 열려 있는 class 들, 열려 있는 태그 이름들) 을 차례로 낸다."""
    classes: list = []
    names: list = []
    for tok in _TOKEN.split(html or ""):
        if not tok:
            continue
        if tok.startswith("<"):
            m = _CLOSE.match(tok)
            if m:
                if names:
                    names.pop()
                    if classes:
                        classes.pop()
            elif not tok.endswith("/>"):
                o = _OPEN.match(tok)
                if o:
                    names.append(o.group(1).lower())
                    c = _CLASS.search(o.group(2) or "")
                    classes.append(set((c.group(1) if c else "").split()))
            yield tok, None, None
        else:
            flat = set()
            for s in classes:
                flat |= s
            yield tok, flat, list(names)


def _quiet(classes: Optional[set], names: Optional[list]) -> bool:
    if classes is None:
        return True
    if classes & set(QUIET):
        return True
    # 이미 칠한 자리 안에는 또 안 칠합니다.
    return bool(set(names or []) & {"mark", "u"})


# ══════════════════════════════════════════════════════════
# ① 수 — 나이 · 해 · 갯수
# ══════════════════════════════════════════════════════════
#
# ★ 왜 수에 따로 색을 주는가
#   이 집은 「틀릴 수 없는 말」을 안 쓰기로 했습니다 (CLAUDE.md).
#   바넘 문장을 피하려고 **나이·연도·센 수**를 일부러 박아 둔 것이라,
#   그 수가 곧 이 글이 다른 점집과 갈리는 자리입니다. 그런데 지금은
#   줄글 속에 묻혀 있습니다.
#
# ★ 소수와 음수는 안 칠합니다. 내부 척도라 화면에 나오면 안 됩니다
#   (tests/test_lens_cuts.test_no_numbers_in_perspective_text).
_NUM = re.compile(
    r"(?<![\d.])(\d{1,4})\s*(살|세|년|해|달|개월|개|자|번|가지|명|쪽|%|분|시)"
    r"(?![\d.])")


def _numbers(text: str) -> str:
    return _NUM.sub(lambda m: '<span class="nu">%s%s</span>'
                    % (m.group(1), m.group(2)), text)


# ══════════════════════════════════════════════════════════
# ② 밑줄 — 손님이 할 것
# ══════════════════════════════════════════════════════════
#
# ★ 처방만 칠합니다. 「…하시오 · …해 보세요 · …두시오」 처럼 손님을
#   움직이는 문장입니다. 진단문에 밑줄을 치면 밑줄의 뜻이 흐려집니다.
#
# ★ 말투 층 뒤에서 돕니다. 캐릭터마다 어미가 갈리기 때문입니다 —
#   하오체는 「보시오」, 해요체는 「보세요」, 합쇼체는 「보십시오」.
# ★ 어미 하나만 봅니다 — 「…시오」.
#
#   뱅크는 하오체 한 벌로 쓰여 있고, 시키는 말은 거기서 **「…시오」
#   한 꼴**입니다 (engine/voice §한 낱말 바꾸기). 그래서 말투 층
#   **앞에서** 찾으면 애매한 자리가 없습니다.
#
# ★ 뒤에서 찾으면 안 됩니다.
#   말투 층이 「하시오」를 캐릭터마다 갈아 끼웁니다 —
#       합쇼체 하십시오 · 해요체 하세요 · 하게체 하게 · 반말 하지
#   그런데 하게체·반말은 **서술 어미와 같은 꼴**이 됩니다(…네/…지).
#   뒤에서 어미로 가르면 「나는 뿌리부터 보오」 같은 소개말에 밑줄이
#   갑니다. 실제로 그랬습니다.
_DO_TAIL = ("시오",)
_SENT = re.compile(r"[^.!?]*[.!?]")
DO_MIN = 8

# ══════════════════════════════════════════════════════════
# 태그를 건너뛰고 **문장**을 잡는다
# ══════════════════════════════════════════════════════════
#
# ★ 처음엔 글조각마다 따로 봤습니다. 그런데 문장이 굵게로 쪼개져
#   있으면 조각이 갈립니다 —
#
#       <p>이번 주에 <b>불 켜진 데서 한 끼</b> 드시오. …</p>
#
#   조각 셋 중 마지막이 「 드시오. 혼자라도…」 뿐이라, 처방을 못 보고
#   그 컷의 **두 번째** 처방에 밑줄이 갔습니다. 문장은 태그를 건너
#   이어져 있으니, 문단을 통째로 놓고 자리를 되짚어야 합니다.
_P = re.compile(r"(<p\b[^>]*>)(.*?)(</p>)", re.S)


def _plain_map(html: str) -> tuple:
    """(태그 걷은 글, 글 한 자마다 원래 자리) — 자리를 되짚기 위한 표."""
    text, at = [], []
    i = 0
    for tok in _TOKEN.split(html or ""):
        if not tok:
            continue
        if not tok.startswith("<"):
            for k, ch in enumerate(tok):
                text.append(ch)
                at.append(i + k)
        i += len(tok)
    return "".join(text), at


def _wrap(html: str, a: int, b: int, open_tag: str, close_tag: str) -> str:
    """글 기준 [a, b) 를 태그로 감싼다. **태그 안은 안 자릅니다.**"""
    _t, at = _plain_map(html)
    if not at or a >= b or b > len(at):
        return html
    lo, hi = at[a], at[b - 1] + 1
    return html[:lo] + open_tag + html[lo:hi] + close_tag + html[hi:]


def find_do(html: str) -> Optional[tuple]:
    """
    밑줄 칠 자리를 **말투 층 앞에서** 찾아 둔다.

    돌려주는 것: (몇 번째 문단, 그 문단의 몇 번째 문장) 또는 None.

    ★ 왜 자리만 기억하고 나중에 칠하는가
      여기서 바로 `<u>` 를 넣으면 문장 끝이 「드시오.</u>」 가 되어,
      말투 층이 어미를 못 찾습니다 — 그 캐릭터만 하오체로 남습니다.
      비유 상자와 근거 줄에서 이미 겪은 자리입니다.

      자리는 안 밀립니다. 뒤에 오는 층(곁말·물음·그림 상자)은 문단을
      **뒤에 붙이기만** 하지 앞을 건드리지 않습니다.
    """
    for pi, m in enumerate(_P.finditer(html or "")):
        c = _CLASS.search(m.group(1))
        if c and set(c.group(1).split()) & set(QUIET):
            continue
        text, _at = _plain_map(m.group(2))
        for si, s in enumerate(_SENT.finditer(text)):
            body = s.group(0).strip()
            if len(body) < DO_MIN:
                continue
            if body.rstrip(".!? ").endswith(_DO_TAIL):
                return (pi, si)
    return None


def _do_at(html: str, spot: tuple) -> str:
    """기억해 둔 자리에 밑줄을 친다."""
    pi, si = spot
    for i, m in enumerate(_P.finditer(html or "")):
        if i != pi:
            continue
        inner = m.group(2)
        text, _at = _plain_map(inner)
        for k, s in enumerate(_SENT.finditer(text)):
            if k != si:
                continue
            # 앞 공백은 밑줄 밖에 둡니다 — 밑줄이 문장 앞에서 떠 보입니다.
            lead = len(s.group(0)) - len(s.group(0).lstrip())
            # ★ 형광펜과 겹치면 밑줄은 물러섭니다.
            #   한 문장에 뜻이 다른 표시가 둘이면 손님은 어느 쪽으로
            #   읽어야 할지 모릅니다. 결론이 처방보다 앞섭니다.
            if "<mark>" in inner:
                return html
            marked = _wrap(inner, s.start() + lead, s.end(), "<u>", "</u>")
            return (html[:m.start()] + m.group(1) + marked + m.group(3)
                    + html[m.end():])
    return html


# ══════════════════════════════════════════════════════════
# ③ 형광펜 — 그 컷의 결론 한 줄
# ══════════════════════════════════════════════════════════
#
# ★ 두 자리에서만 찾습니다. 지어내지 않습니다.
_BITE = re.compile(r'(<p class="bite">)(.*?)(</p>)', re.S)
_BOLD = re.compile(r"<b>(.*?)</b>", re.S)
# 문장 꼴 — **마침표로 끝나는 것**만.
#
# ★ 어미만 보면 조각이 걸립니다.
#   「혼자 지던 것을 나눌지」 「같은 데서 걸린 사람이 그만큼 많다」 가
#   형광펜으로 나갔습니다. 둘 다 문장 가운데를 굵게 한 것이라, 이어
#   읽으면 말이 끊깁니다. 뱅크에서 **문장 통째로** 굵게 한 자리는
#   마침표까지 안에 들어 있습니다 — 그것만 씁니다.
_SENT_TAIL = re.compile(
    r"(오|소|요|다|네|지|까|랴|군|구먼|습니다|비다)[.!?]$")
PEN_MIN = 12


def _first_sentence(inner: str) -> tuple:
    """`.bite` 단락의 첫 문장과 나머지. 태그 안에서 자르지 않습니다."""
    depth_safe = []
    for tok, cls, _n in _walk(inner):
        depth_safe.append((tok, cls is not None))
    plain_at = 0
    for i, (tok, is_text) in enumerate(depth_safe):
        if not is_text:
            plain_at += len(tok)
            continue
        m = _SENT.search(tok)
        if m and len(_TAG.sub("", inner[:plain_at + m.end()]).strip()) >= PEN_MIN:
            cut = plain_at + m.end()
            return inner[:cut], inner[cut:]
        plain_at += len(tok)
    return inner, ""


_KEY = re.compile(r'<p class="[^"]*\bkey\b[^"]*">(.*?)</p>', re.S)


def _last_sentence(inner: str) -> Optional[tuple]:
    """이 문단의 **마지막 문장** 자리. 없으면 None."""
    text, _at = _plain_map(inner)
    spots = [m for m in _SENT.finditer(text) if len(m.group(0).strip()) >= PEN_MIN]
    if not spots:
        return None
    m = spots[-1]
    lead = len(m.group(0)) - len(m.group(0).lstrip())
    return (m.start() + lead, m.end())


def _pen(html: str) -> str:
    """컷 하나에 형광펜 **하나**."""
    m = _BITE.search(html)
    if m:
        head, rest = _first_sentence(m.group(2))
        if _TAG.sub("", head).strip():
            return (html[:m.start()] + m.group(1) + "<mark>" + head + "</mark>"
                    + rest + m.group(3) + html[m.end():])

    # `.bite` 가 없으면 **문장 꼴로 굵게 해 둔 자리**를 씁니다.
    for b in _BOLD.finditer(html):
        # 조용한 자리(비유·풀이·근거) 안이면 건너뜁니다.
        # ★ 태그가 아니라 **속 글**의 자리를 봅니다. `b.start()` 를 주면
        #   `<b>` 태그 토큰을 짚게 되는데, 태그 토큰은 늘 조용한 것으로
        #   세어져 **문장 꼴 굵게가 통째로 걸러졌습니다.**
        if _in_quiet(html, b.start(1)):
            continue
        body = _TAG.sub("", b.group(1)).strip()
        if len(body) < PEN_MIN or not _SENT_TAIL.search(body):
            continue
        return (html[:b.start()] + "<mark>" + b.group(0) + "</mark>"
                + html[b.end():])

    # ★ 관점 컷 — `key` 문단의 **마지막 문장**.
    #
    #   이 문단은 셈 → 뜻 → 결론 순으로 쓰여 있어(engine/lens_cuts),
    #   마지막 문장이 결론입니다. **구조로 그런 것이라 짐작이 아닙니다.**
    #
    #   이게 없으면 19,900원이 여는 관점 컷 열이 훑어읽기에 한 줄도
    #   못 냅니다 — 재보니 값이 두 배인데 형광펜 줄 수가 0원짜리와
    #   같았습니다(7.8줄 대 7.8줄).
    k = _KEY.search(html)
    if k:
        spot = _last_sentence(k.group(1))
        if spot:
            inner = _wrap(k.group(1), spot[0], spot[1], "<mark>", "</mark>")
            return html[:k.start(1)] + inner + html[k.end(1):]
    return html


def _in_quiet(html: str, pos: int) -> bool:
    """이 자리가 조용한 상자 안인가."""
    at = 0
    for tok, cls, names in _walk(html):
        nxt = at + len(tok)
        if at <= pos < nxt:
            return _quiet(cls, names)
        at = nxt
    return False


# ══════════════════════════════════════════════════════════
# 얹기
# ══════════════════════════════════════════════════════════
def mark(html: str, do_spot: Optional[tuple] = None) -> str:
    """
    강조 넷을 얹는다. **글자는 하나도 안 바꿉니다** — 태그만 답니다.

    `do_spot` 은 `find_do()` 가 **말투 층 앞에서** 잡아 둔 밑줄 자리요.
    안 주면 밑줄은 안 칩니다 — 뒤에서 어미로 가르면 틀립니다.

    ★ 순서가 있습니다.
      형광펜을 먼저 칠하고(문장 꼴 `<b>` 를 찾아야 하므로), 그 다음
      밑줄, 마지막에 수입니다. 수를 먼저 칠하면 `<span>` 이 끼어들어
      「33살」 이 든 문장이 문장 꼴로 안 잡힙니다.
    """
    if not html:
        return html
    # ★ 이미 얹은 글에는 다시 안 얹습니다.
    #
    #   층은 여러 번 돌 수 있습니다 — 캐시를 다시 굽거나, 엿보기가
    #   본문을 한 번 더 태우거나. 그때 또 칠하면 `<mark><mark>…` 이
    #   되어 띠가 두 겹으로 짙어집니다. 검사가 이걸 잡았습니다.
    if "<mark>" not in html:
        html = _pen(html)
    if do_spot is not None and "<u>" not in html:
        html = _do_at(html, do_spot)

    out = []
    for tok, cls, names in _walk(html):
        # ★ 이미 굵은 자리에는 수를 또 안 칠합니다.
        #   「<b><span class="nu">26살</span></b>」 처럼 겹치면 표시가
        #   둘인데 뜻은 하나라, 둘 다 힘을 잃습니다.
        if cls is None or _quiet(cls, names) or "b" in (names or []):
            out.append(tok)
            continue
        out.append(_numbers(tok))
    return "".join(out)


def pen_lines(html: str) -> list:
    """형광펜만 뽑는다. 도구와 검사가 이걸로 훑어읽기를 잽니다."""
    return [_TAG.sub("", m).strip()
            for m in re.findall(r"<mark>(.*?)</mark>", html or "", re.S)]
