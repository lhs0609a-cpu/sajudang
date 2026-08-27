"""
1만 명이 들어왔을 때 — 어디서 터지고, 어디서 나가고, 다 다르게 나오는가.

한 사람이 처음 들어와 값을 치르고 스무 사람까지 받는 **전 구간**을 실제로
돌립니다. 화면을 흉내내는 게 아니라 엔진 함수를 그대로 부릅니다.

  chart → hook 5단 → 무료 리포트 → 릴레이 → 유료(한 자리) →
  유료(여덟 글자 전부) → 스무 사람 종합 → 오늘의 일진 → 분석지·공유

재는 것 넷

  [1] 문제 발생지점   구간마다 몇 명이 터졌는가 · 무엇으로
  [2] 이탈지점       구간마다 몇 명이 막히는가 · 왜 (구조적 사유만)
  [3] 유일성         정말 사람마다 다른가 — 가짓수 말고 **최다 점유**
  [4] 적합성         나온 문장이 그 사람의 여덟 글자에서 나온 것인가
                     — 렌더된 글을 되짚어 Features 와 대조합니다

★ [2] 는 **실제 이탈률이 아닙니다.** 실이탈은 `tools/funnel.py` 가 실사용
  기록으로 봅니다. 여기서 재는 건 "구조가 사람을 세우는 자리" 입니다.

    python tools/journey_sim.py [인원수]
"""
from __future__ import annotations

import collections
import json
import random
import re
import sys
import time
import traceback
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "services" / "api") not in sys.path:
    sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import bank as bank_mod          # noqa: E402
from engine import extras as extras_mod      # noqa: E402
from engine import guard                     # noqa: E402
from engine import lens as lens_mod          # noqa: E402
from engine import relay as relay_mod        # noqa: E402
from engine.calendar import CITY_LON, build_chart   # noqa: E402
from engine.daily import build_daily         # noqa: E402
from engine.features import build_features   # noqa: E402
from engine.omnibus import build_omnibus     # noqa: E402
from engine.report import build_report       # noqa: E402
from engine.summary import build_summary, share_payload  # noqa: E402

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.population import hour_unknown_share   # noqa: E402

SEED = 20260827

# 진입 캐릭터. 화면과 같아야 합니다 — apps/web/lib/lenses.ts DEFAULT_LENS
ENTRY_LENS = "pungun"
CONCERNS = ("money", "work", "love", "people", "dir", "health")
AXIS_LETTERS = (("E", "I"), ("S", "N"), ("T", "F"), ("J", "P"))

# 실제 유입 연령대. 1955~2010 은 문턱 재기용 표본이라 더 넓게 잡습니다.
BIRTH_YEARS = (1950, 2012)
DAYS_IN = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def days_in(y: int, m: int) -> int:
    """윤년까지 봅니다. 여기서 2월 30일을 만들면 엔진이 아니라 이 도구가
    터집니다 — 이상한 입력은 [1c] 에서 따로 겨눕니다."""
    if m == 2 and ((y % 4 == 0 and y % 100 != 0) or y % 400 == 0):
        return 29
    return DAYS_IN[m - 1]

# 성향 4글자를 적는 사람 비율 — 선택 입력이라 전원이 적지는 않습니다.
AXIS4_SHARE = 0.55
# 캐릭터가 요구하는 추가 입력을 실제로 채워 주는 비율.
EXTRA_FILL_SHARE = 0.70


# ══════════════════════════════════════════════════════════
# 인구
# ══════════════════════════════════════════════════════════
_HOUR_SRC = ""


def people(n: int, seed: int = SEED) -> list:
    global _HOUR_SRC
    share, src = hour_unknown_share()
    _HOUR_SRC = "표본 %d명 · 시각 미상 %.1f%% — %s" % (n, 100 * share, src)
    rng = random.Random(seed)
    cities = list(CITY_LON)
    out = []
    for i in range(n):
        known = rng.random() >= share
        m = rng.randint(1, 12)
        y = rng.randint(*BIRTH_YEARS)
        out.append({
            "i": i,
            "year": y,
            "month": m,
            "day": rng.randint(1, days_in(y, m)),
            "hour": rng.randint(0, 23) if known else None,
            "minute": rng.randint(0, 59) if known else None,
            "sex": rng.choice("FM"),
            "hour_known": known,
            "city": rng.choice(cities),
            "concern": rng.choice(CONCERNS),
            "axis4": ("".join(rng.choice(p) for p in AXIS_LETTERS)
                      if rng.random() < AXIS4_SHARE else None),
            "fills_extra": rng.random() < EXTRA_FILL_SHARE,
            "rng": random.Random(seed * 7919 + i),
        })
    return out


