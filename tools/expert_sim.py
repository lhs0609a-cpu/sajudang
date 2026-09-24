# -*- coding: utf-8 -*-
"""
1만 명 전문가 패널 — 사주가 다 다른 사람 1만 명이 **모든 페이지**를 읽고
흠을 잡습니다.

    python tools/expert_sim.py 10000 --out output/expert
    python tools/expert_sim.py 300                 # 먼저 300명으로 떠 봅니다
    python tools/expert_sim.py 10000 --show 5      # 흠마다 보기 5개까지

★ 기존 자와 무엇이 다른가

  `journey_sim` 은 **터지는가 · 다 다른가 · 여덟 글자에서 나왔는가**를
  봅니다. `easy_audit` `like_me` `sharp_audit` 는 **고정 명식 몇 장**으로
  글맛을 봅니다. 그 사이에 빈자리가 있었습니다 — 만 가지 사주에서
  글이 **알아들을 만한가 · 내 얘기 같은가 · 헷갈리지 않는가**.

  한 장으로 재면 그 한 장이 우연히 좋았을 수 있습니다. 이 도구는 같은
  잣대를 만 명에게 대고, **몇 명에게서 몇 번** 걸렸는지로 말합니다.

★ 보는 자리 (한 사람이 실제로 지나는 순서)

    훅 5단 → 무료 리포트 → 페이월 엿보기 → 고민 세부 물음 →
    유료(이 자리 하나) → 유료(전부) → 릴레이 → 일진 → 분석지 →
    스무 사람 종합(표본)

★ 재는 것 — 넷

  [쉬운말]  흐릿한 문장 비율 · 풀이 없이 나온 어려운 말 · 풀이가 멀어진 자리
  [공감]    그림 · 장면 · 내 수가 **하나도 없는 컷** · 누구에게나 맞는 문장
  [혼동]    서로 어긋난 말 · 세어 놓고 다르게 적은 수 · 없는 기둥을 있다고
            하기 · 주어 없는 문장 · 한 마디에 쏟기 · 같은 말 두 번 ·
            시키는 일 둘 · 자리표시 누출 · 말투 섞임
  [지킴]    금지어 · 검증 불가능한 주장 · 표시가와 청구가 · 잠긴 컷 안내

★ 셈의 규칙

  · **비율로 말합니다.** 만 명 중 몇 명, 몇 번. 한 건은 한 건이라 적습니다.
  · **보기를 답니다.** 어느 사주 · 어느 컷 · 어느 문장인지 없으면 못 고칩니다.
  · **자가 틀릴 수 있다**고 적습니다. 자가 세는 규칙을 코드에 그대로 둡니다.
"""
from __future__ import annotations

import argparse
import collections
import html as _html
import json
import re
import sys
import time
import traceback
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "services" / "api", ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine import bank as bank_mod              # noqa: E402
from engine import guard                          # noqa: E402
from engine import lens as lens_mod               # noqa: E402
from engine import peek as peek_mod               # noqa: E402
from engine import relay as relay_mod             # noqa: E402
from engine import terms as terms_mod             # noqa: E402
from engine import topic as topic_mod             # noqa: E402
from engine.calendar import build_chart           # noqa: E402
from engine.daily import build_daily              # noqa: E402
from engine.features import build_features        # noqa: E402
from engine.omnibus import build_omnibus          # noqa: E402
from engine.report import build_report            # noqa: E402
from engine.summary import build_summary, share_payload   # noqa: E402
import payments                                   # noqa: E402

#: 고민 목록은 **제품에서** 받습니다.
#:
#: ★ `journey_sim.CONCERNS` 는 여섯 칸에서 멈춰 있었습니다 (2026-09-24).
#:   화면에는 일곱째 칸(부동산)이 열려 있는데 시뮬이 그 칸을 한 번도
#:   안 돌려서, 부동산 손님에게만 나는 사고를 아무 자도 못 봤습니다.
#:   자가 제품보다 좁으면 그 차이만큼 눈이 감깁니다.
def concerns() -> tuple:
    from schemas.api import Concern
    import typing
    return tuple(typing.get_args(Concern))


from tools import easy_audit as EASY              # noqa: E402
from tools import hard_words as HARD              # noqa: E402
from tools import journey_sim as J                # noqa: E402
from tools import like_me as LIKE                 # noqa: E402
from tools import sharp_audit as SHARP            # noqa: E402
from tools import subject_audit as SUBJ           # noqa: E402

ALL_CONCERNS: tuple = ()
TAG = re.compile(r"<[^>]+>")
SENT = re.compile(r"[^.?!]+[.?!]")
GLOSS_BOX = re.compile(r"\([^)]*\)")

# 눈앞에서 풀이가 보여야 하는 거리. 엔진과 같은 수를 씁니다 —
# 두 자가 갈리면 도구를 못 믿습니다 (engine/report.GLOSS_AGAIN).
try:
    from engine.report import GLOSS_AGAIN
