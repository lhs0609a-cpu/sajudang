"""
사주 사전 — 검색으로 들어오는 문 (docs/44)

★ 이 파일이 지키는 것 하나: **틀에 낱말만 바꿔 넣지 않는다.**

  첫 판은 그걸 어겼습니다. 재는 자를 먼저 세워 둔 덕에 **열기 전에**
  걸렸습니다 (`tools/dict_same.py` · 2026-09-24) —

      일주 60장   짝 겹침 76.5%  ·  이 장에만 있는 수 1.1개  ·  최다 점유 5.9%
                  (문턱 35%)        (문턱 4개)               (문턱 2%)

  까닭은 하나였습니다. 문장 다섯 줄이 **예순 장에 한 벌**이고 그 안의
  낱말만 갈렸습니다 — 「발밑 글자를 십신으로 셈하면 ○요. 일지는 여덟
  글자에서 그대 곁자리라…」. 손님 눈에는 예순 장이 한 장이고, 색인도
  같이 봅니다.

  고친 방식은 이 집이 훅에서 쓰던 것과 같습니다 — **문장을 축에 건다.**
  칸마다 딛는 축이 다르면 두 장이 같은 줄을 쓰는 것은 그 축이 같을
  때뿐입니다.

      일간 단     천간 열       두 장이 겹칠 확률 5/59
      일지 단     지지 열둘                      4/59
      앉은 결     오행 관계 다섯
      십신 단     십신 열
      공망 단     여섯 묶음
      인구 단     순위 다섯 칸    + 이 장에만 있는 수를 싣는다
      틀릴 조건   일지 오행 다섯

  글은 `seed/dict.json` 한 자리에 있고 여기서는 **어느 칸을 고를지만**
  셉니다 (`engine/topic.py` 와 같은 꼴).

★ **이 장에만 있는 수**를 넷 이상 답니다 (docs/44 §2 규칙 1).

  「1만 명에 177명」 같은 값은 예순 장에서 스물넷 가지뿐이라 자에 걸립니다.
  그래서 계산으로 갈리는 자리를 씁니다 —

      갑자 순번    1~60    예순 장에 하나씩
      인구 순위    1~60    표본 명수로 세운다
      표본 명수    595~731
      일간 여섯 중 몇째 · 일지 다섯 중 몇째 · 공망 열 중 몇째

  다 만세력을 펴고 대 볼 수 있는 값입니다. 못 대 보는 수는 안 답니다.

★ **새 명리 규칙을 만들지 않습니다.**

  일지 십신은 `features._ten_gods` 와 같은 자(지지 본기 = `HIDDEN[ji][0][0]`)로
  셉니다. 공망은 `sinsal.gongmang`, 인구는 `seed/rarity.json`(표본 40,000)
  에서 받습니다. 십이운성처럼 이 집이 표를 안 가진 것은 **안 냅니다** —
  지어내면 그날로 사전이 아니라 소설이 됩니다 (docs/44 §3 △ 표시).

★ 저장하지 않습니다. 계산으로 나오는 값이라 저장하면 두 벌이 됩니다.
"""
from __future__ import annotations

import html as _html
import json
from functools import lru_cache
from pathlib import Path

from . import bank as bank_mod
from . import guard
from . import rarity as rarity_mod
from . import sinsal as sinsal_mod
from . import terms as terms_mod
from .constants import (CHUNG, CONTROLLED_BY, CONTROLS, ELEMENT_OF_GAN,
                        ELEMENT_OF_JI, GAN, GAN_SOUND, GENERATED_BY, GENERATES,
                        HAP, HIDDEN, JI, JI_SOUND, TEN_GOD_GROUP,
                        YIN_YANG, ten_god)

SEED = Path(__file__).resolve().parents[3] / "seed"


class DictError(KeyError):
    """사전에 없는 자리. 지어내지 않고 터뜨립니다 — 화면은 404 를 냅니다."""


