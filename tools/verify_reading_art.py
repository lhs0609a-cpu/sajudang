"""Review public screens with real local API responses and isolated test data."""
import json
import os
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/reading-images"
WEB = "http://127.0.0.1:3028"
sys.path.insert(0, str(ROOT / "services/api"))
# All data stays in this process or a temporary directory; no production services.
for key in ("DATABASE_URL", "REDIS_URL", "STORE_PATH"):
    os.environ[key] = ""
tmp = tempfile.TemporaryDirectory(prefix="sajudang-reading-art-")
os.environ["STATEMENT_LOG_PATH"] = str(Path(tmp.name) / "statements.jsonl")
from fastapi.testclient import TestClient
from main import app
from playwright.sync_api import sync_playwright, expect

client = TestClient(app)
chart_response = client.post("/v1/chart", json=dict(year=1993, month=5, day=15, hour=None, minute=0, hour_known=False, sex="F", birth_city="서울"))
assert chart_response.status_code == 200, chart_response.text
chart = chart_response.json()
shared = client.post("/v1/share", json=dict(chart_id=chart["chart_id"], concern="money", lens_id="pungun", reveal="light")).json()
seed = dict(year=1993, month=5, day=15, hour=None, minute=0, hourKnown=False, sex="F", sexSet=True,
            city="서울", concern="money", concernSet=True, chartId=chart["chart_id"], features=chart["features"],
            cur="pungun", name="", read=[], skipped=[], seals=[], tier="free", paid=False, axis4=None,
            admin=False, adminSet=True, sessionId="reading-art-local-review")
routes = [
    ("entry", "/?step=a1"), ("nickname", "/?step=a2"), ("concerns", "/?step=a5"),
    ("birth", "/?step=a3"), ("time", "/?step=a4"), ("personality", "/?step=a4b"),
    ("chart", "/?step=a6"), ("hook", "/?step=a7"), ("free", "/pay?step=d0"),
    ("checkout", "/pay?step=d1"), ("lobby", "/lobby?tab=b1"), ("readers", "/lobby?tab=b2"),
    ("reader", "/lobby?tab=b3"), ("elements", "/lobby?tab=b4"),
    ("cover", "/report/pungun?tab=c1"), ("report", "/report/pungun?tab=c2"),
    ("cycles", "/report/pungun?tab=c3"), ("locked", "/report/pungun?tab=c4"),
    ("share", "/report/pungun?tab=c5"), ("feedback", "/report/pungun?tab=c6"),
    ("summary", "/summary"), ("daily", "/daily"), ("library", "/me"),
    ("reviews", "/me?tab=r1"), ("relay", "/relay"), ("legal", "/legal"),
    ("shared", shared["path"]), ("missing", "/missing-reading-art-review"),
]
results = []

def api_route(route):
    req = route.request
    parsed = urlsplit(req.url)
    headers = {"Access-Control-Allow-Origin": WEB, "Access-Control-Allow-Credentials": "true", "Access-Control-Allow-Headers": "content-type", "Access-Control-Allow-Methods": "GET,POST,OPTIONS"}
    if req.method == "OPTIONS":
        route.fulfill(status=204, headers=headers)
        return
    path = parsed.path + ("?" + parsed.query if parsed.query else "")
    if any(part in path for part in ("/pay/confirm", "/subscription/confirm", "/voice/")):
        route.fulfill(status=503, json={"detail": "Disabled during local visual review"}, headers=headers)
        return
    response = client.request(req.method, path, content=req.post_data, headers={"Content-Type": "application/json"})
    route.fulfill(status=response.status_code, body=response.content, content_type="application/json", headers=headers)

with sync_playwright() as pw:
    browser = pw.chromium.launch(channel="msedge", headless=True)
    for width in (390, 1440, 320):
        context = browser.new_context(viewport={"width": width, "height": 900}, reduced_motion="reduce")
        context.add_init_script("localStorage.setItem('sd.sound','off');sessionStorage.setItem('sd.qa','1');localStorage.setItem('sajudang-session'," + json.dumps(json.dumps(dict(state=seed, version=0))) + ");")
        context.route("**/v1/**", api_route)
        context.route("**/api/sales-status", lambda route: route.fulfill(json={"ready": False, "reason": "local-review"}))
        context.route("**/*tosspayments*", lambda route: route.abort())
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        selected = routes if width != 320 else [r for r in routes if r[0] in ("concerns", "time", "elements", "free", "report", "summary", "checkout")]
        for name, path in selected:
            errors.clear()
            try:
                page.goto(WEB + path, wait_until="networkidle", timeout=180000)
                if name in ("report", "free", "summary", "daily"):
                    page.wait_for_function("document.querySelectorAll('.cut-art-heading,.element-legend,.dz').length>0", timeout=30000)
                if name == "report":
                    expect(page.locator(".reading-path")).to_be_visible()
                if name == "elements":
                    expect(page.locator(".element-row")).to_have_count(5)
                    assert page.locator(".element-row meter").evaluate_all("els=>els.every(e=>Number.isFinite(e.value)&&e.value>=0)")
                if name == "time":
                    expect(page.locator(".birth-structure .unknown")).to_have_count(1)
                    page.locator("#birth-hour").fill("15")
                    expect(page.locator(".birth-structure .unknown")).to_have_count(0)
                # Scroll through real content to resolve lazy images and reveal sections.
                page.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')")
                page.wait_for_function("[...document.querySelectorAll('img[src*=\"/images/reading/\"],img[src*=\"/images/concerns/\"]')].every(i=>i.complete&&i.naturalWidth>0)", timeout=30000)
                assert not page.evaluate("document.documentElement.scrollWidth>innerWidth+1"), "horizontal overflow"
                assert not errors, errors
                count = page.locator("img[src*='/images/reading/'],img[src*='/images/concerns/']").count()
                assert count > 0 or name in ("concerns", "hook", "missing"), f"Missing illustrations on {name}"
                page.screenshot(path=str(OUT / f"{width}-{name}.png"), full_page=name in ("concerns", "time", "elements"))
                if name == "report":
                    page.locator(".reading-section").first.screenshot(path=str(OUT / f"{width}-report-section.png"))
                result = dict(width=width, screen=name, images=count, overflow=False, errors=[])
            except Exception as exc:
                result = dict(width=width, screen=name, failure=str(exc), errors=list(errors))
                page.screenshot(path=str(OUT / f"{width}-{name}-failure.png"))
            results.append(result)
            print(json.dumps(result, ensure_ascii=True), flush=True)
            (OUT / "browser-results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        context.close()
    browser.close()
client.close()
tmp.cleanup()
assert not any("failure" in result for result in results), "See browser-results.json"
