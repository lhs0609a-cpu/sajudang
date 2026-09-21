"""
SHIP OS 검산 — C0~C12 (MASTER_BUILD_SHIP_OS.md §45).

★ 이 파일이 지키는 것

  레지스트리(`product-os/*.yaml`)는 **판단**이고 코드는 **사실**입니다.
  둘이 갈리면 관제탑이 거짓말을 합니다 — 그리고 관제탑이 거짓말을
  하면 사람이 그걸 보고 「다 됐다」 고 배포합니다.

  이 집은 값·목패 이름·분량이 두 벌이 되어 어긋난 적이 있습니다.
  완료율은 그 사고가 **더 조용히** 납니다. 그래서 검사로 묶습니다.

★ 하나라도 critical 이면 완료라고 말하지 않습니다 (§45 끝줄).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT / "tools"))

import shipos  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh():
    """레지스트리·사실을 캐시에서 꺼내 씁니다. 검사끼리 안 섞이게."""
    shipos.registry.cache_clear()
    shipos.facts.cache_clear()
    yield
    shipos.registry.cache_clear()
    shipos.facts.cache_clear()


# ══════════════════════════════════════════════════════════
# C0 구조 — 역할 · 여정 · 상태가 있는가
# ══════════════════════════════════════════════════════════
def test_c0_구조가_있다():
    reg = shipos.registry()
    assert reg["product"].get("name"), "제품 이름이 없소"
    assert reg["product"].get("core_value"), "핵심가치가 없소"
    assert reg["product"].get("aha_moment"), "아하가 없소"
    assert reg.get("roles"), "역할이 없소"
    assert reg.get("journeys"), "여정이 없소"
    assert reg.get("critical_flows"), "핵심 플로우가 없소"


def test_c0_레지스트리가_읽힌다():
    """yaml 이 깨지면 관제탑이 **빈 채로** 떠서 '다 됐다'고 말합니다."""
    import yaml
    for name in ("product", "features"):
        f = ROOT / "product-os" / ("%s.yaml" % name)
        assert f.exists(), "%s.yaml 이 없소" % name
        assert yaml.safe_load(f.read_text(encoding="utf-8")), "%s.yaml 이 비었소" % name


# ══════════════════════════════════════════════════════════
# C1 ID — 겹치지 않는가
# ══════════════════════════════════════════════════════════
def test_c1_기능_id가_겹치지_않는다():
    ids = [f["id"] for f in shipos.registry()["features"]]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    assert not dup, "겹친 기능 id: %s" % dup


def test_c1_문_id가_겹치지_않는다():
    ids = [a["id"] for a in shipos.facts()["apis"]]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    assert not dup, "같은 길에 문이 둘이오: %s" % dup


# ══════════════════════════════════════════════════════════
# C2 참조 — 가리킨 것이 실제로 있는가  ★ 가장 중요한 검사
# ══════════════════════════════════════════════════════════
def test_c2_레지스트리가_없는_것을_가리키지_않는다():
    """
    ★ 「문서에는 완료, 실제론 미구현」 을 막는 자리입니다 (§1.1).
      없는 화면·문·표·사건·검사를 가리키면 여기서 걸립니다.
    """
    bad = [(r["id"], r["missing"]) for r in shipos.coverage()["features"]
           if r["missing"]]
    assert not bad, "레지스트리가 코드에 없는 것을 가리키오:\n" + "\n".join(
        "  %-24s %s" % (i, ", ".join(m)) for i, m in bad)


def test_c2_의도적_제외에는_까닭이_있다():
    """까닭 없이 빠진 것은 **누락**입니다 (§1.3)."""
    bad = [f["id"] for f in shipos.registry()["features"]
           if f.get("applicability") == "na" and not f.get("reason")]
    assert not bad, "까닭 없는 na: %s" % bad


def test_c2_조건부에는_조건이_있다():
    bad = [f["id"] for f in shipos.registry()["features"]
           if f.get("applicability") == "conditional"
           and not (f.get("condition") or f.get("reason"))]
    assert not bad, "조건 없는 conditional: %s" % bad


def test_c2_판정이_셋_중_하나다():
    ok = {"required", "conditional", "na"}
    bad = [(f["id"], f.get("applicability")) for f in shipos.registry()["features"]
           if f.get("applicability") not in ok]
    assert not bad, "판정이 required/conditional/na 가 아니오: %s" % bad


# ══════════════════════════════════════════════════════════
# C3 배선 · C4 상태
# ══════════════════════════════════════════════════════════
def test_c3_critical_broken_wire가_없다():
    crit = [w for w in shipos.broken_wires() if w["severity"] == "critical"]
    assert not crit, "끊긴 배선:\n" + "\n".join(
        "  %-4s %-40s %s" % (w["id"], w["where"], w["what"]) for w in crit)


def test_c4_live인데_빠진_것이_있으면_안_된다():
    """
    gap 이나 blocker 가 있는데 live 라 적으면 `partial` 로 내려갑니다.
    그 강등이 실제로 도는지 봅니다 — 안 돌면 완료율이 부풀립니다.
    """
    for r in shipos.coverage()["features"]:
        if r["declared"] == "live" and (r["gap"] or r["blocker"]):
            assert r["status"] != "live", \
                "%s 는 빠진 것이 있는데 live 로 서 있소" % r["id"]


def test_c4_아무것도_안_만든_기능이_만점을_받지_않는다():
    """
    ★ 한 번 이렇게 샜습니다.
      「안 가리킨 축은 안 센다」 로 두었더니, 하나도 안 만든 기능이
      spec 축 하나만 남아 **100%** 로 나왔습니다. §44 가 금하는
      「TODO 를 완료로 간주」 입니다.
    """
    for r in shipos.coverage()["features"]:
        if r["applicability"] != "na" and r["declared"] == "none":
            assert r["score"] < 0.2, \
                "%s 는 아직 없는데 %.0f%% 요" % (r["id"], r["score"] * 100)


# ══════════════════════════════════════════════════════════
# C5 Analytics — 핵심 행동에 사건이 붙어 있는가
# ══════════════════════════════════════════════════════════
def test_c5_핵심_기능에_계측이_붙어_있다():
    """계측 없는 핵심 기능은 완료가 아닙니다 (§48-8)."""
    want = {"BILL-CHECKOUT", "CORE-HOOK", "CORE-REPORT", "CORE-RELAY",
            "PUB-REFERRAL", "PUB-LANDING"}
    by = {f["id"]: f for f in shipos.registry()["features"]}
    for fid in want:
        assert by.get(fid), "%s 가 레지스트리에 없소" % fid
        assert by[fid].get("events"), "%s 에 사건이 안 붙었소" % fid


def test_c5_쏘는_사건이_화이트리스트에_있다():
    """목록에 없으면 서버가 **조용히 버립니다** — 측정되는 줄 알고 삽니다."""
    bad = [w for w in shipos.broken_wires() if w["id"] == "W3"]
    assert not bad, "버려지는 사건: %s" % [w["where"] for w in bad]


# ══════════════════════════════════════════════════════════
# C6 QA — 핵심 기능에 검사가 있는가
# ══════════════════════════════════════════════════════════
def test_c6_핵심_기능에_검사가_있다():
    want = {"BILL-CHECKOUT", "BILL-ENTITLEMENT", "BILL-REFUND",
            "CORE-CHART", "CORE-GUARD", "TRUST-BRAKES", "AUTH-ADMIN-LOGIN"}
    by = {f["id"]: f for f in shipos.registry()["features"]}
    for fid in want:
        assert by.get(fid), "%s 가 레지스트리에 없소" % fid
        assert by[fid].get("qa"), "%s 에 검사가 안 붙었소" % fid


# ══════════════════════════════════════════════════════════
# C7 Permission — 지켜야 할 문이 지켜지는가
# ══════════════════════════════════════════════════════════
def test_c7_주인_문이_전부_잠겨_있다():
    """
    ★ 「안 잠겼다」와 「일부러 열어 뒀다」는 다릅니다 (§1.3).
      일부러 연 문은 `PUBLIC_BY_DESIGN` 에 **까닭과 함께** 적습니다.
      거기 없는데 안 잠긴 문은 누락입니다.
    """
    f = shipos.facts()
    public = set(f.get("public_by_design") or {})
    bad = [a["id"] for a in f["apis"]
           if a["path"].startswith(("/v1/admin", "/v1/funnel", "/v1/jobs"))
           and not a["admin_guard"] and a["id"] not in public]
    assert not bad, "까닭 없이 열린 주인 문: %s" % bad


def test_c7_값이_걸린_문은_주인인지_본다():
    bad = [w["where"] for w in shipos.broken_wires() if w["id"] == "W5"]
    assert not bad, "주인인지 안 보는 문: %s" % bad


def test_c7_일부러_연_문에는_까닭이_적혀_있다():
    for door, why in (shipos.facts().get("public_by_design") or {}).items():
        assert why and len(why) > 15, "%s 를 왜 열어 뒀는지 안 적혔소" % door


def test_c7_권한을_화면에서만_막지_않는다():
    """
    프론트엔드 숨김만으로 권한을 구현하지 않습니다 (§12).
    자격은 **치른 주문**이 정해야 합니다 — 화면이 보낸 tier 가 아니라.
    """
    src = (ROOT / "services/api/routers/report.py").read_text(encoding="utf-8")
    assert "def entitled_tier" in src, "서버가 자격을 안 정하오"
    assert "TIER_RANK[req.tier] <= TIER_RANK[allowed]" in src, \
        "화면이 보낸 tier 를 그대로 믿고 있소"


# ══════════════════════════════════════════════════════════
# C8 Admin — 운영할 수 있는가
# ══════════════════════════════════════════════════════════
def test_c8_운영에_필요한_자리가_있다():
    """관리자에서 운영할 수 없는 기능은 운영 가능한 제품이 아닙니다 (§48-11)."""
    have = {a["id"] for a in shipos.facts()["apis"]}
    for door in ("GET /v1/admin/overview", "GET /v1/admin/orders",
                 "POST /v1/admin/orders/grant", "GET /v1/admin/audit",
                 "GET /v1/admin/tower", "GET /v1/admin/refund-reviews"):
        assert door in have, "운영 자리가 없소: %s" % door


def test_c8_돈을_움직이는_조작은_기록에_남는다():
    """§43 — 주인 행동은 audit log 가 필요합니다."""
    src = (ROOT / "services/api/routers/admin.py").read_text(encoding="utf-8")
    for op in ("refund.decide", "order.grant"):
        assert op in src, "%s 가 감사기록에 안 남소" % op


def test_c8_감사기록에_준식별자를_안_싣는다():
    import audit
    row = audit._clean({"session_id": "s", "chart_id": "c", "payment_key": "p",
                        "status": "paid", "amount": 9900})
    assert row == {"status": "paid", "amount": 9900}, \
        "감사기록에 준식별자가 실리오: %s" % row


# ══════════════════════════════════════════════════════════
# C9 Release Gate
# ══════════════════════════════════════════════════════════
def test_c9_게이트가_돌고_까닭을_댄다():
    g = shipos.release_gate()
    assert g["checks"], "게이트가 비었소"
    for row in g["checks"]:
        assert "name" in row and "pass" in row
    # 통과 못 한 것이 있으면 ready 가 참이면 안 됩니다.
    if not all(r["pass"] for r in g["checks"]):
        assert not g["ready"], "막힌 것이 있는데 READY 라 하오"


# ══════════════════════════════════════════════════════════
# C10 · C11 Round Trip — 소스가 바뀌면 관제탑이 따라오는가
# ══════════════════════════════════════════════════════════
def test_c11_찍어_둔_사실이_지금_소스와_같다():
    """
    ★ 배포 이미지에는 apps/web 도 tools 도 없습니다. 그래서 소스를
      읽어야 아는 것은 `seed/shipos_facts.json` 에 미리 찍습니다.
      안 찍고 배포하면 관제탑이 **옛말**을 합니다.

        python tools/shipos_scan.py
    """
    import shipos_scan
    assert shipos_scan.main(["--check"]) == 0, \
        "찍어 둔 것이 소스와 다르오. python tools/shipos_scan.py 를 돌리시오"


# ══════════════════════════════════════════════════════════
# C12 Hardcode — 완료율을 한 곳에서만 세는가
# ══════════════════════════════════════════════════════════
def test_c12_완료율을_한_곳에서만_센다():
    """
    ★ 이 집은 값·목패 이름·분량이 두 벌이 되어 어긋난 적이 있습니다.
      완료율이 두 벌이 되면 더 조용히 어긋납니다 — 아무도 안 죽고
      숫자만 틀립니다.

      화면과 라우터는 **받아 적기만** 해야 합니다.
    """
    suspects = [
        ROOT / "apps/web/app/admin/tower/page.tsx",
        ROOT / "apps/web/components/Voyage.tsx",
        ROOT / "services/api/routers/admin.py",
        ROOT / "services/api/routers/journey.py",
    ]
    # 가중치를 다시 적거나 축 이름을 늘어놓고 점수를 곱하는 짓
    ban = re.compile(r"WEIGHTS\s*=|weights\s*=\s*\{|0\.14\s*\*|\*\s*0\.12")
    for f in suspects:
        if not f.exists():
            continue
        src = f.read_text(encoding="utf-8", errors="replace")
        assert not ban.search(src), "%s 가 제 손으로 완료율을 세오" % f.name


def test_c12_관제탑_응답이_가드를_지난다():
    """
    ★ 관제탑도 API 입니다. 응답은 금지어 필터를 지납니다.
      레지스트리 글에 금지어를 적으면 그 글이 화면에서 잘려 나갑니다 —
      한 번 그랬습니다(기능 제목에 「수명」 이 들어 있었습니다).
    """
    from engine import guard
    hits = guard.scan(shipos.tower())
    assert not hits, "관제탑 응답이 가드에 걸리오: %s" % [h["path"] for h in hits]


# ══════════════════════════════════════════════════════════
# 유저 관제탑 (§18)
# ══════════════════════════════════════════════════════════
def test_유저_관제탑은_다음_한_걸음만_낸다():
    """둘을 시키면 손님은 **하나도** 안 합니다."""
    src = (ROOT / "services/api/routers/journey.py").read_text(encoding="utf-8")
    assert '"next":' in src
    assert "nxt[0]" in src and "nxt[1]" in src


def test_유저_관제탑이_누구인지_안_돌려준다():
    import os
    import tempfile
    os.environ["STORE_PATH"] = tempfile.mktemp(suffix=".sqlite")
    for m in [k for k in list(sys.modules)
              if k in ("store", "main", "db") or k.startswith("routers")]:
        sys.modules.pop(m, None)
    from fastapi.testclient import TestClient
    import main
    c = TestClient(main.app)
    sid = "sess-voyage-abcdefgh"
    body = c.get("/v1/journey", params={"session_id": sid}).text
    # ★ 보는 것은 **되돌아온 값**이오. 「생년월일을 적어 보시오」 같은
    #   안내 문구까지 잡으면 검사가 글을 막습니다 — 자가 글에 맞으면
    #   그날로 자는 거울이 되오.
    assert sid not in body, "세션을 그대로 돌려주오"
    data = c.get("/v1/journey", params={"session_id": sid}).json()
    for key in ("session_id", "chart_id", "user_key", "orders"):
        assert key not in data, "%s 를 돌려주오" % key
