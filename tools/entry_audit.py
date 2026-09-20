"""
진입부 감사 — 값을 치르기 전에 보는 전부를 잰다.

    python tools/entry_audit.py            # 관문
    python tools/entry_audit.py --show     # 한 사람 분 전문

★ 왜 이 도구가 따로 있나

  2026-09-20 에 재 보니 **이 구간만 어떤 자에도 안 걸리고 있었습니다.**
  `easy` `sharp` `likeme` `drama` `say` `voice` `falsifiable` `worth` —
  어느 도구도 `engine/entry_hook.py` 를 읽지 않았습니다. 화면 글은
  `seed/screen_text.json` 을 거쳐 잡히는데, **서버가 만드는 첫 해석**은
  아무도 안 봤습니다.

  그래서 이렇게 되어 있었습니다 (docs/45 §5):

      본문 480자 · 아라비아 숫자 0개 · 분기 30개 · 최다 점유 21.1%
      장면 30개가 전부 물음표 · 자기부정 문장 3개 · 같은 근거 3번 반복

  재지 않아서 아무도 못 봤습니다. 고친 것보다 **재는 자를 둔 것**이
  더 오래 갑니다.

★ 무엇을 재나 (문턱은 docs/45 §7-1)

  ① 들머리(a1) 글자 수                     500자 이하
  ①' 입력 구간(a5·a3·a6) 글자 수          1,200자 이하
  ② 본문 천 자당 **셀 수 있는 값**         10 이상
  ③ 같은 고민 안에서 **최다 점유**         2% 이하   ← 손님이 친구와 대 봅니다
  ④ **틀릴 수 있는 문장**                  22% 이상
  ⑤ **자기부정 문장**                      0
  ⑥ **근거가 장마다 다른가**               예
  ⑦ **단정이 있는가** (장면이 물음표만은 아닌가)
  ⑧ **풀이 없이 나온 어려운 말**           0

  ★ ②는 가짓수가 아니라 **대 볼 수 있는 값**을 셉니다. 아라비아 수와
    한글 수를 따로 찍습니다 — 이 집은 수를 한글로도 적기 때문에
    `\\d` 만 보는 자는 절반을 못 봅니다(`bank.count_word`).
"""
from __future__ import annotations

