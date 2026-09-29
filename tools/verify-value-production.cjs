const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const api='https://sajudang-api.fly.dev',site='https://saju.megaload.co.kr';
const out=path.resolve('output/quality-value-20260929');
async function json(url,body){const response=await fetch(url,{...(body?{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)}:{}),signal:AbortSignal.timeout(45000)});assert.equal(response.status,200,url);return response.json();}
(async()=>{
 const health=await json(api+'/health');assert.equal(health.store.durable,true);assert.ok(health.cors_origins.includes(site));
 const chart=await json(api+'/v1/chart',{year:1993,month:11,day:25,hour_known:false,sex:'F',birth_city:'서울'});
 const results=[];
 for(const lens of Object.keys(require('../apps/web/lib/character-profiles.json'))){
  const spec=await json(api+'/v1/report/topic/work?lens_id='+lens);
  const topic=Object.fromEntries([1,2,3,4,5].map(n=>[n===1?'choice':'choice'+n,spec[n===1?'options':'options'+n][0].id]));
  const other={...topic,choice4:spec.options4.at(-1).id,choice5:spec.options5.at(-1).id};
  const get=t=>json(api+'/v1/report',{chart_id:chart.chart_id,lens_id:lens,concern:'work',tier:'free',extras:{topic:t}});
  const first=await get(topic),last=await get(other);
  assert.equal(first.practice.version,4,lens);assert.equal(last.practice.version,4,lens);
  assert.notEqual(first.practice.specialist_verdict,last.practice.specialist_verdict,lens+' reading');
  assert.notEqual(first.practice.specialist_action,last.practice.specialist_action,lens+' action');
  assert.ok(first.practice.specialist_review,lens+' review');
  assert.equal(first.practice.specialist_review,first.practice.steps[2]);
  assert.ok(first.cuts.some(c=>c.html.includes('답변으로 좁힌 첫 해석')),lens+' opening');
  const hook=await json(api+'/v1/hook',{chart_id:chart.chart_id,lens_id:lens,concern:'work',topic});
  assert.ok(!JSON.stringify(hook.segments).includes('여덟 글자'),lens+' unknown hour');
  const action=hook.segments.find(s=>s.stage==='2');assert.ok(action.statement_id.startsWith('answer-decisions-v4:'),lens+' cache edition');
  results.push({lens,version:4,changedReading:true,changedAction:true,reviewConsistent:true,unknownHour:true});
 }
 const response=await fetch(site,{signal:AbortSignal.timeout(45000)});assert.equal(response.status,200);
 assert.ok((await response.text()).includes('같은 고민인데, 답은 어떻게 달라지오?'),'A1 update');
 fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,'production-api.json'),JSON.stringify({checkedAt:new Date().toISOString(),site,api,durable:true,results},null,2));
 console.log('PASS production: 20 characters, 40 reports, 20 hooks, durable storage, A1 update');
})().catch(e=>{console.error(e);process.exitCode=1;});
