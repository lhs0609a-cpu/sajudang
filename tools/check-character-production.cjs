const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const {spawn} = require('node:child_process');
const api = 'https://sajudang-api.fly.dev';
const site = process.argv.includes('--local') ? 'http://localhost:3000' : 'https://saju.megaload.co.kr';
const rejected = process.argv.includes('--rejected');
const out = path.resolve('output/character-consistency');
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
  assert.ok(free.cuts.some(c=>c.html.includes('free-depth-essay')));
  assert.ok(free.cuts.every(c=>!c.html.includes('consultation-method')));
  assert.ok(free.cuts.every(c=>!c.html.includes('여덟 글자')));
  const dongja = await json(api + '/v1/report', {chart_id:chart.chart_id,lens_id:'dongja',tier:'free',concern:'work'});
  assert.ok(dongja.cuts.some(c=>c.html.includes('consultation-method')));
  assert.equal(dongja.locked.length, 0);
  console.log('PASS production API: expanded free text, action steps, consultation, access boundary, unknown hour, durable storage');
  if (process.argv.includes('--api-only')) return;
  const port = 19447;
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
    const profiles=require('../apps/web/lib/character-profiles.json');
    const results=[];
    await send('Emulation.setDeviceMetricsOverride',{width:390,height:900,deviceScaleFactor:1,mobile:true});
    let injection;
    for(const [lens,profile] of Object.entries(profiles)){
      const effective=profile.concerns.includes('money')?'money':profile.default_concern;
      const report=await json(api+'/v1/report',{chart_id:chart.chart_id,lens_id:lens,tier:'free',concern:'money'});
      assert.equal(report.concern,effective,lens+' API topic');
      if(lens==='jeokhyeol')assert.ok(!report.cuts.some(c=>/돈이 들어오는 곳|지출|장사·사업/.test(c.title+' '+c.html)),'jeokhyeol finance body');
      const state={admin:false,adminSet:true,chartId:chart.chart_id,cur:'pungun',concern:'money',tier:'free',paid:false,name:'',year:1993,month:11,day:25,hourKnown:false,sex:'F',city:'서울',hookReview:null,topicPick:{chartId:chart.chart_id,concern:'money',choice:'business'}};
      if(injection)await send('Page.removeScriptToEvaluateOnNewDocument',{identifier:injection});
      injection=(await send('Page.addScriptToEvaluateOnNewDocument',{source:`sessionStorage.setItem('sd.qa','1');localStorage.setItem('sd.sound','off');localStorage.setItem('sajudang-session',JSON.stringify({state:${JSON.stringify(state)},version:0}));`})).identifier;
      await send('Page.navigate',{url:site+'/report/'+lens+'?tab='+ (lens==='dongja'?'c2':'c4')});
      let ready=false;
      for(let i=0;i<200;i++){if(await run(`document.querySelectorAll('${lens==='dongja'?'.reading-section':'.free-reading-detail'} .reading-speaker').length>=3`)){ready=true;break;}await pause(200);}
      assert.ok(ready,lens+' load');
      const actual=await run(`(()=>{const s=JSON.parse(localStorage.getItem('sajudang-session')).state;return {cur:s.cur,concern:s.concern,topic:s.topicPick,text:(document.querySelector('.free-reading-detail')||document.querySelector('.reading-section')).innerText,speakers:[...document.querySelectorAll('.reading-speaker')].map(e=>e.dataset.speaker),overflow:document.documentElement.scrollWidth>innerWidth+1}})()`);
      assert.equal(actual.cur,lens);assert.equal(actual.concern,effective);assert.ok(actual.speakers.every(s=>s===lens),lens+' speaker');assert.equal(actual.overflow,false,lens+' overflow');
      if(effective!=='money')assert.ok(!actual.topic||actual.topic.concern===effective,lens+' stale probe');
      if(lens==='jeokhyeol'){assert.ok(!/지출|장사·사업|돈이 들어오는 곳/.test(actual.text));const speech=actual.text.replace(/“[^”]*”|「[^」]*」|『[^』]*』/g,'');assert.ok(!/[가-힣]+(?:하오|시오|있소|없소|해요|합니다)(?:[.?!]|\s|$)/.test(speech),'jeokhyeol mixed endings: '+speech);}
      results.push({lens,effective,...actual});console.log('PASS '+lens+' money -> '+effective);
      if(lens==='jeokhyeol'){
       await send('Page.navigate',{url:site+'/report/'+lens+'?tab=c2'});
       let ready=false;for(let i=0;i<200;i++){if(await run(`document.querySelectorAll('.inline-paid-reading').length===3`)){ready=true;break;}await pause(200);}
       assert.ok(ready,'jeokhyeol inline offers');
       const full=await run(`document.querySelector('.reading-section').innerText`);
       assert.ok(!/돈이 들어오는 곳|장사·사업/.test(full));
       results[results.length-1].fullReading=full;
      }
      if(['jeokhyeol','haengsu','yakcho'].includes(lens)){
       await run(`(document.querySelector('.free-reading-detail')||document.querySelector('.reading-section')).scrollIntoView({block:'start'})`);await pause(300);
       const shot=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(out,lens+'-production.png'),Buffer.from(shot.data,'base64'));
      }
    }
    assert.deepEqual(exceptions,[]);
    fs.writeFileSync(path.join(out,'production-checks.json'),JSON.stringify({site,checkedAt:new Date().toISOString(),results,exceptions},null,2));
  } finally {if(send)await Promise.race([send('Browser.close').catch(()=>{}),pause(1500)]);if(ws)ws.close();browser.kill();}
})().catch(e=>{console.error(e);process.exitCode=1;});
