const {spawn}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const site=process.argv.includes('--local')?'http://localhost:3000':'https://saju.megaload.co.kr';
const directReturn=process.argv.includes('--direct-return');
const direct=process.argv.includes('--direct')||directReturn;
const api='https://sajudang-api.fly.dev',port=19429;
const billing=process.argv.includes('--billing');
const out=path.resolve('output/payment-verification');fs.mkdirSync(out,{recursive:true});
const pause=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const chart=await(await fetch(api+'/v1/chart',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({year:1993,month:11,day:25,hour_known:false,sex:'F',birth_city:'서울'})})).json();
 assert.ok(chart.chart_id);
 const browser=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',['--headless=new','--no-first-run',`--remote-debugging-port=${port}`,`--user-data-dir=${path.join(os.tmpdir(),'checkout-check-'+Date.now())}`,'about:blank'],{windowsHide:true,stdio:'ignore'});
 let ws,send;
 try{
 let pages;for(let i=0;i<60;i++){try{pages=await(await fetch(`http://127.0.0.1:${port}/json`)).json();if(pages.some(p=>p.type==='page'))break;}catch{}await pause(200);}
 ws=new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);await new Promise(r=>ws.onopen=r);
 let id=0;const pending=new Map(),errors=[];
 const confirmations=[];let retryAllowed=false;
 ws.onmessage=e=>{const r=JSON.parse(e.data);if(r.method==='Runtime.exceptionThrown')errors.push(r.params.exceptionDetails.text);if(r.method==='Fetch.requestPaused'){
   if(r.params.request.method==='OPTIONS'){
     void send('Fetch.fulfillRequest',{requestId:r.params.requestId,responseCode:204,responseHeaders:[{name:'Access-Control-Allow-Origin',value:site},{name:'Access-Control-Allow-Methods',value:'POST, OPTIONS'},{name:'Access-Control-Allow-Headers',value:'Content-Type'}]});return;
   }
   if(directReturn && r.params.request.url.endsWith('/v1/report')){
    const fixture=JSON.parse(fs.readFileSync(path.join(out,'paid-fixture.json'),'utf8'));
    fixture.chart_id=chart.chart_id;
    void send('Fetch.fulfillRequest',{requestId:r.params.requestId,responseCode:200,responseHeaders:[{name:'Content-Type',value:'application/json'},{name:'Access-Control-Allow-Origin',value:site}],body:Buffer.from(JSON.stringify(fixture)).toString('base64')});return;
   }
   confirmations.push(JSON.parse(r.params.request.postData));
   const success=retryAllowed;
   const body=billing?{ok:true,order_id:'simulated_no_charge',sub:{has:true,active:true,price:14900,next_charge:null,card:null}}:success?{ok:true,tier:'one',seal:direct?'jeokhyeol':'pungun',granted:{counted:true,cuts:8,chars:3000,minutes:5,lenses:1,tier_name:'검증용'}}:{detail:'승인 확인 연결이 끊겼소. 다시 확인해 주시오.'};
   void send('Fetch.fulfillRequest',{requestId:r.params.requestId,responseCode:success||billing?200:502,responseHeaders:[{name:'Content-Type',value:'application/json'},{name:'Access-Control-Allow-Origin',value:site}],body:Buffer.from(JSON.stringify(body)).toString('base64')});
 }if(r.id){const p=pending.get(r.id);pending.delete(r.id);r.error?p.reject(r.error):p.resolve(r.result);}};
 send=(method,params={})=>new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}));});
 const run=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});assert.ok(!r.exceptionDetails,JSON.stringify(r.exceptionDetails));return r.result.value;};
 const until=async expression=>{for(let i=0;i<120;i++){if(await run(expression))return;await pause(250);}throw Error('Timed out: '+expression);};
 await send('Runtime.enable');await send('Page.enable');