EL_WORD = {"목": "나무", "화": "불", "토": "흙", "금": "쇠", "수": "물"}
YY_WORD = {1: "양", 0: "음"}
#: 뿌리 상태를 화면 말로. ★ 속에서 쓰는 이름(본기·여기)을 표에 그대로 내면
#: 그건 풀이 없는 어려운 말입니다 — 예순 장 가운데 열둘이 그랬습니다.
ROOT_WORD = {"본기": "곧바로 닿음", "여기": "깊이 한 겹", "없음": "안 닿음"}


@lru_cache(maxsize=1)
def table() -> dict:
    raw = json.loads((SEED / "dict.json").read_text("utf-8"))
    return {k: v for k, v in raw.items() if k != "_"}


def _seat_kind(gan: str, ji: str) -> str:
    """일간이 일지를 보는 결 — 오행 상생상극에서 **계산으로** 나옵니다."""
    me, under = ELEMENT_OF_GAN[gan], ELEMENT_OF_JI[ji]
    if me == under:
        return "같음"
    if GENERATED_BY[me] == under:
        return "낳음"
    if GENERATES[me] == under:
        return "낳아줌"
    if CONTROLS[me] == under:
        return "누름"
    if CONTROLLED_BY[me] == under:
        return "눌림"
    raise DictError("오행 관계를 못 가렸소: %s%s" % (gan, ji))


def sixty() -> list:
    """예순 갑자. 천간 열과 지지 열둘이 짝을 맞춰 도는 순서 그대로."""
    return ["%s%s" % (GAN[i % 10], JI[i % 12]) for i in range(60)]


@lru_cache(maxsize=1)
def _order() -> dict:
    """
    예순 장을 **한 번에** 세워 두는 자리.

    ★ 순위는 한 장만 보고는 못 냅니다. 「예순 가운데 몇 번째로 흔한가」는
      예순을 다 세어야 나오는 값이라, 여기서 한 벌 만들어 나눠 씁니다
      (자리마다 제 손으로 세면 두 벌이 됩니다 — 이 집이 완료율에서 겪은
      그 자리요).
    """
    gzs = sixty()
    t = rarity_mod.table()
    cells = t.get("ilju") or {}
    missing = [g for g in gzs if g not in cells]
    if missing:
        raise DictError("인구 표에 없는 일주: %s" % missing[:3])
    n = {g: cells[g]["n"] for g in gzs}
    # 명수가 같으면 갑자 순서로 가릅니다 — 같은 값에 같은 순위를 두면
    # 「예순 가운데 몇째」가 예순 가지가 안 됩니다.
    rank = {g: i + 1 for i, g in enumerate(
        sorted(gzs, key=lambda g: (-n[g], gzs.index(g))))}
    gan_nth: dict = {}
    ji_nth: dict = {}
    gm_nth: dict = {}
    seen_gan: dict = {}
    seen_ji: dict = {}
    seen_gm: dict = {}
    for g in gzs:
        gan, ji = g[0], g[1]
        gm = sinsal_mod.gongmang(gan, ji)
        seen_gan[gan] = seen_gan.get(gan, 0) + 1
        seen_ji[ji] = seen_ji.get(ji, 0) + 1
        seen_gm[gm] = seen_gm.get(gm, 0) + 1
        gan_nth[g] = seen_gan[gan]
        ji_nth[g] = seen_ji[ji]
        gm_nth[g] = seen_gm[gm]
    # ★ 형제 안에서의 순위도 여기서 한 벌 세웁니다. 같은 일간 여섯 · 같은
    #   일지 다섯 안에서 몇째로 흔한가 — 새 명리가 아니라 같은 표를 다시
    #   세는 것이고, 장마다 대 볼 수 있는 수가 넷 더 섭니다.
    gan_rank: dict = {}
    ji_rank: dict = {}
    gan_top: dict = {}
    ji_top: dict = {}
    for key, bag in (("gan", gan_rank), ("ji", ji_rank)):
        groups: dict = {}
        for g in gzs:
            groups.setdefault(g[0] if key == "gan" else g[1], []).append(g)
        for head, members in groups.items():
            members = sorted(members, key=lambda g: (-n[g], gzs.index(g)))
            for i, g in enumerate(members):
                bag[g] = i + 1
            (gan_top if key == "gan" else ji_top)[head] = members[0]
    return {"gzs": gzs, "n": n, "rank": rank,
            "top": max(n.values()), "bottom": min(n.values()),
            "sample": t["sample"], "gan_nth": gan_nth, "ji_nth": ji_nth,
            "gm_nth": gm_nth, "gan_rank": gan_rank, "ji_rank": ji_rank,
            "gan_top": gan_top, "ji_top": ji_top}


