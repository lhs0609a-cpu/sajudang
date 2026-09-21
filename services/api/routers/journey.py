"""
GET /v1/journey — 유저 항해 관제탑 (SHIP OS §18 · §42).

★ 손님은 **개발 상태가 아니라 자기 길**을 봅니다.

  주인 관제탑은 「제품이 어디까지 준비되었는가」 를 봅니다.
  이 자리는 「내가 목표까지 어디까지 왔는가」 를 봅니다.
  같은 여정 단계를 보지만 렌즈가 다릅니다 (§42).

★ 왜 서버가 셈하나

  화면이 제 손으로 「다 읽었음」 을 정하면, 값을 안 치르고도 읽은 것이
  되고 브라우저에서 고칠 수 있습니다. 자격이 정하는 칸(산 것·구독)은
  **치른 주문**이 정합니다 — `entitled_tier` 와 같은 자리를 봅니다.

★ 여기서도 누구인지는 안 내려보냅니다

  세션 아이디는 받되 되돌려 주지 않고, 생년월일·이름·chart_id 도
  응답에 싣지 않습니다. 세는 것은 **몇 개인가**뿐입니다.

★ 다음 행동은 **하나만** 냅니다 (§18)

  할 일을 여럿 늘어놓으면 손님은 하나도 안 합니다. 이 집이 「이번 주
  한 가지」 컷에서 시키는 일을 둘로 만들었다가 겪은 것과 같습니다.
"""
from __future__ import annotations

import hashlib

from fastapi import APIRouter

import store

router = APIRouter(prefix="/v1", tags=["journey"])


def _user_key(session_id: str) -> str:
    return hashlib.sha256(session_id.encode()).hexdigest()[:16]


def _paid(session_id: str) -> list:
    out = []
    for oid in store.get_json("orders:" + session_id) or []:
        o = store.get_json("order:" + oid)
        if isinstance(o, dict) and o.get("status") == "paid":
            out.append(o)
    return out


# 단계 — product-os/product.yaml 의 손님 여정과 같은 뼈대입니다.
# ★ 여기 문구는 **손님이 읽는 글**입니다. 하오체 한 벌 (docs/21).
STEPS = [
    ("chart",  "여덟 글자 세우기",  "생년월일시로 명식을 세우오."),
    ("hook",   "첫 해석 듣기",      "그대의 되풀이를 짚는 다섯 마디요."),
    ("free",   "무료 해석 읽기",    "값 없이 보는 데까지 다 읽으셨소."),
    ("paid",   "깊은 해석 열기",    "값을 치르면 근거와 대운까지 열리오."),
    ("relay",  "다음 사람 만나기",  "그대 사주가 다음 사람을 고르오."),
    ("share",  "분석지 나누기",     "한 장으로 간추려 건넬 수 있소."),
    ("return", "다시 오기",         "오늘의 일진과 회고가 기다리오."),
]

# 다음 한 걸음 — 칸마다 **하나씩**.
NEXT = {
    "chart":  ("생년월일을 적어 보시오", "/?step=a4"),
    "hook":   ("첫 해석을 들어 보시오", "/lobby"),
    "free":   ("무료 해석을 마저 읽으시오", "/pay?step=d0"),
    "paid":   ("어디까지 볼지 고르시오", "/pay?step=d1"),
    "relay":  ("다음 사람을 만나 보시오", "/relay"),
    "share":  ("분석지 한 장을 받아 보시오", "/summary"),
    "return": ("오늘의 일진을 보시오", "/daily"),
}


@router.get("/journey")
def journey(session_id: str, chart_id: str = "", read_free: bool = False) -> dict:
    """
    ★ `read_free` 만 화면이 말합니다 — 「끝까지 읽었는가」 는 서버가
      알 수 없는 것이라 손님 쪽에서 받습니다. 자격이 걸린 칸이 아니라
      거짓으로 켜도 얻는 것이 없습니다. 값이 걸린 칸(paid)은 화면
      말을 안 듣고 **치른 주문**만 봅니다.
    """
    paid = _paid(session_id)
    seals = store.get_json("seals:" + _user_key(session_id)) or []
    sub = store.get_json("sub:" + _user_key(session_id)) or {}
    relayed = bool(store.get_json("relay:" + _user_key(session_id)))
    shared = bool(store.get_json("shared:" + _user_key(session_id)))
    visits = store.get_int("visit:" + _user_key(session_id))

    done = {
        "chart": bool(chart_id),
        "hook": bool(chart_id),
        "free": bool(chart_id) and read_free,
        "paid": bool(paid) or bool(sub.get("status") == "live"),
        "relay": relayed or len(seals) > 1,
        "share": shared,
        "return": visits > 1,
    }

    rows, now_key = [], None
    for key, title, say in STEPS:
        ok = done.get(key, False)
        state = "done" if ok else ("now" if now_key is None else "lock")
        if state == "now":
            now_key = key
        rows.append({"id": key, "title": title, "say": say, "state": state})

    got = sum(1 for r in rows if r["state"] == "done")
    nxt = NEXT.get(now_key or "", None)
    return {
        "steps": rows,
        "done": got,
        "total": len(rows),
        "percent": round(100.0 * got / len(rows)),
        # 다음 한 걸음. 다 했으면 안 냅니다 — 없는 일을 시키지 않습니다.
        "next": ({"say": nxt[0], "href": nxt[1]} if nxt else None),
        # 쌓인 것. 「성취 기록」 자리입니다 (§18).
        "kept": {"readings": len(paid), "seals": len(seals),
                 "subscribed": sub.get("status") == "live"},
    }
