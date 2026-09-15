"""
1만 명이 들어와 어디서 나가는가 — 아홉 축으로 재고, 그 축으로 떨군다.

    python tools/dropout_sim.py [인원수] [--json 파일]

★ 이 도구는 두 가지를 절대 섞지 않습니다 (conversion_sim.py 와 같은 규칙)

    [센 것]     화면과 글의 아홉 축 점수. 엔진과 화면 글을 **실제로 돌려서**
                냅니다. 한 사람 한 사람 자기 훅과 자기 무료 리포트를 받고,
                그 글을 `engine/dramaturgy` 가 그 자리에서 잽니다.
                시각 미상 · 유파 갈림 · 잠긴 컷 · 목패 값도 센 것입니다.

    [가정한 것]  그 점수가 **사람을 얼마나 붙잡는가.** 우리는 이걸 모릅니다.
                실측은 `/v1/funnel` 에 기록이 쌓여야 나옵니다.

  그래서 이 도구의 산출물은 **전환율이 아니라 차례**입니다 —
  어느 화면의 어느 축을 고치면 몇 명이 더 남는가. 가정을 비관·기준·낙관
  세 벌로 돌리고, 세 벌에서 **차례가 안 바뀌는 것**만 「먼저 고칠 것」
  으로 냅니다. 가정이 흔들어도 안 바뀌는 것이 진짜입니다.

★ 화면 차례를 손으로 안 적습니다

  `tools/give_take.py` 는 차례를 파일에 박아 두었는데(FUNNEL) 화면 코드가
  바뀌어 있었습니다 — 자가 옛 순서를 재고 있었습니다. 여기서는
  `apps/web/app/page.tsx` 의 `go("...")` 를 따라 걸어서 **살아 있는 길**을
  찾습니다. 길이 바뀌면 이 도구도 따라 바뀝니다.

★ 아홉 축 — 손님이 말한 그대로

    사주정확도  시주가 섰는가 · 다른 만세력과 갈리는가 · 근거에 수가 있는가
    후킹        당김(pull)   콜드 오픈 · 액트아웃 · 이름으로 예고
    몰입도      빚(내주기와 돌려받기) · 고리
    헷갈리지 않음 쉬움(plain) · 풀이 없는 어려운 말
    명확성      명확(clear)
    감동        울림(heart)
    위로        위로 자리가 실제로 걸렸는가 (engine/heart)
    간결함      한 화면 읽는 시간(secs) · 숨 쉴 자리(pace)
    팩폭        팩폭(bite)  반증 가능한 말 · 산 말 · 안 물러섬
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import random
import re
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "services" / "api") not in sys.path:
    sys.path.insert(0, str(ROOT / "services" / "api"))
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import payments                                        # noqa: E402
from engine import bank as bank_mod                    # noqa: E402
from engine import calendar as cal                     # noqa: E402
from engine import dramaturgy as D                     # noqa: E402
from engine import lens as lens_mod                    # noqa: E402
from engine import relay as relay_mod                  # noqa: E402
from engine import screenscan as S                     # noqa: E402
from engine import terms as terms_mod                  # noqa: E402
from engine.calendar import build_chart                # noqa: E402
from engine.features import build_features             # noqa: E402
from engine.report import build_report                 # noqa: E402

import give_take as GT                                 # noqa: E402
from journey_sim import people as sample_people        # noqa: E402

TODAY = date(2026, 9, 10)
SEED = 20260910
ENTRY_LENS = "pungun"

TAG = re.compile(r"<[^>]+>")


# ══════════════════════════════════════════════════════════
# [센 것] · 살아 있는 길 — 화면 코드를 걸어서 찾는다
# ══════════════════════════════════════════════════════════
STEP_BLOCK = re.compile(r'step === "([a-z0-9]+)"')
GO = re.compile(r'go\("([a-z0-9]+)"\)')
# 주 단추. `onClick` 안이 중괄호로 겹쳐 있어(`{ s.set({…}); go("a5"); }`)
# 괄호를 맞춰 잘라 내려 들면 빗나갑니다. 단추 표시 뒤 300자 안의 첫 `go()`
# 를 그 단추의 목적지로 봅니다.
PRIMARY = re.compile(r'className="btn mt"')


def live_path() -> list:
    """`/` 의 진입 흐름에서 **주 단추만 눌러 갔을 때** 지나는 화면.

    곁문(별칭·성향 넉 자)은 주 단추가 아니라 유령 단추(`btn gh`)라
    본길이 아닙니다. 본길만 셉니다 — 대부분의 손님이 지나는 자리입니다.
    """
    src = (S.WEB / "app" / "page.tsx").read_text(encoding="utf-8")
    marks = [(m.group(1), m.start()) for m in STEP_BLOCK.finditer(src)]
    marks.append(("__end__", len(src)))
    nxt = {}
    for i in range(len(marks) - 1):
        sid, a = marks[i]
        chunk = src[a:marks[i + 1][1]]
        for m in PRIMARY.finditer(chunk):
            g = GO.search(chunk, m.end(), m.end() + 300)
            if g:
                nxt.setdefault(sid, g.group(1))
                break
    # a1 은 `if (step === "a1")` 블록 앞에 주 단추가 없을 수 있어 따로 봅니다.
    path, cur, seen = [], "a1", set()
    while cur and cur not in seen:
        seen.add(cur)
        path.append(cur)
        cur = nxt.get(cur)
    return path


# 훅 뒤는 주소가 갈립니다 — `/pay?step=d0` 로 넘어갑니다.
PAY_PATH = ["d0", "d1", "d2", "d3"]

# 화면 종류마다 읽는 시간의 기준. 넘으면 「간결함」 이 값을 냅니다.
SECS_OK = {"input": 25, "read": 150, "list": 60, "beat": 40}


# ══════════════════════════════════════════════════════════
# [센 것] · 화면 글 아홉 축
# ══════════════════════════════════════════════════════════
def screen_scores() -> dict:
    """화면이 제 손으로 든 글의 점수 — 관리자 화면과 같은 자로."""
    S._screens.cache_clear()
    return {r["id"]: r for r in S.scan_all()}


def give_take_rows() -> dict:
    """화면마다 (내줌 칸, 돌려줌, 고리). give_take 의 셈을 그대로 씁니다."""
    S._screens.cache_clear()
    text, raw = GT.screens_src(), GT.raw_chunks()
    out = {}
    for sid in set(list(text) + list(raw)):
        chunk = raw.get(sid, "")
        out[sid] = {
            "ask": len(GT.FIELD.findall(chunk)) + len(GT.PICKS.findall(chunk)),
            "back": len(GT.gives(chunk)),
            "loop": GT.loops(text.get(sid, "")),
        }
    return out


def unglossed(html: str) -> int:
    """풀이 **없이** 나온 어려운 말이 몇 번인가 — 그 자리에서.

    ★ 처음에는 풀이 상자를 지우고 낱말을 셌습니다. 그런데 이 집의 풀이는
      낱말을 지우는 게 아니라 **뒤에 괄호를 답니다** — 「대운(십 년마다
      판이 바뀌는 것)」. 그러니 상자를 지워도 낱말은 그대로 남고, 자는
      풀어 준 말까지 「안 풀렸다」 고 셌습니다. 고치고 나서도 수가 안
      줄어 그제야 자가 틀린 걸 알았습니다.

      `engine/dramaturgy` 의 쉬움 축과 **같은 셈**을 씁니다. 도구가 따로
      재면 「도구는 붉은데 화면은 통과」 인 자리가 생깁니다.
    """
    text = D.plain(html or "")
    n = 0
    for w in D.HARD:
        n += (len(D.HARD_AT[w].findall(text))
              - len(D.HARD_GLOSSED[w].findall(text)))
    return max(0, n)


# ══════════════════════════════════════════════════════════
# [센 것] · 한 사람이 실제로 받는 글
# ══════════════════════════════════════════════════════════
def compose_seg(segs, i) -> str:
    """훅 한 마디를 **화면이 그리는 대로** 이어 붙인다.

    ★ 처음에는 `seg["html"]` 만 재고 「근거 줄이 없소」 「다음을 이름으로
      안 부르오」 가 100% 라고 냈습니다. 둘 다 거짓이었습니다 — 근거는
      `seg["source"]` 라는 딴 칸에 있고, 다음 마디 이름은 화면이
      `HookSegments` 에서 붙입니다. 자가 화면과 다른 것을 보고 있었소.

      화면이 그리는 차례 그대로 잇습니다 (apps/web/components/HookSegments.tsx) —
      이름표 · 근거(0단만 아래) · 본문 · 다음 마디 이름 · 물음.
    """
    s = segs[i]
    out = []
    if s.get("label"):
        out.append('<div class="lab">%s</div>' % s["label"])
    if s.get("source") and not s.get("source_below"):
        out.append('<span class="src">근거 · %s</span>' % s["source"])
    out.append(s["html"])
    if s.get("source") and s.get("source_below"):
        out.append('<span class="src below">근거 · %s</span>' % s["source"])
    if i < len(segs) - 1:
        out.append('<p>다음 마디 · 「%s」.</p>'
                   % (segs[i + 1].get("label") or "그 선택 뒤의 다른 면"))
    if s.get("question"):
        out.append('<p>%s</p>' % s["question"])
    return chr(10).join(out)



def measure_one(p, cache):
    """한 사람을 엔진에 통과시켜 **그 사람 몫의 아홉 축**을 잰다."""
    out = {"ok": True}
    try:
        ch = build_chart(p["year"], p["month"], p["day"], p["hour"],
                         p["minute"], p["sex"], p["hour_known"], p["city"])
        f = build_features(ch, as_of=TODAY)
    except Exception as e:
        return {"ok": False, "why": type(e).__name__}

    out["hour_known"] = p["hour_known"]
    out["pillars"] = len(f.pillars)

    # ── 다른 만세력과 갈리는가 (유파 선택 · CLAUDE.md 알려진 이슈 9)
    #
    # ★ 상수를 흔들지 않습니다. `build_chart` 가 유파를 인자로 받습니다 —
    #   전역을 바꾸면 같은 프로세스의 다른 셈까지 물듭니다. 그리고
    #   갈래 이름을 틀리면(「정자시」 는 이 집의 갈래가 아닙니다) 아무것도
    #   안 갈리는데 「0% 갈림」 이라는 답이 나옵니다 — 자가 조용히 거짓말합니다.
    #   `Chart.pillars` 는 `Pillar` 이고 `Features.pillars` 는 사전입니다.
    #   여기서 `alt["pillars"]` 라 적었더니 `except` 가 그 오류를 삼켜
    #   **갈림률이 늘 0%** 로 나왔습니다. 안 갈리는 게 아니라 안 세고
    #   있었습니다. 무르게 잡은 `except` 는 자를 조용히 거짓말시킵니다.
    ours = "".join(x["gz"] for x in f.pillars)
    alt = build_chart(p["year"], p["month"], p["day"], p["hour"],
                      p["minute"], p["sex"], p["hour_known"], p["city"],
                      zi_policy="야자시", jieqi_basis="standard")
    out["diverges"] = (ours != "".join(x.gz for x in alt.pillars))

    # ── 훅 다섯 마디. 두 번 어긋나면 2단이 축을 바꿉니다 (bank.TURN_AT)
    rng = p["rng"]
    segs = bank_mod.build_hook(f, p["concern"], p["axis4"], "", "그대")
    marks, misses, yes, dunno = [], 0, 0, 0
    for i, seg in enumerate(segs):
        html = compose_seg(segs, i)
        g = D.score("a7", "훅", html, "read")
        g["unglossed"] = unglossed(html)
        marks.append(g)
        # [가정한 것] 손님의 대답. 셀 수 있는 말이 많을수록 반응이 뚜렷하고,
        # 어려운 말이 많을수록 「잘 모르겠습니다」 로 갑니다.
        p_dunno = 0.10 + 0.30 * (1 - g["plain"] / 100.0) \
            + 0.02 * min(5, g["unglossed"])
        p_yes = (0.30 + 0.35 * (g["bite"] / 100.0)) * (1 - p_dunno)
        r = rng.random()
        if r < p_dunno:
            dunno += 1
        elif r < p_dunno + p_yes:
            yes += 1
        else:
            misses += 1
            if misses == bank_mod.TURN_AT and i + 1 < len(segs):
                try:
                    segs = bank_mod.build_hook(f, p["concern"], p["axis4"],
                                               "", "그대", misses=misses)
                except Exception:
                    pass
    out["hook"] = marks
    out["hook_yes"], out["hook_miss"], out["hook_dunno"] = yes, misses, dunno

    # ── 무료 리포트
    free = build_report(f, "sim", ENTRY_LENS, "free", p["concern"], p["axis4"])
    fh = "".join(c["html"] for c in free["cuts"])
    g = D.score("d0", "무료", fh, "read")
    g["unglossed"] = unglossed(fh)
    out["free"] = g
    out["locked"] = len(free.get("locked") or [])
    ids = {c["id"] for c in free["cuts"]}
    out["solace"] = ("solace" in ids or "hope" in ids)

    # ── 진열대에 뜨는 값 (목패 값이 곧 청구가 · payments.price_of)
    rec = relay_mod.recommend(f, read=[ENTRY_LENS], skipped=[],
                              session_relay_count=0, last_lens=ENTRY_LENS)
    items = rec.get("recommend") or []
    out["relay_empty"] = not items
    if items:
        lid = items[0]["lens_id"]
        # 1순위가 무료 캐릭터일 수 있습니다 — 무거운 리포트 뒤 안전망.
        # 그때는 값이 0 이라 `price_of` 가 거절합니다.
        try:
            price = int(items[0].get("price") or payments.price_of("one", lid))
        except Exception:
            price = 0
        out["price"] = price
        out["needs_input"] = bool(lens_mod.required_input(lid))
    else:
        out["price"], out["needs_input"] = 9900, False
    return out


# ══════════════════════════════════════════════════════════
# [가정한 것] · 사람이 나가는 셈
# ══════════════════════════════════════════════════════════
#
# 축마다 무게를 하나씩 답니다. 이 수는 **잰 것이 아닙니다.** 실측이
# 쌓이면 여기를 갈아 끼웁니다. 그래서 답을 하나로 안 내고 세 벌로 돌립니다.
W = {
    "후킹": 0.55,
    "팩폭": 0.42,
    "감동": 0.34,
    "위로": 0.26,
    "명확성": 0.40,
    "헷갈림": 0.52,
    "간결함": 0.34,
    "몰입(빚)": 0.50,     # 안 돌려준 칸 (셋이면 다 찬 것)
    "사주정확도": 0.55,
    "값": 0.85,
}
# 종류마다 바탕 이탈 — 글과 상관없이 나가는 몫 (딴 일 · 오폭 · 변심)
BASE = {"input": 0.050, "read": 0.040, "list": 0.070, "beat": 0.030}
CASES = (("비관 가정", 1.35), ("기준 가정", 1.00), ("낙관 가정", 0.72))


def traits(rng):
    """[가정한 것] 사람마다 다른 것 넷. 같은 화면도 사람마다 다르게 아픕니다."""
    return {
        "hurry": rng.betavariate(2, 2),    # 급함 — 길이가 아프다
        "lit": rng.betavariate(1.6, 3),    # 명리 문해 — 높으면 어려운 말이 안 아프다
        "doubt": rng.betavariate(2, 2),    # 의심 — 근거가 없으면 아프다
        "ache": rng.betavariate(2, 2),     # 아픔 — 위로·울림이 없으면 아프다
        "purse": rng.betavariate(2, 3),    # 지갑
    }


# 글의 축은 **합이 아니라 가중 평균**으로 봅니다.
#
#   축 여섯을 그냥 더하면 화면 하나가 1.2 를 넘어 첫 화면에서 전원이
#   나갑니다. 그건 모형이 아니라 고장입니다. 사람은 모자란 축을 하나씩
#   세어 나가는 게 아니라 **전체 인상**으로 한 번 판단합니다.
#
#   그래서 축을 **한 화폐로** 재고 평균을 냅니다. 값과 바탕 이탈만
#   밖에 둡니다 — 그건 글의 축이 아니라 목패에 적힌 수와 딴 일입니다.
KAPPA = 0.62


def cost_terms(g, kind, ask, back, loop, tr, gaps=None, flat=None, scale=1.0):
    """이 화면에서 이 사람이 지는 짐 — 축마다 따로.

    ★ 축은 **한 화폐로** 재야 견줄 수 있습니다.

      처음에는 글의 축만 평균을 내고 「안 돌려준 칸」 은 그대로 더했습니다.
      그랬더니 귀속이 통째로 그 축으로 쏠렸습니다 — 평균 낸 축은 셋으로
      나뉘고 안 나눈 축은 그대로였으니, 자가 큰 쪽이 늘 이깁니다.
      축을 견주려면 같은 자로 재야 합니다.
    """
    raw = {}
    raw["후킹"] = W["후킹"] * (1 - g["pull"] / 100.0) * (0.6 + 0.8 * tr["hurry"])
    raw["팩폭"] = W["팩폭"] * (1 - g["bite"] / 100.0) * (0.6 + 0.9 * tr["doubt"])
    raw["감동"] = W["감동"] * (1 - g["heart"] / 100.0) * (0.5 + 1.0 * tr["ache"])
    raw["명확성"] = W["명확성"] * (1 - g["clear"] / 100.0)
    hard = (1 - g["plain"] / 100.0) * 0.6 + (1 - g["figure"] / 100.0) * 0.4
    raw["헷갈림"] = W["헷갈림"] * hard * (1.4 - 0.9 * tr["lit"])
    # * 길이는 죄가 아닙니다 (2026-09-10).
    #
    #   처음에는 읽는 시간(secs)이 기준을 넘으면 벌을 줬습니다. 그랬더니
    #   진입 화면에 좋은 글을 넣을수록 점수가 깎여 「간결함」이 두 번째
    #   이탈 사유로 올라왔습니다. 그런데 engine/dramaturgy 는 **읽는
    #   시간을 점수에 안 씁니다** - 화면에 적어 주기만 합니다. 집의 자가
    #   일부러 안 재는 것을 도구가 혼자 재고 있었습니다.
    #
    #   집이 재는 것은 **한 번에 얼마나 쏟는가**(pace - 한 상자가 화면을
    #   넘는가 · 안 끊고 몇 초를 이어 가는가)입니다. 같은 900자라도 한
    #   덩이로 쏟으면 훑고, 끊어 놓으면 읽습니다. 그쪽만 셉니다.
    raw["간결함"] = W["간결함"] * (1 - g["pace"] / 100.0) \
        * (0.6 + 0.8 * tr["hurry"])
    # 안 돌려준 칸. 셋이면 다 찬 것으로 봅니다 — 넷째 칸이 더 아프지는
    # 않습니다. 이미 서식을 채우는 일이 되어 있습니다.
    debt = max(0, ask - back - loop)
    raw["몰입(빚)"] = W["몰입(빚)"] * min(1.0, debt / 3.0)
    for k, v in (gaps or {}).items():
        raw[k] = raw.get(k, 0.0) + W[k] * v

    norm = KAPPA / sum(W[k] for k in raw)
    t = {k: v * norm for k, v in raw.items()}
    t["바탕"] = BASE.get(kind, 0.05)
    for k, v in (flat or {}).items():
        t[k] = t.get(k, 0.0) + v
    return {k: v * scale for k, v in t.items()}


def walk(m, tr, rng, scale, screens, gt, path):
    """한 사람이 어디까지 갔는가. 나간 자리와 **무엇 때문에** 나갔는지."""
    for sid in path:
        g = dict(screens[sid])
        kind = S.KIND.get(sid, "read")
        row = gt.get(sid, {"ask": 0, "back": 0, "loop": 0})
        gaps, flat = {}, {}

        # ── 화면마다 그 사람 몫으로 갈아 끼우는 자리
        if sid == "a6":
            # 명식이 서는 자리. 시주가 빠지면 여덟 글자가 여섯이 됩니다.
            if not m["hour_known"]:
                gaps["사주정확도"] = 0.55
            if m["diverges"]:
                gaps["사주정확도"] = gaps.get("사주정확도", 0.0) + 0.30
        if sid == "a7":
            for i, seg in enumerate(m["hook"]):
                sg = dict(seg)
                gp = {}
                if sg.get("unglossed"):
                    gp["헷갈림"] = 0.05 * min(6, sg["unglossed"]) \
                        * (1.4 - 0.9 * tr["lit"])
                t = cost_terms(sg, "read", 0, 0, 0, tr, gp, None, scale)
                if rng.random() < 1 - math.exp(-sum(t.values())):
                    return ("a7·%d마디" % (i + 1), max(t, key=t.get))
            continue
        if sid == "d0":
            g = dict(m["free"])
            if m["free"].get("unglossed"):
                gaps["헷갈림"] = 0.03 * min(10, m["free"]["unglossed"]) \
                    * (1.4 - 0.9 * tr["lit"])
            if not m["solace"]:
                gaps["위로"] = 0.4 + 1.0 * tr["ache"]
            # 무료에서 잠긴 컷이 스물 넘게 보입니다 — 고리이기도 하고 벽이기도.
            flat["값"] = W["값"] * 0.012 * max(0, m["locked"] - 8)
        if sid == "d1":
            if m["relay_empty"]:
                return ("d1 진열대", "막다른 화면")
            price = m["price"] or 9900
            # [가정한 것] 지갑에 견준 값. 훅에서 맞은 자리가 많을수록 덜 아픕니다.
            hit = (m["hook_yes"] / 5.0)
            flat["값"] = W["값"] * (price / 9900.0) * (1.35 - tr["purse"]) \
                * (1.15 - 0.55 * hit)
            if m["needs_input"]:
                gaps["몰입(빚)"] = 1.0

        t = cost_terms(g, kind, row["ask"], row["back"], row["loop"],
                       tr, gaps, flat, scale)
        if rng.random() < 1 - math.exp(-sum(t.values())):
            return (sid, max(t, key=t.get))
    return (None, None)


# ══════════════════════════════════════════════════════════
# 돌리기
# ══════════════════════════════════════════════════════════
def run(measured, path, screens, gt, scale, seed, patch=None):
    """같은 난수로 돌립니다 — 고친 것 하나만 달라지도록."""
    if patch:
        sid, axis, val = patch
        screens = dict(screens)
        if sid in screens:
            screens[sid] = dict(screens[sid])
            screens[sid][axis] = val
    left = collections.Counter()
    why = collections.Counter()
    paid = reach = 0
    for m, tr, draw in measured:
        rng = random.Random(draw)
        if patch and patch[0] == "a7":
            m = dict(m)
            m["hook"] = [dict(s, **{patch[1]: patch[2]}) for s in m["hook"]]
        if patch and patch[0] == "d0":
            m = dict(m)
            m["free"] = dict(m["free"], **{patch[1]: patch[2]})
        sid, axis = walk(m, tr, rng, scale, screens, gt, path)
        if sid is None:
            paid += 1
            reach += 1
        else:
            left[sid] += 1
            why[(sid, axis)] += 1
            # 목패까지 갔는가. 앞쪽 화면을 고친 값은 결제 수로는 거의
            # 안 보입니다 — 뒤에서 또 떨어지니까요. 그래서 **도달**도 셉니다.
            if sid.startswith("d"):
                reach += 1
    return paid, left, why, reach


def bar(pct, width=20):
    n = int(round(pct / 100.0 * width))
    return "█" * n + "·" * (width - n)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("n", nargs="?", type=int, default=10000)
    ap.add_argument("--json", default="")
    ap.add_argument("--fixes", type=int, default=14)
    a = ap.parse_args()
    n = a.n

    t0 = time.perf_counter()
    entry = live_path()
    path = entry + PAY_PATH
    screens = screen_scores()
    gt = give_take_rows()

    missing = [s for s in path if s not in screens]
    if missing:
        print("화면 글을 못 찾은 자리: %s" % ", ".join(missing))
        path = [s for s in path if s in screens]

    print("=" * 76)
    print("  1만 명이 어디서 나가는가 — 아홉 축으로 재고, 그 축으로 떨군다")
    print("=" * 76)
    print()
    print("  살아 있는 길 (page.tsx 의 주 단추를 따라 걸은 것)")
    print("    %s" % " → ".join("%s %s" % (s, S.KO.get(s, "?")) for s in path))
    print()

    # ── [센 것] 한 사람씩 엔진에 통과
    pop = sample_people(n, seed=SEED)
    measured, blew = [], collections.Counter()
    for i, p in enumerate(pop):
        m = measure_one(p, None)
        if not m["ok"]:
            blew[m["why"]] += 1
            continue
        tr = traits(p["rng"])
        measured.append((m, tr, SEED * 31 + i))
        if (i + 1) % 1000 == 0:
            print("    … %d/%d  (%.0f초)" % (i + 1, n, time.perf_counter() - t0),
                  flush=True)
    print()

    # ── [센 것] 화면 아홉 축
    print("-" * 76)
    print("  [센 것] 화면마다 아홉 축 — 이 길 위의 화면만")
    print("-" * 76)
    print("  %-4s %-9s %4s %4s %4s %4s %4s %4s %4s %4s %5s %4s"
          % ("화면", "이름", "후킹", "팩폭", "감동", "명확", "쉬움", "비유",
             "속도", "강조", "읽초", "내줌"))
    for sid in path:
        g = screens[sid]
        row = gt.get(sid, {"ask": 0, "back": 0, "loop": 0})
        note = ""
        if row["ask"] and not row["back"] and not row["loop"]:
            note = "  ← 받기만 하오"
        print("  %-4s %-9s %4d %4d %4d %4d %4d %4d %4d %4d %5d %4d%s"
              % (sid, S.KO.get(sid, "?")[:9], g["pull"], g["bite"], g["heart"],
                 g["clear"], g["plain"], g["figure"], g["pace"], g["mark"],
                 g["secs"], row["ask"], note))
    print()

    # ── [센 것] 화면이 스스로 짚은 모자란 것
    print("-" * 76)
    print("  [센 것] 그 화면이 스스로 짚은 모자란 것 — 고칠 자리는 이미 적혀 있소")
    print("-" * 76)
    for sid in path:
        miss = screens[sid].get("missing") or []
        if not miss:
            continue
        print("  %s %s" % (sid, S.KO.get(sid, "?")))
        for x in miss:
            print("      · %s" % x)
    print()

    # ── [센 것] 한 사람 몫 글
    hk = [sum(s["bite"] for s in m["hook"]) / len(m["hook"])
          for m, _, _ in measured]
    hp = [sum(s["plain"] for s in m["hook"]) / len(m["hook"])
          for m, _, _ in measured]
    fr = [m["free"] for m, _, _ in measured]
    print("-" * 76)
    print("  [센 것] 사람마다 받는 글 — 표본 %d명" % len(measured))
    print("-" * 76)
    print("    훅 다섯 마디   팩폭 %.0f · 쉬움 %.0f"
          % (sum(hk) / len(hk), sum(hp) / len(hp)))
    print("    무료 리포트    당김 %.0f · 팩폭 %.0f · 울림 %.0f · 명확 %.0f "
          "· 쉬움 %.0f · 읽는 시간 %.0f초"
          % tuple(sum(x[k] for x in fr) / len(fr)
                  for k in ("pull", "bite", "heart", "clear", "plain", "secs")))
    print("    풀이 없이 나온 어려운 말   훅 %.1f회 · 무료 %.1f회"
          % (sum(sum(s["unglossed"] for s in m["hook"])
                 for m, _, _ in measured) / len(measured),
             sum(m["free"]["unglossed"] for m, _, _ in measured) / len(measured)))
    print("    무료에서 보이는 잠긴 컷    평균 %.1f개 (최다 %d)"
          % (sum(m["locked"] for m, _, _ in measured) / len(measured),
             max(m["locked"] for m, _, _ in measured)))
    print("    시각 미상 %.1f%% · 다른 만세력과 갈릴 자리 %.1f%% "
          "· 위로 자리가 안 걸린 사람 %.1f%%"
          % (100.0 * sum(1 for m, _, _ in measured if not m["hour_known"]) / len(measured),
             100.0 * sum(1 for m, _, _ in measured if m["diverges"]) / len(measured),
             100.0 * sum(1 for m, _, _ in measured if not m["solace"]) / len(measured)))
    if blew:
        print("    엔진이 터진 사람   %s" % dict(blew))
    print()

    # ── [가정한 것] 퍼널
    results = {}
    for name, scale in CASES:
        results[name] = run(measured, path, screens, gt, scale, SEED)

    print("-" * 76)
    print("  [센 것 + 가정한 것] 퍼널 — %d명이 들어왔을 때" % len(measured))
    print("-" * 76)
    print("  %-11s %s" % ("", "  ".join("%-11s" % c[0] for c in CASES)))
    order = []
    for sid in path:
        if sid == "a7":
            order += ["a7·%d마디" % (i + 1) for i in range(5)]
        else:
            order.append(sid)
    alive = {c[0]: len(measured) for c in CASES}
    for sid in order:
        cells = []
        for name, _ in CASES:
            _, left, _, _ = results[name]
            alive[name] -= left[sid]
            cells.append("%5d 남음 (-%d)" % (alive[name], left[sid]))
        label = sid if sid.startswith("a7") else \
            "%s %s" % (sid, S.KO.get(sid, "?"))
        print("  %-13s %s" % (label[:13], "  ".join("%-16s" % c for c in cells)))
    print()
    for name, _ in CASES:
        paid, _, _, _ = results[name]
        print("  %-11s 값을 치른 사람 %d명 (%.2f%%)"
              % (name, paid, 100.0 * paid / len(measured)))
    print()

    # ── 이탈 귀속
    print("-" * 76)
    print("  이탈 귀속 — 어느 화면의 어느 축이 사람을 세웠는가 (기준 가정)")
    print("-" * 76)
    _, left, why, _ = results["기준 가정"]
    tot = sum(why.values())
    print("  %-14s %-11s %7s %6s" % ("화면", "축", "사람", "몫"))
    for (sid, axis), c in why.most_common(18):
        print("  %-14s %-11s %7d %5.1f%%  %s"
              % (sid[:14], axis, c, 100.0 * c / tot, bar(100.0 * c / tot, 16)))
    print()
    byaxis = collections.Counter()
    for (sid, axis), c in why.items():
        byaxis[axis] += c
    print("  축만 모으면")
    for axis, c in byaxis.most_common():
        print("    %-11s %6d  %5.1f%%  %s"
              % (axis, c, 100.0 * c / tot, bar(100.0 * c / tot, 22)))
    print()

    # ── 고칠 차례 — 반사실
    print("-" * 76)
    print("  고칠 차례 — 그 화면의 그 축을 **85점으로** 올리면 몇 명이 더 남는가")
    print("  (같은 난수로 다시 돌립니다. 고친 것 하나만 달라집니다)")
    print("-" * 76)
    AXES = ("pull", "bite", "heart", "clear", "plain", "figure", "pace", "mark")
    KOAX = {"pull": "후킹", "bite": "팩폭", "heart": "감동·울림",
            "clear": "명확성", "plain": "쉬움", "figure": "비유",
            "pace": "숨 쉴 자리", "mark": "강조"}
    def now_at(sid, ax):
        """지금 몇 점인가. 훅과 무료는 **사람마다 달라서** 표본 평균으로."""
        if sid == "a7":
            return sum(sum(s[ax] for s in m["hook"]) / len(m["hook"])
                       for m, _, _ in measured) / len(measured)
        if sid == "d0":
            return sum(m["free"][ax] for m, _, _ in measured) / len(measured)
        return screens[sid][ax]

    cand = []
    for sid in path:
        for ax in AXES:
            cur = now_at(sid, ax)
            if cur >= 85:
                continue
            cand.append((sid, ax, cur))
    rows = []
    base = {name: (results[name][0], results[name][3]) for name, _ in CASES}
    for sid, ax, cur in cand:
        gains, reach = {}, {}
        for name, scale in CASES:
            paid, _, _, rc = run(measured, path, screens, gt, scale, SEED,
                                 patch=(sid, ax, 85))
            gains[name] = paid - base[name][0]
            reach[name] = rc - base[name][1]
        rows.append((sid, ax, cur, gains, reach))
    # 목패까지 데려온 사람 수로 줄을 세웁니다. 결제 수는 뒤 화면이
    # 또 떨어뜨려 앞쪽 고침의 값이 안 보입니다.
    rows.sort(key=lambda r: -r[4]["기준 가정"])

    print("  %-4s %-9s %-11s %5s %-22s %s"
          % ("화면", "이름", "축", "지금", "목패까지 더 온 사람", "값 치른 사람"))
    print("  %-4s %-9s %-11s %5s %s  %s"
          % ("", "", "", "",
             "  ".join("%-6s" % c[0][:2] for c in CASES),
             "  ".join("%-6s" % c[0][:2] for c in CASES)))
    for sid, ax, cur, gains, reach in rows[:a.fixes]:
        r = "  ".join("%-6s" % ("+%d" % reach[c[0]]) for c in CASES)
        g = "  ".join("%-6s" % ("+%d" % gains[c[0]]) for c in CASES)
        print("  %-4s %-9s %-11s %5d %s  %s"
              % (sid, S.KO.get(sid, "?")[:9], KOAX[ax], round(cur), r, g))
    print()
    print("  ※ 세 벌에서 **차례가 안 바뀌는 것**만 먼저 고치시오. 한 벌에서만")
    print("    큰 것은 가정이 만든 것이오.")
    print("-" * 76)
    print("  걸린 시간 %.0f초" % (time.perf_counter() - t0))

    if a.json:
        Path(a.json).write_text(json.dumps({
            "n": len(measured), "path": path,
            "screens": {s: {k: v for k, v in screens[s].items()
                            if k != "missing"} for s in path},
            "missing": {s: screens[s]["missing"] for s in path},
            "give_take": {s: gt.get(s) for s in path},
            "funnel": {c[0]: {"paid": results[c[0]][0],
                              "reach": results[c[0]][3],
                              "left": dict(results[c[0]][1])} for c in CASES},
            "why": {"%s|%s" % k: v for k, v in why.items()},
            "fixes": [{"screen": sc, "axis": ax, "now": round(c),
                       "gain_paid": g, "gain_reach": r}
                      for sc, ax, c, g, r in rows],
        }, ensure_ascii=False, indent=1), encoding="utf8")
        print("  적어 둠 → %s" % a.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
