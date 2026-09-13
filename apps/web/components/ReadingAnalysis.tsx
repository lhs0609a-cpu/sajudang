"use client";

import { useState } from "react";
import type { ConsultationSpec, IntegratedReading } from "@shared/chart";

function Consultation({ spec, busy, onSubmit }: {
  spec: ConsultationSpec; busy: boolean;
  onSubmit: (extras: Record<string, unknown>) => void;
}) {
  const [answers, setAnswers] = useState(spec.answers);
  const changed = JSON.stringify(answers) !== JSON.stringify(spec.answers);
  const submit = (next: Record<string, string>) => onSubmit({ consultation: { concern: spec.concern, answers: next } });
  return <details className="reading-consultation noprint">
    <summary>{spec.title}</summary>
    <p className="sm">{spec.note}</p>
    <form onSubmit={event => { event.preventDefault(); if (changed && !busy) submit(answers); }}>
      {spec.questions.map(question => <fieldset key={question.id} disabled={busy}>
        <legend>{question.question}</legend>
        <p className="sm">{question.reason}</p>
        <div className="reading-options">
          {question.options.map(option => <label key={option.id} className={answers[question.id] === option.id ? "chosen" : ""}>
            <input type="radio" name={question.id} value={option.id} checked={answers[question.id] === option.id}
              onChange={() => setAnswers(prev => ({ ...prev, [question.id]: option.id }))} />
            <span>{option.label}</span>
          </label>)}
        </div>
      </fieldset>)}
      <button type="submit" className="btn" disabled={busy || !changed}>{busy ? "답변을 반영하는 중" : "내 답변으로 풀이 다듬기"}</button>
      {Object.keys(spec.answers).length > 0 && <button type="button" className="btn gh" disabled={busy}
        onClick={() => submit({})}>답변을 지우고 다시 보기</button>}
    </form>
  </details>;
}

export default function ReadingAnalysis({ reading, preview = false, busy = false, onSubmit }: {
  reading: IntegratedReading; preview?: boolean; busy?: boolean;
  onSubmit?: (extras: Record<string, unknown>) => void;
}) {
  return <section className="integrated-reading" aria-label="근거를 연결한 종합 해석" aria-busy={busy}>
    <header className="reading-plan-head">
      <p className="conversion-kicker">{reading.scope === "전체" ? "하나의 명식, 이어지는 이야기" : "이번 고민에서 먼저 볼 것"}</p>
      <h2>{preview ? reading.headline : reading.summary.length ? `이번 풀이의 핵심 ${reading.summary.length}가지` : "먼저 확인할 명식의 범위"}</h2>
      <p className="sm">{reading.boundary}</p>
      {reading.as_of && <p className="sm">{reading.as_of} 기준</p>}
    </header>
    {reading.empty_reason && <p>{reading.empty_reason}</p>}
    {reading.input_error && <p role="alert" className="warn">{reading.input_error}</p>}
    <div className="reading-conclusions">
      {(preview ? reading.summary.slice(0, 1) : reading.summary).map((claim, index) => <article key={claim.id}>
        <p className="reading-origin">{index + 1} · {claim.status}</p>
        {!preview && <h3>{claim.title}</h3>}
        <div className="cutbody" dangerouslySetInnerHTML={{ __html: claim.html }} />
      </article>)}
    </div>
    {!preview && <>
      {onSubmit && <Consultation key={reading.fingerprint} spec={reading.consultation} busy={busy} onSubmit={onSubmit} />}
      <nav className="reading-plan-nav" aria-label="종합 해석 목차">
        {reading.sections.map(section => <a key={section.id} href={`#plan-${section.id}`}>{section.title}</a>)}
      </nav>
      {reading.sections.map(section => <section key={section.id} id={`plan-${section.id}`} className="reading-plan-section">
        <h2>{section.title}</h2>
        <div className="cutbody" dangerouslySetInnerHTML={{ __html: section.html }} />
      </section>)}
    </>}
  </section>;
}
