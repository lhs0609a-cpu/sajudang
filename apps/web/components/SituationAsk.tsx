'use client';

import {useState} from 'react';
import type {TopicAskSpec} from './TopicAsk';

export default function SituationAsk({spec,current,onSubmit,busy}:{
  spec:TopicAskSpec;
  current?:{choice:string;choice2?:string;choice3?:string;choice4?:string;choice5?:string}|null;
  onSubmit:(topic:{choice:string;choice2?:string;choice3?:string;choice4?:string;choice5?:string})=>void;
  busy?:boolean;
}){
  const [pick,setPick]=useState(current?.choice??'');
  const [pick2,setPick2]=useState(current?.choice2??'');
  const [pick3,setPick3]=useState(current?.choice3??'');
  const [pick4,setPick4]=useState(current?.choice4??'');
  const [pick5,setPick5]=useState(current?.choice5??'');
  const ready=!!pick&&(!spec.options2||!!pick2)&&(!spec.options3||!!pick3)&&(!spec.options4||!!pick4)&&(!spec.options5||!!pick5);
  return <section className="extraask entry-situation" aria-labelledby="situation-title">
    <p className="entry-eyebrow">02 · 지금 놓인 장면</p>
    <h1 id="situation-title" className="conversion-title">조금 더 구체적으로<br/>알려주시오.</h1>
    <p className="conversion-lead">같은 고민도 처한 상황에 따라 볼 자리가 다르오.<br/>고른 답은 첫 해석부터 모든 해석자에게 이어집니다.</p>
    <p className="ttl">{spec.title}</p>
    <p className="q">{spec.q}</p>
    <div className="og c2" role="group" aria-label={spec.q}>
      {spec.options.map(option=><button type="button" key={option.id} className={`op ${pick===option.id?'on':''}`} aria-pressed={pick===option.id} onClick={()=>setPick(option.id)}><b>{option.label}</b></button>)}
    </div>
    {spec.q2&&spec.options2&&<><p className="q">{spec.q2}</p><div className="og c2" role="group" aria-label={spec.q2}>
      {spec.options2.map(option=><button type="button" key={option.id} className={`op ${pick2===option.id?'on':''}`} aria-pressed={pick2===option.id} onClick={()=>setPick2(option.id)}><b>{option.label}</b></button>)}
    </div></>}
    {spec.q3&&spec.options3&&<><p className="q">{spec.q3}</p><div className="og c2" role="group" aria-label={spec.q3}>
      {spec.options3.map(option=><button type="button" key={option.id} className={`op ${pick3===option.id?'on':''}`} aria-pressed={pick3===option.id} onClick={()=>setPick3(option.id)}><b>{option.label}</b></button>)}
    </div></>}
    {spec.q4&&spec.options4&&<><p className="ttl">선택한 상담자의 전문 관점 · {spec.character_axis}</p><p className="q">{spec.q4}</p><div className="og c2" role="group" aria-label={spec.q4}>
      {spec.options4.map(option=><button type="button" key={option.id} className={`op ${pick4===option.id?'on':''}`} aria-pressed={pick4===option.id} onClick={()=>setPick4(option.id)}><b>{option.label}</b></button>)}
    </div></>}
    {spec.q5&&spec.options5&&<><p className="q">{spec.q5}</p><div className="og c2" role="group" aria-label={spec.q5}>
      {spec.options5.map(option=><button type="button" key={option.id} className={`op ${pick5===option.id?'on':''}`} aria-pressed={pick5===option.id} onClick={()=>setPick5(option.id)}><b>{option.label}</b></button>)}
    </div></>}
    <p className="ask-status" role="status">{ready?'이 상황을 기준으로 첫 풀이부터 좁혀 보겠습니다.':'가장 가까운 상황을 하나 골라주시오.'}</p>
    <button className="btn" disabled={!ready||busy} onClick={()=>onSubmit({choice:pick,...(pick2?{choice2:pick2}:{}),...(pick3?{choice3:pick3}:{}),...(pick4?{choice4:pick4}:{}),...(pick5?{choice5:pick5}:{})})}>{busy?'준비하고 있소…':'이 상황으로 분석하기'}</button>
  </section>;
}
