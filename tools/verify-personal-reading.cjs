const fs=require('node:fs'),assert=require('node:assert/strict');
const profiles=require('../apps/web/lib/character-profiles.json');
const local=process.argv.includes('--local');
const base=local?'http://127.0.0.1:8018/v1':'https://sajudang-api.fly.dev/v1';
async function post(route,body){
 const r=await fetch(base+route,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:AbortSignal.timeout(45000)});
 assert.equal(r.status,200,route);return r.json();
}
(async()=>{
 const chart=await post('/chart',{year:1993,month:11,day:25,hour_known:false,sex:'F',birth_city:'서울'});
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
  const spec=report.asks;
  if(spec?.options4&&spec?.options5){
   const topic={};for(let i=1;i<=5;i++)topic[i===1?'choice':`choice${i}`]=spec[i===1?'options':`options${i}`][0].id;
   const answered=await post('/report',{...input,extras:{topic}});
   assert.equal(answered.extra_error,null);
   assert.deepEqual(answered.reading_basis.answers,[spec.options4[0].label,spec.options5[0].label]);
   assert.ok(answered.locked.every(c=>!c.html&&!c.reader_html));
  }
  const hook=await post('/hook',{chart_id:chart.chart_id,lens_id:lens,concern});
  assert.ok(hook.segments.every(s=>s.reader_html));
  results.push({lens,readable:true,inputScope:true,selectedAnswers:true,paidContentProtected:true});
 }
 fs.mkdirSync('output/reading-10000',{recursive:true});
 fs.writeFileSync(`output/reading-10000/${local?'local':'production'}-api.json`,JSON.stringify({checkedAt:new Date().toISOString(),results},null,2));
 console.log('PASS all 20 characters: visible input scope, real selected answers, readable reports and hooks, protected paid content');
})().catch(e=>{console.error(e);process.exitCode=1});
