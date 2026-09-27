# -*- coding: utf-8 -*-
"""
손님이 **실제로 받는 글** — 자들이 함께 쓰는 한 자리.

★ 왜 이 파일이 생겼나 (2026-09-27)

  자 셋(`dull_audit` · `same_point` · `verdict_mix`)이 훅을
  `bank.build_hook` 으로 재고 있었습니다. 그런데 손님이 보는 훅은
  `routers/hook` 이 만들고, 그 라우터는 **네 층을 더 얹습니다** —

      portrait     사람부터 그리는 마디 (맨 앞에 끼움)
      topic        고른 상황을 되묻는 컷 (맨 앞에 끼움)
      specialist   그 캐릭터의 전문 판단 (둘째에 끼움)
      voice        말투·호칭을 갈아 끼우는 층 (전부에)

  `build_hook` 은 분석지(`engine/summary`)와 도구(`engine/screenscan`)만
  쓰는 자리요. 그래서 자가 낸 훅 수치는 **다른 물건의 것**이었고, 씨앗
  55줄을 고쳐 배포해도 손님 화면에는 안 닿았습니다. 그 사이 자는
  「고쳤다」 고 찍었습니다.

  자를 제품보다 **좁게** 두는 것보다 나쁩니다 — 좁으면 못 보고 끝나지만,
  다른 것을 재면 고친 줄 알고 넘어갑니다.

★ 그래서 조립을 **한 자리**에 둡니다

  자마다 제 손으로 라우터를 흉내 내면 또 갈립니다. 라우터가 층을 하나
  더 얹는 날 자들이 조용히 옛 물건을 재기 시작하오 — 이 집이 완료율과
  목패 이름에서 겪은 그 자리요.

  `tests/test_seen_page.py` 가 이 조립이 라우터와 어긋나지 않는지 셉니다.

★ 다만 **라우터를 부르지는 않습니다.**

  HTTP 를 태우면 자가 서버·DB·캐시에 매입니다. 대신 라우터가 부르는
  것과 **같은 함수를 같은 차례로** 부르고, 검사가 그 차례를 지킵니다.
"""
from __future__ import annotations

import contextlib
import html as _html
import re
import sys
from datetime import date
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "services" / "api", ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine import character_consultation as _cc     # noqa: E402
from engine import lens as lens_mod                  # noqa: E402
from engine import portrait as portrait_mod          # noqa: E402
from engine import topic as topic_mod                # noqa: E402
from engine import voice as voice_mod                # noqa: E402
from engine.first_reading import build_first_reading  # noqa: E402
from engine.report import build_report               # noqa: E402

TAG = re.compile(r"<[^>]+>")

#: 줄을 **끊는** 태그. 이것만 빈칸으로 바꿉니다.
_BLOCK = re.compile(
    r"</?(?:p|div|br|li|ul|ol|tr|td|th|table|h[1-6]|section|blockquote)"
    r"(?![a-zA-Z0-9])[^>]*>",
    re.I)
#: 글자 사이에 **끼는** 태그 (굵게·형광펜·링크). 이건 **떼어 붙입니다.**
_INLINE = re.compile(r"</?[a-zA-Z][^>]*>")


def plain(html: str) -> str:
    """
    태그를 걷은 글.

    ★ 끼는 태그를 빈칸으로 바꾸면 **낱말이 갈라집니다** (2026-09-27).

      이 집은 센 낱말을 굵게 칩니다 — `<b>쥐고 셈하는 자리</b>요.`
      태그를 전부 빈칸으로 바꾸면 「쥐고 셈하는 자리 **·공백·** 요.」 가
      되어, 문장 끝을 보는 자(「…자리요」 = 단정)가 **한 줄도** 못
      셌습니다. 「옳은 말을 하고도 지는 자리 네.」 가 「그밖」 에 앉아
      있던 진짜 까닭이오.

      줄을 끊는 태그(`<p>` `<br>`)만 빈칸이고, 글자 사이에 끼는
      태그(`<b>` `<em>` `<mark>` `<a>`)는 **떼어 붙입니다.** HTML 이
      원래 그렇게 읽힙니다.
    """
    t = _html.unescape(html or "")
    t = _BLOCK.sub(" ", t)
    t = _INLINE.sub("", t)
    t = TAG.sub(" ", t)                     # 남은 것(주석 등)은 빈칸으로
    return re.sub(r"\s+", " ", t).strip()


