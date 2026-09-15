// Edit only TypeScript string/template/JSX text nodes, never code or comments.
const fs=require('node:fs'),path=require('node:path'),ts=require('typescript');
const root=path.resolve(__dirname,'..');
function hao(s){
 const pairs={'어떻게 불러드릴까요?':'어떻게 부르면 되겠소?','괜찮아요':'괜찮소','몰라요':'모르오','알아요':'아오','좋아요':'좋소','주세요':'주시오','보세요':'보시오','마세요':'마시오','하세요':'하시오','계세요':'계시오','이에요':'이오','예요':'요','했어요':'했소','됐어요':'됐소','해요':'하오','돼요':'되오','봐요':'보오','드려요':'드리오','달라져요':'달라지오','어려워요':'어렵소','쉬워요':'쉽소','고마워요':'고맙소','달라요':'다르오','할까요':'하겠소','볼까요':'보겠소','싶어요':'싶소','여세요':'여시오','누르세요':'누르시오','고르세요':'고르시오'};
 for(const [a,b] of Object.entries(pairs))s=s.split(a).join(b);
 s=s.replace(/습니다/g,'소').replace(/습니까/g,'소').replace(/세요/g,'시오');
 s=s.replace(/([가-힣])니다/g,(all,c)=>(c.charCodeAt(0)-0xac00)%28===17?String.fromCharCode(c.charCodeAt(0)-17)+'오':all);
 s=s.replace(/([가-힣])게요/g,(all,c)=>(c.charCodeAt(0)-0xac00)%28===8?String.fromCharCode(c.charCodeAt(0)-8)+'겠소':all);
 return s.replace(/어요|아요|네요/g,'소');
}
let changed=0;const remaining=[];
function visitFile(file){
 const original=fs.readFileSync(file,'utf8');let text=original;
 const sf=ts.createSourceFile(file,text,ts.ScriptTarget.Latest,true,file.endsWith('.tsx')?ts.ScriptKind.TSX:ts.ScriptKind.TS),edits=[];
 function walk(n){
  if(ts.isStringLiteral(n)||ts.isNoSubstitutionTemplateLiteral(n)||ts.isJsxText(n)||[ts.SyntaxKind.TemplateHead,ts.SyntaxKind.TemplateMiddle,ts.SyntaxKind.TemplateTail].includes(n.kind)){
   const a=n.getStart(sf),b=n.end,raw=text.slice(a,b),next=hao(raw);
   if(raw!==next)edits.push([a,b,next]);return;
  }ts.forEachChild(n,walk);
 }walk(sf);
 if(edits.length){changed++;for(const [a,b,next] of edits.reverse())text=text.slice(0,a)+next+text.slice(b);if(process.argv.includes('--write'))fs.writeFileSync(file,text);else remaining.push(path.relative(root,file));}
}
function walkDir(dir){for(const e of fs.readdirSync(dir,{withFileTypes:true})){const p=path.join(dir,e.name);if(e.isDirectory())walkDir(p);else if(/\.tsx?$/.test(p))visitFile(p);}}
for(const dir of ['apps/web/app','apps/web/components','apps/web/lib'])walkDir(path.join(root,dir));
console.log(JSON.stringify({changed,remaining}));
if(!process.argv.includes('--write')&&changed)process.exitCode=1;
