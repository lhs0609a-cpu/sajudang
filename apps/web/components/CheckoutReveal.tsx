"use client";

import { CHARACTER_QUESTIONS } from '@/lib/curiosity';
import { josa } from '@/lib/josa';

type Peek = {lens_id:string;lens_name:string;ask:string;head:string;mask:number;source:string|null;chars:number};
type Reveal = {hook:string;after:[string,string,string]};

const REVEALS:Record<string,Reveal> = {
  pungun:{hook:'버틸 수 있는 힘과 이제는 내려놔야 할 짐의 경계가 어디인지 가릅니다.',after:['혼자 감당한 몫과 도움받을 수 있었던 몫','지금 유독 무거워진 이유와 바뀐 조건','더 버티기 전에 요청해야 할 단 하나']},
  baegun:{hook:'성격 탓으로 보였던 피로를, 실제로 나를 소모시키는 조건까지 좁힙니다.',after:['잘 풀린 날과 막힌 날을 갈라놓은 조건','급하게 답하게 만드는 숨은 압박','가장 먼저 바꿔야 할 환경 하나']},
  cheongam:{hook:'더 알아봐야 하는 결정인지, 이미 알면서 책임이 두려운 것인지 판정합니다.',after:['판단을 뒤집을 진짜 정보 하나','결정을 미루게 하는 책임의 정체','후회해도 지킬 수 있는 최소 기준']},
  sigye:{hook:'예전에는 맞았지만 지금은 어긋난 방식과, 다시 확인할 정확한 때를 짚습니다.',after:['과거와 지금 사이 달라진 결정 조건','기다려도 되는 일과 움직여야 할 일','다음 변화가 실제인지 확인할 날짜']},
  eunbyeol:{hook:'장점처럼 굳은 자동 반응이 왜 지금은 나를 지치게 하는지 반대편까지 봅니다.',after:['막힐 때 가장 먼저 꺼내는 익숙한 반응','그 반응이 실제로 남긴 결과','이번에 시험할 정반대의 작은 행동']},
  jeokhyeol:{hook:'감정의 크기가 아니라, 거절과 경계를 다루는 방식으로 오래 갈 관계인지 가릅니다.',after:['끌림 뒤에 섞인 기대와 불안','상대가 선을 그었을 때 드러나는 관계의 민낯','좋은 날이 아니어도 지킬 약속의 범위']},
  monghwa:{hook:'새로운 곳으로 향하는 마음과 지금에서 달아나고 싶은 마음을 분리합니다.',after:['새 선택에서 진짜 원하는 장면','환상이 걷힌 평범한 하루의 모습','도망이 아니라 선택으로 남는 조건']},
  seoyeok:{hook:'남에게는 맞는 답과 내 조건에서도 통하는 답을 갈라 빌려온 확신을 걷어냅니다.',after:['내 판단 안에 가장 크게 들어온 타인의 기준','그 사람과 내 조건이 결정적으로 다른 지점','작게 시험해 내 답으로 바꾸는 방법']},
  paeseon:{hook:'기회가 부족한지, 너무 많이 붙잡아 새 기회가 들어올 자리가 없는지 판정합니다.',after:['동시에 붙든 일들이 서로 잡아먹는 비용','하나를 더할 때 반드시 빼야 할 것','포기 없이도 크기를 절반으로 줄이는 패']},
  myeonsang:{hook:'감정이 생긴 곳과 그 감정을 대신 받은 사람을 분리해 관계의 뒷정리를 봅니다.',after:['날카로운 감정이 처음 생긴 자리','가장 가까운 사람에게 옮겨간 순간','상처를 늘리지 않고 다시 말할 시간']},
  wolha:{hook:'말하지 않아 몰랐던 사랑과, 말했는데도 반복해서 무시된 관계를 분명히 가릅니다.',after:['내가 실제로 요청한 것과 눈치채길 바란 것','말한 뒤 상대가 보인 반복된 반응','더 설명할 때와 경계를 세울 때의 기준']},
  hongmae:{hook:'다정함 뒤에 가려진 돈·돌봄·시간의 노동을 꺼내 사랑과 불공정을 분리합니다.',after:['한쪽에 계속 몰리는 관계의 몫','합의였는지 당연하게 떠맡은 일이었는지','오래 함께하기 위해 다시 정할 약속']},
  yeondam:{hook:'다시 연락하고 싶은 마음에서 전달·확인·설득 욕구를 나누고 상대의 실제 경계를 봅니다.',after:['이번 연락으로 정말 얻고 싶은 답','상대가 마지막으로 보여 준 경계','답이 없어도 내 하루를 지킬 중단 기준']},
  hwagyeong:{hook:'누가 옳은지를 반복하지 않고, 의도와 상대가 실제로 겪은 행동의 간격을 비춥니다.',after:['추측을 빼고도 남는 확인 가능한 사실','설명이 길어질수록 가려진 행동 하나','상대가 눈으로 확인할 수 있는 변화']},
  haengsu:{hook:'많이 번 것과 내게 남은 것을 갈라, 돈 뒤에 숨은 시간과 추가 노동까지 계산합니다.',after:['수입에서 비용과 시간을 뺀 진짜 내 몫','일한 만큼 받지 못한 구조의 구멍','다음 거래 전에 먼저 말해야 할 범위와 대가']},
  hunjang:{hook:'정말 더 배워야 하는지, 평가받는 순간이 두려워 준비를 늘리는지 가릅니다.',after:['시작에 꼭 필요한 지식과 핑계가 된 공부','지금 가진 것으로 끝낼 최소 결과','완벽해지기 전에 받아야 할 실제 의견']},
  yakcho:{hook:'의지가 약한 것이 아니라 쉼을 계속 깨우는 책임과 생활의 매듭을 먼저 찾습니다.',after:['쉬려 할 때 가장 먼저 올라오는 부담','오늘 멈춰도 되는 명확한 종료 기준','해석보다 의료 도움을 먼저 받아야 할 경계']},
  ilgwan:{hook:'계산으로 확실한 부분과 현실에서 아직 모르는 조건을 갈라 확신의 범위를 정합니다.',after:['이미 확인한 사실과 전해 들은 말','되돌릴 수 있는 선택과 어려운 선택','판단을 바꿀 조건과 확인할 날짜']},
  nopa:{hook:'처음에는 나를 살린 선택이 지금도 필요한지, 감사와 의무를 떼어 놓고 봅니다.',after:['이 길을 처음 골랐던 절박한 이유','계속할수록 지금 치르는 가장 큰 대가','줄이거나 끝내기 위해 세울 첫 경계']},
  dongja:{hook:'답을 더 얹기 전에 오늘의 내가 감당할 수 있는 가장 작은 한 걸음만 남깁니다.',after:['지금 받아들일 수 있는 조언의 양','오늘 끝내도 되는 가장 작은 일','아무것도 하지 않아도 되는 쉼의 기준']},
};

