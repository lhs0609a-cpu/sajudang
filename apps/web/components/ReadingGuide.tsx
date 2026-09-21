import type { ReportResponse } from '@shared/chart';
import CompanionCat from './CompanionCat';
import ServerText from "@/components/ServerText";
import { IllustratedNote } from "./ReadingArtwork";
export default function ReadingGuide({guide,revelation,preview=false}:{guide:NonNullable<ReportResponse['editorial']>;revelation?:{title:string;body:string;source:string}|null;preview?:boolean}) {
  return <section className="conversion-card" aria-label="이번 해석의 확인 질문">
    <p className="conversion-kicker">{revelation ? '그대의 명식에서 먼저 읽힌 대목' : guide.title}</p>
    <h2 style={{fontSize:22,lineHeight:1.55}}>{revelation?.title ?? guide.question}</h2>
    {revelation?.body && <p className="reading-revelation">{revelation.body}</p>}
    <ServerText as="p" className="conversion-note" html={`읽은 근거 · ${revelation?.source ?? guide.observation}`} />
    <p className="conversion-note">전통 해석의 관점이오. 실제 경험과 함께 살펴보시오.</p>
    {revelation && <p className="reading-revelation"><strong>{guide.perspective}</strong><br/>{guide.question}</p>}
    {preview ? <p className="reading-scene">{guide.scene}</p> : <>
    <IllustratedNote art="action" title="오늘 해볼 것"><p>{guide.action}</p></IllustratedNote>
    <p className="conversion-note">{guide.boundary}</p>
    {/* ★ 접어 두지 않습니다 (2026-09-17). 이 한 줄이 「내 얘기구나」를
        만드는 자리인데 눌러야 열리고 있었습니다. */}
    <p className="reading-scene">{guide.scene}</p>
    <CompanionCat state="rest" message="한 번에 다 안 읽어도 된다냥. 궁금한 것부터 보자!" />
    </>}
  </section>;
}