def hook(f, concern: str, axis4=None, lens_id: str = "nopa",
         name: str = "", misses: int = 0, topic=None) -> list:
    """
    **라우터와 같은 차례로** 훅을 짓는다 (`routers/hook.py`).

    돌려주는 것은 화면에 가는 마디 목록이오 — stage · label · html ·
    source · question · yes · no.
    """
    segs = build_first_reading(f, concern, axis4, name=name,
                               misses=misses, topic=topic)
    # ① 고른 상황을 되묻는 컷 · ② 그 캐릭터의 전문 판단
    if topic:
        focused = topic_mod.ask_cut(f, concern, topic)
        if focused:
            segs.insert(0, {
                "stage": "topic", "label": focused["title"],
                "html": focused["html"], "source": focused["source"],
                "source_below": True,
                "statement_id": "first-reading-v3-topic:" + focused["statement_id"],
                "question": "지금 말씀하신 상황과 맞닿아 있소?",
                "yes": "그 장면부터 놓고 이어서 보겠소.",
                "no": "다르게 느껴지는 부분은 억지로 맞추지 않겠소. "
                      "다음 관점에서 다시 보시오.",
            })
        specialist = (_cc.brief(lens_id, topic,
                                name=lens_mod.public(lens_id)["name"])
                      if lens_id else None)
        if specialist:
            segs.insert(1, {
                "stage": "specialist", "label": specialist["title"],
                "html": specialist["html"],
                "source": "선택한 상황 · 이 상담자의 전문 판단 기준",
                "source_below": True,
                "statement_id": "first-reading-v3-specialist:%s:%s:%s"
                                % (lens_id, topic.get("choice4"),
                                   topic.get("choice5")),
                "question": "이 관점이 지금 놓인 문제의 중심을 제대로 가르고 있소?",
                "yes": specialist["close"],
                "no": "이 관점이 전부는 아니오. 맞지 않는 대목은 버리고 "
                      "다른 상담자의 눈으로 다시 보겠소.",
            })
    # ③ 사람부터 그리는 마디 — **맨 앞**입니다
    port = portrait_mod.build(
        f, lens_id, portrait_mod.HOOK_FACES, cross=True,
        you=lens_mod.you_word(lens_id, name, getattr(f, "sex", None)))
    if port:
        segs.insert(0, {
            "stage": "portrait", "label": portrait_mod.TITLE,
            "html": port["html"], "source": port["source"],
            "source_below": True,
            "statement_id": port["statement_id"],
            "question": "여기 적힌 사람이 그대와 얼마나 닮았소?",
            "yes": "그러면 이 사람을 놓고 물으신 일을 보겠소.",
            "no": "맞지 않는 그림이오. 억지로 끼워 맞추지 않겠소 — "
                  "아닌 줄은 빼고 읽으시오.",
        })
    # ④ 말투·호칭 — **맨 끝**입니다. 이 층을 빼면 자가 하오체만 봅니다.
    tone = (lens_mod.view(lens_id) or {}).get("voice")
    if tone:
        you = lens_mod.you_word(lens_id, name, getattr(f, "sex", None))
        for s in segs:
            for k in ("html", "question", "yes", "no", "source"):
                if s.get(k):
                    s[k] = voice_mod.speak(voice_mod.address(s[k], you), tone)
    return segs


