"use client";

import { useState } from "react";
import CompanionCat from "@/components/CompanionCat";
import { track } from "@/lib/track";

export interface Practice {
  id: string; version: number; source_kind: string; source: string;
  title: string; scene: string; action: string;
}

export default function PracticeCard({ practice }: { practice: Practice }) {
  const [status, setStatus] = useState("");
  const [saved, setSaved] = useState(false);
  return <section className="conversion-card" aria-label="오늘 해볼 행동">
    <p className="conversion-kicker">오늘 해볼 행동 하나 · 무료</p>
    <h2>{practice.title}</h2><p>{practice.scene}</p>
    <p className="conversion-lead">{practice.action}</p>
    <p className="conversion-note">{practice.source}</p>
    <button className="btn gh" onClick={async () => {
      try {
        await navigator.clipboard.writeText(`${practice.title}\n${practice.action}\n${practice.source}`);
        setSaved(true); setStatus("행동 문장을 복사했어요. 원하는 메모에 붙여넣어 보세요.");
        track("practice_saved", "d0");
      } catch { setStatus("자동으로 복사하지 못했어요. 위 문장을 길게 눌러 복사해 주세요."); }
    }}>행동 문장 복사하기</button>
    <CompanionCat state={saved ? "saved" : "rest"} message={saved ? "발도장 꾹. 작은 행동 하나면 충분해요." : "지금 상황과 맞지 않으면 건너뛰어도 괜찮아요."} />
    <p className="conversion-note" role="status">{status}</p>
  </section>;
}
