"""
무료 구간 — 처음 들어온 사람이 값을 치르기 전까지 보는 전부.

★ 왜 따로 재는가
  이 서비스에서 값이 오가는 자리는 하나뿐입니다 — **무료 구간을 다 보고
  잠긴 컷을 마주한 그 순간.** 그 앞이 약하면 뒤의 관점 컷 92개는 아무도
  안 봅니다. 그런데 여태 이 구간만 따로 재는 도구가 없었습니다.
  dup_rate 는 문장 겹침을 보고, journey_sim 은 전 구간을 봅니다.
  여기서는 **처음 30초**만 봅니다.

  python tools/free_funnel.py            1만 명 재기
  python tools/free_funnel.py --show out.json   사람 여섯의 전문을 뽑기
"""
from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import lens as lens_mod                 # noqa: E402
from engine.bank import build_hook                  # noqa: E402
from engine.calendar import build_chart             # noqa: E402
from engine.features import build_features          # noqa: E402
from engine.report import build_report              # noqa: E402

TAG = re.compile(r"<[^>]+>")
AS_OF = date(2026, 8, 27)
CONCERNS = ("money", "work", "love", "people", "dir", "health")

# 서로 최대한 다른 여섯. 신강·신약·중화 · 시각 미상 · 넉 자 있고 없고 ·
# 고민도 다르게. 한 사람만 보면 우연에 속습니다.
SHOWCASE = [
    dict(label="스물아홉 · 여성 · 사랑", birth=(1997, 3, 22, 14, 10, "F"),
         known=True, concern="love", axis4="INFP", name="가은"),
    dict(label="마흔넷 · 남성 · 돈", birth=(1982, 11, 8, 3, 40, "M"),
         known=True, concern="money", axis4=None, name=""),
    dict(label="서른여섯 · 여성 · 일 · 시각 미상", birth=(1990, 6, 1, 0, 0, "F"),
         known=False, concern="work", axis4="ESTJ", name="현주"),
    dict(label="쉰둘 · 남성 · 사람", birth=(1974, 1, 30, 21, 5, "M"),
         known=True, concern="people", axis4=None, name=""),
    dict(label="스물셋 · 여성 · 갈 곳", birth=(2003, 9, 17, 7, 55, "F"),
         known=True, concern="dir", axis4="INTP", name="소민"),
    dict(label="예순 · 남성 · 몸", birth=(1966, 5, 5, 12, 30, "M"),
         known=True, concern="health", axis4=None, name=""),
]


def plain(html: str) -> str:
    return TAG.sub("", html or "").strip()


def _features(birth, known):
    y, mo, d, h, mi, sex = birth
    return build_features(build_chart(y, mo, d, h, mi, sex, hour_known=known),
                          as_of=AS_OF)


# ══════════════════════════════════════════════════════════
# 전문 뽑기 — 눈으로 볼 것
# ══════════════════════════════════════════════════════════
def showcase(lens_id: str = "nopa") -> list:
    out = []
    for spec in SHOWCASE:
        f = _features(spec["birth"], spec["known"])
        you = lens_mod.you_word(lens_id)
        segs = build_hook(f, spec["concern"], spec["axis4"],
                          name=spec["name"], you=you)
        rep = build_report(f, "show", lens_id, "free", spec["concern"],
                           spec["axis4"])
        out.append({
            "label": spec["label"],
            "concern": spec["concern"],
            "axis4": spec["axis4"],
            "pillars": [p["gz"] for p in f.pillars],
            "hour_known": f.hour_known,
            "day_gan": f.day_gan,
            "strength": f.strength,
            "weak_el": f.weak_el,
            "strong_el": f.strong_el,
            "top": f.top_ten_god,
            "flow": f.flow,
            "hook": [{"stage": s["stage"], "label": s["label"],
                      "source": s["source"], "html": s["html"],
                      "question": s["question"], "yes": s["yes"], "no": s["no"]}
                     for s in segs],
            "free_cuts": [{"id": c["id"], "title": c["title"],
                           "source": c["source"], "html": c["html"]}
                          for c in rep["cuts"]],
            "locked": [{"id": c["id"], "title": c["title"],
                        "source": c["source"], "need": c["need_tier"]}
                       for c in rep["locked"]],
            "opening": rep["opening"],
            "closing": rep["closing"],
        })
    return out


