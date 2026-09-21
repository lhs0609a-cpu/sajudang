"""
감사기록 — 주인이 무엇을 언제 했는가 (§43 · §21 audit log).

★ 왜 필요한가

  주인은 환불을 승인하고, 자격을 손으로 열어 주고, 구독을 끊을 수
  있습니다. 전부 **돈이 움직이는 자리**입니다. 그런데 누가 언제
  무엇을 왜 했는지 남는 곳이 없었습니다.

  남지 않으면 세 가지를 못 합니다 —
    · 손님이 "환불해 달라 했는데 안 됐다" 고 할 때 대 볼 것이 없습니다
    · 주인이 실수로 누른 것을 되짚을 수 없습니다
    · 주인 자리가 뚫렸을 때 무엇이 당했는지 모릅니다

★ 무엇을 적는가 (§43)

    when / actor / type / target / before / after / reason

  `before` 와 `after` 를 함께 적습니다. 「환불했다」만 적으면 그 주문이
  그 전에 어떤 상태였는지 몰라, 두 번 눌린 것인지 한 번 눌린 것인지
  가릴 수 없습니다.

★ 무엇을 안 적는가

  손님이 누구인지는 안 적습니다. 세션 아이디도 생년월일도 chart_id 도
  넣지 않습니다 — 준식별자입니다 (CLAUDE.md). 주문번호까지입니다.
  주인 쪽은 이메일을 적습니다. 주인은 자기가 한 일에 이름을 답니다.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

import store

# 두 해. 전자상거래법이 거래 기록을 5년 보관하라 하지만 그건 **거래**
# 기록이고(주문 자체), 이건 주인 조작 기록이라 두 해로 둡니다.
TTL = 730 * 86400
PREFIX = "audit:"

# ★ 값을 안 적는 칸. 여기 적힌 이름이 before/after 에 있으면 가립니다.
REDACT = {"session_id", "chart_id", "payment_key", "billing_key",
          "customer_key", "analytics_sid", "concern"}


def _clean(d: Optional[dict]) -> dict:
    if not isinstance(d, dict):
        return {}
    return {k: v for k, v in d.items() if k not in REDACT}


def record(*, actor: str, type: str, target: str,
           before: Optional[dict] = None, after: Optional[dict] = None,
           reason: str = "") -> str:
    """
    한 줄 남깁니다. 돌려주는 것은 그 줄의 번호.

    ★ 실패해도 **부르는 쪽을 넘어뜨리지 않습니다.** 기록을 못 남겼다고
      환불이 안 되면 그건 손님에게 더 나쁜 일입니다. 다만 조용히
      지나가지도 않습니다 — 로그에 남깁니다.
    """
    now = datetime.now(timezone.utc).isoformat()
    row = {
        "id": uuid.uuid4().hex[:16], "at": now, "actor": actor or "?",
        "type": type, "target": target, "reason": reason[:300],
        "before": _clean(before), "after": _clean(after),
    }
    try:
        store.set_json(PREFIX + now + ":" + row["id"], row, ttl=TTL)
    except Exception:                          # pragma: no cover
        import logging
        logging.getLogger("audit").exception("감사기록을 못 남겼소 %s %s", type, target)
    return row["id"]


def recent(limit: int = 100, target: str = "") -> list[dict]:
    """최근 것부터. 열쇠에 시각이 들어 있어 이름순이 곧 시간순입니다."""
    rows = [v for _, v in store.scan(PREFIX) if isinstance(v, dict)]
    if target:
        rows = [r for r in rows if r.get("target") == target]
    rows.sort(key=lambda r: r.get("at", ""), reverse=True)
    return rows[:limit]
