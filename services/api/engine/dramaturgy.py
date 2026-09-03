"""
연출 감사 — **다음 화가 보고 싶어지는가.**

★ 손님이 한 말 (2026-09-02)

  "전체 사주를 읽을 때마다 미드처럼 다음 화로 넘어가고 싶어 궁금해
  미치겠을 정도로 설계 다 했는지 확인해봐. 모든 페이지가 다 그렇게
  구성되어야 해. 그렇지 않으면 실패야."

  그리고 관리자 화면에 **페이지마다 점수**로 보이게 해 달라 했습니다 —
  ① 팩트를 때리는가 ② 다음 화로 넘어갈 수밖에 없는가 ③ 충실한가
  ④ 쉬운가.

★ 미드는 어떻게 짜는가 (조사한 것)

  한 시간짜리 드라마는 **티저 + 4~5막**입니다. 스트리밍은 광고가
  없는데도 같은 박자를 씁니다 — 광고 때문이 아니라 **사람이 그렇게
  읽기 때문**입니다.

    티저(콜드 오픈)  설명 전에 사건이나 물음부터. 제목보다 앞에 온다
    막마다 액트아웃   막 끝은 반드시 밝힘 · 뒤집기 · 딜레마 · 끊긴 동작 ·
                     남긴 물음 중 **하나**로 끊는다
    댕글링 코즈       답을 주되 **새 물음을 하나 남긴다.** 다 닫으면 안 본다
    버튼             장면을 끊는 짧고 날카로운 한 줄
    A/B 플롯         굵은 줄 하나에 잔 줄 하나를 겹친다

  왜 먹히는가 — **자이가르닉 효과**입니다. 끝난 일보다 **안 끝난 일**이
  머리에 오래 남습니다. 끊긴 자리가 기억에 갈고리를 겁니다.

★ 다만 자동재생은 안 합니다

  넷플릭스가 2012년에 포스트플레이를 넣으면서 「계속 볼지」 를 고르던
  것이 「그만 볼지」 를 고르는 것으로 뒤집혔습니다. 그게 이 집에서
  가장 쉬운 길이지만 **안 씁니다** — 하루 결제 2건 · 세션당 릴레이
  2명 · 만류 문구는 매출보다 앞섭니다 (CLAUDE.md 절대 규칙 4).

  대신 **다음이 무엇인지 이름으로** 말합니다. 고르는 것은 손님이고,
  고를 이유는 우리가 댑니다. 자동으로 밀지 않습니다.

★ 네 지표

  당김(pull)   콜드 오픈 · 액트아웃 · 이름으로 예고 · 버튼
  팩폭(bite)   반증 가능한 말 · 산 말 · 안 물러섬
  충실(depth)  분량 · 근거 · 셀 수 있는 값
  쉬움(plain)  어려운 말 풀이 · 비유 · 문장 길이

  점수는 취향이 아니라 **셀 수 있는 것**만 셉니다. 못 세는 것은
  안 셉니다 — 세는 척하면 도구가 거짓말을 합니다.
"""
from __future__ import annotations

import re
from typing import Optional

from . import terms

TAG = re.compile(r"<[^>]+>")
GLS = re.compile(r'<(?:div|span) class="gls[^"]*">.*?</(?:div|span)>', re.S)


# ══════════════════════════════════════════════════════════
# ① 당김 — 다음 화로 넘어갈 수밖에 없는가
# ══════════════════════════════════════════════════════════
#
# 액트아웃 다섯 꼴. 조사한 분류(revelation · reversal · dilemma ·
# interrupted action · unanswered question)를 이 집의 말로 옮긴 것입니다.
ACT_OUT = {
    "밝힘": re.compile(
        r"실은|사실은|여기서 갈리|그게 바로|까닭이 (?:여기|있)|"
        r"그래서 (?:지금|여태|늘)|이게 (?:그|바로)"),
    "뒤집기": re.compile(
        r"아니오|아닙니다|틀렸소|틀렸습니다|반대요|반대입니다|"
        r"그 말도 틀|말은 틀|성격이 아니(?:라|오|었)"),
    "딜레마": re.compile(
        r"둘 중|하나만|하나뿐|고르|골라|어느 쪽|둘 다는 못|"
        r"택해|갈림|어디까지|둘이오|둘입니다|다 들을 수는"),
    "끊긴 동작": re.compile(
        r"아직|남았|남은|다음에|뒤에 있|여기까지(?:가|는)|더 있|"
        r"안 (?:했|보였|열)"),
    # ★ 끝에 붙는 버튼 글자 때문에 `$` 앵커가 늘 빗나갔습니다.
    #   뒤 구간 **안에** 물음표가 있으면 그건 열어 놓은 고리입니다.
    "남긴 물음": re.compile(r"[?？]"),
}

