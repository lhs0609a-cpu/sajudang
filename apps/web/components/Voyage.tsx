"use client";

/**
 * 「내 항해」 — 유저 항해 관제탑 (SHIP OS §18).
 *
 * ★ 손님은 개발 상태가 아니라 **자기 길**을 봅니다.
 *   지금 어디인지 · 다음 한 걸음 · 잠긴 까닭 · 쌓인 것.
 *
 * ★ 다음 행동은 **하나만** 냅니다.
 *   이 집은 「이번 주 한 가지」 컷에 할 일을 둘 얹었다가, 둘이면
 *   손님이 하나도 안 한다는 것을 배웠습니다. 여기도 같습니다.
 *
 * ★ 칸의 상태는 서버가 정합니다 (`GET /v1/journey`).
 *   값이 걸린 칸(깊은 해석)은 화면 말을 안 듣고 치른 주문만 봅니다 —
 *   화면이 정하면 localStorage 를 고쳐 연 것으로 만들 수 있습니다.
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import { API_BASE } from "@/lib/api";

interface Step { id: string; title: string; say: string; state: "done" | "now" | "lock" }
interface Journey {
  steps: Step[]; done: number; total: number; percent: number;
  next: { say: string; href: string } | null;
  kept: { readings: number; seals: number; subscribed: boolean };
}

const MARK: Record<Step["state"], string> = { done: "✓", now: "→", lock: "·" };

export default function Voyage({
  sessionId, chartId, readFree,
}: { sessionId: string; chartId?: string | null; readFree?: boolean }) {
  const [j, setJ] = useState<Journey | null>(null);
  const [err, setErr] = useState(false);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    if (!sessionId) return;
    let alive = true;
    setErr(false);
    const q = new URLSearchParams({ session_id: sessionId });
    if (chartId) q.set("chart_id", chartId);
    if (readFree) q.set("read_free", "true");
    fetch(`${API_BASE}/v1/journey?${q.toString()}`, { cache: "no-store" })
      .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
      .then((d) => { if (alive) setJ(d); })
      .catch(() => { if (alive) setErr(true); });
    return () => { alive = false; };
  }, [sessionId, chartId, readFree, retry]);

  /* 못 불러왔다고 화면을 비우지 않습니다 — 다시 볼 길을 냅니다. */
  if (err) {
    return (
      <section className="voyage" aria-labelledby="voyage-h">
        <h2 id="voyage-h">내 항해</h2>
        <p className="vsay" role="alert">지금 어디까지 왔는지 세지 못했소.</p>
        <button className="btn gh" onClick={() => setRetry((n) => n + 1)}>
          다시 세어 보기
        </button>
      </section>
    );
  }
  if (!j) {
    return (
      <section className="voyage" aria-labelledby="voyage-h">
        <h2 id="voyage-h">내 항해</h2>
        <p className="vsay" role="status">세는 중이오…</p>
      </section>
    );
  }

  return (
    <section className="voyage" aria-labelledby="voyage-h">
      <h2 id="voyage-h">내 항해</h2>
      <p className="vsay">
        일곱 자리 가운데 <b>{j.done}</b>자리를 지나오셨소.
      </p>

      <div className="vbar" role="img"
           aria-label={`전체 ${j.total}자리 중 ${j.done}자리 지남`}>
        <i style={{ width: `${j.percent}%` }} />
      </div>

      <ol>
        {j.steps.map((s) => (
          <li key={s.id} className={s.state}>
            <i className="vmark" aria-hidden="true">{MARK[s.state]}</i>
            <b>{s.title}</b>
            <small>
              {s.state === "done" ? "지났소" : s.state === "now" ? "지금 여기" : "아직"}
            </small>
          </li>
        ))}
      </ol>

      {j.next ? (
        <div className="vnext">
          <b>다음 한 걸음</b>
          <p>{j.next.say}</p>
          <Link className="btn" href={j.next.href}>하러 가겠습니다</Link>
        </div>
      ) : (
        <div className="vnext">
          <b>다 지나오셨소</b>
          <p>이제는 때를 두고 다시 보는 자리요.</p>
        </div>
      )}
    </section>
  );
}
