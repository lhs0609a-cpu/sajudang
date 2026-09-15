// Real local app/API with controlled failures. Payment provider is blocked.
const {spawn}=require('node:child_process'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),assert=require('node:assert/strict');
const out='D:/developer/sajudang_git/output/audit-20260909/fixes',port=19379;
fs.mkdirSync(out,{recursive:true});
const browser=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',['--headless=new','--no-first-run',`--remote-debugging-port=${port}`,`--user-data-dir=${path.join(os.tmpdir(),'sjd-fixes-'+process.pid)}`,'about:blank'],{windowsHide:true,stdio:'ignore'});
const pause=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 let pages;for(let i=0;i<80;i++){try{pages=await(await fetch(`http://127.0.0.1:${port}/json`)).json();if(pages.some(p=>p.type==='page'))break;}catch{}await pause(200);}
 const ws=new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);await new Promise(r=>ws.onopen=r);
 let n=0,script;const pending=new Map(),exceptions=[],results=[];
 ws.onmessage=e=>{const x=JSON.parse(e.data);if(x.method==='Runtime.exceptionThrown')exceptions.push(x.params.exceptionDetails);if(x.id){const p=pending.get(x.id);pending.delete(x.id);x.error?p.reject(x.error):p.resolve(x.result);}};
 const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++n;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
 const run=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;};
 const until=async expression=>{for(let i=0;i<100;i++){if(await run(expression))return;await pause(150);}throw Error('Timeout '+expression+' '+await run('document.body.innerText'));};
 const birth={year:1993,month:11,day:25,hour:null,minute:null,hour_known:false,sex:'F',birth_city:'서울'};
 const chart=await(await fetch('http://127.0.0.1:8026/v1/chart',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(birth)})).json();assert(chart.chart_id);
 const seed={sessionId:'browser-fixes-20260909',year:1993,month:11,day:25,hour:null,minute:0,hourKnown:false,sex:'F',sexSet:true,city:'서울',concern:'money',concernSet:true,chartId:chart.chart_id,cur:'pungun',name:'',read:[],skipped:[],seals:[],tier:'free',paid:false,visits:9,visitDate:'2020-01-01',axis4:null,admin:false,adminSet:true};
 async function shot(name){const r=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(r.data,'base64'));}
 async function scenario(name,url,endpoint,button,expected,{expiry=false,width=390}={}){
  if(script)await send('Page.removeScriptToEvaluateOnNewDocument',{identifier:script});
  script=(await send('Page.addScriptToEvaluateOnNewDocument',{source:`localStorage.setItem('sajudang-session',${JSON.stringify(JSON.stringify({state:seed,version:0}))});const real=window.fetch;window.__failed=0;window.__retry=false;window.__calls=[];window.fetch=function(input,init){const u=typeof input==='string'?input:(input.url||String(input));window.__calls.push(u);if(${JSON.stringify(endpoint)}&&u.includes(${JSON.stringify(endpoint)})&&!window.__retry&&(!${expiry}||!window.__failed)){window.__failed++;return Promise.resolve(new Response(JSON.stringify({detail:'일시적인 서버 오류입니다.'}),{status:${expiry?404:500},headers:{'Content-Type':'application/json',${expiry?"'X-Chart-Rebuild':'1'":""}}}));}return real.call(this,input,init);};`})).identifier;
  await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:true});
  await send('Page.navigate',{url:'http://127.0.0.1:3026'+url});await pause(1500);
  let before=null;
  if(button){await until(`document.body.innerText.includes(${JSON.stringify(button)})`);before=await run('document.body.innerText');if(name==='history')assert(!before.includes('아직 구매 내역이 없어요'),name+' must not show empty while failed');await shot(name+'-error');await run(`window.__retry=true;[...document.querySelectorAll('button')].find(b=>b.textContent.includes(${JSON.stringify(button)})).click()`);}
  await until(expected);await pause(300);
  const observed=await run('({text:document.body.innerText,calls:window.__calls,failed:window.__failed,overflow:document.documentElement.scrollWidth>innerWidth,state:JSON.parse(localStorage.getItem("sajudang-session")).state})');
  if(button)assert(observed.calls.filter(u=>u.includes(endpoint)).length>=2,name+' must send retry');
  if(expiry){assert(observed.calls.some(u=>u.endsWith('/v1/chart')),'must rebuild chart');assert.equal(observed.state.chartId,chart.chart_id);}
  assert(!observed.overflow,name+' overflow');await shot(name+'-restored');
  results.push({name,status:'passed',before,text:observed.text,failed:observed.failed,request_paths:observed.calls.map(u=>new URL(u, 'http://127.0.0.1:3026').pathname)});console.log(name,'passed');
 }
 try{
  await send('Runtime.enable');await send('Page.enable');await send('Network.enable');await send('Network.setBlockedURLs',{urls:['*tosspayments.com*']});
  for(const row of [
   ['hook','/?step=a7','/v1/hook','무료 해석 다시 불러오기',`document.body.innerText.includes('기둥 3자리의 6글자')&&document.body.innerText.includes('그렇습니다')`],
   ['report','/report/pungun','/v1/report','다시 펴 보겠습니다',`!document.body.innerText.includes('일시적인 서버 오류')&&document.body.innerText.includes('내 것을 펴겠습니다')`],
   ['history','/me','/v1/pay/history','구매 내역 다시 확인하기',`document.body.innerText.includes('아직 구매 내역이 없어요')`],
   ['subscription','/me','/v1/pay/sub?','구독 상태 다시 확인하기',`!document.body.innerText.includes('구독 상태를 확인하지 못했어요')`],
   ['tiers','/pay?step=d1','/v1/pay/tiers','상품 다시 불러오기',`!!document.querySelector('.conversion-product')`,{width:320}],
   ['summary','/summary','/v1/summary','분석지 다시 불러오기',`!document.body.innerText.includes('일시적인 서버 오류')&&document.body.innerText.includes('들고 나가는')`],
   ['daily','/daily','/v1/daily','일진 다시 불러오기',`document.body.innerText.includes('오늘 기운')&&JSON.parse(localStorage.getItem('sajudang-session')).state.visits===1`],
   ['expired-chart','/pay?step=d0','/v1/report',null,`document.body.innerText.includes('오늘 해볼 행동')`,{expiry:true}]
  ])await scenario(...row);
  assert.equal(exceptions.length,0);
  fs.writeFileSync(path.join(out,'browser-fixes.json'),JSON.stringify({status:'passed',provider:'blocked; no charges',results,exceptions},null,2));
 }catch(e){await shot('failure').catch(()=>{});fs.writeFileSync(path.join(out,'browser-fixes.json'),JSON.stringify({status:'failed',error:String(e),results,exceptions},null,2));throw e;}
 finally{await Promise.race([send('Browser.close').catch(()=>{}),pause(1500)]);ws.close();browser.kill();}
})().catch(e=>{console.error(e);browser.kill();process.exitCode=1;});