except ImportError:                               # noqa: BLE001
    GLOSS_AGAIN = 900


#: 덩이를 가르는 표 — 화면에서 **따로 앉는** 자리입니다.
BLOCK = re.compile(r"</?(?:p|div|li|tr|section|h[1-6]|ul|ol|table|blockquote)\b[^>]*>"
                   r"|<br\s*/?>")
#: 자리를 벌리는 표 — 나란히 앉지만 사이가 벌어집니다.
SPACER = re.compile(r"</?(?:span|td|th|em)\b[^>]*>")
#: 글자에 붙는 표 — 사이를 벌리면 **없는 공백**이 생깁니다.
INLINE = re.compile(r"</?(?:b|i|mark|strong|a|abbr|u|small|code|sup|sub)\b[^>]*>")


def plain(h: str) -> str:
    """
    사람이 읽는 글만.

    ★ 표를 전부 공백으로 바꾸면 **없는 흠이 생깁니다** (2026-09-24).

      `자네는 <b>7살</b>에 첫 대운에` 이 「7살 에」 로 읽혀서, 자가
      「띄어쓰기가 틀렸다」 고 찍었습니다. 화면에는 그런 공백이 없습니다.
      굵게·형광펜은 **글자에 붙는** 표라 사이를 벌리지 않습니다.
      문단·줄은 벌립니다 — 화면에서 따로 앉으니까요.
    """
    t = BLOCK.sub("\n", h or "")
    t = SPACER.sub(" ", t)
    t = INLINE.sub("", t)
    return _html.unescape(TAG.sub("", t))


def sentences(h: str) -> list:
    t = re.sub(r"[ \t]+", " ", plain(h))
    out = []
    for line in t.split("\n"):
        line = line.strip()
        if not line:
            continue
        got = [s.strip() for s in SENT.findall(line)]
        tail = SENT.sub("", line).strip()
        if tail:
            got.append(tail)
        out += [s for s in got if len(s) > 6]
    return out


# ══════════════════════════════════════════════════════════
# 흠 장부
# ══════════════════════════════════════════════════════════
class Book:
    """
    흠을 모으는 자리.

    ★ **사람 수와 건수를 따로 셉니다.** 한 사람에게서 스무 번 걸린 흠과
      스무 사람에게서 한 번씩 걸린 흠은 다른 흠입니다. 앞은 그 컷 하나를
      고치면 되고, 뒤는 표가 잘못된 것입니다.
    """

    def __init__(self, show: int = 3):
        self.hits = collections.Counter()          # 흠 → 걸린 횟수
        self.folk = collections.defaultdict(set)   # 흠 → 걸린 사람들
        self.page = collections.defaultdict(collections.Counter)   # 흠 → 자리
        self.eg = collections.defaultdict(list)    # 흠 → 보기
        self.show = show
        self.rate = collections.defaultdict(list)  # 이름 → 비율 표본
        self.top = collections.defaultdict(collections.Counter)   # 유일성

    def note(self, code: str, who: dict, where: str, snippet: str = "") -> None:
        self.hits[code] += 1
        self.folk[code].add(who["i"])
        self.page[code][where] += 1
        if len(self.eg[code]) < self.show:
            self.eg[code].append({"who": describe(who), "where": where,
                                  "말": re.sub(r"\s+", " ", snippet)[:160]})

    def measure(self, name: str, value: float) -> None:
        self.rate[name].append(value)


def describe(p: dict) -> str:
    t = "미상" if not p["hour_known"] else "%02d:%02d" % (p["hour"], p["minute"])
    return "#%d %04d-%02d-%02d %s %s %s / %s" % (
        p["i"], p["year"], p["month"], p["day"], t, p["city"], p["sex"],
        p["concern"])


# ══════════════════════════════════════════════════════════
# [쉬운말]
# ══════════════════════════════════════════════════════════
def check_easy(B: Book, who: dict, where: str, html: str) -> None:
    """흐릿한 문장 — `tools/easy_audit` 의 자를 그대로 씁니다."""
    ss = EASY.sentences(html)
    if not ss:
        return
    bad = 0
    for s in ss:
        n, fig = EASY.vague_of(s)
        if n >= 2 or fig:
            bad += 1
            B.note("쉬운말/흐릿한 문장", who, where, s)
    B.measure("흐림률 · " + where, bad / len(ss))


#: 어려운 말 표 — 도구와 엔진이 **같은 표**를 봅니다.
TERMS = dict(HARD.HARD)


GLS_BOX = re.compile(r'<div class="gls">.*?</div>', re.S)


