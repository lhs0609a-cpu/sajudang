import type { ReportResponse } from '@shared/chart';
import CompanionCat from './CompanionCat';
import ServerText from "@/components/ServerText";
import { IllustratedNote } from "./ReadingArtwork";
import { ReadingSpeaker } from './ReadingVoice';
import CharacterSpeech from './CharacterSpeech';
export default function ReadingGuide({guide,revelation,preview=false,lensId}:{guide:NonNullable<ReportResponse['editorial']>;revelation?:{title:string;body:string;source:string}|null;preview?:boolean;lensId?:string}) {
  return <CharacterSpeech lensId={lensId}><section className="conversion-card interpretation-card" aria-label="계산으로 확인한 첫 해석">
    <ReadingSpeaker lensId={lensId} label="먼저 이 대목부터" />
    <p className="conversion-kicker">1단계 · 해석 · 계산으로 확인한 무료 판정</p>
    <h2 style={{fontSize:22,lineHeight:1.55}}>{revelation?.title ?? guide.question}</h2>
    {revelation?.body && <p className="reading-revelation">{revelation.body}</p>}
    <ServerText as="p" className="conversion-note" html={`읽은 근거 · ${revelation?.source ?? guide.observation}`} />
    <p className="conversion-note">생년월일에서 계산한 전통 해석이오. 실제 경험과 다르면 맞는 말로 취급하지 마시오.</p>
    {revelation && <div className="reading-verdict"><span>이 상담자가 가르는 핵심</span><strong>{guide.perspective}</strong><p>{guide.question}</p></div>}
    {preview ? <><p className="reading-scene">{guide.scene}</p><p className="conversion-note">아래에서 실제 상황을 더 좁힌 뒤, 오늘 끝낼 한 가지 행동까지 바로 이어집니다.</p></> : <>
    <IllustratedNote art="action" title="오늘 해볼 것"><p>{guide.action}</p></IllustratedNote>
    <p className="conversion-note">{guide.boundary}</p>
    {/* ★ 접어 두지 않습니다 (2026-09-17). 이 한 줄이 「내 얘기구나」를
        만드는 자리인데 눌러야 열리고 있었습니다. */}
    <p className="reading-scene">{guide.scene}</p>
    <CompanionCat state="rest" message="한 번에 다 안 읽어도 된다냥. 궁금한 것부터 보자!" />
    </>}
  </section></CharacterSpeech>;
}
