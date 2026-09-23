"use client";
import {useEffect,useState} from "react";
import {useRouter} from "next/navigation";
import Shell from "@/components/Shell";
import {api} from "@/lib/api";
import {useSession} from "@/lib/store";
import {openCheckout} from "@/lib/toss";
export default function FortuneStore(){
 const s=useSession(); const router=useRouter(); const [data,setData]=useState<any>(); const [busy,setBusy]=useState<string|null>(null); const [msg,setMsg]=useState<string>();
 useEffect(()=>{api.fortuneProducts().then(setData).catch(e=>setMsg(e.message))},[]);
 async function buy(p:any){
  if(!s.chartId){router.push('/?step=a1');return;} setBusy(p.id); setMsg(undefined);
  try{const o=await api.payPrepare({session_id:s.sessionId,chart_id:s.chartId,lens_id:s.cur,tier:'one',concern:s.concern,product_id:p.id});
   if(!o.enabled||!o.client_key) throw new Error('현재 결제 설정을 확인하는 중입니다.');
   await openCheckout({clientKey:o.client_key,orderId:o.order_id,amount:o.amount,orderName:p.name,customerKey:o.customer_key});
  }catch(e:any){setMsg(e.message||'결제를 완료하지 못했습니다.')}finally{setBusy(null)}
 }
 return <Shell title="추가 해석 상점"><main className="fortune-store"><p className="eyebrow">결제 후 바로 열리는 실제 분석</p><h1>지금 가장 궁금한 한 가지를 고르세요</h1><p className="store-lead">대운·세운·월운·궁합·신살·택일을 각각 독립된 보고서로 계산합니다. 가격은 서버에서 검증됩니다.</p>{msg&&<p className="conversion-note" role="status">{msg}</p>}<div className="fortune-products">{data?.products?.map((p:any)=><article key={p.id} className="fortune-product"><div><h2>{p.name}</h2><p>{p.summary}</p><strong>{p.price.toLocaleString()}원</strong></div><button className="btn" disabled={!!busy} onClick={()=>buy(p)}>{busy===p.id?'결제창 여는 중':'이 내용 열기'}</button></article>)}</div>{!data&& !msg&&<p>상품을 불러오는 중입니다…</p>}</main></Shell>
}
