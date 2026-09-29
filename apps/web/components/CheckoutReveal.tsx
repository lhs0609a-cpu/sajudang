"use client";

import { CHARACTER_QUESTIONS } from '@/lib/curiosity';
import { josa } from '@/lib/josa';

type Peek = {lens_id:string;lens_name:string;ask:string;head:string;reader_head?:string;mask:number;source:string|null;chars:number};
type Reveal = {hook:string;after:[string,string,string]};

const REVEALS:Record<string,Reveal> = {
  pungun:{hook:'왜 요즘 같은 일이 더 버겁게 느껴질까요? 타고난 사주와 지금의 운을 함께 읽습니다.',after:['원래 중요하게 여기는 일','요즘과 앞으로의 운에서 달라지는 점','내 상황에 맞춰 생각해 볼 선택']},
  baegun:{hook:'잘되는 때와 지치는 때는 무엇이 다를까요? 사주에서 읽은 특징을 일하는 환경과 함께 봅니다.',after:['내가 편하게 능력을 쓰는 조건','쉽게 지치는 상황','바꿔 볼 생활과 일의 방식']},
  cheongam:{hook:'아직 더 알아봐야 할까요, 이제 정해도 될까요? 결정에 필요한 사실부터 나눠 봅니다.',after:['아직 확인하지 못한 정보','결정을 미루는 이유','선택 전에 지킬 기준']},
  sigye:{hook:'예전 방식이 지금도 맞을까요? 지나온 때와 앞으로의 때를 비교해 읽습니다.',after:['예전과 지금의 차이','지금 준비할 일','다음 운을 읽는 기준']},
  monghwa:{hook:'새로운 곳이 좋은 걸까요, 지금을 벗어나고 싶은 걸까요? 새 선택에서 바라는 생활을 봅니다.',after:['새 선택에서 원하는 것','옮긴 뒤의 평범한 하루','먼저 확인할 생활 조건']},
  eunbyeol:{hook:'예전에는 도움이 된 습관이 지금도 통할까요? 막힐 때 나오는 반응부터 봅니다.',after:['어려울 때 반복하는 반응','그 반응이 남긴 결과','이번에 다르게 해볼 행동']},
  jeokhyeol:{hook:'강하게 끌리는 마음이 오래 갈 관계로 이어질까요? 좋을 때와 다툴 때를 함께 봅니다.',after:['끌리는 이유와 기대','의견이 다를 때의 반응','서로 지킬 수 있는 약속']},
  seoyeok:{hook:'다른 사람의 답이 나에게도 맞을까요? 내 조건에서 다시 따져 봅니다.',after:['남의 생각을 따라 정한 기준','나와 그 사람의 다른 조건','내 선택을 시험해 볼 방법']},
  paeseon:{hook:'새 일을 시작하고 싶은데 왜 여유가 없을까요? 이미 붙잡고 있는 일을 함께 봅니다.',after:['동시에 맡은 일의 부담','줄여도 되는 일','새 기회를 살필 여유']},
  myeonsang:{hook:'엉뚱한 사람에게 예민해지는 이유는 무엇일까요? 감정이 생긴 상황부터 돌아봅니다.',after:['감정이 시작된 상황','가까운 사람에게 옮겨간 말','다시 이야기할 방법']},
  wolha:{hook:'내 마음을 몰랐던 걸까요, 알고도 달라지지 않은 걸까요? 말한 내용과 상대의 반응을 나눠 봅니다.',after:['내가 바랐던 것','상대에게 실제로 말한 것','대화를 이어갈 때 볼 반응']},
  hongmae:{hook:'함께하는데 왜 한 사람만 더 애쓸까요? 돈·시간·돌봄을 어떻게 나눴는지 봅니다.',after:['한쪽에 몰린 일','서로 다르게 이해한 약속','함께 지낼 때 다시 정할 것']},
  yeondam:{hook:'다시 연락하고 싶은 마음부터 차분히 살펴봅니다. 상대가 거절한 뜻도 함께 존중합니다.',after:['연락해서 얻고 싶은 답','상대가 마지막으로 보인 반응','연락을 멈춰야 할 기준']},
  hwagyeong:{hook:'좋은 뜻으로 한 말이 왜 다르게 전해졌을까요? 내 뜻과 실제 행동을 나눠 봅니다.',after:['확인한 사실과 추측','상대가 겪은 내 행동','말보다 행동으로 바꿀 것']},
  haengsu:{hook:'열심히 벌었는데 왜 돈이 남지 않을까요? 수입뿐 아니라 비용과 들인 시간도 봅니다.',after:['벌어들인 돈과 실제 남은 돈','추가로 들어간 시간과 비용','다음 거래 전에 정할 조건']},
  hunjang:{hook:'더 배워야 할까요, 지금 해봐도 될까요? 준비와 실행을 나눠 봅니다.',after:['시작에 꼭 필요한 공부','지금 가진 것으로 해볼 일','결과를 보여주고 의견받는 방법']},
  yakcho:{hook:'쉬어도 마음이 바쁜 이유를 돌아봅니다. 진단 대신 생활에서 줄일 부담을 살펴봅니다.',after:['쉬는 시간을 깨는 일','오늘 일을 끝낼 기준','전문가 도움이 필요한 경우']},
  ilgwan:{hook:'확실히 아는 것과 아직 모르는 것을 나눕니다. 사주 계산과 실제 선택의 조건을 함께 봅니다.',after:['계산으로 확인한 내용','현실에서 더 알아볼 정보','결정을 바꿀 수 있는 조건']},
  nopa:{hook:'처음 고른 이유가 지금도 남아 있을까요? 계속할 이유와 달라진 사정을 함께 봅니다.',after:['처음 이 길을 고른 이유','지금 힘들어진 부분','줄이거나 바꿔볼 방법']},
  dongja:{hook:'오늘은 생각을 더 늘리지 않아도 됩니다. 지금 감당할 수 있는 만큼만 함께 봅니다.',after:['지금 가장 힘든 일','오늘 덜어도 되는 부담','아무것도 하지 않고 쉬어도 되는 때']},
};

