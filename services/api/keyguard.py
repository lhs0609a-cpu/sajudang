"""
영업 정보의 문지기 — 한 자리에서.

★ 왜 한 자리인가

  퍼널(`/v1/funnel`)과 관리자(`/v1/admin/*`)는 둘 다 **영업 정보**를
  냅니다. 전환율·매출·이용자 수. 아무나 읽으면 안 됩니다.

  그런데 지키는 코드가 **두 곳에 따로** 있었습니다 — events.py 는
  함수 안에서 직접 비교하고, admin.py 는 `_guard()` 를 따로 두었습니다.
  같은 일을 두 곳에서 하면 한쪽만 고치는 날이 옵니다. 그날 열린 쪽은
  아무도 모릅니다.

★ 없으면 **닫습니다**

  열쇠를 안 정해 두면 503 으로 아예 닫습니다. 열어 두는 쪽이 기본이면
  언젠가 그대로 배포됩니다.

★ 시간을 안 흘립니다

  `hmac.compare_digest` 로 견줍니다. `==` 는 앞자리부터 틀리는 데까지
  걸리는 시간이 달라서, 그 차이로 열쇠를 한 자 한 자 알아낼 수
  있습니다.
"""
from __future__ import annotations

import hmac
import os

from fastapi import HTTPException

#: 퍼널과 관리자가 **같은 열쇠**를 씁니다.
#:
#: 둘을 따로 두면 하나만 걸어 두고 다른 하나는 열린 채 배포되는 날이
#: 옵니다. 어차피 둘 다 보는 사람은 한 사람입니다.
FUNNEL_KEY = os.getenv("FUNNEL_KEY", "").strip()


def require_key(key: str | None) -> None:
    """열쇠가 맞지 않으면 문을 안 열어 준다."""
    if not FUNNEL_KEY:
        raise HTTPException(503, "FUNNEL_KEY 가 설정되지 않았습니다.")
    if not key or not hmac.compare_digest(key, FUNNEL_KEY):
        raise HTTPException(401, "열쇠가 맞지 않습니다.")
