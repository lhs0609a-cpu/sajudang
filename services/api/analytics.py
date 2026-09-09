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
from datetime import datetime, timezone, timedelta
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
    "b1", "b2", "b3", "c1", "c7", "d0", "d1", "d1b", "d2", "d3",
    # 그 밖
    "daily", "me", "relay", "share", "s1", "s2",
}

SERVER_EVENTS = {"payment_approved", "payment_refunded"}

EVENTS = {
    "entry_context", "hook_skip", "reading_expand", "price_view", "checkout_blocked", "reading_mismatch",
    "experiment_exposed",
    "web_lcp", "web_inp", "web_cls",
    "flow_started", "practice_saved", "chart_completed",
    "screen",          # 화면에 닿았다
    "hook_shown",      # 훅 한 단이 열렸다
    "hook_answer",     # 훅 한 단에 답했다
    "free_shown",      # 무료 구간을 봤다
    "free_beat",       # 무료 구간 중간에 답했다 — 여기서 리듬이 끊깁니다
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


def _clean(ev: dict, *, server: bool = False) -> Optional[dict]:
    name = str(ev.get("name") or "")
    if name not in EVENTS and not (server and name in SERVER_EVENTS):
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
    if name == "experiment_exposed":
        import experiments
        if screen != "a1" or out.get("n") != experiments.ID:
            return None
        out["stage"] = experiments.variant(sid)
    return out


def record(events: Iterable[dict], *, server: bool = False) -> int:
    """받아 적는다. 어떤 이유로든 실패해도 예외를 밖으로 내지 않는다."""
    rows = []
    for ev in list(events)[:MAX_BATCH]:
        c = _clean(ev, server=server)
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
    ("a1", "첫 화면"), ("a5", "고민 선택"), ("a3", "생년월일"),
    ("a4", "태어난 시간"), ("a6", "계산 완료"), ("a7", "무료 핵심 해석"),
    ("d0", "무료 상세 해석"), ("d1", "상품·결제"), ("d3", "서버 결제 승인"),
]


