"use client";
import {useEffect,useState} from 'react';
import {API_BASE} from '@/lib/api';
type Row={order_id:string;reason:string;requested_at:string;amount:number};
export default function RefundReviews({accessKey,token}:{accessKey:string;token:string}){
  const [rows,setRows]=useState<Row[]>([]),[notes,setNotes]=useState<Record<string,string>>({}),[message,setMessage]=useState(''),[busy,setBusy]=useState(false);
  const headers:Record<string,string>={'Content-Type':'application/json'};
  if(accessKey)headers['x-funnel-key']=accessKey;if(token)headers['x-admin-token']=token;
  const load=async()=>{const r=await fetch(`${API_BASE}/v1/admin/refund-reviews`,{headers});if(!r.ok)throw Error('환불 확인 요청을 조회하지 못했소.');setRows((await r.json()).requests);};
  useEffect(()=>{void load().catch(e=>setMessage(String(e)));},[accessKey,token]);
  const decide=async(order_id:string,approve:boolean)=>{
    setBusy(true);setMessage('');
    try{
      const r=await fetch(`${API_BASE}/v1/admin/refund-reviews`,{method:'POST',headers,body:JSON.stringify({order_id,approve,note:notes[order_id]||''})});
      const data=await r.json();if(!r.ok)throw Error(data.detail||'처리 실패');
      setNotes(n=>({...n,[order_id]:''}));setMessage(approve?'전액 환불 처리했소.':'검토 결과를 기록했소.');await load();
    }catch(e){setMessage(e instanceof Error?e.message:'처리 실패');}finally{setBusy(false);}
  };
  return <section><h2>계산 오류 환불 확인</h2><p className="sm">승인은 실제 전액 환불을 실행하오. 고객이 제시한 계산 근거를 확인한 뒤 처리하시오.</p>
    {rows.length===0&&<p>대기 중인 요청이 없소.</p>}
    {rows.map(r=><div className="conversion-card" key={r.order_id}><p style={{overflowWrap:'anywhere'}}>{r.order_id}</p><p>{r.reason}</p>
      <p>환불 금액 {r.amount.toLocaleString()}원</p>
      <label>검토 근거<textarea className="fld" value={notes[r.order_id]||''} onChange={e=>setNotes(n=>({...n,[r.order_id]:e.target.value}))} maxLength={300}/></label>
      <button className="btn" disabled={busy||(notes[r.order_id]||'').trim().length<5} onClick={()=>void decide(r.order_id,true)}>오류 확인 · 전액 환불 실행</button>
      <button className="btn gh" disabled={busy||(notes[r.order_id]||'').trim().length<5} onClick={()=>void decide(r.order_id,false)}>근거 기록 · 승인하지 않기</button>
    </div>)}{message&&<p role="status">{message}</p>}
  </section>;
}
