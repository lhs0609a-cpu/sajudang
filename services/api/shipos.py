"""
SHIP OS · 단일 진실 — 상태와 수치를 **여기서만** 셉니다.

    MASTER_BUILD_SHIP_OS.md  §17 관제탑 · §34 배선 · §35 완료율 · §36 릴리스 게이트 · §45 검산

★ 왜 한 파일인가 (§1.1 · §45 C12)

  이 저장소는 값·목패 이름·분량이 **두 벌**이 되어 어긋난 적이 있습니다.
  화면이 "평생운 18컷" 이라 적어 두고 실제로는 11컷이 나갔고, 릴레이
  카드가 4,900원을 보여 주고 19,900원이 청구됐습니다.

  완료율도 똑같습니다. 관리자 화면이 제 손으로 세고 문서가 또 세면
  둘이 갈립니다. 그래서 세는 자리를 하나로 둡니다 — `coverage()` 와
  `release_gate()` 밖에서 완료율을 계산하면 `tests/test_shipos.py` 가
  잡습니다.

★ 판단과 사실을 가릅니다

    product-os/*.yaml       판단 — 무엇이 required 이고 무엇이 na 인가
    seed/shipos_facts.json  사실 — 코드에 무엇이 있는가 (tools/shipos_scan.py)

  판단이 사실과 어긋나면(없는 화면을 live 라 적으면) 그건 **거짓말**이고
  검산이 CRITICAL 로 냅니다. 문서에는 완료, 실제론 미구현을 막는 자리입니다.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
OS_DIR = ROOT / "product-os"
FACTS = ROOT / "seed" / "shipos_facts.json"

# ── 구현축과 가중치 (§35) ─────────────────────────────────
#
# ★ ui_design 을 frontend 와 같은 값으로 둡니다.
#   이 집에는 별도 디자인 산출물(피그마)이 없고 토큰과 화면이 한 몸입니다.
#   축을 지우지 않고 **까닭을 적어** 둡니다 — 지우면 왜 없는지 잊습니다.
WEIGHTS = {
    "spec": 0.08, "ui_design": 0.08, "frontend": 0.14, "backend": 0.14,
    "database": 0.10, "api": 0.10, "analytics": 0.08, "qa": 0.12,
    "security": 0.08, "admin": 0.08,
}

VALUE = {"live": 1.0, "partial": 0.5, "spec": 0.15, "none": 0.0, "broken": 0.0}

# 사건이 화이트리스트에 없으면 서버가 **조용히 버립니다**. 그래서
# 쏘는데 목록에 없는 것은 「측정되는 줄 알았는데 안 되는」 자리입니다.
_TRACK_NOT_EVENTS = {"screen"}       # 이름이 겹쳐 잡히는 것들


def _norm(path: str) -> str:
    """`/v1/pay/order/{order_id}` 와 `/v1/pay/order/{x}` 를 같게 봅니다."""
    return re.sub(r"\{[^}]*\}", "{}", path.rstrip("/")) or "/"


@lru_cache(maxsize=1)
def facts() -> dict:
    if not FACTS.exists():
        return {"apis": [], "screens": [], "client_calls": [], "entities": [],
                "events": {"names": [], "server": [], "screens": []},
                "events_emitted_web": [], "events_emitted_server": [],
                "tests": [], "public_by_design": {}, "ownership_required": []}
    return json.loads(FACTS.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def registry() -> dict:
    """product-os 의 판단. yaml 이 없으면 빈 레지스트리로 돕니다."""
    out: dict = {"product": {}, "roles": [], "journeys": {},
                 "critical_flows": [], "features": [], "wiring": []}
    if not OS_DIR.exists():
        return out
    try:
        import yaml
    except ImportError:                       # pragma: no cover
        return out
    for name in ("product", "features", "wiring"):
        f = OS_DIR / ("%s.yaml" % name)
        if not f.exists():
            continue
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for k, v in data.items():
            out[k] = v
    return out


# ══════════════════════════════════════════════════════════
# 증거 — 레지스트리가 가리키는 것이 코드에 실제로 있는가
# ══════════════════════════════════════════════════════════
def _have() -> dict:
    f = facts()
    return {
        "apis": {a["id"] for a in f["apis"]},
        "api_paths": {_norm(a["path"]) for a in f["apis"]},
        # 화면 id 와 주소를 한 자루에 둡니다. `/legal` 처럼 `@screen`
        # 태그가 없는 자리도 레지스트리가 가리킬 수 있어야 합니다.
        "screens": {s["id"] for s in f["screens"]} | set(f.get("routes") or []),
        "entities": set(f["entities"]),
        "stores": set(f.get("stores") or []),
        "events": set(f["events"]["names"]) | set(f["events"]["server"]),
        "tests": set(f["tests"]),
    }


def _missing(feat: dict) -> list[str]:
    """이 기능이 가리키는데 코드에 없는 것."""
    have, out = _have(), []
    for api in feat.get("apis") or []:
        if api not in have["apis"]:
            out.append("api:%s" % api)
    for s in feat.get("screens") or []:
        if s not in have["screens"]:
            out.append("screen:%s" % s)
    for e in feat.get("entities") or []:
        if e not in have["entities"]:
            out.append("entity:%s" % e)
    # 곳간에 사는 상태 — DB 표가 아닙니다 (store.py 의 키 앞머리)
    for k in feat.get("stores") or []:
        if k not in have["stores"]:
            out.append("store:%s" % k)
    for e in feat.get("events") or []:
        if e not in have["events"]:
            out.append("event:%s" % e)
    for q in feat.get("qa") or []:
        if Path(q).name not in have["tests"] and not (ROOT / q).exists():
            out.append("qa:%s" % q)
    return out


def _axes(feat: dict, missing: list[str]) -> dict:
    """
    구현축별 상태 (§17.1).

    ★ 안 가리킨 축을 **빼면 안 됩니다.**

      처음 판은 「아무것도 안 가리킨 축은 안 센다」 였습니다. 그러면
      아직 하나도 안 만든 기능(status: none · 가리킨 것 0)이 spec 축
      하나만 남아 **100%** 로 나왔습니다. SEO 도, 백업도, 관제탑도
      만들기 전에 완료였습니다. §44 가 금하는 그것입니다 —
      "TODO 를 완료로 간주".

      그래서 축은 기본값이 **그 기능이 주장하는 상태**이고, 가리킨
      것이 있는 축만 증거로 덮어씁니다. 못 만든 기능은 못 만든 만큼
      나옵니다. 빼는 축은 기능 전체가 `na` 일 때뿐입니다.
    """
    base = feat.get("status", "none")
    claimed = "partial" if (base == "live" and (feat.get("gap") or feat.get("blocker"))) else base
    bad = {m.split(":", 1)[0] for m in missing}
    if "store" in bad:
        bad.add("entity")

    def ev(kind: str, declared) -> str:
        """가리킨 것이 있으면 증거로, 없으면 주장한 상태 그대로."""
        if not declared:
            return claimed
        return "broken" if kind in bad else claimed

    front = ev("screen", feat.get("screens") or feat.get("components"))
    api = ev("api", feat.get("apis"))
    axes = {
        # 레지스트리에 판정과 까닭이 적혀 있으면 spec 은 선 것입니다.
        "spec": "live",
        "ui_design": front,
        "frontend": front,
        "backend": api,
        "api": api,
        "database": ev("entity", feat.get("entities") or feat.get("stores")),
        "analytics": ev("event", feat.get("events")),
        "qa": ev("qa", feat.get("qa")),
        "security": ev("sec", feat.get("security")),
        "admin": ev("adm", feat.get("admin")),
    }
    # ★ 축이 정말로 해당 없는 자리 — 기능이 스스로 적습니다.
    #   까닭 없이 빼는 길은 없습니다 (§1.3).
    for k in feat.get("axes_na") or []:
        axes[k] = None
    return axes


def _feature_score(axes: dict) -> float:
    num = den = 0.0
    for k, w in WEIGHTS.items():
        v = axes.get(k)
        if v is None:
            continue
        num += w * VALUE.get(v, 0.0)
        den += w
    return (num / den) if den else 0.0


def _active(feat: dict) -> bool:
    """완료율에 세는 기능인가. na 는 안 셉니다 (의도적 제외)."""
    return feat.get("applicability") in ("required", "conditional")


# ══════════════════════════════════════════════════════════
# 배선 (§9 · §34) — 코드끼리 이어져 있는가
# ══════════════════════════════════════════════════════════
def broken_wires() -> list[dict]:
    """
    ★ 레지스트리와 **무관하게** 코드만 보고 찾는 끊긴 자리.
      여기 나오는 것은 사람이 안 적어도 드러납니다.
    """
    f, out = facts(), []
    have = _have()
    public = set(f.get("public_by_design") or {})
    own_need = set(f.get("ownership_required") or [])

    # W1 화면이 부르는데 그런 문이 없다
    for call in f.get("client_calls") or []:
        if _norm(call) not in have["api_paths"] and call != "/health":
            out.append({"id": "W1", "severity": "critical",
                        "what": "화면이 부르는데 서버에 그 자리가 없소",
                        "where": call})

    # W2 열어 뒀는데 아무도 안 부른다
    #
    # ★ 「화면이 부를 자리가 아닌 문」은 빼고 셉니다. 도구가 쓰는 문을
    #   고아로 세면, 진짜 고아(만들어 놓고 화면에 안 붙인 자리)가
    #   그 소음에 묻힙니다. 다만 **까닭이 적힌 것만** 뺍니다 (§1.3).
    tool_only = set(f.get("not_for_screens") or {})
    called = {_norm(c) for c in (f.get("client_calls") or [])}
    for a in f["apis"]:
        if a["id"] in public or a["id"] in tool_only \
                or a["path"].startswith("/v1/admin") \
                or a["path"] in ("/health",) or a["path"].startswith("/v1/jobs"):
            continue
        if _norm(a["path"]) not in called:
            out.append({"id": "W2", "severity": "warn",
                        "what": "열어 뒀는데 화면이 안 부르오",
                        "where": a["id"]})

    # W3 쏘는데 화이트리스트에 없다 — 서버가 조용히 버립니다
    known = set(f["events"]["names"]) | set(f["events"]["server"])
    for name in f.get("events_emitted_web") or []:
        if name in _TRACK_NOT_EVENTS or name in known:
            continue
        if name in {s["id"] for s in f["screens"]}:
            continue
        out.append({"id": "W3", "severity": "critical",
                    "what": "쏘는데 화이트리스트에 없어 서버가 버리오",
                    "where": name})

    # W4 목록에는 있는데 아무도 안 쏜다
    #
    # ★ W3 와 **다른 자**로 잽니다. 쏘는 자리가 삼항이거나 이름이
    #   변수로 넘어가면 좁은 자에 안 잡혀, 멀쩡히 도는 사건이 죽은
    #   것으로 나옵니다. 여기서는 「화면이 그 이름을 아는가」 를 봅니다.
    fired = (set(f.get("events_emitted_web") or [])
             | set(f.get("events_known_web") or [])
             | set(f.get("events_emitted_server") or []))
    for name in f["events"]["names"]:
        if name not in fired:
            out.append({"id": "W4", "severity": "warn",
                        "what": "화이트리스트에 있는데 아무도 안 쏘오",
                        "where": name})

    # W5 자격이 걸린 자리인데 주인인지 안 본다
    #
    # ★ 「소유권을 견준다」와 「세션에서 열쇠를 짓는다」는 **둘 다**
    #   주인을 보는 것입니다. `/v1/pay/sub` 는 `_k(session_id)` 로 제
    #   자리만 여니 남의 것을 못 봅니다. 앞쪽만 세면 멀쩡한 자리가
    #   붉게 뜨고, 진짜 뚫린 자리(`/v1/pay/order/{id}` — 세션을 아예
    #   안 받습니다)가 그 소음에 묻힙니다.
    for a in f["apis"]:
        if a["id"] in own_need and not (
                a["ownership_check"] or a["session_guard"] or a["admin_guard"]):
            out.append({"id": "W5", "severity": "critical",
                        "what": "값이 걸린 자리인데 주인인지 안 보오",
                        "where": a["id"]})

    # W6 까닭 없이 열린 문
    for a in f["apis"]:
        if a["path"].startswith(("/v1/admin", "/v1/funnel", "/v1/jobs")) \
                and not a["admin_guard"] and a["id"] not in public:
            out.append({"id": "W6", "severity": "critical",
                        "what": "주인 자리인데 안 잠겼고 까닭도 안 적혔소",
                        "where": a["id"]})
    return out


# ══════════════════════════════════════════════════════════
# 완료율 (§35) — ★ 세는 자리는 여기 하나
# ══════════════════════════════════════════════════════════
def coverage() -> dict:
    reg = registry()
    feats, rows = reg.get("features") or [], []
    for ft in feats:
        miss = _missing(ft)
        axes = _axes(ft, miss)
        score = _feature_score(axes)
        status = ft.get("status", "none")
        if miss:
            status = "broken"
        elif status == "live" and (ft.get("gap") or ft.get("blocker")):
            status = "partial"
        rows.append({
            "id": ft.get("id"), "title": ft.get("title"),
            "group": ft.get("group"), "applicability": ft.get("applicability"),
            "reason": ft.get("reason"), "gap": ft.get("gap"),
            "blocker": ft.get("blocker"),
            "declared": ft.get("status", "none"), "status": status,
            "axes": axes, "score": round(score, 4), "missing": miss,
            "screens": ft.get("screens") or [], "apis": ft.get("apis") or [],
            "entities": ft.get("entities") or [], "events": ft.get("events") or [],
            "qa": ft.get("qa") or [],
        })

    live = [r for r in rows if _active(r) ]
    overall = round(sum(r["score"] for r in live) / len(live), 4) if live else 0.0
    tally = {k: 0 for k in ("live", "partial", "spec", "none", "broken")}
    for r in live:
        tally[r["status"]] = tally.get(r["status"], 0) + 1
    return {
        "overall": overall,
        "counted": len(live),
        "na": len([r for r in rows if r["applicability"] == "na"]),
        "tally": tally,
        "features": rows,
    }


def by_stage() -> list[dict]:
    """역할 × 여정 단계 (§17.1 · §39.2 중단)."""
    reg = registry()
    cov = {r["id"]: r for r in coverage()["features"]}
    by_screen: dict = {}
    for r in cov.values():
        for s in r["screens"]:
            by_screen.setdefault(s, []).append(r["id"])
    out = []
    for role, stages in (reg.get("journeys") or {}).items():
        for st in stages:
            ids, seen = [], set()
            for s in st.get("screens") or []:
                for fid in by_screen.get(s, []):
                    if fid not in seen:
                        seen.add(fid)
                        ids.append(fid)
            got = [cov[i] for i in ids]
            out.append({
                "role": role, "stage": st["id"], "title": st["title"],
                "screens": st.get("screens") or [], "features": ids,
                "score": round(sum(g["score"] for g in got) / len(got), 4) if got else None,
                "broken": [g["id"] for g in got if g["status"] == "broken"],
            })
    return out


# ══════════════════════════════════════════════════════════
# 릴리스 게이트 (§36)
# ══════════════════════════════════════════════════════════
def release_gate() -> dict:
    cov, wires = coverage(), broken_wires()
    crit = [w for w in wires if w["severity"] == "critical"]
    feats = {r["id"]: r for r in cov["features"]}
    reg = registry()

    blockers = sorted({r["blocker"] for r in cov["features"]
                       if r.get("blocker") and _active(r)})
    lying = [r["id"] for r in cov["features"] if r["missing"]]

    def _flow_ok(flow: dict) -> bool:
        return True

    checks = [
        ("P0 blocker = 0", not blockers, blockers),
        ("critical broken wire = 0", not crit, [w["where"] for w in crit]),
        ("레지스트리가 코드와 일치", not lying, lying),
        ("auth pass", feats.get("AUTH-ADMIN-LOGIN", {}).get("status") == "live", []),
        ("permission pass", feats.get("PERM-SERVER-SIDE", {}).get("status") in ("live",), []),
        ("payment pass", feats.get("BILL-CHECKOUT", {}).get("status") == "live"
         and feats.get("BILL-ENTITLEMENT", {}).get("status") == "live", []),
        ("analytics pass", feats.get("ANALYTICS-EVENTS", {}).get("status") == "live", []),
        ("admin operation pass", feats.get("ADMIN-ORDERS", {}).get("status") == "live", []),
        ("error states pass", feats.get("OPS-ERROR-TRACKING", {}).get("status") == "live", []),
        ("migration pass", feats.get("OPS-MIGRATION", {}).get("status") == "live", []),
        ("backup documented", feats.get("OPS-BACKUP", {}).get("status") == "live", []),
    ]
    rows = [{"name": n, "pass": bool(ok), "detail": d} for n, ok, d in checks]
    return {"ready": all(r["pass"] for r in rows), "checks": rows,
            "critical_flows": reg.get("critical_flows") or []}


def next_actions(limit: int = 8) -> list[dict]:
    """다음에 무엇부터 (§40)."""
    cov, out = coverage(), []
    wires = broken_wires()
    for w in wires:
        if w["severity"] == "critical":
            out.append({"p": 0, "why": "critical broken wire",
                        "what": "%s — %s" % (w["where"], w["what"])})
    for r in cov["features"]:
        if not _active(r):
            continue
        if r["missing"]:
            out.append({"p": 0, "why": "레지스트리가 코드와 다름",
                        "what": "%s — %s" % (r["id"], ", ".join(r["missing"]))})
        elif r.get("blocker"):
            out.append({"p": 1, "why": "blocker", "what": "%s — %s" % (r["id"], r["blocker"])})
        elif r["status"] == "none" and r["applicability"] == "required":
            out.append({"p": 2, "why": "required 인데 없음", "what": "%s — %s" % (r["id"], r["title"])})
        elif r["status"] == "partial":
            out.append({"p": 3, "why": "절반만", "what": "%s — %s" % (r["id"], r["title"])})
    for w in wires:
        if w["severity"] != "critical":
            out.append({"p": 4, "why": "warn wire",
                        "what": "%s — %s" % (w["where"], w["what"])})
    out.sort(key=lambda r: r["p"])
    return out[:limit]


def tower() -> dict:
    """관제탑이 한 번에 받아 가는 것 (§17.2 · §39.2)."""
    cov = coverage()
    return {
        "product": registry().get("product") or {},
        "overall": cov["overall"], "tally": cov["tally"],
        "counted": cov["counted"], "na": cov["na"],
        "features": cov["features"],
        "stages": by_stage(),
        "wires": broken_wires(),
        "gate": release_gate(),
        "next": next_actions(),
        "weights": WEIGHTS,
    }
