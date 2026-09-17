# -*- coding: utf-8 -*-
"""내 얘기 같은가 — 그림·장면·내 수를 센다.

    python tools/like_me.py [인원수] [--show <컷id>] [--worst N]

★ 손님이 시킨 것 (2026-09-17)

    "글에 비유가 적어서 공감이 잘 안가, 너무 다 추상적이야
     구체적으로 내 이야기구나 딱 보자마자 소름돋게 만들어야는데
     전체 페이지를"

★ 왜 못 봤나 — 자가 **표지**를 세고 **그림**을 안 셌습니다

  연출 점수의 비유 축(`dramaturgy.FIGURE`)은 「처럼·같이·셈이오」 같은
  **표지**를 셉니다. 그래서 스물여덟 화면이 전부 95~100이었습니다.

  그 표지가 걸린 자리를 뽑아 보니 —

      같이   162번 중 거의 전부가 「함께」 라는 뜻이었습니다
             「여럿이 같이 할 때」 「같은 일에서 같이 막히오」
             「그 짐을 같이 들어 줄 사람을 보겠소」
      셈이    75번 중 상당수가 「…한 셈이 되오」 라는 말버릇입니다

  비유에는 두 쪽이 있습니다 — **표지**(처럼·같소)와 **그림**(무엇처럼).
  자가 왼쪽만 세고 있었으니, 그림 없이 표지만 있는 글도 만점이었습니다.
  자가 없는 자리는 안 보입니다. 이번에는 **오른쪽**을 셉니다.

★ 무엇이 「내 얘기」를 만드는가 — 셋

  ① 그림   표지 + **눈에 보이는 물건**. 「눌러 둔 용수철이 손을 떼면
           튀는 것과 같소」 는 그림이고, 「두 힘이 같이 걸린 것이오」 는
           표지만입니다.
  ② 장면   손님이 **어제 겪은 자리**. 「회의에서 옳은 말을 하고 집에
           와서 후회하오」. `engine/real` 이 이걸 하려고 있습니다.
  ③ 내 수   나이·해·개수. 「상관 2개 · 불 0자 · 36살」. 바넘 문장은
           아무 결과도 금지하지 않아 어떤 관찰에서도 살아남습니다.

  셋 중 하나도 없이 **누구에게나 맞는 꼴**로 끝나면 「누구나」로 셉니다.

★ 옛말 그림도 따로 셉니다

  곳간·가마·나룻배는 그림이기는 하나 손님이 오늘 본 물건이 아닙니다.
  이 집의 말투는 옛말이라 그릇을 통째로 바꿀 수는 없고, 다만 **얼마나
  기울었는지**는 알고 있어야 합니다. 그래서 갈라 셉니다.
"""
from __future__ import annotations

import argparse
import collections
import html as _html
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT / "tools"))

from engine import bank as bank_mod                    # noqa: E402
from engine import dramaturgy as D                     # noqa: E402
from engine import lens as lens_mod                    # noqa: E402
from engine import screenscan as SS                    # noqa: E402
from engine.calendar import build_chart                # noqa: E402
from engine.features import build_features             # noqa: E402
from engine.report import build_report                 # noqa: E402

TODAY = date(2026, 9, 17)
CONCERNS = ("money", "work", "love", "people", "dir", "health")
BIRTHS = [(1993, 11, 25, 15, 55, "M", True),
          (1978, 2, 4, 0, 20, "F", True),
          (2001, 7, 17, 23, 10, "F", True)]

TAG = re.compile(r"<[^>]+>")
SENT = re.compile(r"[^.?!]+[.?!]")
GLOSS = re.compile(r"\([^)]*\)")

# ── 표지와 몸은 **집이 들고** 자는 빌려 씁니다 ───────────────────
#   두 벌을 들면 한쪽만 고쳐집니다. 이 자를 만들면서 얻은 표를
#   `engine/dramaturgy` 로 옮겨 심었고, 여기서는 그걸 가져다 씁니다.
MARK = D.FIGURE
NOW_THING = D.THING_NOW
OLD_THING = D.THING_OLD
LIVE_THING = D.THING_LIVE

