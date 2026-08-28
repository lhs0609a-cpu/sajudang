"""
만 명이 골목(a1)으로 들어오면 몇 명이 값을 치르는가.

    python tools/conversion_sim.py [인원수]

★ 이 도구는 **두 가지를 절대 섞지 않습니다.**

    [센 것]    코드가 실제로 그렇게 동작하는 것. 엔진을 돌려서 셉니다.
               막는 문, 목패 값, 컷 수, 추가 입력 요구, 브레이크 상한.
    [가정한 것] 사람이 화면에서 나갈 확률. 우리는 이걸 **모릅니다.**
               실측은 /v1/funnel 에 기록이 쌓여야 나옵니다.

  그래서 결과를 하나의 수로 내지 않습니다. 가정을 **비관·기준·낙관**
  세 벌로 돌리고, 어느 가정이 답을 가장 크게 흔드는지(민감도)를 같이
  냅니다. 답보다 **무엇을 먼저 재야 하는지**가 이 도구의 산출물입니다.

★ 적중률·전환율을 "예측" 이라 부르지 않습니다. 이건 산수입니다 —
  가정을 넣으면 나오는 값이고, 가정이 틀리면 값도 틀립니다.
"""
from __future__ import annotations

import collections
import random
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "services" / "api") not in sys.path:
    sys.path.insert(0, str(ROOT / "services" / "api"))

import payments                                   # noqa: E402
from engine import bank as bank_mod               # noqa: E402
from engine import lens as lens_mod               # noqa: E402
from engine.calendar import build_chart           # noqa: E402
from engine.features import build_features        # noqa: E402
from engine.report import build_report            # noqa: E402

sys.path.insert(0, str(ROOT / "tools"))
# ★ 인구 표본은 journey_sim 이 쓰는 것과 **같은 것**을 씁니다.
#   도구마다 다른 인구를 보면 숫자를 나란히 놓을 수 없습니다.
#   (population.sample 은 Features 를 내놓습니다 — 여기서는 사람의
#    입력값 자체가 필요해서 journey_sim.people 을 씁니다)
from journey_sim import people as sample_people    # noqa: E402

N_DEFAULT = 10000
SEED = 20260828


# ══════════════════════════════════════════════════════════
# [가정한 것] — 화면마다 몇 %가 다음으로 넘어가는가
# ══════════════════════════════════════════════════════════
#
# ★ 여기 있는 수는 **측정값이 아닙니다.** 우리 손님으로 잰 것이 하나도
#   없습니다. 그래서 폭을 넓게 잡았습니다. 이 표를 고치는 것이 이 도구를
#   쓰는 방법입니다 — /v1/funnel 에 실기록이 쌓이면 그 값으로 갈아
#   끼우고 다시 돌리세요.
#
#   각 줄: (단계 이름, 비관, 기준, 낙관, 무엇을 뜻하는가)
STEPS = [
    ("a1 골목 → 이름",      0.35, 0.55, 0.72,
     "대문에서 첫 버튼을 누른다. 여기가 가장 크게 샙니다"),
    ("a2 이름 → 고민",      0.80, 0.88, 0.94,
     "이름을 적거나 그냥 넘어간다. 빠져나갈 이유가 적은 화면"),
    ("a5 고민 → 날",        0.78, 0.87, 0.93,
     "여섯 중 하나를 고른다. 감정으로 여는 질문이라 잘 걷힙니다"),
    ("a3 날 → 때",          0.62, 0.75, 0.85,
     "년·월·일 + 성별. 이 흐름에서 가장 무거운 화면"),
    ("a4 때 → 성향",        0.82, 0.90, 0.95,
     "「모르오」가 크게 있어 막히지 않는 화면"),
    ("a4b 성향 → 명식",     0.80, 0.89, 0.94,
     "열여섯 칸이지만 「모르오」가 위에 있음"),
    ("a6 명식 → 훅",        0.86, 0.92, 0.96,
     "여덟 글자를 받은 직후. 여기서 나가면 이상한 자리"),
    ("a7 훅 → 무료 6단",    0.55, 0.70, 0.82,
     "훅 다섯 단을 끝까지 읽고 다음을 누른다"),
    ("d0 무료 → 목패",      0.30, 0.45, 0.60,
     "1,592자를 읽고 값 고르는 화면으로 간다"),
    ("d1 목패 → 결제창",    0.18, 0.30, 0.44,
     "목패를 고르고 「이걸로 하겠소」를 누른다"),
    ("d2 결제창 → 승인",    0.55, 0.70, 0.82,
     "PG 결제창에서 실제로 값을 치른다"),
]

