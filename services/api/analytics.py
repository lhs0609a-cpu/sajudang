"""
계측 — 어디서 나가는지 본다.

왜 필요한가
    초반을 고치려면 어디서 나가는지 알아야 합니다. 지금까지는
    a3 생일 입력에서 절반이 나가는지 훅 두 번째 단에서 나가는지
    알 방법이 없었습니다. 고칠 때마다 뭐가 좋아졌는지도 몰랐습니다.

★ 절대 넣지 않는 것 (docs/11 · CLAUDE.md)
    생년월일시 · 이름 · 고을 · 얼굴 · 이메일 · 전화 · IP
    chart_id 도 넣지 않습니다. 생년월일시 해시라서 같은 생일이면
    같은 값이 나옵니다 — 그 자체가 준식별자입니다.

    남기는 것은 **익명 세션 열쇠 · 화면 이름 · 사건 이름 · 몇 초**뿐입니다.
    세션 열쇠는 브라우저가 만든 난수이고 사람과 이어지지 않습니다.

★ 왜 구글 애널리틱스를 안 쓰는가
    사주 서비스의 화면 이름은 그 자체로 민감합니다("재회", "이혼").
    제3자에게 넘기지 않고 우리 서버에만 남깁니다.

저장
    DB 가 있으면 events 테이블, 없으면 JSONL(볼륨) 에 append.
    statement_log 와 같은 방식입니다.
"""
from __future__ import annotations

import json
import logging
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

import db

log = logging.getLogger("analytics")

ROOT = Path(__file__).resolve().parents[2]
EVENT_LOG_PATH = Path(os.getenv("EVENT_LOG_PATH", ROOT / "var" / "events.jsonl"))

# ── 받아 주는 것만 받는다 ──────────────────────────────────
#
# 화이트리스트입니다. 여기 없는 이름은 버립니다. 그래야 프런트에서
# 실수로 이름·생일을 event 이름에 끼워 보내도 서버가 막습니다.

SCREENS = {
    # 진입
    "a1", "a2", "a3", "a4", "a4b", "a5", "a6", "a7",
    # 진열대 · 리포트 · 결제
    "b1", "b2", "b3", "c1", "c7", "d0", "d1", "d2", "d3",
    # 그 밖
    "daily", "me", "relay", "share", "s1", "s2",
}

EVENTS = {
    "screen",          # 화면에 닿았다
    "hook_shown",      # 훅 한 단이 열렸다
    "hook_answer",     # 훅 한 단에 답했다
    "free_shown",      # 무료 구간을 봤다
    "tier_view",       # 값 고르는 화면
    "tier_pick",       # 티어를 골랐다
    "pay_start",       # 결제창으로 갔다
    "pay_done",        # 결제가 끝났다
    "pay_fail",        # 결제가 막혔다
    "relay_take",      # 릴레이로 다음 사람에게 갔다
    "relay_skip",      # 거절했다
    "share_click",     # 공유를 눌렀다
    "share_land",      # 공유 링크로 들어왔다
    "drop_guess",      # 창을 닫으려 한다 (beacon)
}

MAX_BATCH = 40                 # 한 번에 받는 사건 수
# ★ 최소 16자. 8자로 두면 "1993-05-15" 같은 생년월일이 세션 열쇠로
#   통과합니다. 우리가 만드는 열쇠는 32자입니다.
SESSION_RE = re.compile(r"^[A-Za-z0-9_-]{16,64}$")

# 사건에 딸려 오는 값 중 **숫자만** 받습니다. 문자열은 안 받습니다 —
# 문자열을 열어 두면 언젠가 거기에 이름이 실려 옵니다.
NUM_KEYS = {"stage", "ms", "n", "yes"}


def _clean(ev: dict) -> Optional[dict]:
    name = str(ev.get("name") or "")
    if name not in EVENTS:
        return None
    screen = str(ev.get("screen") or "")
    if screen not in SCREENS:
        return None
    sid = str(ev.get("sid") or "")
    if not SESSION_RE.match(sid):
        return None

    out = {
        "name": name,
        "screen": screen,
        "sid": sid,
        "at": datetime.now(timezone.utc).isoformat(),
    }
    for k in NUM_KEYS:
        v = ev.get(k)
        if v is None:
            continue
        try:
            out[k] = int(v)
        except (TypeError, ValueError):
            continue        # 숫자가 아니면 통째로 버립니다
    return out