# 다음이 무엇인지 **이름으로** 말했는가. 「더 있소」 는 예고가 아닙니다.
NAMED_NEXT = re.compile(r"「[^」]{2,20}」|『[^』]{2,20}』|<b>[^<]{2,20}</b>\s*(?:컷|자리)")

# 콜드 오픈 — 첫 줄이 설명이 아니라 사건이나 물음인가
#
# ★ 낱말을 세지 않고 **말투**를 봅니다.
#
#   전에는 열한 개짜리 동사 목록이었습니다(`했다|였다|섰다`…). 그래서
#   「붓끝이 종이에 닿았다」 도 「검은 고양이가 그 아래 앉아 있다」 도
#   콜드 오픈이 아닌 것으로 나왔습니다. 목록에 없는 동사였을 뿐인데요.
#   그 자를 고치려면 글을 쓸 때마다 목록에 동사를 보태야 합니다 —
#   그건 자가 글을 쫓아다니는 것입니다.
#
#   이 집은 말투가 셋으로 갈려 있습니다. 집이 하는 말은 **하오체**
#   (…오 · …소 · …요), 손님이 누르는 말은 **합쇼체**(…습니다),
#   그리고 지문은 **한다체**(…다)뿐입니다. 그러니 「…다」 로 끝나는
#   줄은 곧 지문이고, 지문으로 여는 것이 곧 콜드 오픈입니다.
#   `(?<!니)` 로 합쇼체를 빼면 남는 것은 지문 한 벌입니다.
NARR = re.compile(r"(?<!니)다[.!?…\"'」』]*$")
ASK = re.compile(r"[?？]")
COLD_BAD = re.compile(r"이란|이라 하오|말합니다|뜻이오|뜻입니다|설명|"
                      r"보는 법|이라고 하")


def _cold_open(lines: list) -> bool:
    """첫 두 줄 중 하나가 지문이거나 물음이면 연 것입니다."""
    for s in lines[:2]:
        s = s.strip()
        if not s or COLD_BAD.search(s):
            continue
        if ASK.search(s) or NARR.search(s):
            return True
    return False


# ══════════════════════════════════════════════════════════
# ② 팩폭 — 팩트를 때리는가
# ══════════════════════════════════════════════════════════
#
# 반증 가능 — 숫자 · 못 박은 때 · 관찰 가능한 행동. 틀릴 수 있어야
# 맞았을 때 소름이 돋습니다 (tools/falsifiable.py 와 같은 결).
FALSIFIABLE = re.compile(
    r"\d+\s*(?:개|자리|살|세|년|해|번|명|컷|글자|시|분|%)|"
    r"[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]|"
    r"프로필을 보|연락을 기다|다시 열어 보|되돌려|밤에|저녁이면")

# 뜬 말 / 산 말 / 물러섬 — tools/blunt_audit.py 와 같은 말뭉치입니다.
AIR = re.compile(r"기운|자리|흐름|구조|결이|결을|결은|쪽이|쪽으로|쪽에|"
                 r"힘이|힘을|힘은|빈자리|배치")
LIFE = re.compile(
    r"돈|월급|삯|빚|일|직장|상사|동료|사람|친구|가족|부모|자식|말|잠|밥|"
    r"약속|집|방|계약|시험|면접|이사|연락|카톡|주말|퇴근|출근|통장|"
    r"저축|장사|손님|아침|저녁|밤|새벽")
HEDGE = re.compile(r"게요|쯤|아마|조금|약간|다소|수도 있|편이|듯|"
                   r"경향|하기도|그럴 수|정도")


