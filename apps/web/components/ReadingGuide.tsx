import type { ReportResponse } from '@shared/chart';
import CompanionCat from './CompanionCat';
export default function ReadingGuide({guide,revelation}:{guide:NonNullable<ReportResponse['editorial']>;revelation?:{title:string;body:string;source:string}|null}) {
  return <section className="conversion-card" aria-label="이번 해석의 확인 질문">
    <p className="conversion-kicker">{revelation ? '그대의 명식에서 먼저 읽힌 대목' : guide.title}</p>
    <h2 style={{fontSize:22,lineHeight:1.55}}>{revelation?.title ?? guide.question}</h2>
    {revelation?.body && <p className="reading-revelation">{revelation.body}</p>}
    <p className="conversion-note">읽은 근거 · {revelation?.source ?? guide.observation}</p>
    <p className="conversion-note">전통 해석의 관점이오. 실제 경험과 함께 살펴보시오.</p>
    {revelation && <p className="reading-revelation"><strong>{guide.perspective}</strong><br/>{guide.question}</p>}
    <p><strong>오늘 해볼 것</strong><br />{guide.action}</p>
    <p className="conversion-note">{guide.boundary}</p>
    <details className="conversion-details"><summary>내 경험에 대입해 보기</summary>
      <p>{guide.scene}</p>
    </details>
    <CompanionCat state="rest" message="한 번에 다 안 읽어도 된다냥. 궁금한 것부터 보자!" />
  </section>;
}
