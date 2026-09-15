import type { LockedCut } from '@shared/chart';
import { readingText } from '@/lib/reading-journey';

const QUESTIONS: Record<string,string> = {
  daeun_now:'이 패턴은 지금의 흐름과 어떻게 맞물리오?',
  yongsin:'더 밀어붙여야 하오, 다른 힘을 빌려야 하오?',
};
export default function NextReading({cuts}:{cuts:LockedCut[]}) {
  const rows=cuts.filter(c=>c.need_tier==='one' && !!c.teaser)
    .sort((a,b)=>Number(b.id in QUESTIONS)-Number(a.id in QUESTIONS)).slice(0,2);
  if (!rows.length) return null;
  return <section className="next-reading" aria-label="이어지는 실제 해석">
    <p className="conversion-kicker">여기서 한 걸음 더</p>
    <h2>반복을 알았다면,<br/>다음은 달라질 지점이오.</h2>
    {rows.map((cut,i)=><article key={cut.id}><span className="next-reading-number">0{i+1}</span><div>
      <h3>{QUESTIONS[cut.id] ?? cut.title}</h3>
      <p>{readingText(cut.teaser ?? '')}</p>
      <small>추가 해석 「{cut.title}」의 실제 첫 문장</small>
    </div></article>)}
  </section>;
}
