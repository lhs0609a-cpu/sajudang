"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Shell from "@/components/Shell";
import ReadingAnalysis from "@/components/ReadingAnalysis";
import { api, ApiError } from "@/lib/api";
import { useSession } from "@/lib/store";
import type { OmnibusResponse } from "@shared/chart";

export default function OmnibusPage() {
  const s = useSession();
  const [book, setBook] = useState<OmnibusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [retry, setRetry] = useState(0);
  const [extras, setExtras] = useState<Record<string, unknown> | null>(null);
  const identity = `${s.chartId}:${s.concern}:${s.sessionId}`;
  const [seenIdentity, setSeenIdentity] = useState(identity);
  if (seenIdentity !== identity) {
    setSeenIdentity(identity); setExtras(null); setBook(null); setError(null);
  }
  useEffect(() => {
    if (!s.chartId) return;
    let alive = true;
    setBusy(true); setError(null);
    api.omnibus({ chart_id: s.chartId, session_id: s.sessionId, concern: s.concern,
      axis4: s.axis4, display_name: s.name.slice(0, 12), extras })
      .then(value => { if (alive) setBook(value); })
      .catch(err => { if (alive) {
        setBook(null);
        setError(err instanceof ApiError ? err.message : "종합 풀이를 불러오지 못했습니다.");
      } })
      .finally(() => { if (alive) setBusy(false); });
    return () => { alive = false; };
  }, [s.chartId, s.sessionId, s.concern, s.axis4, s.name, extras, retry]);

  return <Shell title="전체 풀이">
    <header className="reading-plan-head">
      <p className="conversion-kicker">사주 전체 풀이</p>
      <h1>흩어진 단서를<br />하나의 이야기로.</h1>
      <p>핵심 해석과 영역별 적용, 지금의 선택을 함께 읽습니다.</p>
    </header>
    {!s.chartId && <p>명식을 먼저 세우면 전체 풀이를 이어서 볼 수 있습니다. <Link href="/">사주 입력하기</Link></p>}
    {busy && <p role="status">{book ? "답변을 반영해 풀이를 다듬고 있습니다." : "명식과 각 영역의 근거를 연결하고 있습니다."}</p>}
    {error && <div role="alert" className="warn"><p>{error}</p>
      <button className="btn" onClick={() => setRetry(v => v + 1)}>다시 불러오기</button>
      <Link className="btn gh" href={`/report/${s.cur}`}>읽던 자리로 돌아가기</Link>
    </div>}
    {book && <>
      <div className="eight" aria-label="계산된 명식">
        {book.head.pillars.map(pillar => <span key={pillar.label} title={pillar.label}>{pillar.gz}</span>)}
      </div>
      {!book.head.hour_known && <p className="sm">시각 미상 · 시주를 제외한 세 기둥으로 읽습니다.</p>}
      <ReadingAnalysis reading={book.reading} busy={busy} onSubmit={value => {
        setBusy(true); setExtras(prev => ({ ...(prev || {}), ...value }));
      }} />
      <section className="reading-plan-section">
        <h2>여러 영역에 이어지는 관계</h2>
        <div dangerouslySetInnerHTML={{ __html: book.consensus.html }} />
        <details><summary>특정 영역에서 먼저 다룬 해석</summary><div dangerouslySetInnerHTML={{ __html: book.split.html }} /></details>
      </section>
      <section className="reading-book-appendix">
        <h2>캐릭터별로 더 읽기</h2>
        <p className="sm">같은 명식의 다른 관점입니다. 앞의 종합 해석과 실제 경험을 함께 대조하며 읽어 보세요.</p>
        {book.chapters.map(chapter => <details key={chapter.lens_id}>
          <summary>{chapter.name} · {chapter.archetype}</summary>
          {chapter.cuts.map(cut => <article key={cut.id} className="blk">
            <h3>{cut.title}</h3><p className="sm">{cut.source}</p>
            <div className="cutbody" dangerouslySetInnerHTML={{ __html: cut.html }} />
          </article>)}
          {chapter.needs_input && <p>이 관점은 추가 상황을 받으면 더 구체적으로 살펴볼 수 있습니다.</p>}
          <Link className="btn gh" href={`/report/${chapter.lens_id}?tab=c2`}>{chapter.name}의 자리에서 읽기</Link>
        </details>)}
      </section>
      <button className="btn gh noprint" onClick={() => window.print()}>종합 풀이 인쇄·PDF로 저장</button>
    </>}
    <Link className="btn gh noprint" href={`/report/${s.cur}`}>읽던 자리로</Link>
  </Shell>;
}
