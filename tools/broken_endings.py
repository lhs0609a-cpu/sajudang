# -*- coding: utf-8 -*-
"""
비문 사냥 — 말투 층이 문장 끝을 잘못 꿰는 자리.

    python tools/broken_endings.py [인원수]

★ 왜 따로 재나

  뱅크는 하오체 한 벌로 쓰고, `engine/voice.speak` 가 캐릭터마다 어미를
  갈아 끼웁니다 (docs/07). 그 갈이가 **연결 어미**에 걸리면 한국어가
  아닌 말이 나갑니다 —

      「지금 그 얼굴이 앞에 있고입니다.」      (…있고 + 입니다)
      「끊으게」 「끊으지」                      (매개모음 '으' 를 못 떼서)

  이 집은 이미 한 번 겪었습니다 (CLAUDE.md — 시키는 말이 비문). 그때는
  시키는 말만 봤습니다. 이 자는 **모든 문장 끝**을 봅니다.

★ 자가 무엇을 흠이라 하는가

  연결 어미(-고 · -며 · -지만 · -아서/어서) 바로 뒤에 종결 어미가 붙은
  자리, 매개모음이 남은 시킴꼴, 종결이 두 번 겹친 자리.
  아니라고 판정하는 쪽으로 좁게 잡습니다 — 없는 흠을 세면 고칠 자리가
  묻힙니다.
"""
from __future__ import annotations

import collections
import html as _html
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "services" / "api", ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine import bank as bank_mod              # noqa: E402
from engine import lens as lens_mod              # noqa: E402
from engine.calendar import build_chart          # noqa: E402
from engine.features import build_features       # noqa: E402
from engine.report import build_report           # noqa: E402

from tools import journey_sim as J               # noqa: E402

TAG = re.compile(r"<[^>]+>")

# ★ 자를 좁게 잡습니다 (2026-09-24).
#
#   처음에는 「-아서/-어서/-면서 + 종결」 까지 다 흠이라 했는데,
#   「혼자 짊어지고 있어서요.」 「배우고 기대면서 다시 일어서네.」 가
#   걸렸습니다. 앞은 멀쩡한 우리말이고 뒤는 「일어서-」 라는 어간입니다.
#   자가 부풀면 진짜 비문이 그 안에 묻힙니다.
#
#   남긴 것은 **연결 어미 -고 뒤에 종결이 붙은 자리**뿐입니다. 이름씨
#   (창고·사고·참고)는 -고로 끝나도 「창고입니다」 가 맞으므로, 앞에
#   붙는 것이 **움직씨 어간**일 때만 셉니다.
STEM = r"(?:있|없|하|되|아니|이|가|오|보|주|받|쓰|짓|남|참|들|나|살|묻|늘|접|맞)"
BAD = {
    "연결 어미 -고 뒤에 종결": re.compile(
        STEM + r"고(?:입니다|이에요|예요|이오|네|지|습니다)(?=[.!?…\s]|$)"),
    "종결이 두 번": re.compile(
        r"(?:입니다|습니다|이에요|예요|이오|소)"
        r"(?:입니다|습니다|이에요|예요|요|이오)(?=[.!?…]|$)"),
    "매개모음이 남은 시킴": re.compile(r"[가-힣]으(?:게|지)(?=[.!?…\s]|$)"),
    "어미가 겹친 물음": re.compile(r"(?:나요|까요|소|네)\?[^가-힣]*(?:요|까)\?"),
}

SENT = re.compile(r"[^.?!]+[.?!]")


def plain(h: str) -> str:
    t = (h or "").replace("<br />", "\n")
    return _html.unescape(TAG.sub("", t))


def sentences(h: str) -> list:
    out = []
    for line in plain(h).split("\n"):
        line = re.sub(r"\s+", " ", line).strip()
        if not line:
            continue
        got = [s.strip() for s in SENT.findall(line)]
        tail = SENT.sub("", line).strip()
        if tail:
            got.append(tail)
        out += [s for s in got if len(s) > 4]
    return out


def main() -> int:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    today = date(2026, 9, 24)
    pop = J.people(n, seed=20260925)
    lenses = [x["id"] for x in lens_mod.released()]
    hits = collections.Counter()
    where = collections.defaultdict(collections.Counter)
    eg = collections.defaultdict(list)
    for i, p in enumerate(pop):
        p["concern"] = J.CONCERNS[i % len(J.CONCERNS)]
        lens_id = lenses[i % len(lenses)]
        ch = build_chart(p["year"], p["month"], p["day"], p["hour"],
                         p["minute"], p["sex"], p["hour_known"], p["city"])
        f = build_features(ch, as_of=today)
        pages = [("훅", "".join(s["html"] for s in
                               bank_mod.build_hook(f, p["concern"], p["axis4"], "", "그대")))]
        for tier in ("free", "all"):
            rep = build_report(f, "sim", lens_id, tier, p["concern"], p["axis4"])
            for c in rep["cuts"]:
                pages.append(("%s/%s" % (lens_id, c["id"]), c["html"]))
        for label, html in pages:
            for s in sentences(html):
                for name, rx in BAD.items():
                    m = rx.search(s)
                    if m:
                        hits[name] += 1
                        where[name][label] += 1
                        if len(eg[name]) < 8:
                            eg[name].append("[%s] %s" % (label, s[:120]))
    print("\n비문 사냥 — %d명 · 캐릭터 %d명분\n" % (n, len(lenses)))
    if not hits:
        print("  걸린 자리 없음")
        return 0
    for name, k in hits.most_common():
        print("  %-22s %5d회   %s" % (name, k,
              ", ".join("%s(%d)" % x for x in where[name].most_common(3))))
        for s in eg[name][:5]:
            print("        ", s)
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
