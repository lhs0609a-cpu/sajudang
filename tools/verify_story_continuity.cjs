// Real local app/API with controlled failures. Payment provider is blocked.
const {spawn}=require('node:child_process'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),assert=require('node:assert/strict');
const out='C:/Users/leegu/AppData/Local/sajudang-continuity-browser',port=19381;
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
 const until=async expression=>{for(let i=0;i<100;i++){if(await run('Boolean('+expression+')'))return;await pause(150);}throw Error('Timeout '+expression+' '+await run('document.body.innerText'));};
 const birth={year:1993,month:11,day:25,hour:null,minute:null,hour_known:false,sex:'F',birth_city:'서울'};
 const chart=await(await fetch('http://127.0.0.1:8026/v1/chart',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(birth)})).json();assert(chart.chart_id);
 const seed={sessionId:'browser-fixes-20260909',year:1993,month:11,day:25,hour:null,minute:0,hourKnown:false,sex:'F',sexSet:true,city:'서울',concern:'money',concernSet:true,chartId:chart.chart_id,cur:'pungun',name:'',read:[],skipped:[],seals:[],tier:'free',paid:false,visits:9,visitDate:'2020-01-01',axis4:null,admin:false,adminSet:true};

 const lenses=JSON.parse(fs.readFileSync(path.join(__dirname,'../seed/lenses.json'),'utf8'));
 const install=async(state)=>{
  if(script)await send('Page.removeScriptToEvaluateOnNewDocument',{identifier:script});
  script=(await send('Page.addScriptToEvaluateOnNewDocument',{source:`localStorage.setItem('sajudang-session',${JSON.stringify(JSON.stringify({state,version:0}))});const real=window.fetch;window.fetch=(input,init)=>real(typeof input==='string'?input.replace('https://sajudang-api.fly.dev','http://127.0.0.1:8026'):input,init);`})).identifier;
 };
 const navigate=async(url,width=390)=>{await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:true});await send('Page.navigate',{url:'http://127.0.0.1:3027'+url});};
 const shot=async(name)=>{const r=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(r.data,'base64'));};
 try {
  await send('Runtime.enable');await send('Page.enable');await send('Network.enable');await send('Network.setBlockedURLs',{urls:['*tosspayments.com*']});
  for(const width of [320,390,768]){
   await install({...seed,chartId:null,cur:'wolha',features:null,year:null,month:null,day:null,sexSet:false,concernSet:false});await navigate('/?step=a1',width);
   await until(`document.querySelector('.guide-intro')&&document.body.innerText.includes('풍운도령')`);
   assert(await run(`(()=>{const guide=document.querySelector('.guide-intro');const cta=[...document.querySelectorAll('button')].find(b=>b.textContent.includes('내 고민으로 무료 해석 보기'));return !!(guide.compareDocumentPosition(cta) & Node.DOCUMENT_POSITION_FOLLOWING);})()`));
   assert.equal(await run(`document.documentElement.scrollWidth>innerWidth`),false);
   await shot('entry-'+width);
   await run(`[...document.querySelectorAll('button')].find(b=>b.textContent.includes('내 고민으로 무료 해석 보기')).click()`);
   await until(`document.querySelector('[data-screen="a5"]')`);
   assert.equal(await run(`JSON.parse(localStorage.getItem('sajudang-session')).state.cur`),'pungun');
   const small=await run(`[...document.querySelectorAll('.top .tb')].filter(e=>{const r=e.getBoundingClientRect();return r.width<44||r.height<44}).map(e=>e.textContent)`);assert.deepEqual(small,[]);
   if(width===390){
    await run(`[...document.querySelectorAll('.op')][0].click()`);
    await run(`[...document.querySelectorAll('button')].find(b=>b.textContent.includes('이 고민으로 이어가기')).click()`);
    await until(`document.querySelector('#birth-year')`);
    for(const [id,value] of [['birth-year','1993'],['birth-month','11'],['birth-day','25']])await run(`(()=>{const el=document.getElementById(${JSON.stringify(id)});Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(el,${JSON.stringify(value)});el.dispatchEvent(new Event('input',{bubbles:true}));})()`);
    await run(`[...document.querySelectorAll('button')].find(b=>b.textContent==='여성').click()`);
    await run(`[...document.querySelectorAll('button')].find(b=>b.textContent.includes('태어난 시간으로 이어가기')).click()`);
    await until(`document.body.innerText.includes('시간을 몰라요')`);
    await run(`[...document.querySelectorAll('button')].find(b=>b.textContent.includes('시간을 몰라요')).click()`);
    await until(`document.body.innerText.includes('내 고민의 무료 해석 읽기')`);
    await run(`[...document.querySelectorAll('button')].find(b=>b.textContent.includes('내 고민의 무료 해석 읽기')).click()`);
    await until(`document.body.innerText.includes('기둥 3자리의 6글자')`);
    assert(await run(`document.body.innerText.includes('풍운도령')`));await shot('fresh-journey-hook');
    results.push({case:'fresh-input-to-unknown-hour-hook',status:'passed'});
   }
   results.push({case:'entry-'+width,status:'passed'});
  }
  for(const lens of lenses){
   await install({...seed,cur:lens.id});await navigate('/report/'+lens.id);
   await until(`document.body.innerText.includes('내 것을 펴겠습니다')`);
   assert(await run(`document.body.innerText.includes(${JSON.stringify(lens.name)})`));
   await run(`[...document.querySelectorAll('button')].find(b=>b.textContent.includes('내 것을 펴겠습니다')).click()`);
   await until(`document.querySelector('.reading-section')`);
   const text=await run('document.body.innerText');assert(!text.includes('도령이 두루마리'),lens.id);assert(!text.includes('도령이 긴 종이'),lens.id);
   assert.equal(await run(`document.documentElement.scrollWidth>innerWidth`),false,lens.id+' overflow');
   if(['pungun','wolha','dongja'].includes(lens.id))await shot('reader-'+lens.id);
   results.push({case:'reader-'+lens.id,status:'passed'});console.log(lens.id,'passed');
  }
  assert.equal(exceptions.length,0);fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({results,exceptions,scope:'3 entry widths and 20 real reader routes; not 10000 browser users'},null,2));
 } finally {await Promise.race([send('Browser.close').catch(()=>{}),pause(1500)]);ws.close();browser.kill();}
})().catch(e=>{console.error(e);browser.kill();process.exitCode=1;});
