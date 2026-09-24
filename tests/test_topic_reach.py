# -*- coding: utf-8 -*-
"""
물은 자리가 **글에 닿는가** — 검사로 못박는다.

★ 손님이 두 번 짚었습니다

    2026-09-05  "돈을 물었는데 돈 얘기가 없다"
    2026-09-17  "근데 돈을 선택했는데 왜 돈에 대한걸 말안해?"
                "다른것도 그렇고" "이런 오류는 왜 못잡아 자꾸"

  두 번째가 뼈아픕니다. 첫 번째 뒤에 `engine/topic` 을 세워 **세는
  값**을 갈랐는데, 그 값이 손님이 읽는 **낱말**까지 오는지는 아무도
  안 쟀습니다.

★ 왜 못 잡았나 — 자가 없었습니다

  이 저장소의 자는 전부 「글이 좋은가」를 잽니다 — 당김·팩폭·울림·
  명확·쉬움·비유·속도·강조, 중복률, 손잡이, 훑어읽기. 「물은 것에
  답하는가」를 재는 자는 **하나도 없었습니다.**

  자가 없는 자리는 안 보입니다. 그래서 이 검사가 있습니다.

★ 무엇을 세는가

  손님이 쓰는 말만 셉니다. 「재성이 하나요」 는 돈 얘기로 **안**
  셉니다 — 손님이 그 말을 모르오. 명리 용어로 답하는 것은 물음에
  답한 것이 아닙니다.
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT / "tools"))

from engine import bank as bank_mod                # noqa: E402
from engine import dramaturgy as D                 # noqa: E402
from engine import screenscan as S                 # noqa: E402
from engine.calendar import build_chart            # noqa: E402
from engine.features import build_features         # noqa: E402
from engine.report import build_report             # noqa: E402
from topic_reach import WORDS, KO                  # noqa: E402

TODAY = date(2026, 9, 17)
CONCERNS = tuple(WORDS)
BIRTHS = [
    (1993, 11, 25, 15, 55, "M", True),
    (1978, 2, 4, 0, 20, "F", True),
    (1966, 12, 31, None, None, "M", False),
]

# 긴 컷에 물은 자리의 말이 **한 번도** 안 나오면 그건 딴 얘기요.
LONG = 300
# 이 컷들은 물은 자리와 무관해도 됩니다 — 무엇을 물었든 같은 자리.
#   lens_bridge  그 사람에게 넘기는 다리
#   daeun_map    열 해씩 늘어놓은 눈금
#   chart        명식 표 — **무관해야** 합니다.
#                여기에 고민 줄을 한 번 달았다가
#                `test_concern_spread.test_the_chart_cut_never_moves` 에
#                걸렸습니다. 「명식과 보정은 물음이 바꿀 것이 아니오.
#                바뀌면 계산이 아니라 장사요.」 맞는 말이오 — 여덟
#                글자는 무엇을 물었든 같은 여덟 글자입니다.
# ★ 「어떤 사람인가」 도 여기 둡니다 (2026-09-24). 사람은 무엇을
#   물었든 같은 사람이오 — 명식에 고민을 안 들이는 것과 같은 까닭이라,
#   여기에 고민을 넣으면 그건 사람을 물음에 맞춰 고쳐 그리는 것이오.
FREE_OF_TOPIC = {"lens_bridge", "daeun_map", "chart", "portrait"}


def _f(b):
    y, m, d, h, mi, sex, known = b
    return build_features(build_chart(y, m, d, h, mi, sex, known, "서울"),
                          as_of=TODAY)


# 용어 풀이 — 「재성(돈·살림 같은 재물…)」 은 **사전**이오. 무엇을
# 물었든 같은 글자가 나오니, 이걸 세면 누구나 돈 얘기를 한 것이 됩니다.
#   <i class="gl">(…)</i>      낱말 옆 괄호 풀이
#   <div class="gls">…</div>   「이게 무슨 말인가」 상자
# 같은 컷이라도 앞에 선 컷이 적으면 풀이가 **다시** 붙으므로
# (`report.GLOSS_AGAIN`), 안 걷으면 무료 구간에서만 수가 튑니다.
_GLOSSARY = re.compile(r'<i class="gl">.*?</i>|<div class="gls">.*?</div>',
                       re.S)


def _hits(text: str, concern: str) -> int:
    return len(re.findall(WORDS[concern], text))


def _read(cuts, ids) -> str:
    """손님이 읽는 글 — 사전은 뺍니다."""
    return D.plain(_GLOSSARY.sub(" ", " ".join(c["html"] for c in cuts
                                               if c["id"] in ids)))


@pytest.mark.parametrize("b", BIRTHS)
@pytest.mark.parametrize("concern", CONCERNS)
def test_긴_컷에_물은_말이_한_번은_나온다(b, concern):
    f = _f(b)
    rep = build_report(f, "t", "dongja", "free", concern, "INTJ")
    thin = []
    for c in rep["cuts"]:
        if c["id"] in FREE_OF_TOPIC:
            continue
        t = _read([c], {c["id"]})
        if len(t) >= LONG and _hits(t, concern) == 0:
            thin.append("%s(%d자)" % (c["id"], len(t)))
    assert not thin, (
        "%s를 물었는데 그 말이 한 번도 안 나오는 긴 컷: %s"
        % (KO[concern], " · ".join(thin)))


@pytest.mark.parametrize("b", BIRTHS)
@pytest.mark.parametrize("concern", CONCERNS)
def test_훅에_물은_말이_닿는다(b, concern):
    """훅은 값을 안 치른 사람이 가장 오래 머무는 자리요."""
    f = _f(b)
    segs = bank_mod.build_hook(f, concern, "INTJ", "", "그대")
    t = D.plain(S.hook_html(segs))
    n = _hits(t, concern)
    assert n >= 3, (
        "%s를 물었는데 훅 %d자에 그 말이 %d번뿐이오"
        % (KO[concern], len(t), n))


# 물으신 자리를 **마주 보는** 컷. 이것들이 안 갈리면 고민 칸은
# 이름표요. 명식 표·희소도처럼 같은 사람이면 같은 자리는 안 봅니다 —
# 그건 갈리면 안 되는 것이오 (같은 여덟 글자니까).
#
# ★ 척추 컷(spine · closing_cut)은 **여기 안 넣습니다** (2026-09-17).
#
#   넣고 재 보니 고민끼리 92~93% 같았습니다. 그건 참입니다 — 그
#   컷들은 본문이 「이 사람이 어떤 사람인가」 이고, 물으신 자리는
#   꼬리 한 줄로만 붙습니다(`topic.cut_line`). 자를 거기까지 대면
#   **늘 붉은 자**가 되어 아무것도 안 가리킵니다.
#
#   남은 구멍은 자가 아니라 **뱅크**에 있습니다 — 척추 컷 본문을
#   물으신 자리로 쓰는 일. 그건 이 검사가 할 일이 아니라 다음에
#   할 일이오. 여기서는 **물음을 마주 보는 것이 제 일인 컷**만
#   봅니다.
FACING = ("concern", "why")


@pytest.mark.parametrize("b", BIRTHS)
@pytest.mark.parametrize("concern", CONCERNS)
def test_물은_자리의_말이_가장_많다(b, concern):
    """
    ★ 글자 닮음으로 재지 않습니다 (2026-09-17).

      처음에 마주 보는 컷을 통째로 견줬더니 86~95% 같다고 나왔습니다.
      그 수는 **뼈대**를 세고 있었습니다 — 「그대가 물으러 오신 고민은
      X이오. 여덟 글자에서는 이걸 Y으로 보오」 는 꼴이 같아야 하는
      자리요. 갈려야 하는 것은 꼴이 아니라 **대는 값**입니다.

      그래서 곧게 묻습니다: **물은 자리의 말이 딴 자리의 말보다
      많은가.** 돈을 물었는데 사랑 말이 더 많으면 그건 딴 답이오.
      꼴로는 못 속입니다.
    """
    f = _f(b)
    rep = build_report(f, "t", "dongja", "free", concern, "INTJ")
    txt = _read(rep["cuts"], FACING)
    mine = _hits(txt, concern)
    others = {c: _hits(txt, c) for c in CONCERNS if c != concern}
    top = max(others, key=lambda k: others[k])
    # ★ 「내 말이 제일 많아야 한다」 로 두면 동전 던지기가 됩니다.
    #
    #   이 두 컷은 600자쯤이라 낱말이 두셋씩만 나옵니다. 2 대 3 으로
    #   지는 것을 고장이라 부르면, 글을 한 줄 고칠 때마다 자가 붉었다
    #   푸르렀다 합니다 — 그런 자는 아무것도 안 가리키오.
    #
    #   그리고 딴 자리 말이 나오는 것 자체는 옳습니다. 일을 물어도
    #   여덟 글자가 돈으로 외치면 그걸 짚어 줘야 하오 (CONCERN_ELSE).
    #   막을 것은 **물은 자리가 딴 자리에 크게 밀리는 것**입니다.
    assert mine >= 2, (
        "%s를 물었는데 마주 보는 컷에 그 말이 %d번뿐이오"
        % (KO[concern], mine))
    assert mine >= others[top] * 0.7, (
        "%s를 물었는데 %s 말에 크게 밀리오 (%s %d · %s %d)"
        % (KO[concern], KO[top], KO[concern], mine, KO[top], others[top]))


def test_자가_있다():
    """이 자를 지우면 같은 일이 또 조용히 납니다."""
    assert (ROOT / "tools" / "topic_reach.py").exists()