def _root(gan: str, hidden: list) -> str:
    """
    통근 — 일간이 발밑에 뿌리를 내렸는가.

    ★ 이 집이 이미 쓰는 자입니다 (`terms.MEANING['통근']` · features 의 힘 셈).
      새 규칙이 아니라 **같은 규칙을 사전에서도 보이는** 것입니다.
    """
    me = ELEMENT_OF_GAN[gan]
    if ELEMENT_OF_GAN[hidden[0][0]] == me:
        return "본기"
    if any(ELEMENT_OF_GAN[g] == me for g, _ in hidden[1:]):
        return "여기"
    return "없음"


def _marks(gz: str, gan: str, ji: str) -> list:
    """
    일주 **둘로만** 서는 이름. 나머지 여섯 글자를 봐야 하는 것은 안 냅니다.

    ★ 표는 `engine/sinsal` 한 벌에서 받습니다. 여기서 다시 적으면 두 벌이
      되고, 두 벌이 되면 리포트와 사전이 다른 말을 합니다.
    """
    out = []
    if sinsal_mod.YANGIN.get(gan) == ji:
        out.append("양인")
    if sinsal_mod.HONGYEOM.get(gan) == ji:
        out.append("홍염")
    if gz in sinsal_mod.GWAEGANG:
        out.append("괴강")
    if gz in sinsal_mod.BAEKHO:
        out.append("백호")
    return out


def ilju_facts(gz: str) -> dict:
    """일주 한 자리의 **센 값**. 이 장에만 있는 수가 넷 이상 서야 합니다."""
    o = _order()
    if gz not in o["n"]:
        raise DictError("예순 갑자에 없는 일주요: %r" % (gz,))
    gan, ji = gz[0], gz[1]
    hidden = HIDDEN[ji]
    hidden_gan = hidden[0][0]
    n = o["n"][gz]
    group = sinsal_mod.SAMHAP_OF.get(ji)
    if not group:
        raise DictError("삼합 묶음에 없는 지지요: %r" % (ji,))
    return {
        "gz": gz,
        "gan": gan,
        "gan_sound": GAN_SOUND[gan],
        "gan_el": ELEMENT_OF_GAN[gan],
        "gan_yy": YY_WORD[YIN_YANG[gan]],
        "ji": ji,
        "ji_sound": JI_SOUND[ji],
        "ji_el": ELEMENT_OF_JI[ji],
        "ji_hidden": hidden_gan,
        "hidden": hidden,
        # 발밑에 든 글자를 **다** 십신으로 셈한 것 — 예순 장이 다 다릅니다.
        "hidden_tg": [(g, w, ten_god(g, gan)) for g, w in hidden],
        # 일지 십신 — features._ten_gods 와 **같은 자**로 셉니다.
        "ji_tengod": ten_god(hidden_gan, gan),
        "seat": _seat_kind(gan, ji),
        "root": _root(gan, hidden),
        "marks": _marks(gz, gan, ji),
        "gongmang": sinsal_mod.gongmang(gan, ji),
        "chung": CHUNG[ji],
        "hap": HAP.get(ji),
        "wonjin": sinsal_mod.WONJIN[ji],
        "samhap": group,
        "samhap_of": dict(sinsal_mod.SAMHAP[group]),
        # ── 이 장에만 있는 수 ───────────────────────────────────────
        "idx": o["gzs"].index(gz) + 1,
        "rank": o["rank"][gz],
        "n": n,
        "gap": o["top"] - n,
        "over": n - o["bottom"],
        "gan_nth": o["gan_nth"][gz],
        "ji_nth": o["ji_nth"][gz],
        "gm_nth": o["gm_nth"][gz],
        "tg_group": TEN_GOD_GROUP[ten_god(hidden_gan, gan)],
        "gan_kin": [g for g in o["gzs"] if g[0] == gan and g != gz],
        "ji_kin": [g for g in o["gzs"] if g[1] == ji and g != gz],
        "gan_rank": o["gan_rank"][gz],
        "ji_rank": o["ji_rank"][gz],
        "gan_top": o["gan_top"][gan],
        "gan_top_n": o["n"][o["gan_top"][gan]],
        "ji_top": o["ji_top"][ji],
        "ji_top_n": o["n"][o["ji_top"][ji]],
        "per10k": round(n / o["sample"] * 10000),
        "sample": o["sample"],
        "slug": "%s%s" % (GAN_SOUND[gan], JI_SOUND[ji]),
    }