export default function CheckoutReveal({lensId,name,peek,cuts,chars,minutes}:{lensId:string;name:string;peek:Peek[]|null;cuts:number;chars:number;minutes:number}){
  const reveal=REVEALS[lensId] ?? {hook:'무료 풀이에서 멈춘 질문을 실제 장면과 선택 기준까지 이어서 봅니다.',after:['반복되는 장면의 원인','선택이 갈리는 기준','오늘 바꿀 한 가지']};
  return <section className="checkout-reveal" aria-label="결제 후 추가로 확인할 내용">
    <p className="conversion-kicker">더 읽으면 알 수 있는 내용</p>
    <h3>{CHARACTER_QUESTIONS[lensId] ?? `${name}${josa(name,'이','가')} 아직 말하지 않은 핵심`}</h3>
    <p className="checkout-reveal-hook">{reveal.hook}</p>
    <ol className="checkout-reveal-after">{reveal.after.map((line,index)=><li key={line}><span>{String(index+1).padStart(2,'0')}</span><strong>{line}</strong><i aria-hidden="true"/></li>)}</ol>
    {peek?.length ? <div className="checkout-real-preview">
      <span>이 사주로 만든 실제 해석의 일부</span>
      {peek.slice(0,3).map((row,index)=><article key={`${row.lens_id}-${index}`}>
        <small>{row.lens_name} · {row.chars.toLocaleString()}자</small>
        <h4>{row.ask}</h4>
        <p>{row.reader_head ?? row.head}…</p>
        <div className="checkout-secret" aria-label={`${row.mask.toLocaleString()}자의 이어지는 해석은 결제 후 공개`}><i/><i/><b>이어지는 해석은 결제 후 읽을 수 있습니다</b></div>
      </article>)}
    </div>:<p className="conversion-note">이 사주로 만든 해석 예시를 불러오고 있소…</p>}
    <div className="checkout-reveal-volume">
      <span>추가로 읽을 수 있는 분량</span>
      <strong>{cuts}개 질문에 대한 해석 전체</strong>
      <p>{chars.toLocaleString()}자 · 약 {minutes}분. 궁금한 제목을 골라 읽을 수 있습니다. 결제 전에 아래의 포함 내용과 결제 조건을 확인하세요.</p>
    </div>
  </section>;
}
