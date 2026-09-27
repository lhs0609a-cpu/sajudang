# -*- coding: utf-8 -*-
"""
무료 구간이 **무엇으로 채워져 있나** — 줄마다 갈라 세는 자.

    python tools/verdict_mix.py             200명
    python tools/verdict_mix.py --show 1    첫 화면을 줄마다 펴 본다

★ 왜 이 자를 만드나 (2026-09-25 · 세 번째)

  손님이 말했습니다 — 「너무 내용만 길고 뭔소리인지 하나도 모르겠어. 이
  사람에 대해 완벽하게 파악해서 날카롭게 질문하고, 이런 사람이다, 이런 것
  때문에 꼬였을 거다, 이런 식으로 진짜 헉 소리 나게 만들어야 하는데.」

  앞선 두 자는 **겹침**을 셌습니다 (`dull_audit` 글자 · `same_point` 뜻).
  이 자는 다른 것을 셉니다 — 한 줄 한 줄이 **무슨 일을 하는가.**

★ ★ 이 자가 처음에 **딴 물건을 재고 있었습니다** (2026-09-27에 고침)

  훅을 `bank.build_hook` 으로 재고 있었습니다. 손님이 보는 훅은
  `routers/hook` 이 만들고, 거기에 네 층이 더 얹힙니다 — 자세한 것은
  아래 `seen_page` 머리말에.

  그래서 처음 적어 둔 수치(「첫 화면 446자 · 단정 0줄 · 사전 33%」)는
  **분석지의 것**이었습니다. 자를 맞추고 다시 재니 —

      첫 화면 = `portrait` 「어떤 사람인가」 · 366자 · 10줄
          그림 36% · 인과 9% · 셈 10% · 몸사림 10%

  그리고 그 열 줄 가운데 **여섯을 「그밖」 으로** 세고 있었습니다. 열어
  보니 이 집에서 가장 잘 쓴 글이었습니다 —

      「요새 — 전에 통하던 것이 안 통하네.
        방법이 낡은 것이 아니라 판이 바뀐 것이네.」
      「맡으면 끝까지 하는데, 이미 넘겨도 될 일의 단톡방을 아직 못
        나가고 있네.」

  손님이 「이런 사람이다」 라 바란 그것이고, 물건이 들었고, 겪은 일을
  짚습니다. 자가 그걸 못 세면 **고칠 데가 아닌 자리를 가리킵니다.**
  그래서 「그림」 칸을 새로 세웠습니다.

★ 아홉으로 갈라 셉니다

  단정    이 사람이 어떤 사람인지 **말하는** 줄 (「~ 자리요」 「~ 사람이오」)
  그림    이 사람을 **그리는** 줄 — 장면과 물건이 든 줄
  인과    「그래서 이렇게 꼬였다」 — 원인과 결과를 잇는 줄
  셈      센 값을 대는 줄
  물음    되묻는 줄
  사전    낱말 뜻을 푸는 줄
  몸사림  못 한다 · 아니다 · 단정할 수 없다
  시킴    오늘 할 일
  그밖    아직 못 가린 줄 — **이 칸이 크면 자를 의심하시오**

  **첫 화면**을 따로 봅니다 — 거기서 손님이 살지 나갈지 정합니다.
"""
from __future__ import annotations

import argparse
import collections
import html as _html
import random
import re
import statistics
import sys
from pathlib import Path
from typing import get_args

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "services" / "api", ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

#: 손님이 **실제로 받는 글**은 `tools/seen_page` 한 자리에서 받습니다.
#
# ★ 이 자는 `bank.build_hook` 을 부르고 있었습니다 (2026-09-27에 고침).
#   그건 분석지(`engine/summary`)와 도구(`engine/screenscan`)만 쓰는
#   자리요. 손님 훅은 `routers/hook` 이 만들고, 그 라우터는 네 층을 더
#   얹습니다 — portrait · topic · specialist · 말투.
#
#   그래서 이 자가 낸 훅 수치는 **다른 물건의 것**이었습니다. 자를
#   제품보다 좁게 두는 것보다 나쁩니다 — 좁으면 못 보고 끝나지만, 다른
#   것을 재면 **고친 줄 알고 넘어갑니다.** 실제로 그렇게 됐습니다:
#   씨앗 55줄을 고쳐 배포했는데 손님 화면에는 안 닿았고 자는 「고쳤다」
#   고 찍었습니다.
#
#   조립을 자마다 흉내 내지 않습니다 — 라우터가 층을 하나 더 얹는 날
#   자들이 조용히 옛 물건을 재기 시작하오.
#   `tests/test_seen_page.py` 가 그 어긋남을 셉니다.
from engine import portrait as _portrait             # noqa: E402
from tools.seen_page import free_page as _free_page   # noqa: E402
from tools.seen_page import sample as _sample         # noqa: E402
from tools.seen_page import lens as _lens_of          # noqa: E402
from schemas.api import Concern                     # noqa: E402

