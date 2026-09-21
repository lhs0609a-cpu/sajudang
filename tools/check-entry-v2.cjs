const {spawn}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const out=path.resolve('output/a1-a7-research-20260921/screens');
fs.mkdirSync(out,{recursive:true});
const base='http://127.0.0.1:3038',api='http://127.0.0.1:8018',port=19389;
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
 try{
  await send('Runtime.enable');await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
  await send('Page.addScriptToEvaluateOnNewDocument',{source:`localStorage.setItem('sd.sound','off');if(!sessionStorage.getItem('entry-v2-test')){localStorage.setItem('sajudang-session',JSON.stringify({state:{admin:false,adminSet:true},version:0}));sessionStorage.setItem('entry-v2-test','1');}`});
  await send('Page.navigate',{url:base+'/?step=a1'});await screen('a1');await capture('a1',390);
  await click('내 고민으로 무료 해석 보기');await screen('a5');await capture('a5',390);
  await run(`document.querySelectorAll('.entry-concern')[2].click()`);await click('이야기로 이어가기');await screen('a3');await capture('a3',390);
  await fill('birth-year','1993');await fill('birth-month','2');await fill('birth-day','31');
  assert.ok(await run(`!!document.querySelector('#birth-error')`));
  await fill('birth-month','7');await fill('birth-day','14');await click('여성');await click('태어난 시간으로');await screen('a4');await capture('a4',390);
  await run(`document.querySelector('.entry-faq').open=true`);await click('별칭 입력');await screen('a2');await capture('a2',390);await fill('entry-alias','가은');await click('이 이름으로');await screen('a4');
  await click('시간을 모르오');await screen('a4b');await capture('a4b',390);
  await click('INFP');await click('선택한 성향으로');await screen('a6');await until(`document.querySelector('.entry-chart')`);await capture('a6',390);
  assert.ok(await run(`document.querySelector('.entry-chart').innerText.includes('여섯 글자')`));
  await click('내 고민의 무료 해석');await screen('a7');await until(`document.querySelector('.hook-chapter')`);await capture('a7',390);
  await click('아닙니다');await click('아닙니다');await pause(700);
  await until(`[...document.querySelectorAll('.first-reading-action')].some(e=>e.textContent.includes('맞지 않는 부분'))`);
  await click('맞습니다');await click('잘 모르겠습니다');await click('맞습니다');await until(`document.querySelector('.entry-afterword')`);
  await send('Page.reload');await screen('a7');await until(`document.querySelector('.entry-afterword')`);
  assert.ok(await run(`document.querySelector('.hook-progress').textContent.includes('5 / 5')`));
  await click('내 사랑의 반복과 이유 읽기');await until(`document.querySelector('[data-screen="d0"]')`);
  results.push({flow:'a1-a5-a3-a4-a2-a4-a4b-a6-a7-d0',invalidDate:true,unknownHour:true,alias:true,axis:true,rejection:true,restore:true});
  for(const width of [320,1366]){
   await send('Emulation.setDeviceMetricsOverride',{width,height:width===320?740:900,deviceScaleFactor:1,mobile:width<900});
   for(const step of ['a1','a5','a3','a4','a4b','a6','a7']){
    await send('Page.navigate',{url:base+'/?step='+step});await screen(step);
    if(step==='a6')await until(`document.querySelector('.entry-chart')`);
    if(step==='a7')await until(`document.querySelector('.hook-chapter')`);
    await capture(step,width);
   }
  }
  const cr=await fetch(api+'/v1/chart',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({year:1987,month:11,day:3,hour:17,minute:40,hour_known:true,sex:'M',birth_city:'서울'})});const chart=await cr.json();assert.ok(chart.chart_id);
  for(const concern of ['money','work','love','people','dir','health']){
   const response=await fetch(api+'/v1/hook',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({chart_id:chart.chart_id,concern,lens_id:'pungun'})});
   const data=await response.json();assert.equal(response.status,200);assert.equal(data.segments.length,5);assert.ok(data.segments[0].statement_id.startsWith('first-reading-v2'));
   results.push({concern,segments:5,source:data.segments[0].source});
  }
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
  await send('Page.navigate',{url:base+'/?step=a4'});await screen('a4');
  await fill('birth-hour','25');
  assert.ok(await run(`[...document.querySelectorAll('button')].find(b=>b.textContent.includes('이 시간으로')).disabled`));
  await fill('birth-hour','15');await fill('birth-minute','99');
  assert.ok(await run(`[...document.querySelectorAll('button')].find(b=>b.textContent.includes('이 시간으로')).disabled`));
  await fill('birth-minute','20');await click('이 시간으로');await screen('a4b');
  await click('사주만으로 보기');await screen('a6');await until(`document.querySelector('.entry-chart')`);
  assert.ok(await run(`document.querySelector('.entry-chart').innerText.includes('여덟 글자')`));
  await click('내 고민의 무료 해석');await screen('a7');await until(`document.querySelector('.hook-chapter')`);
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  await capture('a7-known-hour',390);
  assert.ok(await run(`document.querySelector('.hook-progress').textContent.includes('0 / 5')`));
  results.push({knownHour:true,invalidHour:true,invalidMinute:true,skipAxis:true,reducedMotion:true,newChartResetsReview:true});
  assert.equal(exceptions.length,0,JSON.stringify(exceptions));
  fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({results,exceptions},null,2));console.log('PASS:',results.length,'checks; screenshots:',out);
 }finally{await Promise.race([send('Browser.close').catch(()=>{}),pause(1500)]);ws.close();browser.kill();}
})().catch(e=>{console.error(e);browser.kill();process.exitCode=1;});