export default function CheckoutReveal({lensId,name,peek,cuts,chars,minutes}:{lensId:string;name:string;peek:Peek[]|null;cuts:number;chars:number;minutes:number}){
  const reveal=REVEALS[lensId] ?? {hook:'무료 풀이에서 멈춘 질문을 실제 장면과 선택 기준까지 이어서 봅니다.',after:['반복되는 장면의 원인','선택이 갈리는 기준','오늘 바꿀 한 가지']};
  return <section className="checkout-reveal" aria-label="결제 후 추가로 확인할 내용">
    <p className="conversion-kicker">결제 후 가장 먼저 밝혀지는 것</p>
    <h3>{CHARACTER_QUESTIONS[lensId] ?? `${name}${josa(name,'이','가')} 아직 말하지 않은 핵심`}</h3>
    <p className="checkout-reveal-hook">{reveal.hook}</p>
    <ol className="checkout-reveal-after">{reveal.after.map((line,index)=><li key={line}><span>{String(index+1).padStart(2,'0')}</span><strong>{line}</strong><i aria-hidden="true"/></li>)}</ol>
    {peek?.length ? <div className="checkout-real-preview">
      <span>지금 이 명식에서 실제로 열린 질문</span>
      {peek.slice(0,3).map((row,index)=><article key={`${row.lens_id}-${index}`}>
        <small>{row.lens_name} · {row.chars.toLocaleString()}자</small>
        <h4>{row.ask}</h4>
        <p>{row.head}…</p>
        <div className="checkout-secret" aria-label={`${row.mask.toLocaleString()}자의 이어지는 해석은 결제 후 공개`}><i/><i/><b>핵심 판정 {row.mask.toLocaleString()}자 잠김</b></div>
      </article>)}
    </div>:<p className="conversion-note">그대의 명식에서 열리는 실제 질문을 불러오고 있소…</p>}
    <div className="checkout-reveal-volume">
      <span>결제하면 바로 열리는 답</span>
      <strong>{cuts}개 질문에 대한 해석 전체</strong>
      <p>{chars.toLocaleString()}자 · 약 {minutes}분. 한두 문장 요약이 아니라, 원인부터 선택 기준과 오늘 할 행동까지 제목별로 찾아 읽는 본문입니다.</p>
    </div>
  </section>;
}
