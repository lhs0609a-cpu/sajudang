const assert=require('node:assert/strict');
const {browser}=require('./check-member-browser.cjs');

(async()=>{
  let client;
  try{
    client=await browser(19512,true);
    await client.go('/?step=a5&qa=1');
    await client.until("document.body.innerText.includes('오늘은 어떤 답이')");
    await client.run("Array.from(document.querySelectorAll('.entry-concern')).find(e=>e.innerText.includes('사랑')).click() ");
    await client.run("Array.from(document.querySelectorAll('button')).find(e=>e.innerText.includes('사랑 상황을 더 알려주기')).click()");
    await client.until("document.body.innerText.includes('조금 더 구체적으로')");
    const screen=await client.run("document.body.innerText");
    for(const label of ['짝사랑·썸','연애 중','연인과 갈등 중','결혼을 고민 중','부부 관계','이별 중·이별 후','재회를 고민 중'])assert.ok(screen.includes(label),label);
    await client.run("Array.from(document.querySelectorAll('.entry-situation .op')).find(e=>e.innerText.includes('부부 관계')).click()");
    await client.run("Array.from(document.querySelectorAll('.entry-situation .op')).find(e=>e.innerText.includes('믿음·거짓말 문제')).click()");
    await client.run("Array.from(document.querySelectorAll('.entry-situation .op')).find(e=>e.innerText.includes('결혼 생활이 맞을지')).click()");
    await client.run("Array.from(document.querySelectorAll('.entry-situation .op')).find(e=>e.innerText.includes('거의 나 혼자')).click()");
    await client.run("Array.from(document.querySelectorAll('.entry-situation .op')).find(e=>e.innerText.includes('감정과 관계')).click()");
    await client.run("Array.from(document.querySelectorAll('.entry-situation .btn')).find(e=>e.innerText.includes('이 상황으로 분석하기')).click()");
    await client.until("location.search.includes('step=a3')");
    assert.equal(await client.run("JSON.parse(localStorage.getItem('sajudang-session')).state.topicPick.choice"),'married');
    assert.equal(await client.run("JSON.parse(localStorage.getItem('sajudang-session')).state.topicPick.choice3"),'marry');
    assert.equal(await client.run("JSON.parse(localStorage.getItem('sajudang-session')).state.topicPick.choice4"),'a');
    assert.equal(await client.run("JSON.parse(localStorage.getItem('sajudang-session')).state.topicPick.choice5"),'b');

    const specs=await client.run(`Promise.all(${JSON.stringify(['money','work','love','people','dir','health'])}.map(async concern=>{const r=await fetch('/api/backend/v1/report/topic/'+concern);return {concern,ok:r.ok,data:await r.json()}}))`);
    assert.ok(specs.every(row=>row.ok&&row.data.options.length>=2&&row.data.options2.length>=2&&row.data.options3.length>=2));
    const characterIds=['pungun','baegun','cheongam','sigye','eunbyeol','jeokhyeol','monghwa','seoyeok','paeseon','myeonsang','wolha','hongmae','yeondam','hwagyeong','haengsu','hunjang','yakcho','ilgwan','nopa','dongja'];
    const characterSpecs=await client.run(`Promise.all(${JSON.stringify(['pungun','baegun','cheongam','sigye','eunbyeol','jeokhyeol','monghwa','seoyeok','paeseon','myeonsang','wolha','hongmae','yeondam','hwagyeong','haengsu','hunjang','yakcho','ilgwan','nopa','dongja'])}.map(async id=>{const r=await fetch('/api/backend/v1/report/topic/love?lens_id='+id);return {id,ok:r.ok,data:await r.json()}}))`);
    assert.ok(characterSpecs.every(row=>row.ok&&row.data.options4.length>=4&&row.data.options5.length>=4));
    assert.equal(new Set(characterSpecs.map(row=>row.data.q4+'|'+row.data.q5)).size,characterIds.length);
    const chart=await client.run(`fetch('/api/backend/v1/chart',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({year:1993,month:5,day:15,hour:10,minute:20,hour_known:true,sex:'F',birth_city:'서울'})}).then(r=>r.json())`);
    await client.run(`(()=>{const saved=JSON.parse(localStorage.getItem('sajudang-session'));Object.assign(saved.state,{year:1993,month:5,day:15,hour:10,minute:20,hourKnown:true,sex:'F',sexSet:true,city:'서울',chartId:${JSON.stringify(chart.chart_id)},features:${JSON.stringify(chart.features)},concern:'love',concernSet:true,cur:'pungun',topicPick:{concern:'love',lensId:'pungun',choice:'married',choice2:'trust',choice3:'marry',choice4:'a',choice5:'b'},hookReview:null});localStorage.setItem('sajudang-session',JSON.stringify(saved));})()`);
    await client.go('/?step=a7&qa=1');
    await client.until("document.body.innerText.includes('부부 관계')&&document.body.innerText.includes('믿음·거짓말 문제')&&document.body.innerText.includes('결혼 생활이 맞을지')&&document.body.innerText.includes('거의 나 혼자')&&document.body.innerText.includes('감정과 관계')&&document.body.innerText.includes('/ 7')");
    const report=await client.run(`fetch('/api/backend/v1/report',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({chart_id:${JSON.stringify(chart.chart_id)},lens_id:'pungun',tier:'free',session_id:'browser-situation-check',concern:'love',extras:{topic:{choice:'married',choice2:'trust',choice3:'marry',choice4:'a',choice5:'b'}}})}).then(async r=>({ok:r.ok,data:await r.json()}))`);
    assert.equal(report.ok,true,JSON.stringify(report));
    assert.equal(report.data.asks,null);
    assert.ok(report.data.cuts.some(c=>c.id==='topic_ask'&&c.html.includes('부부 관계')&&c.html.includes('믿음·거짓말 문제')&&c.html.includes('결혼 생활이 맞을지')));

    // A character whose scope changes the concern must not reuse the old answers.
    // Cheongam is the third released seat and maps love to his direction/work scope.
    await client.go('/lobby?tab=b2&qa=1');
    await client.until("document.querySelectorAll('.op.face').length>=3");
    await client.run("document.querySelectorAll('.op.face')[2].click()");
    await client.until("document.querySelector('.seatnow .btn.mt')");
    await client.run("document.querySelector('.seatnow .btn.mt').click()");
    await client.until("location.search.includes('step=a5b')&&location.search.includes('next=')");
    assert.equal(await client.run("JSON.parse(localStorage.getItem('sajudang-session')).state.concern"),'dir');
    assert.equal(await client.run("JSON.parse(localStorage.getItem('sajudang-session')).state.topicPick"),null);
    assert.deepEqual(client.errors,[]);
    console.log('PASS: detailed situation -> all six topics -> focused report -> character scope re-ask');
  }finally{if(client)await client.close();}
})().catch(error=>{console.error(error.stack||error.message);process.exitCode=1;});
