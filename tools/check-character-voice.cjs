const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const ts=require('../apps/web/node_modules/typescript');
const cache={};function load(file){file=path.resolve(file);if(cache[file])return cache[file];if(file.endsWith('.json'))return JSON.parse(fs.readFileSync(file,'utf8'));const exp={};cache[file]=exp;const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020,esModuleInterop:true}}).outputText;vm.runInNewContext(code,{exports:exp,require:name=>load(path.resolve(path.dirname(file),name)+(name.endsWith('.json')?'':'.ts'))});return exp;}
const voice=load('apps/web/lib/character-voice.ts'),topic=load('apps/web/lib/character-topic.ts');
const rows=JSON.parse(fs.readFileSync('output/character-consistency/voice-parity.json','utf8'));const errors=[];
for(const [word,tone,ask,expected] of rows){const actual=voice.voiceWord(word,tone,ask);if(actual!==expected)errors.push({word,tone,ask,expected,actual});}
assert.deepEqual(errors.slice(0,20),[]);
assert.equal(topic.characterConcern('jeokhyeol','money'),'love');
assert.equal(topic.characterConcern('haengsu','love'),'money');
assert.equal(topic.characterConcern('pungun','money'),'money');
assert.equal(voice.characterText('그대가 그대로 보시오.','jeokhyeol'),'네가 그대로 봐.');
assert.equal(voice.characterText('그대는 준비됐소?','yeondam'),'당신은 준비됐습니까?');
assert.equal(voice.characterText('“제가 할게요”라고 말하시오.','jeokhyeol'),'“제가 할게요”라고 말해.');
console.log('PASS',rows.length,'server/browser ending parity cases, address particles, quotations, specialist topic switches');
