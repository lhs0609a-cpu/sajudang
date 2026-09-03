"""
말투 감사 — 스무 명이 **제 말투로만** 말하는가.

    python tools/voice_audit.py [--show]

★ 왜 이 도구가 생겼는가 (2026-09-03)

  손님이 약초의원(해요체)의 리포트를 읽다 멈췄습니다. 한 화면 안에
  이런 것들이 같이 있었습니다 —

      이게 무슨 말이네요            ← 비문. 「이게 무슨 말이오」 가 갈렸음
      불이 거의 없는 것이지.         ← 반말. 해요체 캐릭터인데
      …그걸 어디서 얻는지를 보오     ← 하오체 잔여. 용어 줄이 speak 를 안 거침
      억울했을 게요                 ← 하오체 잔여
      …없네요 …것이네요 …후회했네요   ← 여덟 문장이 잇달아 「네요」

  뱅크는 **하오체 한 벌**로 쓰고 `engine.voice.speak` 가 맨 끝에서
  어미만 갈아 끼웁니다. 그러니 이상한 말투는 셋 중 하나입니다 —

    ① 섞임    그 캐릭터 말투가 아닌 어미가 섞였다
    ② 굳음    원문이 하오체가 아니라 **다섯 말투에서 글자가 똑같다**
              (「…것이지」 처럼 한다체·반말로 쓴 원문. 스무 명 전부에게
               같은 어미로 나가므로 목소리가 하나가 됩니다)
    ③ 쏠림    한 어미가 그 사람 문장의 몇 %를 먹는가

  ①②는 **버그**입니다. ③은 정도의 문제라 문턱을 둡니다.

★ 이 도구는 화면에 나가는 글만 봅니다.
  주석·문서는 한다체로 써도 됩니다. 손님이 읽는 것만 셉니다.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import bank as bank_mod              # noqa: E402
from engine import lens as lens_mod              # noqa: E402
from engine import voice as voice_mod            # noqa: E402
from engine.calendar import build_chart          # noqa: E402
from engine.features import build_features       # noqa: E402
from engine.report import build_report           # noqa: E402

TAG = re.compile(r"<[^>]+>")

# ══════════════════════════════════════════════════════════
# 어미 가리기
# ══════════════════════════════════════════════════════════
#
# ★ 순서가 뜻입니다. 「네요」 를 「네」 보다 먼저 봐야 하게체로 안 셉니다.
#   「…요」 는 맨 뒤입니다 — 「자리요」 같은 하오체 명사 종결이라,
#   앞의 것들이 다 빗나간 뒤에야 여기로 옵니다.
_ENDS = (
    ("hapsyo", ("십시오", "습니다", "ㅂ니다", "니다")),
    ("haeyo", ("네요", "세요", "에요", "예요", "아요", "어요", "여요",
               "워요", "해요", "돼요", "봐요", "줘요", "래요")),
    ("hage", ("게나", "네", "구먼", "게")),
    ("banmal", ("지", "야", "어", "아")),
    ("hao", ("시오", "오", "소")),
)

# 한다체 — 뱅크에 있으면 안 되는 꼴. 스무 명 전부에게 그대로 나갑니다.
_HANDA = ("한다", "된다", "있다", "없다", "이다", "간다", "온다", "본다")


# 어미가 아니라 **조사**로 끝나는 줄 — 근거 줄·이름표가 이렇습니다.
#   「지금 대운 庚申 비견, 35살까지」 의 「까지」 를 반말 「지」 로 세면
#   합쇼체 캐릭터가 반말을 한 것처럼 잡힙니다.
_PARTICLE = ("까지", "부터", "에서", "으로", "마다", "처럼", "보다", "인가")


def ending_of(sent: str) -> str:
    """문장 하나의 말투. 못 가리면 '기타'."""
    w = sent.rstrip()
    if not w:
        return "기타"
    if w.endswith(_PARTICLE):
        return "기타"
    # ★ 「해요」 하나만 따로 봅니다.
    #   「그 판의 한 해요」 의 해는 **해(年)** 라 하오체 명사 종결이고,
    #   「말해요」 의 해요는 해요체 동사입니다. 꼬리가 같아서, 낱말이
    #   통째로 「해요」 일 때만 이름으로 셉니다.
    if w.split()[-1] == "해요":
        return "hao_noun"
    for tone, tails in _ENDS:
        for t in tails:
            if w.endswith(t):
                return tone
    if w.endswith("요"):
        return "hao_noun"          # 자리요 · 글자요 — 하오체 명사 종결
    for t in _HANDA:
        if w.endswith(t):
            return "handa"
    return "기타"


# 덩이를 가르는 태그 — 이걸 그냥 지우면 「…갈리오.해로 좁혀」 처럼
# 두 문장이 한 줄로 붙어, 뒷 문장의 어미로 앞 문장을 잘못 셉니다.
_BLOCK = re.compile(r"</(?:p|div|li|ul|ol|h[1-6]|em|blockquote)>|<br\s*/?>")


def sentences(html: str) -> list:
    """문장으로 가른다. 태그는 걷되 덩이는 갈라 둔다."""
    txt = TAG.sub("", _BLOCK.sub(chr(10), html))
    txt = txt.replace("&nbsp;", " ")
    out = []
    for s in re.split(r"(?<=[.!?…])\s+|\n+", txt):
        s = re.sub(r"\s+", " ", s).strip()
        s = s.rstrip(".!?… ")
        if len(s) > 4:
            out.append(s)
    return out


# ══════════════════════════════════════════════════════════
# 한 사람이 하는 말을 다 모은다
# ══════════════════════════════════════════════════════════
CHARTS = [(1993, 11, 25, 13), (1988, 3, 3, 7), (2001, 7, 19, 20),
          (1975, 6, 6, 4)]
CONCERNS = ("money", "love", "health")


def said(lid: str, price) -> list:
    """그 캐릭터의 리포트에서 손님이 읽는 문장 전부."""
    got = []
    tier = "one" if price else "free"
    for i, (y, m, d, h) in enumerate(CHARTS):
        f = build_features(build_chart(y, m, d, h, 0, "M", True, "서울"))
        try:
            r = build_report(f, "cid", lid, tier, CONCERNS[i % len(CONCERNS)],
                             None)
        except Exception:                          # noqa: BLE001
            continue
        for k in ("opening", "closing"):
            got += sentences(r.get(k) or "")
        for c in r.get("cuts", []):
            got += sentences(c.get("html", ""))
    return got


def hooked() -> list:
    """훅 5단. 어느 캐릭터가 내주든 같은 글이 나갑니다."""
    got = []
    for y, m, d, h in CHARTS:
        f = build_features(build_chart(y, m, d, h, 0, "M", True, "서울"))
        for concern in CONCERNS:
            try:
                segs = bank_mod.build_hook(f, concern)
            except Exception:                      # noqa: BLE001
                continue
            for s in segs:
                got += sentences(s.get("html", ""))
                for k in ("yes", "no", "q"):
                    got += sentences(s.get(k) or "")
    return got


# ══════════════════════════════════════════════════════════
# ② 굳은 문장 — 다섯 말투에서 글자가 똑같은 것
# ══════════════════════════════════════════════════════════
def frozen(lines: list) -> list:
    """
    다섯 말투를 다 걸어도 안 바뀌는 종결 문장.

    ★ 이게 왜 버그인가 — 뱅크가 하오체면 speak 가 반드시 손을 댑니다.
      안 바뀐다는 것은 **원문이 하오체가 아니라는 뜻**이고, 그러면 그
      문장만 스무 명에게 똑같은 어미로 나갑니다.
    """
    bad = []
    for s in lines:
        forms = {voice_mod.speak(s + ".", v) for v in voice_mod.VOICES}
        if len(forms) > 1:
            continue
        tone = ending_of(s)
        if tone in ("hao", "hao_noun", "기타"):
            continue                    # 하오체거나 어미가 아닌 줄
        bad.append((tone, s))
    return bad


def main() -> int:
    show = "--show" in sys.argv
    lenses = lens_mod.released()
    view = lens_mod._views()

    print("=" * 76)
    print("  말투 감사 — 스무 명이 제 말투로만 말하는가")
    print("=" * 76)
    print()

    mixed_total = 0
    skew_bad = []
    rows = []
    for l in lenses:
        lid = l["id"]
        v = (view.get(lid) or {}).get("voice") or "hao"
        lines = said(lid, l.get("price"))
        if not lines:
            continue
        tones = Counter(ending_of(s) for s in lines)
        # ① 섞임 — 제 말투도, 하오체 명사 종결도, 기타도 아닌 것
        wrong = [(t, s) for s in lines
                 for t in [ending_of(s)]
                 if t not in (v, "hao_noun", "기타")]
        mixed_total += len(wrong)
        # ③ 쏠림 — 어미 한 결이 몇 %인가
        named = sum(c for t, c in tones.items() if t != "기타")
        top = tones.most_common(1)[0] if named else ("기타", 0)
        share = (100.0 * tones[v] / named) if named else 0.0
        rows.append((lid, v, len(lines), len(wrong), share, top))
        if show and wrong:
            print("  ── %s (%s) — 섞인 문장 %d" % (lid, v, len(wrong)))
            for t, s in wrong[:8]:
                print("       [%s] %s" % (t, s[:64]))
            print()

    print("  ① 섞임 — 제 말투가 아닌 문장")
    print("     %-11s %-7s %6s %7s %7s" % ("캐릭터", "말투", "문장", "섞임",
                                           "제말투%"))
    for lid, v, n, w, share, _top in sorted(rows, key=lambda r: -r[3]):
        mark = "  ←" if w else ""
        print("     %-11s %-7s %6d %7d %6.0f%%%s" % (lid, v, n, w, share, mark))
    print()
    print("     섞인 문장 합계 %d" % mixed_total)
    print()

    # ② 굳은 문장
    all_lines = []
    for l in lenses[:1]:
        all_lines += said(l["id"], l.get("price"))
    all_lines += hooked()
    fro = frozen(sorted(set(all_lines)))
    print("  ② 굳은 문장 — 다섯 말투에서 글자가 똑같은 것  %d" % len(fro))
    if fro:
        by = Counter(t for t, _ in fro)
        for t, c in by.most_common():
            print("       %-8s %3d" % (t, c))
        print()
        for t, s in fro[:20 if show else 8]:
            print("       [%s] %s" % (t, s[:66]))
    print()

    # ③ 쏠림
    print("  ③ 쏠림 — 한 어미가 그 사람 문장의 몇 %를 먹는가")
    for lid, v, n, w, share, top in sorted(rows, key=lambda r: -r[4])[:6]:
        print("     %-11s %-7s 으뜸 %-9s %3d회" % (lid, v, top[0], top[1]))
    print()
    print("-" * 76)
    print("  ①② 는 버그입니다. 뱅크를 하오체로 되돌리거나 speak 를")
    print("  거치게 하면 사라집니다. tests/test_voice_clean.py 가 셉니다.")
    print("-" * 76)
    return 1 if (mixed_total or fro) else 0


if __name__ == "__main__":
    raise SystemExit(main())
