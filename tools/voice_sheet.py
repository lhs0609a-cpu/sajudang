"""
목소리를 넣을 문장이 몇 개인가 — 발주 전에 세는 자리.

    python tools/voice_sheet.py
    python tools/voice_sheet.py --write out.json    읽힐 문장을 뽑아 적는다

★ 왜 세고 시작하나

  "훅 5단과 캐릭터 첫마디만" 이라고 하면 스물다섯 마디쯤으로 들린다.
  그런데 **훅은 고정 문장이 아니다.** 사람의 여덟 글자에서 조합된다 —

      0 찌르기   STAB[고민][약한 오행] + STAB2[주도십신]
      1 부정확인 MYTH_TG[십신][고민] + MYTH_ST[강약][고민] + PATT[십신].b
      ...

  그래서 미리 만들어 둘 수 있는지 없는지는 **재 봐야** 안다. 여기서
  인구 표본을 돌려 실제로 몇 가지가 나오는지 센다.

★ 세 갈래로 갈린다

  고정   캐릭터 첫마디 · 화면에 박힌 도령의 말
         → 미리 만들어 파일로 둔다. 값이 한 번만 든다.
  조합   훅 5단
         → 가짓수를 보고 정한다. 적으면 미리, 많으면 그때그때 만들고
           같은 문장은 다시 안 만든다(해시로 곳간에 둔다).
  본문   리포트 컷 2,000여 개
         → 읽히지 않는다. 값도 용량도 감당이 안 되고, 무엇보다 읽는
           속도를 손님이 정해야 하는 글이다.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine.calendar import build_chart                  # noqa: E402
from engine.features import build_features               # noqa: E402
from engine.bank import build_hook                       # noqa: E402

# dup_rate.py 와 같은 이름을 씁니다 — 도구마다 다르면 숫자를 못 견줍니다
CONCERNS = ["money", "work", "love", "people", "dir", "health"]
SEED_DIR = ROOT / "seed"
WEB = ROOT / "apps" / "web"


def _bare(html: str) -> str:
    """태그와 풀이 괄호를 걷어낸 말."""
    s = re.sub(r"<i class=\"gl\">\([^)]*\)</i>", "", html)
    s = re.sub(r"<[^>]*>", "", s)
    return " ".join(s.split()).strip()


def key(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def fixed_lines():
    """미리 만들 수 있는 말 — 화면에 박혀 있어 사람마다 안 변한다."""
    out = []

    # 캐릭터 첫마디
    try:
        lenses = json.loads((SEED_DIR / "lenses.json").read_text(encoding="utf-8"))
        items = lenses if isinstance(lenses, list) else lenses.get("lenses", [])
        for l in items:
            if isinstance(l, dict) and isinstance(l.get("opening_quote"), str):
                out.append(("캐릭터", l.get("id", "?"), l["opening_quote"]))
    except FileNotFoundError:
        pass

    # 화면에 박힌 도령의 말 (<Say> 안)
    for p in sorted((WEB / "app").rglob("*.tsx")):
        code = re.sub(r"/\*.*?\*/", " ", p.read_text(encoding="utf-8"), flags=re.S)
        code = re.sub(r"//[^\n]*", " ", code)
        for m in re.finditer(r"<Say[^>]*>(.{6,300}?)</Say>", code, re.S):
            t = _bare(re.sub(r"\{[^{}]*\}", "", m.group(1)))
            if len(t) >= 6 and re.search(r"[가-힣]", t):
                out.append(("화면", p.stem, t))
    return out


def hook_variety(n: int):
    """훅 5단이 실제로 몇 가지나 나오는가."""
    per_stage: list[Counter] = [Counter() for _ in range(5)]
    whole = Counter()
    made = 0
    import random
    rng = random.Random(20260901)

    for _ in range(n):
        c = build_chart(rng.randint(1960, 2006), rng.randint(1, 12),
                        rng.randint(1, 28), rng.randint(0, 23), 0,
                        rng.choice("FM"), True)
        f = build_features(c)
        for concern in CONCERNS:
            try:
                segs = build_hook(f, concern)
            except Exception:
                continue
            made += 1
            texts = []
            for i, s in enumerate(segs[:5]):
                t = _bare(s.get("html", "") if isinstance(s, dict) else str(s))
                if t:
                    per_stage[i][key(t)] += 1
                    texts.append(t)
            if texts:
                whole[key(" ".join(texts))] += 1
    return per_stage, whole, made


def main() -> int:
    n = 400
    print("=" * 76)
    print("  목소리를 넣을 문장 — 발주 전에 세기")
    print("=" * 76)

    fixed = fixed_lines()
    kinds = Counter(k for k, _, _ in fixed)
    uniq = {key(t) for _, _, t in fixed}

    print("\n[1] 고정 — 미리 만들어 두면 되는 말")
    for k, c in kinds.most_common():
        print("     %-8s %4d 마디" % (k, c))
    print("     서로 다른 말  %d 마디" % len(uniq))

    print("\n[2] 조합 — 훅 5단 (표본 %d명 × 고민 6가지)" % n)
    try:
        per_stage, whole, made = hook_variety(n)
    except Exception as e:                     # noqa: BLE001
        print("     못 셌습니다: %s" % e)
        return 0

    if not made:
        print("     못 셌습니다 (명식을 하나도 못 세웠습니다)")
        return 0

    tot = 0
    for i, c in enumerate(per_stage):
        if not c:
            continue
        top = c.most_common(1)[0][1] / sum(c.values()) * 100
        tot += len(c)
        print("     %d단   서로 다른 말 %4d   최다 점유 %.1f%%" % (i, len(c), top))
    print("     ─────────────────────────────────────────")
    print("     단별 합계        %4d 마디" % tot)
    print("     한 벌 통째로     %4d 가지 (%d 벌 중)" % (len(whole), made))

    print("\n[3] 무엇을 만들 것인가")
    print("     고정 %d + 훅 단별 %d = **%d 마디**" % (len(uniq), tot, len(uniq) + tot))
    print()
    print("     ★ 훅은 단(段)별로 만듭니다 — 한 벌 통째로 만들면 %d 가지라"
          % len(whole))
    print("       감당이 안 되고, 사람이 바뀔 때마다 새로 만들어야 합니다.")
    print("       단별로 두면 조합이 달라도 이미 만든 것을 다시 씁니다.")
    print()
    print("     ★ 리포트 본문(2,000여 컷)은 안 읽힙니다. 값도 용량도")
    print("       문제지만, 무엇보다 읽는 속도를 손님이 정해야 하는 글입니다.")

    if "--write" in sys.argv:
        out = ROOT / (sys.argv[sys.argv.index("--write") + 1]
                      if len(sys.argv) > sys.argv.index("--write") + 1
                      else "voice_lines.json")
        rows = [{"id": key(t), "kind": k, "where": w, "text": t}
                for k, w, t in fixed]
        out.write_text(json.dumps(rows, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        print("\n  고정 %d 마디를 적었습니다 — %s" % (len(rows), out))

    print("-" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
