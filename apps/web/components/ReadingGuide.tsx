import type { ReportResponse } from '@shared/chart';
import CompanionCat from './CompanionCat';
export default function ReadingGuide({guide}:{guide:NonNullable<ReportResponse['editorial']>}) {
  return <section className="conversion-card" aria-label="이번 해석의 확인 질문">
    <p className="conversion-kicker">{guide.title}</p>
    <h2 style={{fontSize:22,lineHeight:1.55}}>{guide.question}</h2>
    <p className="conversion-note">읽은 근거 · {guide.observation}</p>
    <p><strong>오늘 해볼 것</strong><br />{guide.action}</p>
    <p className="conversion-note">{guide.boundary}</p>
    <details className="conversion-details"><summary>내 경험에 대입해 보기</summary>
      <p>{guide.scene}</p>
    </details>
    <CompanionCat state="rest" message="한 번에 다 읽지 않아도 돼요. 지금 필요한 질문 하나부터." />
  </section>;
}