def make_extras(need, rng):
    """캐릭터가 요구하는 추가 입력을 채워 준다. 저장하지 않는 값들입니다."""
    T = extras_mod.text()
    if need == "blood":
        return {"blood": {"type": rng.choice(["A", "B", "O", "AB"])}}
    if need == "image":
        return {"image": {"pick": rng.choice(list(T["IMAGE"]))}}
    if need == "cards":
        return {"cards": {"picks": rng.sample(list(T["CARD"]), 3)}}
    if need == "partner":
        m = rng.randint(1, 12)
        py = rng.randint(1955, 2008)
        return {"partner": {"year": py, "month": m,
                            "day": rng.randint(1, days_in(py, m)),
                            "hour": rng.randint(0, 23),
                            "minute": rng.randint(0, 59),
                            "sex": rng.choice("FM"), "hour_known": True}}
    if need == "context":
        return {"context": {"situation": rng.choice(list(T["SITUATION"])),
                            "stance": rng.choice(["push", "hold", "let"]),
                            "months": rng.randint(0, 60)}}
    return None


# ══════════════════════════════════════════════════════════
# 집계기
# ══════════════════════════════════════════════════════════
class Tally:
    def __init__(self):
        self.fail = collections.Counter()          # 구간 → 터진 수
        self.sample = {}                           # 구간 → 첫 역추적
        self.stop = collections.Counter()          # 이탈 사유 → 수
        self.reached = collections.Counter()       # 구간 → 도달 수
        self.uniq = collections.defaultdict(collections.Counter)
        self.fit_bad = collections.Counter()       # 적합성 항목 → 어긋난 수
        self.fit_bad_ex = {}
        self.fit_run = collections.Counter()
        self.guard_hit = collections.Counter()
        self.notes = collections.Counter()
        self.ms = collections.defaultdict(list)      # 구간 → 걸린 밀리초

    def clock(self, stage):
        return _Clock(self, stage)

    def fit(self, key, ok, ctx=""):
        self.fit_run[key] += 1
        if not ok:
            self.fit_bad[key] += 1
            self.fit_bad_ex.setdefault(key, ctx)

    def blew(self, stage, e):
        self.fail[stage] += 1
        self.sample.setdefault(stage, "%s: %s\n%s" % (
            type(e).__name__, e,
            "".join(traceback.format_tb(e.__traceback__)[-2:])))


class _Clock:
    """구간이 몇 밀리초 걸렸는가. 1만 명이 한꺼번에 오면 이게 곧 병목입니다."""

    def __init__(self, T, stage):
        self.T, self.stage = T, stage

    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *a):
        self.T.ms[self.stage].append((time.perf_counter() - self.t0) * 1000)
        return False


TAG = re.compile(r"<[^>]+>")


def plain(html: str) -> str:
    return TAG.sub("", html or "")


def cuts_text(rep) -> str:
    return "".join(c["html"] for c in rep["cuts"])