import collections
import html
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT / "services" / "api"), str(ROOT / "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)

from falsifiable import judge                    # noqa: E402
from engine import entry_hook                    # noqa: E402
from engine.calendar import build_chart          # noqa: E402
from engine.features import build_features       # noqa: E402

TAGS = re.compile(r"<[^>]+>")
GLOSS = re.compile(r'<i class="gl">.*?</i>', re.S)
# ★ **틀릴 수 있는 수만** 셉니다. 「여덟 글자」는 늘 여덟이라 셈이 아니고
#   「다섯이 비었소」는 넷이면 틀립니다. `tests/test_falsifiable.py` 와
#   같은 한 벌을 씁니다 — 재는 자가 둘이면 언젠가 갈립니다.
NUM_HAN = re.compile(r"(?:하나|둘|셋|넷|다섯|여섯|일곱|여덟|아홉|열)"
                     r"(?=이오|이고|이네|이에요|뿐|밖에|째|이 비|가 비)"
                     r"|하나도 없")
NUM_AR = re.compile(r"\d+")

# 해석을 스스로 깎는 말. 아니라고 답할 자리는 **버튼**이 따로 있습니다 —
# 문장으로 또 물러서면 남는 것은 물러선 자국뿐입니다.
HEDGE = ("다르다면 다르다고", "내려놓아도 되오", "증명하는 값은 아니오",
         "여러 관점 중 하나", "맞는 부분만", "참고만")

# 화면이 손님에게 읽히는 **설명** — 첫 해석 앞의 고정 문구.
#
# ★ 들머리와 입력 구간을 **따로** 셉니다. 들머리는 「여기가 무엇을 하는
#   집인가」를 말해야 하는 자리라 한 문단이 필요하고, 입력 구간은
#   묻는 것마다 까닭 한 줄이면 됩니다. 한 칸으로 합쳐 두면 둘 중
#   어느 쪽이 부은 것인지 안 보입니다.
GATE = {"들머리(a1)": 500, "입력 구간(a5·a3·a6)": 1200,
        "천자당 수": 10.0, "최다 점유": 2.0, "틀릴 수 있는 문장": 22.0}

CHARTS = [(1997, 3, 22, 14, 10, "F"), (1985, 11, 3, 7, 40, "M"),
          (2001, 6, 18, 21, 5, "F"), (1972, 9, 9, 3, 25, "M"),
          (1993, 5, 15, None, None, "F")]


def plain(h: str) -> str:
    """태그를 걷는다. 괄호 풀이는 **본문이 아니라 주석**이라 뺍니다."""
    return TAGS.sub("", GLOSS.sub("", html.unescape(h or "")))


def features():
    for y, m, d, hh, mi, sx in CHARTS:
        yield build_features(build_chart(y, m, d, hh, mi, sx,
                                         hour_known=hh is not None))


def _ko(body: str) -> int:
    got = re.findall(r"[가-힣][가-힣0-9 ,.·?!“”‘’~—\-()]*", body)
    return len(re.sub(r"\s", "", " ".join(g.strip() for g in got)))


def screen_words() -> tuple:
    """(들머리, 입력 구간) — 첫 해석 전에 읽는 설명."""
    src = (ROOT / "apps/web/components/EntryFlow.tsx").read_text("utf-8")
    # 주석은 손님이 안 읽습니다.
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    src = re.sub(r"//[^\n]*", " ", src)
    parts = re.split(r'if \(step === "(\w+)"\)', src)
    blocks = dict(zip(parts[1::2], parts[2::2]))
    concerns = _ko((ROOT / "apps/web/lib/entry-copy.ts").read_text("utf-8"))
    gate = _ko(blocks.get("a1", ""))
    form = sum(_ko(blocks.get(k, "")) for k in ("a5", "a3", "a6")) + concerns
    return gate, form


def corpus(f):
    out = []
    for concern in entry_hook.CONCERNS:
        out.extend(entry_hook.build(f, concern))
    return out


def spread(n: int = 1200) -> tuple:
    """같은 고민을 고른 사람들 안에서 같은 글을 받는 비율."""
    random.seed(20260920)
    seen = collections.Counter()
    for _ in range(n):
        known = random.random() > 0.15
        f = build_features(build_chart(
            random.randint(1970, 2006), random.randint(1, 12),
            random.randint(1, 28),
            random.randint(0, 23) if known else None,
            0 if known else None, random.choice("FM"), hour_known=known))
        seen[" ".join(plain(c["html"]) for c in corpus(f)[:4])] += 1
    return len(seen), 100 * max(seen.values()) / n


def main() -> int:
    if "--show" in sys.argv:
        f = next(features())
        for c in entry_hook.build(f, "work"):
            print("─" * 70)
            print("[%s] %s" % (c["stage"], c["label"]))
            for line in plain(c["html"]).split("</p>"):
                if line.strip():
                    print("   " + line.strip())
            print("   근거 ·", plain(c["source"]))
        return 0

    print("=" * 70)
    print("  진입부 감사 — 값을 치르기 전에 보는 전부")
    print("=" * 70)

    body, source, chapters = [], [], []
    for f in features():
        cs = corpus(f)
        chapters.extend(cs)
        body.extend(plain(c["html"]) for c in cs)
        source.extend(plain(c["source"]) for c in cs)
    text = " ".join(body)
    n = len(re.sub(r"\s", "", text))
    ar, han = len(NUM_AR.findall(text)), len(NUM_HAN.findall(text))
    sents, hard, _ = judge(text)
    per1k = (ar + han) / max(n, 1) * 1000

    gate_n, form_n = screen_words()
    kinds, top = spread()
    hedges = sum(text.count(h) for h in HEDGE)

    one = entry_hook.build(next(features()), "work")
    same_source = len({c["source"] for c in one}) < len(one)
    # 장면 장(두 번째)이 물음표로만 끝나면 단정이 하나도 없다는 뜻입니다.
    scene_asks = sum(1 for s in entry_hook.SCENES.values()
                     for v in s.values() if v[0].rstrip().endswith("?"))

    rows = [
        ("들머리(a1)", gate_n, GATE["들머리(a1)"], gate_n <= GATE["들머리(a1)"], "자"),
        ("입력 구간(a5·a3·a6)", form_n, GATE["입력 구간(a5·a3·a6)"],
         form_n <= GATE["입력 구간(a5·a3·a6)"], "자"),
        ("천자당 수", round(per1k, 1), GATE["천자당 수"],
         per1k >= GATE["천자당 수"], "  (아라비아 %d · 한글 %d)" % (ar, han)),
        ("최다 점유", round(top, 2), GATE["최다 점유"], top <= GATE["최다 점유"],
         "%%  (서로 다른 글 %d)" % kinds),
        ("틀릴 수 있는 문장", round(100 * hard / max(sents, 1), 1),
         GATE["틀릴 수 있는 문장"], 100 * hard / max(sents, 1) >= GATE["틀릴 수 있는 문장"], "%"),
        ("자기부정 문장", hedges, 0, hedges == 0, "개"),
        ("근거가 장마다 다른가", "아니오" if same_source else "예", "예",
         not same_source, ""),
        ("물음표로만 끝나는 장면", scene_asks, 0, scene_asks == 0, "개"),
    ]
    bad = 0
    for name, got, want, ok, unit in rows:
        bad += 0 if ok else 1
        print("  %-22s %8s%-22s  문턱 %-6s %s"
              % (name, got, unit, want, "통과" if ok else "★ 못 넘음"))

    print("-" * 70)
    print("  본문 %d자 · 근거 %d자 · 장 %d개 (고민 여섯 × 명식 %d)"
          % (n, len(re.sub(r"\s", "", " ".join(source))),
             len(chapters), len(CHARTS)))
    if bad:
        print("  ★ %d 칸이 문턱을 못 넘었소. docs/45 §7-1 을 보시오." % bad)
    else:
        print("  전부 통과. 고치면 이 자를 다시 돌리시오.")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
