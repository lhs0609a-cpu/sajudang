"""Review all character illustrations in the real report flow on local servers."""
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/visual-review"
WEB = os.getenv("SJD_VISUAL_WEB", "http://127.0.0.1:3037")
API = os.getenv("SJD_VISUAL_API", "http://127.0.0.1:8037")


def request(path, payload=None):
    req = Request(API + path, data=json.dumps(payload).encode() if payload else None,
                  headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=30) as response:
        return json.load(response)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    chart = request("/v1/chart", dict(year=1993, month=5, day=15, hour=None,
                    minute=0, hour_known=False, sex="F", birth_city="서울"))
    lenses = json.loads((ROOT / "seed/lenses.json").read_text(encoding="utf-8"))
    seed = dict(year=1993, month=5, day=15, hour=None, minute=0, hourKnown=False,
                sex="F", sexSet=True, city="서울", concern="health", concernSet=True,
                chartId=chart["chart_id"], sessionId="visual-browser-review",
                cur="myeonsang", name="", read=[], skipped=[], seals=[], tier="free",
                paid=False, axis4=None, admin=False, adminSet=True)
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge", headless=True)
        for width, chars in [(390, lenses), (320, [x for x in lenses if x["id"] in ("myeonsang", "yakcho", "monghwa", "paeseon")])]:
            context = browser.new_context(viewport=dict(width=width, height=844), reduced_motion="reduce")
            context.add_init_script("localStorage.setItem('sd.sound','off');sessionStorage.setItem('sd.qa','1');"
                "localStorage.setItem('sajudang-session'," + json.dumps(json.dumps(dict(state=seed, version=0))) + ");")
            # Only this local API is allowed; do not visit payments or deployed APIs.
            context.route("https://**/*", lambda route: route.abort())
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            for character in chars:
                id = character["id"]
                errors.clear()
                page.goto(WEB + f"/report/{id}?tab=c2", wait_until="networkidle", timeout=90000)
                panel = page.locator(".visual-consultation")
                panel.wait_for(timeout=30000)
                expect(panel.locator(".choice-tile").first).to_be_visible(timeout=30000)
                panel.scroll_into_view_if_needed()
                # Load even collapsed feature tabs for the asset audit. In normal use
                # those images correctly remain lazy until the user opens the tab.
                panel.locator("img").evaluate_all("imgs => imgs.forEach(i => i.loading = 'eager')")
                page.wait_for_function("Array.from(document.querySelectorAll('.visual-consultation img')).every(i => i.complete && i.naturalWidth > 0)")
                assert not page.evaluate("document.documentElement.scrollWidth > innerWidth + 1"), (width, id, "overflow")
                assert not errors, (id, errors)
                panel.screenshot(path=str(OUT / f"{width}-{id}.png"))
                submit = panel.locator(".visual-submit")
                expect(submit).to_be_disabled()
                kind = panel.get_attribute("data-visual-kind")
                if kind == "face":
                    panel.get_by_role("button", name="둥근형", exact=False).click()
                    panel.locator(".face-details summary").click()
                    panel.get_by_role("button", name="눈꼬리가 올라간 눈", exact=False).click()
                elif kind == "body":
                    panel.locator(".body-region-list").get_by_role("button", name="목", exact=True).click()
                    panel.get_by_role("button", name="뒷모습", exact=True).click()
                    panel.locator(".body-map").get_by_role("button", name="등", exact=True).press("Enter")
                    panel.get_by_role("button", name="아프거나 불편합니다", exact=True).click()
                    panel.get_by_role("button", name="일상에 지장이 있습니다", exact=True).click()
                elif kind == "cards":
                    tiles = panel.locator(".choice-tile")
                    for i in (3, 0, 5):
                        tiles.nth(i).click()
                    assert panel.locator(".choice-tile[aria-pressed=true]").count() == 3
                    expect(tiles.nth(1)).to_be_disabled()
                    tiles.nth(0).click()
                    expect(submit).to_be_disabled()
                    tiles.nth(2).click()
                else:
                    panel.locator(".choice-tile").first.click()
                with page.expect_response(lambda r: r.url.endswith("/v1/report") and r.request.method == "POST") as response:
                    submit.click()
                report = response.value.json()
                assert not report.get("extra_error"), report.get("extra_error")
                assert any(c["id"] == kind for c in report["cuts"] + report["locked"]), (id, kind)
                expect(panel.get_by_role("button", name="다시 고르겠습니다")).to_be_enabled(timeout=30000)
                panel.screenshot(path=str(OUT / f"{width}-{id}-selected.png"))
                if kind == "face":
                    panel.get_by_role("button", name="다시 고르겠습니다").click()
                    panel.get_by_role("button", name="네모형", exact=False).filter(has_text="이마와").click()
                    with page.expect_response(lambda r: r.url.endswith("/v1/report") and r.request.method == "POST") as changed:
                        panel.locator(".visual-submit").click()
                    new_cut = next(c for c in changed.value.json()["cuts"] if c["id"] == "face")
                    assert "네모형" in new_cut["html"] and "둥근형" not in new_cut["html"]
                assert "regions" not in page.evaluate("localStorage.getItem('sajudang-session')"), "body input persisted"
                results.append(dict(width=width, lens=id, kind=kind, errors=list(errors)))
                print(json.dumps(results[-1], ensure_ascii=False), flush=True)
            context.close()
        # Contact sheets use the exact same optimized assets served to the app.
        page = browser.new_page(viewport=dict(width=1200, height=900))
        prompts = json.loads((ROOT / "assets/choice-prompts.json").read_text(encoding="utf-8"))
        labels = {}
        for l in lenses:
            def gather(v):
                if isinstance(v, dict):
                    if isinstance(v.get("image"), str):
                        labels.setdefault(Path(v["image"]).name, v.get("label", ""))
                    for item in v.values(): gather(item)
                elif isinstance(v, list):
                    for item in v: gather(item)
            gather(request("/v1/report/choices?lens_id=" + l["id"]))
        groups = [("장면 그림", [x for x in prompts if not x["id"].startswith(("face-", "card-"))]),
                  ("얼굴형", [x for x in prompts if x["id"].startswith("face-")]),
                  ("패", [x for x in prompts if x["id"].startswith("card-")])]
        html = '<!doctype html><html lang="ko"><meta charset="utf-8"><title>성신당 그림 상담 도감</title><style>body{background:#141614;color:#e9dfcd;font:16px sans-serif;margin:30px}h1{font-size:28px}section{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin:24px 0}figure{margin:0;background:#222820;border-radius:10px;overflow:hidden}img{display:block;width:100%;aspect-ratio:1;object-fit:cover}figcaption{padding:12px;font-size:13px;line-height:1.5}small{display:block;color:#b4b3a4;margin-top:4px}</style><h1>성신당 · 맥락에 맞춰 고르는 그림</h1>'
        for index, (title, items) in enumerate(groups):
            part = '<h2>' + title + '</h2><section>'
            for item in items:
                file = item["id"] + ".webp"
                part += f'<figure><img src="{WEB}/choices/{file}"><figcaption>{labels.get(file, item["id"])}<small>{item["id"]}</small></figcaption></figure>'
            part += '</section>'
            page.set_content(html.split('<h1>')[0] + part)
            page.wait_for_function("Array.from(document.images).every(i => i.complete && i.naturalWidth > 0)")
            page.screenshot(path=str(OUT / f"sheet-{index}.png"), full_page=True)
            html += part
        # SVG comparisons: screenshots are a visual review, not a substitute asset.
        svgs = sorted((ROOT / "apps/web/public/choices").glob("*.svg"))
        part = '<h2>부위 비교 도해</h2><section>'
        for file in svgs:
            part += f'<figure><img style="object-fit:contain;background:#eee4d3" src="{WEB}/choices/{file.name}"><figcaption>{labels.get(file.name, file.stem)}</figcaption></figure>'
        part += '</section>'
        page.set_content(html.split('<h1>')[0] + part)
        page.wait_for_function("Array.from(document.images).every(i => i.complete && i.naturalWidth > 0)")
        page.screenshot(path=str(OUT / "sheet-diagrams.png"), full_page=True)
        html += part
        (OUT / "index.html").write_text(html.replace(WEB + "/choices/", "../../apps/web/public/choices/"), encoding="utf-8")
        browser.close()
    (OUT / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
