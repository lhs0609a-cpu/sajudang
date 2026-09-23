const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const {browser}=require('./check-member-browser.cjs');

const stamp=crypto.randomBytes(7).toString('hex');
const password='Together!'+crypto.randomBytes(12).toString('base64url');
const hostName='together_host_'+stamp;
const guestName='together_guest_'+stamp;

function request(path,body){
  return `(async()=>{const r=await fetch(${JSON.stringify('/api/backend'+path)},{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(${JSON.stringify(body)})});const data=await r.json();return {ok:r.ok,status:r.status,data};})()`;
}

async function sessionId(client){
  await client.until("!!localStorage.getItem('sajudang-session')");
  return client.run("JSON.parse(localStorage.getItem('sajudang-session')).state.sessionId");
}

async function signup(client,username,sid){
  const result=await client.run(request('/v1/account/signup',{username,password,session_id:sid,consent:true}));
  assert.equal(result.ok,true,JSON.stringify(result));
}

async function save(client,birth,name){
  const result=await client.run(request('/v1/account/save',{birth,lens_id:'jeokhyeol',concern:'love',axis4:null,name,tier:'free'}));
  assert.equal(result.ok,true,JSON.stringify(result));
}

async function remove(client){
  return client.run(request('/v1/account/delete',{password,confirm:true})).catch(()=>({ok:false}));
}

(async()=>{
  let host,guest,hostRegistered=false,guestRegistered=false;
  try{
    host=await browser(19502,true);
    await host.go('/?qa=1');
    const hostSid=await sessionId(host);
    await signup(host,hostName,hostSid);hostRegistered=true;
    await save(host,{year:1991,month:4,day:17,hour:9,minute:30,hour_known:true,sex:'F',birth_city:'서울'},'운영 초대 검증 A');
    const invite=await host.run(request('/v1/referral/invite',{}));
    assert.equal(invite.ok,true,JSON.stringify(invite));
    assert.match(invite.data.code,/^[A-Za-z0-9_-]{20,64}$/);

    guest=await browser(19503,true);
    await guest.go('/?invite='+encodeURIComponent(invite.data.code)+'&with=lover&qa=1');
    await guest.until("document.body.innerText.includes('소중한 사람이 함께 보자고 했어요')");
    assert.equal(await guest.run("localStorage.getItem('sd.invite.relation')"),'lover');
    const guestSid=await sessionId(guest);
    await signup(guest,guestName,guestSid);guestRegistered=true;
    await save(guest,{year:1988,month:11,day:3,hour:20,minute:10,hour_known:true,sex:'M',birth_city:'서울'},'운영 초대 검증 B');
    const claim=await guest.run(request('/v1/referral/claim',{code:invite.data.code,relation:'lover'}));
    assert.equal(claim.ok,true,JSON.stringify(claim));
    assert.equal(claim.data.credit.percent,5);
    assert.equal(claim.data.comparisons[0].relation_label,'연인');
    assert.equal(claim.data.comparisons[0].status,'ready');

    const both=await Promise.all([
      host.run(request('/v1/referral/comparisons',{})),
      guest.run(request('/v1/referral/comparisons',{})),
    ]);
    for(const side of both){
      assert.equal(side.ok,true,JSON.stringify(side));
      const row=side.data.comparisons[0];
      assert.equal(row.status,'ready');
      assert.equal(row.relation,'lover');
      for(const key of ['shared','difference','watch','action'])assert.ok(row[key]);
      const publicData=JSON.stringify(row);
      assert.equal(publicData.includes(hostName)||publicData.includes(guestName)||publicData.includes('1991')||publicData.includes('1988'),false);
    }

    await guest.go('/me');
    await guest.until("document.body.innerText.includes('연인 · 함께 보기')");
    assert.ok(await guest.run("document.body.innerText.includes('생년월일은 서로 공개하지')"));
    assert.ok(await guest.run("document.body.innerText.includes('우리 둘의 공통점과 차이')"));
    assert.deepEqual(host.errors,[]);assert.deepEqual(guest.errors,[]);
    console.log('PASS: production together-view invite, consent, lover relation, two-sided private comparison, 5% credit');
  }finally{
    if(guest&&guestRegistered){const result=await remove(guest);if(!result.ok)console.error('Guest QA account cleanup needs retry');}
    if(host&&hostRegistered){const result=await remove(host);if(!result.ok)console.error('Host QA account cleanup needs retry');}
    if(guest)await guest.close();if(host)await host.close();
  }
})().catch(error=>{console.error(error.stack||error.message);process.exitCode=1;});
