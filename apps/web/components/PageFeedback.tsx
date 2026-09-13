"use client";
import { useState } from 'react';
import { usePathname } from 'next/navigation';
import { api } from '@/lib/api';
import { useSession } from '@/lib/store';

export default function PageFeedback({screen}: {screen?:string}) {
  const path=usePathname();
  const session=useSession();
  const [ease,setEase]=useState<number|null>(null);
  const [success,setSuccess]=useState<'yes'|'partly'|'no'|null>(null);
  const [state,setState]=useState<'idle'|'sending'|'done'>('idle');
  const [error,setError]=useState('');
  if(path==='/admin')return null;
  const route=path.startsWith('/report/')?'/report/[id]':path.startsWith('/s/')?'/s/[token]':path;
  const pageId=screen||'route:'+route;
  return <details className="page-feedback noprint">
    <summary>이 화면 사용 의견 남기기 · 선택</summary>
    <p className="sm">하려던 일을 마친 뒤 알려주세요. 기본 선택은 없으며, 화면 종류와 평가만 90일간 보관합니다. 이름·생년월일·공유 주소는 보내지 않습니다.</p>
    {state==='done'?<p role="status">의견을 받았습니다. 이용하기 어려운 부분을 고치는 데 쓰겠습니다.</p>:<form onSubmit={async e=>{
      e.preventDefault();if(!ease||!success||state==='sending')return;
      setState('sending');setError('');
      try{await api.pageEvaluation({session_id:session.sessionId,page_id:pageId,ease,success});setState('done');}
      catch{setState('idle');setError('보내지 못했습니다. 답변은 남아 있으니 다시 시도해 주세요.');}
    }}>
      <fieldset disabled={state==='sending'}><legend>이 화면에서 하려던 일을 할 수 있었나요?</legend>
        <div className="reading-options">{([['yes','할 수 있었다'],['partly','일부만 할 수 있었다'],['no','할 수 없었다']] as const).map(([value,label])=><label key={value}>
          <input type="radio" name="page-success" checked={success===value} onChange={()=>setSuccess(value)}/>{label}</label>)}</div>
      </fieldset>
      <fieldset disabled={state==='sending'}><legend>그 일을 하기가 얼마나 쉬웠나요?</legend><p>1 매우 어려웠다 · 7 매우 쉬웠다</p>
        <div className="ease-options">{[1,2,3,4,5,6,7].map(value=><label key={value}><input type="radio" name="page-ease" checked={ease===value} onChange={()=>setEase(value)}/>{value}</label>)}</div>
      </fieldset>
      <button className="btn gh" disabled={!ease||!success||state==='sending'}>{state==='sending'?'보내는 중':'화면 평가 보내기'}</button>
      {error&&<p role="alert">{error}</p>}
    </form>}
  </details>;
}
