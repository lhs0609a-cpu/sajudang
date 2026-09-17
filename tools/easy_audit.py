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
# ★ 「것 같소」 는 비유 표지가 아니라 **추측 어미**입니다 (2026-09-17).
#   「마음에 걸린 대목, 왜 반복됐을 것 같소?」 가 「풀지 않은 비유」 로
#   잡혔습니다. 손님에게 묻는 말이지 그림이 아니오.
FIGURE = re.compile(r"같이,|(?<!것 )같소|셈이오|셈이라|처럼|듯이|것과 같")
UNPACK = re.compile(r"그러니까|곧 |말이오|뜻이오|이란 |란 말")

TAG = re.compile(r"<[^>]+>")
SENT = re.compile(r"[^.?!]+[.?!]")
GLOSS = re.compile(r"\([^)]*\)")          # 풀이 괄호는 따로 셈에서 뺍니다

SOURCES = list((ROOT / "seed").glob("*.json")) + \
    list((ROOT / "services" / "api" / "engine").glob("*.py"))


# 화면 글에서 새 나온 **코드 조각** — 손님은 이걸 못 봅니다 (2026-09-17).
#
# ★ `engine/screenscan` 은 소스 순서로 읽습니다. 그래서 JSX 의 조건절이
#   글 사이에 섞여 「…0 && ` · 잠긴 자리 $ ▮ 컷`} 근거 · 입력한 명식…」
#   같은 **있지도 않은 문장**이 만들어지고, 그것이 흐릿한 문장으로
#   잡혔습니다. 고칠 글이 아니라 고칠 자가 없는 자리요.
#
#   `▮` 하나만 든 문장은 **뺍니다 안 합니다** — 그건 값이 들어갈
#   자리일 뿐 진짜 글줄입니다 (「끝까지 들은 자리는 ▮ 곳이오」).
#   `tools/easy_source` 는 ▮ 까지 통째로 뺐는데, 그러면 진짜 글도
#   같이 숨습니다.
CODEY = re.compile(r"&&|\{|\}|=>|className|\.length|\$")


def sentences(html: str) -> list:
    """한 문장씩. **덩이를 넘어서 잇지 않습니다.**

    ★ 화면 글은 줄바꿈으로 이어져 옵니다 (engine/screenscan 끝). 그
      덩이 하나하나가 화면에서 따로 앉는 것 — 문단 · 나레이션 한 줄 ·
      버튼입니다. 그런데 여기서 온 글을 마침표로만 갈랐더니, 마침표
      없이 끝나는 버튼이 **다음 덩이와 한 문장**이 됐습니다 —

          「맞습니다 아닙니다 잘 모르겠습니다 다음 마디 · 「…」.」

      손님은 이런 문장을 본 적이 없습니다. 고칠 글이 아니라 자가
      만든 문장이오. 줄바꿈에서 먼저 끊고, 그 안에서 마침표로 가릅니다.
      마침표 없이 끝난 꼬리도 한 덩이로 셉니다 — 근거 줄은 묶음표로
      끝나오.
    """
    t = _html.unescape(TAG.sub(" ", html.replace("<br />", " ")))
    out = []
    for line in t.split(chr(10)):
        line = re.sub(r"\s+", " ", line).strip()
        if not line:
            continue
        got = [x.strip() for x in SENT.findall(line)]
        tail = SENT.sub("", line).strip()
        if tail:
            got.append(tail)
        out += [x for x in got if len(x) > 6 and not CODEY.search(x)]
    return out


# 손에 잡히는 말 — 이게 하나라도 있으면 뜬 낱말 하나쯤은 그림이 됩니다.
#   ★ 「사람」 은 안 넣습니다. 「가르는 사람이라 흐릿한 자리에서」 가
#     바로 그 말로 흐릿했습니다.
CONCRETE = re.compile(
    r"돈|월급|삯|통장|저축|회사|직장|학교|가게|집|방|문|친구|동료|가족|부모|"
    r"배우자|윗사람|아랫사람|후배|선생|어머니|모임|계획|마감|날짜|시간|달력|"
    r"자격증|경력|이사|이직|출장|승진|출근|퇴근|책상|책|밥|국|끼니|잠|"
    r"\d|살|해|년|주|하루|밤|저녁|아침|말|글|일을|일이|일은|일에|"
    # ★ 한글 수도 수요 (2026-09-17). 「계절이 바뀌는 날 **스물넷**이오」
    #   를 자가 「손에 잡히는 것이 없다」 고 찍었습니다. 이 집은 수를
    #   한글로도 적소 — `\d` 만 보면 그 절반을 못 봅니다.
    r"하나|둘|셋|넷|다섯|여섯|일곱|여덟|아홉|열|스물|서른|마흔|쉰|"
    r"입춘|경칩|한 번|두 번")


def vague_of(s: str) -> tuple[int, bool]:
    """
    (뜬 낱말 수, 풀지 않은 비유). 뜬 낱말이 하나뿐이어도 **손에 잡히는
    말이 하나도 없으면** 둘로 셉니다 — 손님이 짚은 두 문장이 그 꼴이오.
    """
    bare = GLOSS.sub("", s)
    n = len(VAGUE_RE.findall(bare))
    if n == 1 and not CONCRETE.search(bare):
        n = 2
    # ★ 비유가 **그 문장 안에서 이미 땅에 닿았으면** 수수께끼가 아니오
    #   (2026-09-17).
    #
    #   「장터 장사처럼 크게 들어오고 크게 나가는 **돈**이오」 를 자가
    #   「풀지 않은 비유」 로 찍고 있었습니다. 「그러니까」 라는 표지가
    #   없다고요. 그런데 그 문장에는 돈이 있소 — 손님은 이미 그림을
    #   그렸습니다. 표지를 찾을 게 아니라 **닿았는지**를 봐야 하오.
    #
    #   「칼날처럼 센 힘이오」 는 그대로 걸립니다. 거기엔 손에 잡히는
    #   것이 없소.
    fig = (bool(FIGURE.search(bare)) and not UNPACK.search(bare)
           and not CONCRETE.search(bare))
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