# 훅 안에서 한 단씩 빠져나가는 비율 (a7 → 무료 로 넘어가기 전).
# 다섯 단을 다 읽어야 다음 버튼이 나옵니다.
HOOK_STAGE_PASS = {"비관": 0.86, "기준": 0.93, "낙관": 0.97}

CASES = ("비관", "기준", "낙관")
IDX = {"비관": 1, "기준": 2, "낙관": 3}


def funnel(case: str, n: int) -> list:
    """단계별 남는 사람 수. 곱셈입니다 — 화면이 많을수록 가혹합니다."""
    left = float(n)
    rows = []
    for row in STEPS:
        name, why = row[0], row[4]
        rate = row[IDX[case]]
        if name.startswith("a7"):
            # 훅은 다섯 단이라 단마다 한 번씩 더 샙니다
            rate = rate * (HOOK_STAGE_PASS[case] ** 5)
        before = left
        left *= rate
        rows.append((name, rate, before, left, why))
    return rows


# ══════════════════════════════════════════════════════════
# [센 것] — 코드가 실제로 막는 문
# ══════════════════════════════════════════════════════════
def counted(n: int) -> dict:
    """엔진을 그대로 돌려서 센다. 여기 있는 수는 가정이 아니다."""
    people = sample_people(n, seed=SEED)
    rng = random.Random(SEED)

    released = [l for l in lens_mod.released()]
    priced = [l for l in released if l.get("price")]
    free_lens = [l for l in released if not l.get("price")]

    out = {
        "n": n,
        "released": len(released),
        "priced": len(priced),
        "free_lens": [l["id"] for l in free_lens],
        "prices": sorted({l["price"] for l in priced}),
        "tier_price": dict(payments.TIER_PRICE),
        "blew": 0,
        "blew_why": None,
        "no_hour": 0,
        "no_axis4": 0,
        "locked_hist": collections.Counter(),
        "free_chars": [],
        "one_price": collections.Counter(),
        "needs_input": collections.Counter(),
    }

    # 값이 걸리는 화면 하나를 실제로 만들어 봅니다. 스무 사람 전부를
    # 만 번 돌리면 너무 오래 걸리므로, 리포트는 표본으로만 셉니다.
    probe = min(n, 400)

    for i, p in enumerate(people):
        try:
            ch = build_chart(p["year"], p["month"], p["day"],
                             p["hour"], p["minute"], p["sex"],
                             p["hour_known"], p["city"])
            f = build_features(ch)
        except Exception as e:
            # ★ 조용히 삼키지 않습니다.
            #   전에 여기서 인자 순서를 틀려 **만 명이 전부 터졌는데**,
            #   그게 "명식이 터진 사람 10000명" 이라는 그럴듯한 발견으로
            #   찍혔습니다. 터지면 왜 터졌는지 같이 냅니다.
            out["blew"] += 1
            if out["blew_why"] is None:
                out["blew_why"] = "%s: %s" % (type(e).__name__, e)
            continue

        if not p["hour_known"]:
            out["no_hour"] += 1
        if not p["axis4"]:
            out["no_axis4"] += 1

        if i >= probe:
            continue

        # 이 사람이 처음 만나는 캐릭터를 하나 골라 무료 리포트를 냅니다.
        lens = rng.choice(released)
        rep = build_report(f, "sim", lens["id"], "free", p["concern"],
                           p["axis4"])
        out["locked_hist"][len(rep["locked"])] += 1
        out["free_chars"].append(
            sum(len(c["html"]) for c in rep["cuts"]))
        if rep.get("needs_input"):
            out["needs_input"][rep["needs_input"]] += 1

        try:
            out["one_price"][payments.price_of("one", lens["id"])] += 1
        except payments.PaymentError:
            out["one_price"]["없음"] += 1

    return out


