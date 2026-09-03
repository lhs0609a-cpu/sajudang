"""
말투가 한 사람 안에서 갈리지 않는가 — 스무 명 전수.

★ 2026-09-03. 손님이 약초의원(해요체)의 리포트를 읽다 멈췄습니다.
  한 화면 안에 이런 것들이 같이 있었습니다 —

      이게 무슨 말이네요            비문. 상자 제목이 말투를 탔음
      불이 거의 없는 것이지.         반말. 원문이 하오체가 아니었음
      …얻는지를 보오 〔자평 명리〕     하오체 잔여. 출처 묶음표가 문장 끝을 가림
      억울했을 게요                 하오체 잔여
      …없네요 …것이네요 …후회했네요   여덟 문장이 잇달아 「네요」

  재보니 스무 명에서 **섞인 문장이 1,044개** 였습니다. 은별 무녀는
  합쇼체 198 · 해요체 123 이 한 사람 안에 섞여 있었고, 한 문장
  안에서도 「…편이에요. …다닙니다. …반복돼요.」 였습니다.

★ 이 검사가 지키는 규칙 셋

    ① 뱅크는 **하오체 한 벌**로 쓴다 — 다른 말투로 쓰면 speak 가
       손댈 자리가 없어 그 문장만 스무 명에게 똑같이 나간다
    ② 화면에 나가는 글은 speak 를 **거친다** — 근거 줄·용어 상자·
       훅까지. 한 줄이라도 빠지면 그 자리에서 말투가 갈린다
    ③ 손으로 쓴 곁말(flavor)은 **그 캐릭터의 말투로** 쓴다

  ①②는 `tools/voice_audit.py` 가 세고, 이 검사가 0을 잠급니다.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT / "tools"))

import pytest                                          # noqa: E402

from engine import lens as lens_mod                    # noqa: E402
from engine import voice as V                          # noqa: E402
from engine.calendar import build_chart                # noqa: E402
from engine.features import build_features             # noqa: E402
from engine.report import build_report                 # noqa: E402
from voice_audit import ending_of, frozen, sentences   # noqa: E402


@pytest.fixture(scope="module")
def spoken():
    """스무 명이 실제로 손님에게 내보내는 문장."""
    f = build_features(build_chart(1993, 11, 25, 15, 55, "M", True, "서울"))
    out = {}
    for l in lens_mod.released():
        lines = []
        tier = "one" if l.get("price") else "free"
        r = build_report(f, "t", l["id"], tier, "money", None)
        for k in ("opening", "closing"):
            lines += sentences(r.get(k) or "")
        for c in r.get("cuts", []):
            lines += sentences(c.get("html", ""))
        out[l["id"]] = lines
    return out


def test_아무도_남의_말투로_말하지_않는다(spoken):
    """
    ★ 「제 말투가 아닌 어미」 가 하나라도 있으면 그 화면에서 사람이
      바뀐 것처럼 읽힙니다. 하오체 명사 종결(자리요)과 어미가 아닌
      줄(조사로 끝나는 근거 줄)은 세지 않습니다.
    """
    view = lens_mod._views()
    bad = []
    for lid, lines in spoken.items():
        want = (view.get(lid) or {}).get("voice") or V.HAO
        for s in lines:
            tone = ending_of(s)
            if tone not in (want, "hao_noun", "기타"):
                bad.append("%s(%s) ← [%s] %s" % (lid, want, tone, s[:56]))
    assert not bad, "말투가 섞인 문장 %d개\n  %s" % (
        len(bad), "\n  ".join(sorted(set(bad))[:15]))


def test_뱅크는_하오체_한_벌이다(spoken):
    """
    ★ 다섯 말투를 다 걸어도 **글자가 안 바뀌는** 종결 문장은 원문이
      하오체가 아니라는 뜻입니다. 그러면 그 문장만 스무 명에게 같은
      어미로 나가, 관점이 스물이어도 목소리가 하나가 됩니다.
    """
    # ★ 하오체 캐릭터의 글만 봅니다 — 나머지는 이미 speak 를 거친
    #   결과라, 거기에 speak 를 다시 걸면 안 바뀌는 게 당연합니다.
    view = lens_mod._views()
    raw = sorted({s for lid, ls in spoken.items() for s in ls
                  if ((view.get(lid) or {}).get("voice") or V.HAO) == V.HAO})
    stuck = frozen(raw)
    assert not stuck, "하오체가 아닌 원문 %d개\n  %s" % (
        len(stuck), "\n  ".join("[%s] %s" % (t, s[:60])
                                for t, s in stuck[:15]))


def test_출처_묶음표가_문장_끝을_가리지_않는다():
    """근거 줄은 「…보오 〔자평 명리 · 용신〕」 로 끝납니다."""
    s = "그 자리를 보오 〔자평 명리 · 용신〕"
    assert V.speak(s, V.HAPSYO).startswith("그 자리를 봅니다")


def test_상자_제목은_말투를_타지_않는다():
    """
    ★ 「이게 무슨 말이오」 였습니다. 말투 층을 타서 해요체 캐릭터에게서
      「이게 무슨 말이네요」 라는 비문이 나왔습니다. 표지판은 말이
      아니니 어느 말투에도 안 걸리는 꼴로 둡니다.
    """
    from engine import terms
    box = terms.picture_box(["편관"])
    for v in V.VOICES:
        assert "이게 무슨 말인가" in V.speak(box, v)


@pytest.mark.parametrize("v", [V.HAPSYO, V.HAGE, V.BANMAL, V.HAEYO])
def test_ㄹ받침_어간이_비문이_되지_않는다(v):
    """
    ★ ㄹ탈락은 규칙입니다 — 살다→삽니다·사네. 이걸 안 하면
      「살습니다 · 살네」 가 나옵니다.
    """
    got = V.speak("덜 찬 채로 살소.", v)
    assert "살습니다" not in got and "살네" not in got, got


def test_해요체가_네요_한_결로만_나가지_않는다(spoken):
    """
    ★ 여덟 문장이 잇달아 「네요」 였습니다. 「네요」 는 알아채는 말이라
      한 번 쓰면 살고 여덟 번 쓰면 기계입니다. 불규칙이 걸리는 자리는
      물러서므로 0 이 되지는 않지만, 절반을 넘으면 안 됩니다.
    """
    for lid, lines in spoken.items():
        if (lens_mod._views().get(lid) or {}).get("voice") != V.HAEYO:
            continue
        ends = [s for s in lines if ending_of(s) == V.HAEYO]
        if len(ends) < 40:
            continue
        neyo = sum(1 for s in ends if s.rstrip().endswith("네요"))
        assert neyo / len(ends) < 0.5, (
            "%s — 해요체 %d줄 중 「네요」 가 %d줄"
            % (lid, len(ends), neyo))
