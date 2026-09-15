"""
쉬운 말 감사 — 초등학생이 읽고 **무슨 말인지** 아는가.

    python tools/easy_audit.py                  # 기본 명식 한 장
    python tools/easy_audit.py --birth 1993-11-25T15:50 --city 수원 \
        --sex M --concern work --axis4 INTJ --lens baegun
    python tools/easy_audit.py --show           # 흐릿한 문장 전부 · 어디서 왔나

★ 손님이 한 말 (2026-09-11)

  "가르는 사람이라 흐릿한 자리에서 유독 답답하오.
   곳간과 문간같이, 쌓는 데와 드나드는 데가 다르오.
   이런 것처럼 추상적이거나 애매한 건 다 쉬운 말로 바꿔 줘. 전체가
   초등학생도 이해가 될 정도로. 뭔 말인지 모르면 무슨 소용이야."

★ 어려운 **낱말**만 재던 도구는 이미 있습니다 (hard_words · plain_audit).
  그런데 손님이 짚은 두 문장에는 어려운 낱말이 **하나도 없습니다.**
  「가르는」 「흐릿한」 「자리」 「곳간」 — 다 아는 말인데, 무슨 뜻인지
  모릅니다. 쉬운 낱말로 **흐릿하게** 말한 것입니다.

★ 흐릿한 문장 — 이 도구가 세는 것

  ① 뜬 낱말   자리 · 결 · 기운 · 판 · 온도 · 그릇 · 틀 · 쪽 · 데 …
              명리가 쓰는 **빈 그릇 같은 말**. 무엇이 담겼는지 안 말하면
              손님은 그림을 못 그립니다.
  ② 풀지 않은 비유  「A같이, B」 「A인 셈이오」 — 비유만 던지고
              **그래서 손님 삶에서 무엇인지**를 안 대면 수수께끼입니다.
  ③ 주어 없는 문장  누가 그렇다는 것인지 없으면 사전 뜻풀이입니다.

  뜬 낱말이 **둘 이상**이거나, 비유를 풀지 않았으면 흐릿하다고 봅니다.

★ 쉬운 말의 기준 (뱅크를 고칠 때)

  · 누가 · 언제 · 무엇을 하는지로 말한다 — 「자리」 대신 회사·돈·친구·집
  · 비유를 쓰면 **바로 뒤에** 「그러니까 ~라는 말이오」 로 푼다
  · 한 문장에 한 뜻. 스무 자 넘는 문장은 둘로 끊는다
  · 말투(하오체 · 「그대」)는 그대로 — voice 층이 캐릭터마다 갈아 끼웁니다
"""
from __future__ import annotations

import argparse
import html as _html
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "services" / "api") not in sys.path:
    sys.path.insert(0, str(ROOT / "services" / "api"))

from engine.calendar import build_chart           # noqa: E402
from engine.features import build_features       # noqa: E402
from engine.report import build_report           # noqa: E402

# ① 뜬 낱말 — 뒤에 무엇이 담겼는지 안 말하면 빈 그릇
VAGUE = ["자리", "결", "기운", "판", "온도", "그릇", "틀", "마디", "칸", "바탕",
         "몫", "땔감", "곳간", "문간", "볕", "저울", "철", "쪽", "데서", "데가",
         "데는", "흐름", "힘이", "힘은", "힘을", "얼굴", "길이", "길을"]
VAGUE_RE = re.compile("|".join(
    r"(?<![가-힣])%s(?=[이가은는을를의에도로와과만]|[ ,.]|$)" % w if len(w) == 1
    else re.escape(w) for w in VAGUE))
# ② 비유 표지 — 뒤에 풀이가 없으면 수수께끼
FIGURE = re.compile(r"같이,|같소|셈이오|셈이라|처럼|듯이|것과 같")
UNPACK = re.compile(r"그러니까|곧 |말이오|뜻이오|이란 |란 말")

TAG = re.compile(r"<[^>]+>")
SENT = re.compile(r"[^.?!]+[.?!]")
GLOSS = re.compile(r"\([^)]*\)")          # 풀이 괄호는 따로 셈에서 뺍니다