def dominance() -> dict:
    """
    목패끼리 견준다.

    ★ 잣대를 고쳤습니다.
      처음에는 **컷 수**로 견줬습니다. 그런데 「달마다 듣기」는 스무 사람을
      열어서, 어떤 한 사람짜리 목패와 견줘도 컷 수가 항상 많습니다.
      그 잣대로는 one 이 영원히 '밀리는' 것으로 나옵니다 — 틀린 계산이
      아니라 **틀린 질문**입니다.

      손님이 실제로 묻는 것은 이겁니다:
          "더 싼 저걸 사면, 이걸 안 사도 되는가?"

      그러니 지배는 이렇게 셉니다 —
          값이 같거나 비싼데, **그 목패만 여는 것이 하나도 없다.**

      지금 「이 자리 하나」는 12,900원부터 대운 맵을, 15,900원부터 성향
      대조를 엽니다. 달삯으로는 **아무리 오래 내도 안 열립니다.**
      그래서 밀리지 않습니다. 그 아래(8,900원 이하)는 값이 달삯보다
      싸서 밀리지 않습니다.
    """
    from engine.calendar import build_chart
    from engine.features import build_features

    f = build_features(build_chart(1997, 3, 22, 14, 10, "F", True, "서울"))
    rows, bad = [], 0
    order = sorted(lens_mod.released(), key=lambda x: -(x.get("price") or 0))

    sub_price = payments.TIER_PRICE["sub"]
    for l in order:
        cuts = {}
        for t in ("one", "sub"):
            if t == "one" and not l.get("price"):
                continue
            r = build_report(f, "sim", l["id"], t, "love", "INFP")
            cuts[t] = {c["id"] for c in r["cuts"]}

        subs = "%s원 %d컷 20사람" % (f"{sub_price:,}", len(cuts["sub"]))
        if "one" not in cuts:
            rows.append({"name": l["name"], "one": "— 목패가 없음",
                         "sub": subs, "only": "", "dominated": False})
            continue

        price = l["price"]
        only = sorted(cuts["one"] - cuts["sub"])
        # 값이 같거나 비싼데, 이 목패만 여는 것이 하나도 없으면 밀린다
        d = price >= sub_price and not only
        bad += 1 if d else 0
        rows.append({
            "name": l["name"],
            "one": "%s원 %d컷 1사람" % (f"{price:,}", len(cuts["one"])),
            "sub": subs,
            "only": ("이것만 여는 컷: " + " · ".join(only)) if only
                    else ("달삯보다 쌈" if price < sub_price else "이것만 여는 것 없음"),
            "dominated": d})

    default = "pungun"
    name = next((l["name"] for l in order if l["id"] == default), default)
    return {"rows": rows, "bad": bad, "total": len(rows),
            "default_name": "%s(%s)" % (name, default),
            "sub_price": sub_price}


# ══════════════════════════════════════════════════════════
# 출력
# ══════════════════════════════════════════════════════════
BAR = "█"


def rule(t=""):
    print("\n" + t)
    print("─" * 78)


