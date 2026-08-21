"""
신살(神殺) · 궁위(宮位) — 누가 돕고, 어디서 오는가.

★ 표는 유파마다 다릅니다. 지장간(docs/05 §3)과 같은 원칙입니다.
  **아래 표를 쓰기로 확정하고 문서에 남깁니다.** 중간에 바꾸면 기존
  사용자 결과가 달라집니다.

여기서 확정한 유파
    천을귀인  일간 기준 · 가결 "甲戊庚牛羊 乙己鼠猴鄉 丙丁猪雞位 壬癸兔蛇藏 六辛逢馬虎"
    태극귀인  **일간 기준** (년간 기준 유파도 있음 — 우리는 일간)
    양인      **양간만** (음간 양인을 쓰는 유파도 있음 — 우리는 안 씀)
    도화·역마·화개  **년지와 일지 둘 다** 기준으로 봄 (년지만 보는 유파도 있음)
    공망      **일주 순중공망** (년주 기준 유파도 있음 — 우리는 일주)
    괴강      庚辰 庚戌 壬辰 戊戌 (壬戌을 넣는 유파도 있음 — 우리는 뺌)

★ 해석에서 지키는 것 (docs/11 · CLAUDE.md 절대 규칙 2)
    · "귀인이 나타난다" 처럼 단정하지 않는다
    · "조상 덕에 잘 된다" 처럼 인과를 확정하지 않는다
    · 전통 해석 체계가 그렇게 본다는 사실만 전한다
"""
from __future__ import annotations

from typing import Optional

from .constants import GAN, JI, ELEMENT_OF_GAN, HIDDEN, TEN_GOD_GROUP, ten_god

# ══════════════════════════════════════════════════════════
# 길신 — 일간 기준
# ══════════════════════════════════════════════════════════
# 천을귀인(天乙貴人) — 가장 대표적인 길신
CHEONEUL = {
    "甲": "丑未", "戊": "丑未", "庚": "丑未",
    "乙": "子申", "己": "子申",
    "丙": "亥酉", "丁": "亥酉",
    "壬": "卯巳", "癸": "卯巳",
    "辛": "寅午",
}

# 태극귀인(太極貴人) — 시작과 끝을 관장. 학문·역학·종교에 인연
TAEGEUK = {
    "甲": "子午", "乙": "子午",
    "丙": "卯酉", "丁": "卯酉",
    "戊": "辰戌丑未", "己": "辰戌丑未",
    "庚": "寅亥", "辛": "寅亥",
    "壬": "巳申", "癸": "巳申",
}

# 문창귀인(文昌貴人) — 글·시험·표현
MUNCHANG = {
    "甲": "巳", "乙": "午", "丙": "申", "丁": "酉", "戊": "申",
    "己": "酉", "庚": "亥", "辛": "子", "壬": "寅", "癸": "卯",
}

# 금여(金輿) — 배우자·안락
GEUMYEO = {
    "甲": "辰", "乙": "巳", "丙": "未", "丁": "申", "戊": "未",
    "己": "申", "庚": "戌", "辛": "亥", "壬": "丑", "癸": "寅",
}

# 암록(暗祿) — 드러나지 않는 도움. 건록과 육합하는 자리
AMROK = {
    "甲": "亥", "乙": "戌", "丙": "申", "丁": "未", "戊": "申",
    "己": "未", "庚": "巳", "辛": "辰", "壬": "寅", "癸": "丑",
}