TAG = re.compile(r"<[^>]+>")
SENT = re.compile(r"[^.?!]+[.?!]")
CONCERNS = get_args(Concern)

# ── 줄의 일감을 가리는 자 ─────────────────────────────────────
#
# ★ 차례가 중요합니다. 앞의 것이 이깁니다 — 한 줄이 여러 일을 하면 **가장
#   센 일**로 셉니다. 물음표가 붙은 단정은 단정이 아니라 물음입니다.

#: 몸사림 — 판단을 **거두는** 줄. 이 집의 규칙이 만든 줄이라 필요하되,
#: 한 장에 쌓이면 「아무것도 안 말해 주는 집」이 됩니다.
FLINCH = re.compile(
    r"판단할 수 (는 )?없|정할 수 없|세어서 나오지 않|안 말해 주|"
    r"맡은 일이 아니|말하지 않(소|네)|알 수 없|가를 일이 아니|"
    r"짐작하지 않았|보증하지 않|아닌 대목이 있거든|억지로 끼워|"
    r"맞는 말로 취급하지|단정하는 것은 아니|증거가 아니")

#: 물음 — 손님에게 되묻는 줄.
ASK = re.compile(r"[?？]\s*$")

#: 사전 — 낱말 뜻을 푸는 줄.
DICT_ = re.compile(
    r"^(이게 무슨 말인가)|"
    r"^(년주|월주|일주|시주)\s|"
    r"^(비견|겁재|식신|상관|정재|편재|정관|편관|정인|편인|비겁|식상|재성|"
    r"관성|인성|일간|일지|월지|월주|년주|일주|시주|대운|세운|용신|공망|"
    r"신살|절기|절입|지장간|통근|진태양시|양인|도화|역마|화개|괴강|백호)"
    r"\s*[^,.]{0,4}(이오|요|네|이네|쪽이오|자리요|것이오)")

#: 시킴 — 오늘 할 일.
DO = re.compile(r"(시오|하십시오|하세요|보세요|하시게|하게|보게)[.!]?\s*$")

#: 인과 — 「그래서 이렇게 꼬였다」. 원인과 결과를 잇는 말.
#
# ★ 이 집은 **까닭을 뒤에 대는** 꼴을 많이 씁니다 — 「~느라 품이 더
#   들었네」 「~것이 아니라 ~것이네」. 「때문」 같은 이음말만 찾으면 절반을
#   놓칩니다 (처음에 그래서 인과가 3%로 나왔습니다).
WHY = re.compile(
    r"^(그래서|그러니|그런데)\s"
    r"|(때문|까닭|탓|덕에|바람에|하니|느라|므로|기에)"
    r"|(것이 아니라|게 아니라|아니라\s).{0,30}(것이|거요|거네|이오|이네)"
    r"|(동안|사이에|뒤에|나서).{0,30}(미뤄|늦|막히|굳|새|남이|이미)")

