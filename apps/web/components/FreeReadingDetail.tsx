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
  const rows = cuts.filter(c => FREE_DETAIL_IDS.has(c.id));
  if (!rows.length) return null;
  return <CharacterSpeech lensId={lensId}><section className="free-reading-detail" aria-label="무료 상세 풀이">
    <p className="conversion-kicker">그 말이 그대의 일상에서는 어떻게 나타나는지</p>
    {rows.map(c => {
      // Keep valid server HTML blocks intact. Insert the question after the
      // concrete case, before MBTI reflection, while free reading continues.
      const pivot = c.html.indexOf('<div class="mbti-reading">');
      const split = c.id === 'spine_scene' && pivot > 0;
      return <article key={c.id}>
      <ReadingVoice lensId={lensId} label="그대에게 들려주는 해석">
        <h2>{c.title}</h2>
        <div dangerouslySetInnerHTML={{__html:split ? c.html.slice(0,pivot) : c.html}} />
      </ReadingVoice>
      <ServerText as="p" className="conversion-note" html={`이렇게 읽은 근거 · ${c.source}`} />
      {onOpen && <InlinePaidReading after={c.id} cuts={locked} lensId={lensId ?? selected} onOpen={onOpen} />}
      {split && <ReadingVoice lensId={lensId} label="그대의 성향에 맞춰 한 걸음 더"><div dangerouslySetInnerHTML={{__html:c.html.slice(pivot)}} /></ReadingVoice>}
    </article>;})}
    <p className="preview-bridge">여기까지는 그대가 힘을 쓰는 방식과 그 뒤에 남는 피로를 보았소. 그렇다면 같은 힘이 어떤 때는 기회가 되고, 어떤 때는 되풀이되는 고민이 되는 까닭은 무엇일까? 다음 질문에서 그 차이를 더 깊이 짚어보오.</p>
    <FriendInvite />
  </section></CharacterSpeech>;
}
