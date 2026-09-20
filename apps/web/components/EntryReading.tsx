"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { track } from "@/lib/track";
import { useSession } from "@/lib/store";
import type { HookSegment } from "@shared/chart";
import ServerText from "./ServerText";

export default function EntryReading({ segments, chartId, concern, lensId, onMiss, onDone }: {
  segments: HookSegment[]; chartId: string; concern: string; lensId: string;
  onMiss: () => void; onDone: () => void;
}) {
  const [answers, setAnswers] = useState<Record<string, boolean | null>>(() => {
    const saved = useSession.getState().hookReview;
    return saved?.edition === "entry3" && saved.chartId === chartId && saved.concern === concern && saved.lensId === lensId
      ? saved.answers : {};
  });
  const [at, setAt] = useState(() => {
    const next = segments.findIndex(item => !Object.prototype.hasOwnProperty.call(answers, item.stage));
    return next < 0 ? segments.length - 1 : next;
  });
  const heading = useRef<HTMLHeadingElement>(null);
  const moved = useRef(false);
  const completed = segments.every(item => Object.prototype.hasOwnProperty.call(answers, item.stage));
  const current = segments[at];

  useEffect(() => { if (completed) onDone(); }, [completed, onDone]);
  useEffect(() => {
    track("hook_shown", "a7", { stage: at });
    if (moved.current) {
      heading.current?.focus({ preventScroll: true });
      heading.current?.scrollIntoView({ block: "start", behavior: "auto" });
    }
  }, [at]);

  const answer = (value: boolean | null) => {
    if (Object.prototype.hasOwnProperty.call(answers, current.stage)) return;
    const next = { ...answers, [current.stage]: value };
    setAnswers(next);
    useSession.getState().set({ hookReview: { chartId, concern, lensId, edition: "entry3", answers: next } });
    track("hook_answer", "a7", { stage: at, yes: value === null ? 2 : value ? 1 : 0 });
    // ★ 묻지 않은 장은 공감률에 안 싣습니다. 진도를 표시하려고 `answer(null)`
    //   을 부르는 자리가 있어서, 그대로 두면 **묻지도 않은 문장**의 노출이
    //   100건 문턱을 채웁니다. 재어야 할 것은 물어본 자리뿐입니다.
    if (current.response_mode === "experience")
      void api.feedback({ statement_id: current.statement_id, chart_id: chartId,
        stage: current.stage, lens_id: lensId, concern, answer: value === null ? null : value ? 1 : 0 }).catch(() => {});
    if (value === false) onMiss();
  };
  const next = () => {
    if (!Object.prototype.hasOwnProperty.call(answers, current.stage)) answer(null);
    if (at < segments.length - 1) { moved.current = true; setAt(at + 1); }
    else onDone();
  };

  return <section className="entry-reading" aria-label="나의 첫 해석">
    <div className="entry-chapter-nav" aria-label="해석 읽기 순서">
      {segments.map((item, index) => <button key={item.stage} aria-current={at === index ? "step" : undefined}
        disabled={index > at && !Object.prototype.hasOwnProperty.call(answers, segments[index - 1].stage)}
        onClick={() => { moved.current = true; setAt(index); }}>
        <span>{String(index + 1).padStart(2, "0")}</span>{item.nav || item.label}
      </button>)}
    </div>
    <article className="entry-reading-card">
      <p className="entry-eyebrow">무료 첫 해석 · {at + 1} / {segments.length}</p>
      <h2 ref={heading} tabIndex={-1}>{current.label}</h2>
      <div className="entry-reading-body" dangerouslySetInnerHTML={{ __html: current.html }} />
      {current.source && <details className="entry-evidence"><summary>이 해석은 무엇을 보고 나왔나요?</summary>
        <ServerText html={current.source} /></details>}
      {current.response_mode === "experience" && !Object.prototype.hasOwnProperty.call(answers, current.stage) &&
        <div className="entry-response"><p>{current.question}</p>
          {/* 누르는 것은 손님입니다 — 손님은 합쇼체로 말합니다 (.\dev.ps1 buttons) */}
          <div><button onClick={() => answer(true)}>겪은 일과 가깝습니다</button>
            <button onClick={() => answer(false)}>제 경험과 다릅니다</button></div>
          <button className="entry-text-button" onClick={() => answer(null)}>잘 모르겠습니다</button>
        </div>}
      {answers[current.stage] !== undefined && answers[current.stage] !== null &&
        <p className="entry-reply" role="status">{answers[current.stage] ? current.yes : current.no}</p>}
      <button className="btn" onClick={next}>{current.next_label || (at === segments.length - 1 ? "첫 해석 정리하기" : "다음 장 읽기")}</button>
    </article>
  </section>;
}
