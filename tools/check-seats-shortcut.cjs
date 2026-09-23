const {spawn}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const site='https://sajudang-three.vercel.app',api='https://sajudang-api.fly.dev',port=19437;
const out=path.resolve('output/funnel-10000');fs.mkdirSync(out,{recursive:true});
const pause=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const browser=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',['--headless=new','--no-first-run',`--remote-debugging-port=${port}`,`--user-data-dir=${path.join(os.tmpdir(),'sjd-shortcut-'+Date.now())}`,'about:blank'],{windowsHide:true,stdio:'ignore'});
 let ws,send;
 try{
  let pages;for(let i=0;i<80;i++){try{pages=await(await fetch(`http://127.0.0.1:${port}/json`)).json();if(pages.some(p=>p.type==='page'))break;}catch{}await pause(200);}
  ws=new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);await new Promise(r=>ws.onopen=r);
  let id=0;const pending=new Map(),errors=[],requests=[],results=[];
  ws.onmessage=e=>{const r=JSON.parse(e.data);if(r.method==='Runtime.exceptionThrown')errors.push(r.params.exceptionDetails.text);if(r.method==='Network.requestWillBeSent'&&r.params.request.url.endsWith('/v1/report')&&r.params.request.postData)requests.push(JSON.parse(r.params.request.postData));if(r.id){const p=pending.get(r.id);pending.delete(r.id);r.error?p.reject(r.error):p.resolve(r.result);}};
  send=(method,params={})=>new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}));});
  const run=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});assert.ok(!r.exceptionDetails,JSON.stringify(r.exceptionDetails));return r.result.value;};
  const until=async expression=>{for(let i=0;i<180;i++){if(await run(expression))return;await pause(200);}throw Error('Timeout '+expression);};
  await send('Runtime.enable');await send('Page.enable');await send('Network.enable');
  await send('Page.addScriptToEvaluateOnNewDocument',{source:`sessionStorage.setItem('sd.qa','1');localStorage.setItem('sd.sound','off');`});
  await send('Page.navigate',{url:site+'/?qa=1'});await until(`!!document.querySelector('.seats-shortcut a')`);
  await until(`getComputedStyle(document.querySelector('.seats-shortcut')).position==='fixed'`);
  for(const width of [320,390,1280]){
   await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<700});
   for(const bottom of [false,true]){
    await run(`scrollTo(0,${bottom?'document.documentElement.scrollHeight':'0'})`);await pause(350);
    const bounds=await run(`(()=>{const a=document.querySelector('.seats-shortcut a'),r=a.getBoundingClientRect();return {visible:r.top>=0&&r.bottom<=innerHeight&&r.left>=0&&r.right<=innerWidth,clickable:a.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)),fixed:getComputedStyle(a.parentElement).position,overflow:document.documentElement.scrollWidth>innerWidth+1}})()`);
    assert.deepEqual(bounds,{visible:true,clickable:true,fixed:'fixed',overflow:false});
   }
   await run('scrollTo(0,0)');await pause(300);
   const shot=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(out,`seats-shortcut-${width}.png`),Buffer.from(shot.data,'base64'));
   results.push({width,topAndBottomVisible:true});
  }
  await run(`document.querySelector('.seats-shortcut a').click()`);await until(`!!document.querySelector('[data-screen="b2"]')`);
  assert.equal(await run(`document.querySelectorAll('.og .op.face').length`),20);
  assert.equal(await run(`JSON.parse(localStorage.getItem('sajudang-session')).state.chartId`),null);
  await run(`document.querySelectorAll('.og .op.face')[1].click()`);await until(`!!document.querySelector('.seatnow')`);
  await run(`document.querySelector('.seatnow .btn').click()`);await until(`!!document.querySelector('[data-screen="a5"]')`);
  const selected=await run(`JSON.parse(localStorage.getItem('sajudang-session')).state.cur`);assert.equal(selected,'baegun');
  const chart=await(await fetch(api+'/v1/chart',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({year:1993,month:11,day:25,hour_known:false,sex:'F',birth_city:'서울'})})).json();assert.ok(chart.chart_id);
  await run(`(()=>{const x=JSON.parse(localStorage.getItem('sajudang-session'));Object.assign(x.state,{chartId:${JSON.stringify(chart.chart_id)},tier:'free',paid:true,topicPick:{chartId:${JSON.stringify(chart.chart_id)},concern:'work',choice:''},concern:'work'});localStorage.setItem('sajudang-session',JSON.stringify(x));})()`);
  await send('Page.navigate',{url:site+'/'});await until(`!!document.querySelector('.seats-shortcut a')`);
  await run(`document.querySelector('.seats-shortcut a').click()`);await until(`!!document.querySelector('[data-screen="b2"]')`);
  await run(`document.querySelectorAll('.og .op.face')[1].click()`);await until(`!!document.querySelector('.seatnow')`);
  await run(`document.querySelector('.seatnow .btn').click()`);await until(`!!document.querySelector('.reading-section .reading-speaker')`);
  assert.ok(requests.some(r=>r.lens_id==='baegun'&&r.tier==='all'&&r.chart_id===chart.chart_id));
  assert.ok(await run(`location.pathname==='/report/baegun'&&!!document.querySelector('.seats-shortcut a')`));
  assert.equal(await run(`JSON.parse(localStorage.getItem('sajudang-session')).state.chartId`),chart.chart_id);
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(out,'seats-shortcut-checks.json'),JSON.stringify({site,results,freshBrowse:true,characters:20,selectedCharacterKept:true,returningChartKept:true,serverEntitlementRequested:true,errors},null,2));
  console.log('PASS: fresh entry, 20 seats, returning visit skips input, server entitlement requested, 320/390/1280, no live purchase');
 }finally{if(send)await Promise.race([send('Browser.close').catch(()=>{}),pause(1500)]);if(ws)ws.close();browser.kill();}
})().catch(e=>{console.error(e);process.exitCode=1;});
