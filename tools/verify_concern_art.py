"""Check generated concern cards and their selection handoff on local web."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

OUT = Path(__file__).resolve().parents[1] / 'output/concern-images'
with sync_playwright() as pw:
    browser = pw.chromium.launch(channel='msedge', headless=True)
    results = []
    for width in [320, 390, 768, 1440]:
        context = browser.new_context(viewport={'width': width, 'height': 900}, reduced_motion='reduce')
        context.add_init_script("localStorage.setItem('sd.sound','off');localStorage.setItem('sajudang-session',JSON.stringify({state:{admin:false,adminSet:true,concernSet:false},version:0}));")
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto('http://127.0.0.1:3028/?step=a5', wait_until='networkidle', timeout=180000)
        cards = page.locator('.concern-card')
        expect(cards).to_have_count(6, timeout=60000)
        page.wait_for_function("[...document.querySelectorAll('.concern-art img')].every(i=>i.complete&&i.naturalWidth>0)")
        expect(page.locator('.concern-card[aria-pressed=true]')).to_have_count(0)
        for index in range(6):
            cards.nth(index).click()
            expect(page.locator('.concern-card[aria-pressed=true]')).to_have_count(1)
            expect(cards.nth(index)).to_have_attribute('aria-pressed', 'true')
        assert not page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
        page.locator('.concern-grid').screenshot(path=str(OUT / f'choices-{width}.png'))
        page.screenshot(path=str(OUT / f'page-{width}.png'), full_page=True)
        page.locator('[data-screen="a5"] button.btn.mt').click()
        expect(page.locator('[data-screen="a3"] .concern-reminder img')).to_have_attribute('src', '/images/concerns/health-v1.webp')
        assert not errors, errors
        results.append({'width': width, 'loaded': 6, 'selection': 'passed', 'handoff': 'passed', 'overflow': False})
        context.close()
    browser.close()
    (OUT / 'browser-results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results))

