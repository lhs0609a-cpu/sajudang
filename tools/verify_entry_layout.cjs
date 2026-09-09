const {spawn}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const out=process.env.AUDIT_OUT||path.join(os.tmpdir(),'sajudang-layout-hao'),port=19383;
fs.mkdirSync(out,{recursive:true});
const browser=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',['--headless=new','--no-first-run',`--remote-debugging-port=${port}`,`--user-data-dir=${path.join(os.tmpdir(),'sjd-layout-'+process.pid)}`,'about:blank'],{windowsHide:true,stdio:'ignore'});
const pause=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 let pages;for(let i=0;i<80;i++){try{pages=await(await fetch(`http://127.0.0.1:${port}/json`)).json();if(pages.some(p=>p.type==='page'))break;}catch{}await pause(200);}
 const ws=new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);await new Promise(r=>ws.onopen=r);
 let n=0;const pending=new Map(),exceptions=[],results=[];
 ws.onmessage=e=>{const x=JSON.parse(e.data);if(x.method==='Runtime.exceptionThrown')exceptions.push(x.params.exceptionDetails);if(x.id){const p=pending.get(x.id);pending.delete(x.id);x.error?p.reject(x.error):p.resolve(x.result);}};
 const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++n;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
 const run=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;};
 const until=async expression=>{for(let i=0;i<100;i++){if(await run(`Boolean(document.body && (${expression}))`))return;await pause(150);}throw Error('Timeout '+expression);};
 try{
  await send('Runtime.enable');await send('Page.enable');
  await send('Page.addScriptToEvaluateOnNewDocument',{source:`localStorage.setItem('sajudang-session',JSON.stringify({state:{admin:false,adminSet:true},version:0})); localStorage.setItem('sd.sound','off'); window.__audioContexts=[]; const AC=window.AudioContext; if(AC)window.AudioContext=class extends AC { constructor(...a){super(...a);window.__audioContexts.push(this);} };`});
  for(const [width,height] of [[320,740],[390,844],[768,1024],[899,800],[900,600],[1366,768],[1920,911],[1536,728],[960,455]]){
   await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<900});
   await send('Page.navigate',{url:(process.env.WEB_BASE||'http://127.0.0.1:3028')+'/?step=a1'});
   await until(`document.querySelector('.guide-intro')`);await pause(1200);
   const layout=await run(`(()=>{const hero=document.querySelector('.gatehero'),faq=document.querySelector('.gatedoubt'),button=[...document.querySelectorAll('button')].find(b=>b.textContent.includes('내 고민으로 무료 해석 보기'));button.scrollIntoView({block:'center'});const r=button.getBoundingClientRect();return {position:getComputedStyle(hero).position,overlap:faq.getBoundingClientRect().top<hero.getBoundingClientRect().bottom-1,overflow:document.documentElement.scrollWidth>innerWidth,hit:button.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)),cat:!!document.querySelector('.companion-cat svg')};})()`);
   assert.equal(layout.position,'relative');assert.equal(layout.overlap,false);assert.equal(layout.overflow,false);assert.equal(layout.hit,true);assert.equal(layout.cat,true);
   const shot=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(out,width+'x'+height+'.png'),Buffer.from(shot.data,'base64'));
   await run('scrollTo(0,0)');await pause(150);
   const topShot=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(path.join(out,width+'x'+height+'-top.png'),Buffer.from(topShot.data,'base64'));
   if(width===390 && await run(`!!document.querySelector('.entry-greeting-actions button')`)) {
    const point=await run(`(()=>{const b=document.querySelector('.entry-greeting-actions button');b.scrollIntoView({block:'center'});const r=b.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2};})()`);
    await send('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,...point});
    await send('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,...point});
    await until(`localStorage.getItem('sd.sound')==='on' && window.__audioContexts.some(c=>c.state==='running')`);
    assert.equal(await run(`!!document.querySelector('.entry-greeting-portrait video')`),false,'Unproduced greeting must not reuse the old portrait video');
    layout.bgmEnabled=true;
   }
   await run(`[...document.querySelectorAll('button')].find(b=>b.textContent.includes('내 고민으로 무료 해석 보기')).click()`);
   await until(`document.querySelector('[data-screen="a5"]')`);
   assert.equal(await run(`/해요|돼요|괜찮아요|하세요/.test(document.body.innerText)`),false);
   results.push({width,height,...layout});console.log(width,height,'passed');
  }
  assert.equal(exceptions.length,0);fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({results,exceptions},null,2));
 }finally{await Promise.race([send('Browser.close').catch(()=>{}),pause(1500)]);ws.close();browser.kill();}
})().catch(e=>{console.error(e);browser.kill();process.exitCode=1;});
