# -*- coding: utf-8 -*-
"""
한 장을 잰다 — **v2 와 v1 을 같은 자로** 나란히.

★ 왜 자가 먼저인가

  이 집은 같은 사고를 두 번 겪었습니다 — 자가 제품보다 좁아서,
  고쳐서 **배포까지 했는데 손님 화면에는 안 닿았고** 자는 「고쳤다」 고
  찍었습니다. 그래서 v2 를 짜기 전에 자부터 둡니다.

  재는 것 (게이트):

      손님 축 겹침    사주만 바꿨을 때 글자 그대로 같은 몫
      시키는 일       한 장에 몇 개인가 (하나여야 하오)
      파는 말         한 장에 몇 곳인가 (한 곳이어야 하오)
      되풀이          글자 그대로 같은 문장
      분량            예산 안인가
      근거에 수       아라비아 숫자가 든 근거 줄의 비율
      가드            금지어 위반

씀:
    python tools/page_audit.py              # v2 · v1 나란히
    python tools/page_audit.py --show       # v2 한 장을 글로
    python tools/page_audit.py --show v1    # v1 한 장을 글로
"""
from __future__ import annotations

import difflib
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "services" / "api", ROOT, ROOT / "tools"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine import guard as guard_mod          # noqa: E402
from engine.reading.claim import FACT          # noqa: E402
from engine import reading                     # noqa: E402
from engine.calendar import build_chart        # noqa: E402
from engine.features import build_features     # noqa: E402
from engine.report import build_report         # noqa: E402
import seen_page as SP                         # noqa: E402

AS_OF = date(2026, 9, 27)
CONCERN = "money"
LENS = "pungun"
TOPIC = {"concern": "money", "choice": "invest", "choice2": "spread",
         "choice3": "earn", "choice4": "b", "choice5": "b"}
#: ★ 한 사람으로 재면 그 사람 몫 겹침이 100% 로 찍히고 나머지 몫은
#:   한 번도 안 찍힙니다. 여럿을 봅니다.
PEOPLE = [(1993, 4, 5, 0, 0, "F", False), (1978, 11, 22, 14, 10, "M", True),
          (2001, 7, 3, 6, 40, "F", True), (1966, 1, 19, 21, 5, "M", True),
          (1985, 9, 14, 11, 20, "F", True)]

FREE_DETAIL = {"spine_depth", "spine_scene", "lens_bridge"}


def feats(row):
    y, m, d, h, mi, sex, hk = row
    return build_features(build_chart(y, m, d, h, mi, sex, hour_known=hk),
                          as_of=AS_OF)


# ── 한 장을 토막으로 ─────────────────────────────────────────────
def page_v2(f) -> list:
    """돌려주는 것: [(자리, 제목, 본문, 근거)]"""
    p = reading.build(f, CONCERN, "free")
    out = [("주장", p.thesis, "", "")]
    # ★ 첫머리 도출 명시도 손님이 읽는 글이오 — 자에 넣습니다.
    if p.derived:
        out.append(("도출", "무엇에서 나왔는가", SP.plain(p.derived.html), ""))
    for c in p.claims:
        out.append((c.axis, c.verdict, SP.plain(c.body), c.source))
    rx = p.prescription
    out.append(("처방", "오늘 할 하나",
                " ".join((rx.한가지, rx.확인, rx.갈림)), "축 · " + rx.축))
    for c in p.appendix:
        out.append(("부록:" + c.axis, c.verdict, SP.plain(c.body), c.source))
    for l in reading.locked_list(f, CONCERN, "free"):
        out.append(("잠김:" + l["axis"], l["title"], "", l["counted"]))
    return out