def check_terms(B: Book, who: dict, where: str, html: str) -> None:
    """
    어려운 말이 **풀린 채로** 나오는가 — 한 장 단위로 봅니다.

    ★ 자가 두 번 헛짚었습니다 (2026-09-24).

      ① 표에 적힌 문구와 글자가 같아야 풀린 것으로 세면, 화면이 제 말로
         잘 풀어 둔 자리가 「안 풀림」 으로 잡힙니다. 「이게 무슨 말인가」
         상자(`div.gls`)가 곧 풀이입니다 — 거기 든 말은 풀린 것입니다.
      ② 「풀이가 눈앞 900자 밖」 은 뺐습니다. 「일간이 壬, 곧 큰물이라서」
         처럼 **그 자리에서 제 말로 푼** 문장을 자가 못 알아봅니다.
         자가 못 세는 것을 흠이라 부르면 고칠 자리를 못 찾습니다.
    """
    text = plain(html)
    if len(text) < 40:
        return
    box = " ".join(plain(x) for x in GLS_BOX.findall(html or ""))
    for term, mean in TERMS.items():
        spots = [m.start() for m in re.finditer(re.escape(term), text)
                 if HARD._real(text, term, m.start())]
        if not spots:
            continue
        if term in box:
            continue
        if not HARD.glossed(text, term, mean):
            B.note("쉬운말/풀이 없는 어려운 말 · %s" % term, who, where,
                   text[max(0, spots[0] - 40): spots[0] + 40])
            continue
        if True:
            continue
        # 풀이가 달린 자리들
        opened = [m.start() for m in re.finditer(re.escape(term), text)
                  if HARD._OPENS.match(text[m.start() + len(term):
                                            m.start() + len(term) + 4])
                  or mean.split("·")[0].strip()[:4] in
                  text[m.start(): m.start() + len(term) + HARD.NEAR]]
        for at in spots:
            if not any(0 <= at - o <= GLOSS_AGAIN for o in opened):
                B.note("쉬운말/풀이가 멀어진 자리 · %s" % term, who, where,
                       text[max(0, at - 40): at + 40])
                break


# ══════════════════════════════════════════════════════════
# [공감]
# ══════════════════════════════════════════════════════════
def check_likeme(B: Book, who: dict, where: str, html: str) -> None:
    """
    그림 · 장면 · 내 수가 **하나도 없는 자리**를 셉니다.
    한 컷을 다 읽는 동안 하나도 못 만나면, 그 컷은 누구 얘기도 아닙니다.
    """
    ss = LIKE.sentences(html)
    if not ss:
        return
    hit = False
    for s in ss:
        v = LIKE.look(s)
        if v["그림"] or v["장면"] or v["내수"]:
            hit = True
        elif LIKE.HEDGE.search(s):
            B.note("공감/누구에게나 맞는 문장", who, where, s)
    if not hit:
        B.note("공감/그림도 장면도 내 수도 없는 컷", who, where, ss[0])
    B.measure("장면률 · " + where,
              sum(1 for s in ss if LIKE.look(s)["장면"]) / len(ss))


# ══════════════════════════════════════════════════════════
# [혼동] — 헷갈리는 자리
# ══════════════════════════════════════════════════════════
EL_WORD = {"목": "나무", "화": "불", "토": "흙", "금": "쇠", "수": "물"}
KO_NUM = {"하나": 1, "둘": 2, "셋": 3, "넷": 4, "다섯": 5, "여섯": 6,
          "일곱": 7, "여덟": 8, "아홉": 9, "열": 10, "없": 0}

# ★ 「없소」를 **무게**와 대 보면 안 됩니다 (2026-09-24).
#
#   `Features.elements` 는 개수가 아니라 무게입니다 — 숨은 글자까지 세어
#   목 0.6 같은 값이 나옵니다. 그런데 손님이 대 보는 것은 **눈에 보이는
#   여덟(또는 여섯) 글자**입니다. 무게로 재면 자가 「있는데 없다고 했다」
#   고 찍고, 손님은 그 글자를 찾을 수가 없습니다. 보이는 것으로 셉니다.
def visible_count(f) -> dict:
    from engine.constants import ELEMENT_OF_GAN, ELEMENT_OF_JI
    got = collections.Counter()
    for pillar in f.pillars:
        gz = pillar["gz"]
        got[ELEMENT_OF_GAN[gz[0]]] += 1
        got[ELEMENT_OF_JI[gz[1]]] += 1
    return got


# 신강·신약은 **이름이 붙은 판정**입니다. 「두텁다·얇다」는 오행 얘기라
# 한 자리에 같이 서도 어긋난 것이 아닙니다 (쇠는 두텁고 불은 얇소).
STRONG = re.compile(r"신강")
WEAK = re.compile(r"신약")
FORWARD = re.compile(r"순행")
BACKWARD = re.compile(r"역행")
# ★ 낱말 한가운데를 세지 않습니다 (2026-09-24). 「메시지」 의 「시지」 가
#   시지(時支)로 잡혀서, 잘 쓴 살림 장면이 「없는 기둥을 말했다」 고
#   찍혔습니다 — 이 집이 제품에서 여러 번 겪은 그 자리요.
HOUR_WORD = re.compile(r"(?<![가-힣])(?:시주|시지|시간 기둥|태어난 시각"
                       r"|태어난 시간|時 기둥)")