SOURCES = list((ROOT / "seed").glob("*.json")) + \
    list((ROOT / "services" / "api" / "engine").glob("*.py"))


def sentences(html: str) -> list:
    t = _html.unescape(TAG.sub(" ", html.replace("<br />", " ")))
    t = re.sub(r"\s+", " ", t)
    return [s.strip() for s in SENT.findall(t) if len(s.strip()) > 6]


# 손에 잡히는 말 — 이게 하나라도 있으면 뜬 낱말 하나쯤은 그림이 됩니다.
#   ★ 「사람」 은 안 넣습니다. 「가르는 사람이라 흐릿한 자리에서」 가
#     바로 그 말로 흐릿했습니다.
CONCRETE = re.compile(
    r"돈|월급|통장|회사|직장|학교|가게|집|친구|동료|가족|부모|배우자|윗사람|"
    r"아랫사람|후배|선생|계획|마감|날짜|시간|달력|자격증|경력|이사|이직|출장|"
    r"\d|살|해|년|주|하루|밤|저녁|아침|말|글|일을|일이|일은|일에")


def vague_of(s: str) -> tuple[int, bool]:
    """
    (뜬 낱말 수, 풀지 않은 비유). 뜬 낱말이 하나뿐이어도 **손에 잡히는
    말이 하나도 없으면** 둘로 셉니다 — 손님이 짚은 두 문장이 그 꼴이오.
    """
    bare = GLOSS.sub("", s)
    n = len(VAGUE_RE.findall(bare))
    if n == 1 and not CONCRETE.search(bare):
        n = 2
    fig = bool(FIGURE.search(bare)) and not UNPACK.search(bare)
    return n, fig


def where(s: str) -> str:
    """이 문장이 어디서 왔나 — 앞 열두 자로 찾습니다. 못 찾으면 조립된 문장."""
    bare = GLOSS.sub("", s)
    probe = re.sub(r"\s+", " ", bare)[:12].strip()
    if len(probe) < 6:
        return "?"
    for p in SOURCES:
        try:
            for i, line in enumerate(p.read_text("utf-8").splitlines(), 1):
                if probe in TAG.sub("", line):
                    return "%s:%d" % (p.relative_to(ROOT).as_posix(), i)
        except UnicodeDecodeError:
            continue
    return "조립"


def audit(rep: dict) -> tuple[int, list]:
    total, bad = 0, []
    for c in rep["cuts"]:
        for s in sentences(c["html"]):
            total += 1
            n, fig = vague_of(s)
            if n >= 2 or fig:
                bad.append((c["id"], n, fig, s))
    return total, bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--birth", default="1993-11-25T15:50")
    ap.add_argument("--city", default="수원")
    ap.add_argument("--sex", default="M")
    ap.add_argument("--concern", default="work")
    ap.add_argument("--axis4", default="INTJ")
    ap.add_argument("--lens", default="baegun")
    ap.add_argument("--tier", default="one")
    ap.add_argument("--today", default=date.today().isoformat())
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()
    dt = datetime.fromisoformat(a.birth)
    f = build_features(build_chart(dt.year, dt.month, dt.day, dt.hour,
                                   dt.minute, a.sex, True, a.city),
                       as_of=date.fromisoformat(a.today))
    rep = build_report(f, "audit", a.lens, a.tier, a.concern, a.axis4)
    total, bad = audit(rep)
    by_cut = Counter(c for c, _, _, _ in bad)
    print("문장 %d개 중 흐릿한 문장 %d개 (%.0f%%)"
          % (total, len(bad), 100 * len(bad) / max(total, 1)))
    print("  컷별: " + " · ".join("%s %d" % kv for kv in by_cut.most_common()))
    if a.show:
        for cid, n, fig, s in bad:
            print("\n[%s] 뜬말 %d%s  ← %s\n  %s"
                  % (cid, n, " · 풀지 않은 비유" if fig else "", where(s), s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
