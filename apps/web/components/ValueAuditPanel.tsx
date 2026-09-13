"use client";
import {useEffect,useState} from 'react';
import {API_BASE} from '@/lib/api';
type Check={key:string;name:string;level:number;weight:number;evidence:string;fix:string|null;source:string};
type Row={id:string;title?:string;case?:string;score:number;before?:number;delta?:number;checks:Check[];
  sections?:{id:string;title:string;score:number;metric:string}[]};
type Response={audit:{available:boolean;stale?:boolean|null;note:string;at?:string;source_fingerprint?:string;
  coverage?:{routes:number;screens:number;results:number;note:string};pages?:Row[];results?:Row[];auxiliary_results?:Row[]};
  pages:{note:string;rows:{page_id:string;n:number;ease_mean:number;ease_score_100:number;sample_note:string}[]};
  readings:{results:{id:string;n:number;reader_score:number;value_n:number;value_mean_1_5:number|null;sample_note:string}[]}};

export default function ValueAuditPanel({adminKey,token}:{adminKey:string;token:string}) {
  const [data,setData]=useState<Response|null>(null),[error,setError]=useState('');
  const [tab,setTab]=useState<'pages'|'results'|'auxiliary_results'>('pages'),[query,setQuery]=useState(''),[low,setLow]=useState(false);
  const [limit,setLimit]=useState(30),[tick,setTick]=useState(0);
  useEffect(()=>{
    let alive=true;const controller=new AbortController();
    const headers:Record<string,string>={};if(adminKey)headers['x-funnel-key']=adminKey;if(token)headers['x-admin-token']=token;
    setError('');
    fetch(API_BASE+'/v1/admin/value-audit',{headers,signal:controller.signal}).then(r=>{if(!r.ok)throw new Error();return r.json();})
      .then(value=>{if(alive)setData(value);}).catch(()=>{if(alive)setError('평가표를 불러오지 못했습니다. 관리자 인증과 서버 연결을 확인해 주세요.');});
    return()=>{alive=false;controller.abort();};
  },[adminKey,token,tick]);
  const rows=(data?.audit[tab]||[]).filter(r=>(!low||r.score<80)&&`${r.id} ${r.title||''}`.includes(query));
  return <section className="conversion-card value-audit-panel">
    <h2>페이지·결과별 품질과 실제 사용자 평가</h2>
    <p>내부 점수와 실제 응답을 분리해 봅니다. 높은 내부 점수가 구매 만족도를 보장하지는 않습니다.</p>
    <button className="btn gh" onClick={()=>setTick(v=>v+1)}>최신 평가표와 응답 불러오기</button>
    {error&&<p role="alert">{error}</p>}
    {data&&<>
      <p>{data.audit.note}</p>
      {!data.audit.available?<p>생성된 검사표가 없습니다. 아직 점수를 표시할 수 없습니다.</p>:<>
        <p>검사 시각 {data.audit.at} · 코드 {data.audit.source_fingerprint}</p>
        {data.audit.stale&&<p role="alert">검사 뒤 코드가 바뀌었습니다. 아래는 이전 검사값이며 새 코드의 점수로 사용할 수 없습니다.</p>}
        <p>{data.audit.coverage?.note}</p>
        <div className="reading-controls"><button aria-pressed={tab==='pages'} onClick={()=>{setTab('pages');setLimit(30);}}>페이지 {data.audit.pages?.length}개</button>
          <button aria-pressed={tab==='results'} onClick={()=>{setTab('results');setLimit(30);}}>통합 결과 {data.audit.results?.length}개</button>
          <button aria-pressed={tab==='auxiliary_results'} onClick={()=>{setTab('auxiliary_results');setLimit(30);}}>대화·일진·분석지 {data.audit.auxiliary_results?.length||0}개</button></div>
        <label>대상 검색<input value={query} onChange={e=>{setQuery(e.target.value);setLimit(30);}} placeholder="화면 이름, R01, money, pungun"/></label>
        <label><input type="checkbox" checked={low} onChange={e=>{setLow(e.target.checked);setLimit(30);}}/>80점 미만만 보기</label>
        <p>{rows.length}개 중 {Math.min(limit,rows.length)}개 표시 · 모든 점수는 내부 검사값</p>
        {rows.slice(0,limit).map(r=><details key={r.id}><summary>{r.title||r.id} · {r.before??'—'} → {r.score}점</summary>
          <p>{r.id} · 실제 사용자 평점은 아래 응답 영역에서 별도 확인</p>
          <table className="tbl"><thead><tr><th>검사</th><th>충족</th><th>근거와 개선점</th></tr></thead><tbody>{r.checks.map(c=><tr key={c.key}>
            <td><a href={c.source} target="_blank" rel="noreferrer">{c.name}</a></td><td>{c.level}/2</td><td>{c.evidence}{c.fix&&<p>{c.fix}</p>}</td></tr>)}</tbody></table>
          {r.sections&&<details><summary>문단별 가독성 검사</summary>{r.sections.map(s=><p key={s.id}>{s.title} · {s.score}점 · {s.metric}</p>)}</details>}
        </details>)}
        {limit<rows.length&&<button className="btn gh" onClick={()=>setLimit(v=>v+30)}>30개 더 보기</button>}
      </>}
      <h3>실제 페이지 사용 의견</h3><p>{data.pages.note}</p>
      {!data.pages.rows.length?<p>아직 응답이 없어 실제 점수는 미측정입니다.</p>:data.pages.rows.map(r=><p key={r.page_id}>{r.page_id} · {r.n}명 · 쉬운 정도 {r.ease_mean}/7 ({r.ease_score_100}/100 환산) · {r.sample_note}</p>)}
      <h3>실제 결과별 독자 평가</h3><p>독자 지수는 이해·공감·위로·실행 답변을 동일 가중치로 환산한 자체 지수입니다. 가격 대비 평가는 실제 결제 권한이 확인된 응답만 집계합니다.</p>
      {!data.readings.results?.length?<p>아직 결과별 응답이 없어 실제 점수는 미측정입니다.</p>:data.readings.results.map(r=><details key={r.id}><summary>{r.id} · 응답 {r.n}건</summary>
        <p>독자 지수 {r.reader_score}/100 · 가격 대비 평가 {r.value_mean_1_5??'미측정'}/5 ({r.value_n}건)</p><p>{r.sample_note}</p></details>)}
    </>}
  </section>;
}
