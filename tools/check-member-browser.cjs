const {spawn}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const site='https://saju.megaload.co.kr',out=path.resolve('output/member-mbti-release');
const pause=ms=>new Promise(r=>setTimeout(r,ms));fs.mkdirSync(out,{recursive:true});
async function browser(port,mute=false){
 const child=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',['--headless=new','--no-first-run',...(mute?['--mute-audio']:[]),`--remote-debugging-port=${port}`,`--user-data-dir=${path.join(os.tmpdir(),'sjd-member-'+port+'-'+Date.now())}`,'about:blank'],{windowsHide:true,stdio:'ignore'});
 let pages;for(let i=0;i<100;i++){try{pages=await(await fetch(`http://127.0.0.1:${port}/json`)).json();if(pages.some(p=>p.type==='page'))break;}catch{}await pause(200);}
 const ws=new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);await new Promise(r=>ws.onopen=r);let id=0;const pending=new Map(),errors=[];
 ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.text);if(m.id){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(m.error):p.resolve(m.result);}};
 const send=(method,params={})=>new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}));});
 const run=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});assert.ok(!r.exceptionDetails,'Browser evaluation failed');return r.result.value;};
 const until=async expr=>{for(let i=0;i<160;i++){if(await run(expr))return;await pause(250);}throw Error('Timed out: '+expr);};
 const go=async route=>{await send('Page.navigate',{url:site+route});await until('document.readyState==="complete"');};
 const input=async(selector,value)=>run(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(e,${JSON.stringify(value)});e.dispatchEvent(new Event('input',{bubbles:true}));})()`);
 await send('Runtime.enable');await send('Page.enable');await send('Network.enable');await send('Page.addScriptToEvaluateOnNewDocument',{source:"sessionStorage.setItem('sd.qa','1');localStorage.setItem('sd.sound','off');"});
 await send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:out});
 return {send,run,until,go,input,errors,close:async()=>{await Promise.race([send('Browser.close').catch(()=>{}),pause(1500)]);ws.close();child.kill();}};
}
module.exports={browser};
if(require.main===module)(async()=>{
 let a,b;const name='qa_'+crypto.randomBytes(9).toString('hex'),password=crypto.randomBytes(18).toString('base64url');let registered=false;
 try{
  a=await browser(19458);await a.go('/?qa=1');await a.until("!!localStorage.getItem('sajudang-session')");
  const chart=await a.run(`(async()=>{const r=await fetch('/api/backend/v1/chart',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({year:1993,month:5,day:15,hour:10,minute:20,hour_known:true,sex:'F',birth_city:'서울'})});if(!r.ok)throw Error('chart '+r.status);return r.json();})()`);
  await a.run(`(()=>{const x=JSON.parse(localStorage.getItem('sajudang-session'));Object.assign(x.state,{year:1993,month:5,day:15,hour:10,minute:20,hourKnown:true,sex:'F',sexSet:true,city:'서울',axis4:'INFP',name:'보관함 검증',chartId:${JSON.stringify(chart.chart_id)},features:${JSON.stringify(chart.features)},cur:'jeokhyeol',concern:'love',concernSet:true,tier:'free'});localStorage.setItem('sajudang-session',JSON.stringify(x));})()`);
  await a.go('/me');await a.until("!!document.querySelector('.member-form')");
  await a.run("Array.from(document.querySelectorAll('.member-tabs button')).find(e=>e.textContent==='회원가입').click()");
  await a.input('.member-form input[autocomplete=username]',name);await a.input('.member-form input[autocomplete=new-password]',password);
  await a.input('.member-form label:nth-of-type(3) input',password);
  await a.run("document.querySelector('.member-form input[type=checkbox]').click();document.querySelector('.member-form button[type=submit],.member-form button').click()");
  await a.until("!!document.querySelector('.member-library code')");registered=true;
  await a.until("!!document.querySelector('.member-library a[href^=\"/library/\"]')");
  const cookie=(await a.send('Network.getAllCookies')).cookies.find(c=>c.name==='__Host-sajudang-member');assert.ok(cookie?.httpOnly&&cookie.secure&&cookie.sameSite==='Lax');
  assert.equal(await a.run("document.cookie.includes('sajudang-member')"),false);
  await a.run("Array.from(document.querySelectorAll('.member-library button')).find(e=>e.textContent==='안전한 곳에 저장했습니다').click()");
  for(const width of [390,1280]){await a.send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:width<700});await pause(300);assert.equal(await a.run('document.documentElement.scrollWidth>innerWidth+1'),false);const shot=await a.send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(out,'library-'+width+'.png'),Buffer.from(shot.data,'base64'));}
  await a.run("document.querySelector('.member-library a[href^=\"/library/\"]').click()");await a.until("!!document.querySelector('.mbti-reading')");
  assert.ok(await a.run("document.body.innerText.includes('INFP')&&document.body.innerText.includes('내가 고른 MBTI에 맞춘 실행법')"));
  const rid=await a.run("location.pathname.split('/').pop()");
  await a.run("Array.from(document.querySelectorAll('button')).find(e=>e.textContent==='풀이 다운로드 · 인쇄/PDF').click()");
  const file=path.join(out,'성신당-보관한-풀이.html');for(let i=0;i<80&&!fs.existsSync(file);i++)await pause(250);assert.ok(fs.existsSync(file));assert.ok(fs.readFileSync(file,'utf8').includes('INFP'));
  b=await browser(19459);await b.go('/me');await b.until("!!document.querySelector('.member-form')");await b.input('.member-form input[autocomplete=username]',name);await b.input('.member-form input[type=password]',password);await b.run("document.querySelector('.member-form button').click()");await b.until("!!document.querySelector('.member-library a[href^=\"/library/\"]')");
  const lib=await b.run("fetch('/api/backend/v1/account/library').then(r=>r.json())");assert.equal(lib.readings[0].id,rid);
  await b.run("Array.from(document.querySelectorAll('.member-library button')).find(e=>e.textContent==='이 사주로 다른 캐릭터 보기').click()");await b.until("!!document.querySelector('[data-screen=b2]')");assert.equal(await b.run("document.querySelectorAll('.og .op.face').length"),20);
  assert.ok(await b.run("JSON.parse(localStorage.getItem('sajudang-session')).state.features?.pillars.length>0"));
  await b.run("document.querySelectorAll('.og .op.face')[1].click()");await b.until("!!document.querySelector('.seatnow')");await b.run("document.querySelector('.seatnow .btn').click()");await b.until("!!document.querySelector('.reading-section .reading-speaker')");
  await b.until("document.querySelector('.reading-speaker')?.dataset.speaker==='baegun'");
  await b.go('/me');await b.until("!!document.querySelector('.member-library a[href^=\"/library/\"]')");await b.run("Array.from(document.querySelectorAll('.member-library button')).find(e=>e.textContent==='로그아웃').click()");await b.until("!!document.querySelector('.member-form')");assert.equal(await b.run("fetch('/api/backend/v1/account/reading/'+"+JSON.stringify(rid)+").then(r=>r.status)"),401);
  assert.deepEqual(a.errors,[]);assert.deepEqual(b.errors,[]);
  fs.writeFileSync(path.join(out,'checks.json'),JSON.stringify({site,signup:true,automaticSave:true,mbtiInArchive:true,httpOnlySecureCookie:true,download:true,secondBrowserLogin:true,sameLibrary:true,otherCharacters:20,logoutBlocksArchive:true,widths:[390,1280],runtimeErrors:[],liveCharge:false},null,2));console.log('PASS: member signup, save, private cookie, MBTI archive, download, second-browser login, 20 seats, logout, 390/1280');
 }finally{
  if(a&&registered){const result=await a.run(`fetch('/api/backend/v1/account/delete',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({password:${JSON.stringify(password)},confirm:true})}).then(r=>({ok:r.ok}))`).catch(()=>({ok:false}));if(!result.ok)console.error('QA account cleanup needs retry');}
  if(a)await a.close();if(b)await b.close();
 }
})().catch(e=>{console.error(e.message);process.exitCode=1;});