#: 단정 — **이 사람이 어떤 사람인지 말하는** 줄. 「헉」이 여기서 납니다.
#
# ★ 주어가 **없는** 단정을 놓치고 있었습니다. 이 집은 하오체 한 벌로 쓰고
#   주어를 자주 생략합니다 — 「오래 버틴 것을 쉽게 버리지는 않지만, 지금의
#   비용을 따져야 다음으로 가는 사람이네」 에는 「그대」 가 없습니다.
#   주어를 요구하면 자가 제 집 글을 못 읽습니다.
#: ★ 「~했을 것이오」 도 단정입니다 (2026-09-25).
#
#   첫 화면을 대비 단정으로 고친 뒤 자가 그것을 「그밖」으로 셌습니다 —
#   「마음은 크게 썼을 것이오」 「다툰 뒤 먼저 손 내미는 쪽일 것이오」.
#   이 집이 일부러 쓰는 꼴이오: 단정이면서 손님이 아니라고 할 수 있는 말.
#   그걸 못 세면 고친 것이 안 보입니다.
#: ★ 「**~ 자리요**」 가 이 집의 단정 꼴입니다 (2026-09-27).
#
#   자를 제품에 맞추고 나서야 보였습니다. 손님이 보는 첫 화면은 이미
#   경쟁 이야기를 닫고 단정으로 엽니다 —
#
#       「게을러서 흐트러지는 자리가 아니오. 생각이 늘면 끼니와 잠이
#         먼저 밀리는 자리요.」
#
#   Pennington & Hastie 가 말한 **유일함**이 바로 이 꼴이오 — 뻔한 남의
#   이야기를 먼저 닫아야 확신이 섭니다. 자가 이것을 「그밖」 으로 세면
#   있는 것을 없다고 적습니다.
VERDICT = re.compile(
    r"자리(가 아니오|가 아니네|요|네|이오|이네)[.!]?$"
    r"|(사람이|쪽이|편이)[오네요]|(사람이네|사람이오|쪽이네|쪽이오|편이네|편이오)"
    # ★ 받침이 붙은 꼴을 놓치고 있었습니다 — 「컸을」 「썼을」 「갈」.
    #   한국말은 어간에 받침이 붙어 한 글자가 되니, 앞 글자를 지정하면
    #   반드시 새오 (`terms.WORD_START` 에서 겪은 그 자리요).
    r"|것이(오|네|요)[.!]?$"
    r"|(그대|자네|너|당신|그쪽)[는은가이]?\s.{0,40}"
    r"(이오|요|네|이네|하오|하네|드오|드네|보오|보네)$"
    # ★ **자리를 갈라 주는 줄**도 단정입니다 (2026-09-27).
    #
    #   docs/45 ② 가 몸사림을 「역할 갈라 주기」 로 바꾼 그 꼴이오 —
    #   「버는 자리와 쥐는 자리가 따로 있소」 「가까워지는 일과 오래
    #   보는 일은 서로 다른 일이오」. 고쳐 놓은 것을 자가 못 보면
    #   고친 자리를 또 고치게 됩니다.
    r"|(따로 있|서로 다른|다른 일이(오|네)|별개의 일이(오|네)"
    r"|다르(오|네)[.!]?$|섞어 부르는)")

#: 그림 — **이 사람을 그리는** 줄 (2026-09-27).
#
# ★ 자를 라우터에 맞추고 나서야 진짜 첫 화면을 봤습니다. `portrait` 이고,
#   그 열 줄 가운데 여섯을 자가 「그밖」 으로 세고 있었습니다 —
#
#       「요새 — 전에 통하던 것이 안 통하네.」
#       「맡으면 끝까지 하는데, 이미 넘겨도 될 일의 단톡방을 아직 못
#         나가고 있네.」
#       「대신 먼저 연락하는 쪽도 자네가 아니라서, 그 사이가 몇 해째
#         같은 자리에 있네.」
#
#   이것이 이 집에서 **가장 잘 쓴 글**입니다. 손님이 「이런 사람이다」 라
#   바란 그것이고, 물건이 들었고(단톡방), 겪은 일을 짚습니다.
#
#   자가 이걸 못 세면 「단정 0%」 라 적고, 고칠 데가 아닌 자리를 가리킵니다.
#   ★ 자가 제 집 글을 못 읽는 자리를 만들지 마시오.
#: ★ 면 머리말은 **`portrait.HEAD` 에서 받습니다** (2026-09-27).
#:
#:   손으로 여섯을 베껴 적어 두었는데 표에는 열이 있었습니다 — 「돈을
#:   쓸 때」 「말할 때」 「남들이 잘못 아는 것」 「혼자 있을 때」 가 빠져
#:   그 네 면이 통째로 「그밖」 으로 셌습니다. 이 집이 되풀이하는 자리요
#:   (캐릭터가 보는 자리를 네 곳에 적던 그것).
_FACE_HEADS = "|".join(re.escape(h) for h in _portrait.HEAD.values())

DRAW = re.compile(
    r"^(" + _FACE_HEADS + r")"
    r"|(하는데|인데|있는데|없는데),?\s"
    r"|(못 나가|못 하고|안 나가|같은 자리에|아직 .{0,12}(있|못))"
    r"|(쪽이라|편이라|사람이라),?\s")

#: 끊음 — **아니라고 끊는** 줄. 이 집의 **위로**요 (2026-09-27).
#:
#: ★ 예순 줄이 「그밖」 에 앉아 있었습니다 —
#:
#:     「그것은 게을러서가 아니오.」
#:     「오래 견뎠다는 사실만으로 더 견딜 의무가 생기지는 않소.」
#:     「그거 자네 흠 아니오.」
#:
#:   Kim & LoSavio 가 말한 **밖에 있는 까닭**이 이 꼴이오 — 자기 탓을
#:   끊어 주는 줄이라, 몸사림(판단을 거두는 줄)과 **정반대**입니다.
#:   둘을 한 칸에 넣으면 위로를 늘려야 할 자리에서 줄이라 읽습니다.
CUT_OFF = re.compile(
    r"(가 아니오|가 아니네|은 아니오|은 아니네|지는 않소|지는 않네"
    r"|흠 아니오|흠 아니네|탓이 아니오|탓이 아니네|잘못이 아니오"
    r"|잘못이 아니네|게 아니오|게 아니네|뿐이오|뿐이네)[.!]?\s*$")

