// Uses real-engine fixture responses; no purchases or production writes.
const {spawn}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const fixture=JSON.parse(fs.readFileSync('artifacts/entry-research/browser-fixture.json','utf8'));
const out=path.resolve('artifacts/entry-research/browser');fs.mkdirSync(out,{recursive:true});
const base='http://127.0.0.1:3038',port=19438;
const browser=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',['--headless=new','--no-first-run',`--remote-debugging-port=${port}`,`--user-data-dir=${path.join(os.tmpdir(),'sjd-entry-'+process.pid)}`,'about:blank'],{windowsHide:true,stdio:'ignore'});
const pause=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 let pages;for(let i=0;i<100;i++){try{pages=await(await fetch(`http://127.0.0.1:${port}/json`)).json();if(pages.some(p=>p.type==='page'))break;}catch{}await pause(150);}
 assert(pages?.some(p=>p.type==='page'),'Browser did not start');
 const ws=new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);await new Promise(r=>ws.onopen=r);
 let serial=0;const pending=new Map(),exceptions=[],results=[];
 const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++serial;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
 ws.onmessage=async e=>{const x=JSON.parse(e.data);
  if(x.id){const p=pending.get(x.id);pending.delete(x.id);x.error?p.reject(x.error):p.resolve(x.result);}
  if(x.method==='Runtime.exceptionThrown')exceptions.push(x.params.exceptionDetails);
  if(x.method==='Fetch.requestPaused'){
   const r=x.params, url=new URL(r.request.url);let body={};
   let req={};try{req=JSON.parse(r.request.postData||'{}');}catch{}
   if(url.pathname.includes('/chart'))body=fixture.chart;
   else if(url.pathname.endsWith('/hook'))body=req.misses?fixture.rejected:fixture.hook;
   else if(url.pathname.endsWith('/report'))body=fixture.reports[req.lens_id]||fixture.reports.pungun;
   else if(url.pathname.includes('sales-status'))body={ready:false,reason:'Browser fixture'};
   else if(url.pathname.includes('/relay'))body={items:[],forced:false};
   else if(url.pathname.includes('/pay/tiers'))body={tiers:[]};
   try{await send('Fetch.fulfillRequest',{requestId:r.requestId,responseCode:200,responseHeaders:[{name:'Content-Type',value:'application/json'},{name:'Access-Control-Allow-Origin',value:'*'},{name:'Access-Control-Allow-Headers',value:'*'},{name:'Access-Control-Allow-Methods',value:'GET,POST,OPTIONS'}],body:Buffer.from(JSON.stringify(body)).toString('base64')});}catch{}
  }
 };
 const run=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;};
 const until=async expression=>{for(let i=0;i<180;i++){if(await run(`Boolean(document.body && (${expression}))`))return;await pause(200);}throw Error('Timeout '+expression);};
 const click=async text=>run(`(()=>{const b=[...document.querySelectorAll('button')].find(b=>b.textContent.includes(${JSON.stringify(text)}));if(!b)throw Error('Missing button');if(b.disabled)throw Error('Disabled button');b.click();})()`);
 const input=async (id,value)=>run(`(()=>{const n=document.getElementById(${JSON.stringify(id)});Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(n,${JSON.stringify(value)});n.dispatchEvent(new Event('input',{bubbles:true}));})()`);
 const shot=async name=>{await pause(350);const s=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(s.data,'base64'));};
 try{
  await send('Runtime.enable');await send('Page.enable');
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  await send('Fetch.enable',{patterns:[{urlPattern:'*/v1/*'},{urlPattern:'*/api/sales-status*'}]});
  await send('Page.addScriptToEvaluateOnNewDocument',{source:`localStorage.setItem('sd.sound','off');`});
  await send('Page.navigate',{url:base+'/?step=a1'});await until(`document.querySelector('.entry-gate')`);
  await run(`localStorage.setItem('sajudang-session',JSON.stringify({state:{admin:false,adminSet:true},version:0}))`);
  for(const [width,height] of [[320,740],[390,844],[1440,960]]){
   await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<900});
   await send('Page.navigate',{url:base+'/?step=a1'});await until(`document.querySelector('.entry-gate')`);await pause(400);
   assert.equal(await run('document.documentElement.scrollWidth>innerWidth'),false,'A1 overflow '+width);
   await until(`Object.keys(document.querySelector('.entry-gate .btn')).some(key=>key.startsWith('__reactProps'))`);
   await run(`document.querySelector('.entry-gate .btn').scrollIntoView({block:'center',behavior:'instant'})`);await pause(500);
   assert(await run(`(()=>{const b=document.querySelector('.entry-gate .btn');const r=b.getBoundingClientRect();return b.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));})()`),'A1 button blocked');
   await run('scrollTo(0,0)');await shot('a1-'+width);results.push({screen:'a1',width,overflow:false});
  }
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
  await until(`Object.keys(document.querySelector('.entry-gate .btn')).some(key=>key.startsWith('__reactProps'))`);
  await pause(300);
  await click('내 고민으로 무료 해석 보기');await until(`document.querySelector('.entry-concerns')`);
  assert.equal(await run(`document.querySelectorAll('.entry-concerns>button').length`),6);await shot('a5');
  await click('계속 버틸까');await click('이 질문으로 시작하기');await until(`document.getElementById('birth-year')`);
  await input('birth-year','1993');await input('birth-month','2');await input('birth-day','30');
  await until(`document.getElementById('birth-error')`);assert(await run(`[...document.querySelectorAll('button')].find(b=>b.textContent.includes('마지막으로')).disabled`));
  await input('birth-month','5');await input('birth-day','15');await click('여성');await shot('a3');
  await click('마지막으로 출생 시간');await until(`document.getElementById('birth-hour')`);
  await click('시간을 모르겠어요');await until(`document.querySelector('.entry-axis')`);await click('사주만으로 보기');
  await until(`[...document.querySelectorAll('button')].some(b=>b.textContent.includes('나의 첫 해석 읽기'))`);await shot('a6');
  await click('나의 첫 해석 읽기');await until(`document.querySelector('.entry-reading-card h2')`);await shot('a7-first');
  assert.equal(await run(`document.querySelector('.entry-reading-body').textContent.includes('<p>')`),false);
  await click('내 경험과 달라요');await until(`document.querySelector('.entry-reply')`);await pause(250);
  await click('반복되는 이유 읽기');await until(`document.querySelector('.entry-reading-body').textContent.includes('성격을 정하지')`);await shot('a7-response');
  await click('오늘 바꿔볼 행동');await until(`document.querySelector('.entry-reading-card h2').textContent.includes('오늘은')`);
  await click('첫 해석 정리하기');await until(`document.querySelector('.entry-next')`);await shot('a7-complete');
  await send('Page.reload');await until(`document.querySelector('.entry-next')`);
  results.push({flow:'a1-a7',invalidDateBlocked:true,unknownTime:true,rejection:true,resume:true});
  for(const lensId of ['pungun','jeokhyeol','dongja']){
   await run(`(()=>{const saved=JSON.parse(localStorage.getItem('sajudang-session'));saved.state.cur=${JSON.stringify(lensId)};localStorage.setItem('sajudang-session',JSON.stringify(saved));})()`);
   await send('Page.navigate',{url:base+'/pay?step=d0'});await until(`document.querySelector('.character-reading-offer')`);
   const freeCount=await run(`document.querySelectorAll('.character-free article').length`);
   assert.equal(freeCount,fixture.reports[lensId].reading_offer.free_ids.length);
   assert.equal(await run(`!!document.querySelector('.character-paid')`),lensId!=='dongja');
   if(lensId!=='dongja'){
    assert(await run(`document.querySelector('.character-free').getBoundingClientRect().top<document.querySelector('.character-paid').getBoundingClientRect().top`));
    await run(`document.querySelector('.character-paid').scrollIntoView({block:'start'})`);await shot('offer-'+lensId);
   }
   results.push({lensId,freeCount,paidOffer:lensId!=='dongja'});
  }
  assert.equal(exceptions.length,0,JSON.stringify(exceptions));
  fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(results,null,2));console.log(JSON.stringify(results));
 } catch(e){console.error(JSON.stringify({url:await run('location.href'),text:await run('document.body.innerText'),exceptions}));await shot('failure');throw e;} finally{ws.close();browser.kill();}
})().catch(e=>{console.error(e);browser.kill();process.exitCode=1;});