def page_v1(f) -> list:
    """화면이 이어 붙이는 차례 그대로 (apps/web/app/pay/page.tsx d0)."""
    rep = build_report(f, "m", LENS, "free", CONCERN, "INTP",
                       extras={"topic": TOPIC})
    cuts = {c["id"]: c for c in rep["cuts"]}
    ed, pr = rep.get("editorial"), rep.get("practice")
    out = []
    sp = cuts.get("spine")
    if sp:   # 1단계 머리 = spine 의 bite. 뒤에서 같은 컷을 또 폅니다.
        m = re.search(r'<p[^>]*class="[^"]*\bbite\b[^"]*"[^>]*>([\s\S]*?)</p>',
                      sp["html"])
        out.append(("1단계", "", SP.plain(m.group(1) if m else ""), SP.plain(sp["source"])))
    if ed:
        out.append(("1단계관점", "", " ".join(
            str(ed.get(k) or "") for k in
            ("perspective", "question", "scene", "boundary")), ""))
    for cid in ("spine_depth", "spine_scene", "lens_bridge"):
        c = cuts.get(cid)
        if c:
            out.append(("3단계:" + cid, c["title"], SP.plain(c["html"]),
                        SP.plain(c["source"])))
    if pr:
        out.append(("4단계", pr["title"], " ".join(
            [str(pr.get(k) or "") for k in
             ("focus", "decision", "trap", "review", "example", "mbti")]
            + list(pr.get("steps") or [])), pr["source"]))
    for c in rep["cuts"]:
        if c["id"] in FREE_DETAIL:
            continue
        out.append(("근거절:" + c["id"], c["title"], SP.plain(c["html"]),
                    SP.plain(c["source"])))
    for l in rep["locked"]:
        out.append(("잠김:" + l["id"], l["title"], SP.plain(l["teaser"]),
                    SP.plain(l["source"])))
    return out


# ── 잣대 ────────────────────────────────────────────────────────
_NORM = lambda s: re.sub(r"[^0-9A-Za-z가-힣一-鿿]", "", s)
#: ★ 한자를 지우면 안 됩니다 (2026-09-28). 「그대 글자 戊午 · 癸亥에서
#:   나온 것이오」 가 사람마다 다른 글자인데, 한자를 지우니 여섯 사람
#:   문장이 글자 그대로 같다고 찍혔습니다 — 자가 제 눈을 가린 것이오.
_SELL = re.compile(r"결제|구매 후|값을 치|가격|열립니다|열리오|더 이어지|"
                   r"사시면|풀이 열기")
_HEDGE = re.compile(r"단정하(지|는)|맞는 말로 취급|억지로|경험을 먼저|"
                    r"내 이야기로|계산 결과가 아니오|아닌 줄")


def sents(t):
    t = re.sub(r"\s+", " ", t)
    return [s.strip() for s in
            re.split(r"(?<=오\.)|(?<=소\.)|(?<=요\.)|(?<=다\.)|(?<=[.!?])\s+", t)
            if len(s.strip()) >= 12]


def measure(pages: list, name: str) -> dict:
    one = pages[0]
    body = " ".join(b for _, _, b, _ in one)
    src = [s for _, _, _, s in one if s]
    allx = [(w, s) for w, _, b, _ in one for s in sents(b)]
    cnt = Counter(_NORM(s) for _, s in allx)
    dup = {k: v for k, v in cnt.items() if v > 1 and len(k) >= 12}

    # 손님 축 겹침 — 자리별로 맞대고 8자 이상 이어진 덩이만
    keys = [w for w, _, _, _ in one]
    tot = same = 0
    worst = []
    for i, (w, _, b, _) in enumerate(one):
        if len(b) < 20:
            continue
        common = b
        for other in pages[1:]:
            row = next((x for x in other if x[0] == w), None)
            if row is None:
                common = ""
                break
            sm = difflib.SequenceMatcher(None, common, row[2], autojunk=False)
            common = "".join(common[a:a + n]
                             for a, _, n in sm.get_matching_blocks() if n >= 8)
        tot += len(b)
        same += len(common)
        worst.append((w, len(b), len(common) / len(b)))

    viol = []
    for w, _, b, s in one:
        ok, hits = guard_mod.check(b + " " + s)
        if not ok:
            viol.append((w, hits))

    # ── 명패 시험: **문장째 남과 같은 것** ──────────────────────
    #
    # ★ 왜 덩이 겹침과 따로 재는가 (2026-09-28)
    #
    #   손님이 「하드코딩된 말을 전부 없애라」 하셨습니다. 그 말의 단위는
    #   **문장**이오 — 「지금 33살이오」 와 「지금 48살이오」 는 여덟 자
    #   덩이로는 겹치지만 손님 눈에는 다른 말입니다. 한국말 문장 뼈대는
    #   겹치는 것이 정상이오.
    #
    #   문헌이 가리키는 잣대도 이쪽입니다 — Greene(1977)·Harris &
    #   Greene(1984): 바넘 문장은 「맞다」 를 올리고 「나만의 것」 을
    #   떨어뜨립니다. 그 「나만의 것」 은 **남의 풀이에도 그대로 있는
    #   문장이 몇 자인가**로 잽니다.
    #
    #   그래서 둘을 다 냅니다 — 덩이 겹침(뼈대까지)과 명패(문장째).
    others = set()
    for other in pages[1:]:
        for w, _, b, _ in other:
            for x in sents(b):
                others.add(_NORM(x))
    same_s = sum(len(x) for _, x in allx if _NORM(x) in others)
    body_len = sum(len(x) for _, x in allx) or 1

    # ── 날카로움: 댈 수 있는 값이 든 문장의 몫 ──
    hard = sum(1 for _, x in allx if FACT.search(x))
    # ── 첫 화면: 가장 먼저 읽는 세 문장에 센 값이 몇 개 ──
    head3 = [x for _, x in allx][:3]
    # ── 리듬: 컷마다 「센값/뜬말」 차례가 몇 가지인가 ──
    beats = set()
    for w, _, b, _ in one:
        ss = sents(b)
        if len(ss) >= 2:
            beats.add(tuple("수" if FACT.search(x) else "뜬" for x in ss))

    return {
        "name": name,
        "명패겹침": 100.0 * same_s / body_len,
        "센값비율": (100.0 * hard / len(allx)) if allx else 0.0,
        "첫3문장센값": sum(len(FACT.findall(x)) for x in head3),
        "리듬가지": len(beats),
        "토막": len(one),
        "글자": sum(len(b) for _, _, b, _ in one),
        "문장": len(allx),
        "되풀이종": len(dup),
        "되풀이자": sum(len(k) * (v - 1) for k, v in dup.items()),
        # ★ 마침표를 요구하면 「…적으시오 — 쥐는 글자가…」 를 못 셉니다.
        #   시키는 말은 꼬리가 아니라 **말 그 자체**로 셉니다.
        "시키는일": len(re.findall(r"(?:시오|십시오|하세요)(?![가-힣])", body)),
        "파는말": len(_SELL.findall(body)),
        "면책": len(_HEDGE.findall(body)),
        "손님축겹침": (100.0 * same / tot) if tot else 0.0,
        "근거에수": (100.0 * sum(1 for s in src if re.search(r"\d", s)) / len(src))
                    if src else 0.0,
        "가드위반": len(viol),
        "worst": sorted(worst, key=lambda x: -x[1] * x[2])[:6],
        "dup": dup,
    }