def _row(key: str, value: str) -> str:
    return ('<div class="r"><span class="k">%s</span>'
            '<span class="v">%s</span></div>'
            % (_html.escape(key), value))


def _band(rank: int) -> dict:
    for b in table()["BAND"]:
        if rank <= b["upto"]:
            return b
    raise DictError("순위가 예순을 넘었소: %d" % rank)


def _hidden_say(f: dict) -> str:
    """지장간을 **가중치째** 적습니다 — 이 집이 실제로 세는 값입니다."""
    return " · ".join("%s %g" % (g, w) for g, w in f["hidden"])


def _hidden_tg_say(f: dict) -> str:
    """
    발밑에 든 글자를 **다** 십신으로 셈해 적습니다.

    ★ 예순 장이 여기서 전부 갈립니다 — (일간 × 일지) 짝이라 겹치는 장이
      없습니다. 그러면서 새 규칙이 아닙니다: `features` 가 힘을 셀 때 쓰는
      바로 그 지장간 표(`HIDDEN`)와 십신 자(`ten_god`)입니다.
    """
    return " · ".join("<b>%s</b>(%s)" % (g, tg) for g, _, tg in f["hidden_tg"])


def _first(say: str) -> str:
    """
    한 문장만.

    ★ 천간·지지의 **일반 설명**은 제 장이 따로 설 자리입니다 (docs/44 의
      기둥·묶음·잎). 일주 장에 통째로 실으면 같은 일지를 딛은 다섯 장이
      그 대문만으로 닮아 버립니다 — 재보니 닮은 짝 상위 셋이 전부 같은
      일지였습니다(70.4% · 69.6% · 69.3%).

      그러니 여기서는 **한 줄만 가리키고** 나머지는 그 글자의 장으로
      보냅니다. 사전에서는 그게 맞습니다 — 되풀이는 손님에게도 짐입니다.
    """
    head = say.split(". ", 1)[0]
    return head if head.endswith(".") else head + "."


def _deep_tg(f: dict) -> list:
    """
    **숨은** 글자의 십신만. 본기는 위에서 이미 한 단을 받았습니다.

    ★ 같은 말을 두 번 하지 않습니다 — 「센 값과 문장이 같은 말을 하게
      두기」 (CLAUDE.md). 본기 십신은 ④단이 맡고, 여기는 겉에 안 보이는
      것만 폅니다.
    """
    out = []
    for _, _, tg in f["hidden_tg"][1:]:
        if tg not in out:
            out.append(tg)
    return out


def _n(v: int) -> str:
    return format(v, ",")


def _kin_top(f: dict, spot: dict) -> str:
    """형제 가운데 으뜸 — 자기 자신이면 그렇게 말합니다."""
    me_gan = f["gan_top"] == f["gz"]
    me_ji = f["ji_top"] == f["gz"]
    key = ("kin_top_both" if me_gan and me_ji else
           "kin_top_gan" if me_gan else
           "kin_top_ji" if me_ji else "kin_top")
    return spot[key].format(**f)


#: 사전의 주소 한 벌. 화면과 라우터가 제 손으로 짜 맞추면 두 벌이 됩니다.
BASE = "/사주사전"