# ══════════════════════════════════════════════════════════
# 한 사람
# ══════════════════════════════════════════════════════════
def run_one(p, T: Tally, today: date):
    rng = p["rng"]

    # ── 1 · 명식 ────────────────────────────────────────
    T.reached["1 명식"] += 1
    try:
        with T.clock("1 명식"):
            ch = build_chart(p["year"], p["month"], p["day"], p["hour"],
                             p["minute"], p["sex"], p["hour_known"], p["city"])
            f = build_features(ch, as_of=today)
    except Exception as e:
        T.blew("1 명식", e)
        T.stop["명식을 못 세움 — 그 자리에서 끝"] += 1
        return
    T.uniq["명식(여덟 글자)"]["".join(x["gz"] for x in f.pillars)] += 1

    # 적합성 — 시각 미상이면 시주가 없어야 한다
    T.fit("시각 미상이면 시주 없음",
          (len(f.pillars) == 3) if not p["hour_known"] else (len(f.pillars) == 4),
          "hour_known=%s pillars=%d" % (p["hour_known"], len(f.pillars)))

    # ── 2 · 훅 5단 ──────────────────────────────────────
    T.reached["2 훅 5단"] += 1
    try:
        with T.clock("2 훅 5단"):
            segs = bank_mod.build_hook(f, p["concern"], p["axis4"], "", "그대")
    except Exception as e:
        T.blew("2 훅 5단", e)
        T.stop["훅을 못 만듦 — 첫 화면이 빔"] += 1
        return
    hook_html = "".join(s["html"] for s in segs)
    T.uniq["훅 전문"][hook_html] += 1
    T.uniq["훅 0단(찌르기)"][segs[0]["html"]] += 1
    if not p["axis4"]:
        T.notes["넉 자 미입력 — 훅 2.5단(어긋난 자리)이 빠짐"] += 1

    # 적합성 — 훅 0단이 이 사람의 약오행·일간·고민에서 나왔는가
    B = bank_mod.bank()
    T.fit("훅 찌르기 = STAB[고민][약오행]",
          B["STAB"][p["concern"]][f.weak_el] in segs[0]["html"],
          "%s/%s" % (p["concern"], f.weak_el))
    T.fit("훅 일간 줄 = STAB_GAN[일간]",
          B["STAB_GAN"][f.day_gan] in segs[0]["html"], f.day_gan)
    T.fit("훅 1단 = MYTH_TG[주도십신][고민]",
          B["MYTH_TG"][f.top_ten_god][p["concern"]] in segs[1]["html"],
          "%s/%s" % (f.top_ten_god, p["concern"]))

    # ── 3 · 무료 리포트 ──────────────────────────────────
    T.reached["3 무료 리포트"] += 1
    free_lens = ENTRY_LENS
    try:
        with T.clock("3 무료 리포트"):
            free = build_report(f, "sim", free_lens, "free", p["concern"],
                                p["axis4"])
    except Exception as e:
        T.blew("3 무료 리포트", e)
        T.stop["무료 리포트가 안 나옴"] += 1
        return
    T.uniq["무료 리포트 전문"][cuts_text(free)] += 1
    if free["locked"]:
        T.stop["무료에서 잠긴 컷을 봄 (%d컷) — 결제 갈림길"
               % len(free["locked"])] += 1

    # 적합성 — 명식 컷에 그 사람의 여덟 글자가 그대로 있는가
    chart_cut = next(c for c in free["cuts"] if c["id"] == "chart")
    T.fit("명식 컷에 실제 기둥이 그대로",
          all(x["gz"] in chart_cut["html"] for x in f.pillars),
          "".join(x["gz"] for x in f.pillars))
    lack_cut = next(c for c in free["cuts"] if c["id"] == "lack")
    T.fit("없는 것 컷 = 약오행",
          bank_mod.element_word(f.weak_el) in lack_cut["html"]
          and B["LACK_LIVED"][f.top_ten_god] in lack_cut["html"],
          "%s/%s" % (f.weak_el, f.top_ten_god))
    place_cut = next(c for c in free["cuts"] if c["id"] == "place")
    T.fit("어느 자리 컷 = 일지·일간",
          f.day_ji in place_cut["html"]
          and B["PLACE_NOTE"][f.day_gan] in place_cut["html"],
          "%s/%s" % (f.day_ji, f.day_gan))

    # ── 4 · 릴레이 ──────────────────────────────────────
    T.reached["4 릴레이"] += 1
    try:
        with T.clock("4 릴레이"):
            rec = relay_mod.recommend(f, read=[free_lens], skipped=[],
                                      session_relay_count=0, last_lens=free_lens)
    except Exception as e:
        T.blew("4 릴레이", e)
        T.stop["릴레이가 터짐 — 다음 사람이 안 뜸"] += 1
        return
    items = rec.get("recommend") or []
    if rec.get("blocked"):
        T.stop["릴레이 브레이크 — 세션당 상한에 걸림"] += 1
    if rec.get("forced"):
        T.notes["무거운 리포트 뒤 무료 캐릭터가 강제로 앞에 붙음"] += 1
    if not items:
        T.stop["추천할 사람이 하나도 없음 — 막다른 화면"] += 1
        return
    T.uniq["릴레이 1순위"][items[0]["lens_id"]] += 1
    T.uniq["릴레이 상위3 묶음"][",".join(sorted(x["lens_id"] for x in items))] += 1
    if items[0].get("price", 0) == 0:
        T.notes["1순위가 무료 캐릭터 (근거 없음 대체 또는 정서 안전망)"] += 1

    # 규칙이 밖으로 새지 않는가
    leak = [k for k in ("rule_id", "priority", "score", "reach", "complement")
            if any(k in it for it in items)]
    T.fit("릴레이 응답에 분기표가 안 실림", not leak, ",".join(leak))
    T.fit("근거에 연산자가 없음",
          not any(re.search(r"[<>≤≥=]", it.get("reason") or "") for it in items),
          (items[0].get("reason") or "")[:44])
    # 소수·음수는 내부 점수입니다. "관성이 3 자리" 같은 정수 자릿수는 읽히는
    # 사실이라 통과시킵니다.
    raw = [it.get("reason") or "" for it in items
           if re.search(r"\d+\.\d|-\d", it.get("reason") or "")]
    T.fit("근거에 내부 점수(소수·음수)가 안 실림", not raw, raw[0][:44] if raw else "")

    # ── 5 · 유료 · 한 자리 ───────────────────────────────
    pick = items[0]
    lens_id = pick["lens_id"]
    need = lens_mod.required_input(lens_id)
    ex = make_extras(need, rng) if (need and p["fills_extra"]) else None

    T.reached["5 유료 · 한 자리"] += 1
    try:
        with T.clock("5 유료 · 한 자리"):
            one = build_report(f, "sim", lens_id, "one", p["concern"],
                               p["axis4"], ex)
    except Exception as e:
        T.blew("5 유료 · 한 자리", e)
        T.stop["값을 치렀는데 리포트가 안 나옴"] += 1
        return
    T.uniq["유료(한 자리) 전문"][cuts_text(one)] += 1
    if one.get("needs_input"):
        T.stop["캐릭터가 입력을 더 요구 — %s" % one["needs_input"]] += 1
    if one["locked"]:
        T.notes["한 자리에서 또 잠긴 컷 %d개" % len(one["locked"])] += 1

    yong = next((c for c in one["cuts"] if c["id"] == "yongsin"), None)
    T.fit("용신 컷 = 그 사람의 용신",
          yong is not None and bank_mod.element_word(f.yongsin) in yong["html"],
          f.yongsin)
    dn = next((c for c in one["cuts"] if c["id"] == "daeun_now"), None)
    T.fit("지금 대운 컷 = 실제 현재 대운",
          dn is not None and f.daeun[f.daeun_now]["gz"] in dn["html"],
          f.daeun[f.daeun_now]["gz"])
    T.fit("대운 진입 전이면 들어갔다고 말하지 않음",
          f.daeun_started
          or (dn is not None and "아직 첫 대운에 들지 않았소" in dn["html"]),
          "started=%s" % f.daeun_started)

    # ── 5b · 두 번째 릴레이 · 세 번째(브레이크에 걸림) ─────
    #
    # 한 사람을 읽고 나면 다음이 뜹니다. 세 번째는 세션 상한에 걸려야
    # 정상입니다 — 브레이크가 실제로 서는지 여기서 봅니다.
    read2 = [free_lens, lens_id]
    try:
        with T.clock("5b 릴레이 2회차"):
            rec2 = relay_mod.recommend(f, read=read2, skipped=[],
                                       session_relay_count=1, last_lens=lens_id)
        if not (rec2.get("recommend") or []):
            T.stop["두 번째 릴레이에서 추천이 빔 — 여기서 끝남"] += 1
        rec3 = relay_mod.recommend(f, read=read2, skipped=[],
                                   session_relay_count=2, last_lens=lens_id)
        T.fit("세 번째 릴레이는 브레이크에 걸림", bool(rec3.get("blocked")),
              "blocked=%s" % rec3.get("blocked"))
    except Exception as e:
        T.blew("5b 릴레이 2회차", e)

    # ── 6 · 유료 · 여덟 글자 전부 ─────────────────────────
    T.reached["6 유료 · 전부"] += 1
    try:
        with T.clock("6 유료 · 전부"):
            alls = build_report(f, "sim", lens_id, "all", p["concern"],
                                p["axis4"], ex)
    except Exception as e:
        T.blew("6 유료 · 전부", e)
        T.stop["가장 비싼 걸 샀는데 안 나옴"] += 1
        return
    T.uniq["유료(전부) 전문"][cuts_text(alls)] += 1
    T.uniq["유료(전부) 컷 구성"][",".join(c["id"] for c in alls["cuts"])] += 1
    if alls["locked"]:
        T.notes["'전부' 인데 잠긴 컷 %d개" % len(alls["locked"])] += 1
    if not any(c["id"] == "axis" for c in alls["cuts"]):
        T.stop["넉 자 미입력이라 대조 컷이 통째로 빠짐 (가장 비싼 상품)"] += 1

    # 두 번째 결제가 진짜 다른 물건인가 — 같은 사람을 다른 캐릭터로
    if len(items) > 1:
        l2 = items[1]["lens_id"]
        n2 = lens_mod.required_input(l2)
        e2 = make_extras(n2, rng) if (n2 and p["fills_extra"]) else None
        try:
            second = build_report(f, "sim", l2, "all", p["concern"], p["axis4"], e2)
            a = {plain(c["html"]) for c in alls["cuts"]}
            b = [plain(c["html"]) for c in second["cuts"]]
            T.uniq["두 번째 리포트의 새 문단 수"][
                str(sum(1 for x in b if x not in a))] += 1
        except Exception as e:
            T.blew("6b 두 번째 리포트", e)

    # ── 7 · 스무 사람 종합 ───────────────────────────────
    T.reached["7 스무 사람 종합"] += 1
    omni = None
    try:
        with T.clock("7 스무 사람 종합"):
            omni = build_omnibus(f, "sim", p["concern"], p["axis4"], "", ex)
    except Exception as e:
        T.blew("7 스무 사람 종합", e)
        T.stop["종합이 안 나옴"] += 1
    if omni:
        T.uniq["종합 전문"][json.dumps(omni, ensure_ascii=False,
                                    sort_keys=True)] += 1
        n_read = len(omni.get("chapters") or [])
        if n_read < 20:
            T.notes["종합에 스무 명이 다 안 옴 (%d명)" % n_read] += 1

    # ── 8 · 오늘의 일진 ─────────────────────────────────
    T.reached["8 오늘의 일진"] += 1
    try:
        with T.clock("8 오늘의 일진"):
            d = build_daily(f, today)
        T.uniq["일진(같은 날)"][json.dumps(d, ensure_ascii=False,
                                       sort_keys=True)] += 1
    except Exception as e:
        T.blew("8 오늘의 일진", e)

    # ── 9 · 분석지 · 공유 ───────────────────────────────
    T.reached["9 분석지 · 공유"] += 1
    try:
        with T.clock("9 분석지 · 공유"):
            s = build_summary(ch, f, p["concern"], p["axis4"])
            sp = share_payload(s)
        T.uniq["분석지"][json.dumps(s, ensure_ascii=False, sort_keys=True)] += 1
        blob = json.dumps(sp, ensure_ascii=False)
        # ★ 부분일치로 보면 값(19900)이 생년(1990)으로 잡힙니다. 토큰으로 봅니다.
        yr = re.search(r"(?<!\d)%d(?!\d)" % p["year"], blob)
        T.fit("공유 payload 에 생년월일·고을이 없음",
              not yr and p["city"] not in blob,
              "%d/%s" % (p["year"], p["city"]))
    except Exception as e:
        T.blew("9 분석지 · 공유", e)

    # ── 가드 — 전 출력면을 한 번 더 훑는다 ──────────────
    for label, txt in (("훅", hook_html), ("무료", cuts_text(free)),
                       ("유료 한 자리", cuts_text(one)),
                       ("유료 전부", cuts_text(alls))):
        ok, hits = guard.check(plain(txt))
        if not ok:
            for h in hits:
                T.guard_hit["%s · %s" % (label, h)] += 1



