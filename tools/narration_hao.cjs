// Audit/edit only the Narration component's literal lines; preserve code and comments.
const fs=require('node:fs'),path=require('node:path'),ts=require('typescript');
const root=path.resolve(__dirname,'..');let changed=[];
function hao(text){return text.replace(/입니다(?=[.!?])/g,'이오').replace(/이다(?=[.!?])/g,'이오').replace(/한다(?=[.!?])/g,'하오').replace(/된다(?=[.!?])/g,'되오').replace(/는다(?=[.!?])/g,'소').replace(/([가-힣])다(?=[.!?])/g,(_,c)=>{let n=c.charCodeAt(0)-0xac00;return n%28===4?String.fromCharCode(c.charCodeAt(0)-4)+'오':c+'소';});}
function file(p){const original=fs.readFileSync(p,'utf8'),sf=ts.createSourceFile(p,original,ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX),edits=[];
 function literals(n){if(ts.isStringLiteral(n)||ts.isNoSubstitutionTemplateLiteral(n)||[ts.SyntaxKind.TemplateHead,ts.SyntaxKind.TemplateMiddle,ts.SyntaxKind.TemplateTail].includes(n.kind)){const a=n.getStart(sf),b=n.end,t=original.slice(a,b),v=hao(t);if(v!==t)edits.push([a,b,v]);return;}ts.forEachChild(n,literals);}
 function walk(n){if((ts.isJsxSelfClosingElement(n)||ts.isJsxOpeningElement(n))&&n.tagName.getText(sf)==='Narration'){for(const attr of n.attributes.properties)if(ts.isJsxAttribute(attr)&&attr.name.getText(sf)==='lines')literals(attr);}ts.forEachChild(n,walk);}walk(sf);
 if(edits.length){let text=original;for(const[a,b,v]of edits.sort((x,y)=>y[0]-x[0]))text=text.slice(0,a)+v+text.slice(b);changed.push(path.relative(root,p));if(process.argv.includes('--write'))fs.writeFileSync(p,text);}}
function dir(d){for(const e of fs.readdirSync(d,{withFileTypes:true})){const p=path.join(d,e.name);if(e.isDirectory())dir(p);else if(p.endsWith('.tsx'))file(p);}}
dir(path.join(root,'apps/web/app'));console.log(JSON.stringify({changed}));if(changed.length&&!process.argv.includes('--write'))process.exitCode=1;
