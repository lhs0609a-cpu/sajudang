"use client";
import {Suspense,useEffect,useState} from "react";
import {useSearchParams} from "next/navigation";
import Shell from "@/components/Shell";
import {ArtImage} from "@/components/ReadingArtwork";
import {api} from "@/lib/api";
import {useSession} from "@/lib/store";
function FortuneResultInner(){
 const q=useSearchParams(); const s=useSession(); const [result,setResult]=useState<any>(); const [error,setError]=useState<string>(); const product=q.get("product")||"annual_flow";
 useEffect(()=>{if(!s.chartId)return; api.fortuneCalculate({session_id:s.sessionId,chart_id:s.chartId,product_id:product,year:new Date().getFullYear()}).then(setResult).catch(e=>setError(e.message))},[s.chartId,s.sessionId,product]);
 return (<Shell screen="d3" title="상세 분석 결과"><main className="fortune-store"><ArtImage art="archive" className="fortune-result-art" /><p className="eyebrow">결제한 분석 결과</p>{error?<p className="warn">{error}</p>:!result?<p>결과를 펼치는 중입니다…</p>:<><h1>{result.title}</h1><p className="store-lead">그대의 명식에서 계산한 결과입니다. 각 항목의 결론과 바로 해볼 행동을 함께 적었습니다.</p><div className="fortune-result-list">{(result.rows||[]).map((x:any,i:number)=><article key={i}><p className="fortune-result-index">{String(i+1).padStart(2,"0")}</p><h2>{x.year??x.age??x.month??x.name??x.axis??x.date}</h2><p>{x.reading||x.focus||x.signal||x.verdict}</p><small>{x.action||x.reason||x.target||"명식 계산 근거"}</small></article>)}</div></>}</main></Shell>);
}
export default function FortuneResult(){return <Suspense fallback={<Shell screen="d3" title="상세 분석 결과"><main className="fortune-store"><p>결과를 펼치는 중입니다…</p></main></Shell>}><FortuneResultInner/></Suspense>}