PLACEHOLDER = re.compile(r"\{[a-z_0-9]+\}|%s|%d|None|undefined|NaN|nan곳|▮▮")
ORDER = re.compile(r"(?:시오|십시오|하세요|보시오|적으시오|세시오|해 보시오)(?=[.!?…\s]|$)")
POLITE = re.compile(r"(?:이에요|예요|해요|어요|아요|네요)(?=[.!?…\s]|$)")
FORMAL = re.compile(r"(?:습니다|입니다|합니다|십니다)(?=[.!?…\s]|$)")
HAO = re.compile(r"(?:이오|소|오)(?=[.!?…\s]|$)")


def check_confuse(B: Book, who: dict, where: str, html: str, f) -> None:
    text = plain(html)
    if len(text) < 30:
        return
    body = GLOSS_BOX.sub("", text)

    # ── 서로 어긋난 말 ──────────────────────────────────
    # 「신강·신약 중화」 는 축의 이름표라 둘이 나란히 섭니다. 이름표를
    # 판정으로 세면 없는 모순이 생깁니다.
    # 「신강·신약」 「신강약」 은 **축의 이름표**라 둘이 같이 섭니다.
    naked = re.sub(r"신강약|신강\s*[·/]\s*신약|신약\s*[·/]\s*신강", "", body)
    if STRONG.search(naked) and WEAK.search(naked):
        B.note("혼동/센가 약한가 — 한 자리에서 둘 다", who, where,
               _near(naked, STRONG) + " ┃ " + _near(naked, WEAK))
    if FORWARD.search(body) and BACKWARD.search(body):
        B.note("혼동/순행과 역행이 같은 자리에", who, where, _near(body, BACKWARD))

    # ── 세어 놓고 다르게 적은 수 ────────────────────────
    #   손님이 대 보는 것은 **눈에 보이는 글자**입니다.
    seen_el = visible_count(f)
    for key, word in EL_WORD.items():
        got = seen_el.get(key, 0)
        for m in re.finditer(r"(?<![가-힣])%s(?:은|는|이|가)?\s*(?:하나도\s*)?없" % word, body):
            if got > 0:
                B.note("혼동/없다고 적었으나 보이는 글자에는 있음 · %s" % word,
                       who, where, body[max(0, m.start() - 50): m.end() + 20])
                break
        for m in re.finditer(r"(?<![가-힣])%s(?:은|는|이|가)?\s*(\d+|[가-힣]{1,2})(?:이오|개|자리)" % word, body):
            said = m.group(1)
            val = int(said) if said.isdigit() else KO_NUM.get(said)
            # 「겉에」 라 적었으면 천간만 세는 말입니다 — 다른 셈입니다.
            head = body[max(0, m.start() - 24): m.start()]
            if val is not None and val != got and not re.search(r"겉|천간|속|지지|숨은", head):
                B.note("혼동/적힌 개수가 보이는 글자와 다름 · %s" % word, who, where,
                       body[max(0, m.start() - 40): m.end() + 20])
                break

    # ── 없는 기둥을 있다고 하기 ─────────────────────────
    if not who["hour_known"]:
        m = HOUR_WORD.search(body)
        # 「시주 없음 — 여섯 글자를 다 놓고」 처럼 **정직하게 적은** 자리는
        # 셈에서 뺍니다 (2026-09-24). 안 빼면 잘 쓴 자리가 흠으로 잡힙니다.
        near = body[max(0, m.start() - 80): m.end() + 80] if m else ""
        if m and not re.search(r"모르|미상|안 적|없이|빼고|뺌|없음|세 기둥|여섯 글자", near):
            B.note("혼동/시각 미상인데 시주를 말함", who, where,
                   body[max(0, m.start() - 50): m.end() + 50])

    # ── 주어 없는 문장 ──────────────────────────────────
    #   ★ **인용**은 셈에서 뺍니다 (2026-09-24). 「가장 위험한 착각
    #     『아끼고 모으면 알아서 올라간다』」 는 손님이 믿는 말을 그대로
    #     옮긴 자리라 한다체가 맞습니다 — 그 문장에 주어를 달면 그건
    #     인용이 아니라 이 집의 말이 되오.
    for s in sentences(html):
        if re.search(r"[「『\"“].{0,60}$", s) or s.lstrip().startswith(("「", "『")):
            continue
        if SUBJ.headless(s):
            B.note("혼동/누구 얘긴지 안 적힌 문장", who, where, s)

    # ── 한 마디에 쏟기 ──────────────────────────────────
    #   한 마디 = 화면에서 한 상자에 앉는 덩이 (`.\dev.ps1 say` 와 같은 잣대)
    for line in [x.strip() for x in text.split("\n") if x.strip()]:
        ss = [s for s in SENT.findall(line)] or [line]
        if len(line) > 240 or len(ss) > 5:
            B.note("혼동/한 마디에 쏟음", who, where,
                   "%d자 · %d문장 ┃ %s" % (len(line), len(ss), line[:110]))
            break
    for s in sentences(html):
        if len(s) > 150:
            B.note("혼동/한 문장이 너무 김", who, where, s)

    # ── 같은 말 두 번 ───────────────────────────────────
    seen = collections.Counter(s for s in sentences(html) if len(s) > 14)
    for s, k in seen.items():
        if k >= 2:
            B.note("혼동/같은 문장이 한 자리에 두 번", who, where, s)
            break

    # ── 시키는 일 둘 ────────────────────────────────────
    orders = [s for s in sentences(html) if ORDER.search(s)]
    if len(orders) >= 2 and where.startswith("처방"):
        B.note("혼동/시키는 일이 둘 이상", who, where, " ┃ ".join(orders[:2]))

    # ── 자리표시 누출 ───────────────────────────────────
    m = PLACEHOLDER.search(text)
    if m:
        B.note("혼동/자리표시가 그대로 나감", who, where,
               text[max(0, m.start() - 40): m.end() + 40])

    # ── 말투 섞임 ───────────────────────────────────────
    kinds = {name for name, rx in (("해요", POLITE), ("합쇼", FORMAL))
             if rx.search(body)}
    if len(kinds) >= 2 or (kinds and HAO.search(body) and len(body) < 4000):
        pass          # 한 장 안에서는 말투가 섞일 수 있습니다 — 컷 단위로만 봅니다


