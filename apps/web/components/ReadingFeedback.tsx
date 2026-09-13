"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useSession } from "@/lib/store";

type Answer = "yes" | "partly" | "no";
type Dimension = "clarity" | "recognition" | "comfort" | "usefulness";
const questions: [Dimension, string][] = [
  ["clarity", "뜻을 쉽게 이해할 수 있었나요?"],
  ["recognition", "실제 내 모습이나 경험이 떠올랐나요?"],
  ["comfort", "마음을 이해받았다고 느꼈나요?"],
  ["usefulness", "읽고 나서 해볼 일이 분명해졌나요?"],
];
const options: [Answer, string][] = [["yes", "그렇다"], ["partly", "일부 그렇다"], ["no", "아니다"]];

export default function ReadingFeedback({ lensId, version, resultKey, scope }: { lensId: string; version: number; resultKey:string; scope:'book'|'focus' }) {
  const s = useSession();
  const [answers, setAnswers] = useState<Partial<Record<Dimension, Answer>>>({});
  const [status, setStatus] = useState<"idle" | "sending" | "done">("idle");
  const [error, setError] = useState("");
  const [value,setValue]=useState<number|null>(null);
  if (!s.chartId) return null;
  return <details className="reading-feedback noprint">
    <summary>이 글이 어땠는지 알려주기 · 선택</summary>
    <p className="sm">이름·생년월일·상담 이유를 저장하지 않고, 아래 평가만 90일간 보관합니다. 같은 풀이의 평가는 새 답변으로 바뀝니다.</p>
    {status === "done" ? <p role="status">알려주셔서 고맙습니다. 더 이해하기 쉽고 도움이 되는 글로 다듬겠습니다.</p> :
      <form onSubmit={async event => {
        event.preventDefault();
        if (status === "sending" || !s.chartId || questions.some(([key]) => !answers[key])) return;
        setStatus("sending"); setError("");
        try {
          await api.readingEvaluation({ chart_id: s.chartId, session_id: s.sessionId, lens_id: lensId,
            version, concern:s.concern, scope, result_key:resultKey, value_for_money:value,
            ...answers as Record<Dimension, Answer> });
          setStatus("done");
        } catch (err) { setStatus("idle"); setError(err instanceof ApiError ? err.message : "평가를 보내지 못했습니다. 잠시 뒤 다시 시도해 주세요."); }
      }}>
        {questions.map(([key, label]) => <fieldset key={key} disabled={status === "sending"}>
          <legend>{label}</legend>
          <div className="reading-options">{options.map(([value, text]) => <label key={value}>
            <input type="radio" name={`feedback-${key}`} value={value} checked={answers[key] === value}
              onChange={() => setAnswers(prev => ({...prev, [key]: value}))} />{text}
          </label>)}</div>
        </fieldset>)}
        {<fieldset disabled={status==='sending'}><legend>이 풀이를 구매했다면, 가격에 비해 얻은 내용은 어땠나요? · 선택</legend>
          <p className="sm">1 매우 아쉬웠다 · 3 보통 · 5 충분히 값어치 있었다</p>
          <div className="ease-options">{[1,2,3,4,5].map(n=><label key={n}><input type="radio" name="value-for-money" checked={value===n} onChange={()=>setValue(n)}/>{n}</label>)}</div>
          {value!==null&&<button type="button" className="btn gh" onClick={()=>setValue(null)}>가격 대비 답변 지우기</button>}
        </fieldset>}
        {error && <p role="alert">{error}</p>}
        <button className="btn gh" type="submit" disabled={status === "sending" || questions.some(([key]) => !answers[key])}>
          {status === "sending" ? "보내는 중…" : "내 평가 보내기"}
        </button>
      </form>}
  </details>;
}