# 양인(羊刃) — 양간만. 힘이 넘쳐 날이 서는 자리
YANGIN = {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"}

# ══════════════════════════════════════════════════════════
# 삼합 기준 — 년지·일지 둘 다에서 본다
# ══════════════════════════════════════════════════════════
_SAMHAP = {
    "寅午戌": {"도화": "卯", "역마": "申", "화개": "戌"},
    "申子辰": {"도화": "酉", "역마": "寅", "화개": "辰"},
    "巳酉丑": {"도화": "午", "역마": "亥", "화개": "丑"},
    "亥卯未": {"도화": "子", "역마": "巳", "화개": "未"},
}
SAMHAP_OF = {j: group for group in _SAMHAP for j in group}

# ══════════════════════════════════════════════════════════
# 일주 자체로 성립하는 것
# ══════════════════════════════════════════════════════════
GWAEGANG = {"庚辰", "庚戌", "壬辰", "戊戌"}          # 괴강
BAEKHO = {"甲辰", "乙未", "丙戌", "丁丑", "戊辰", "壬戌", "癸丑"}  # 백호대살

# 지지 원진
WONJIN = {"子": "未", "未": "子", "丑": "午", "午": "丑", "寅": "酉",
          "酉": "寅", "卯": "申", "申": "卯", "辰": "亥", "亥": "辰",
          "巳": "戌", "戌": "巳"}

# ══════════════════════════════════════════════════════════
# 궁위(宮位) — 어느 기둥이 누구 자리인가
# ══════════════════════════════════════════════════════════
PALACE = {
    "년주": {"who": "조상", "also": "뿌리·집안·물려받은 것", "age": "0~15세"},
    "월주": {"who": "부모·형제", "also": "자란 환경·직장", "age": "16~30세"},
    "일주": {"who": "자신·배우자", "also": "일지가 배우자 자리", "age": "31~45세"},
    "시주": {"who": "자식·아랫사람", "also": "말년·결실", "age": "46세~"},
}

# 십신 묶음별 — 그 귀인이 어느 쪽 사람인가
HELPER_KIND = {
    "인성": "손윗사람 · 스승 · 어른",
    "관성": "조직 · 상사 · 공적인 자리",
    "재성": "거래처 · 실무로 얽힌 사람",
    "식상": "후배 · 아랫사람 · 내가 만든 것",
    "비겁": "또래 · 동료 · 형제 같은 사이",
}


def _hit_pillars(pillars, targets: str) -> list:
    """지지가 targets 안에 드는 기둥의 라벨."""
    return [p.label for p in pillars if p.ji in targets]


def gongmang(day_gan: str, day_ji: str) -> str:
    """일주 순중공망 — 그 순(旬)에서 비는 두 지지."""
    g, j = GAN.index(day_gan), JI.index(day_ji)
    return JI[(10 + j - g) % 12] + JI[(11 + j - g) % 12]


def find(chart) -> list:
    """
    명식에서 성립하는 신살을 전부 찾는다.

    돌려주는 것: [{key, name, hanja, kind, at:[기둥라벨], target}]
      kind = 길신 / 살 / 특수
    """
    pillars = chart.pillars
    dg, dj = chart.day_gan, chart.day_ji
    out = []

    def add(key, name, hanja, kind, targets, at=None):
        hits = at if at is not None else _hit_pillars(pillars, targets)
        if hits:
            out.append({"key": key, "name": name, "hanja": hanja,
                        "kind": kind, "at": hits, "target": targets})

    # ── 일간 기준 길신 ──
    add("cheoneul", "천을귀인", "天乙貴人", "길신", CHEONEUL[dg])
    add("taegeuk", "태극귀인", "太極貴人", "길신", TAEGEUK[dg])
    add("munchang", "문창귀인", "文昌貴人", "길신", MUNCHANG[dg])
    add("geumyeo", "금여", "金輿", "길신", GEUMYEO[dg])
    add("amrok", "암록", "暗祿", "길신", AMROK[dg])

    # ── 양인 ──
    if dg in YANGIN:
        add("yangin", "양인", "羊刃", "살", YANGIN[dg])

    # ── 삼합 기준 — 년지·일지 둘 다에서 본다 ──
    year_ji = pillars[0].ji
    seen = {}
    for base_label, base_ji in (("년지", year_ji), ("일지", dj)):
        group = SAMHAP_OF.get(base_ji)
        if not group:
            continue
        for nm, target in _SAMHAP[group].items():
            hits = _hit_pillars(pillars, target)
            if hits:
                cur = seen.setdefault(nm, {"at": set(), "target": set()})
                cur["at"].update(hits)
                cur["target"].add(target)
    meta = {"도화": ("dohwa", "桃花", "특수"),
            "역마": ("yeokma", "驛馬", "특수"),
            "화개": ("hwagae", "華蓋", "특수")}
    for nm, info in seen.items():
        key, hanja, kind = meta[nm]
        out.append({"key": key, "name": nm, "hanja": hanja, "kind": kind,
                    "at": sorted(info["at"]), "target": "".join(sorted(info["target"]))})

    # ── 일주 자체 ──
    if dg + dj in GWAEGANG:
        add("gwaegang", "괴강", "魁罡", "특수", dj, at=["일주"])
    if dg + dj in BAEKHO:
        add("baekho", "백호대살", "白虎大殺", "살", dj, at=["일주"])

    # ── 공망 ──
    gm = gongmang(dg, dj)
    hits = [p.label for p in pillars if p.ji in gm and p.label != "일주"]
    if hits:
        out.append({"key": "gongmang", "name": "공망", "hanja": "空亡",
                    "kind": "특수", "at": hits, "target": gm})

    # ── 원진 (일지 기준) ──
    wj = WONJIN[dj]
    hits = [p.label for p in pillars if p.ji == wj and p.label != "일주"]
    if hits:
        out.append({"key": "wonjin", "name": "원진", "hanja": "怨嗔",
                    "kind": "살", "at": hits, "target": wj})

    return out


def helpers(chart, features) -> list:
    """
    ★ "누가 귀인인가" — 길신이 앉은 기둥을 궁위로 읽는다.

    천을귀인이 년주에 있으면 윗대·손윗사람 쪽,
    일지에 있으면 배우자 쪽, 시주에 있으면 아랫사람 쪽으로 본다.
    """
    out = []
    for s in find(chart):
        if s["kind"] != "길신":
            continue
        for label in s["at"]:
            p = next(x for x in chart.pillars if x.label == label)
            group = TEN_GOD_GROUP[ten_god(HIDDEN[p.ji][0][0], chart.day_gan)]
            out.append({
                "sinsal": s["name"],
                "hanja": s["hanja"],
                "pillar": label,
                "ji": p.ji,
                "who": PALACE[label]["who"],
                "age": PALACE[label]["age"],
                "kind": HELPER_KIND[group],
                "ten_god_group": group,
            })
    return out


def ancestor(chart, features) -> dict:
    """
    ★ "조상이 어떻게 돕는가" — 년주를 조상 자리로 읽는다.

    확정하지 않는다. 년주에 무엇이 앉았는지와, 그것이 이 사주에
    필요한 오행(용신)인지 아닌지만 말한다.
    """
    p = chart.pillars[0]
    gan_god = ten_god(p.gan, chart.day_gan)
    ji_god = ten_god(HIDDEN[p.ji][0][0], chart.day_gan)
    el_gan = ELEMENT_OF_GAN[p.gan]
    el_ji = ELEMENT_OF_GAN[HIDDEN[p.ji][0][0]]

    sinsal_here = [s for s in find(chart) if "년주" in s["at"]]
    good = [s["name"] for s in sinsal_here if s["kind"] == "길신"]
    bad = [s["name"] for s in sinsal_here if s["kind"] == "살"]

    needed = features.yongsin
    supports = needed in (el_gan, el_ji)
    weighs = features.strong_el in (el_gan, el_ji) and features.strength == "신강"

    if supports:
        stance = "돕는 쪽"
    elif weighs:
        stance = "짐이 되는 쪽"
    else:
        stance = "크게 관여하지 않는 쪽"

    return {
        "pillar": p.gz,
        "gan_ten_god": gan_god,
        "ji_ten_god": ji_god,
        "elements": [el_gan, el_ji],
        "yongsin": needed,
        "supports_yongsin": supports,
        "stance": stance,
        "good_sinsal": good,
        "bad_sinsal": bad,
        "inherited": TEN_GOD_GROUP[gan_god],
    }


def palaces(chart) -> list:
    """네 기둥을 궁위로 읽은 것. 시주가 없으면 시주 자리를 비운다."""
    out = []
    for p in chart.pillars:
        info = PALACE[p.label]
        out.append({"pillar": p.label, "gz": p.gz, "who": info["who"],
                    "also": info["also"], "age": info["age"],
                    "ten_god": ten_god(p.gan, chart.day_gan)
                    if p.label != "일주" else "일간(자신)"})
    if not chart.hour_known:
        out.append({"pillar": "시주", "gz": None, "who": PALACE["시주"]["who"],
                    "also": PALACE["시주"]["also"], "age": PALACE["시주"]["age"],
                    "ten_god": None, "unknown": True})
    return out
