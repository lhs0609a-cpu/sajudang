r"""
SHIP OS · 사실 수집기 — 코드에서 긁어 `seed/shipos_facts.json` 에 찍습니다.

★ 왜 찍어 두는가

  관제탑은 배포본에서도 돌아야 하는데, 배포 이미지에는 `apps/web` 도
  `tools/` 도 `tests/` 도 없습니다 (Dockerfile 은 seed 와 services/api 만
  넣습니다). 그래서 **소스를 읽어야 아는 것**은 여기서 미리 재어
  seed 에 찍고, 서버는 찍힌 것을 읽습니다.

  연출 점수가 `seed/screen_text.json` 을 쓰는 것과 같은 방식입니다.
  찍은 것이 소스와 어긋나면 `tests/test_shipos.py` 가 잡습니다 —
  안 찍고 배포하면 관제탑이 옛말을 합니다.

★ 여기서 재는 것은 **사실**입니다. 판단이 아닙니다.
  무엇이 required 이고 무엇이 na 인지는 `product-os/features.yaml` 이
  들고 있습니다. 이 파일은 "있다/없다/이어져 있다" 만 셉니다.

    .\dev.ps1 shipos-scan          찍기
    python tools/shipos_scan.py --check   찍힌 것이 지금 소스와 같은가
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "services" / "api"
WEB = ROOT / "apps" / "web"
OUT = ROOT / "seed" / "shipos_facts.json"

# ── 공개로 두기로 한 문 ────────────────────────────────────
#
# ★ 「잠기지 않았다」와 「일부러 열어 두었다」는 다릅니다 (§1.3).
#   까닭 없이 열린 문은 누락이고, 까닭이 적힌 문은 설계입니다.
#   여기 없는데 안 잠긴 문이 있으면 검사가 BROKEN 으로 냅니다.
PUBLIC_BY_DESIGN = {
    "GET /v1/admin/gate":
        "들어오기 전에 문이 어떤 꼴인지 물어봐야 화면이 로그인 칸을 그릴지 "
        "열쇠 칸을 그릴지 정합니다. 참·거짓 둘만 답하고 아이디도 열쇠도 안 흘립니다.",
    "POST /v1/admin/login":
        "로그인하는 자리입니다. 여기를 잠그면 들어올 길이 없습니다. "
        "대신 5분 10회 잠금이 있습니다 (adminauth._too_many).",
    "POST /v1/admin/logout":
        "쪽지를 버리는 자리입니다. 남의 쪽지는 못 버립니다 — 자기가 든 것만 버립니다.",
    "POST /v1/events":
        "손님 브라우저가 계측을 보내는 문입니다. 이름·화면이 화이트리스트이고 "
        "값은 숫자만 받습니다. 조회 문(/v1/funnel)은 잠겨 있습니다.",
    "GET /v1/pay/webhook":
        "토스 개발자센터에 주소를 넣기 전에 사람이 눈으로 보는 자리입니다. "
        "아무 일도 하지 않고 살아 있다는 것만 알립니다.",
    "POST /v1/pay/webhook":
        "PG 가 두드리는 문이라 우리 열쇠를 줄 수 없습니다. 대신 본문을 안 믿고 "
        "시크릿 키로 토스에 되물어 확인합니다 (payments.lookup_by_order).",
    "GET /v1/share/{token}":
        "공유 링크는 받은 사람이 여는 자리입니다. 생년월일시·고을이 payload 에 없습니다.",
    "POST /v1/share/{token}/open":
        "공유 링크를 연 횟수를 세는 자리입니다.",
    "GET /v1/voice/{key}.mp3":
        "이미 렌더된 소리 조각입니다. 열쇠는 내용 해시라 맞혀서 다른 사람 것을 못 엽니다.",
}

# ── 화면이 안 불러도 되는 문 ──────────────────────────────
#
# ★ 「아무도 안 부른다」와 「화면이 부를 자리가 아니다」는 다릅니다.
#   도구와 다른 서버가 쓰는 문을 고아로 세면, 진짜 고아(만들어 놓고
#   화면에 안 붙인 자리)가 그 소음에 묻힙니다.
NOT_FOR_SCREENS = {
    "GET /v1/funnel":
        "사람이 도구로 봅니다 (tools/funnel.py). 화면에 매출·전환을 "
        "띄우는 자리는 주인 화면(/v1/admin/overview)이 따로 있습니다.",
    "GET /v1/review/stats":
        "공감률 집계입니다. 실응답 100건이 쌓이기 전에는 화면에 안 냅니다 "
        "— 지어낸 숫자를 띄우지 않기로 한 자리입니다.",
    "POST /v1/omnibus":
        "스무 사람을 한 번에 짓는 자리라 화면이 아니라 도구·검사가 씁니다.",
    "GET /v1/pay/order/{order_id}":
        "주문 하나의 상태를 되묻는 자리입니다. 화면은 구매 내역"
        "(/v1/pay/history)으로 한 번에 받아 갑니다.",
}

# 손님 자격이 걸린 문 — 세션이나 소유권을 봐야 하는 자리
OWNERSHIP_REQUIRED = {
    "POST /v1/pay/confirm", "POST /v1/pay/refund", "GET /v1/pay/history",
    "GET /v1/pay/order/{order_id}", "POST /v1/pay/restore",
    "GET /v1/pay/sub", "POST /v1/pay/sub/cancel", "POST /v1/pay/sub/resume",
    "POST /v1/pay/sub/register", "POST /v1/pay/sub/restore",
}


def _routers() -> list[dict]:
    """
    서버가 여는 문 전부.

    ★ 따옴표 두 가지를 다 봅니다.
      처음 판은 큰따옴표만 봤습니다. `routers/jobs.py` 가 작은따옴표로
      쓰여 있어서 **갱신 작업 문이 통째로 안 보였고**, 레지스트리가
      그 문을 가리키자 "코드에 없다"는 거짓 경보가 났습니다.
      자가 못 보는 것을 글 탓으로 돌리면 안 됩니다.
    """
    out = []
    for f in sorted((API / "routers").glob("*.py")):
        src = f.read_text(encoding="utf-8")
        pre = re.search(r'APIRouter\(\s*prefix\s*=\s*["\']([^"\']*)["\']', src)
        prefix = pre.group(1) if pre else ""
        hits = list(re.finditer(
            r'@router\.(get|post|put|patch|delete)\(\s*["\']([^"\']*)["\']', src))
        for i, m in enumerate(hits):
            verb, path = m.group(1).upper(), m.group(2)
            end = hits[i + 1].start() if i + 1 < len(hits) else len(src)
            body = src[m.end():end]
            fn = re.search(r"\ndef (\w+)", body)
            out.append({
                "id": "%s %s" % (verb, (prefix + path) or "/"),
                "method": verb,
                "path": (prefix + path) or "/",
                "file": "services/api/routers/%s.py" % f.stem,
                "handler": fn.group(1) if fn else None,
                # 주인 열쇠·세션·소유권 중 하나라도 보는가
                # ★ 주인 문을 지키는 길은 둘입니다 — `_guard()`(열쇠·쪽지)
                #   와 `adminauth.session_of()`(쪽지만). `/v1/admin/me` 가
                #   뒤쪽으로 지키고 있는데 앞쪽만 세어 「안 잠김」 이라
                #   나왔습니다. 이름이 아니라 **지키는가**를 봅니다.
                #   잡(job) 문은 세 번째 길로 지킵니다 — 머리표 열쇠를
                #   `hmac.compare_digest` 로 견줍니다. 이름이 셋인데
                #   앞의 둘만 세어 갱신 문이 「안 잠김」 으로 나왔습니다.
                "admin_guard": bool(re.search(
                    r"_guard\(|require_admin|session_of\(|compare_digest\(", body)),
                "session_guard": bool(re.search(
                    r"session_of\(|session_id|_user_key\(", body)),
                "ownership_check": bool(re.search(
                    r'session_id.{0,80}!=|!=.{0,80}session_id|'
                    r'"orders:"\s*\+\s*req\.session_id|'
                    r'get_json\("orders:"', body, re.S)),
            })
    # /health 는 main.py 가 냅니다
    main = (API / "main.py").read_text(encoding="utf-8")
    for m in re.finditer(r'@app\.(get|post)\(\s*["\']([^"\']*)["\']', main):
        out.append({
            "id": "%s %s" % (m.group(1).upper(), m.group(2)),
            "method": m.group(1).upper(), "path": m.group(2),
            "file": "services/api/main.py", "handler": None,
            "admin_guard": False, "session_guard": False,
            "ownership_check": False,
        })
    return out


def _screens() -> list[dict]:
    """화면 — `@screen` 태그가 붙은 자리."""
    if not WEB.exists():
        return []
    out = []
    for f in sorted(WEB.glob("app/**/*.tsx")):
        src = f.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"@screen\s+([a-z0-9 ]+)", src)
        if not m:
            continue
        route = "/" + str(f.relative_to(WEB / "app")).replace("\\", "/")
        route = re.sub(r"/page\.tsx$", "", route) or "/"
        for sid in m.group(1).split():
            out.append({"id": sid, "route": route,
                        "file": str(f.relative_to(ROOT)).replace("\\", "/")})
    # 주인 화면은 @screen 을 안 답니다 — 손님 화면 그래프와 섞이면
    # 고아·막다른 검사가 주인 자리를 손님 자리로 셉니다.
    if (WEB / "app/admin/page.tsx").exists():
        out.append({"id": "adm-login", "route": "/admin",
                    "file": "apps/web/app/admin/page.tsx"})
        out.append({"id": "adm-overview", "route": "/admin",
                    "file": "apps/web/app/admin/page.tsx"})
        out.append({"id": "adm-refund", "route": "/admin",
                    "file": "apps/web/app/admin/page.tsx"})
    if (WEB / "app/admin/tower/page.tsx").exists():
        out.append({"id": "adm-tower", "route": "/admin/tower",
                    "file": "apps/web/app/admin/tower/page.tsx"})
    return out


def _web_files() -> list[Path]:
    return (list(WEB.glob("app/**/*.ts*")) + list(WEB.glob("lib/**/*.ts*"))
            + list(WEB.glob("components/**/*.ts*")))


def _client_calls() -> list[str]:
    """
    화면이 실제로 부르는 서버 자리.

    ★ 템플릿 리터럴을 먼저 접습니다.
      `/v1/chart/${encodeURIComponent(id)}` 에서 괄호가 나오면 낱말이
      끊겨 `/v1/chart/${encodeURIComponent` 라는 **있지도 않은 길**이
      나왔습니다. 자가 못 읽은 것을 「끊긴 배선」 이라 부르면, 진짜
      끊긴 자리가 그 소음에 묻힙니다.
    """
    if not WEB.exists():
        return []
    seen = set()
    for f in _web_files():
        src = f.read_text(encoding="utf-8", errors="replace")
        # ① `${ ... }` 를 통째로 한 칸으로 접는다 (중첩 괄호 포함)
        flat = re.sub(r"\$\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", "{}", src)
        # ★ 따옴표 **뒤**만 보면 안 됩니다.
        #   `fetch(`${API_BASE}/v1/pay/history?…`)` 처럼 앞에 틀이 붙는
        #   꼴이 흔한데, 접고 나면 길 바로 앞 글자가 `}` 입니다.
        #   따옴표만 보다가 환불·구매내역·항해가 전부 「아무도 안
        #   부르오」 로 나왔습니다 — 멀쩡히 부르고 있는데요.
        for m in re.finditer(r'(?:["\'`]|\})(/v1/[A-Za-z0-9_/{}.\-]*)', flat):
            p = m.group(1)
            # ★ 끝에 빗금이 붙은 것은 **부르는 길이 아니라 접두사 검사**입니다.
            #   `path.startsWith("/v1/pay/")` 를 길로 세었다가 `/v1/pay` 라는
            #   있지도 않은 자리를 「화면이 부르는데 서버에 없다」고 냈습니다.
            if p.endswith("/"):
                continue
            if p.count("/") < 2:
                continue
            seen.add(p)
        if "/health" in src:
            seen.add("/health")
    return sorted(seen)


def _routes() -> list[str]:
    """화면이 사는 주소. `@screen` 이 없는 자리(/legal · /admin)도 셉니다."""
    if not WEB.exists():
        return []
    out = set()
    for f in WEB.glob("app/**/page.tsx"):
        r = "/" + str(f.relative_to(WEB / "app")).replace("\\", "/")
        out.add(re.sub(r"/page\.tsx$", "", r) or "/")
    return sorted(out)


def _stores() -> list[str]:
    """
    곳간 열쇠 앞머리 — 세션에 묶인 상태가 사는 자리.

    ★ 표(SQLAlchemy 테이블)와 **다른 것**입니다. 주문·인장·구독은
      DB 표가 아니라 곳간(store.py) 키로 삽니다. 레지스트리가 이걸
      `entities` 로 적었다가 "그런 표 없다"는 거짓 경보를 냈습니다.
    """
    out = set()
    for f in list(API.glob("*.py")) + list((API / "routers").glob("*.py")):
        src = f.read_text(encoding="utf-8")
        for m in re.finditer(r'["\']([a-z][a-z0-9_-]{2,20}):["\']', src):
            out.add(m.group(1))
    return sorted(out)


def _events() -> dict:
    """계측 화이트리스트 — 이름과 화면."""
    src = (API / "analytics.py").read_text(encoding="utf-8")

    def _set(name: str) -> list[str]:
        m = re.search(name + r"\s*=\s*\{(.*?)\n\}", src, re.S)
        if not m:
            return []
        return sorted(set(re.findall(r'"([a-z0-9_]+)"', m.group(1))))

    return {"names": _set("EVENTS"), "server": _set("SERVER_EVENTS"),
            "screens": _set("SCREENS")}


def _emitted() -> list[str]:
    """화면이 실제로 쏘는 사건 이름."""
    if not WEB.exists():
        return []
    seen = set()
    for f in _web_files():
        src = f.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r'track\(\s*["\']([a-z0-9_]+)["\']', src):
            seen.add(m.group(1))
        for m in re.finditer(r'name:\s*["\']([a-z0-9_]+)["\']', src):
            seen.add(m.group(1))
    return sorted(seen)


def _events_known_web(names: list[str]) -> list[str]:
    """
    화면이 이 이름을 **아는가**. `_emitted` 와 **다른 물음**입니다.

    ★ 두 물음을 한 자로 재다가 크게 틀렸습니다.

      「쏘는데 목록에 없다」(W3)는 좁게 재야 합니다 — 실제 `track(…)`
      호출만. 넓게 재면 CSS 낱말까지 사건으로 잡혀 경보가 수백 줄이
      되고, 그러면 진짜가 묻힙니다.

      「목록에 있는데 아무도 안 쏜다」(W4)는 넓게 재야 합니다 —
      쏘는 자리가 `track(ok ? "relay_take" : "relay_skip")` 이거나
      이름이 변수로 넘어가면 좁은 자에는 안 잡혀, 멀쩡히 도는 사건
      열 개가 죽은 것으로 나왔습니다.

      그래서 **아는 이름만** 찾습니다 — 화이트리스트에 있는 이름이
      화면 소스 어딘가에 글자로 있는가. 자를 글에 맞추는 것이 아니라,
      묻는 것이 다르니 자를 둘 두는 것입니다.
    """
    if not WEB.exists():
        return []
    want = set(names)
    seen = set()
    for f in _web_files():
        src = f.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r'["\']([a-z][a-z0-9_]{2,30})["\']', src):
            if m.group(1) in want:
                seen.add(m.group(1))
    return sorted(seen)


def _server_emitted() -> list[str]:
    seen = set()
    for f in list(API.glob("*.py")) + list((API / "routers").glob("*.py")):
        src = f.read_text(encoding="utf-8")
        for m in re.finditer(r'"name":\s*"([a-z0-9_]+)"', src):
            seen.add(m.group(1))
    return sorted(seen)


def _entities() -> list[str]:
    src = (API / "models.py").read_text(encoding="utf-8")
    return sorted(set(re.findall(r'__tablename__\s*=\s*"(\w+)"', src)))


def _tests() -> list[str]:
    d = ROOT / "tests"
    return sorted(p.name for p in d.glob("test_*.py")) if d.exists() else []


def collect() -> dict:
    ev = _events()
    return {
        "apis": _routers(),
        "screens": _screens(),
        "routes": _routes(),
        "stores": _stores(),
        "client_calls": _client_calls(),
        "events": ev,
        "events_emitted_web": _emitted(),
        # 화면이 **아는** 이름. 죽은 사건을 셀 때만 씁니다 (위 설명 참고).
        "events_known_web": _events_known_web(ev["names"]),
        "events_emitted_server": _server_emitted(),
        "entities": _entities(),
        "tests": _tests(),
        "public_by_design": PUBLIC_BY_DESIGN,
        "not_for_screens": NOT_FOR_SCREENS,
        "ownership_required": sorted(OWNERSHIP_REQUIRED),
    }


def _frozen(d: dict) -> str:
    return json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True)


def main(argv: list[str]) -> int:
    got = collect()
    # 화면·클라이언트 호출은 apps/web 이 있어야 잽니다. 없는 기계에서
    # 찍으면 **있던 것을 지웁니다** — 그러면 관제탑이 화면을 잃습니다.
    web_missing = not WEB.exists()
    if "--check" in argv:
        if not OUT.exists():
            print("찍어 둔 것이 없소.  python tools/shipos_scan.py")
            return 1
        old = json.loads(OUT.read_text(encoding="utf-8"))
        if web_missing:
            for k in ("screens", "routes", "client_calls", "events_emitted_web",
                      "events_known_web"):
                got[k] = old.get(k, got[k])
        if _frozen(old) != _frozen(got):
            print("찍어 둔 것이 지금 소스와 다르오.  python tools/shipos_scan.py")
            for k in sorted(got):
                if _frozen({k: old.get(k)}) != _frozen({k: got[k]}):
                    print("   다른 칸: %s" % k)
            return 1
        print("[OK] 찍어 둔 것이 소스와 같소")
        return 0

    if web_missing and OUT.exists():
        old = json.loads(OUT.read_text(encoding="utf-8"))
        for k in ("screens", "routes", "client_calls", "events_emitted_web",
                  "events_known_web"):
            got[k] = old.get(k, got[k])
        print("※ apps/web 이 없어 화면 칸은 찍어 둔 것을 그대로 둡니다")

    OUT.write_text(_frozen(got) + "\n", encoding="utf-8")
    print("찍었소 → %s" % OUT.relative_to(ROOT))
    print("   문 %d · 화면 %d · 사건 %d · 표 %d"
          % (len(got["apis"]), len(got["screens"]),
             len(got["events"]["names"]), len(got["entities"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
