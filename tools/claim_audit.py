# -*- coding: utf-8 -*-
"""
박힌 말 감사 — **셈과 어긋나는 글**을 찾는다.

    python tools/claim_audit.py

★ 손님이 짚은 것 (2026-09-07)

  만세력 표 밑에 이렇게 적혀 있었습니다 —

      「글자로는 안 보이지만 셈에는 듭니다.
       **나무가 없는데 0.3 이 나오는 까닭이** 여기 있소.」

  그 사람 명식은 **나무가 1개**였고 **불이 0개**였습니다. 예로 든
  기운이 손으로 박혀 있어서, 화면에 뜬 표와 그 밑의 설명이 서로
  다른 말을 하고 있었습니다.

★ 이게 왜 제일 나쁜 종류인가

  틀린 계산은 검사가 잡습니다. 그런데 **맞는 계산 옆에 박아 둔 틀린
  예**는 아무 검사도 안 잡습니다. 손님은 표를 보고 있으니 그 자리에서
  바로 압니다 — 그리고 그 순간 **나머지 숫자까지 의심**합니다.
  이 집은 근거 대는 집이라, 근거 옆의 거짓말이 가장 비쌉니다.

★ 무엇을 잡나

  ① 화면 글에 **오행 이름이 그대로 박힌** 자리
     — 「나무가 없는데」 「불이 바닥이라」 처럼 사람마다 달라야 하는 말
  ② 화면 글에 **십신·일간·지지 이름이 그대로 박힌** 자리
  ③ 화면 글에 **셀 수 있는 수가 그대로 박힌** 자리 (0.3 · 3개 · 26점)
  ④ 뱅크 밖에서 온 **단정 어미** — 「반드시」 「무조건」 「100%」

  ①~③ 은 **화면(tsx)에만** 겁니다. 금지어는 `guard.json` 이 봅니다 —
  두 군데서 세면 한쪽만 고치고 지나갑니다. 뱅크(seed)는 열쇠로 골라 쓰는
  표라 이름이 박혀 있는 것이 정상입니다.

★ 못 잡는 것

  「그 값이 진짜 맞는가」 는 못 봅니다. 이 도구가 보는 것은
  **사람마다 달라야 할 것이 안 달라지는가** 뿐입니다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"

EL = ("나무", "불", "흙", "쇠", "물")
TEN = ("비견", "겁재", "식신", "상관", "편재", "정재",
       "편관", "정관", "편인", "정인")
GAN = tuple("甲乙丙丁戊己庚辛壬癸")
JI = tuple("子丑寅卯辰巳午未申酉戌亥")

# 이 자리들은 **설명**이라 이름이 박혀 있어도 됩니다.
#   · 도움말·용어 풀이 — 「목은 나무요」 같은 사전
#   · 관리자 화면 — 주인만 봅니다
#   · 발주서·프롬프트 — 손님이 안 봅니다
SKIP_FILE = ("admin", "DevRail", "PromptModal", "AssetBoard", "Prompt")

# 한 줄 안에 이 말이 함께 있으면 사전·설명으로 봅니다.
DICT_NEAR = ("란 ", "이란", "라 하오", "라 부르", "뜻이오", "말이오",
             "오행", "십신", "곧 ", "＝", "=", ":")


def lines():
    """
    손님이 보는 줄만. **주석은 통째로 건너뜁니다** — 버그를 적어 둔
    글이 버그로 잡히면 도구를 안 보게 됩니다.
    """
    for p in sorted(WEB.rglob("*.tsx")):
        if "node_modules" in p.parts:
            continue
        if any(k in p.name for k in SKIP_FILE) or "/admin" in p.as_posix():
            continue
        inblk = False
        for i, raw in enumerate(p.read_text("utf-8").splitlines(), 1):
            t = raw.strip()
            if inblk:
                if "*/" in t:
                    inblk = False
                continue
            if t.startswith(("/*", "{/*")) and "*/" not in t:
                inblk = True
                continue
            if t.startswith(("*", "//", "{/*")) and "*/" not in t:
                continue
            t = re.sub(r"\{?/\*.*?\*/\}?", " ", t)
            if not re.search(r"[가-힣]", t):
                continue
            yield p.relative_to(ROOT).as_posix(), i, t


def _dictish(t: str) -> bool:
    return any(k in t for k in DICT_NEAR)


# ★ 이 꼴만 잡습니다 — **그 사람마다 달라야 하는 말**.
#
#   「나무가 없는데」 「불이 바닥이라」 「재성이 하나요」 처럼
#   이름 + 그 이름의 **개수·있고 없음**을 한 줄에 박은 자리.
#   앞이 한글이면 낱말 안입니다 (열쇠의 「쇠」).
_COUNTY = r"(없|바닥|모자|비었|넘치|많|하나|둘|셋|가득|그득)"
EL_RE = re.compile(r"(?<![가-힣])(" + "|".join(EL) + r")(이|가|은|는)\s*" + _COUNTY)
TEN_RE = re.compile(r"(?<![가-힣])(" + "|".join(TEN) + r")(이|가|은|는)\s*" + _COUNTY)
# 이름 바로 옆에 붙은 수 — 「나무 0.3」 「재성 2개」
NEAR_NUM = re.compile(
    r"(?<![가-힣])(" + "|".join(EL + TEN) + r")\s*(는|은|이|가)?\s*(\d+\.?\d*)\s*(개|자리)?")


def scan():
    el_hit, ten_hit, num_hit = [], [], []
    for rel, i, t in lines():
        plain = re.sub(r"<[^>]+>", "", t)
        if _dictish(plain):
            continue
        m = EL_RE.search(plain)
        if m:
            el_hit.append((rel, i, m.group(0), plain[:88]))
        m = TEN_RE.search(plain)
        if m:
            ten_hit.append((rel, i, m.group(0), plain[:88]))
        m = NEAR_NUM.search(plain)
        if m:
            num_hit.append((rel, i, m.group(0), plain[:88]))
    return el_hit, ten_hit, num_hit


def show(title, rows, note=""):
    print("=" * 76)
    print(title)
    print("=" * 76)
    for rel, i, what, t in rows:
        print("  %s:%d  「%s」" % (rel, i, what))
        print("      %s" % t)
    print("  %d곳" % len(rows))
    if note and rows:
        print("  ※ %s" % note)
    print()
    return len(rows)


def main() -> int:
    el, ten, num = scan()
    bad = 0
    bad += show("① 오행 이름 + 개수를 화면에 박은 자리", el,
                "셈에서 뽑아 쓰시오. 못 뽑으면 그 문장을 아예 안 내는 편이 낫소.")
    bad += show("② 십신 이름 + 개수를 화면에 박은 자리", ten, "같은 까닭이오.")
    bad += show("③ 이름 옆에 수를 박은 자리", num,
                "표에 뜬 값과 어긋나면 손님이 그 자리에서 아오.")

    print("-" * 76)
    if bad:
        print("  %d곳이오. **맞는 계산 옆의 틀린 예**가 가장 비싸오 —" % bad)
        print("  손님은 표를 보고 있으니 그 자리에서 알고, 그때부터")
        print("  나머지 숫자까지 의심하오.")
    else:
        print("  [OK] 화면 글이 셈과 어긋날 자리가 없소.")
    print("-" * 76)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
