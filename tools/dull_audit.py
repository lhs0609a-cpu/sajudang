# -*- coding: utf-8 -*-
"""
왜 안 와닿는가 — 무료 구간 한 장을 **손님 눈으로** 세는 자.

    python tools/dull_audit.py             200명
    python tools/dull_audit.py --n 1000
    python tools/dull_audit.py --show 1    한 사람 몫에서 걸린 자리를 펴 본다

★ 왜 이 자를 새로 세우나 (2026-09-25)

  손님이 무료 구간 전문을 그대로 붙여 놓고 말했습니다 —
  「왜 전체가 풀이가 어렵고 와닿지가 않지? 전체 다 그래.」

  이 집에는 이미 자가 많습니다. `easy_audit`(쉬운 말) · `sharp_audit`
  (팩폭) · `likeme`(내 얘기 같은가) · `dup_rate`(문장 겹침) · `skim_audit`.
  그런데 그 자들은 다 **통과**하고 있었습니다. 까닭은 재는 단위입니다 —

      dup_rate      같은 문장이 **여러 사람 사이에서** 겹치는가
      easy_audit    한 **문장**이 흐린가
      likeme        천 자에 장면이 몇 줄인가

  손님이 읽는 것은 **한 장**입니다. 한 장 안에서 같은 근거 줄이 다섯 번,
  같은 괄호가 여섯 번, 시키는 일이 여덟 개 나오는 것은 위의 어느 자에도
  안 걸립니다. 문장 하나하나는 쉽고, 사람끼리도 안 겹치니까요.

  그래서 이 자는 **한 장 안**을 봅니다.

★ 세는 것 여덟

  ① 되풀이     같은 문장이 한 장에 두 번 이상 — 낭비된 글자수
  ② 근거 줄    글자 그대로 같은 근거 줄이 몇 번
  ③ 괄호       같은 낱말에 풀이가 몇 번 · 괄호가 먹는 글자 몫
  ④ 시키는 일  한 장에 몇 개 (CLAUDE.md — 둘이면 하나도 안 한다)
  ⑤ 유인 문구  페이월로 부르는 말이 몇 번
  ⑥ 속말 유출  「판정 안 함」 「사용자」 처럼 집 안에서만 쓰는 말
  ⑦ 뜬 수      본문에 나온 수 가운데 **무엇을 센 수인지** 안 적힌 것
  ⑧ 분량       한 장 글자수 · 컷 수 · 한 컷 평균

  ①~③ 은 「어렵다」의 정체입니다. 글이 어려운 게 아니라 **같은 말이
  자꾸 끼어들어** 읽는 줄기가 끊기는 것입니다.
  ④~⑦ 은 「안 와닿는다」 쪽입니다.
"""
from __future__ import annotations

import argparse
import collections
import html as _html
import random
import re
import statistics
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "services" / "api", ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine import lens as lens_mod                 # noqa: E402
from engine.bank import build_hook                  # noqa: E402
from engine.calendar import build_chart             # noqa: E402
from engine.features import build_features          # noqa: E402
from engine.report import build_report              # noqa: E402
from schemas.api import Concern                     # noqa: E402
from typing import get_args

TAG = re.compile(r"<[^>]+>")
GLOSS = re.compile(r'<i class="gl">\(([^)]*)\)</i>')
SENT = re.compile(r"[^.?!]+[.?!]")
AS_OF = date(2026, 8, 27)
#: 고민 목록은 `schemas.api.Concern` 한 자리에서 받습니다 — 자를 제품보다
#: 좁게 두면 새 칸의 사고를 아무 자도 못 봅니다 (CLAUDE.md).
CONCERNS = get_args(Concern)

#: 시키는 말 — 뱅크는 하오체 한 벌이라 「…시오」 꼴이 기본입니다.
ORDER = re.compile(r"(시오|하십시오|하세요|보세요|적으세요)[.!]?$")

