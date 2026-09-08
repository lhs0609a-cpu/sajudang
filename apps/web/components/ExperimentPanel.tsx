"use client";
import { useEffect, useState } from 'react';
import { API_BASE } from '@/lib/api';
type Arm = {variant:number;mature_visitors:number;buyers:number;conversion:number|null;ci95:(number|null)[];gross:number;refunds:number;net:number;net_per_visitor:number|null};
type Result = {groups:Arm[];immature:number;note:string;sample_ratio_warning:boolean;performance:{metric:string;browsers:number;p75:number|null;good_threshold:number;unit:string}[]};
export default function ExperimentPanel({accessKey,token}:{accessKey:string;token:string}) {
  const [data,setData] = useState<Result|null>(null);
  const [error,setError] = useState('');
  useEffect(()=>{
    const controller = new AbortController();
    const load = async()=>{
      try {
        const headers:Record<string,string>={};
        if(accessKey)headers['x-funnel-key']=accessKey;
        if(token)headers['x-admin-token']=token;
        const r=await fetch(`${API_BASE}/v1/experiments`,{headers,signal:controller.signal});
        if(!r.ok)throw Error('실험 지표를 불러오지 못했어요.');
        setData(await r.json());setError('');
      } catch(e) {if(!controller.signal.aborted)setError(e instanceof Error?e.message:'조회 실패');}
    };
    void load();const timer=setInterval(()=>{if(!document.hidden)void load();},60000);
    return()=>{controller.abort();clearInterval(timer);};
  },[accessKey,token]);
  const percent=(x:number|null)=>x===null?'관찰 전':`${(100*x).toFixed(2)}%`;
  return <section><h2>첫 화면 A/B 실험 · 무료 가치 설명</h2>
    <p className="sm">익명 브라우저에 50:50 고정 배정합니다. 가격·상품·결제 조건은 동일합니다.</p>
    {error&&<p role="status">{error}</p>}
    {data&&<><div style={{overflowX:'auto'}}><table><thead><tr><th>군</th><th>7일 관찰 완료</th><th>구매자</th><th>전환율 / 95% 구간</th><th>매출</th><th>환불</th><th>순매출</th></tr></thead>
      <tbody>{data.groups.map(g=><tr key={g.variant}><td>{g.variant===0?'A · 첫 해석 무료':'B · 행동까지 무료'}</td><td>{g.mature_visitors}</td><td>{g.buyers}</td><td>{percent(g.conversion)} ({g.ci95.map(percent).join('–')})</td><td>{g.gross.toLocaleString()}원</td><td>{g.refunds.toLocaleString()}원</td><td>{g.net.toLocaleString()}원</td></tr>)}</tbody></table></div>
      <p className="sm">관찰 중 {data.immature}개 브라우저. {data.note} 순매출은 수수료·세금 차감 전이며 재구독 매출은 제외합니다.</p></>}
    {data?.sample_ratio_warning&&<p role="alert">실험 배정 비율이 예상과 다릅니다. 효과 비교 전에 수집 상태를 확인하세요.</p>}
    {data&&<><h3>첫 방문 실제 성능 · 최근 30일</h3><p className="sm">브라우저별 가장 큰 값의 75백분위수입니다. 관찰된 브라우저만 포함합니다.</p>
      <ul>{data.performance.map(p=><li key={p.metric}>{p.metric.replace('web_','').toUpperCase()} · {p.p75??'관찰 전'} {p.unit} · {p.browsers}개 브라우저 · 양호 기준 {p.good_threshold} 이하</li>)}</ul></>}
  </section>;
}
