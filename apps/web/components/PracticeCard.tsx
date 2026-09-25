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
  specialist_name?: string; specialist_axis?: string; case_summary?: string;
  specialist_verdict?: string; specialist_action?: string; specialist_close?: string;
}

export default function PracticeCard({ practice, lensId }: { practice: Practice; lensId?: string }) {
  const [status, setStatus] = useState("");
  const [saved, setSaved] = useState(false);
  return <CharacterSpeech lensId={lensId}><section className="conversion-card" aria-label="해석을 현실에 적용하는 오늘 행동">
    <ArtImage art="action" className="practice-art" />
    <ReadingSpeaker lensId={lensId} label="오늘은 이렇게 해보시오" soft />
    <p className="conversion-kicker">4단계 · 해석을 현실에 적용 · 오늘 끝낼 한 가지</p>
    <h2>{practice.specialist_axis ? `${practice.specialist_axis}부터 가르겠소` : practice.title}</h2>
    {practice.case_summary && <p className="practice-case"><span>당신이 고른 실제 상황</span><strong>{practice.case_summary}</strong></p>}
    {practice.specialist_verdict ? <div className="practice-verdict">
      <span>{practice.specialist_name ?? '이 상담자'}의 날카로운 판정</span>
      <p>{practice.specialist_verdict}</p>
    </div> : <p>{practice.scene}</p>}
    {/* ★ 시키는 일은 **하나**입니다 (2026-09-25).
     *
     *   손님이 무료 구간을 통째로 붙여 놓고 「와닿지 않는다」 했습니다.
     *   이 카드를 세어 보니 시키는 일이 넷(펼치면 아홉)이었습니다 —
     *   오늘의 과제 + 단계 셋(각각 h3 제목을 달아 독립 과제처럼 섰습니다)
     *   + 갈림 + 접힌 다섯. 둘이면 손님은 **하나도** 안 합니다 (CLAUDE.md).
     *
     *   글은 그대로 둡니다. 지우면 판정이 얇아집니다 — 「길다고 문장을
     *   지우기」 금지. 대신 **하나로 묶습니다**: 과제 하나, 그 아래는
     *   「그 하나를 이렇게」 라고 이름을 붙인 순서요. 제목을 떼니 단계가
     *   과제로 안 읽힙니다.
     *
     *   「QUEST 01」도 걷었습니다 — 영어 속말이고, 하오체 판정 바로 위에서
     *   말투가 튑니다. */}
    <div className="practice-mission">
      <span>오늘 할 하나</span>
      <h3>{practice.specialist_action ?? practice.action}</h3>
      <p>읽고 끝내지 말고, 오늘 가능한 가장 작은 크기로 실행하시오.</p>
    </div>
    {practice.steps?.length ? <div className="practice-how">
      <h3>그 하나를 이렇게 하시오</h3>
      <ol className="practice-steps">{practice.steps.map((step, i) =>
        <li key={i}><p>{step}</p></li>
      )}</ol>
    </div> : null}
    {practice.decision && <div className="practice-decision"><h3>상황이 다르면 여기서 갈립니다</h3><p>{practice.decision}</p></div>}
    {(practice.focus || practice.mbti || practice.example || practice.trap || practice.review) && <details className="practice-deeper">
      <summary>내 상황에 맞춘 실행 보정까지 보기</summary>
      <div className="practice-workbook">
        {([['focus','먼저 살필 지점'],['mbti','내 MBTI에 맞춘 실행법'],['example','실제로 적는 예시'],['trap','여기까지 애쓰지는 마시오'],['review','오늘 행동이 끝났다는 기준']] as const).map(([key,title])=>practice[key]
          ? <div key={key}><h3>{title}</h3><p>{practice[key]}</p></div> : null)}
      </div>
    </details>}
    {practice.specialist_close && <blockquote className="practice-close">{practice.specialist_close}</blockquote>}
    <ServerText as="p" className="conversion-note" html={practice.source} />
    <button className="btn gh" onClick={async () => {
      try {
        await navigator.clipboard.writeText([practice.specialist_axis, practice.case_summary, practice.specialist_verdict, practice.specialist_action ?? practice.action, ...(practice.steps ?? []).map((step, i) => `${i + 1}. ${step}`), practice.decision, practice.focus, practice.mbti, practice.example, practice.trap, practice.review, practice.specialist_close, practice.source].filter(Boolean).join('\n\n'));
        setSaved(true); setStatus("행동 문장을 복사했소. 원하는 메모에 붙여넣어 보시오.");
        track("practice_saved", "d0");
      } catch { setStatus("자동으로 복사하지 못했소. 위 문장을 길게 눌러 복사해 주시오."); }
    }}>행동 문장 복사하기</button>
    <CompanionCat state={saved ? "saved" : "rest"} message={saved ? "발도장 꾹! 작은 행동 하나면 충분하다냥." : "지금 필요한 행동부터 골라보자냥."} />
    <p className="conversion-note" role="status">{status}</p>
  </section></CharacterSpeech>;
}