#: 옮김 — 같은 말을 **쉬운 말로 다시** 하는 줄.
#:
#: ★ 예순두 줄이 「~는 말이오」 로 끝납니다. 낱말 뜻을 푸는 「사전」 과
#:   다릅니다 — 문장을 옮기는 것이오. 이 집이 일부러 하는 일이되
#:   (docs/21 쉬운말), 한 장에 쌓이면 **같은 말을 두 번** 읽는 것입니다.
RESAY = re.compile(r"(는|란) 말이(오|네|요)[.!]?\s*$|^(쉽게 말하면|곧|즉)(?=\s|$)")

#: 비유 — 물건에 대 보는 줄.
FIGURE = re.compile(r"(같소|같네|같아요|같습니다|같은 것이|처럼요|셈이(오|네))")

#: 약속 — 안 하겠다고 **지키는** 고백. 법무가 요구하는 줄이오.
#:
#: ★ `same_point` 에서 겪은 자리요 — 몸사림으로 세면 「줄여라」 가 되는데
#:   이건 **줄이면 안 되는** 줄입니다.
KEEP = re.compile(
    r"(참고했|판정하거나|계산을 바꾼|의료|진단을 대신|전문가와 확인"
    r"|보증하지 않|맡은 일이 아니)")

#: 이음 — 다음 줄로 넘기는 **표지판**. 내용이 없습니다.
#:
#: ★ 이 칸이 이 자의 쓸모요. 「실제로는 이렇소」 「내 눈으로는 이렇게
#:   보이오」 「여기까지는 사람의 모습이오」 「월주 태어난 달의 두
#:   글자요」 — 손님이 읽을 것이 없는 줄이오. 손님이 「내용만 길고
#:   뭔소리인지 모르겠다」 고 한 그 자리입니다.
#   ★ 「월주 태어난 달의 두 글자요」 는 이음이 **아니고 사전**이오 —
#     명식 컷이 기둥 이름을 푸는 자리요. `DICT_` 로 옮겼습니다. 자가
#     고칠 데가 아닌 자리를 가리키게 두면 멀쩡한 글을 지웁니다.
JOINT = re.compile(
    r"^(실제로는|내 눈으로는|여기까지|이 그림이 나온 자리|오늘은|그럼)"
    r"|(이렇소|이렇네|보겠소|보겠네|보오[.!]|보네[.!]|짚었소|짚었네)\s*$"
    r"|^(이 캐릭터가 보는 기준|맞았는지 재는 법)")

#: 셈 — 센 값을 대는 줄.
COUNT = re.compile(r"\d|하나|둘|셋|넷|다섯|여섯|일곱|여덟|아홉|열|없소|없네|비었")


#: ★ `plain` 은 **`seen_page` 한 자리**에서 받습니다 (2026-09-27).
#:
#:   자마다 제 손으로 적고 있었더니, 굵게 태그가 낱말을 갈라
#:   놓는 사고(「자리</b>요」 → 「자리 요」)를 세 번 따로 고쳐야
#:   했습니다. 문장 끝을 보는 패턴이 전부 새던 자리요.
from tools.seen_page import plain                      # noqa: E402,F401


def sentences(text: str) -> list:
    got = [s.strip() for s in SENT.findall(text)]
    tail = SENT.sub("", text).strip()
    if tail:
        got.append(tail)
    return [s for s in got if len(s) > 5]


KINDS = ("단정", "그림", "끊음", "인과", "옮김", "비유", "셈", "물음",
         "사전", "몸사림", "약속", "시킴", "이음", "그밖")


def kind_of(s: str) -> str:
    """한 줄의 일감. **센 것부터** 봅니다 — 앞의 것이 이깁니다."""
    if ASK.search(s):
        return "물음"
    # 약속은 몸사림보다 **먼저** 봅니다 — 꼴이 겹치는데 뜻이 반대요.
    if KEEP.search(s):
        return "약속"
    if FLINCH.search(s):
        return "몸사림"
    if DICT_.match(s):
        return "사전"
    if DO.search(s):
        return "시킴"
    if WHY.search(s):
        return "인과"
    # 끊음은 단정보다 먼저 — 「~자리가 아니오」 가 둘 다에 걸립니다.
    if CUT_OFF.search(s):
        return "끊음"
    if VERDICT.search(s):
        return "단정"
    if DRAW.search(s):
        return "그림"
    if RESAY.search(s):
        return "옮김"
    if FIGURE.search(s):
        return "비유"
    if COUNT.search(s):
        return "셈"
    # ★ 맨 끝입니다. 위의 어느 것도 아니면 **표지판**인지 봅니다.
    if JOINT.search(s):
        return "이음"
    return "그밖"