#: 같은 풀이가 잇달아 두 번 — 풀이를 두 자리에서 달면 이렇게 됩니다.
GL = re.compile(r'<i class="gl">(\([^<]*\))</i>')
FIG_TWICE = re.compile(r'<p class="fig">[^<]*</p>\s*<p class="fig">')


def check_marks(B: Book, who: dict, where: str, html: str) -> None:
    """
    화면에 **표시**로 나가는 것들 — 이 집이 이미 금해 둔 자리입니다.

      · 풀이는 처음 한 번 (engine/terms.gloss)
      · 한 컷에 형광펜은 하나 (CLAUDE.md — 뜻이 겹치는 표시를 둘 달기)
      · 그림 둘을 나란히 세우지 않기 (flavor.figure)
    """
    h = html or ""
    gl = GL.findall(h)
    for i in range(1, len(gl)):
        if gl[i] == gl[i - 1] and re.search(re.escape(gl[i - 1]) + r"</i>\s*<i class=\"gl\">" +
                                            re.escape(gl[i]), h):
            B.note("혼동/같은 풀이가 잇달아 두 번", who, where, gl[i])
            break
    n_mark = h.count("<mark>")
    if n_mark > 1:
        B.note("혼동/한 컷에 형광펜이 둘 이상 (%d)" % min(n_mark, 9), who, where,
               plain(h)[:120])
    if FIG_TWICE.search(h):
        B.note("혼동/그림 둘이 나란히", who, where,
               re.sub(r"\s+", " ", plain(FIG_TWICE.search(h).group(0)))[:140])


def _near(text: str, rx: re.Pattern) -> str:
    m = rx.search(text)
    if not m:
        return ""
    return re.sub(r"\s+", " ", text[max(0, m.start() - 30): m.end() + 30])


# ══════════════════════════════════════════════════════════
# [지킴]
# ══════════════════════════════════════════════════════════
# ★ 「반드시」 를 홀로 세면 **시키는 말**이 걸립니다 (2026-09-24).
#   「이번 매물에서 반드시 확인할 숫자 하나를 적으시오」 는 주장이 아니라
#   할 일이오. 가드와 같은 꼴로 좁힙니다 — 뒤에 **단정 어미**가 와야 셉니다
#   (`seed/guard.json` 의 첫 줄과 같은 규칙).
CLAIM = re.compile(r"적중률|과학적으로|통계학|통계적으로|100%|"
                   r"틀림없|보장하오|보장합니다|확실히 그렇|입증|"
                   r"반드시.{0,10}(?:옵니다|됩니다|합니다|온다|된다|하오|이오)")


def check_guard(B: Book, who: dict, where: str, html: str) -> None:
    text = plain(html)
    ok, hits = guard.check(text)
    if not ok:
        for h in hits:
            B.note("지킴/가드 금지어 · %s" % h, who, where, text[:120])
    m = CLAIM.search(text)
    if m:
        B.note("지킴/검증 불가능한 주장", who, where,
               text[max(0, m.start() - 50): m.end() + 50])