#: **읽는 자리에서 대 보라는 말**은 시키는 일이 아닙니다 (2026-09-25).
#
# ★ 처음에는 「…시오」 꼴을 다 세었습니다. 그랬더니 「세어 보시오」
#   「겪은 일과 맞춰 보시오」 가 오늘 할 일로 잡혔습니다. 그건 이 집이
#   일부러 두는 줄입니다 — 손님이 만세력을 펴고 대 볼 수 있어야 근거요
#   (CLAUDE.md 「근거 줄에 수를 안 대기」). 손이 가는 일과 눈이 가는 일은
#   달리 셉니다. 섞어 세면 지우지 말아야 할 줄을 지우게 됩니다.
CHECK = re.compile(r"(세어|맞춰|떠올려|견줘|대\s?보|읽어|보고)\s*[^.]{0,6}"
                   r"(보시오|보세요|시오)[.!]?$")

#: 뜻이 있는 겹말. 이건 되풀이가 아니라 한 낱말입니다.
_REDUP = {"그때", "꼬박", "차근", "차곡", "하나", "이제", "따로", "번번",
          "더더", "곰곰", "두근", "조금", "가끔", "종종", "자주", "울며"}

#: 페이월로 부르는 말. 한 장에 여러 번 나오면 글이 아니라 광고가 됩니다.
#
# ★ 이 칸은 **화면 파일까지** 봐야 정직합니다 (2026-09-25). 서버는 잠긴 컷
#   목록만 내려보내고, 그걸 몇 번 그릴지는 화면이 정합니다. 처음에는 서버
#   목록 길이를 세서, 화면을 고쳐도 눈금이 안 움직였습니다 — 자가 제품보다
#   좁으면 고친 것이 안 보입니다.
LURE = ("이 풀이 열기", "결제하기", "여기서 결론이 갈립니다", "이 자리 하나",
        "구매 후 공개", "결제 후 열리는")

#: 무료 한 장에서 잠긴 풀이를 맛보이는 상자가 **몇 자리에** 서는가.
#   `apps/web/components/InlinePaidReading.tsx` 한 자리에서 읽습니다 —
#   여기 손으로 적으면 두 벌이 되어, 고친 뒤에도 자가 옛 수를 냅니다.
_SLOTS = re.compile(r"INLINE_READING_SLOTS = \[(.*?)\]", re.S)


def inline_slots() -> int:
    src = ROOT / "apps" / "web" / "components" / "InlinePaidReading.tsx"
    if not src.exists():
        return -1
    m = _SLOTS.search(src.read_text(encoding="utf-8"))
    return len(re.findall(r"'[^']+'", m.group(1))) if m else -1

#: 집 안에서만 쓰는 말. 화면에 나오면 손님은 무슨 말인지 모릅니다.
INSIDE = ("판정 안 함", "사용자", "QUEST", "tier", "None", "null",
          "free", "concern", "axis4")

#: 「무엇을 센 수인지」를 적어 주는 낱말. 수 뒤에 이게 없으면 손님은 그
#: 수가 어디서 나왔는지 모릅니다.
COUNTED = ("자", "개", "곳", "명", "살", "년", "해", "번", "분", "%", "월",
           "글자", "칸", "쪽", "만", "시", "도", "일", "원", "째", "쌍", "줄")

#: 날짜·시각·좌표는 **무엇인지 명백한 수**입니다 — 뜬 수로 세면 자가 거짓을
#: 말합니다. 명식 컷의 「1993-04-05 03:37」 「15:00 → 14:28」 「동경 135°」
#: 「1961.8~」 가 그렇습니다 (2026-09-25에 자를 고쳤습니다).
PLAIN_NUM = re.compile(
    r"\d{4}-\d\d-\d\d|\d{1,2}:\d\d|\d+°|\d{4}\.\d+|-?\d+\.\d+분|\d{4}~|\d+~")


