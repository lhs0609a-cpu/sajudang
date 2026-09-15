"""Every public page and report tab in three viewports; API/analytics isolated."""
import json, os, re
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'out/design-20260909/browser';OUT.mkdir(parents=True,exist_ok=True)
WEB=os.getenv('SJD_AUDIT_WEB','http://127.0.0.1:3029')
API='http://127.0.0.1:8029'
ROUTES=[('entry','/?step=a1'),('concern','/?step=a5'),('birth','/?step=a3'),('hour','/?step=a4'),('chart','/?step=a6'),('hook','/?step=a7'),('free','/pay?step=d0'),('pay','/pay?step=d1'),('lobby','/lobby?tab=b1'),('readers','/lobby?tab=b2'),('reader','/lobby?tab=b3'),('pillars','/lobby?tab=b4'),('cover','/report/pungun?tab=c1'),('reading','/report/pungun?tab=c2'),('cycles','/report/pungun?tab=c3'),('locked','/report/pungun?tab=c4'),('share','/report/pungun?tab=c5'),('reflection','/report/pungun?tab=c6'),('summary','/summary'),('daily','/daily'),('library','/me'),('relay','/relay'),('legal','/legal'),('admin','/admin'),('not-found','/missing-design-page')]

def main():
 results=[]
 with sync_playwright() as pw:
  req=pw.request.new_context()
  chart=req.post(API+'/v1/chart',data=dict(year=1993,month=11,day=25,hour=None,minute=0,hour_known=False,sex='F',birth_city='서울')).json()
  shared=req.post(API+'/v1/share',data=dict(chart_id=chart['chart_id'],concern='money',lens_id='pungun',reveal='light')).json()
  ROUTES.append(('shared',shared['path']))
  seed=dict(year=1993,month=11,day=25,hour=None,minute=0,hourKnown=False,sex='F',sexSet=True,city='서울',concern='money',concernSet=True,chartId=chart['chart_id'],cur='pungun',name='',read=[],skipped=[],seals=[],tier='free',paid=False,axis4=None,admin=False,adminSet=True)
  browser=pw.chromium.launch(channel='msedge',headless=True)
  for width in (320,390,1440):
   ctx=browser.new_context(viewport=dict(width=width,height=900),reduced_motion='reduce')
   ctx.add_init_script("localStorage.setItem('sd.sound','off');sessionStorage.setItem('sd.qa','1');if(!localStorage.getItem('sajudang-session'))localStorage.setItem('sajudang-session',"+json.dumps(json.dumps(dict(state=seed,version=0)))+");")
   def api_route(route):
    suffix=route.request.url.split('sajudang-api.fly.dev',1)[1]
    headers={'Access-Control-Allow-Origin':WEB,'Access-Control-Allow-Headers':'content-type','Access-Control-Allow-Methods':'GET,POST,OPTIONS','Access-Control-Allow-Credentials':'true'}
    if route.request.method=='OPTIONS':route.fulfill(status=204,headers=headers);return
    response=route.fetch(url=API+suffix)
    route.fulfill(response=response,headers={**response.headers,**headers})
   ctx.route('https://sajudang-api.fly.dev/**',api_route)
   ctx.route(re.compile(r'https://[^/]*tosspayments\.com/.*'),lambda r:r.abort())
   page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   for name,path in ROUTES:
    errors.clear()
    try:
     page.goto(WEB+path,wait_until='networkidle',timeout=30000)
     if path.startswith('/report/'):
      page.locator('.phone[data-screen]').wait_for(timeout=15000)
     page.evaluate('document.fonts.ready')
     page.wait_for_timeout(200)
     info=page.evaluate('''() => ({overflow:document.documentElement.scrollWidth>innerWidth+1,height:document.documentElement.scrollHeight,phoneWidth:document.querySelector('.phone')?.getBoundingClientRect().width,railVisible:!!document.querySelector('.brand-rail')&&getComputedStyle(document.querySelector('.brand-rail')).display!=='none',bg:getComputedStyle(document.documentElement).getPropertyValue('--bg').trim(),screen:document.querySelector('[data-screen]')?.dataset.screen,chars:document.body.innerText.length})''')
     page.screenshot(path=str(OUT/f'{width}-{name}.png'),full_page=False)
     result=dict(width=width,page=name,errors=list(errors),**info)
     assert not info['overflow'], 'horizontal overflow'
     assert info['bg']=='#141614','brand styles missing'
     assert not errors,'page JavaScript error'
    except Exception as e:
     result=dict(width=width,page=name,failure=str(e),errors=list(errors))
     page.screenshot(path=str(OUT/f'{width}-{name}-failure.png'))
    results.append(result)
    print(json.dumps(result),flush=True)
    (OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
   ctx.close()
  browser.close()
 assert not any('failure' in r for r in results)

if __name__=='__main__':main()
