const {browser}=require('./check-member-browser.cjs');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const pause=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const a=await browser(19462,true),out=path.resolve('output/member-mbti-release');
 try{
  await a.send('Page.addScriptToEvaluateOnNewDocument',{source:`localStorage.removeItem('sd.sound');window.__bgm={sources:[],gains:[],contexts:[]};const C=window.AudioContext;window.AudioContext=class extends C{constructor(...args){super(...args);window.__bgm.contexts.push(this);}createBufferSource(){const s=super.createBufferSource();window.__bgm.sources.push(s);s.addEventListener('ended',()=>s.__ended=true);return s;}createGain(){const g=super.createGain();window.__bgm.gains.push(g);return g;}};`});
  await a.go('/?qa=1');await a.until('window.__bgm.sources.length===1');
  await a.send('Input.dispatchMouseEvent',{type:'mousePressed',x:25,y:250,button:'left',clickCount:1});await a.send('Input.dispatchMouseEvent',{type:'mouseReleased',x:25,y:250,button:'left',clickCount:1});
  await a.until('window.__bgm.contexts[0].state==="running"');await pause(1300);
  const initial=await a.run(`(()=>{const {sources,gains,contexts}=window.__bgm,s=sources[0],b=s.buffer,d=b.getChannelData(0);return {sources:sources.length,loop:s.loop,loopStart:s.loopStart,loopEnd:s.loopEnd,duration:b.duration,gain:gains[0].gain.value,time:contexts[0].currentTime,seamJump:Math.abs(d[0]-d[d.length-1])};})()`);
  assert.equal(initial.loop,true);assert.ok(Math.abs(initial.gain-.12)<.005);assert.ok(initial.duration>30);assert.equal(initial.loopEnd,initial.duration);
  await a.run("document.querySelector('.seats-shortcut a').click()");await a.until("!!document.querySelector('[data-screen=b2]')");
  await a.run("document.querySelector('a[href=\"/me\"]').click()");await a.until("!!document.querySelector('.member-library')");
  await a.run("document.querySelector('.seats-shortcut a').click()");await a.until("!!document.querySelector('[data-screen=b2]')");
  assert.equal(await a.run('window.__bgm.sources.length'),1);assert.ok(await a.run('window.__bgm.contexts[0].currentTime')>initial.time);
  assert.equal(await a.run('Array.from(document.querySelectorAll("video")).some(v=>!v.muted)'),false);
  const requested=await a.run("performance.getEntriesByType('resource').map(e=>e.name).filter(u=>u.includes('/audio/bgm/'))");assert.ok(requested.length===1&&requested[0].includes('moon-thread-loop.mp3'));
  // Two accelerated full cycles verify that the source does not finish or restart.
  await a.run('window.__bgm.sources[0].playbackRate.value=window.__bgm.sources[0].buffer.duration/2');await pause(4600);assert.equal(await a.run('!!window.__bgm.sources[0].__ended'),false);assert.equal(await a.run('window.__bgm.sources.length'),1);
  await a.run('window.__bgm.sources[0].playbackRate.value=1');await a.run("document.querySelector('.snd').click()");await pause(1100);assert.equal(await a.run('!!window.__bgm.sources[0].__ended'),true);assert.equal(await a.run("localStorage.getItem('sd.sound')"),'off');
  await a.run("document.querySelector('.snd').click()");await a.until('window.__bgm.sources.length===2');await pause(1000);assert.ok(Math.abs(await a.run('window.__bgm.gains[1].gain.value')-.12)<.005);
  const remote=await fetch('https://saju.megaload.co.kr/audio/bgm/moon-thread-loop.mp3');assert.equal(remote.status,200);const hash=crypto.createHash('sha256').update(Buffer.from(await remote.arrayBuffer())).digest('hex');assert.equal(hash,crypto.createHash('sha256').update(fs.readFileSync('BGM/moon-thread-loop.mp3')).digest('hex'));
  for(const old of ['altar','card','hall','outside','study','tray'])assert.equal((await fetch('https://saju.megaload.co.kr/audio/bgm/'+old+'.mp3')).status,404);
  assert.deepEqual(a.errors,[]);fs.writeFileSync(path.join(out,'bgm-checks.json'),JSON.stringify({site:'https://saju.megaload.co.kr',file:'moon-thread-loop.mp3',hash,initial,continuesAcrossPages:true,twoCyclesWithoutRestart:true,oldFilesRemoved:6,videoMusicMuted:true,muteAndResume:true,requests:requested.length,errors:[]},null,2));console.log('PASS: exact BGM file, 12% volume, continuous pages, loop twice, mute/resume, old 6 assets removed');
 }finally{await a.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
