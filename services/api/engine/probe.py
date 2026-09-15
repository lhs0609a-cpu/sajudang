# -*- coding: utf-8 -*-
"""
확인 문항 — 리포트 앞에 묻는 행동 물음 여섯, 그리고 **맞대 보기**.

★ 왜 (2026-09-11)

  손님이 가져온 바깥 글이 날카로웠던 까닭은 사주가 아니라 **행동 증거**
  였습니다 — 「돈 되는 걸 보면 직접 하기보다 남이 하게 판을 깐다」 같은,
  그 사람이 실제로 하는 일. 우리는 생년월일과 넉 자만 받았습니다.

  자유 입력은 받지 않습니다 (개인정보가 섞이고 가드를 우회합니다 —
  CLAUDE.md). **고를 것만** 묻고, 여덟 글자가 가리키는 쪽과 하나씩
  맞댑니다.

★ 여섯 = 공통 셋 + **그 사람 척추 전용 셋** (2026-09-11)

  모두에게 같은 물음 여섯이면 날카로움이 사람마다 안 갈립니다. 공통 셋은
  사람을 가장 잘 가르는 것(끝냄 · 규칙 · 말), 나머지 셋은 **그 척추를
  시험하는** 물음입니다(seed/spine.json 의 probes). 보기마다 그 척추에
  맞춘 풀이(read)가 있어 「타고난 대로 살아온 곳이오」 같은 공통 문장을
  쓰지 않습니다.

★ 답이 한 줄과 어긋나면 **방향을 틉니다**

  척추 전용 물음이 거의 다 빗나가면, 여덟 글자가 두 번째로 미는 쪽
  (spine.alt_key)을 불러 「그대는 A 힘을 B 힘으로 쓰는 사람이오」 로
  한 줄을 다시 세웁니다. 손님이 고른 것이 결론을 바꾸는 자리입니다.

★ 판정은 셈입니다. 공통 물음은 여덟 글자가 **한쪽을 가리킬 때만**
  같다/다르다를 말하고, 센 수(「관성 0 · 신강」)를 같이 냅니다.

★ 저장하지 않습니다. 계산하고 버립니다.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from . import guard

SEED = Path(__file__).resolve().parents[3] / "seed" / "probe.json"

# 공통 셋 — 사람을 가장 잘 가르는 물음. 나머지 셋은 척추 전용.
GENERIC = ("finish", "rules", "speak")
SPINE_IDS = ("s0", "s1", "s2")


@lru_cache(maxsize=1)
def table() -> dict:
    return json.loads(SEED.read_text("utf-8"))


def _has(f, key: str) -> bool:
    return any(s.get("key") == key for s in (f.sinsal or []))


def predict(f, dim: str) -> tuple[Optional[str], str]:
    """
    여덟 글자가 이 물음에서 **어느 쪽을 가리키는가** — (보기 id 또는 None, 센 수).

    ★ 조건은 셀 수 있는 값으로만 씁니다. 차례가 곧 우선입니다.
    """
    g = f.ten_gods
    if dim == "finish":
        if f.gwan == 0 and f.sik >= 1:
            return "start", "관성 0 · 식상 %d" % f.sik
        if f.gwan >= 2 and f.gwan >= f.sik:
            return "finish", "관성 %d · 식상 %d" % (f.gwan, f.sik)
        if f.sik >= f.gwan + 2:
            return "start", "식상 %d · 관성 %d" % (f.sik, f.gwan)
        return "even", "식상 %d · 관성 %d" % (f.sik, f.gwan)
    if dim == "money":
        if f.jae == 0 and f.inn >= 2:
            return "pass", "재성 0 · 인성 %d" % f.inn
        if f.sik >= 2 and f.jae >= 1 and g.get("편재", 0) >= 1:
            return "build", "식상 %d → 재성 %d · 편재 %d" % (f.sik, f.jae, g["편재"])
        if f.inn >= 2:
            return "why", "인성 %d" % f.inn
        if f.bi >= 2 and f.strength == "신강":
            return "do", "비겁 %d · 신강" % f.bi
        return None, "재성 %d · 식상 %d · 인성 %d" % (f.jae, f.sik, f.inn)
    if dim == "rules":
        if f.gwan == 0 and f.strength == "신강":
            return "mine", "관성 0 · 신강"
        if f.gwan >= 2:
            return "ok", "관성 %d" % f.gwan
        if g.get("상관", 0) >= 1 and f.gwan <= 1:
            return "tight", "상관 %d · 관성 %d" % (g["상관"], f.gwan)
        return None, "관성 %d" % f.gwan
    if dim == "speak":
        if g.get("상관", 0) >= 2 or f.sik >= 3:
            return "now", "상관 %d · 식상 %d" % (g.get("상관", 0), f.sik)
        if f.inn >= 2 or f.gwan >= 2:
            return "hold", "인성 %d · 관성 %d" % (f.inn, f.gwan)
        if g.get("식신", 0) >= 1 and g.get("상관", 0) == 0:
            return "later", "식신 %d · 상관 0" % g["식신"]
        return None, "식상 %d" % f.sik
    if dim == "load":
        if f.bi >= 2 and f.strength == "신강":
            return "self", "비겁 %d · 신강" % f.bi
        if f.strength == "신약" and f.inn >= 1:
            return "ask", "신약 · 인성 %d" % f.inn
        if f.jae >= 1 and f.gwan >= 1:
            return "split", "재성 %d · 관성 %d" % (f.jae, f.gwan)
        return None, "비겁 %d · %s" % (f.bi, f.strength)
    if dim == "rest":
        if _has(f, "hwagae") or f.inn >= 3:
            return "alone", "화개" if _has(f, "hwagae") else "인성 %d" % f.inn
        if _has(f, "dohwa") or f.bi >= 3:
            return "people", "도화" if _has(f, "dohwa") else "비겁 %d" % f.bi
        if f.gwan == 0 and f.strength == "신강" and f.sik >= 2:
            return "work", "관성 0 · 신강 · 식상 %d" % f.sik
        return None, "인성 %d · 비겁 %d" % (f.inn, f.bi)
    return None, ""


def _spine_probes(f) -> list:
    """이 사람 척추 전용 물음 셋. 명식이 없으면 빈 목록."""
    if f is None:
        return []
    from . import spine as spine_mod
    return list((spine_mod.table()["spines"].get(spine_mod.key(f)) or {})
                .get("probes") or [])[:3]


def spec(f=None) -> dict:
    """
    화면이 그릴 물음 — 공통 셋 + 척추 전용 셋.
    판정 규칙(hit)과 풀이(read)는 안 내려보냅니다 — 분기표입니다.
    """
    T = table()
    dims = {d["id"]: d for d in T["dims"]}
    items = [{"id": k, "q": dims[k]["q"],
              "options": [{"id": o, "label": v["label"]}
                          for o, v in dims[k]["options"].items()]}
             for k in GENERIC]
    for sid, p in zip(SPINE_IDS, _spine_probes(f)):
        items.append({"id": sid, "q": p["q"],
                      "options": [{"id": str(i), "label": o}
                                  for i, o in enumerate(p["opts"])]})
    return {"id": "probe", "title": T["ask_title"], "why": T["ask_why"],
            "items": items}


def clean(answers, f=None) -> dict:
    """모르는 물음·보기는 버립니다 — 목록에 있는 것만 판정합니다."""
    if not isinstance(answers, dict):
        return {}
    dims = {d["id"]: d for d in table()["dims"]}
    sp = _spine_probes(f)
    out = {}
    for k, v in answers.items():
        v = str(v)
        if k in dims and v in dims[k]["options"]:
            out[k] = v
        elif k in SPINE_IDS and SPINE_IDS.index(k) < len(sp) \
                and v.isdigit() and int(v) < len(sp[SPINE_IDS.index(k)]["opts"]):
            out[k] = v
    return out


def turn_key(f, payload, sp=None) -> Optional[str]:
    """
    답이 한 줄과 어긋나 **방향을 트는가** — 틀면 두 번째 후보 척추의 열쇠.

    ★ 척추 전용 물음을 둘 넘게 답했고, 그중 맞은 것이 절반이 안 되면 틉니다.
      리포트는 이 열쇠로 장면과 「이번 주 한 가지」 를 **그 사람답게** 바꿉니다.
      「그대의 답을 먼저 믿으시오」 라 해 놓고 아무것도 안 바꾸면 말뿐이오.
    """
    ans = clean((payload or {}).get("answers") if isinstance(payload, dict) else None, f)
    sprobes = _spine_probes(f)
    got = [(int(ans[sid]), sprobes[i]) for i, sid in enumerate(SPINE_IDS)
           if sid in ans and i < len(sprobes)]
    if len(got) < 2:
        return None
    hits = sum(1 for k, p in got if k in (p.get("hit") or []))
    if hits * 2 >= len(got):
        return None
    from . import spine as spine_mod
    ak = spine_mod.alt_key(f)
    T = spine_mod.table()
    if ak in T["spines"] and (T.get("short") or {}).get(ak):
        return ak
    return None


def _jo(word: str, with_b: str, without: str) -> str:
    ch = word[-1] if word else ""
    has = "가" <= ch <= "힣" and (ord(ch) - 0xAC00) % 28 != 0
    return word + (with_b if has else without)


def cut(f, payload, sp=None) -> Optional[dict]:
    """
    고른 것과 여덟 글자를 맞댄 컷. 답이 없으면 None.

    sp  spine.read(f) — 한 줄 이름 · 짧은 힘(short) · 열쇠. 글만 주면 이름만 씁니다.
    ★ 무료입니다 — 묻고 나서 답을 값 뒤에 두면 받아 내는 것이오.
    """
    if isinstance(sp, str):
        sp = {"name": sp}
    sp = sp or {}
    ans = clean((payload or {}).get("answers") if isinstance(payload, dict) else None, f)
    if not ans:
        return None
    T = table()
    dims = {d["id"]: d for d in T["dims"]}
    parts = ['<p class="tale">%s</p>' % T["intro"]]
    same = diff = judged = 0
    ev = []
    # ── 공통 물음 — 여덟 글자가 가리키는 쪽과 맞댄다 ──
    for d in T["dims"]:
        pick = ans.get(d["id"])
        if not pick:
            continue
        opt = dims[d["id"]]["options"]
        pred, why = predict(f, d["id"])
        parts.append('<p class="q">%s</p>' % d["q"])
        parts.append('<p class="tale">%s</p>' % T["said"].format(label=opt[pick]["label"]))
        if pred is None:
            parts.append('<p class="hit">%s</p>' % T["none"].format(why=why))
            ev.append("%s ?" % d["id"])
            continue
        judged += 1
        if pred == pick:
            same += 1
            parts.append('<p class="hit">%s</p>' % T["same"].format(why=why))
            ev.append("%s =" % d["id"])
        else:
            diff += 1
            parts.append('<p class="hit">%s</p>' % T["diff"].format(
                pred=opt[pred]["desc"], pick=opt[pick]["desc"], why=why))
            ev.append("%s ≠" % d["id"])
    # ── 척추 전용 물음 — 보기마다 그 척추에 맞춘 풀이 ──
    sprobes = _spine_probes(f)
    s_ans = s_hit = 0
    for i, sid in enumerate(SPINE_IDS):
        pick = ans.get(sid)
        if pick is None or i >= len(sprobes):
            continue
        p, k = sprobes[i], int(pick)
        s_ans += 1
        hit = k in (p.get("hit") or [])
        s_hit += 1 if hit else 0
        parts.append('<p class="q">%s</p>' % p["q"])
        parts.append('<p class="tale">%s</p>' % T["said"].format(label=p["opts"][k]))
        read = (p.get("read") or [""] * 4)[k]
        if read:
            parts.append('<p class="hit">%s</p>' % read)
        ev.append("%s %s" % (sid, "=" if hit else "≠"))
    # ── 모아 말하기 · 방향 틀기 ──
    n_all, same_all = judged + s_ans, same + s_hit
    diff_all = n_all - same_all
    S = T["sum"]
    name = sp.get("name") or "그 한 줄"
    if n_all < 3:
        tail = S["few"].format(n=n_all)
    elif same_all * 3 >= n_all * 2:
        tail = S["hi"].format(n=n_all, same=same_all, spine=name)
    elif diff_all * 3 >= n_all * 2:
        tail = S["lo"].format(n=n_all, diff=diff_all)
    else:
        tail = S["mid"].format(n=n_all, same=same_all, diff=diff_all)
    parts.append('<p class="tale">%s</p>' % tail)
    if s_ans >= 2 and s_hit * 2 < s_ans and sp.get("short"):
        from . import spine as spine_mod
        ak = spine_mod.alt_key(f)
        alt = spine_mod.table()["spines"].get(ak) or {}
        alt_short = (spine_mod.table().get("short") or {}).get(ak)
        if alt and alt_short:
            parts.append(
                '<p class="bite">그 사람만 보는 물음 %d개 가운데 %d개만 한 줄과 '
                '맞았소. 여덟 글자는 「%s」이라 하지만, 그대의 답은 두 번째로 센 '
                '%s 쪽 — 「%s」에 더 가깝소. 그러니 그대는 <b>%s %s 쓰는 '
                '사람</b>이오.</p>'
                % (s_ans, s_hit, name, ak.split(">")[0], alt.get("name", ""),
                   _jo(sp["short"], "을", "를"), _jo(alt_short, "으로", "로")))
    return {
        "id": "probe", "title": T["title"],
        "source": ("물음 %d개 · 여덟 글자와 같음 %d · 다름 %d — 고르신 것을 "
                   "여덟 글자가 가리키는 쪽과 맞댔소 〔자평 명리 · 십신〕"
                   % (len(ans), same_all, diff_all)),
        "html": guard.enforce("".join(parts), {"cut": "probe"}),
        "min_level": 0,
        "statement_id": "probe:%s:%s" % (sp.get("id", ""), ",".join(ev)),
    }
