"use client";
import {useCallback,useEffect,useState} from 'react';
import {API_BASE} from '@/lib/api';
type Order={order_id:string;amount:number;tier:string;status:string;opened_at:string|null;review_status:string|null;review_note:string|null;reissued_from?:string|null};
export default function RefundHistory({sessionId}:{sessionId:string}){
  const [orders,setOrders]=useState<Order[]>([]),[message,setMessage]=useState('');
  const [selected,setSelected]=useState<string|null>(null),[reason,setReason]=useState(''),[busy,setBusy]=useState(false);
  const [loading,setLoading]=useState(true),[loadError,setLoadError]=useState('');
  const load=useCallback(async(signal?:AbortSignal)=>{
    setLoading(true);setLoadError('');
    try{
      const r=await fetch(`${API_BASE}/v1/pay/history?session_id=${encodeURIComponent(sessionId)}`,{signal});
      if(!r.ok)throw Error('history unavailable');
      const data=await r.json();if(!Array.isArray(data.orders))throw Error('invalid history');
      if(!signal?.aborted)setOrders(data.orders);
    }catch{if(!signal?.aborted)setLoadError('구매 내역을 확인하지 못했소. 구매가 없다는 뜻은 아니오. 잠시 후 다시 확인해 주시오.');}
    finally{if(!signal?.aborted)setLoading(false);}
  },[sessionId]);
  useEffect(()=>{const controller=new AbortController();setOrders([]);if(sessionId)void load(controller.signal);return()=>controller.abort();},[sessionId,load]);
  const request=async(o:Order)=>{
    setBusy(true);setMessage('');
    try{
      const r=await fetch(`${API_BASE}/v1/pay/refund`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sessionId,order_id:o.order_id,reason,calc_error:!!o.opened_at})});
      const data=await r.json();if(!r.ok)throw Error(data.detail||'환불 요청을 처리하지 못했소.');
      setMessage(data.status==='review_requested'?'계산 오류 확인 요청을 접수했소. 처리 상태는 이곳에서 확인할 수 있소.':data.reissue?'전액 환불하고 추가 결제 없이 리포트를 재발행했소. 기존 리포트에서 다시 읽을 수 있소.':'전액 환불 처리됐소. 카드사 반영까지 시간이 걸릴 수 있소.');
      setSelected(null);setReason('');await load();
    }catch(e){setMessage(e instanceof Error?e.message:'요청 실패');}finally{setBusy(false);}
  };
  return <section className="conversion-card"><h2>구매 내역과 환불</h2>
    {loading&&<p role="status">구매 내역을 확인하고 있소…</p>}
    {loadError&&<div role="alert"><p>{loadError}</p><button className="btn gh" disabled={loading} onClick={()=>void load()}>구매 내역 다시 확인하기</button></div>}
    {!loading&&!loadError&&!orders.length&&<p className="conversion-note">아직 구매 내역이 없소. 다른 기기의 구매는 주문번호로 복원할 수 있소.</p>}
    {orders.map(o=><div key={o.order_id} className="conversion-card">
      <p>{o.amount.toLocaleString()}원 · {o.status==='paid'?'구매 완료':o.status==='refunded'?'환불 완료':o.status==='canceled'?'취소 완료':'확인 중'}</p>
      {o.reissued_from&&<p>계산 오류 확인 후 추가 결제 없이 재발행한 리포트이오.</p>}
      <p className="conversion-note" style={{overflowWrap:'anywhere'}}>주문번호 {o.order_id}</p>
      {o.review_status&&<p>계산 오류 확인: {o.review_status==='pending'?'접수됨':o.review_status==='approved'?'환불 처리':'확인 완료 · 승인되지 않음'}</p>}
      {o.review_note&&<p className="conversion-note">검토 결과: {o.review_note}</p>}
      {o.status==='paid'&&!o.reissued_from&&o.review_status!=='pending'&&<button className="btn gh" onClick={()=>{setSelected(o.order_id);setReason('');}}>{o.opened_at?'계산 오류 확인 요청':'열람 전 전액 환불'}</button>}
      {selected===o.order_id&&<><label htmlFor="refund-reason">{o.opened_at?'틀렸다고 생각하는 계산과 비교 근거':'환불 사유'}</label>
        <textarea id="refund-reason" className="fld" maxLength={200} value={reason} onChange={e=>setReason(e.target.value)}/>
        {o.tier==='sub'&&<p className="conversion-note">현재 이용 중인 구독 기간을 환불하면 이용과 자동결제가 함께 종료되오.</p>}
        <p className="conversion-note">{o.opened_at?'열람 후에는 계산 오류를 확인한 뒤 전액 환불하오. 이 버튼만으로 자동 환불되지 않소.':`${o.amount.toLocaleString()}원 전액을 원래 결제수단으로 돌려드리고, 해당 구매의 열람 권한은 종료되오.`}</p>
        <button className="btn" disabled={busy||reason.trim().length<2} onClick={()=>void request(o)}>{busy?'처리 중…':o.opened_at?'확인 요청 접수하기':`${o.amount.toLocaleString()}원 전액 환불 요청`}</button>
        <button className="btn gh" disabled={busy} onClick={()=>setSelected(null)}>닫기</button></>}
    </div>)}
    {message&&<p role="status">{message}</p>}
  </section>;
}
