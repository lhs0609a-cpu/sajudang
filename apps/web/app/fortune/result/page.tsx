"use client";
import {useEffect,useState} from "react";
import {useSearchParams} from "next/navigation";
import Shell from "@/components/Shell";
import {api} from "@/lib/api";
import {useSession} from "@/lib/store";
export default function FortuneResult(){const q=useSearchParams();const s=useSession();const [r,setR]=useState<any>();const [err,setErr]=useState<string>();const product=q.get("product")||"annual_flow";useEffect(()=>{if(!s.chartId)return;api.fortuneCalculate({session_id:s.sessionId,chart_id:s.chartId,product_id:product,year:new Date().getFullYear()}).then(setR).catch(e=>setErr(e.message))},[s.chartId,s.sessionId,product]);return <Shell title="상세 분석 결과"><main className="fortune-store"><p className="eyebrow">결제 권한 확인 후 열리는 원문</p>{err?<p className="warn">{err}</p>:!r?<p>결제 권한과 명식을 확인하는 중입니다…</p>:<><h1>{r.title}</h1><p className="store-lead">계산 근거를 숨기지 않고, 지금 행동으로 옮길 수 있는 문장으로 정리했습니다.</p><div className="fortune-result-list">{(r.rows||[]).map((x:any,i:number)=><article key={i}><h2>{x.year??x.age??x.month??x.name??x.axis??x.date}</h2><p>{x.reading||x.focus||x.signal||x.verdict}</p><small>{x.action||x.reason||x.target||"명식 계산 결과"}</small></article>)}</div></>}</main></Shell>}
