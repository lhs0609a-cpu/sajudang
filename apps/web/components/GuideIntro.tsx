import CharArt from './CharArt';
import { LENS_BY_ID } from '@/lib/lenses';

/** The guide is introduced before any character dialogue or personal input. */
export default function GuideIntro() {
  return <section className="guide-intro" aria-label="성신당 길잡이 소개">
    <CharArt lens={LENS_BY_ID.pungun} size="talk" />
    <div><p className="conversion-kicker">성신당 길잡이 · 풍운도령</p>
      <p>“풍운도령이오. 먼저 그대의 고민을 듣고, 무료 해석부터 안내하겠소.”</p>
      <p className="conversion-note">첫 해석은 풍운도령과, 다른 관점은 스무 해석자 중에서 선택해요. 고양이는 쉬어갈 때 곁에 있어요.</p>
    </div>
  </section>;
}