def term_href(word: str) -> str:
    """
    그 말이 실린 자리. 풀이표에 없는 말은 안 잇습니다 (빈 값).

    ★ 낱말마다 한 장이 아니라 **용어집 한 장의 앵커**입니다. 재 보니 한
      항목이 평균 69자였습니다 — 쉰여섯 개의 얄팍한 장은 유사문서가 아니라
      집 전체를 낮추는 짐입니다 (docs/44 §2 · `tools/dict_same.py`).
      낱말이 제 셈을 들고 설 만큼 자라면 그때 장으로 올립니다.
    """
    return "%s/용어#%s" % (BASE, word) if word in terms_mod.MEANING else ""


def ilju_href(gz: str) -> str:
    """일주 한 장의 주소. 예순 갑자에 없으면 터뜨립니다."""
    return "%s/일주/%s" % (BASE, ilju_facts(gz)["slug"])


def _kin_links(gzs: list) -> str:
    """형제 일주를 서로 잇습니다 — 묶음 안을 돌아볼 길이 없으면 잎은 고아요."""
    return " · ".join('<a class="gt" href="%s">%s</a>' % (ilju_href(g), g)
                      for g in gzs)


def ilju_page(gz: str) -> dict:
    """
    일주 한 장.

    ★ 제목에도 **센 값**을 넣습니다 (docs/44 §2 규칙 4). 「병신일주 특징」
      처럼 낱말만 바꾼 제목이면 예순 장이 한 장으로 접힙니다.
    """
    f = ilju_facts(gz)
    T = table()
    seat = T["SEAT"][f["seat"]]
    band = _band(f["rank"])
    spot = T["SPOT"]
    el_gan, el_ji = EL_WORD[f["gan_el"]], EL_WORD[f["ji_el"]]

    count = (
        '<div class="calc">'
        + _row("갑자 순번", "예순 가운데 <b>%d번째</b>" % f["idx"])
        + _row("일간", "<b>%s</b> · %s · %s(%s)"
               % (f["gan"], f["gan_sound"], el_gan, f["gan_yy"]))
        + _row("일지", "<b>%s</b> · %s · %s" % (f["ji"], f["ji_sound"], el_ji))
        + _row("일지 속 글자", _hidden_say(f))
        # ★ 조사는 `bank.josa_hanja` — 한자는 **읽는 소리**로 받침을 봅니다.
        #   「辛 로 셈」 이 나가던 자리요 (辛 은 「신」이라 「辛으로」).
        + _row("일지 십신", "<b>%s</b> (속의 으뜸 글자 %s 셈)"
               % (f["ji_tengod"],
                  bank_mod.josa_hanja(f["ji_hidden"], "으로", "로")))
        + _row("앉은 결", "%s 아래 %s — <b>%s</b>" % (el_gan, el_ji, seat["name"]))
        + _row("뿌리", "<b>%s</b>" % ROOT_WORD[f["root"]])
        + _row("공망", "<b>%s</b>" % f["gongmang"])
        + _row("부딪히는 글자", "<b>%s</b>%s · 원진 %s"
               % (f["chung"], (" · 짝 %s" % f["hap"]) if f["hap"] else "",
                  f["wonjin"]))
        + _row("셋이 모이는 짝(삼합)", "%s · 도화 %s · 역마 %s · 화개 %s"
               % (f["samhap"], f["samhap_of"]["도화"],
                  f["samhap_of"]["역마"], f["samhap_of"]["화개"]))
        + (_row("일주로 서는 이름", "<b>%s</b>" % " · ".join(f["marks"]))
           if f["marks"] else "")
        + _row("표본 %s명 중" % _n(f["sample"]),
               "<b>%s명</b> · 흔한 순서로 <b>%d위</b>" % (_n(f["n"]), f["rank"]))
        + "</div>")

    said = (
        # ① 일간 — 한 줄만. 나머지는 그 글자의 장으로
        #    ★ 일지의 일반 설명은 여기서 **뺐습니다.** 지지에 건 단이 넉 단
        #      이어서, 같은 일지를 딛은 다섯 장이 그것만으로 닮았습니다.
        #      표에 「巳 · 사 · 불」 이 이미 서 있고, 자세한 것은 그 글자의
        #      장이 할 말이오.
        '<p class="tale">%s</p>' % _first(T["GAN"][f["gan"]])
        # ③ 앉은 결 — 오행 관계 다섯 갈래
        #    ★ 조사를 손으로 박지 않습니다 (CLAUDE.md). 「기미(己未)은」 이
        #      나갔던 자리요 — 한자는 **읽는 소리**로 받침을 봅니다.
        + '<p class="tale">%s %s</p>'
          % (T["SEAT_LEAD"].format(
                 name="%s%s" % (f["gan_sound"], f["ji_sound"]), gz=f["gz"],
                 은=bank_mod.josa_hanja(f["ji"], "은", "는")[1:]),
             seat["say"])
        # ④ 십신 — 열 갈래 + 뒤 토막은 일간 오행 × 십신 묶음 (스물다섯 칸)
        + '<p class="tale">%s %s</p>'
          % (T["TENGOD"][f["ji_tengod"]],
             T["TGEL"][f["gan_el"]][f["tg_group"]])
        # ⑤ 발밑에 든 글자를 **다** 셈한 단 — 예순 장이 다 다릅니다
        + '<p class="tale">%s %s</p>'
          % (T["HID"][str(len(f["hidden"]))].format(
                 ji=f["ji"], list=_hidden_tg_say(f)),
             " ".join(T["HIDTG"][tg] for tg in _deep_tg(f)))
        # ⑥ 통근 — 뿌리가 닿는가 (세 갈래)
        + '<p class="tale">%s</p>' % T["ROOT"][f["root"]][f["gan_el"]]
        # ⑦ 부딪히는 글자 · 짝 · 원진 — 지지 열둘
        + '<p class="tale">%s %s</p>'
          % (spot["meet"].format(
                 chung=f["chung"], wonjin=f["wonjin"],
                 pair=(spot["pair_yes"].format(hap=f["hap"]) if f["hap"]
                       else spot["pair_no"])),
             _first(T["MEET"][f["ji"]]))
        # ⑧ 일주 둘로 서는 이름이 있을 때만
        + "".join('<p class="tale">%s</p>' % T["MARK"][m] for m in f["marks"])
        # ⑨ 공망 — 여섯 묶음
        + '<p class="tale">공망은 <b>%s</b>요. %s</p>'
          % (f["gongmang"], T["GONGMANG"][f["gongmang"]])
        # ⑩ 한 줄로 접는 자리 — 앉은 결 다섯 × 십신 열 = 쉰 가지.
        #    짧은 토막 열다섯으로 쉰 가지를 냅니다 (`lens_cuts` 와 같은 셈).
        + '<p class="tale">%s</p>'
          % T["FOLD"]["frame"].format(obj=T["FOLD"]["obj"][f["ji_tengod"]],
                                      verb=T["FOLD"]["verb"][f["seat"]])
        # ⑪ 형제와 대 보기 — 새 문장이 아니라 같은 표를 다시 센 값이오
        #    ★ 으뜸이 **자기 자신**일 때 「으뜸 庚辰 698명」 이라 적으면
        #      손님은 그 줄을 두 번 읽고도 무슨 말인지 모릅니다.
        + '<p class="sm">%s %s</p>' % (spot["kin"].format(**f), _kin_top(f, spot))
        # 형제 목록 — 이 장에서만 나오는 묶음이고, 뒤에 링크가 될 자리요
        + '<p class="sm">%s</p>'
          % spot["kin_list"].format(gan_list=_kin_links(f["gan_kin"]),
                                    ji_list=_kin_links(f["ji_kin"]))
        # ⑫ 자리 짚기 — 틀은 걷고 **이 장에만 있는 수**만 남깁니다
        + '<p class="sm">%s</p>' % spot["mark"].format(**f)
        # ⑪ 인구 — 순위 다섯 칸. 수는 여기서 싣습니다
        + '<p class="bite">%s</p>'
          % band["say"].format(sample=_n(f["sample"]), n=_n(f["n"]),
                               per10k=_n(f["per10k"]), rank=f["rank"],
                               gap=_n(f["gap"]), over=_n(f["over"]))
        # ⑫ 틀릴 조건 — **두 축**으로 (engine/depth 와 같은 규칙)
        #    ★ 처음에는 오행 다섯으로 갈랐는데, 다섯이면 여는 줄이 예순 장의
        #      5.9%를 먹어 최다 점유 문턱(2%)을 넘었습니다. 지지 열둘로 옮기니
        #      이번엔 **같은 일지를 딛은 다섯 장**이 닮았습니다(70%) — 지지에
        #      건 단이 넉 단이었기 때문이오. 그래서 틀릴 조건은 일간과 일지를
        #      **둘 다** 냅니다. 뜻으로도 그게 맞소 — 일간이 모자란 것과
        #      일지가 무너지는 자리는 다른 조건이오.
        + '<p class="tale">%s %s %s</p>'
          % (T["COUNTER"]["JI"][f["ji"]], T["COUNTER"]["GAN"][f["gan"]], ""))

    nxt = ('<p class="sm">%s <b>%s</b> · <b>%s</b> · <b>%s</b> · <b>%s</b></p>'
           % (spot["next"], f["gan"], f["ji"], f["ji_tengod"], f["gongmang"]))

    # ★ 사전에서는 괄호로 풀지 않고 **그 말의 장으로 잇습니다** — 까닭은
    #   `terms.link` 머리말에. 예순 장에 똑같이 깔리던 197자가 여기서
    #   빠집니다.
    seen: set = set()
    html = terms_mod.link(count + said + nxt, term_href, seen)
    return {
        "id": "ilju/%s" % f["slug"],
        "gz": f["gz"],
        "slug": f["slug"],
        "title": "%s%s일주 — %s 일지 · 공망 %s · 예순 중 %d위"
                 % (f["gan_sound"], f["ji_sound"], f["ji_tengod"],
                    f["gongmang"], f["rank"]),
        "lead": "%s 일간이 %s 위에 앉은 %s. 표본 %s명에 %s명."
                % (el_gan, el_ji, seat["name"], _n(f["sample"]), _n(f["n"])),
        "source": "일간 %s · 일지 %s(속의 으뜸 %s) · 십신 %s · 갑자 %d번째 "
                  "〔자평 명리 · 십신〕"
                  % (f["gan"], f["ji"], f["ji_hidden"], f["ji_tengod"], f["idx"]),
        "html": guard.enforce(html, {"cut": "dict:ilju:%s" % f["gz"]}),
        "facts": f,
        # 이 장에만 나오는 수 — 자(tools/dict_same)가 이것을 셉니다.
        "own": ["%d번째" % f["idx"], "%d위" % f["rank"], "%s명" % _n(f["n"]),
                "%s 여섯 중 %d" % (f["gan"], f["gan_nth"]),
                "%s 다섯 중 %d" % (f["ji"], f["ji_nth"]),
                "%s 열 중 %d" % (f["gongmang"], f["gm_nth"])],
    }