# ── 살림의 장면 — 손님이 어제 겪은 자리 ──────────────────────────
#
# ★ 낱말을 넓혔습니다 (2026-09-17)
#
#   처음 적을 때 **일터와 집안**에서만 골랐습니다. 그래서 통장·휴대폰·
#   구독·공고·계산기처럼 손님이 오늘 손에 쥔 물건이 한 칸도 안 셌습니다 —
#   「안 쓰는 구독이 몇 달째 빠져나가고 있을 것이오」 가 장면이 아닌
#   것으로 나왔습니다.
#
#   넓힐 때 지킨 금: **물건·자리·한 일**만 넣습니다. 「자리」 「마음」
#   「때」 같은 말은 안 넣습니다 — 그건 아무 문장에나 붙어서, 넣는
#   순간 자가 제 글에 유리해집니다. 자를 글에 맞추면 그날로 자는
#   거울이 되오.
SCENE = re.compile(
    r"회의|보고|결재|상사|윗사람이|사수|후임|팀장|부장|면접|이력서|"
    r"출근|퇴근|야근|점심시간|회식|술자리|연차|월요일|금요일|주말|"
    r"단톡|단체방|카톡|답장|읽씹|안 읽|읽고도|전화가 오|연락이 끊|"
    r"소개팅|데이트|기념일|생일|명절|제사|시댁|처가|친정|잔소리|"
    r"엄마가|아버지가|부모가|형제|남매|아이가|애가|육아|등원|"
    r"월세|전세|보증금|대출|이자|적금|할부|카드값|생활비|용돈|"
    r"장보|배달|택배|반품|환불|계약서|견적|입금|정산|세금|"
    r"헬스장|운동|다이어트|야식|배탈|감기|병원|약국|건강검진|"
    r"시험|자격증|학원|과제|마감|납기|발표|프로젝트|이직|퇴사|사직서|"
    # 손에 쥔 물건 · 오늘 한 일
    r"통장|잔액|계좌|이체|송금|현금|지갑|영수증|장바구니|구독|결제|계산기|"
    r"휴대폰|알림|메시지|메모|문자|채팅방|공고|지원서|강의|수업|"
    r"밥값|술값|커피값|택시|지하철|버스|주차|"
    r"청소|빨래|설거지|장을 보|냉장고|끼니|아침밥|저녁밥|도시락|"
    r"약속을 미루|약속을 잡|모임|동창|이웃|"
    r"잠이 안 오|잠이 안 온|잠을 설|밤을 새|늦잠|낮잠|산책|걷기|스트레칭")

# ── 내 수 — 대 볼 수 있는 값 ───────────────────────────────────
MINE_NUM = re.compile(
    r"\d+\s*(?:살|세|해|년|개|자|번|명|가지|달|시간|퍼센트|%)|"
    r"(?:하나|둘|셋|넷|다섯|여섯|일곱|여덟|아홉|열|스물|서른|마흔|쉰|예순)"
    r"\s*(?:살|해|개|자|번|명|가지|달)")

# ── 누구에게나 맞는 꼴 ─────────────────────────────────────────
HEDGE = re.compile(
    r"할 때가 있|하기 쉽|한 편이|편이오|하는 수가 있|그런 사람이오|"
    r"경향이|때때로|가끔|자주 그러|대체로|대개|보통은|"
    r"사람이오\.|것이오\.|그렇소\.|나오오\.|드러나오\.|보이오\.")


def sentences(h: str) -> list:
    t = _html.unescape(TAG.sub(" ", (h or "").replace("<br />", " ")))
    t = re.sub(r"\s+", " ", t)
    return [s.strip() for s in SENT.findall(t) if len(s.strip()) > 6]


def look(s: str) -> dict:
    """한 문장을 갈라 본다. 풀이 괄호는 뺍니다 — 사전이지 그림이 아니오."""
    bare = GLOSS.sub("", s)
    mark = bool(MARK.search(bare))
    now = bool(NOW_THING.search(bare))
    old = bool(OLD_THING.search(bare))
    live = bool(LIVE_THING.search(bare))
    body = now or old or live
    return {
        "그림": mark and body,
        "오늘그림": mark and now,
        "옛그림": mark and old and not now,
        "빈표지": mark and not body,
        "장면": bool(SCENE.search(bare)),
        "내수": bool(MINE_NUM.search(bare)),
        "len": len(bare),
    }


