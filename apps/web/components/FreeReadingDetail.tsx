"use client";
import type { ReportCut, LockedCut } from '@shared/chart';
import ServerText from './ServerText';
import ReadingVoice from './ReadingVoice';
import InlinePaidReading from './InlinePaidReading';
import { useSession } from '@/lib/store';
import CharacterSpeech from './CharacterSpeech';
import FriendInvite from './FriendInvite';

export const FREE_DETAIL_IDS = new Set(['spine_depth', 'spine_scene', 'lens_bridge']);

/** Full, server-authorized observations before asking the reader to buy more. */
export default function FreeReadingDetail({cuts, lensId, locked = [], onOpen}: {cuts: ReportCut[]; lensId?: string; locked?: LockedCut[]; onOpen?: () => void}) {
  const selected = useSession(s => s.cur);
  const timing = (lensId ?? selected) === 'pungun';
  const rows = cuts.filter(c => FREE_DETAIL_IDS.has(c.id));
  if (!rows.length) return null;
  return <CharacterSpeech lensId={lensId}><section className="free-reading-detail" aria-label="추가 질문을 반영한 무료 상세 해석">
    <p className="conversion-kicker">{timing ? '3단계 · 왜 하필 지금 · 올해 내게 중요한 일' : '3단계 · 내 답을 바탕으로 자세히 읽기'}</p>
    {rows.map(c => {
      // Keep valid server HTML blocks intact. Insert the question after the
      // concrete case, before MBTI reflection, while free reading continues.
      const body = c.reader_html ?? c.html;
      const pivot = body.indexOf('<div class="mbti-reading">');
      const split = c.id === 'spine_scene' && pivot > 0;
      return <article key={c.id}>
      <ReadingVoice lensId={lensId} label={timing && c.id === 'spine_scene' ? '태어난 사주와 올해를 함께 읽기' : '무료 핵심 해석'}>
        <h2>{c.reader_title ?? c.title}</h2>
        <div dangerouslySetInnerHTML={{__html:split ? body.slice(0,pivot) : body}} />
      </ReadingVoice>
      <details className="reading-evidence"><summary>왜 이렇게 읽었나요?</summary><ServerText as="p" className="conversion-note" html={c.source} /></details>
      {onOpen && c.id !== 'spine_scene' && <InlinePaidReading after={c.id} cuts={locked} lensId={lensId ?? selected} onOpen={onOpen} />}
      {split && <ReadingVoice lensId={lensId} label="내 답을 바탕으로 읽기"><div dangerouslySetInnerHTML={{__html:body.slice(pivot)}} /></ReadingVoice>}
    </article>;})}
    <p className="preview-bridge">사주에서 읽은 내용과 실제로 겪은 일을 함께 보시오. 다음에는 그대가 고른 상황에서 무엇을 해볼지 정리하겠소.</p>
    <FriendInvite />
  </section></CharacterSpeech>;
}