def main() -> int:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else N_DEFAULT
    print("=" * 78)
    print("  만 명이 골목으로 들어오면 몇 명이 값을 치르는가 — %d명" % n)
    print("=" * 78)

    # ── 1. 막는 문부터 ────────────────────────────────────
    rule("[1] 먼저 — 지금 배포본에서 값을 치를 수 있는가  ★ 센 것")
    cfg_ok = payments.ENABLED
    print("  결제 열쇠(TOSS)      %s" % ("있음" if cfg_ok else "**없음**"))
    if payments.DISABLED_REASON:
        print("  거절 사유            %s" % payments.DISABLED_REASON)
    print("  라이브 키인가        %s" % ("예" if payments.LIVE else "아니오"))
    if not cfg_ok:
        print()
        print("  ★ 지금 이 상태로 만 명이 들어오면 값을 치르는 사람은")
        print("    **0명**입니다. 모델이 아니라 코드가 그렇습니다 —")
        print("    /v1/pay/prepare 가 503 으로 거절합니다.")
        print("    아래 숫자는 전부 '열쇠를 넣었다면' 의 이야기입니다.")

    c = counted(n)

    rule("[2] 코드가 세우는 문  ★ 센 것")
    print("  불 켜진 캐릭터        %d명 (값 있는 캐릭터 %d명)"
          % (c["released"], c["priced"]))
    print("  캐릭터 값의 종류      %s"
          % " · ".join("%s원" % f"{p:,}" for p in c["prices"]))
    print("  목패 값               one %s / all %s원 / sub %s원·월"
          % ("캐릭터 값", f"{c['tier_price']['all']:,}",
             f"{c['tier_price']['sub']:,}"))
    if c["free_lens"]:
        print("  ★ 값이 없는 캐릭터    %s — 이 사람을 만난 손님에게는"
              % ", ".join(c["free_lens"]))
        print("                        「이 자리 하나」 목패가 아예 안 나옵니다")
    print("  명식이 터진 사람      %d명%s"
          % (c["blew"], "" if not c["blew"] else "  ← 봐야 합니다"))
    if c["blew_why"]:
        print("      첫 사유           %s" % c["blew_why"])
    print("  시각 미상             %d명 (%.1f%%)"
          % (c["no_hour"], 100 * c["no_hour"] / n))
    print("  넉 자 미입력          %d명 (%.1f%%)"
          % (c["no_axis4"], 100 * c["no_axis4"] / n))

    if c["needs_input"]:
        tot = sum(c["needs_input"].values())
        print("  추가 입력을 요구      %d명 중 %d명" % (min(n, 400), tot))
        for k, v in c["needs_input"].most_common():
            print("      %-10s %d명 — 안 적으면 그 컷이 빕니다" % (k, v))

    print()
    print("  브레이크 (지켜야 하는 것 — 매출 최적화로도 못 건드립니다)")
    from engine import relay as relay_mod
    b = relay_mod.BREAKS()
    print("      하루 결제         %s건까지" % b.get("per_day_purchase"))
    print("      세션당 릴레이     %s명까지" % b.get("per_session_relay"))
    print("      ★ 즉 한 사람이 하루에 낼 수 있는 값은 최대 2건입니다.")

    # ── 2b. 목패끼리 잡아먹는가 ───────────────────────────
    rule("[2b] 목패끼리 잡아먹는가  ★ 센 것")
    dom = dominance()
    print("  손님이 묻는 것은 이겁니다 — \"더 싼 저걸 사면 이건 안 사도 되는가?\"")
    print("  그래서 컷 수가 아니라 **그 목패만 여는 것**으로 견줍니다.")
    print()
    print("  %-11s %-20s %s" % ("캐릭터", "이 자리 하나", "이 목패라야 열리는 것"))
    print("  " + "─" * 74)
    for r in dom["rows"]:
        print("  %-11s %-20s %s %s"
              % (r["name"], r["one"], r["only"],
                 "← 밀림" if r["dominated"] else ""))
    print("  " + "─" * 74)
    print("  달마다 듣기: %s원/월 · 스무 사람 · 기본 층만"
          % f"{dom['sub_price']:,}")
    print()
    if dom["bad"]:
        print("  ★ 아직 밀리는 캐릭터: **%d / %d명**" % (dom["bad"], dom["total"]))
    else:
        print("  [OK] 밀리는 목패 없음 — 셋이 서로 다른 것을 팝니다.")
        print("       one 깊이 · sub 넓이 · all 둘 다")

    # ── 3. 퍼널 ──────────────────────────────────────────
    rule("[3] 화면을 지나면 몇이 남는가  ▲ 가정한 것 (측정값 아님)")
    print("  화면마다의 통과율은 **우리 손님으로 잰 것이 하나도 없습니다.**")
    print("  아래는 가정을 넣고 곱한 산수입니다. 폭을 넓게 잡았습니다.")
    print()
    print("  %-22s %7s %7s %7s" % ("단계", "비관", "기준", "낙관"))
    print("  " + "─" * 74)
    rows = {k: funnel(k, n) for k in CASES}
    for i, row in enumerate(STEPS):
        print("  %-22s %7s %7s %7s"
              % (row[0],
                 "%.0f" % rows["비관"][i][3],
                 "%.0f" % rows["기준"][i][3],
                 "%.0f" % rows["낙관"][i][3]))
    print("  " + "─" * 74)
    ends = {k: rows[k][-1][3] for k in CASES}
    print("  %-22s %7s %7s %7s"
          % ("값을 치르는 사람",
             "%.0f" % ends["비관"], "%.0f" % ends["기준"], "%.0f" % ends["낙관"]))
    print("  %-22s %6.2f%% %6.2f%% %6.2f%%"
          % ("전환율", 100 * ends["비관"] / n,
             100 * ends["기준"] / n, 100 * ends["낙관"] / n))

    # ── 4. 어디서 가장 많이 잃는가 ────────────────────────
    rule("[4] 어느 화면이 사람을 가장 많이 잃는가  ▲ 가정 위의 산수")
    base = rows["기준"]
    lost = sorted(((r[2] - r[3], r[0], r[1], r[4]) for r in base),
                  reverse=True)
    for amount, name, rate, why in lost:
        bar = BAR * max(1, int(amount / (n / 60)))
        print("  %-22s %5.0f명 잃음  통과 %4.0f%%  %s"
              % (name, amount, 100 * rate, bar))
        print("  %-22s %s" % ("", why))

    # ── 5. 민감도 ────────────────────────────────────────
    rule("[5] 어느 가정이 답을 가장 크게 흔드는가  ★ 여기가 이 도구의 요점")
    print("  한 단계만 비관→낙관으로 바꾸고 나머지는 기준으로 두면,")
    print("  값을 치르는 사람이 몇 명 늘어나는가.")
    print()
    swing = []
    for i, row in enumerate(STEPS):
        v = float(n)
        for j, r2 in enumerate(STEPS):
            rate = r2[3] if i == j else r2[2]      # i번만 낙관
            if r2[0].startswith("a7"):
                rate *= HOOK_STAGE_PASS["낙관" if i == j else "기준"] ** 5
            v *= rate
        swing.append((v - ends["기준"], row[0], row[2], row[3]))
    for gain, name, b, g in sorted(swing, reverse=True):
        print("  %-22s +%5.1f명   (%.0f%% → %.0f%%)"
              % (name, gain, 100 * b, 100 * g))

    # ── 6. 값 ────────────────────────────────────────────
    rule("[6] 그래서 얼마가 들어오는가  ▲ 가정 위의 산수")
    print("  ★ 값을 치르는 사람이 **무엇을 고르는가**부터 정해야 합니다.")
    print("    지금 구조에서는 셋을 나란히 놓고 보면 「달마다 듣기」가")
    print("    스무 명 중 %d명의 캐릭터에서 이깁니다. 그래서 두 벌로 냅니다."
          % dom["bad"])
    print()
    one_tot = sum(v for k, v in c["one_price"].items() if k != "없음")
    one_sum = sum(k * v for k, v in c["one_price"].items() if k != "없음")
    avg_one = one_sum / one_tot if one_tot else 0
    sub_price = c["tier_price"]["sub"]

    print("  ㈎ 손님이 목패를 **값만 보고 고른다면** (=대부분 sub)")
    for k in CASES:
        print("     %-6s %4.0f명 × %s원/월  =  첫 달 약 %s원"
              % (k, ends[k], f"{sub_price:,}",
                 f"{ends[k] * sub_price:,.0f}"))
    print("     ※ 달삯은 **유지되는 동안만** 들어옵니다. 이탈률은 안 잽니다.")
    print()
    print("  ㈏ 손님이 **읽던 그 사람만** 산다면 (=one, 평균 %s원)"
          % f"{avg_one:,.0f}")
    for k in CASES:
        print("     %-6s %4.0f명 × %s원  =  약 %s원"
              % (k, ends[k], f"{avg_one:,.0f}",
                 f"{ends[k] * avg_one:,.0f}"))
    none = c["one_price"].get("없음", 0)
    if none:
        print("     ★ 값 없는 캐릭터를 만난 %d명(%.1f%%)에게는 이 목패가"
              % (none, 100 * none / max(1, sum(c["one_price"].values()))))
        print("       아예 안 뜹니다 — 살 것이 sub/all 뿐입니다.")
    print()
    print("  ★ 브레이크: 한 사람이 하루에 낼 수 있는 값은 **2건**입니다.")
    print("    위 수는 1인 1건으로 잡은 것이라 상한에 안 걸립니다.")

    rule("읽는 법")
    print("  · [1][2] 는 **센 것**입니다. 코드가 그렇게 동작합니다.")
    print("  · [3]~[6] 은 **가정 위의 산수**입니다. 예측이 아닙니다.")
    print("  · 가장 쓸모 있는 칸은 [5] 입니다 — 무엇을 먼저 재고")
    print("    먼저 고칠지가 거기 있습니다.")
    print("  · 실측이 들어오면 STEPS 표를 갈아 끼우고 다시 도세요.")
    print("    (/v1/funnel · tools/funnel.py)")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