# ══════════════════════════════════════════════════════════
# 이상한 입력 — 사람은 반드시 이렇게 칩니다
# ══════════════════════════════════════════════════════════
#
# 인구 표본은 멀쩡한 값만 냅니다. 그래서 여기서 따로 겨눕니다.
# 보는 것: 거절하는가 · **무엇이라 말하는가**. 이 집은 우리말로 말하기로
# 했는데(apps/web/lib/birth.ts), 서버 쪽에서 파이썬 원문이 새면
# 그 자리에서 몰입이 깨집니다.
BAD_BIRTHS = [
    ("2월 30일", dict(year=1993, month=2, day=30, hour=9, minute=0)),
    ("윤년 아닌 해의 2월 29일", dict(year=1993, month=2, day=29, hour=9, minute=0)),
    ("11월 31일", dict(year=2000, month=11, day=31, hour=9, minute=0)),
    ("범위 밖 연도(1899)", dict(year=1899, month=5, day=5, hour=9, minute=0)),
    ("범위 밖 연도(2101)", dict(year=2101, month=5, day=5, hour=9, minute=0)),
]

HANGUL = re.compile(r"[가-힣]")
ASCII_MSG = re.compile(r"[a-z]{4,}")


def probe_bad_input() -> list:
    """돌려주는 것: [(무엇, 거절했는가, 우리말인가, 실제 문구)]"""
    rows = []
    for label, kw in BAD_BIRTHS:
        try:
            build_chart(kw["year"], kw["month"], kw["day"], kw["hour"],
                        kw["minute"], "F", True, "서울")
            rows.append((label, False, False, "받아들임 — 거절하지 않았습니다"))
        except Exception as e:
            msg = str(e)
            rows.append((label, True, bool(HANGUL.search(msg))
                         and not ASCII_MSG.search(msg), msg))

    # 추가 입력이 틀렸을 때 — **그 컷만 접는가, 지어내지는 않는가.**
    #
    # ★ 예전에는 리포트 전체가 422 로 막혔습니다. 값을 치른 사람도요.
    #   지금은 그 컷만 접고 extra_error 로 사유를 보냅니다. 그러니
    #   여기서 볼 것은 셋입니다 —
    #     ① 리포트가 나오는가   ② 사유를 우리말로 말하는가
    #     ③ 틀린 값으로 컷을 **지어내지 않았는가**
    ch = build_chart(1993, 7, 14, 5, 20, "F", True, "대전")
    f = build_features(ch, as_of=date(2026, 8, 27))
    bad_extras = [
        ("상대 사주에 2월 30일", "wolha", "partner",
         {"partner": {"year": 1990, "month": 2, "day": 30, "hour": 9,
                      "minute": 0, "sex": "M", "hour_known": True}}),
        ("모르는 혈액형", "jeokhyeol", "blood", {"blood": {"type": "C"}}),
        ("패를 두 장만", "paeseon", "cards", {"cards": {"picks": ["gil", "mun"]}}),
    ]
    for label, lid, cut_id, ex in bad_extras:
        try:
            rep = build_report(f, "probe", lid, "all", "love", "INFP", ex)
        except Exception as e:
            rows.append((label, True, False,
                         "★ 리포트 전체가 막힘: %s — 값을 치른 사람입니다"
                         % type(e).__name__))
            continue
        err = rep.get("extra_error")
        made = any(c["id"] == cut_id for c in rep["cuts"])
        if made:
            rows.append((label, False, False,
                         "★ 틀린 값으로 %s 컷을 지어냈습니다" % cut_id))
        elif not err:
            rows.append((label, False, False,
                         "★ 조용히 빠졌습니다 — 무엇이 틀렸는지 말하지 않음"))
        else:
            rows.append((label, True,
                         bool(HANGUL.search(err)) and not ASCII_MSG.search(err),
                         "그 컷만 접음 (%d컷은 그대로) · %s"
                         % (len(rep["cuts"]), err)))
    return rows