GATE = {"명패겹침": ("≤", 10.0), "손님축겹침": ("≤", 55.0),
        "센값비율": ("≥", 55.0),
        "첫3문장센값": ("≥", 3), "시키는일": ("=", 1), "파는말": ("≤", 1),
        "되풀이종": ("=", 0), "글자": ("≤", 5800), "가드위반": ("=", 0),
        "근거에수": ("≥", 90.0), "면책": ("≤", 2)}


def main(argv):
    if "--show" in argv:
        which = argv[argv.index("--show") + 1] if len(argv) > argv.index("--show") + 1 else "v2"
        f = feats(PEOPLE[0])
        rows = page_v1(f) if which == "v1" else page_v2(f)
        for w, t, b, s in rows:
            print("\n── %s · %s" % (w, t))
            if s:
                print("   근거 · %s" % s)
            if b:
                print("   " + b)
        return 0

    v2 = measure([page_v2(feats(p)) for p in PEOPLE], "v2")
    v1 = measure([page_v1(feats(p)) for p in PEOPLE], "v1")

    print("%-12s %10s %10s   %s" % ("잣대", "v1(지금)", "v2(새것)", "게이트"))
    print("-" * 56)
    for k, (op, want) in GATE.items():
        a, b = v1[k], v2[k]
        fmt = "%10.1f" if isinstance(b, float) else "%10d"
        ok = {"≤": b <= want, "=": b == want, "≥": b >= want}[op]
        print(("%-12s " + fmt + " " + fmt + "   %s %s  %s")
              % (k, a, b, op, want, "통과" if ok else "✗"))
    print("-" * 56)
    for m in (v1, v2):
        print("%s  토막 %d · %d자 · 문장 %d · 되풀이 %d종 %d자"
              % (m["name"], m["토막"], m["글자"], m["문장"],
                 m["되풀이종"], m["되풀이자"]))
    print("\n가장 많이 겹치는 자리 (v2)")
    for w, n, r in v2["worst"]:
        print("   %-18s %5d자 %5.0f%%" % (w, n, r * 100))
    print("\n가장 많이 겹치는 자리 (v1)")
    for w, n, r in v1["worst"]:
        print("   %-18s %5d자 %5.0f%%" % (w, n, r * 100))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
