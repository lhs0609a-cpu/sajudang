# -*- coding: utf-8 -*-
"""
읽는 글 v2 — 단위가 컷이 아니라 **주장**.

    claim.py    계약. 이 집이 배운 금을 타입이 막습니다
    axes.py     주장 생산자. 축마다 한 꼴, 슬롯은 셈이 채웁니다
    render.py   말로 옮기는 층 (하오체 한 벌 · 그대 한 벌)
    compose.py  한 장의 주인. 고르기·차례·예산·처방·파는 말

v1(`engine/report` `engine/first_reading` …)은 그대로 돕니다.
게이트를 넘을 때 넘깁니다 — `tools/page_audit.py`.
"""
from .claim import Budget, Claim, ClaimError, Counted, Ground, Page, \
    Prescription, Scene           # noqa: F401
from .compose import build, locked_list    # noqa: F401
