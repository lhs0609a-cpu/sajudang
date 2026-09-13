"use client";
import { useEffect, useState } from 'react';
import type { IntegratedReading } from '@shared/chart';

type Practice = NonNullable<IntegratedReading['practice']>;
const KEY='sd.reading-practice';
type Saved={id:string; when:string; action:string; observe:string; expires:number};
function savedRows(): Saved[] {
  try {
    const raw=JSON.parse(localStorage.getItem(KEY)||'[]');
    return Array.isArray(raw) ? raw.filter((r:Saved)=>typeof r.id==='string' && r.expires>Date.now()).slice(-20) : [];
  } catch { return []; }
}

export default function ReadingPractice({practice, id}: {practice:Practice; id:string}) {
  const [when,setWhen]=useState(practice.trigger);
  const [action,setAction]=useState(practice.action);
  const [message,setMessage]=useState('');
  useEffect(()=>{
    const rows=savedRows(), row=rows.find(r=>r.id===id);
    if(row){setWhen(row.when);setAction(row.action);setMessage('이 브라우저에 남겨 둔 행동입니다.');}
    try {localStorage.setItem(KEY,JSON.stringify(rows));} catch { /* Saving remains optional. */ }
  },[id]);
  return <section className="reading-practice reading-plan-section" aria-label="오늘의 실행 카드">
    <h2>읽은 뒤 남길 한 가지</h2>
    <label>언제 해볼까요?<input maxLength={160} value={when} onChange={e=>setWhen(e.target.value)}/></label>
    <label>그때 해볼 일<textarea maxLength={320} rows={3} value={action} onChange={e=>setAction(e.target.value)}/></label>
    <p><strong>해본 뒤 확인할 것</strong><br/>{practice.observe}</p>
    <details><summary>지금 하기 어렵다면</summary><p>{practice.fallback}</p></details>
    <p className="sm">원하는 말로 고쳐도 됩니다. 저장을 누르면 이 브라우저에만 30일간 남고 서버로 보내지 않습니다. 브라우저 데이터를 지우면 사라집니다.</p>
    <div className="reading-practice-actions noprint">
      <button className="btn gh" disabled={!when.trim()||!action.trim()} onClick={()=>{
        try {const rows=savedRows().filter(r=>r.id!==id);rows.push({id,when,action,observe:practice.observe,expires:Date.now()+30*86400000});
          localStorage.setItem(KEY,JSON.stringify(rows.slice(-20)));setMessage('이 브라우저에 30일간 저장했습니다.');
        } catch {setMessage('저장할 수 없습니다. 내용을 복사해 보관해 주세요.');}
      }}>이 브라우저에 저장</button>
      <button className="btn gh" onClick={async()=>{
        try {await navigator.clipboard.writeText(`${when}\n${action}\n확인할 것: ${practice.observe}`);setMessage('실행 카드를 복사했습니다.');}
        catch {setMessage('복사하지 못했습니다. 입력칸의 글을 직접 선택해 복사해 주세요.');}
      }}>실행 카드 복사</button>
      <button className="btn gh" onClick={()=>{
        try {localStorage.setItem(KEY,JSON.stringify(savedRows().filter(r=>r.id!==id)));setWhen(practice.trigger);setAction(practice.action);setMessage('저장한 행동을 지웠습니다.');}
        catch {setMessage('지우지 못했습니다. 브라우저 설정에서 사이트 데이터를 삭제할 수 있습니다.');}
      }}>저장한 행동 지우기</button>
    </div>
    <p role="status">{message}</p>
  </section>;
}
