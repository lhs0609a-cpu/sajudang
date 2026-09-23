'use client';
import { useEffect, useState } from 'react';
export type Promotion = {percent:number; ends_at:string; server_now:string};
export default function PromotionNote({value}:{value:Promotion|null|undefined}) {
  const [seconds,setSeconds]=useState(0);
  useEffect(()=>{
    if(!value){setSeconds(0);return;}
    const remaining=Date.parse(value.ends_at)-Date.parse(value.server_now),start=performance.now();
    const update=()=>setSeconds(Math.max(0,Math.floor((remaining-(performance.now()-start))/1000)));
    update();const timer=setInterval(update,1000);return()=>clearInterval(timer);
  },[value?.ends_at,value?.server_now]);
  if(!value)return null;
  return <p className="conversion-note">{seconds>0?`${value.percent}% 기간 할인 · ${Math.floor(seconds/3600)}시간 ${Math.floor(seconds%3600/60)}분 ${seconds%60}초 남음`:'기간 할인이 종료되었습니다. 새 주문에는 현재 가격이 적용됩니다.'}<br/>{new Date(value.ends_at).toLocaleString('ko-KR',{timeZone:'Asia/Seoul'})} (한국 시간) 마감 · 이미 만든 주문은 결제 버튼의 금액을 따릅니다.</p>;
}
