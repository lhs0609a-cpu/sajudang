const assert = require('node:assert/strict');
const { browser } = require('./check-member-browser.cjs');

(async () => {
  const a = await browser(19471, true);
  try {
    await a.send('Emulation.setDeviceMetricsOverride', {
      width: 390, height: 844, deviceScaleFactor: 1, mobile: true,
    });
    await a.go('/?qa=1');
    await a.until("document.querySelector('.journey-guide')?.classList.contains('show')");
    const ui = await a.run(`(() => {
      const s = document.querySelector('.sound-float .snd').getBoundingClientRect();
      const g = document.querySelector('.journey-guide').getBoundingClientRect();
      return {
        soundCount: document.querySelectorAll('.sound-float .snd').length,
        soundPosition: getComputedStyle(document.querySelector('.sound-float')).position,
        soundLabel: document.querySelector('.sound-float .snd').innerText.trim(),
        sound: [s.left, s.top, s.right, s.bottom, s.width, s.height],
        guidePosition: getComputedStyle(document.querySelector('.journey-guide')).position,
        guideText: document.querySelector('.journey-guide').innerText,
        guide: [g.left, g.top, g.right, g.bottom],
        overflow: document.documentElement.scrollWidth > innerWidth + 1,
      };
    })()`);
    assert.equal(ui.soundCount, 1);
    assert.equal(ui.soundPosition, 'fixed');
    assert.ok(ui.sound[4] >= 44 && ui.sound[5] >= 44 && ui.sound[0] >= 0 && ui.sound[2] <= 390);
    assert.equal(ui.guidePosition, 'fixed');
    assert.ok(ui.guide[0] >= 0 && ui.guide[2] <= 390 && ui.guide[3] <= 844);
    assert.ok(ui.guideText.includes('진행 가이드'));
    assert.equal(ui.overflow, false);
    await a.go('/lobby');
    await a.until("document.querySelector('.journey-guide')?.classList.contains('show')");
    assert.equal(await a.run("document.querySelectorAll('.sound-float .snd').length"), 1);
    assert.equal(await a.run("document.querySelectorAll('.journey-guide').length"), 1);
    const consultation = await a.run(`(async () => {
      const chartResponse = await fetch('/api/backend/v1/chart', {
        method: 'POST', headers: {'content-type': 'application/json'},
        body: JSON.stringify({year:1993,month:5,day:15,hour:10,minute:20,hour_known:true,sex:'F',birth_city:'서울'})
      });
      if (!chartResponse.ok) throw new Error('chart ' + chartResponse.status);
      const chart = await chartResponse.json();
      const spec = await fetch('/api/backend/v1/report/topic/love?lens_id=wolha').then(r => r.json());
      const topic = {};
      for (const [suffix, key] of [['','options'],['2','options2'],['3','options3'],['4','options4'],['5','options5']]) {
        if (spec[key]?.[0]) topic['choice' + suffix] = spec[key][0].id;
      }
      const response = await fetch('/api/backend/v1/report', {
        method: 'POST', headers: {'content-type': 'application/json'},
        body: JSON.stringify({chart_id:chart.chart_id,lens_id:'wolha',tier:'free',session_id:'guide-production-check',concern:'love',extras:{topic}})
      });
      if (!response.ok) throw new Error('report ' + response.status);
      return {report: await response.json(), chart, topic};
    })()`);
    const report = consultation.report;
    assert.equal(report.practice.specialist_axis, '말하지 않은 기대와 지켜지지 않은 약속');
    assert.ok(report.practice.case_summary.includes('/'));
    assert.ok(report.practice.specialist_verdict.length > 25);
    assert.ok(report.practice.specialist_action.length > 25);
    assert.ok(report.practice.specialist_close.length > 25);
    await a.run(`(() => {
      const saved = JSON.parse(localStorage.getItem('sajudang-session'));
      Object.assign(saved.state, {
        year:1993,month:5,day:15,hour:10,minute:20,hourKnown:true,sex:'F',sexSet:true,city:'서울',
        chartId:${JSON.stringify(consultation.chart.chart_id)},features:${JSON.stringify(consultation.chart.features)},
        cur:'wolha',concern:'love',concernSet:true,tier:'free',
        topicPick:{chartId:${JSON.stringify(consultation.chart.chart_id)},lensId:'wolha',concern:'love',...${JSON.stringify(consultation.topic)}}
      });
      localStorage.setItem('sajudang-session', JSON.stringify(saved));
    })()`);
    await a.go('/pay?step=d0');
    await a.until("!!document.querySelector('.practice-verdict')");
    assert.ok(await a.run("document.querySelector('.practice-verdict').innerText.includes('날카로운 판정')"));
    assert.ok(await a.run("document.querySelector('.practice-mission').innerText.includes('오늘의 QUEST 01')"));
    assert.equal(await a.run("document.querySelectorAll('.inline-paid-reading').length"), 2);
    assert.equal(await a.run("document.querySelectorAll('.inline-paid-mask').length"), 2);
    assert.equal(await a.run("document.documentElement.scrollWidth > innerWidth + 1"), false);
    await a.go('/pay?step=d1');
    await a.until("!!document.querySelector('.conversion-product')");
    await a.run("document.querySelector('.conversion-product').click()");
    await a.until("document.querySelectorAll('.checkout-real-preview article').length >= 1");
    assert.equal(await a.run("document.querySelectorAll('.checkout-reveal-after li').length"), 3);
    assert.ok(await a.run("document.querySelector('.checkout-reveal').innerText.includes('결제 후 가장 먼저 밝혀지는 것')"));
    assert.ok(await a.run("document.querySelector('.checkout-open-list summary').innerText.includes('결제하면 열리는')"));
    assert.equal(await a.run("document.querySelector('.checkout-open-list').open"), true);
    assert.ok(await a.run("document.querySelector('.checkout-reveal').compareDocumentPosition(document.querySelector('#checkout-terms')) & Node.DOCUMENT_POSITION_FOLLOWING"));
    assert.equal(await a.run("document.documentElement.scrollWidth > innerWidth + 1"), false);
    assert.deepEqual(a.errors, []);
    console.log(JSON.stringify({ pass: true, mobile: ui, pages: ['/', '/lobby', '/pay?step=d0', '/pay?step=d1'], specialistPractice: true, strategicPaidVeils: 2, checkoutQuestionsBeforePayment: true }));
  } finally {
    await a.close();
  }
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
