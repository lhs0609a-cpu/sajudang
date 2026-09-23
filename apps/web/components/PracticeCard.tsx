"use client";

import { useState } from "react";
import CompanionCat from "@/components/CompanionCat";
import { track } from "@/lib/track";
import ServerText from "@/components/ServerText";
import { ArtImage } from "./ReadingArtwork";
import { ReadingSpeaker } from './ReadingVoice';
import CharacterSpeech from './CharacterSpeech';

export interface Practice {
  id: string; version: number; source_kind: string; source: string;
  title: string; scene: string; action: string;
  steps?: string[];
  focus?: string; example?: string; decision?: string; trap?: string; review?: string; mbti?: string;
}

export default function PracticeCard({ practice, lensId }: { practice: Practice; lensId?: string }) {
  const [status, setStatus] = useState("");
  const [saved, setSaved] = useState(false);
  return <CharacterSpeech lensId={lensId}><section className="conversion-card" aria-label="오늘 해볼 행동">
    <ArtImage art="action" className="practice-art" />
    <ReadingSpeaker lensId={lensId} label="오늘은 이렇게 해보시오" soft />
    <p className="conversion-kicker">오늘 해볼 행동 하나 · 무료</p>
    <h2>{practice.title}</h2><p>{practice.scene}</p>
    {practice.focus && <div className="practice-focus"><h3>이번 풀이에서 먼저 살필 지점</h3><p>{practice.focus}</p></div>}
    {practice.mbti && <div className="practice-focus"><h3>내가 고른 MBTI에 맞춘 실행법</h3><p>{practice.mbti}</p></div>}
    <p className="conversion-lead">{practice.action}</p>
    {practice.steps?.length ? <ol className="practice-steps">{practice.steps.map((step, i) =>
      <li key={i}><h3>{['먼저, 한 장면만 꺼내시오', '이렇게 말하거나 적어보시오', '오늘 밤, 이것만 확인하시오'][i]}</h3><p>{step}</p></li>
    )}</ol> : null}
    <div className="practice-workbook">
      {([['example','예를 들면, 이렇게 적으시오'],['decision','상황이 다르면 행동도 달라지오'],['trap','이렇게까지 애쓰지는 마시오'],['review','오늘의 행동이 끝났다는 기준']] as const).map(([key,title])=>practice[key]
        ? <div key={key}><h3>{title}</h3><p>{practice[key]}</p></div> : null)}
    </div>
    <ServerText as="p" className="conversion-note" html={practice.source} />
    <button className="btn gh" onClick={async () => {
      try {
        await navigator.clipboard.writeText([practice.title, practice.focus, practice.mbti, practice.action, ...(practice.steps ?? []).map((step, i) => `${i + 1}. ${step}`),practice.example,practice.decision,practice.trap,practice.review, practice.source].filter(Boolean).join('\n\n'));
        setSaved(true); setStatus("행동 문장을 복사했소. 원하는 메모에 붙여넣어 보시오.");
        track("practice_saved", "d0");
      } catch { setStatus("자동으로 복사하지 못했소. 위 문장을 길게 눌러 복사해 주시오."); }
    }}>행동 문장 복사하기</button>
    <CompanionCat state={saved ? "saved" : "rest"} message={saved ? "발도장 꾹! 작은 행동 하나면 충분하다냥." : "지금 필요한 행동부터 골라보자냥."} />
    <p className="conversion-note" role="status">{status}</p>
  </section></CharacterSpeech>;
}
