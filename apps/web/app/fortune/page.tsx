"use client";
import {useEffect,useState} from "react";
import {useRouter} from "next/navigation";
import Shell from "@/components/Shell";
import {api} from "@/lib/api";
import {useSession} from "@/lib/store";
import {openCheckout} from "@/lib/toss";
import {ArtImage, type ReadingArt, ScreenReadingGuide} from "@/components/ReadingArtwork";

type Offer={id:string;name:string;price:number;summary?:string;includes?:string[]};
const PRODUCT_ART: Record<string, ReadingArt> = {
 daeun_deep:"daily", annual_flow:"daily", monthly_calendar:"time", sinsal_detail:"fire",
 compatibility:"archive", couple_compatibility:"archive", taekil:"birth",
 time_bundle:"daily", relationship_bundle:"archive", all_bundle:"archive",
};
export default function FortuneStore(){
 const s=useSession(); const router=useRouter(); const [data,setData]=useState<{products:Offer[];bundles:Offer[]}>({products:[],bundles:[]}); const [busy,setBusy]=useState<string|null>(null); const [msg,setMsg]=useState<string>();
 useEffect(()=>{api.fortuneProducts().then(setData).catch(e=>setMsg(e.message))},[]);
 async function buy(p:Offer){
  if(!s.chartId){router.push('/?step=a1');return;} setBusy(p.id); setMsg(undefined);
  try{const o=await api.payPrepare({session_id:s.sessionId,chart_id:s.chartId,lens_id:s.cur,tier:'one',concern:s.concern,product_id:p.id});
   if(!o.enabled||!o.client_key) throw new Error('현재 결제 준비가 끝나지 않았소. 잠시 뒤 다시 시도해 주시오.');
   await openCheckout({clientKey:o.client_key,orderId:o.order_id,amount:o.amount,orderName:p.name,customerKey:o.customer_key});
  }catch(e:any){setMsg(e.message||'결제를 시작하지 못했소.')}finally{setBusy(null)}
 }
 const card=(p:Offer)=><article key={p.id} className="fortune-product"><ArtImage art={PRODUCT_ART[p.id] ?? "archive"} className="fortune-product-art" /><div className="fortune-product-copy"><p className="fortune-product-kicker">{p.includes ? "묶음 분석" : "단일 분석"}</p><h2>{p.name}</h2><p>{p.summary||`${p.includes?.length||0}개 분석을 한 번에 엽니다.`}</p><strong>{p.price.toLocaleString()}원</strong></div><div className="fortune-product-actions"><button className="btn" disabled={!!busy} onClick={()=>buy(p)}>{busy===p.id?'결제창 여는 중':'이 내용 열기'}</button>{!p.includes&&<button className="btn gh" onClick={()=>router.push(`/fortune/result?product=${p.id}`)}>결과 보기</button>}</div></article>;
 return <Shell screen="c4" title="추가 해석 상점"><main className="fortune-store"><ScreenReadingGuide screen="c4" /><p className="eyebrow">결제 후 바로 열리는 실제 분석</p><h1>지금 가장 궁금한 한 가지를 고르세요</h1><p className="store-lead">대운·세운·월운·궁합·신살·택일을 각각 독립된 보고서로 계산합니다. 결제 금액과 열람 범위는 서버에서 다시 확인합니다.</p>{msg&&<p className="conversion-note" role="status">{msg}</p>}<section><h2>개별 분석</h2><div className="fortune-products">{data.products.map(card)}</div></section><section><h2>패키지</h2><div className="fortune-products">{data.bundles.map(card)}</div></section>{!data.products.length&&!msg&&<p>상품을 불러오는 중입니다…</p>}</main></Shell>
}