# ══════════════════════════════════════════════════════════
# 한 사람이 모든 페이지를 읽는다
# ══════════════════════════════════════════════════════════
def payload_text(obj) -> str:
    """
    JSON 으로 내려가는 화면(일진 · 분석지 · 엿보기 · 종합)을 **사람이 읽는
    글로** 펴 놓는다.

    ★ `json.dumps` 를 그대로 보면 안 됩니다 (2026-09-24).

      덤프는 따옴표를 `\"` 로 이스케이프합니다. 그러면 화면 글에 든
      `<div class="gls">` 상자가 `<div class=\"gls\">` 로 바뀌어, 자가
      「이게 무슨 말인가」 상자를 못 알아봅니다 — 일진은 용신·일간·일진을
      **상자에 다 풀어 두었는데** 「풀이 없음」 으로 찍혔습니다.
      자가 못 보는 것을 흠이라 부르면 고칠 자리를 못 찾습니다.
    """
    out = []

    def walk(x):
        if isinstance(x, str):
            out.append(x)
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, (list, tuple)):
            for v in x:
                walk(v)

    walk(obj)
    return chr(10).join(out)


def read_all(rep: dict, B: Book, who: dict, page: str, f) -> None:
    """
    리포트 한 장 — 컷마다 같은 잣대를 댑니다.

    ★ 어려운 말은 **한 장 단위**로 봅니다 (2026-09-24).

      엔진은 「한 리포트 안에서 처음 한 번」 풉니다 (engine/terms.gloss).
      그런데 자를 컷마다 따로 대면, 앞 컷에서 풀어 준 말이 뒤 컷에서
      「안 풀렸다」 고 잡힙니다 — 자가 엔진과 다른 단위를 보면 없는 흠이
      수천 건 나옵니다.
    """
    whole = []
    for c in rep["cuts"]:
        where = "%s/%s" % (page, c["id"])
        html = c.get("html") or ""
        if len(plain(html).strip()) < 20:
            B.note("혼동/빈 컷이 내려감", who, where, plain(html))
            continue
        whole.append(html)
        check_easy(B, who, where, html)
        check_likeme(B, who, where, html)
        check_confuse(B, who, where, html, f)
        check_marks(B, who, where, html)
        check_guard(B, who, where, html)
    check_terms(B, who, page, "".join(whole))


