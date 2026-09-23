import profiles from './character-profiles.json';
import { youOf } from './lenses';
export type Voice = 'hao'|'hapsyo'|'hage'|'banmal'|'haeyo';
const base=0xac00, last=0xd7a3;
const jong=(s:string)=>{const n=s.charCodeAt(s.length-1);return n>=base&&n<=last?(n-base)%28:null;};
const jung=(s:string)=>Math.floor((s.charCodeAt(s.length-1)-base)/28)%21;
const bright=(s:string)=>[0,2,8,12].includes(jung(s));
const noun:Record<string,string>={hapsyo:'입니다',hage:'네',banmal:'지',haeyo:'예요'};
function ae(stem:string){const j=jong(stem);return j===null||j===0||[7,17,19,27].includes(j)?null:j===20?'어':bright(stem)?'아':'어';}
function imperative(stem:string,tone:Voice):string{
  if(tone==='hapsyo')return stem+'십시오';
  if(tone==='haeyo')return stem+'세요';
  let bare=stem,eu=false;
  if(bare.endsWith('으')&&bare.length>=2&&jong(bare.slice(0,-1))){bare=bare.slice(0,-1);eu=true;}
  if(tone==='hage'){
    const back:Record<string,string>={물:'묻',들:'듣',실:'싣',걸:'걷'};
    if(eu&&back[bare])return back[bare]+'게';
    if(bare==='마')return '말게';
    return bare.endsWith('드')&&!eu?bare.slice(0,-1)+'들게':bare+'게';
  }
  const tail=bare.slice(-1), head=bare.slice(0,-1), contract:Record<string,string>={하:'해',되:'돼',마:'마',오:'와'};
  if(contract[tail])return head+contract[tail];
  if(bare.length>=2&&tail==='르'&&jong(head)===0)return head.slice(0,-1)+String.fromCharCode(head.charCodeAt(head.length-1)+8)+(bright(head)?'라':'러');
  if(tail==='드'&&!eu)return head+'들어';
  if(eu&&jong(bare))return bare+(jong(bare)===20?'어':bright(bare)?'아':'어');
  const add=ae(bare);if(add)return bare+add;
  if(jong(bare)!==0)return bare+'지';
  const j=jung(bare), cho=Math.floor((tail.charCodeAt(0)-base)/(28*21));
  const changed:Record<number,number>={8:9,13:14,20:6,18:4};
  return changed[j]!==undefined?head+String.fromCharCode(base+(cho*21+changed[j])*28):bare;
}
const keepYo=/(네요|세요|예요|에요|아요|어요|여요|워요|와요|해요|돼요|봐요|줘요|래요|켜요|쳐요|펴요|러요|지요|든요|게요|나요|려요|겨요|죠)$/;
export function voiceWord(word:string,tone:Voice,ask=false):string{
  if(tone==='hao'||!word)return word;
  if(word.endsWith('십시오'))return word;
  if(word==='요')return noun[tone];
  if(word.endsWith('시오'))return imperative(word.slice(0,-2),tone);
  if(word.endsWith('요')){
    if(keepYo.test(word)&&!/[0-9]세요$/.test(word))return word;
    const n=word.slice(0,-1);return n&&!jong(n)?n+noun[tone]:word;
  }
  const end=word.slice(-1),stem=word.slice(0,-1),j=jong(stem);
  if(!stem||!['오','소'].includes(end)||j===null||(end==='소')!==(j!==0))return word;
  const dropped=j===8?stem.slice(0,-1)+String.fromCharCode(stem.charCodeAt(stem.length-1)-8):null;
  if(tone==='hapsyo'){
    const s=dropped??stem;
    return jong(s)?s+(ask?'습니까':'습니다'):s.slice(0,-1)+String.fromCharCode(s.charCodeAt(s.length-1)+17)+(ask?'니까':'니다');
  }
  if(tone==='hage')return (dropped??stem)+(ask?'나':'네');
  if(ask)return stem+(tone==='haeyo'?'나요':'지');
  if(stem.length>=2&&stem.endsWith('이')&&jong(stem.slice(0,-1)))return stem.slice(0,-1)+(tone==='haeyo'?'이에요':'이야');
  if(stem.endsWith('하')||stem.endsWith('되'))return stem.slice(0,-1)+(stem.endsWith('하')?'해':'돼')+(tone==='haeyo'?'요':'');
  const add=ae(stem);return stem+(add?add+(tone==='haeyo'?'요':''):tone==='haeyo'?'네요':'지');
}
export function characterText(text:string,lensId:string,name='',sex?:'M'|'F'|null):string{
  const tone=(profiles[lensId as keyof typeof profiles]?.voice??'hao') as Voice;
  const you=youOf(lensId,name,sex);
  // Tags, URLs and explicitly quoted example dialogue retain their original meaning.
  return text.split(/(<[^>]*>|https?:\/\/[^\s<]+|“[^”]*”|「[^」]*」|『[^』]*』)/g).map(part=>{
    if(/^(<|https?:\/\/|“|「|『)/.test(part))return part;
    const addressed=you==='그대'?part:part.replace(/그대(?!로)([가는를와라]|요(?=[.!?…\s<]|$))?/g,(_,josa='')=>{
      if(you==='너'&&josa==='가')return '네가';
      const particles:Record<string,string>={가:'이',는:'은',를:'을',와:'과',라:'이라',요:'이오'};
      return you+(jong(you)&&particles[josa]?particles[josa]:josa);
    });
    return addressed.replace(/([^\s.!?…—–〔,]+)(?=\s*(?:([.!?…])|[—–,]|〔|$))/g,(_,w,p)=>voiceWord(w,tone,p==='?'));
  }).join('');
}
