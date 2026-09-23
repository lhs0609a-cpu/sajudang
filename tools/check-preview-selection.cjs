const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const ts = require('../apps/web/node_modules/typescript');
const source = fs.readFileSync('apps/web/lib/preview-selection.ts', 'utf8');
const compiled = ts.transpileModule(source, {compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText;
const api = {};
vm.runInNewContext(compiled, {exports:api});
const row = id => Object.freeze({id,title:id,teaser:'actual excerpt',chars:120,need_tier_name:'one'});
const cuts = Object.freeze(['lc_test_root','lc_test_bowl','lc_test_seat','lc_test_tie','lc_test_road','lc_test_pace','concern_pattern','concern_turn','daeun_map'].map(row));
for (const [concern,first] of Object.entries({money:'bowl',work:'seat',love:'seat',people:'tie',dir:'road',health:'pace'})) {
  const selected=api.selectPreviewCuts(cuts,concern);
  assert.equal(selected.map(c=>c.id).join(','),`lc_test_${first},concern_pattern,concern_turn`);
  assert.equal(new Set(selected.map(c=>c.id)).size,3);
  assert.ok(selected.every(c=>cuts.includes(c)));
}
assert.equal(api.selectPreviewCuts([], 'money').length,0);
assert.equal(api.selectPreviewCuts([{...row('hidden'),teaser:''}], 'money').length,0);
assert.equal(api.selectPreviewCuts([row('only')], 'money').length,1);
assert.equal(api.selectPreviewCuts([row('only'),row('only')], 'money').length,1);
assert.equal(api.selectPreviewCuts(cuts,'unknown').length,3);
assert.equal(api.selectPreviewCuts([row('lc_ilgwan_term'),row('concern_pattern'),row('concern_turn')],'money')[0].id,'concern_pattern');
console.log('PASS: 6 concern priorities; sparse, empty, duplicate and unknown-topic fallbacks; source immutability');