def plain(html: str) -> str:
    return re.sub(r"\s+", " ", _html.unescape(TAG.sub(" ", html or ""))).strip()


def sentences(text: str) -> list:
    got = [s.strip() for s in SENT.findall(text)]
    tail = SENT.sub("", text).strip()
    if tail:
        got.append(tail)
    return [s for s in got if len(s) > 6]


def _one(rng: random.Random) -> dict:
    y = rng.randint(1960, 2007)
    mo, d = rng.randint(1, 12), rng.randint(1, 28)
    h, mi = rng.randint(0, 23), rng.randint(0, 59)
    sex = rng.choice(("M", "F"))
    known = rng.random() > 0.15
    concern = rng.choice(CONCERNS)
    axis4 = rng.choice((None, "INFP", "ESTJ", "INTP", "ENFJ", "ISTP"))
    f = build_features(build_chart(y, mo, d, h, mi, sex, hour_known=known),
                       as_of=AS_OF)
    segs = build_hook(f, concern, axis4)
    rep = build_report(f, "m", "nopa", "free", concern, axis4)
    blocks = []
    for s in segs:
        blocks.append({"where": "훅%s" % s["stage"], "title": s["label"],
                       "html": s["html"], "source": s.get("source") or ""})
    for c in rep["cuts"]:
        blocks.append({"where": "무료", "title": c["title"],
                       "html": c["html"], "source": c.get("source") or ""})
    return {"concern": concern, "axis4": axis4, "blocks": blocks,
            "locked": rep["locked"]}


