"""Smoke-check every declared navigation target with local synthetic data only."""
import json
import argparse
import re
from pathlib import Path
from urllib.parse import urlsplit
import verify_reading_browser as base
from playwright.sync_api import sync_playwright
from fastapi.testclient import TestClient
import store
import keyguard

OUT=base.ROOT/'artifacts/value-research/browser'
OUT.mkdir(parents=True,exist_ok=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--only',nargs='+')
    args=parser.parse_args()
    client=TestClient(base.app)
    birth=dict(year=1993,month=11,day=25,hour=15,minute=30,hour_known=True,sex='F',birth_city='서울')
    chart=client.post('/v1/chart',json=birth).json()
    store.set_json('orders:value-pages',['value-pages'])
    store.set_json('order:value-pages',dict(status='paid',tier='all',session_id='value-pages'))
    keyguard.FUNNEL_KEY='local-value-browser-only'
    shared=client.post('/v1/share',json={'chart_id':chart['chart_id'],'concern':'work','lens_id':'pungun'}).json()
    seed=dict(year=1993,month=11,day=25,hour=15,minute=30,hourKnown=True,sex='F',sexSet=True,
        city='서울',concern='work',concernSet=True,chartId=chart['chart_id'],features=chart['features'],
        sessionId='value-pages',cur='pungun',name='',read=[],skipped=[],seals=[],tier='all',paid=True,axis4=None,admin=False,adminSet=True)
    src=(base.ROOT/'apps/web/lib/store.ts').read_text('utf-8')
    targets=re.findall(r'\{ id: "(\w+)", name: "[^"]+", href: "([^"]+)" \}',src)
    targets += [('book','/omnibus'),('legal','/legal'),('shared',shared['path']),('admin','/admin')]
    if args.only: targets=[row for row in targets if row[0] in args.only]
    results=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True)
        ctx=browser.new_context(viewport={'width':390,'height':844},reduced_motion='reduce')
        ctx.add_init_script("localStorage.setItem('sd.sound','off');localStorage.setItem('sd.adminkey','local-value-browser-only');localStorage.setItem('sd.reading-preferences',JSON.stringify({instant:true,large:false}));sessionStorage.setItem('sd.qa','1');localStorage.setItem('sajudang-session',"+json.dumps(json.dumps({'state':seed,'version':0}))+');')
        ctx.route('https://**/*',lambda route:route.abort())
        def api_route(route):
            req=route.request;url=urlsplit(req.url)
            path=url.path+('?' +url.query if url.query else '')
            cors={'Access-Control-Allow-Origin':base.WEB,'Access-Control-Allow-Methods':'GET,POST,OPTIONS','Access-Control-Allow-Headers':'content-type,x-admin-token,x-funnel-key'}
            if req.method=='OPTIONS':route.fulfill(status=204,headers=cors);return
            if path.startswith('/v1/pay/') and url.path not in ('/v1/pay/tiers','/v1/pay/peek'):
                route.fulfill(status=403,content_type='application/json',body='{"detail":"Local payment actions disabled"}',headers=cors);return
            response=client.request(req.method,path,content=req.post_data or None,
                headers={k:v for k,v in req.headers.items() if k in ('content-type','x-admin-token','x-funnel-key')})
            route.fulfill(status=response.status_code,body=response.content,content_type='application/json',headers=cors)
        ctx.route(base.API+'/**',api_route)
        page=ctx.new_page();errors=[]
        page.on('pageerror',lambda err:errors.append(str(err)))
        for sid,path in targets:
            errors.clear()
            response=page.goto(base.WEB+path,wait_until='domcontentloaded' if sid=='admin' else 'networkidle',timeout=90000)
            page.locator('.phone').first.wait_for(timeout=30000) if sid!='admin' else page.get_by_role('heading',name='페이지·결과별 품질과 실제 사용자 평가').wait_for(timeout=60000)
            if sid=='admin': page.get_by_role('button',name='실시간 · 5초마다 (멈추기)',exact=True).click()
            if sid in ('c2','c7','book','s1'):
                page.locator('.integrated-reading').wait_for(timeout=60000)
            elif sid.startswith('c') and sid not in ('c8',):
                page.locator('[data-screen]').first.wait_for(timeout=60000)
            elif sid=='shared': page.locator('[data-screen="s1"]').wait_for(timeout=60000)
            overflow=page.evaluate('document.documentElement.scrollWidth > innerWidth + 1')
            if overflow:
                print(json.dumps(page.evaluate("Array.from(document.querySelectorAll('body *')).filter(e=>e.getBoundingClientRect().right>innerWidth+1).slice(0,12).map(e=>({tag:e.tagName,cls:e.className,text:e.textContent.slice(0,70),right:e.getBoundingClientRect().right}))"),ensure_ascii=False),flush=True)
            actual=page.locator('[data-screen]').first.get_attribute('data-screen') if page.locator('[data-screen]').count() else None
            row=dict(id=sid,path=path if sid!='shared' else '/s/[token]',http=response.status if response else None, same_document=response is None,
                actual_screen=actual,overflow=overflow,errors=list(errors),
                note='결제 제공자 호출 차단 · 외부 결제 완료는 미검증' if sid.startswith('d') else '')
            if sid in ('a1','a3','a7','c2','d0','d1','c7','g1','book','admin'):
                page.screenshot(path=str(OUT/f'{sid}-390.png'),timeout=10000)
            results.append(row)
            (OUT/('pages-focused.json' if args.only else 'pages.json')).write_text(json.dumps(results,ensure_ascii=False,indent=2),'utf-8')
            print(json.dumps(row,ensure_ascii=False),flush=True)
        # Explicitly verify the new admin table is populated, not just mounted.
        if any(sid=='admin' for sid,_ in targets):
            page.get_by_role('button',name=re.compile('통합 결과 660개')).wait_for(timeout=60000)
            page.get_by_role('button',name=re.compile('대화·일진·분석지 540개')).wait_for(timeout=60000)
        assert all((r['http']==200 or r['same_document']) and not r['overflow'] and not r['errors'] for r in results),results
        print(json.dumps({'passed':True,'targets':len(results)},ensure_ascii=False),flush=True)
        ctx.close();browser.close()


if __name__=='__main__':main()