class Box:
    """한 자리(컷·화면)에 쌓이는 셈.

    ★ 문장 단위 「누구나」는 자로서 너무 매웠습니다 (2026-09-17).

      「없는 쇠를 일에서 메우느라 같은 일을 남보다 오래 붙들었소.
       느린 것이 아니라 없는 것으로 한 것이오.」

      뒤 문장만 떼면 아무것도 안 가리킵니다. 그런데 그건 앞 문장을
      받아 **맺는** 자리라 원래 그렇게 생겼습니다. 그것까지 고장이라
      부르면 자가 늘 붉습니다.

      그래서 **컷 단위**도 같이 셉니다 — 이 컷을 한 장 읽는 동안
      그림도 장면도 수도 **하나도** 못 만나는가. 그게 손님이 겪는
      단위입니다.
    """

    def __init__(self):
        self.n = 0
        self.chars = 0
        self.c = collections.Counter()
        self.flat = []          # 셋 다 없는 문장
        self.insts = 0          # 이 자리가 그려진 횟수
        self.blank = 0          # 그중 셋 다 하나도 없던 횟수

    def page(self, html: str):
        """컷 한 장을 통째로 본다."""
        self.insts += 1
        hit = False
        for s in sentences(html):
            v = look(s)
            if v["그림"] or v["장면"] or v["내수"]:
                hit = True
            self.add(s)
        if not hit:
            self.blank += 1

    def add(self, s: str):
        v = look(s)
        self.n += 1
        self.chars += v["len"]
        for k in ("그림", "오늘그림", "옛그림", "빈표지", "장면", "내수"):
            if v[k]:
                self.c[k] += 1
        if not (v["그림"] or v["장면"] or v["내수"]):
            self.c["누구나"] += 1
            if HEDGE.search(s):
                self.flat.append(s)

    def per_k(self, k: str) -> float:
        return 1000.0 * self.c[k] / max(1, self.chars)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("n", nargs="?", type=int, default=2)
    ap.add_argument("--show", default="")
    ap.add_argument("--worst", type=int, default=0)
    a = ap.parse_args()

    lenses = [l["id"] for l in lens_mod.released()]
    boxes: dict = collections.defaultdict(Box)

    for b in BIRTHS[:a.n]:
        y, m, d, h, mi, sex, known = b
        f = build_features(build_chart(y, m, d, h, mi, sex, known, "서울"),
                           as_of=TODAY)
        for concern in CONCERNS:
            segs = bank_mod.build_hook(f, concern, "INTJ", "", "그대")
            boxes["훅 5단"].page(SS.hook_html(segs))
            for lid in lenses:
                for c in build_report(f, "e", lid, "free", concern,
                                      "INTJ")["cuts"]:
                    boxes[c["id"]].page(c["html"])
    for sid, txt in ((k, v[0]) for k, v in SS._screens().items()):
        if sid in SS.KO:
            boxes["화면 " + sid].page(txt)

    if a.show:
        bx = boxes.get(a.show)
        if not bx:
            print("그런 자리가 없소: %s" % a.show)
            return 1
        print("[%s] 누구에게나 맞는 꼴 %d줄" % (a.show, len(bx.flat)))
        for s in bx.flat[:40]:
            print("   ", s[:90])
        return 0

    print("=" * 84)
    print("  내 얘기 같은가 — 1천자당 그림·장면·내 수 · 맨컷 = 셋 다 없는 장")
    print("=" * 84)
    print("  %-16s %6s %6s %6s %6s %6s %6s  %5s"
          % ("자리", "문장", "그림", "오늘", "옛", "장면", "내수", "맨컷"))
    print("  " + "-" * 80)
    rows = sorted(boxes.items(),
                  key=lambda kv: kv[1].per_k("그림") + kv[1].per_k("장면")
                  + kv[1].per_k("내수"))
    tot = Box()
    for name, bx in rows:
        tot.n += bx.n
        tot.chars += bx.chars
        tot.insts += bx.insts
        tot.blank += bx.blank
        tot.c.update(bx.c)
        print("  %-16s %6d %6.1f %6.1f %6.1f %6.1f %6.1f  %4.0f%%"
              % (name[:16], bx.n, bx.per_k("그림"), bx.per_k("오늘그림"),
                 bx.per_k("옛그림"), bx.per_k("장면"), bx.per_k("내수"),
                 100.0 * bx.blank / max(1, bx.insts)))
    print("  " + "-" * 80)
    print("  %-16s %6d %6.1f %6.1f %6.1f %6.1f %6.1f  %4.0f%%"
          % ("합", tot.n, tot.per_k("그림"), tot.per_k("오늘그림"),
             tot.per_k("옛그림"), tot.per_k("장면"), tot.per_k("내수"),
             100.0 * tot.blank / max(1, tot.insts)))
    print()
    print("  표지만 있고 그림이 없는 문장: %d개 (표지 %d개 중 %.0f%%)"
          % (tot.c["빈표지"], tot.c["빈표지"] + tot.c["그림"],
             100.0 * tot.c["빈표지"] / max(1, tot.c["빈표지"] + tot.c["그림"])))
    print("  옛 물건으로 그린 그림: %d개 (그림 %d개 중 %.0f%%)"
          % (tot.c["옛그림"], tot.c["그림"],
             100.0 * tot.c["옛그림"] / max(1, tot.c["그림"])))

    if a.worst:
        print()
        print("  누구에게나 맞는 꼴 — 많이 나오는 자리")
        cnt = collections.Counter()
        where = {}
        for name, bx in boxes.items():
            for s in bx.flat:
                k = re.sub(r"\d+", "N", GLOSS.sub("", s)).strip()
                cnt[k] += 1
                where.setdefault(k, name)
        for k, v in cnt.most_common(a.worst):
            print("  %4d회 [%-14s] %s" % (v, where[k][:14], k[:56]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