def _page(rng: random.Random) -> dict:
    """
    손님이 받는 글 한 벌. 조립은 `tools/seen_page` 한 자리에서.

    ★ `voice_on=False` — **말투 층만** 끕니다 (2026-09-27).

      아래 결 패턴은 하오체 어미로 적혀 있는데 손님 화면은 캐릭터
      말투로 나갑니다. 켠 채로 재니 「옳은 말을 하고도 지는 자리 네」
      같은 **단정이 절반 넘게** 「그밖」 으로 떨어졌습니다. 갈래 51%가
      「그밖」 이면 그 위의 백분율은 아무 뜻이 없소.

      말투는 어간을 안 건드리고 꼬리만 가니, **줄이 무슨 일을 하는가는
      말투가 바꿀 수 없습니다.** 조립·차례·고른 컷은 전부 그대로요 —
      `tests/test_seen_page.py` 가 두 글이 어미만 다른지 셉니다.
    """
    concern = rng.choice(CONCERNS)
    axis4 = rng.choice((None, "INFP", "ESTJ", "INTP", "ENFJ", "ISTP"))
    f = _sample(rng)
    pg = _free_page(f, concern, axis4, lens_id=_lens_of(rng),
                    voice_on=False)
    return {"first": plain(pg["blocks"][0]["html"]),
            "all": [plain(b["html"]) for b in pg["blocks"]]}


def audit(page: dict) -> dict:
    def mix(texts):
        bag = collections.Counter()
        for t in texts:
            for s in sentences(t):
                bag[kind_of(s)] += 1
        return bag

    first = mix([page["first"]])
    whole = mix(page["all"])
    return {"first": first, "whole": whole,
            "first_chars": len(page["first"]),
            "chars": sum(len(t) for t in page["all"]),
            # 첫 단정이 몇 번째 줄에 오는가 — 늦으면 손님은 그 앞에서 나갑니다
            "first_verdict_at": next(
                (i for i, s in enumerate(sentences(page["first"]), 1)
                 if kind_of(s) == "단정"), 0),
            "lines_first": len(sentences(page["first"]))}


def _pct(bag: collections.Counter) -> str:
    tot = max(1, sum(bag.values()))
    return " · ".join("%s %2.0f%%" % (k, 100 * bag[k] / tot)
                      for k in KINDS if bag[k])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--show", type=int, default=0)
    ap.add_argument("--seed", type=int, default=20260925)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    rows = [audit(_page(rng)) for _ in range(a.n)]

    def avg(fn):
        return statistics.mean(fn(r) for r in rows)

    print("\n무료 구간이 무엇으로 채워져 있나 (%d명)" % a.n)
    print("=" * 74)

    for name, key, extra in (("첫 화면", "first", True),
                             ("무료 전체", "whole", False)):
        bag = collections.Counter()
        for r in rows:
            bag.update(r[key])
        tot = max(1, sum(bag.values()))
        chars = avg(lambda r: r["first_chars" if key == "first" else "chars"])
        print("\n  %s — %d자 · 줄 %.0f개" % (name, chars, tot / len(rows)))
        for k in KINDS:
            if not bag[k]:
                continue
            n = bag[k] / len(rows)
            bar = "█" * int(round(28 * bag[k] / tot))
            print("    %-6s %-28s %4.1f줄  %2.0f%%"
                  % (k, bar, n, 100 * bag[k] / tot))
        if extra:
            late = [r["first_verdict_at"] for r in rows]
            none = sum(1 for x in late if x == 0)
            print("    ★ 첫 화면에 **단정이 한 줄도 없는 사람** %.0f%% (%d/%d)"
                  % (100 * none / len(rows), none, len(rows)))
            got = [x for x in late if x]
            if got:
                print("      있는 사람은 %.1f번째 줄에서 처음 만납니다"
                      % statistics.mean(got))

    if a.show:
        for r in rows[:a.show]:
            print("\n" + "-" * 74)
        rng2 = random.Random(a.seed)
        p = _page(rng2)
        print("  첫 화면을 줄마다 (%d자)" % len(p["first"]))
        for i, s in enumerate(sentences(p["first"]), 1):
            print("    %2d [%-4s] %s" % (i, kind_of(s), s[:62]))
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
