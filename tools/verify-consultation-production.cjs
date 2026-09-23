const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const {spawn} = require('node:child_process');
const api = 'https://sajudang-api.fly.dev';
const site = process.argv.includes('--local') ? 'http://localhost:3000' : 'https://saju.megaload.co.kr';
const rejected = process.argv.includes('--rejected');
const out = path.resolve('output/consultation-depth');
const pause = ms => new Promise(r => setTimeout(r, ms));
async function json(url, body) {
  const res = await fetch(url, body ? {method:'POST', headers:{'content-type':'application/json'},body:JSON.stringify(body),signal:AbortSignal.timeout(45000)} : {signal:AbortSignal.timeout(45000)});
  assert.equal(res.status, 200, url);
  return res.json();
}
(async () => {
  const health = await json(api + '/health');
  assert.equal(health.store.durable, true);
  const chart = await json(api + '/v1/chart', {year:1993,month:11,day:25,hour_known:false,sex:'F',birth_city:'서울'});
  const free = await json(api + '/v1/report', {chart_id:chart.chart_id,lens_id:'pungun',tier:'free',concern:'work'});
  assert.equal(free.practice.steps.length, 3);
  assert.equal(free.practice.version, 2);
  for(const key of ['focus','example','decision','trap','review'])assert.ok(free.practice[key]?.length>45,key);
  assert.ok(free.cuts.some(c=>c.html.includes('free-depth-workbook')));
  assert.ok(free.cuts.some(c=>c.html.includes('free-depth-essay')));
  assert.ok(free.cuts.every(c=>!c.html.includes('consultation-method')));
  assert.ok(free.cuts.every(c=>!c.html.includes('여덟 글자')));
  const dongja = await json(api + '/v1/report', {chart_id:chart.chart_id,lens_id:'dongja',tier:'free',concern:'work'});
  assert.ok(dongja.cuts.some(c=>c.html.includes('consultation-method')));
  assert.equal(dongja.locked.length, 0);
  console.log('PASS production API: expanded free text, action steps, consultation, access boundary, unknown hour, durable storage');
  if (process.argv.includes('--api-only')) return;
  const port = 19427;
  const browser = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', ['--headless=new','--no-first-run',`--remote-debugging-port=${port}`,`--user-data-dir=${path.join(os.tmpdir(),'sjd-production-'+Date.now())}`,'about:blank'], {windowsHide:true,stdio:'ignore'});
  let ws, send;
  try {
    let pages;
    for(let i=0;i<60;i++){try{pages=await(await fetch(`http://127.0.0.1:${port}/json`)).json();if(pages.some(p=>p.type==='page'))break;}catch{}await pause(200);}
    assert.ok(pages);
    ws = new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);
    await new Promise(r=>ws.onopen=r);
    let id=0;const pending=new Map(), exceptions=[];
    ws.onmessage=e=>{const r=JSON.parse(e.data);if(r.method==='Runtime.exceptionThrown')exceptions.push(r.params.exceptionDetails.text);if(r.id){const p=pending.get(r.id);pending.delete(r.id);r.error?p.reject(r.error):p.resolve(r.result);}};
    send=(method,params={})=>new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}));});
    const run=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});assert.ok(!r.exceptionDetails,JSON.stringify(r.exceptionDetails));return r.result.value;};
    await send('Runtime.enable');await send('Page.enable');
    const state={admin:false,adminSet:true,chartId:chart.chart_id,cur:'pungun',concern:'work',tier:'free',paid:false,year:1993,month:11,day:25,hourKnown:false,sex:'F',city:'서울',hookReview:null,topicPick:{chartId:chart.chart_id,concern:'work',choice:''}};
    if(process.argv.includes('--inline-checks')){state.concern='money';state.topicPick.concern='money';}
    if(rejected) state.hookReview={chartId:chart.chart_id,concern:'work',lensId:'pungun',edition:'first-reading-v2',answers:{'0':false,'1':false}};
    await send('Page.addScriptToEvaluateOnNewDocument',{source:`if(location.origin===${JSON.stringify(site)}){localStorage.setItem('sd.sound','off');localStorage.setItem('sajudang-session',JSON.stringify({state:${JSON.stringify(state)},version:0}));}`});
    const results=[];
    for(const width of [390,1280,1920]){
      await send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:width<900});
      await send('Page.navigate',{url:site+'/pay?step=d0'});
      let ready=false;
      for(let i=0;i<160;i++){if(await run(rejected ? `document.querySelectorAll('.reading-evidence .blk').length>=5` : `document.querySelectorAll('.practice-steps li').length===3 && !!document.querySelector('.next-reading')`)){ready=true;break;}await pause(250);}
      assert.ok(ready,'New production UI did not load');
      const speakers=await run(`Array.from(document.querySelectorAll('.reading-speaker')).map(e=>e.dataset.speaker)`);
      assert.ok(speakers.length>=5,'Missing repeated character attribution');
      assert.ok(speakers.every(id=>id==='pungun'),'Incorrect reading character');
      await run(`document.querySelector('.reading-speaker').scrollIntoView({block:'center'})`);
      for(let i=0;i<40;i++){if(await run(`(()=>{const img=document.querySelector('.reading-speaker img');return img.complete&&img.naturalWidth>0})()`))break;await pause(150);}
      assert.ok(await run(`document.querySelector('.reading-speaker img').naturalWidth>0`),'Portrait did not load');
      if(!rejected){
        await run(`document.querySelector('.free-reading-detail .reading-voice').scrollIntoView({block:'start'})`);await pause(500);
        const portraitShot=await send('Page.captureScreenshot',{format:'png'});
        fs.writeFileSync(path.join(out,`character-free-${width}.png`),Buffer.from(portraitShot.data,'base64'));
      }
      const evidence=await run(`Array.from(document.querySelectorAll('.reading-evidence .blk')).map(e=>({opacity:getComputedStyle(e).opacity,display:getComputedStyle(e).display,visibility:getComputedStyle(e).visibility,chars:e.innerText.length}))`);
      assert.ok(evidence.length>0);
      assert.ok(evidence.every(e=>Number(e.opacity)>0 && e.display!=='none' && e.visibility!=='hidden' && e.chars>0),'Reading evidence is invisible: '+JSON.stringify(evidence));
      if(rejected){
        await run(`document.querySelector('.reading-evidence').scrollIntoView({block:'start'})`);await pause(500);
        const shot=await send('Page.captureScreenshot',{format:'png'});
        fs.writeFileSync(path.join(out,`production-rejected-${width}.png`),Buffer.from(shot.data,'base64'));
        assert.equal(await run(`document.documentElement.scrollWidth>innerWidth+1`),false);
        results.push({width,rejected:true,visibleBlocks:evidence.length});
        continue;
      }
      const checks=await run(`(()=>{const action=document.querySelector('.practice-steps');const next=document.querySelector('.next-reading');return {overflow:document.documentElement.scrollWidth>innerWidth+1,essays:document.querySelectorAll('.free-depth-essay').length,actionBeforePreview:!!(action.compareDocumentPosition(next)&Node.DOCUMENT_POSITION_FOLLOWING),steps:action.children.length}})()`);
      assert.equal(checks.overflow,false);assert.ok(checks.essays>=2);assert.ok(checks.actionBeforePreview);assert.equal(checks.steps,3);
      await run(`document.querySelector('.practice-steps').scrollIntoView({block:'center'})`);await pause(400);
      const shot=await send('Page.captureScreenshot',{format:'png'});
      fs.writeFileSync(path.join(out,`production-${width}.png`),Buffer.from(shot.data,'base64'));
      results.push({width,...checks});
    }
    // Deliberately keep the session on pungun while opening a different report.
    await send('Page.navigate',{url:site+'/report/baegun?tab=c4'});
    let characterReady=false;
    for(let i=0;i<160;i++){if(await run(`document.querySelectorAll('.free-reading-detail .reading-speaker').length>=3`)){characterReady=true;break;}await pause(250);}
    assert.ok(characterReady,'Direct character report failed');
    assert.ok(await run(`Array.from(document.querySelectorAll('.reading-speaker')).every(e=>e.dataset.speaker==='baegun')`),'Report portrait used stale session character');
    await run(`document.querySelector('.free-reading-detail').scrollIntoView({block:'start'})`);await pause(700);
    const characterShot=await send('Page.captureScreenshot',{format:'png'});
    fs.writeFileSync(path.join(out,'character-reading.png'),Buffer.from(characterShot.data,'base64'));
    await send('Page.navigate',{url:site+'/report/dongja?tab=c2'});
    let bodyReady=false;
    for(let i=0;i<160;i++){if(await run(`document.querySelectorAll('.reading-section .reading-speaker').length>=3`)){bodyReady=true;break;}await pause(250);}
    assert.ok(bodyReady,'Full report character headings missing');
    assert.ok(await run(`Array.from(document.querySelectorAll('.reading-speaker')).every(e=>e.dataset.speaker==='dongja')`),'Full report used incorrect character');
    await send('Page.navigate',{url:site+'/?step=a7'});
    let hookReady=false;
    for(let i=0;i<160;i++){if(await run(`!!document.querySelector('.hook-chapter .reading-speaker')`)){hookReady=true;break;}await pause(250);}
    assert.ok(hookReady,'First dialogue character heading missing');
    assert.equal(await run(`document.querySelector('.hook-chapter .reading-speaker').dataset.speaker`),'pungun');
    if(process.argv.includes('--inline-checks')){
      const characters=['baegun','cheongam','sigye','eunbyeol','jeokhyeol','monghwa','seoyeok','paeseon','myeonsang','wolha','hongmae','yeondam','hwagyeong','haengsu','hunjang','yakcho','ilgwan','nopa','pungun','dongja'];
      for(const character of characters){
        await send('Page.navigate',{url:site+'/report/'+character+'?tab=c2'});
        let loaded=false;
        for(let i=0;i<160;i++){if(await run(`!!document.querySelector('.reading-section .reading-speaker[data-speaker="${character}"]')`)){loaded=true;break;}await pause(200);}
        if (!loaded) {
          fs.writeFileSync(path.join(out,'failed-character.json'),JSON.stringify({character,body:await run(`document.body.innerText`),url:await run(`location.href`),exceptions},null,2));
        }
        assert.ok(loaded,character+' did not load');
        const cards=await run(`Array.from(document.querySelectorAll('.inline-paid-reading')).map(e=>({lens:e.dataset.lens,chapter:e.dataset.chapter,hasTeaser:!!e.querySelector('blockquote p')?.innerText,withinReading:!!e.closest('.reading-section')}))`);
        const expected=['pungun','dongja'].includes(character)?0:3;
        assert.equal(cards.length,expected,character+' inline count');
        assert.equal(new Set(cards.map(c=>c.chapter)).size,expected,character+' repeated chapter');
        assert.ok(cards.every(c=>c.lens===character&&c.hasTeaser&&c.withinReading));
        results.push({character,inlineQuestions:cards.length});
        console.log('PASS inline reading',character,cards.length);
      }
      await send('Emulation.setDeviceMetricsOverride',{width:390,height:900,deviceScaleFactor:1,mobile:true});
      await send('Page.navigate',{url:site+'/report/ilgwan?tab=c2'});
      for(let i=0;i<160;i++){if(await run(`document.querySelectorAll('.inline-paid-reading').length===3`))break;await pause(200);}
      await run(`document.documentElement.style.scrollBehavior='auto';document.body.style.overflowAnchor='none';document.querySelector('.inline-paid-reading').scrollIntoView({block:'start',behavior:'instant'})`);await pause(1500);
      await run(`document.querySelector('.inline-paid-reading').scrollIntoView({block:'start',behavior:'instant'})`);await pause(500);
      assert.equal(await run(`document.documentElement.scrollWidth>innerWidth+1`),false);
      const inlineShot=await send('Page.captureScreenshot',{format:'png'});
      fs.writeFileSync(path.join(out,'inline-paid-mobile.png'),Buffer.from(inlineShot.data,'base64'));
      const clickedQuestion = await run(`document.querySelector('.inline-paid-reading h3').textContent`);
      await run(`document.querySelector('.inline-paid-reading button').click()`);
      let linked=false;
      for(let i=0;i<160;i++){if(await run(`!!document.querySelector('[data-screen="d1"]')`)){linked=true;break;}await pause(200);}
      assert.ok(linked);assert.equal(await run(`JSON.parse(localStorage.getItem('sajudang-session')).state.cur`),'ilgwan');
      for(let i=0;i<60;i++){if(await run(`!!document.querySelector('.checkout-reading-intent')`))break;await pause(200);}
      assert.equal(await run(`document.querySelector('.consultation-offer h1').textContent`),clickedQuestion);
      for(let i=0;i<160;i++){if(await run(`!!document.querySelector('#checkout-terms button')`))break;await pause(200);}
      assert.ok(await run(`!!document.querySelector('#checkout-terms button') && !document.querySelector('#pricelist')`));
    }
    assert.deepEqual(exceptions,[]);
    fs.writeFileSync(path.join(out,rejected?'production-rejected-checks.json':'production-checks.json'),JSON.stringify({site,api,checkedAt:new Date().toISOString(),durable:true,results,exceptions},null,2));
    console.log('PASS production browser',JSON.stringify(results));
  } finally {if(send)await Promise.race([send('Browser.close').catch(()=>{}),pause(1500)]);if(ws)ws.close();browser.kill();}
})().catch(e=>{console.error(e);process.exitCode=1;});