@contextlib.contextmanager
def hao_only():
    """
    말투 층을 잠깐 끈다 — 자가 **하오체 한 벌**로 읽게.

    ★ 왜 이 문이 필요한가 (2026-09-27)

      `verdict_mix` 가 줄마다 「무슨 일을 하는가」 를 갈랐는데 절반이
      「그밖」 으로 떨어졌습니다. 열어 보니 이런 줄이었습니다 —

          「옳은 말을 하고도 지는 자리 네.」        ← 단정이오
          「그만둔 뒤에도 그 일 연락을 받고 있네.」   ← 그림이오

      자의 결 패턴이 **하오체 어미**(…이오 · …자리요 · …소)로 적혀
      있는데, 손님 화면은 `voice` 층을 지나 캐릭터의 말투로 나갑니다.
      스무 명 가운데 하오체는 일곱뿐이라, 자는 제 집 글의 절반 이상을
      읽지 못한 채 「단정 0%」 라 적고 있었습니다.

      말투는 어간을 안 건드리고 **꼬리만** 갑니다. 그러니 줄이 무슨
      일을 하는가는 말투가 바꿀 수 없소 — 갈래는 하오체로 세고, 길이와
      겹침은 손님 글로 잽니다. 두 글이 어미만 다른지는
      `tests/test_seen_page.py` 가 셉니다.
    """
    keep = voice_mod.speak
    voice_mod.speak = lambda text, tone=None, **kw: text
    try:
        yield
    finally:
        voice_mod.speak = keep


def free_page(f, concern: str, axis4=None, lens_id: str = "nopa",
              name: str = "", topic=None, voice_on: bool = True) -> dict:
    """
    값을 치르기 전 손님이 받는 **전부** — 훅 마디 + 무료 컷 + 잠긴 목록.

    자들이 이것을 재야 합니다. 「첫 화면」 은 `blocks[0]` 이오.

    `voice_on=False` 면 말투 층만 끕니다 (`hao_only` 머리말을 보시오).
    """
    with (contextlib.nullcontext() if voice_on else hao_only()):
        segs = hook(f, concern, axis4, lens_id=lens_id, name=name, topic=topic)
        rep = build_report(f, "m", lens_id, "free", concern, axis4)
    blocks = [{"where": "훅:%s" % s.get("stage"), "title": s.get("label") or "",
               "html": s.get("html") or "", "source": s.get("source") or "",
               "question": s.get("question") or ""}
              for s in segs]
    blocks += [{"where": c["id"], "title": c.get("title") or "",
                "html": c.get("html") or "", "source": c.get("source") or "",
                "question": ""}
               for c in rep["cuts"]]
    return {"blocks": blocks, "locked": rep["locked"],
            "concern": concern, "lens_id": lens_id,
            "hook_stages": [s.get("stage") for s in segs]}


#: 자들이 같은 사람을 쓰게. 서로 다른 표본을 쓰면 수치를 나란히 못 놓습니다.
AS_OF = date(2026, 9, 27)


def sample(rng, *, hour_known: Optional[bool] = None):
    """자들이 함께 쓰는 사람 하나."""
    from engine.calendar import build_chart
    from engine.features import build_features
    if hour_known is None:
        hour_known = rng.random() > 0.15
    return build_features(
        build_chart(rng.randint(1960, 2007), rng.randint(1, 12),
                    rng.randint(1, 28), rng.randint(0, 23), rng.randint(0, 59),
                    rng.choice("MF"), hour_known=hour_known), as_of=AS_OF)

#: 자들이 **스무 명을 다 보게**. 한 사람만 보면 그 사람 몫 겹침이
#: 100% 로 찍히고 나머지 열아홉 몫은 한 번도 안 찍힙니다.
def lens(rng) -> str:
    """★ 목록은 `engine/lens` **한 자리**에서 받습니다 (손표를 두지 마시오)."""
    return rng.choice(sorted(x["id"] for x in lens_mod.all_lenses()))
