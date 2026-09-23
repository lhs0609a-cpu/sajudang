"use client";
import {useEffect,useState} from 'react';
import Link from 'next/link';
import {useRouter} from 'next/navigation';
import Shell from '@/components/Shell';
import PracticeCard from '@/components/PracticeCard';
import {ReadingSpeaker} from '@/components/ReadingVoice';
import {selectSavedReading} from '@/components/MemberLibrary';
import {memberCall,downloadReading,useMember} from '@/lib/member';
export default function SavedReading({params}:{params:{id:string}}){
  const {user,ready}=useMember(),router=useRouter();const [row,setRow]=useState<any>(null),[error,setError]=useState('');
  useEffect(()=>{setRow(null);if(user)memberCall('/reading/'+encodeURIComponent(params.id)).then(setRow).catch(e=>setError(e.message));},[params.id,user?.id]);
  return <Shell screen="f2" title="보관한 풀이"><Link className="btn gh" href="/me">내 보관함으로</Link>
    {ready&&!user?<Link className="btn" href={'/me?returnTo='+encodeURIComponent('/library/'+params.id)}>로그인하고 풀이 열기</Link>:row?<>
      <h1>{row.name||'나'}의 사주 · {row.lens_name}</h1><p>{row.birth.year}.{row.birth.month}.{row.birth.day} · {row.axis4||'MBTI 미선택'}</p><p className="sm">보관한 기본 풀이입니다. 추가 상대방 정보와 일회성 상담 답변은 포함하지 않습니다. 환불·이용 기간 만료 시 현재 열람 가능한 범위를 표시합니다.</p>
      <button className="btn" onClick={()=>downloadReading(row.id).catch(e=>setError(e.message))}>풀이 다운로드 · 인쇄/PDF</button>
      {row.report.cuts.map((cut:any)=><section className="conversion-card" key={cut.id}><ReadingSpeaker lensId={row.lens_id} label={cut.title}/><h2>{cut.title}</h2><div dangerouslySetInnerHTML={{__html:cut.html}}/><p className="src">{cut.source}</p></section>)}
      {row.report.practice&&<PracticeCard practice={row.report.practice} lensId={row.lens_id}/>}
      <button className="btn" onClick={async()=>{try{await selectSavedReading(row);router.push('/lobby?tab=b2');}catch(e){setError((e as Error).message);}}}>이 사주로 20자리 둘러보기</button>
      <button className="btn gh" onClick={async()=>{if(!window.confirm('이 풀이를 보관함에서 삭제할까요? 구매 권한은 유지됩니다.'))return;try{await memberCall('/reading/'+row.id,undefined,'DELETE');router.push('/me');}catch(e){setError((e as Error).message);}}}>이 풀이 보관 삭제</button>
    </>:!error&&<p>보관한 풀이를 불러오고 있습니다.</p>}
    {error&&<p role="alert">{error}</p>}
  </Shell>;
}
