"""Production web error recovery against an isolated API; no real PG calls."""
import json
from audit_checkout_browser import API, WEB, OUT
from playwright.sync_api import sync_playwright

def main():
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge", headless=True)
        birth = dict(year=1993, month=11, day=25, hour=None, minute=0, hour_known=False, sex="F", birth_city="서울")
        chart = pw.request.new_context().post(API + "/v1/chart", data=birth).json()
        seed = dict(year=1993, month=11, day=25, hour=None, minute=0, hourKnown=False, sex="F", sexSet=True, city="서울", concern="money", concernSet=True, chartId=chart["chart_id"], cur="pungun", name="", read=[], skipped=[], seals=[], tier="free", paid=False, axis4=None, admin=False, adminSet=True)
        for name, path, endpoint, retry, success in [
            ("hook", "/?step=a7", "/v1/hook", "무료 해석 다시 불러오기", ".vt"),
            ("free-report", "/pay?step=d0", "/v1/report", "무료 해석 다시 불러오기", ".conversion-primary"),
            ("products", "/pay?step=d1", "/v1/pay/tiers", "상품 다시 불러오기", ".conversion-product"),
        ]:
            ctx = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
            ctx.add_init_script("localStorage.setItem('sd.sound','off');localStorage.setItem('sajudang-session'," + json.dumps(json.dumps(dict(state=seed, version=0))) + ");")
            state = dict(retry=False, failed=0, recovered=0)
            def route_api(route):
                req = route.request
                suffix = req.url.split("sajudang-api.fly.dev", 1)[1]
                headers = {"Access-Control-Allow-Origin": WEB, "Access-Control-Allow-Credentials": "true", "Access-Control-Allow-Headers": "content-type", "Access-Control-Allow-Methods": "GET, POST, OPTIONS"}
                if req.method == "OPTIONS":
                    route.fulfill(status=204, headers=headers)
                elif endpoint in suffix and not state["retry"]:
                    state["failed"] += 1
                    route.fulfill(status=500, json={"detail": "일시적인 서버 오류입니다."}, headers=headers)
                else:
                    response = route.fetch(url=API + suffix)
                    if endpoint in suffix and response.ok:
                        state["recovered"] += 1
                    route.fulfill(response=response, headers={**response.headers, **headers})
            ctx.route("https://sajudang-api.fly.dev/**", route_api)
            page = ctx.new_page()
            try:
                page.goto(WEB + path)
                page.get_by_role("button", name=retry, exact=True).wait_for(timeout=20000)
                state["retry"] = True
                page.get_by_role("button", name=retry, exact=True).click()
                if name == "free-report":
                    page.get_by_role("button", name="추가 해석과 가격 보기", exact=True).wait_for(timeout=20000)
                else:
                    page.locator(success).first.wait_for(timeout=20000)
                assert state["recovered"] > 0
                results.append(dict(name=name, status="passed", **state))
            except Exception as exc:
                results.append(dict(name=name, status="failed", error=str(exc), text=page.locator("body").inner_text(), **state))
            ctx.close()
        browser.close()
    (OUT / "recovery.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf8")
    print(json.dumps(results, ensure_ascii=False))

if __name__ == "__main__":
    main()