# ══════════════════════════════════════════════════════════
# 보고
# ══════════════════════════════════════════════════════════
def pct(a, b):
    return "%5.1f%%" % (100.0 * a / b) if b else "    —"


def report(T: Tally, n: int) -> int:
    W = 78
    print("=" * W)
    print("  %d명이 들어왔을 때 — 전 구간" % n)
    print("=" * W)
    print("  %s" % _HOUR_SRC)
    print()

    print("[1] 문제 발생지점 — 구간마다 몇 명이 터졌는가")
    print("-" * W)
    tot = 0
    for stage in sorted(T.reached):
        r = T.reached[stage]
        fl = T.fail.get(stage, 0)
        tot += fl
        print("  %-20s 도달 %6d   터짐 %5d  %s %s"
              % (stage, r, fl, pct(fl, r), "←" if fl else ""))
    for stage in sorted(T.fail):
        if stage not in T.reached:
            print("  %-20s              터짐 %5d  ←" % (stage, T.fail[stage]))
            tot += T.fail[stage]
    print("  %-20s %s" % ("합계",
                          "터짐 0건 — 전 구간 통과" if not tot else "터짐 %d건" % tot))
    if T.sample:
        print()
        for stage, tb in T.sample.items():
            print("  ── %s ──" % stage)
            for ln in tb.strip().splitlines():
                print("     " + ln)
    print()

    print("[1b] 구간별 소요 시간 — 1만 명이 한꺼번에 오면 여기가 병목")
    print("-" * W)
    print("  %-20s %8s %8s %8s %10s" % ("", "중앙값", "p95", "최대", "1만명 합(추정)"))
    for stage in sorted(T.ms):
        v = sorted(T.ms[stage])
        if not v:
            continue
        med = v[len(v) // 2]
        p95 = v[min(len(v) - 1, int(len(v) * 0.95))]
        print("  %-20s %7.1fms %7.1fms %7.1fms %8.1fs"
              % (stage, med, p95, v[-1], sum(v) / len(v) * 10000 / 1000.0))
    print()

    print("[1c] 이상한 입력 — 거절하는가, 그리고 우리말로 말하는가")
    print("-" * W)
    for label, refused, korean, msg in probe_bad_input():
        mark = "OK " if (refused and korean) else "봄  "
        print("  %s %-26s %s · %s" % (
            mark, label,
            "거절함" if refused else "★ 안 거절함",
            "우리말" if korean else "★ 파이썬 원문"))
        print("       %s" % msg)
    print()

    print("[2] 이탈지점 — 구조가 사람을 세우는 자리 (실이탈률 아님)")
    print("-" * W)
    if not T.stop:
        print("  없음")
    for why, c in T.stop.most_common():
        print("  %6d명 %s  %s" % (c, pct(c, n), why))
    if T.notes:
        print()
        print("  참고로 세어 둔 것")
        for why, c in T.notes.most_common():
            print("  %6d명 %s  %s" % (c, pct(c, n), why))
    print()

    print("[3] 유일성 — 정말 사람마다 다른가")
    print("-" * W)
    print("  %-26s %8s %9s %9s" % ("", "가짓수", "1인 전용", "최다 점유"))
    for key, cnt in T.uniq.items():
        total = sum(cnt.values())
        kinds = len(cnt)
        singles = sum(1 for v in cnt.values() if v == 1)
        _, tv = cnt.most_common(1)[0]
        share = tv / total if total else 0
        flag = "← 쏠림" if share > 0.10 else ("← 눈여겨볼 것" if share > 0.05 else "")
        print("  %-26s %8d %8s  %8s %s"
              % (key, kinds, pct(singles, total), pct(tv, total), flag))
    print()

    print("[4] 적합성 — 나온 글이 그 사람의 여덟 글자에서 나왔는가")
    print("-" * W)
    for key in sorted(T.fit_run):
        ran, bad = T.fit_run[key], T.fit_bad.get(key, 0)
        print("  %s %-40s %6d건 중 어긋남 %d %s"
              % ("OK " if not bad else "틀림", key, ran, bad,
                 "(%s)" % T.fit_bad_ex[key] if bad else ""))
    print()

    print("[5] 가드 — 금지어가 새어 나갔는가")
    print("-" * W)
    if not T.guard_hit:
        print("  위반 0건")
    for k, c in T.guard_hit.most_common(20):
        print("  %6d  %s" % (c, k))
    print()

    bad = tot + sum(T.fit_bad.values()) + sum(T.guard_hit.values())
    print("=" * W)
    print("  터짐 %d · 적합성 어긋남 %d · 가드 위반 %d"
          % (tot, sum(T.fit_bad.values()), sum(T.guard_hit.values())))
    print("=" * W)
    return 0 if bad == 0 else 1


def main() -> int:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    T = Tally()
    today = date(2026, 8, 27)
    pop = people(n)
    for i, p in enumerate(pop):
        run_one(p, T, today)
        if (i + 1) % 1000 == 0:
            print("  … %d/%d" % (i + 1, n), file=sys.stderr)
    return report(T, n)


if __name__ == "__main__":
    sys.exit(main())