def _rows() -> list[dict]:
    if db.HAS_DB:
        import models
        from sqlalchemy import select
        with db.session() as s:
            return [
                {"name": e.name, "screen": e.screen, "sid": e.sid,
                 "stage": e.stage, "yes": e.yes, "n": e.n, "ms": e.ms, "at": e.at.isoformat()}
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


def clear() -> int:
    """
    쌓인 사건을 지운다. 배포 직후 시험분을 치우는 용도입니다.
    statement_log 는 건드리지 않습니다 — 그건 공감률의 원천 자산입니다.
    """
    n = len(_rows())
    if db.HAS_DB:
        import models
        from sqlalchemy import delete
        with db.session() as s:
            s.execute(delete(models.Event))
    elif EVENT_LOG_PATH.exists():
        EVENT_LOG_PATH.unlink()
    return n


def funnel() -> dict:
    """Version 2 entry cohorts, ordered steps, seven-day conversion window.

    Browser identifiers are not unique people. Direct/legacy paths remain in
    screen totals, but cannot manufacture completion of skipped entry steps.
    """
    rows = _rows()
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=30)
    timed = []
    first_exposure = {}
    for r in rows:
        try:
            at = datetime.fromisoformat(str(r.get("at", "")).replace("Z", "+00:00"))
            if at.tzinfo is None:
                at = at.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
        if (at <= now and r.get("name") == "flow_started" and r.get("n") == 2
                and r.get("screen") == "a1" and r.get("sid")):
            sid = r["sid"]
            first_exposure[sid] = min(at, first_exposure.get(sid, at))
        if cutoff <= at <= now:
            timed.append((at, r))
    timed.sort(key=lambda item: item[0])
    cohorts, progress = {}, {}
    approved = set()
    seen = defaultdict(set)
    reached = [set() for _ in FUNNEL]
    shown, answered, yes = defaultdict(set), defaultdict(set), defaultdict(set)
    for at, r in timed:
        sid = r.get("sid")
        if not sid:
            continue
        name, screen = r.get("name"), r.get("screen")
        if name == "screen":
            seen[screen].add(sid)
        if (name == "flow_started" and screen == "a1" and r.get("n") == 2
                and sid not in cohorts and first_exposure.get(sid) == at):
            cohorts[sid] = at
            progress[sid] = 1
            reached[0].add(sid)
        if sid not in cohorts or at - cohorts[sid] > timedelta(days=7):
            continue
        if name == "payment_approved":
            approved.add(sid)
        index = progress[sid]
        if index < len(FUNNEL):
            expected = FUNNEL[index][0]
            matches = (name == "payment_approved" if expected == "d3"
                       else name == "chart_completed" if expected == "a6"
                       else name == "screen" and screen == expected)
            if matches:
                reached[index].add(sid)
                progress[sid] += 1
        stage = r.get("stage")
        if stage is not None:
            if name == "hook_shown":
                shown[stage].add(sid)
            elif name == "hook_answer" and sid in shown[stage] and sid not in answered[stage]:
                answered[stage].add(sid)
                if r.get("yes") == 1:
                    yes[stage].add(sid)
    steps, prev = [], None
    first = len(reached[0])
    for (screen, label), visitors in zip(FUNNEL, reached):
        n = len(visitors)
        steps.append({"screen": screen, "label": label, "sessions": n,
                      "from_prev": round(100*n/prev,1) if prev else None,
                      "lost": prev-n if prev is not None else None,
                      "from_top": round(100*n/first,1) if first else None})
        prev = n
    hook = []
    for stage in sorted(set(shown) | set(answered)):
        sh, an = len(shown[stage]), len(answered[stage])
        hook.append({"stage": stage, "shown": sh, "answered": an,
                     "answer_rate": round(100*an/sh,1) if sh else None,
                     "yes_rate": round(100*len(yes[stage])/an,1) if an else None})
    contexts = {}
    for at, row in timed:
        sid = row.get("sid")
        if row.get("name") == "entry_context" and sid in cohorts and cohorts[sid] <= at <= cohorts[sid] + timedelta(minutes=5):
            contexts.setdefault(sid, row)
    segments = []
    for field, labels in (("n", ["모바일", "태블릿", "데스크톱"]),
                          ("stage", ["직접·내부", "검색", "소셜", "기타 추천"]),
                          ("yes", ["신규 브라우저", "재방문 브라우저"])):
        for value, label in enumerate(labels):
            members = {sid for sid, row in contexts.items() if row.get(field) == value}
            mature = {sid for sid in members if now - cohorts[sid] >= timedelta(days=7)}
            buyers = mature & reached[-1]
            segments.append({"dimension": field, "label": label, "visitors": len(members),
                             "mature": len(mature), "buyers": len(buyers),
                             "conversion": round(100 * len(buyers) / len(mature), 2) if mature else None})
    mature = {sid for sid, at in cohorts.items() if now-at >= timedelta(days=7)}
    buyers = len(mature & approved)
    goal = {"target_percent": 5, "visitors": len(mature), "buyers": buyers,
            "conversion": round(100 * buyers / len(mature), 2) if mature else None,
            "additional_buyers_needed": max(0, (len(mature) + 19) // 20 - buyers),
            "unit": "anonymous_browser", "approval_source": "server"}
    return {"total_events": len(rows), "sessions": first, "steps": steps, "hook": hook, "goal": goal,
            "segments": segments, "context_missing": len(cohorts) - len(contexts),
            "counts": dict(Counter(r.get("name") for _, r in timed)),
            "screen_totals": {key: len(value) for key,value in seen.items()},
            "version": 2, "cohort_days": 30, "conversion_days": 7,
            "unit": "anonymous_browser", "approval_source": "server",
            "immature_sessions": sum(now-at < timedelta(days=7) for at in cohorts.values())}


def count(name: str) -> int:
    """
    사건 하나가 몇 번 일어났는가.

    ★ 주인 화면이 「지금 결제가 막히고 있는가」 를 물을 때 씁니다.
      `funnel()` 은 전체를 한 번 훑어 표를 만드는 자리라, 수 하나가
      필요할 때 그걸 부르면 표 전체를 다시 셉니다.

    ★ 화이트리스트 밖 이름은 0 입니다 — 없는 사건을 세는 척하지
      않습니다.
    """
    if name not in EVENTS:
        return 0
    return sum(1 for r in _rows() if r.get("name") == name)
