const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),ts=require('../apps/web/node_modules/typescript');
const js=ts.transpileModule(fs.readFileSync('apps/web/lib/toss.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
function setup(){
 const scripts=[],timers=new Map();let n=0;
 const ctx={exports:{},window:{location:{origin:'https://example.com'}},document:{createElement:()=>({remove(){this.removed=true;}}),head:{appendChild:e=>scripts.push(e)}},setTimeout:fn=>{timers.set(++n,fn);return n;},clearTimeout:id=>timers.delete(id)};
 vm.runInNewContext(js,ctx);return{ctx,scripts,timers,api:ctx.exports};
}
(async()=>{
 for(const error of ['network','missing-factory','timeout']){
   const {ctx,scripts,timers,api}=setup();
   const first=api.loadToss();assert.equal(api.loadToss(),first,'Concurrent loads must share a script');
   const rejected=assert.rejects(first);
   if(error==='network')scripts[0].onerror();else if(error==='missing-factory')scripts[0].onload();else [...timers.values()][0]();
   await rejected;assert.ok(scripts[0].removed);assert.equal(timers.size,0);
   const retry=api.loadToss();assert.equal(scripts.length,2);
   ctx.window.TossPayments=()=>({});scripts[1].onload();assert.equal(await retry,ctx.window.TossPayments);assert.equal(timers.size,0);
 }
 const {ctx,api}=setup();let request;
 ctx.window.TossPayments=key=>{assert.equal(key,'test-public');return{payment:({customerKey})=>{assert.equal(customerKey,'anonymous-hash');return{requestPayment:async r=>{request=r;}};}};};
 await api.openCheckout({clientKey:'test-public',customerKey:'anonymous-hash',orderId:'sjd_test',orderName:'Reading',amount:9900});
 assert.equal(request.amount.value,9900);assert.equal(request.orderId,'sjd_test');
 assert.ok(request.successUrl.includes('toss=ok&order=sjd_test'));assert.ok(request.failUrl.includes('toss=fail&order=sjd_test'));
 console.log('PASS SDK network failure, missing factory, timeout, retries, concurrent loading, checkout parameters');
})().catch(e=>{console.error(e);process.exitCode=1;});
