"""Local browser + real in-process API; synthetic orders, no PG or production calls.

Start Next with NEXT_PUBLIC_API_BASE=http://127.0.0.1:8041 on port 3039.
The browser intercepts that API host and exercises the actual FastAPI handlers.
"""
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "reading-review" / "browser"
OUT.mkdir(parents=True, exist_ok=True)
os.environ.update(STORE_PATH="", REDIS_URL="", DATABASE_URL="",
    STATEMENT_LOG_PATH=str(OUT / "statements.jsonl"), REVIEW_LOG_PATH=str(OUT / "reviews.jsonl"),
    CORS_ORIGINS="http://127.0.0.1:3039")
sys.path.insert(0, str(ROOT / "services" / "api"))
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright, expect
from main import app
import store

WEB = "http://127.0.0.1:3039"
API = "http://127.0.0.1:8041"


def main():
    client = TestClient(app)
    birth = dict(year=1993, month=11, day=25, hour=15, minute=0, hour_known=True, sex="F", birth_city="서울")
    chart = client.post("/v1/chart", json=birth).json()
    seed = dict(year=1993, month=11, day=25, hour=15, minute=0, hourKnown=True,
        sex="F", sexSet=True, city="서울", concern="work", concernSet=True, chartId=chart["chart_id"],
        features=chart["features"], sessionId="reading-browser", cur="pungun", name="", read=[], skipped=[],
        seals=[], tier="all", paid=True, axis4=None, admin=False, adminSet=True)
    store.set_json("orders:reading-browser", ["reading-browser"])
    store.set_json("order:reading-browser", {"status": "paid", "tier": "all", "session_id": "reading-browser"})
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge", headless=True)
        for width in (320, 390, 1280):
            ctx = browser.new_context(viewport={"width": width, "height": 900}, reduced_motion="reduce")
            ctx.add_init_script("localStorage.setItem('sd.sound','off');sessionStorage.setItem('sd.qa','1');localStorage.setItem('sajudang-session'," + json.dumps(json.dumps({"state": seed, "version": 0})) + ");")
            ctx.route("https://**/*", lambda route: route.abort())
            responses = []

            def api_route(route):
                req = route.request
                url = urlsplit(req.url)
                path = url.path + ("?" + url.query if url.query else "")
                cors = {"Access-Control-Allow-Origin": WEB, "Access-Control-Allow-Methods": "GET,POST,OPTIONS", "Access-Control-Allow-Headers": "content-type"}
                if req.method == "OPTIONS":
                    route.fulfill(status=204, headers=cors)
                    return
                # Provider endpoints cannot be reached by this read-only preview.
                if path.startswith("/v1/pay/") and path.split("?")[0] not in ("/v1/pay/tiers", "/v1/pay/peek"):
                    route.fulfill(status=403, content_type="application/json", body='{"detail":"preview"}', headers=cors)
                    return
                response = client.request(req.method, path, content=req.post_data or None, headers={"Content-Type": "application/json"})
                if url.path in ("/v1/report", "/v1/omnibus"):
                    responses.append(response.json())
                route.fulfill(status=response.status_code, body=response.content, content_type="application/json", headers=cors)

            ctx.route(API + "/**", api_route)
            page = ctx.new_page()
            errors = []
            page.on("pageerror", lambda err: errors.append(str(err)))
            page.goto(WEB + "/omnibus", wait_until="networkidle", timeout=90000)
            expect(page.locator(".integrated-reading")).to_be_visible(timeout=30000)
            assert responses[-1]["reading"]["scope"] == "전체"
            before = responses[-1]["reading"]
            page.screenshot(path=str(OUT / f"book-{width}.png"))
            assert not page.evaluate("document.documentElement.scrollWidth > innerWidth + 1"), (width, "overflow")
            form = page.locator(".reading-consultation")
            form.locator("summary").click()
            expect(form.get_by_role("button", name="내 답변으로 풀이 다듬기")).to_be_disabled()
            form.get_by_label("내 경험과 다름", exact=True).check()
            form.get_by_label("업무와 역할", exact=True).check()
            form.get_by_label("이미 바꿔 보았음", exact=True).check()
            form.get_by_role("button", name="내 답변으로 풀이 다듬기").click()
            expect(page.locator("#plan-revised")).to_be_visible(timeout=30000)
            after = responses[-1]["reading"]
            assert before["summary"][0]["id"] not in {c["id"] for c in after["summary"]}
            expect(page.locator("#plan-decision")).to_contain_text("이미 바꿔 보았다고 답했습니다")
            page.locator(".reading-consultation summary").click()
            page.get_by_role("button", name="답변을 지우고 다시 보기").click()
            expect(page.locator("#plan-revised")).to_have_count(0, timeout=30000)
            assert responses[-1]["reading"]["fingerprint"] == before["fingerprint"]
            page.goto(WEB + "/report/pungun?tab=c2", wait_until="networkidle", timeout=90000)
            expect(page.locator(".integrated-reading")).to_be_visible(timeout=30000)
            expect(page.get_by_role("link", name="다른 영역까지 전체 풀이로 읽기")).to_be_visible()
            assert not page.evaluate("document.documentElement.scrollWidth > innerWidth + 1"), (width, "report overflow")
            assert not errors, errors
            results.append({"width": width, "book": True, "report": True, "rejection": True, "reset": True, "overflow": False, "errors": errors})
            ctx.close()
        # A saved client-side tier cannot grant the integrated book.
        order = store.get_json("order:reading-browser")
        order["status"] = "refunded"
        store.set_json("order:reading-browser", order)
        response = client.post("/v1/omnibus", json={"chart_id": chart["chart_id"], "session_id": "reading-browser"})
        assert response.status_code == 402
        browser.close()
    (OUT / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), "utf-8")
    print(json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    main()
