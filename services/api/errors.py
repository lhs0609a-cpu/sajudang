"""
터진 자리 — 주인이 알 수 있게 (SHIP OS §30 · §41).

★ 왜 필요한가

  손님에게는 말투 맞춘 문장이 갑니다 — 「처리를 마치지 못했소.」
  그건 잘한 일입니다. 그런데 그 일이 **있었다는 것을 주인이 몰랐습니다.**
  로그는 Fly 에 쌓일 뿐 아무도 안 보고, 집계도 안 됩니다.

  운영 모니터링 없는 production 배포는 §44 가 금하는 것입니다.

★ 밖에 보내지 않습니다

  센트리 같은 곳에 붙이면 **요청 본문이 통째로** 남의 서버로 갑니다.
  이 집의 요청 본문에는 생년월일시가 들어 있습니다. 그래서 자체
  곳간에 **세어서** 둡니다 — 무엇이 몇 번 터졌는가, 마지막이 언제인가.

★ 무엇을 적는가

    길 · 예외 이름 · 첫 줄 · 횟수 · 처음/마지막 시각

  적지 않는 것 — 요청 본문 · 세션 · 명식 · 생년월일. 스택트레이스도
  통째로는 안 적습니다(경로에 사용자 값이 섞여 들어옵니다).
  터진 자리를 **찾을 만큼**만 남깁니다.
"""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timezone

import store

log = logging.getLogger("errors")

PREFIX = "err:"
TTL = 14 * 86400          # 두 주. 그보다 오래된 것은 이미 고쳤거나 잊혔습니다.
KEEP = 200                # 서로 다른 터진 자리 몇 가지까지 들고 있나

# 길에 박힌 값은 지웁니다 — `/v1/pay/order/sjd_a1b2…` 가 저마다 다른
# 자리로 세어지면, 같은 버그가 백 가지로 흩어져 한 번도 눈에 안 띕니다.
_IDISH = re.compile(r"/(?:[0-9a-f]{16,}|sjd_[A-Za-z0-9]+|\d+)(?=/|$)")


def _bucket(path: str) -> str:
    return _IDISH.sub("/{id}", path or "?")


def record(path: str, exc: BaseException) -> str:
    """
    한 번 터졌다고 셉니다. 돌려주는 것은 그 자리의 번호(traceId).

    ★ 기록하다 또 터지면 안 됩니다. 여기서 나는 예외는 삼킵니다 —
      오류를 적다가 오류를 내면 원래 오류가 묻힙니다.
    """
    where = _bucket(path)
    kind = type(exc).__name__
    head = (str(exc) or "").strip().splitlines()[:1]
    head = head[0][:200] if head else ""
    fp = hashlib.sha256(("%s|%s" % (where, kind)).encode()).hexdigest()[:12]
    now = datetime.now(timezone.utc).isoformat()
    try:
        row = store.get_json(PREFIX + fp) or {
            "id": fp, "path": where, "kind": kind, "first": now, "count": 0}
        row.update(last=now, count=int(row.get("count", 0)) + 1, message=head)
        store.set_json(PREFIX + fp, row, ttl=TTL)
    except Exception:                                    # pragma: no cover
        log.exception("오류를 적지 못했소")
    return fp


def recent(limit: int = 50) -> list[dict]:
    rows = [v for _, v in store.scan(PREFIX) if isinstance(v, dict)]
    rows.sort(key=lambda r: r.get("last", ""), reverse=True)
    return rows[:limit]


def summary() -> dict:
    """주인 화면 한 줄 — 지금 터지고 있는가."""
    rows = recent(KEEP)
    today = datetime.now(timezone.utc).date().isoformat()
    return {
        "kinds": len(rows),
        "total": sum(int(r.get("count", 0)) for r in rows),
        "today": sum(int(r.get("count", 0)) for r in rows
                     if str(r.get("last", ""))[:10] == today),
        "worst": rows[0] if rows else None,
    }