def record(events: Iterable[dict]) -> int:
    """받아 적는다. 어떤 이유로든 실패해도 예외를 밖으로 내지 않는다."""
    rows = []
    for ev in list(events)[:MAX_BATCH]:
        c = _clean(ev)
        if c:
            rows.append(c)
    if not rows:
        return 0

    try:
        if db.HAS_DB:
            import models
            with db.session() as s:
                for r in rows:
                    s.add(models.Event(
                        name=r["name"], screen=r["screen"], sid=r["sid"],
                        stage=r.get("stage"), ms=r.get("ms"),
                        n=r.get("n"), yes=r.get("yes"),
                        at=datetime.now(timezone.utc)))
            return len(rows)

        EVENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with EVENT_LOG_PATH.open("a", encoding="utf-8") as fp:
            for r in rows:
                fp.write(json.dumps(r, ensure_ascii=False) + "\n")
        return len(rows)
    except Exception as e:                     # noqa: BLE001
        # ★ 계측 실패가 서비스를 멈춰서는 안 됩니다.
        log.warning("계측 기록 실패: %s", e)
        return 0


# ══════════════════════════════════════════════════════════
# 읽기 — 퍼널
# ══════════════════════════════════════════════════════════

# 사람이 지나가는 차례. 이 순서로 세어야 "어디서 새는지" 가 보입니다.
FUNNEL = [
    ("a1", "골목 — 첫 화면"),
    ("a2", "이름을 적다"),
    ("a3", "생년월일"),
    ("a4", "때"),
    ("a5", "고민 고르기"),
    ("a6", "여덟 글자가 서다"),
    ("a7", "도령이 말하다 (훅)"),
    ("d0", "값 없이 한 겹 더"),
    ("d1", "어디까지 볼지"),
    ("d2", "값을 치르다"),
    ("d3", "받았다"),
]


def _rows() -> list[dict]:
    if db.HAS_DB:
        import models
        from sqlalchemy import select
        with db.session() as s:
            return [
                {"name": e.name, "screen": e.screen, "sid": e.sid,
                 "stage": e.stage, "yes": e.yes}
                for e in s.execute(select(models.Event)).scalars()
            ]
    if not EVENT_LOG_PATH.exists():
        return []
    out = []
    with EVENT_LOG_PATH.open(encoding="utf-8") as fp:
        for line in fp:
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out


def funnel() -> dict:
    """
    화면별 도달 **사람 수**(세션 수). 방문 수가 아니라 사람 수라야
    "새로고침 100번" 이 숫자를 부풀리지 않습니다.
    """
    rows = _rows()
    seen: dict[str, set] = defaultdict(set)
    for r in rows:
        if r.get("name") == "screen":
            seen[r["screen"]].add(r["sid"])

    steps, prev = [], None
    for sid_, label in FUNNEL:
        n = len(seen.get(sid_, ()))
        steps.append({
            "screen": sid_, "label": label, "sessions": n,
            "from_prev": None if prev in (None, 0) else round(100.0 * n / prev, 1),
            "lost": None if prev is None else max(prev - n, 0),
        })
        prev = n

    first = steps[0]["sessions"] if steps else 0
    for st in steps:
        st["from_top"] = round(100.0 * st["sessions"] / first, 1) if first else None

    # 훅 단별 — 초반이 어디서 끊기는가
    shown = Counter()
    answered = Counter()
    yes = Counter()
    for r in rows:
        stg = r.get("stage")
        if stg is None:
            continue
        if r.get("name") == "hook_shown":
            shown[stg] += 1
        elif r.get("name") == "hook_answer":
            answered[stg] += 1
            if r.get("yes"):
                yes[stg] += 1

    hook = []
    for stg in sorted(set(shown) | set(answered)):
        sh, an = shown[stg], answered[stg]
        hook.append({
            "stage": stg, "shown": sh, "answered": an,
            "answer_rate": round(100.0 * an / sh, 1) if sh else None,
            "yes_rate": round(100.0 * yes[stg] / an, 1) if an else None,
        })

    return {
        "total_events": len(rows),
        "sessions": len({r["sid"] for r in rows if r.get("sid")}),
        "steps": steps,
        "hook": hook,
        "counts": dict(Counter(r.get("name") for r in rows)),
    }
