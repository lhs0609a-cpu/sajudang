const {spawn}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const out=path.resolve('output/preconsult-v3/screens');
fs.mkdirSync(out,{recursive:true});
const base='http://127.0.0.1:3038',api='http://127.0.0.1:8018',port=19391;
const browser=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',[
  '--headless=new','--no-first-run',`--remote-debugging-port=${port}`,
  `--user-data-dir=${path.join(os.tmpdir(),'sjd-entry-v2-'+process.pid)}`,'about:blank'
],{windowsHide:true,stdio:'ignore'});
const pause=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 let pages;for(let i=0;i<80;i++){try{pages=await(await fetch(`http://127.0.0.1:${port}/json`)).json();if(pages.some(p=>p.type==='page'))break;}catch{}await pause(200);}
 if(!pages)throw Error('Browser did not start');
 const ws=new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);await new Promise(r=>ws.onopen=r);
 let n=0;const pending=new Map(),exceptions=[],results=[];
 ws.onmessage=e=>{const x=JSON.parse(e.data);if(x.method==='Runtime.exceptionThrown')exceptions.push(x.params.exceptionDetails);if(x.id){const p=pending.get(x.id);pending.delete(x.id);x.error?p.reject(x.error):p.resolve(x.result);}};
 const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++n;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
 const run=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;};
 const until=async expression=>{for(let i=0;i<180;i++){if(await run(`Boolean(document.body && (${expression}))`))return;await pause(200);}throw Error('Timeout '+expression);};
 const click=async text=>{await until(`[...document.querySelectorAll('button')].some(b=>b.textContent.includes(${JSON.stringify(text)})&&!b.disabled)`);await run(`[...document.querySelectorAll('button')].find(b=>b.textContent.includes(${JSON.stringify(text)})&&!b.disabled).click()`);await pause(350);};
 const fill=async(id,value)=>{await run(`(()=>{const e=document.getElementById(${JSON.stringify(id)});Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(e,${JSON.stringify(value)});e.dispatchEvent(new Event('input',{bubbles:true}));})()`);await pause(100);};
 const screen=step=>until(`document.querySelector('[data-screen="${step}"]')`);
 const capture=async(name,width)=>{
  await until(`[...document.querySelectorAll('.entry-art img,.entry-concern-image img')].every(i=>i.complete&&i.naturalWidth>0)`);
  await run('scrollTo(0,0)');await pause(450);
  const check=await run(`({overflow:document.documentElement.scrollWidth>innerWidth+1,broken:[...document.images].filter(i=>i.complete&&!i.naturalWidth).map(i=>i.src),title:document.querySelector('h1')?.innerText,text:document.body.innerText})`);
  assert.equal(check.overflow,false,name+' overflow');assert.equal(check.broken.length,0,name+' broken image');assert.ok(!check.text.includes('???'),name+' corrupted text');
  const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
  fs.writeFileSync(path.join(out,`${width}-${name}.png`),Buffer.from(shot.data,'base64'));
  results.push({name,width,overflow:check.overflow,title:check.title});
 };
 try {
  await send('Runtime.enable');await send('Page.enable');
  const chart=await(await fetch(api+'/v1/chart',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({year:1993,month:11,day:25,hour:15,minute:55,hour_known:true,sex:'M',birth_city:'서울'})})).json();
  assert.ok(chart.chart_id);
  const state={admin:false,adminSet:true,chartId:chart.chart_id,cur:'pungun',concern:'money',tier:'free',paid:false,year:1993,month:11,day:25,hour:15,minute:55,hourKnown:true,sex:'M',city:'서울',axis4:'INTJ',hookReview:null};
  await send('Page.addScriptToEvaluateOnNewDocument',{source:`if(location.origin===${JSON.stringify(base)}){localStorage.setItem('sd.sound','off');if(!sessionStorage.getItem('reading-v2-test')){localStorage.setItem('sajudang-session',JSON.stringify({state:${JSON.stringify(state)},version:0}));sessionStorage.setItem('reading-v2-test','1');}}`});
  for (const width of [390,320,1920]) {
    if(width!==390) await run(`(()=>{const saved=JSON.parse(localStorage.getItem('sajudang-session'));saved.state.topicPick=null;localStorage.setItem('sajudang-session',JSON.stringify(saved));})()`);
    await send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:width<900});
    await send('Page.navigate',{url:base+'/pay?step=d0'});await screen('d0');
    await until(`document.querySelector('.reading-evidence .blk') && document.querySelector('.locked-veil')`);
    await capture('d0',width);
    const media=await run(`(()=>{const e=document.querySelector('.scr>.sceneart');return {w:e.clientWidth,h:e.clientHeight,parent:e.parentElement.clientWidth,display:getComputedStyle(e).display}})()`);
    assert.ok(media.w>width*0.25&&media.h>140,JSON.stringify(media));
    assert.equal(await run(`document.querySelector('.reading-evidence').tagName`),'SECTION');
    assert.ok(await run(`document.querySelectorAll('.reading-evidence .blk').length<=3`));
    const button=await run(`(()=>{const b=document.querySelector('.extraask .go');return b?{w:b.clientWidth,h:b.clientHeight}:null})()`);
    assert.ok(button&&button.w>200&&button.h>=56,JSON.stringify(button));
    results.push({width,media,button,freeScope:true,visibleEvidence:true});
    if(width===390){
      await run(`document.querySelector('.extraask').scrollIntoView({block:'center'})`);await pause(500);
      fs.writeFileSync(path.join(out,'390-question.png'),Buffer.from((await send('Page.captureScreenshot',{format:'png'})).data,'base64'));
      await run(`document.querySelectorAll('.extraask .og').forEach(g=>g.querySelector('button').click())`);await pause(350);
      assert.equal(await run(`document.querySelector('.extraask .go').disabled`),false);
      await click('이걸로 보겠습니다');await until(`document.querySelector('.reading-evidence .blk')&&!document.querySelector('.extraask')`);
      results.push({questionSubmission:true});
    }
  }
  await send('Page.navigate',{url:base+'/lobby?tab=b2'});await until(`document.querySelectorAll('.op.face').length>=20`);
  await until(`document.querySelectorAll('.op.face .charart img').length>=20`);
  await run(`document.querySelectorAll('.op.face .charart img').forEach(i=>i.loading='eager')`);
  await until(`[...document.querySelectorAll('.op.face .charart img')].every(i=>i.complete&&i.naturalWidth>0)`);
  assert.ok(await run(`[...document.querySelectorAll('.op.face .charart')].every(e=>getComputedStyle(e).backgroundImage==='none'&&getComputedStyle(e).backgroundColor==='rgba(0, 0, 0, 0)')`));
  await capture('characters',1920);
  await run(`document.querySelector('.op.face').scrollIntoView({block:'start'})`);await pause(350);
  fs.writeFileSync(path.join(out,'1920-character-cards.png'),Buffer.from((await send('Page.captureScreenshot',{format:'png'})).data,'base64'));
  results.push({transparentCharacterBackgrounds:20});
  await send('Page.navigate',{url:base+'/report/pungun?tab=c4'});await screen('c4');await until(`document.querySelector('.locked-veil')`);await capture('c4',1920);
  assert.equal(await run(`document.querySelectorAll('.next-reading .locked-veil').length`),1);
  const firstQuestion=await run(`document.querySelector('.preview-focus h3').textContent`);
  await run(`document.querySelectorAll('.preview-questions button')[1].click()`);await pause(150);
  assert.notEqual(await run(`document.querySelector('.preview-focus h3').textContent`),firstQuestion);
  assert.equal(await run(`document.querySelectorAll('.preview-questions button[aria-pressed=true]').length`),1);
  results.push({singleFocusedPreview:true,questionSwitchUpdatesExcerpt:true});
  await run(`document.querySelector('.next-reading').scrollIntoView({block:'start'})`);await pause(350);
  fs.writeFileSync(path.join(out,'1920-locked-preview.png'),Buffer.from((await send('Page.captureScreenshot',{format:'png'})).data,'base64'));
  await click('이 질문의 다음 내용');await screen('d1');await until(`document.querySelector('.conversion-product')`);await capture('d1',1920);
  await run(`document.querySelector('.conversion-product').click()`);await until(`document.querySelector('.paid-preview .locked-veil')`);
  results.push({selectedProductHasMaskedPreview:true});
  for (const width of [390,320]) {
    await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:true});
    for(const [url,name,ready] of [
      ['/lobby?tab=b1','b1',`document.querySelector('[data-screen="b1"] .og')`],
      ['/lobby?tab=b2','characters',`document.querySelector('.op.face .character-question')`],
      ['/lobby?tab=b3','b3',`document.querySelector('.consultation-scope')`],
      ['/report/pungun?tab=c1','c1',`document.querySelector('[data-screen="c1"] .conversion-card')`],
      ['/report/pungun?tab=c2','c2',`document.querySelector('.next-reading .locked-veil')`],
      ['/report/pungun?tab=c3','c3',`document.querySelector('[data-screen="c3"] .locked-veil')`],
      ['/report/pungun?tab=c4','c4',`document.querySelector('.next-reading .locked-veil')`],
      ['/pay?step=d1','d1',`document.querySelector('.conversion-product')`]
    ]) {await send('Page.navigate',{url:base+url});await until(ready);await capture(name,width);
      if(name==='characters') assert.ok(await run(`[...document.querySelectorAll('.op.face')].every(e=>{const r=e.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth+1})`),'Character cards clipped');
      if(name==='d1') assert.ok(await run(`document.querySelector('#pricelist').getBoundingClientRect().top<innerHeight`),'Prices require an extra screen of introduction');
    }
  }
  await send('Page.navigate',{url:base+'/report/baegun?tab=c4'});await screen('c4');await until(`document.querySelector('.next-reading .locked-veil')`);
  await click('이 질문의 다음 내용');await screen('d1');
  assert.equal(await run(`JSON.parse(localStorage.getItem('sajudang-session')).state.cur`),'baegun');
  results.push({directCharacterLinkKeepsPurchaseContext:true});
  assert.equal(exceptions.length,0,JSON.stringify(exceptions));
  fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({results,exceptions},null,2));console.log('PASS',results.length,'checks',out);
 } finally {await Promise.race([send('Browser.close').catch(()=>{}),pause(1500)]);ws.close();browser.kill();}
})().catch(e=>{console.error(e);browser.kill();process.exitCode=1;});
