const fs=require('node:fs'),assert=require('node:assert/strict');
const profiles=require('../apps/web/lib/character-profiles.json');
const local=process.argv.includes('--local');
const personalization=process.argv.includes('--personalization');
const output=personalization?'output/personalization-audit':'output/reading-10000';
const base=local?'http://127.0.0.1:8018/v1':'https://sajudang-api.fly.dev/v1';
async function post(route,body){
 const r=await fetch(base+route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:AbortSignal.timeout(45000)});
 assert.equal(r.status,200,route);return r.json();
}
(async()=>{
 const chart=await post('/chart',{year:1993,month:11,day:25,hour_known:false,sex:'F',birth_city:'서울'});
 for(const year of [1900,1920,1935]){
  const old=await post('/chart',{year,month:5,day:17,hour_known:false,sex:'F',birth_city:'서울'});
  const f=old.features,current=f.daeun[f.daeun_now];
  assert.ok(current.start_age<=f.age&&f.age<current.start_age+10,'current decade covers '+year);
 }
 const boundary=await post('/chart',{year:1951,month:1,day:1,hour:0,minute:0,hour_known:true,sex:'M',birth_city:'서울'});
 assert.equal(boundary.features.birth_year,1951);
 const results=[];
 for(const [lens,profile] of Object.entries(profiles)){
  const concern=profile.concerns[0]||'work';
  const input={chart_id:chart.chart_id,lens_id:lens,tier:'free',concern};
  const report=await post('/report',input);
  assert.ok(report.reading_basis?.birth.includes('시간은 제외'),lens+' input scope');
  assert.deepEqual(report.reading_basis.answers,[],lens+' no invented answers');
  assert.ok(report.cuts.every(c=>c.reader_html&&c.reader_title));
  assert.ok(report.locked.every(c=>!c.html&&!c.reader_html));
  const depth=report.cuts.find(c=>c.id==='spine_depth');
  if(depth)assert.ok(depth.reader_html.includes('personal-reading'));
  if(personalization){
   assert.equal(report.reading_basis.version,'personal-reading-v3');
   const composite=depth||report.cuts.find(c=>c.id==='yongsin');
   assert.ok(composite?.reader_html.includes('chart-synthesis'),lens+' composite chart reasoning');
   if(!depth)assert.equal(report.sells,false,lens+' free-only scope');
   const scene=report.cuts.find(c=>c.id==='spine_scene');
   if(scene)assert.ok(scene.reader_html.includes('올해 글자가 닿는 생활 자리'),lens+' position-specific timing');
   else assert.equal(report.sells,false,lens+' free-only timing scope');
  }
  const spec=report.asks;
  assert.ok(spec?.options4&&spec?.options5,lens+' character questions');
  if(spec?.options4&&spec?.options5){
   const topic={};for(let i=1;i<=5;i++)topic[i===1?'choice':`choice${i}`]=spec[i===1?'options':`options${i}`][0].id;
   const answered=await post('/report',{...input,extras:{topic}});
   assert.equal(answered.extra_error,null);
   assert.deepEqual(answered.reading_basis.answers,[spec.options4[0].label,spec.options5[0].label]);
   assert.ok(answered.locked.every(c=>!c.html&&!c.reader_html));
  }
  const hook=await post('/hook',{chart_id:chart.chart_id,lens_id:lens,concern});
  assert.ok(hook.segments.every(s=>s.reader_html));
  if(lens==='pungun'){
   const preview=await post('/pay/peek',{chart_id:chart.chart_id,lens_id:lens,tier:'one',concern});
   const lack=preview.rows.find(r=>r.cut_id==='lack');
   assert.ok(lack?.reader_head&&!lack.reader_head.includes('못 타고났'));
   assert.ok(lack.reader_head.includes('해당하는 글자'));
  }
  results.push({lens,readable:true,inputScope:true,selectedAnswers:true,paidContentProtected:true});
 }
 const collisionChecks=[];
 if(personalization){
  const collisions=JSON.parse(fs.readFileSync('output/personalization-audit/before/collisions.json','utf8'));
  for(const example of collisions){
   const texts=[];
   for(const row of example.pair){
    const [year,month,day,hour,minute,sex,hour_known]=row.input;
    const c=await post('/chart',{year,month,day,hour,minute,sex,hour_known,birth_city:'서울'});
    const r=await post('/report',{chart_id:c.chart_id,lens_id:row.lens,tier:'free',concern:row.concern});
    const core=r.cuts.find(c=>c.id==='spine_depth');
    const delivered=core?[core]:r.cuts.filter(c=>['why','daeun_now','yongsin'].includes(c.id));
    assert.ok(delivered.length,'available composite reading');
    if(!core)assert.equal(r.sells,false);
    texts.push(delivered.map(c=>c.reader_html.split('<details')[0]).join('\n').replace(/[0-9一-龥\s]+/g,''));
   }
   assert.notEqual(texts[0],texts[1],example.lens+' previously identical core now reflects different chart structure');
   collisionChecks.push({lens:example.lens,previouslyIdenticalCoreCaseNowDistinguished:true,compared:example.lens==='dongja'?'available free-only chapters':'core'});
  }
 }
 fs.mkdirSync(output,{recursive:true});
 fs.writeFileSync(`${output}/${local?'local':'production'}-api.json`,JSON.stringify({checkedAt:new Date().toISOString(),results,collisionChecks},null,2));
 console.log('PASS all 20 characters: visible input scope, real selected answers, readable reports and hooks, protected paid content');
})().catch(e=>{console.error(e);process.exitCode=1});
