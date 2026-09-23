'use client';
import {useEffect,useState} from 'react';
import Link from 'next/link';
export default function InvitationArrival(){
  const [arrived,setArrived]=useState(false);
  useEffect(()=>{const q=new URLSearchParams(location.search),code=q.get('invite'),relation=q.get('with');if(code&&/^[A-Za-z0-9_-]{20,64}$/.test(code)){try{localStorage.setItem('sd.invite',code);if(relation&&/^(lover|family|relative|friend|coworker|other)$/.test(relation))localStorage.setItem('sd.invite.relation',relation);setArrived(true);}catch{}}},[]);
  if(!arrived)return null;
  return <div className="invitation-arrival" role="status">소중한 사람이 함께 보자고 했어요. 먼저 내 무료 풀이를 확인해 보세요. <Link href="/">내 풀이 시작하기 →</Link><button aria-label="함께 보기 안내 닫기" onClick={()=>setArrived(false)}>×</button></div>;
}
