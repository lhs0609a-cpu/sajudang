"use client";

import type { ReportResponse } from '@shared/chart';
import { track } from '@/lib/track';

export default function ReadingBasis({basis}:{basis:ReportResponse['reading_basis']}) {
  if (!basis) return null;
  return <section className="reading-basis" aria-label={basis.title}>
    <p className="conversion-kicker">{basis.title}</p>
    <ul><li>{basis.birth}</li><li>{basis.timing}</li></ul>
    {basis.answers.length>0 && <p className="reading-basis-answers"><span>직접 고른 상황</span>{basis.answers.join(' · ')}</p>}
    <details onToggle={event=>{if(event.currentTarget.open) track('reading_expand','reading',{stage:6});}}>
      <summary>사주와 내 답을 어떻게 함께 읽나요?</summary>
      <p>{basis.scope}</p>
      <p>각 해석 아래에서 계산 근거를 펼쳐 볼 수 있습니다. 태어난 시간을 모르면 그 부분을 제외합니다.</p>
    </details>
  </section>;
}