# ══════════════════════════════════════════════════════════
# 1만 명 재기 — 처음 30초의 품질
# ══════════════════════════════════════════════════════════
def measure(n: int = 10000, seed: int = 20260827) -> dict:
    rng = random.Random(seed)
    stage_txt = {}          # 단별 본문
    hook_all, free_all = [], []
    hook_chars, free_chars = [], []
    n_free_cuts, n_locked = [], []
    locked_titles = Counter()
    stage_count = Counter()
    no_axis = 0

    for _ in range(n):
        y = rng.randint(1960, 2007)
        mo, d = rng.randint(1, 12), rng.randint(1, 28)
        h, mi = rng.randint(0, 23), rng.randint(0, 59)
        sex = rng.choice(("M", "F"))
        known = rng.random() > 0.15
        concern = rng.choice(CONCERNS)
        axis4 = rng.choice((None, "INFP", "ESTJ", "INTP", "ENFJ", "ISTP"))
        if axis4 is None:
            no_axis += 1

        f = _features((y, mo, d, h, mi, sex), known)
        segs = build_hook(f, concern, axis4)
        rep = build_report(f, "m", "nopa", "free", concern, axis4)

        joined = []
        for s in segs:
            body = plain(s["html"])
            stage_txt.setdefault(s["stage"], []).append(body)
            stage_count[s["stage"]] += 1
            joined.append(body)
        hook_all.append("|".join(joined))
        hook_chars.append(sum(len(x) for x in joined))

        cuts = [plain(c["html"]) for c in rep["cuts"]]
        free_all.append("|".join(cuts))
        free_chars.append(sum(len(x) for x in cuts))
        n_free_cuts.append(len(rep["cuts"]))
        n_locked.append(len(rep["locked"]))
        for c in rep["locked"]:
            locked_titles[c["title"]] += 1

    def spread(rows):
        c = Counter(rows)
        top, hits = c.most_common(1)[0]
        eff = 1 / sum((v / len(rows)) ** 2 for v in c.values())
        return {"kinds": len(c), "effective": eff,
                "top_share": hits / len(rows), "sample": top[:80]}

    return {
        "n": n,
        "no_axis": no_axis / n,
        "stages": {k: dict(spread(v), shown=stage_count[k] / n)
                   for k, v in sorted(stage_txt.items())},
        "hook_whole": spread(hook_all),
        "free_whole": spread(free_all),
        "hook_chars": sorted(hook_chars),
        "free_chars": sorted(free_chars),
        "free_cuts": Counter(n_free_cuts),
        "locked_cuts": Counter(n_locked),
        "locked_titles": locked_titles,
    }


def _pct(x):
    return "%.1f%%" % (x * 100)


def main() -> int:
    if "--show" in sys.argv:
        dest = Path(sys.argv[sys.argv.index("--show") + 1])
        dest.write_text(json.dumps(showcase(), ensure_ascii=False, indent=1),
                        encoding="utf-8")
        print("사람 %d 명의 무료 구간 전문을 뽑았습니다 → %s"
              % (len(SHOWCASE), dest))
        return 0

    n = 10000
    for a in sys.argv[1:]:
        if a.isdigit():
            n = int(a)
    m = measure(n)

    print("무료 구간 — %d명\n" % m["n"])
    print("훅 단별  (본문만 · 근거 줄 제외)")
    print("  %-6s %6s %9s %10s %9s" % ("단", "나온율", "가짓수", "유효", "최다"))
    NAMES = {"0": "찌르기", "1": "부정확인", "2": "순서", "2.5": "어긋남",
             "3": "이름"}
    for k, v in m["stages"].items():
        print("  %-6s %6s %9d %10.1f %9s"
              % (NAMES.get(k, k), _pct(v["shown"]), v["kinds"],
                 v["effective"], _pct(v["top_share"])))

    print("\n훅 전문      %d가지 · 최다 %s"
          % (m["hook_whole"]["kinds"], _pct(m["hook_whole"]["top_share"])))
    print("무료 리포트   %d가지 · 최다 %s"
          % (m["free_whole"]["kinds"], _pct(m["free_whole"]["top_share"])))

    hc, fc = m["hook_chars"], m["free_chars"]
    def q(a, p):
        return a[int(len(a) * p) - 1]
    print("\n분량 (글자)")
    print("  훅        중앙 %4d · p10 %4d · p90 %4d" % (q(hc, .5), q(hc, .1), q(hc, .9)))
    print("  무료      중앙 %4d · p10 %4d · p90 %4d" % (q(fc, .5), q(fc, .1), q(fc, .9)))

    print("\n결제 갈림길에서 보이는 것")
    for k in sorted(m["free_cuts"]):
        print("  무료 컷 %2d개 — %s" % (k, _pct(m["free_cuts"][k] / m["n"])))
    for k in sorted(m["locked_cuts"]):
        print("  잠긴 컷 %2d개 — %s" % (k, _pct(m["locked_cuts"][k] / m["n"])))

    print("\n잠긴 컷 제목 (이게 궁금증을 만드는 자리)")
    for t, c in m["locked_titles"].most_common():
        print("  %-24s %s" % (t, _pct(c / m["n"])))

    bad = [k for k, v in m["stages"].items() if v["top_share"] > 0.05]
    if bad:
        print("\n[X] 한 문장이 5%% 넘게 겹치는 단: %s" % ", ".join(bad))
        return 1
    print("\n[OK] 어느 단도 한 문장이 5%%를 넘지 않습니다")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
