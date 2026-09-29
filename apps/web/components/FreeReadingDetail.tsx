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
    <p className="conversion-kicker">{timing ? '3단계 · 왜 하필 지금 · 명식과 현재 운의 분석' : '3단계 · 답을 반영한 해석 · 실제 장면과 반복 조건'}</p>
    {rows.map(c => {
      // Keep valid server HTML blocks intact. Insert the question after the
      // concrete case, before MBTI reflection, while free reading continues.
      const pivot = c.html.indexOf('<div class="mbti-reading">');
      const split = c.id === 'spine_scene' && pivot > 0;
      return <article key={c.id}>
      <ReadingVoice lensId={lensId} label={timing && c.id === 'spine_scene' ? '원국·대운·세운 분석' : '무료 핵심 해석'}>
        <h2>{c.title}</h2>
        <div dangerouslySetInnerHTML={{__html:split ? c.html.slice(0,pivot) : c.html}} />
      </ReadingVoice>
      <ServerText as="p" className="conversion-note" html={`이렇게 읽은 근거 · ${c.source}`} />
      {onOpen && c.id !== 'spine_scene' && <InlinePaidReading after={c.id} cuts={locked} lensId={lensId ?? selected} onOpen={onOpen} />}
      {split && <ReadingVoice lensId={lensId} label="고른 답을 반영한 해석"><div dangerouslySetInnerHTML={{__html:c.html.slice(pivot)}} /></ReadingVoice>}
    </article>;})}
    <p className="preview-bridge">{timing ? '원국은 타고난 구조, 대운은 긴 배경, 세운은 올해 더해지는 조건이오. 아래에서는 이 분석과 그대가 답한 실제 상황을 나누어 읽으시오.' : '같은 힘이 어떤 날에는 성과를 만들고, 어떤 날에는 피로만 남겼소. 아래에서는 두 날을 갈라놓은 조건과 오늘 끊을 반복 하나를 판정하오.'}</p>
    <FriendInvite />
  </section></CharacterSpeech>;
}
