"use client";

/**
 * 훅 5단 — 한 단씩 열리고, 응답하면 다음이 열린다.
 *
 * ★ html 은 서버가 렌더한 것입니다. 여기서 문장을 만들지 않습니다.
 * ★ 공감률은 서버가 shown=true 를 줄 때만 그립니다. 100건 미만이면 안 그립니다.
 */
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { HookSegment } from "@shared/chart";

function Agreement({ statementId }: { statementId: string }) {
  const [data, setData] = useState<{ shown: boolean; rate?: number; total?: number } | null>(null);
  useEffect(() => {
    let alive = true;
    api.agreement(statementId).then((d) => alive && setData(d)).catch(() => {});
    return () => { alive = false; };
  }, [statementId]);

  // 응답 100건 미만 → 아무것도 그리지 않는다 (숫자를 지어내지 않는다)
  if (!data?.shown || data.rate == null) return null;
  return (
    <div className="agr">
      <span>이 문장에</span>
      <div className="bar"><i style={{ ["--w" as string]: `${data.rate}%` }} /></div>
      <b>{data.rate}%</b>
      <span>가 &quot;그렇다&quot; · {data.total?.toLocaleString()}명</span>
    </div>
  );
}

export default function HookSegments({
  segments, chartId, lensId, concern, charName, onDone,
}: {
  segments: HookSegment[];
  chartId: string;
  lensId: string;
  concern: string;
  charName: string;
  onDone?: () => void;
}) {
  const [open, setOpen] = useState(1);
  const [replies, setReplies] = useState<Record<number, string>>({});

  const vote = async (i: number, yes: boolean) => {
    const seg = segments[i];
    setReplies((r) => ({ ...r, [i]: yes ? seg.yes : seg.no }));
    try {
      await api.feedback({
        statement_id: seg.statement_id, chart_id: chartId,
        answer: yes ? 1 : 0, stage: seg.stage, lens_id: lensId, concern,
      });
    } catch {
      /* 기록 실패가 읽기를 막아서는 안 된다 */
    }
    setTimeout(() => {
      setOpen((n) => Math.max(n, i + 2));
      if (i + 1 >= segments.length) onDone?.();
    }, 660);
  };

  return (
    <>
      {segments.slice(0, open).map((seg, i) => (
        <div className="blk in" key={seg.statement_id}>
          {seg.label && <div className="lab">{seg.label}</div>}
          {seg.source && <span className="src">근거 · {seg.source}</span>}
          <div dangerouslySetInnerHTML={{ __html: seg.html }} />
          {seg.source && <Agreement statementId={seg.statement_id} />}

          {replies[i] === undefined ? (
            <div className="vt">
              <button onClick={() => vote(i, true)}>그렇소</button>
              <button onClick={() => vote(i, false)}>아니오</button>
            </div>
          ) : (
            <div className="react on">
              <div className="say"><small>{charName}</small>{replies[i]}</div>
            </div>
          )}
        </div>
      ))}
    </>
  );
}
