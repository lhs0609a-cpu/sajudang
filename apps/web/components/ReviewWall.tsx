"use client";
import {useEffect,useState} from "react";
import {api} from "@/lib/api";
export default function ReviewWall({lensId}:{lensId?:string}) {
  const [rows,setRows]=useState<{body:string;rating:number|null;verified:boolean}[]>([]);
  useEffect(()=>{let live=true; api.recentReviews(lensId).then(r=>{if(live)setRows(r.reviews)}).catch(()=>{}); return()=>{live=false}},[lensId]);
  if(!rows.length)return null;
  return <section className="review-wall" aria-label="먼저 읽어보는 이용자 후기">
    <p className="review-wall-kicker">결제 전에, 먼저 읽어보세요</p>
    <h3>사람들이 실제로 멈춰 읽은 문장</h3>
    <div className="review-wall-grid">{rows.slice(0,4).map((r,i)=><blockquote key={i}><div className="review-stars">{"★".repeat(Math.max(0,r.rating||5))}</div><p>“{r.body}”</p>{r.verified&&<small>구매 후 작성된 후기</small>}</blockquote>)}</div>
  </section>;
}