def term_page(word: str) -> dict:
    """용어 한 장. 풀이는 `terms` 한 자리에서 받습니다 — 두 벌로 쓰지 않습니다."""
    mean = terms_mod.MEANING.get(word)
    if not mean:
        raise DictError("풀이표에 없는 말이오: %r" % (word,))
    pic = terms_mod.PICTURE.get(word) or ""
    html = ('<div class="calc">%s</div>' % _row("한 줄 풀이", _html.escape(mean))
            + ('<p class="tale">%s</p>' % pic if pic else ""))
    return {
        "id": "term/%s" % word,
        "slug": word,
        "title": "%s — %s" % (word, mean),
        "lead": mean,
        "source": "풀이표 〔engine/terms〕",
        "html": guard.enforce(html, {"cut": "dict:term:%s" % word}),
        "own": [word, mean[:8]],
    }


def index() -> dict:
    """기둥이 쓸 목록. 무엇이 몇 장 열렸는지 **세어서** 냅니다."""
    iljus = [ilju_facts(gz) for gz in sixty()]
    return {
        "ilju": [{"gz": x["gz"], "slug": x["slug"], "tengod": x["ji_tengod"],
                  "rank": x["rank"], "n": x["n"]}
                 for x in iljus],
        "term": sorted(terms_mod.MEANING),
        "counts": {"ilju": len(iljus), "term": len(terms_mod.MEANING)},
    }
