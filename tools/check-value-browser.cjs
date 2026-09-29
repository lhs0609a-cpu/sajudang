const {spawn}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const production=process.argv.includes('--production');
const out=path.resolve('output/quality-value-20260929/'+(production?'production-screens':'screens'));fs.mkdirSync(out,{recursive:true});
const base=production?'https://saju.megaload.co.kr':'http://localhost:3038',port=19529,pause=ms=>new Promise(r=>setTimeout(r,ms));
const browser=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',['--headless=new','--no-first-run',`--remote-debugging-port=${port}`,`--user-data-dir=${path.join(os.tmpdir(),'sjd-value-'+process.pid)}`,'about:blank'],{windowsHide:true,stdio:'ignore'});
(async()=>{
 let pages;for(let i=0;i<80;i++){try{pages=await(await fetch(`http://127.0.0.1:${port}/json`)).json();if(pages.some(p=>p.type==='page'))break;}catch{}await pause(250);}
 assert.ok(pages,'Browser unavailable');
 const ws=new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);await new Promise(r=>ws.onopen=r);
 let id=0;const pending=new Map(),errors=[],results=[];
 ws.onmessage=e=>{const x=JSON.parse(e.data);if(x.method==='Runtime.exceptionThrown')errors.push(x.params.exceptionDetails);if(x.id){const p=pending.get(x.id);pending.delete(x.id);x.error?p.reject(x.error):p.resolve(x.result);}};
 const send=(method,params={})=>new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}));});
 const run=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;};
 const until=async expr=>{for(let i=0;i<240;i++){if(await run(`Boolean(document.body && (${expr}))`))return;await pause(250);}throw Error('Timeout '+expr);};
 const screen=name=>until(`document.querySelector('[data-screen="${name}"]')`);
 const click=async label=>{await until(`[...document.querySelectorAll('button')].some(b=>b.textContent.includes(${JSON.stringify(label)})&&!b.disabled&&Object.keys(b).some(k=>k.startsWith('__reactProps')))`);await run(`[...document.querySelectorAll('button')].find(b=>b.textContent.includes(${JSON.stringify(label)})&&!b.disabled).click()`);await pause(500);};
 const fill=async(id,value)=>{await run(`(()=>{const e=document.getElementById(${JSON.stringify(id)});Object.getOwnPropertyDescriptor(e instanceof HTMLSelectElement?HTMLSelectElement.prototype:HTMLInputElement.prototype,'value').set.call(e,${JSON.stringify(value)});e.dispatchEvent(new Event(e instanceof HTMLSelectElement?'change':'input',{bubbles:true}));})()`);await pause(100);};
 const shot=async(name)=>{await pause(400);const check=await run(`({overflow:document.documentElement.scrollWidth>innerWidth+1,broken:[...document.images].filter(i=>i.complete&&!i.naturalWidth).map(i=>i.src),text:document.body.innerText})`);assert.equal(check.overflow,false,name+' overflow');assert.deepEqual(check.broken,[],name+' images');const s=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(s.data,'base64'));results.push({screen:name,overflow:false,brokenImages:0});};
 try{
  await send('Runtime.enable');await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
  await send('Page.addScriptToEvaluateOnNewDocument',{source:`localStorage.setItem('sd.sound','off');if(!sessionStorage.getItem('value-audit')){localStorage.setItem('sajudang-session',JSON.stringify({state:{admin:false,adminSet:true},version:0}));sessionStorage.setItem('value-audit','1');}`});
  await send('Page.navigate',{url:base+'/?step=a1'});await screen('a1');await pause(1800);await shot('390-a1');
  await run(`document.querySelector('.entry-sample').open=true;document.querySelector('.entry-sample').scrollIntoView({block:'center'})`);await shot('390-a1-example');
  await click('내 고민으로 무료 해석 보기');await screen('a5');await shot('390-a5');
  await run(`document.querySelectorAll('.entry-concern')[1].click()`);await click('상황을 더 알려주기');await screen('a5b');
  await until(`document.querySelectorAll('.entry-situation [role="group"]').length===5`);await shot('390-a5b');
  await run(`document.querySelectorAll('.entry-situation [role="group"]').forEach(g=>g.querySelector('button').click())`);await click('이 상황으로 분석하기');await screen('a3');
  await fill('birth-year','2001');await fill('birth-month','2');await fill('birth-day','29');assert.equal(await run(`document.getElementById('birth-day').value`),'');
  await fill('birth-year','1993');await fill('birth-month','11');await fill('birth-day','25');await click('여성');await shot('390-a3');await click('태어난 시간으로');await screen('a4');await shot('390-a4');
  await click('시간을 모르겠습니다');await screen('a4b');await shot('390-a4b');await click('사주만으로 보기');await screen('a6');await until(`document.querySelector('.entry-chart')`);await shot('390-a6');
  assert.ok(await run(`document.querySelector('.entry-chart').textContent.includes('여섯 글자')`));
  await click('내 고민의 무료 해석');await screen('a7');await until(`document.querySelector('.hook-chapter')`);await shot('390-a7');
  for(let i=0;i<120;i++){
   const done=await run(`(()=>{if(document.querySelector('.entry-afterword'))return true;const b=[...document.querySelectorAll('button')].find(b=>b.textContent==='맞습니다'&&!b.disabled);if(b)b.click();return false;})()`);
   if(done)break;await pause(600);
  }
  await until(`document.querySelector('.entry-afterword')`);await run(`document.querySelector('.entry-afterword .btn').click()`);await screen('d0');
  await until(`document.querySelector('.practice-mission')`);await run(`document.querySelector('.practice-verdict').scrollIntoView({block:'start'})`);await shot('390-action');
  assert.ok(await run(`document.querySelector('.practice-verdict').textContent.includes('나눌 사람이 없는 구조')`));
  assert.ok(await run(`document.querySelector('.practice-decision').textContent.includes('다음 날')`));
  assert.equal(await run(`document.querySelectorAll('.practice-steps').length`),0);
  results.push({journey:'a1-a5-a5b-a3-a4-a4b-a6-a7-d0',invalidDateBlocked:true,unknownHour:true,answerApplied:true,duplicateTasksRemoved:true});
  for(const width of [320,1366]){
   await send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:width<900});
   await send('Page.navigate',{url:base+'/?step=a1'});await screen('a1');await shot(width+'-a1');
   await send('Page.navigate',{url:base+'/pay?step=d0'});await screen('d0');await until(`document.querySelector('.practice-mission')`);await run(`document.querySelector('.practice-verdict').scrollIntoView({block:'start'})`);await shot(width+'-action');
  }
  assert.deepEqual(errors,[]);fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({results,errors},null,2));console.log('PASS',results.length,'browser checks');
 }catch(e){fs.writeFileSync(path.join(out,'failure.json'),JSON.stringify({error:String(e),errors,state:await run(`({url:location.href,text:document.body.innerText})`)},null,2));throw e;}
 finally{await Promise.race([send('Browser.close').catch(()=>{}),pause(1500)]);ws.close();browser.kill();}
})().catch(e=>{console.error(e);browser.kill();process.exitCode=1;});