const state={admin:false,adminSet:true,sessionId:'checkout-audit-'+Date.now(),chartId:chart.chart_id,cur:direct?'jeokhyeol':'pungun',concern:direct?'love':'work',tier:'free',paid:false,year:1993,month:11,day:25,hourKnown:false,sex:'F',city:'서울'};
 await send('Page.addScriptToEvaluateOnNewDocument',{source:`if(location.origin===${JSON.stringify(site)}&&!sessionStorage.getItem('checkout-audit')){localStorage.setItem('sd.sound','off');localStorage.setItem('sajudang-session',JSON.stringify({state:${JSON.stringify(state)},version:0}));sessionStorage.setItem('checkout-audit','1');}`});
 await send('Emulation.setDeviceMetricsOverride',{width:1280,height:960,deviceScaleFactor:1,mobile:false});
 if(billing){
   await send('Fetch.enable',{patterns:[{urlPattern:'*/v1/pay/sub/register',requestStage:'Request'}]});
   await send('Page.navigate',{url:site+'/pay?step=d2&sub=ok&customerKey=simulated&authKey=simulated'});
   await until(`!!document.querySelector('[data-screen="d3"]')`);
   assert.ok(confirmations.length>=1);for(const request of confirmations)assert.equal(request.session_id,state.sessionId);
   console.log('PASS simulated billing callback waits for saved session; no live billing sent');return;
 }
 if(process.argv.includes('--recovery')){
   await send('Fetch.enable',{patterns:[{urlPattern:'*/v1/pay/confirm',requestStage:'Request'}]});
   await send('Page.navigate',{url:site+'/pay?step=d2&toss=ok&order=sjd_simulated_no_charge&paymentKey=simulated_no_charge'});
   await until(`Array.from(document.querySelectorAll('button')).some(b=>b.textContent.includes('같은 주문 승인 다시 확인하기'))`);
   retryAllowed=true;
   await run(`Array.from(document.querySelectorAll('button')).find(b=>b.textContent.includes('같은 주문 승인 다시 확인하기')).click()`);
   await until(`!!document.querySelector('[data-screen="d3"]')`);
   assert.ok(confirmations.length>=2);for(const request of confirmations){assert.deepEqual(request,confirmations[0]);assert.equal(request.session_id,state.sessionId);}
   assert.deepEqual(errors,[]);
   console.log('PASS simulated approval failure -> same-order retry -> purchased reading, no live approval sent');
   return;
 }
 if(direct){
  await send('Page.navigate',{url:site+'/report/jeokhyeol?tab=c2'});
  await until(`document.querySelectorAll('.inline-paid-reading').length===3`);
  await run(`document.querySelector('.inline-paid-reading .btn').click()`);
 }else{
  await send('Page.navigate',{url:site+'/pay?step=d1'});
  await until(`!!document.querySelector('#pricelist .conversion-product')`);
  await run(`document.querySelector('#pricelist .conversion-product').click()`);
 }
 await until(`Array.from(document.querySelectorAll('#checkout-terms button')).some(b=>b.textContent.includes('원 결제하기')&&!b.disabled)`);
 if(direct){
  assert.equal(await run(`document.querySelectorAll('#pricelist').length`),0);
  assert.ok(await run(`!!(document.querySelector('#checkout-terms').compareDocumentPosition(document.querySelector('.paid-preview'))&Node.DOCUMENT_POSITION_FOLLOWING)`));
  assert.ok(await run(`document.querySelector('.conversion-title').innerText.includes(JSON.parse(sessionStorage.getItem('sd.reading-intent')).question)`));
 }
 const price=await run(`document.querySelector('#checkout-terms .conversion-price').innerText`);
 if(directReturn){
  const intent=await run(`JSON.parse(sessionStorage.getItem('sd.reading-intent'))`);
  retryAllowed=true;
  await send('Fetch.enable',{patterns:[{urlPattern:'*/v1/pay/confirm',requestStage:'Request'},{urlPattern:'*/v1/report',requestStage:'Request'}]});
  await send('Page.navigate',{url:site+'/pay?step=d2&toss=ok&order=sjd_simulated_no_charge&paymentKey=simulated_no_charge'});
  await until(`location.pathname==='/report/jeokhyeol' && !!document.getElementById('reading-'+${JSON.stringify(intent.chapterId)})`);
  await until(`document.activeElement?.id==='reading-'+${JSON.stringify(intent.chapterId)}`);
  assert.deepEqual(errors,[]);assert.ok(confirmations.length>0);
  for(const request of confirmations)assert.equal(request.session_id,state.sessionId);
  fs.writeFileSync(path.join(out,'direct-return-checks.json'),JSON.stringify({site,chapter:intent.chapterId,paidResponseMocked:true,charged:false,approvalReturnsToChapter:true,errors},null,2));
  console.log('PASS direct purchase: simulated approval returns to selected chapter, focused and readable; no live charge');return;
 }
 await run(`document.querySelector('#checkout-terms').scrollIntoView({block:'start'})`);await pause(300);
 let shot=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(out,'checkout.png'),Buffer.from(shot.data,'base64'));
 await run(`Array.from(document.querySelectorAll('#checkout-terms button')).find(b=>b.textContent.includes('원 결제하기')).click()`);
 let opened=false;
 for(let i=0;i<100;i++){
   const tree=await send('Page.getFrameTree');
   const hasToss=f=>{try{if(new URL(f.frame.url).hostname.endsWith('tosspayments.com'))return true;}catch{}return(f.childFrames||[]).some(hasToss);};
   const targets=await send('Target.getTargets');
   const gateway=targets.targetInfos.some(t=>{try{return /(^|\.)(tosspayments\.com|toss\.im|tosspayments\.com\.cn)$/.test(new URL(t.url).hostname);}catch{return false;}});
   if(hasToss(tree.frameTree)||gateway){opened=true;break;}
   await pause(300);
 }
 await pause(1500);
 const messages=await run(`Array.from(document.querySelectorAll('.warn')).map(e=>e.innerText)`);
 shot=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(out,'gateway.png'),Buffer.from(shot.data,'base64'));
 const result={site,price,gatewayOpened:opened,errors,messages,charged:false};
 fs.writeFileSync(path.join(out,'checks.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
 assert.ok(opened,'Toss checkout failed to open');assert.deepEqual(errors,[]);
 }finally{if(send)await Promise.race([send('Browser.close').catch(()=>{}),pause(1000)]);if(ws)ws.close();browser.kill();}
})().catch(e=>{console.error(e);process.exitCode=1;});
