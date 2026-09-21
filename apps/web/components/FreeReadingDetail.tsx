import type { ReportCut } from '@shared/chart';
import ServerText from './ServerText';

export const FREE_DETAIL_IDS = new Set(['spine_depth', 'spine_scene', 'lens_bridge']);

/** Full, server-authorized observations before asking the reader to buy more. */
export default function FreeReadingDetail({cuts}: {cuts: ReportCut[]}) {
  const rows = cuts.filter(c => FREE_DETAIL_IDS.has(c.id));
  if (!rows.length) return null;
  return <section className="free-reading-detail" aria-label="무료 상세 풀이">
    <p className="conversion-kicker">그 말이 그대의 일상에서는 어떻게 나타나는지</p>
    {rows.map(c => <article key={c.id}>
      <h2>{c.title}</h2>
      <div dangerouslySetInnerHTML={{__html:c.html}} />
      <ServerText as="p" className="conversion-note" html={`이렇게 읽은 근거 · ${c.source}`} />
    </article>)}
    <p className="preview-bridge">여기까지는 그대가 힘을 쓰는 방식과 그 뒤에 남는 피로를 보았소. 그렇다면 같은 힘이 어떤 때는 기회가 되고, 어떤 때는 되풀이되는 고민이 되는 까닭은 무엇일까? 다음 질문에서 그 차이를 더 깊이 짚어보오.</p>
  </section>;
}
