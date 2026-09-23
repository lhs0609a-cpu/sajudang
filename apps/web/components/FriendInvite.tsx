'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useMember } from '@/lib/member';

type Credit = {percent:number; expires_at:number; status:string};
type Relation = 'lover'|'family'|'relative'|'friend'|'coworker'|'other';
type Comparison = {id:string;relation:Relation;relation_label:string;status:'waiting'|'ready';shared?:string;difference?:string;watch?:string;action?:string};
const RELATIONS: {id:Relation;label:string}[] = [
  {id:'lover',label:'연인'},{id:'family',label:'가족'},{id:'relative',label:'친지'},
  {id:'friend',label:'친구'},{id:'coworker',label:'동료'},{id:'other',label:'그 밖의 소중한 사람'},
];
async function call(path:string, body:unknown={}) {
  const r = await fetch('/api/backend/v1/referral/'+path, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const data=await r.json(); if (!r.ok) throw new Error(data.detail||'초대 혜택을 확인하지 못했습니다.'); return data;
}

export default function FriendInvite() {
  const {user,ready}=useMember();
  const [code,setCode]=useState(''),[incoming,setIncoming]=useState(''),[relation,setRelation]=useState<Relation>('friend'),[credit,setCredit]=useState<Credit|null>(null),[comparisons,setComparisons]=useState<Comparison[]>([]),[message,setMessage]=useState(''),[busy,setBusy]=useState(false);
  useEffect(()=>{try {const q=new URLSearchParams(location.search),ref=q.get('invite'),withWhom=q.get('with') as Relation|null;if(ref&&/^[A-Za-z0-9_-]{20,64}$/.test(ref)){localStorage.setItem('sd.invite',ref);if(RELATIONS.some(r=>r.id===withWhom))localStorage.setItem('sd.invite.relation',withWhom!);}setIncoming(localStorage.getItem('sd.invite')||'');const saved=localStorage.getItem('sd.invite.relation') as Relation|null;if(RELATIONS.some(r=>r.id===saved))setRelation(saved!);}catch{}},[]);
  useEffect(()=>{let active=true;setCode('');setCredit(null);const load=()=>{if(user)call('invite').then(data=>{if(active){setCode(data.code);setCredit(data.credit);setComparisons(data.comparisons||[]);}}).catch(()=>{});};load();window.addEventListener('sd:reading-saved',load);return()=>{active=false;window.removeEventListener('sd:reading-saved',load);};},[user?.id]);
  async function run(fn:()=>Promise<void>) {setBusy(true);setMessage('');try{await fn();}catch(e){setMessage((e as Error).message);}finally{setBusy(false);}}
  const share=()=>run(async()=>{
    const url=new URL('/',location.origin);url.searchParams.set('invite',code);url.searchParams.set('with',relation);
    const label=RELATIONS.find(r=>r.id===relation)?.label||'소중한 사람';
    if(navigator.share){try{await navigator.share({title:'성신당 — 우리 둘 함께 보기',text:`${label} 관계인 우리, 사주에서는 무엇이 닮고 다를까? 내 결과를 보고 네 풀이도 이어서 확인해 봐.`,url:url.href});}catch(e){if((e as Error).name==='AbortError')return;throw e;}}
    else {await navigator.clipboard.writeText(url.href);setMessage('함께 보기 링크를 복사했습니다. 원하는 사람에게 보내 주세요.');}
  });
  if(!ready)return null;
  return <section className="conversion-card friend-invite" aria-label="소중한 사람과 함께 보기">
    <p className="conversion-kicker">혼자 읽은 나를, 함께 있을 때의 우리로</p>
    <h2>{incoming?'소중한 사람이 함께 보자고 했어요':'연인·가족·친지와 우리 둘 함께 보기'}</h2>
    <p>링크를 받은 사람이 자기 무료 풀이를 보관하면, 생년월일은 서로 공개하지 않고 두 사람의 닮은 점·다른 점·조심할 지점을 함께 보여드립니다.</p>
    <p className="sm">연인, 가족, 친지, 친구, 동료 누구에게나 보낼 수 있습니다. 두 사람 모두 동의해 연결한 경우에만 비교 결과가 열립니다.</p>
    {credit&&<p role="status">{credit.status==='ready'?`초대 ${credit.percent}% 할인 사용 가능 · ${new Date(credit.expires_at*1000).toLocaleDateString('ko-KR')}까지`:credit.status==='reserved'?'결제하려던 주문에 할인이 적용되어 있습니다. 같은 상품에서 결제를 이어가세요.':credit.status==='used'?'초대 할인을 사용했습니다.':'초대 할인 기간이 종료되었습니다.'}</p>}
    {comparisons.map(row=><article key={row.id} className="together-result">
      <p className="conversion-kicker">{row.relation_label} · 함께 보기</p>
      {row.status==='waiting'?<p>상대의 기본 풀이가 보관되면 비교 결과가 이곳에 열립니다.</p>:<><h3>우리 둘의 공통점과 차이</h3><p><b>닮은 점</b><br/>{row.shared}</p><p><b>다른 점</b><br/>{row.difference}</p><p><b>조심할 점</b><br/>{row.watch}</p><p><b>지금 해볼 일</b><br/>{row.action}</p></>}
    </article>)}
    {!user?<Link className="btn" href="/me">{incoming?'내 풀이를 보관하고 함께 보기':'로그인하고 함께 보기 링크 만들기'}</Link>:<>
      {incoming&&incoming!==code&&<button className="btn" disabled={busy} onClick={()=>run(async()=>{const data=await call('claim',{code:incoming,relation});setCredit(data.credit);setComparisons(data.comparisons||[]);localStorage.removeItem('sd.invite');localStorage.removeItem('sd.invite.relation');setIncoming('');setMessage('두 사람을 연결했습니다. 각자의 풀이가 보관되면 비교 결과가 열립니다.');})}>동의하고 우리 둘 연결하기</button>}
      {!incoming&&<label>누구와 함께 볼까요?<select value={relation} onChange={e=>setRelation(e.target.value as Relation)}>{RELATIONS.map(r=><option key={r.id} value={r.id}>{r.label}</option>)}</select></label>}
      <button className="btn gh" disabled={busy||!code} onClick={share}>{busy?'확인 중…':'함께 보기 링크 보내기'}</button>
    </>}
    {message&&<p role="status">{message}</p>}
  </section>;
}