# ══════════════════════════════════════════════════════════
# ④ 쉬움 — 손님이 알아들을 수 있는가
# ══════════════════════════════════════════════════════════
HARD = tuple(sorted(terms.MEANING, key=len, reverse=True))
# ★ 낱말 **머리**에서만 셉니다.
#
#   그냥 `w in text` 로 세면 「성격」 안의 「격」 이 걸립니다. 격은 이 집의
#   한 글자짜리 어려운 말이고, 성격은 손님이 매일 쓰는 말입니다. 실제로
#   「성격이 아니라 눌러 온 값」 이라는 줄 하나 때문에 화면 하나가
#   「격을 안 풀었소」 로 내려앉았습니다.
#
#   앞이 한글이 아니면 낱말의 머리입니다. 뒤는 안 봅니다 — 「시주를」
#   「대운이」 처럼 조사가 붙는 게 보통이라서요.
HARD_AT = {w: re.compile(r"(?<![가-힣])" + re.escape(w)) for w in HARD}
HARD_GLOSSED = {w: re.compile(r"(?<![가-힣])" + re.escape(w) + r"\s*[（(]")
                for w in HARD}
SENT = re.compile(r"(?<=[.!?…])\s+")


def plain(html: str) -> str:
    """손님이 눈으로 읽는 글자만."""
    if not html:
        return ""
    t = TAG.sub(" ", html)
    return re.sub(r"\s+", " ", t.replace("&nbsp;", " ")).strip()


def _pct(part: float, whole: float) -> float:
    return 0.0 if whole <= 0 else max(0.0, min(1.0, part / whole))


def _lines(text: str) -> list:
    return [s.strip() for s in SENT.split(text) if s.strip()]


# ══════════════════════════════════════════════════════════
# 화면 하나를 잰다
# ══════════════════════════════════════════════════════════
#
# ★ 기준 분량은 화면 종류마다 다릅니다.
#   입력 화면에 리포트만큼 쓰면 그건 충실한 게 아니라 방해입니다.
FLOOR = {"input": 120, "beat": 260, "read": 900, "list": 200}