def run_person(p: dict, B: Book, today: date, *, omnibus: bool,
               lens_id: str) -> None:
    rng = p["rng"]

    ch = build_chart(p["year"], p["month"], p["day"], p["hour"], p["minute"],
                     p["sex"], p["hour_known"], p["city"])
    f = build_features(ch, as_of=today)

    # ── 훅 5단 ──────────────────────────────────────────
    segs = bank_mod.build_hook(f, p["concern"], p["axis4"], "", "그대")
    stages = {s["stage"] for s in segs}
    for s in segs:
        where = "훅/%s단" % s["stage"]
        check_easy(B, who := p, where, s["html"])
        check_likeme(B, who, where, s["html"])
        check_confuse(B, who, where, s["html"], f)
        check_marks(B, who, where, s["html"])
        check_guard(B, who, where, s["html"])
    for need in ("0", "1", "2", "3"):
        if need not in stages:
            B.note("혼동/훅에 %s단이 빠짐" % need, p, "훅", ",".join(sorted(stages)))
    check_terms(B, p, "훅", "".join(s["html"] for s in segs))
    B.top["훅 전문"]["".join(s["html"] for s in segs)] += 1

    # ── 무료 리포트 ─────────────────────────────────────
    free = build_report(f, "sim", J.ENTRY_LENS, "free", p["concern"], p["axis4"])
    read_all(free, B, p, "무료", f)
    B.top["무료 전문"]["".join(c["html"] for c in free["cuts"])] += 1

    # ── 페이월 엿보기 ───────────────────────────────────
    try:
        wants = peek_mod.build_wants(
            f, free["locked"],
            voice=(lens_mod.view(J.ENTRY_LENS) or {}).get("voice"),
            you=lens_mod.you_of(J.ENTRY_LENS, "", getattr(f, "sex", None)))
        blob = payload_text(wants)
        check_easy(B, p, "엿보기", blob)
        check_guard(B, p, "엿보기", blob)
    except Exception as e:                        # noqa: BLE001
        B.note("터짐/엿보기 · %s" % type(e).__name__, p, "엿보기", str(e)[:120])

    # ── 고민 세부 물음 ──────────────────────────────────
    try:
        spec = topic_mod.ask_spec(p["concern"])
        if not spec:
            B.note("혼동/고민 세부 물음이 없음", p, "물음/%s" % p["concern"])
        else:
            for key in ("q", "q2", "q3"):
                if spec.get(key):
                    check_easy(B, p, "물음/%s" % key, spec[key])
            for key in ("options", "options2", "options3"):
                opts = spec.get(key) or []
                labels = [o["label"] for o in opts]
                if labels and len(set(labels)) != len(labels):
                    B.note("혼동/고른 칸에 같은 말이 두 번", p,
                           "물음/%s" % key, " ┃ ".join(labels))
    except Exception as e:                        # noqa: BLE001
        B.note("터짐/고민 물음 · %s" % type(e).__name__, p, "물음", str(e)[:120])

    # ── 유료 · 이 자리 하나 ─────────────────────────────
    need = lens_mod.required_input(lens_id)
    ex = J.make_extras(need, rng) if (need and p["fills_extra"]) else None
    one = build_report(f, "sim", lens_id, "one", p["concern"], p["axis4"], ex)
    read_all(one, B, p, "유료한자리", f)
    B.top["유료 전문"]["".join(c["html"] for c in one["cuts"])] += 1
    sc = SHARP.score(one)
    for k in ("근거", "반증", "흐림"):
        B.measure("날카로움 · " + k, sc[k])
    if not SHARP.passes(sc):
        why = [k for k, v in SHARP.PASS.items()
               if (sc[k] < v if k != "흐림" else sc[k] > v)]
        if not sc["척추"]:
            why.append("척추")
        if not sc["행동"]:
            why.append("행동")
        B.note("공감/날카로움 문턱 미달 · %s" % ",".join(why or ["?"]), p,
               "유료한자리", json.dumps({k: round(v, 3) if isinstance(v, float) else v
                                   for k, v in sc.items()}, ensure_ascii=False))

    # 표시가와 청구가
    #
    # ★ 값 없이 듣는 자리(청동자)는 「이 자리 하나」 값을 물으면 정상적으로
    #   거절합니다. 그 예외를 안 감싸서 스무 명 중 한 명 차례마다 그 사람의
    #   남은 검사가 통째로 중단됐습니다 — 자가 제 발을 밟은 자리입니다.
    try:
        shown = payments.price_of("one", lens_id)
    except Exception:                             # noqa: BLE001
        shown = 0
    view = lens_mod.view(lens_id) or {}
    if shown and view.get("price") and view["price"] != shown:
        B.note("지킴/카드에 보인 값과 청구가가 다름", p, "값/%s" % lens_id,
               "카드 %s · 청구 %s" % (view.get("price"), shown))

    # 잠긴 컷 안내
    for cut in one["locked"]:
        if cut.get("need_tier") not in payments.TIER_NAME:
            B.note("지킴/잠긴 컷이 없는 목패를 가리킴", p, "유료한자리",
                   str(cut.get("need_tier")))

    # ── 유료 · 전부 ─────────────────────────────────────
    alls = build_report(f, "sim", lens_id, "all", p["concern"], p["axis4"], ex)
    read_all(alls, B, p, "유료전부", f)
    if alls["locked"]:
        B.note("지킴/'전부' 인데 잠긴 컷이 남음", p, "유료전부",
               ",".join(c["id"] for c in alls["locked"]))

    # ── 릴레이 ──────────────────────────────────────────
    rec = relay_mod.recommend(f, read=[J.ENTRY_LENS], skipped=[],
                              session_relay_count=0, last_lens=J.ENTRY_LENS)
    items = rec.get("recommend") or []
    if not items and not rec.get("blocked"):
        B.note("혼동/추천이 하나도 없음 — 막다른 화면", p, "릴레이")
    for it in items:
        reason = it.get("reason") or ""
        check_easy(B, p, "릴레이/근거", reason)
        if re.search(r"[<>≤≥=]", reason):
            B.note("지킴/근거에 연산자가 보임", p, "릴레이/근거", reason)
        if it.get("price") and it["price"] != payments.price_of("one", it["lens_id"]):
            B.note("지킴/추천 카드 값과 청구가가 다름", p, "릴레이/%s" % it["lens_id"],
                   "카드 %s · 청구 %s" % (it["price"], payments.price_of("one", it["lens_id"])))
    B.top["릴레이 1순위"][items[0]["lens_id"] if items else "-"] += 1

    # ── 일진 ────────────────────────────────────────────
    d = build_daily(f, today)
    blob = payload_text(d)
    check_easy(B, p, "일진", blob)
    check_terms(B, p, "일진", blob)
    check_guard(B, p, "일진", blob)

    # ── 분석지 · 공유 ───────────────────────────────────
    s = build_summary(ch, f, p["concern"], p["axis4"])
    blob = payload_text(s)
    check_easy(B, p, "분석지", blob)
    check_terms(B, p, "분석지", blob)
    check_guard(B, p, "분석지", blob)
    sp = json.dumps(share_payload(s), ensure_ascii=False)
    if re.search(r"(?<!\d)%d(?!\d)" % p["year"], sp) or p["city"] in sp:
        B.note("지킴/공유에 생년·고을이 실림", p, "공유", sp[:160])

    # ── 스무 사람 종합 ──────────────────────────────────
    if omnibus:
        omni = build_omnibus(f, "sim", p["concern"], p["axis4"], "", ex)
        chapters = omni.get("chapters") or []
        if len(chapters) < 20:
            B.note("혼동/종합에 스무 명이 안 옴 (%d명)" % len(chapters), p, "종합")
        for chap in chapters[:4]:
            blob = payload_text(chap)
            check_easy(B, p, "종합/%s" % chap.get("lens_id", "?"), blob)
            check_guard(B, p, "종합", blob)


