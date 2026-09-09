"use client";
import Link from "next/link";
import Shell from "@/components/Shell";
import CompanionCat from "@/components/CompanionCat";

export default function ErrorPage({reset}:{error:Error & {digest?:string};reset:()=>void}){
  return <Shell title="다시 펼치는 이야기"><header className="editorial-heading"><p className="conversion-kicker">페이지를 열지 못했소</p><h1>잠시 책장이<br/>걸린 모양이오.</h1><p>페이지를 다시 열어보시오. 결제 중이었다면 구매 내역에서 승인 여부를 먼저 확인해 주시오.</p></header><CompanionCat message="괜찮다냥. 잠깐 쉬고 다시 펼쳐보자!"/><button className="btn mt" onClick={reset}>페이지 다시 열기</button><Link className="btn gh" href="/me">구매 내역 확인하기</Link></Shell>;
}