def score(sid: str, title: str, html: str, kind: str = "read",
          next_named: Optional[str] = None,
          declared: Optional[list] = None) -> dict:
    """
    화면 하나의 네 점수와 **무엇이 모자란지**.

    sid        화면 이름 (a1 · c2 …)
    html       손님이 실제로 읽는 글 (HTML 그대로)
    kind       input 입력 · beat 한 마디 · read 읽는 자리 · list 고르는 자리
    next_named 화면 밖에서 다음 자리를 이름으로 예고했으면 그 이름
    declared   화면이 `<ActOut kind="딜레마">` 로 **선언한** 액트아웃

    ★ 왜 선언을 받나

      말뭉치로만 찾으면 글을 고칠 때마다 정규식을 쫓아가게 됩니다.
      그건 글을 고치는 게 아니라 **검사에 맞춰 쓰는 것**입니다.

      `ActOut` 은 자리가 고정된 부품이고(버튼 바로 위) 무슨 꼴인지
      스스로 적습니다. 그러면 그건 **있는 것**입니다. 말뭉치는
      부품을 안 쓰는 자리 — 엔진이 짓는 글 — 를 위해 남겨 둡니다.
    """
    body = GLS.sub(" ", html or "")
    text = plain(body)
    lines = _lines(text)
    n = len(text)
    miss = []

    # ── ① 당김 ────────────────────────────────────────────
    # ★ 끝을 **마지막 두 문장**으로만 보면 안 됩니다.
    #
    #   화면 글은 파일에 적힌 순서대로 읽히는데, 막을 끊는 줄 뒤에도
    #   버튼 · 고지 · 각주가 따라붙습니다. 두 문장만 보면 액트아웃을
    #   써 넣고도 「없다」 고 나옵니다 — 실제로 그렇게 나왔습니다.
    #
    #   그래서 **뒤 40%** 안에 있으면 셉니다. 미드에서도 액트아웃은
    #   막의 마지막 한 줄이 아니라 마지막 **비트**입니다.
    cut = max(1, int(len(lines) * 0.6))
    tail = " ".join(lines[cut:]) if lines else ""
    last = lines[-1] if lines else ""

    cold = 25 if _cold_open(lines) else 0
    if not cold:
        miss.append("콜드 오픈이 없소 — 첫 줄이 설명이오. 사건이나 물음부터 여시오")

    kinds = list(declared or [])
    kinds += [k for k, rx in ACT_OUT.items()
              if rx.search(tail) and k not in kinds]
    act = 30 if kinds else 0
    if not act:
        miss.append("액트아웃이 없소 — 끝이 그냥 끝나오. "
                    "밝힘·뒤집기·딜레마·끊긴 동작·남긴 물음 중 하나로 끊으시오")

    named = 25 if (NAMED_NEXT.search(body) or next_named) else 0
    if not named:
        miss.append("다음을 이름으로 안 부르오 — 「더 있소」는 예고가 아니오")

    button = 20 if (last and len(last) <= 42) else 0
    if not button:
        miss.append("버튼이 무디오 — 마지막 한 줄을 짧게 끊으시오 (42자 이내)")

    pull = cold + act + named + button

    # ── ② 팩폭 ────────────────────────────────────────────
    f_hits = len(FALSIFIABLE.findall(text))
    air = len(AIR.findall(text))
    life = len(LIFE.findall(text))
    hedge = len(HEDGE.findall(text))

    s_fals = round(40 * _pct(f_hits, max(3, n / 260)))
    if s_fals < 24:
        miss.append("틀릴 수 없는 말이오 — 수·글자·해 본 행동을 박으시오")
    s_life = round(35 * _pct(life, max(1, air)))
    if s_life < 21:
        miss.append("뜬 말이 산 말보다 많소 — 돈·잠·연락 같은 살림의 말로 바꾸시오")
    s_firm = round(25 * (1 - _pct(hedge, max(2, n / 220))))
    if s_firm < 15:
        miss.append("물러서는 말이 많소 — 「게요·아마·쯤」을 걷으시오")
    bite = s_fals + s_life + s_firm

    # ── ③ 충실 ────────────────────────────────────────────
    floor = FLOOR.get(kind, FLOOR["read"])
    s_len = round(45 * _pct(n, floor))
    if s_len < 27:
        miss.append("분량이 얇소 — %d자 자리에 %d자요" % (floor, n))
    has_src = 30 if re.search(r'class="src"|근거 ·|근거·', html or "") else 0
    if not has_src and kind in ("read", "beat"):
        miss.append("근거 줄이 없소 — 무엇을 보고 한 말인지 적으시오")
    counted = len(re.findall(r"\d", text))
    s_cnt = round(25 * _pct(counted, 6))
    if s_cnt < 15:
        miss.append("셀 수 있는 값이 적소 — 개수·나이·해를 내시오")
    depth = s_len + has_src + s_cnt

    # ── ④ 쉬움 ────────────────────────────────────────────
    used = [w for w in HARD if HARD_AT[w].search(text)]
    glossed = [w for w in used if HARD_GLOSSED[w].search(text)]
    s_gloss = round(45 * (1.0 if not used else _pct(len(glossed), len(used))))
    if used and s_gloss < 27:
        miss.append("어려운 말이 풀이 없이 지나가오 — %s"
                    % " · ".join(w for w in used if w not in glossed)[:40])
    # ★ 뜻풀이는 푼 게 아닙니다. 「식신 = 밖으로 내놓는 힘」 은 모르는
    #   말을 모르는 말로 바꾼 것입니다. **그림이 그려지는 한 줄**이
    #   있어야 손님이 압니다 (tools/plain_audit.py 가 같은 것을 셉니다).
    s_pic = 25 if re.search(r"처럼|같이|마치|셈이오|셈입니다|빗대", text) else 0
    if not s_pic:
        miss.append("비유가 없소 — 그림이 그려지는 한 줄을 다시오")
    avg = (sum(len(l) for l in lines) / len(lines)) if lines else 0
    s_sent = 30 if avg and avg <= 46 else (15 if avg and avg <= 60 else 0)
    if s_sent < 30:
        miss.append("문장이 기오 — 한 문장 평균 %d자요 (46자 아래로)" % avg)
    easy = s_gloss + s_pic + s_sent

    total = round((pull + bite + depth + easy) / 4)
    return {
        "id": sid, "title": title, "kind": kind, "chars": n,
        "pull": pull, "bite": bite, "depth": depth, "plain": easy,
        "total": total,
        "actout": kinds,
        "missing": miss,
    }


def grade(total: int) -> str:
    """점수를 사람 말로. 붉은 것이 뭔지 한눈에 보여야 고칩니다."""
    if total >= 80:
        return "좋소"
    if total >= 65:
        return "쓸 만하오"
    if total >= 50:
        return "모자라오"
    return "고쳐야 하오"