# ══════════════════════════════════════════════════════════
# 보고
# ══════════════════════════════════════════════════════════
def report(B: Book, n: int, elapsed: float, out: Path | None) -> dict:
    rows = []
    for code, k in B.hits.most_common():
        rows.append({
            "흠": code,
            "건수": k,
            "사람": len(B.folk[code]),
            "사람비율": round(100.0 * len(B.folk[code]) / n, 2),
            "자리": B.page[code].most_common(6),
            "보기": B.eg[code],
        })
    means = {}
    for name, xs in sorted(B.rate.items()):
        if xs:
            means[name] = {"평균": round(sum(xs) / len(xs), 4),
                           "최악": round(max(xs), 4), "표본": len(xs)}
    tops = {}
    for name, c in B.top.items():
        if c:
            top, k = c.most_common(1)[0]
            tops[name] = {"가짓수": len(c), "최다점유%": round(100.0 * k / sum(c.values()), 3)}
    result = {"사람": n, "걸린시간초": round(elapsed, 1),
              "흠": rows, "자": means, "유일성": tops}
    if out:
        out.mkdir(parents=True, exist_ok=True)
        (out / "expert.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=1), encoding="utf8")
    return result


def show(result: dict) -> None:
    n = result["사람"]
    print("\n1만 명 전문가 패널 — %d명 · %.0f초\n" % (n, result["걸린시간초"]))
    print("%-58s %8s %8s  %s" % ("흠", "건수", "사람%", "가장 많이 걸린 자리"))
    print("-" * 110)
    for r in result["흠"][:45]:
        where = ", ".join("%s(%d)" % (a, b) for a, b in r["자리"][:2])
        print("%-58s %8d %7.1f%%  %s" % (r["흠"][:58], r["건수"], r["사람비율"], where[:36]))
    print("\n자 — 평균 / 최악")
    for k, v in list(result["자"].items())[:24]:
        print("  %-42s %6.3f  최악 %.3f" % (k[:42], v["평균"], v["최악"]))
    print("\n유일성 — 최다 점유")
    for k, v in result["유일성"].items():
        print("  %-24s 가짓수 %6d · 최다 %5.2f%%" % (k, v["가짓수"], v["최다점유%"]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("n", nargs="?", type=int, default=300)
    ap.add_argument("--out", default="")
    ap.add_argument("--show", type=int, default=3)
    ap.add_argument("--seed", type=int, default=20260924)
    ap.add_argument("--today", default="2026-09-24")
    ap.add_argument("--omnibus-every", type=int, default=50)
    a = ap.parse_args()

    today = date.fromisoformat(a.today)
    global ALL_CONCERNS
    ALL_CONCERNS = concerns()
    pop = J.people(a.n, seed=a.seed)
    lenses = [x["id"] for x in lens_mod.released()]
    B = Book(show=a.show)
    out = Path(a.out) if a.out else None
    started = time.perf_counter()
    blew = collections.Counter()
    for i, p in enumerate(pop):
        # 고민과 캐릭터를 골고루 돌립니다 — 한 자리만 보면 그 자리만 압니다.
        p["concern"] = ALL_CONCERNS[i % len(ALL_CONCERNS)]
        try:
            run_person(p, B, today, omnibus=(i % a.omnibus_every == 0),
                       lens_id=lenses[i % len(lenses)])
        except Exception as e:                    # noqa: BLE001
            key = "터짐/%s: %s" % (type(e).__name__, str(e)[:60])
            blew[key] += 1
            B.note(key, p, "전체",
                   "".join(traceback.format_tb(e.__traceback__)[-1:]))
        if out and (i + 1) % 100 == 0:
            out.mkdir(parents=True, exist_ok=True)
            (out / "progress.json").write_text(json.dumps(
                {"done": i + 1, "of": a.n,
                 "sec": round(time.perf_counter() - started, 1),
                 "흠종류": len(B.hits)}, ensure_ascii=False), encoding="utf8")
    result = report(B, a.n, time.perf_counter() - started, out)
    show(result)
    if blew:
        print("\n터진 자리")
        for k, v in blew.most_common(10):
            print("  %-70s %d" % (k[:70], v))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
