"""Live web bundle with isolated API data. No production analytics or PG requests."""
import json
import os
import re
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out/conversion-improvements/browser"
OUT.mkdir(parents=True, exist_ok=True)
WEB = os.getenv("SJD_AUDIT_WEB", "http://127.0.0.1:3029")
API = "http://127.0.0.1:8029"


def main():
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge", headless=True)
        for width, answer in [(320, "neutral"), (390, "yes"), (390, "no"), (1920, "neutral"), (390, "ready"), (390, "temporary")]:
            ctx = browser.new_context(viewport={"width": width, "height": 844}, reduced_motion="reduce")
            ctx.add_init_script("localStorage.setItem('sd.sound','off'); if(!localStorage.getItem('sajudang-session')) localStorage.setItem('sajudang-session',JSON.stringify({state:{admin:false,adminSet:true},version:0}));")
            status_calls = [0]
            if answer in ("ready", "temporary"):
                def sales_route(route):
                    status_calls[0] += 1
                    temporary = answer == "temporary" and status_calls[0] == 1
                    route.fulfill(json={"ready":not temporary,"reason":"temporary" if temporary else None})
                ctx.route("**/api/sales-status", sales_route)
            page = ctx.new_page()
            errors, requests, snapshots = [], [], []
            page.on("pageerror", lambda e: errors.append(str(e)))

            def api_route(route):
                request = route.request
                path = request.url.split("sajudang-api.fly.dev", 1)[1]
                requests.append(path.split("?")[0])
                if request.method == "OPTIONS":
                    route.fulfill(status=204, headers={"Access-Control-Allow-Origin": WEB,
                        "Access-Control-Allow-Credentials": "true", "Access-Control-Allow-Headers": "content-type", "Access-Control-Allow-Methods": "GET, POST, OPTIONS"})
                    return
                response = route.fetch(url=API + path)
                body = response.body()
                if path == "/v1/pay/prepare" and response.status == 200:
                    # Isolate the WEB sellability gate from the provider config.
                    data = response.json()
                    data.update(enabled=True, client_key="test_ck_browser_audit")
                    body = json.dumps(data).encode()
                route.fulfill(status=response.status, body=body, headers={**response.headers,
                    "Access-Control-Allow-Origin": WEB, "Access-Control-Allow-Credentials": "true"})

            ctx.route("https://sajudang-api.fly.dev/**", api_route)
            ctx.route(re.compile(r"https://[^/]*tosspayments\.com/.*"), lambda route: route.abort())

            def snapshot(screen):
                page.locator(f'[data-screen="{screen}"]').wait_for()
                text = page.locator("body").inner_text()
                data = page.evaluate("""() => ({height:document.documentElement.scrollHeight,
                    viewport:innerHeight,overflow:document.documentElement.scrollWidth>innerWidth,
                    buttons:[...document.querySelectorAll('button')].map(b=>({text:b.innerText,disabled:b.disabled}))})""")
                snapshots.append({"screen": screen, "chars": len(text), **data})
                (OUT / f"{width}-{answer}-{screen}.txt").write_text(text, encoding="utf8")
                page.screenshot(path=str(OUT / f"{width}-{answer}-{screen}.png"), full_page=False)

            try:
                page.goto(WEB + "/?step=a1")
                snapshot("a1")
                page.get_by_role("button", name="내 고민으로 무료 해석 보기", exact=True).click()
                snapshot("a5")
                page.get_by_role("button", name="돈 버는 것, 모이는 것").click()
                page.get_by_role("button", name="이 고민으로 이어가기", exact=True).click()
                snapshot("a3")
                page.locator("#birth-year").fill("1993")
                page.locator("#birth-month").fill("11")
                page.locator("#birth-day").fill("25")
                page.get_by_role("button", name="여성", exact=True).click()
                page.get_by_role("button", name="태어난 시간으로 이어가기", exact=True).click()
                snapshot("a4")
                page.get_by_role("button", name="시간을 모르오 · 시주 없이 보기", exact=True).click()
                page.get_by_role("button", name="내 고민의 무료 해석 읽기", exact=True).wait_for(timeout=30000)
                snapshot("a6")
                page.get_by_role("button", name="내 고민의 무료 해석 읽기", exact=True).click()
                page.locator(".vt").first.wait_for(timeout=30000)
                snapshot("a7")
                assert page.get_by_role("button", name="응답 건너뛰고 무료 요약 보기", exact=True).count() == 0
                name = {"yes":"그렇소", "no":"아니오"}.get(answer,"잘 모르겠소")
                for i in range(5):
                    page.get_by_role("button", name=name, exact=True).last.click()
                    page.wait_for_timeout(850)
                page.get_by_role("button", name="무료 해석과 오늘의 행동 보기", exact=True).click()
                page.get_by_role("button", name="추가 해석과 가격 보기", exact=True).wait_for(timeout=30000)
                snapshot("d0")
                assert page.locator(".reading-evidence").get_attribute("open") is None
                assert snapshots[-1]["height"] / snapshots[-1]["viewport"] < 5, "summary too long"
                if answer == "no":
                    assert "맞지 않았던 5마디" in page.locator("body").inner_text()
                    page.reload()
                    page.get_by_text("맞지 않았던 5마디는 접어 두겠소.", exact=True).wait_for()
                else:
                    assert "맞지 않았던" not in page.locator("body").inner_text()
                page.locator(".reading-evidence summary").click()
                assert page.locator(".reading-evidence .blk").count() > 0
                page.locator(".reading-evidence summary").click()
                page.get_by_role("button", name="추가 해석과 가격 보기", exact=True).click()
                page.locator(".conversion-product").first.wait_for(timeout=30000)
                page.locator(".conversion-product").first.click()
                page.locator(".paid-preview").wait_for(timeout=30000)
                if answer == "temporary":
                    page.get_by_role("button", name="결제 연결 다시 확인하기", exact=True).click()
                if answer in ("ready", "temporary"):
                    page.get_by_role("button", name="19,900원 결제하기", exact=True).wait_for(timeout=30000)
                else:
                    page.get_by_text("현재 유료 판매를 준비하고 있소.", exact=True).wait_for()
                    assert "/v1/pay/prepare" not in requests, "unavailable sales must not create orders"
                assert "/v1/events" not in requests, "QA must not contaminate analytics"
                snapshot("d1")
                text = page.locator("body").inner_text()
                assert "잠시 후 결제를 다시 시도" not in text
                assert not any(x["overflow"] for x in snapshots)
                results.append({"width": width, "answer": answer, "reached": "d1", "screens": snapshots,
                    "checkout_button_visible": bool(page.get_by_role("button", name=re.compile(r"원 결제하기$")).count()),
                    "seller_setup_message": "판매자 정보 등록" in text,
                    "errors": errors, "requests": requests})
            except Exception as exc:
                page.screenshot(path=str(OUT / f"{width}-{answer}-failure.png"))
                (OUT / f"{width}-{answer}-failure.txt").write_text(page.locator("body").inner_text(), encoding="utf8")
                results.append({"width": width, "answer": answer, "failure": str(exc), "screens": snapshots, "errors": errors})
            finally:
                ctx.close()
            print(json.dumps({k: v for k, v in results[-1].items() if k not in ("screens", "requests")}), flush=True)
            (OUT / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf8")
        browser.close()
    assert not any("failure" in r or r["errors"] for r in results), "browser regression failed"


if __name__ == "__main__":
    main()
