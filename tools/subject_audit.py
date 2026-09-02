"""
주어 감사 — **누구 얘기인지 안 적힌 문장**을 찾는다.

    python tools/subject_audit.py            요약
    python tools/subject_audit.py --all      걸린 문장 전량

★ 무엇이 문제였나

  손님이 2026-09-02 에 화면을 보고 말했습니다 — "주어가 다 빠져있어."
  「2 · 왜 반복되나」 컷이 이렇게 나가고 있었습니다:

      먼저 만든다. 그리고 과정에서 즐거움을 얻는다.
      중화라 크게 티가 안 났을 게요. …
      그래서 끝에서 내놓은 것이 부족했다고 여긴다.

  가운데 줄만 손님에게 하는 말이고, 앞뒤는 **사전 뜻풀이**입니다.
  누가 만드는지, 누가 여기는지가 안 적혀 있습니다.

★ 왜 이렇게 됐나 — 뱅크 조각의 두 쓰임

  IGNITE · PATT · BLAME · FLOW · RESULT 는 **조각**입니다. 훅 2단의
  순서 상자(`<div class="seq">`)에서는 이 맨꼴이 맞습니다 — 상자 안에
  낱말로 서 있으니 주어가 필요 없습니다. 그런데 같은 조각을 리포트
  본문 문단에 그대로 떨어뜨리면 주어가 사라집니다.

  그래서 **문단에 쓸 때만** 주어를 답니다. 상자는 안 건드립니다.

★ 무엇을 잡나

  문단(`<p>`) 안의 문장 중
    · 한다체(-ㄴ다/-는다/-았다…)로 끝나고
    · 앞에 사람을 가리키는 말이 없는 것
  을 잡습니다. 하오체·합쇼체·해요체·반말로 끝나면 그건 손님에게
  하는 말이라 통과입니다.

  순서 상자(`.seq`)·근거 줄·표는 뺍니다. 거기서는 맨꼴이 맞습니다.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import lens as lens_mod                 # noqa: E402
from engine.bank import build_hook                  # noqa: E402
from engine.calendar import build_chart             # noqa: E402
from engine.daily import build_daily                # noqa: E402
from engine.features import build_features          # noqa: E402
from engine.report import build_report              # noqa: E402

AS_OF = date(2026, 8, 27)

# free_funnel.SHOWCASE 와 같은 여섯. 도구끼리 같은 사람을 봐야
# 한쪽에서 고친 것이 다른 쪽에서 보입니다.
PEOPLE = [
    ("스물아홉 · 여 · 사랑", (1997, 3, 22, 14, 10, "F"), True, "love", "INFP", "가은"),
    ("마흔넷 · 남 · 돈", (1982, 11, 8, 3, 40, "M"), True, "money", None, ""),
    ("서른여섯 · 여 · 일 · 시각미상", (1990, 6, 1, 0, 0, "F"), False, "work", "ESTJ", "현주"),
    ("쉰둘 · 남 · 사람", (1974, 1, 30, 21, 5, "M"), True, "people", None, ""),
    ("스물셋 · 여 · 갈 곳", (2003, 9, 17, 7, 55, "F"), True, "dir", "INTP", "소민"),
    ("예순 · 남 · 몸", (1966, 5, 5, 12, 30, "M"), True, "health", None, ""),
]

# 말투 다섯이 다 섞이게 고릅니다. 어미가 바뀌면 잡히는 것도 달라집니다.
LENSES = ("pungun", "nopa", "eunbyeol", "sigye", "hongmae", "dongja",
          "baegun", "wolha", "haengsu", "yakcho")
TIERS = ("free", "one", "all")

TAG = re.compile(r"<[^>]+>")
# 문단만 봅니다. 순서 상자·표·근거는 여기서 안 걸립니다.
PARA = re.compile(r"<p\b[^>]*>(.*?)</p>", re.S)
# 순서 상자는 통째로 들어냅니다 — 그 안의 맨꼴은 맞는 것입니다.
SEQ = re.compile(r'<div class="seq">.*?</div>\s*(?:</div>)?', re.S)
SPLIT = re.compile(r"(?<=[.!?…])\s+")

# ★ 한다체를 가려내는 법 — 뒤집어서 봅니다.
#
#   하오체·해요체·반말·하게체는 「다」로 안 끝납니다 (…소 · …오 · …요 ·
#   …지 · …네 · …게). 「다」로 끝나면서 손님에게 하는 말은 합쇼체
#   (…습니다 · …입니다) 와 하오체 청유(…하리다 · …주시다) 뿐입니다.
#
#   그래서 **「다」로 끝나되 「니다」·「리다」가 아닌 것** = 한다체입니다.
#   낱말을 하나씩 세는 것보다 이쪽이 안 샙니다.
PLAIN_TAIL = "다"
SPOKEN_DA = ("니다", "리다")

# 사람을 가리키는 말. **이것만** 주어로 봅니다.
#
# ★ 「[가-힣]{1,5}(은|는|이|가)」 같은 넓은 그물을 쓰면 안 됩니다 —
#   「만드는」·「얻는」의 「는」이 걸려서 주어 없는 문장이 통과합니다.
#   처음에 그렇게 짰다가 10종만 잡혔습니다. 좁혀야 보입니다.
SUBJ = re.compile(
    r"(그대|자네|당신|아저씨|그쪽|손님|어르신|낭자|도련님|"
    r"남들|사람들|세상|나는|내가|우리|누구|이 사람|그 사람|"
    r"[가-힣]{1,4}(?:씨|님)\b)")


def sentences(html: str) -> list:
    """문단 안의 문장만. 상자·표·근거는 빼고 본다."""
    if not html:
        return []
    body = SEQ.sub(" ", html)
    out = []
    for para in PARA.findall(body):
        txt = TAG.sub(" ", para)
        txt = txt.replace("&nbsp;", " ")
        txt = re.sub(r"\s+", " ", txt).strip()
        if not txt:
            continue
        out.extend(s.strip() for s in SPLIT.split(txt) if s.strip())
    return out


def headless(s: str) -> bool:
    """주어 없는 한다체인가."""
    body = s.rstrip(" .!?…。\"'”’)")
    if not body.endswith(PLAIN_TAIL) or body.endswith(SPOKEN_DA):
        return False
    return not SUBJ.search(s)


def _features(birth, known):
    y, mo, d, h, mi, sex = birth
    return build_features(build_chart(y, mo, d, h, mi, sex, hour_known=known),
                          as_of=AS_OF)


def scan():
    hits = Counter()
    where = defaultdict(set)

    def take(html, place):
        for s in sentences(html):
            if headless(s):
                hits[s] += 1
                where[s].add(place)

    for label, birth, known, concern, axis4, name in PEOPLE:
        f = _features(birth, known)

        for lens_id in LENSES:
            you = lens_mod.you_word(lens_id)
            for seg in build_hook(f, concern, axis4, name=name, you=you):
                take(seg["html"], "훅 %s단" % seg["stage"])

            for tier in TIERS:
                rep = build_report(f, "audit", lens_id, tier, concern, axis4,
                                   name=name)
                for c in rep["cuts"]:
                    take(c["html"], "컷 %s" % c["id"])
                take(rep.get("opening") or "", "여는 말")
                take(rep.get("closing") or "", "닫는 말")
                for l in rep.get("locked") or []:
                    take(l.get("teaser") or "", "잠긴 %s" % l.get("id"))

        d = build_daily(f, on=AS_OF)
        take(d.get("html") or "", "일진")

    return hits, where


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="걸린 문장 전량")
    a = ap.parse_args()

    hits, where = scan()
    kinds = len(hits)
    print("주어 감사 — 사람 %d · 캐릭터 %d · 값 %d"
          % (len(PEOPLE), len(LENSES), len(TIERS)))
    print("=" * 72)
    if not kinds:
        print("[OK] 주어 없는 한다체 문장 없음")
        return 0

    print("주어 없는 한다체 %d 종 · 연 %d 번" % (kinds, sum(hits.values())))
    print("-" * 72)
    rows = hits.most_common() if a.all else hits.most_common(30)
    for s, n in rows:
        print("%4d  %-44s  %s" % (n, s[:44], " · ".join(sorted(where[s])[:3])))
    if not a.all and kinds > len(rows):
        print("… %d 종 더. --all 로 다 봅니다." % (kinds - len(rows)))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