def audit(page: dict) -> dict:
    bodies = [plain(b["html"]) for b in page["blocks"]]
    # ★ 근거 줄도 손님이 읽는 글입니다. 셈에서 빼 두었다가 「판정 안 함」
    #   같은 속말을 못 봤습니다 — 자가 화면보다 좁으면 그 자리는 안 보입니다.
    whole = " ".join(bodies + [plain(b["source"]) for b in page["blocks"]]
                     + [b["title"] or "" for b in page["blocks"]])
    n_chars = sum(len(x) for x in bodies)

    # ① 되풀이 — 같은 문장이 한 장에 두 번 이상
    bag = collections.Counter()
    for b in bodies:
        for s in sentences(b):
            bag[s] += 1
    twice = {s: c for s, c in bag.items() if c > 1}
    waste = sum(len(s) * (c - 1) for s, c in twice.items())

    # ①-2 낱말이 **곧바로** 되풀이된 자리.
    #
    # ★ 「삼거리 노파삼거리 노파가 먼저 읽은 사람의 모습」 이 스무 명 가운데
    #   열아홉의 첫 컷 첫 줄로 나가고 있었습니다 (2026-09-25). `bank.josa` 는
    #   낱말째 돌려주는데(`josa("나무","이","가")` → "나무가") 조립하는 쪽이
    #   앞에 이름을 또 붙였습니다.
    #
    #   문장 되풀이 셈으로는 안 걸립니다 — 한 문장 **안**이기 때문입니다.
    #   겹말(그때그때·꼬박꼬박)은 뜻이 있는 말이라 걷어 냅니다.
    echo = [m.group(1) for m in re.finditer(r"([가-힣]{2,7})\1", whole)
            if m.group(1) not in _REDUP]

    # ② 근거 줄 — **꼬리를 따로** 셉니다.
    #
    #   ★ 줄 전체로 세면 안 걸립니다. 앞은 센 값이라 컷마다 다르고, 뒤의
    #     「어떻게 읽는가」 설명만 글자 그대로 같습니다 — 손님 눈에는 그
    #     꼬리가 컷마다 다시 나오는 사전이오.
    srcs = [plain(b["source"]) for b in page["blocks"] if b["source"]]
    src_bag = collections.Counter(srcs)
    src_top, src_top_n = src_bag.most_common(1)[0] if src_bag else ("", 0)
    src_waste = sum(len(s) * (c - 1) for s, c in src_bag.items() if c > 1)
    tails = [x.split("—", 1)[1].strip() for x in srcs if "—" in x]
    tail_bag = collections.Counter(tails)
    tail_top, tail_top_n = tail_bag.most_common(1)[0] if tail_bag else ("", 0)
    tail_waste = sum(len(t) * (c - 1) for t, c in tail_bag.items() if c > 1)

    # ③ 괄호 — 같은 낱말에 풀이가 몇 번
    gl = collections.Counter()
    gl_chars = 0
    for b in page["blocks"]:
        for m in GLOSS.finditer(b["html"] + " " + (b["source"] or "")):
            gl[m.group(1)] += 1
            gl_chars += len(m.group(1)) + 2
    gl_again = sum(c - 1 for c in gl.values() if c > 1)

    # ④ 시키는 일 — 한 장 합계와 **한 컷 최다**를 같이 봅니다.
    #   컷 하나에 둘이 들면 손님은 그 컷에서 하나도 안 합니다 (CLAUDE.md).
    per_cut = [[s for s in sentences(b)
                if ORDER.search(s) and not CHECK.search(s)] for b in bodies]
    orders = [s for g in per_cut for s in g]
    order_worst = max((len(g) for g in per_cut), default=0)
    order_over = sum(1 for g in per_cut if len(g) > 1)
    checks = [s for b in bodies for s in sentences(b) if CHECK.search(s)]

    # ⑤ 유인 문구 — 서버 글에 몇 번. 화면이 몇 번 그리는지는 `inline_slots`.
    lure = sum(whole.count(w) for w in LURE)

    # ⑥ 속말 유출
    inside = collections.Counter()
    for w in INSIDE:
        n = len(re.findall(r"(?<![A-Za-z가-힣])%s(?![A-Za-z가-힣])" % re.escape(w),
                           whole))
        if n:
            inside[w] = n

    # ⑦ 뜬 수 — 무엇을 센 수인지 안 적힌 것
    #   ★ **본문과 근거 줄만** 봅니다. 컷 제목까지 넣었더니 단 번호
    #     (「1 · 먼저, 사주로 못 정하는 것」 의 1)가 뜬 수로 잡혔습니다 —
    #     차례를 가리키는 수는 손님이 무엇인지 압니다.
    #   날짜·시각·좌표 자리도 걷어 냅니다 (PLAIN_NUM 머리말).
    scan = PLAIN_NUM.sub(" ", " ".join(
        bodies + [plain(b["source"]) for b in page["blocks"]]))
    loose = []
    for m in re.finditer(r"\d[\d,]*", scan):
        near = scan[m.end():m.end() + 4]
        if not any(w in near for w in COUNTED):
            loose.append(scan[max(0, m.start() - 12):m.end() + 4].strip())

    return {"chars": n_chars, "cuts": len(bodies),
            "per_cut": n_chars / max(1, len(bodies)),
            "twice": twice, "waste": waste, "echo": echo,
            "src_n": len(srcs), "src_kinds": len(src_bag),
            "src_top": src_top, "src_top_n": src_top_n, "src_waste": src_waste,
            "tail_kinds": len(tail_bag), "tail_top": tail_top,
            "tail_top_n": tail_top_n, "tail_waste": tail_waste,
            "src_chars": sum(len(x) for x in srcs),
            "gl_again": gl_again, "gl_chars": gl_chars, "gl": gl,
            "orders": orders, "order_worst": order_worst,
            "order_over": order_over, "checks": checks,
            "lure": lure, "inside": inside, "loose": loose}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--show", type=int, default=0)
    ap.add_argument("--seed", type=int, default=20260925)
    a = ap.parse_args()
    rng = random.Random(a.seed)

    rows = []
    for _ in range(a.n):
        rows.append(audit(_one(rng)))

    def avg(k):
        return statistics.mean(r[k] for r in rows)

    print("\n왜 안 와닿는가 — 무료 구간 한 장을 손님 눈으로 (%d명)" % a.n)
    print("=" * 74)
    print("\n  분량")
    print("    한 장 %d자 · 컷 %.1f개 · 한 컷 평균 %d자"
          % (avg("chars"), avg("cuts"), avg("per_cut")))

    print("\n  ① 되풀이 — 같은 문장이 한 장에 두 번 이상")
    print("    한 장에 %.1f종 · 낭비된 글자 %d자 (본문의 %.1f%%)"
          % (statistics.mean(len(r["twice"]) for r in rows),
             avg("waste"), 100 * avg("waste") / avg("chars")))
    print("    낱말이 곧바로 되풀이된 자리 %.1f개  %s"
          % (statistics.mean(len(r["echo"]) for r in rows),
             sorted({w for r in rows for w in r["echo"]})[:4] or ""))

    print("\n  ② 근거 줄")
    print("    한 장에 %.1f줄인데 종류는 %.1f가지 · 낭비 %d자 (본문의 %.1f%%)"
          % (avg("src_n"), avg("src_kinds"), avg("src_waste"),
             100 * avg("src_waste") / avg("chars")))
    print("    근거 줄이 먹는 글자 %d자 (본문의 %.1f%%)"
          % (avg("src_chars"), 100 * avg("src_chars") / avg("chars")))
    print("    ★ 꼬리(어떻게 읽는가 설명)는 %.1f가지뿐 — 가장 많이 깔린 것이 %.1f번"
          % (avg("tail_kinds"), avg("tail_top_n")))
    print("      되풀이된 꼬리 글자 %d자 (본문의 %.1f%%)"
          % (avg("tail_waste"), 100 * avg("tail_waste") / avg("chars")))

    print("\n  ③ 괄호 풀이")
    print("    되풀이된 풀이 %.1f개 · 괄호가 먹는 글자 %d자 (본문의 %.1f%%)"
          % (avg("gl_again"), avg("gl_chars"),
             100 * avg("gl_chars") / avg("chars")))

    print("\n  ④ 시키는 일 — 한 장에 %.1f개 · 한 컷에 최다 %.1f개 · "
          "둘 이상인 컷 %.1f개"
          % (statistics.mean(len(r["orders"]) for r in rows),
             avg("order_worst"), avg("order_over")))
    print("      (대 보라는 말 %.1f개는 따로 셉니다 — 근거요)"
          % statistics.mean(len(r["checks"]) for r in rows))

    print("\n  ⑤ 페이월로 부르는 말 — 서버 글에 %.1f번 · "
          "화면이 맛보기 상자를 세우는 자리 %d곳"
          % (avg("lure"), inline_slots()))

    ins = collections.Counter()
    for r in rows:
        ins.update(r["inside"])
    print("\n  ⑥ 속말 유출 — %s" % (dict(ins.most_common(6)) or "없소"))

    print("\n  ⑦ 뜬 수 — 무엇을 센 수인지 안 적힌 수가 한 장에 %.1f개"
          % statistics.mean(len(r["loose"]) for r in rows))

    if a.show:
        for r in rows[:a.show]:
            print("\n" + "-" * 74)
            print("  한 사람 몫에서 걸린 자리")
            print("\n  되풀이된 문장:")
            for s, c in sorted(r["twice"].items(), key=lambda x: -len(x[0]))[:6]:
                print("    %d번 · %s" % (c, s[:64]))
            print("\n  되풀이된 풀이:")
            for w, c in r["gl"].most_common(6):
                if c > 1:
                    print("    %d번 · (%s)" % (c, w[:44]))
            print("\n  시키는 일 %d개:" % len(r["orders"]))
            for s in r["orders"][:8]:
                print("    · %s" % s[:64])
            print("\n  가장 여러 번 깔린 근거 줄 (%d번):" % r["src_top_n"])
            print("    %s" % r["src_top"][:150])
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
