"use client";

/**
 * 내 자료 · 문의 — 손님이 제품 안에서 쓸 수 있는 권리와 창구.
 *
 * ★ 왜 한 상자에 두는가
 *   둘 다 「내 서재」에서 **나에 대한 것**을 다루는 자리입니다.
 *   열람·삭제는 법이 준 권리(개인정보보호법 제35·36조)이고,
 *   문의는 그 권리를 쓰다 막혔을 때 갈 곳입니다.
 *
 * ★ 지우는 것은 되돌릴 수 없어 **두 걸음**입니다.
 *   먼저 무엇이 지워지고 무엇이 남는지 서버에게 물어 보여 주고,
 *   손님이 한 번 더 누르면 지웁니다 (§6-6).
 */

import { useCallback, useEffect, useState } from "react";
import { API_BASE } from "@/lib/api";

interface Plan {
  removes: Record<string, number>;
  keeps: { 거래기록?: number; 왜: string } & Record<string, unknown>;
}
interface Thread {
  id: string; topic: string; body: string; status: string;
  at: string; reply: string; replied_at: string;
}
interface Topic { id: string; say: string }

async function jsonOf(r: Response) {
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d?.detail ?? "잘 안 되었소.");
  return d;
}

export default function MyData({ sessionId }: { sessionId: string }) {
  /* ── 지우기 ─────────────────────────────────────────── */
  const [plan, setPlan] = useState<Plan | null>(null);
  const [gone, setGone] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const forget = useCallback(async (confirm: boolean) => {
    setBusy(true);
    setErr(null);
    try {
      const d = await jsonOf(await fetch(`${API_BASE}/v1/me/forget`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, confirm }),
      }));
      setPlan(d.plan);
      if (d.done) setGone(true);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "지우지 못했소.");
    } finally {
      setBusy(false);
    }
  }, [sessionId]);

  /* 내려받기 — 브라우저가 파일로 받습니다. */
  const download = useCallback(async () => {
    setBusy(true);
    setErr(null);
    try {
      const d = await jsonOf(await fetch(
        `${API_BASE}/v1/me/data?session_id=${encodeURIComponent(sessionId)}`));
      const blob = new Blob([JSON.stringify(d, null, 2)],
                            { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "성신당-내자료.json";
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "내려받지 못했소.");
    } finally {
      setBusy(false);
    }
  }, [sessionId]);

  /* ── 문의 ───────────────────────────────────────────── */
  const [topics, setTopics] = useState<Topic[]>([]);
  const [topic, setTopic] = useState("");
  const [body, setBody] = useState("");
  const [threads, setThreads] = useState<Thread[]>([]);
  const [sent, setSent] = useState(false);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let alive = true;
    fetch(`${API_BASE}/v1/support/topics`)
      .then(jsonOf).then((d) => { if (alive) setTopics(d.topics); })
      .catch(() => { /* 갈래를 못 받아도 아래 내역은 보입니다 */ });
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    if (!sessionId) return;
    let alive = true;
    fetch(`${API_BASE}/v1/support/mine?session_id=${encodeURIComponent(sessionId)}`)
      .then(jsonOf).then((d) => { if (alive) setThreads(d.threads ?? []); })
      .catch(() => { /* 조용히 둡니다 — 문의가 없는 것과 구별이 안 됩니다 */ });
    return () => { alive = false; };
  }, [sessionId, reload]);

  const ask = useCallback(async () => {
    setBusy(true);
    setErr(null);
    try {
      await jsonOf(await fetch(`${API_BASE}/v1/support`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, topic, body }),
      }));
      setBody("");
      setSent(true);
      setReload((n) => n + 1);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "보내지 못했소.");
    } finally {
      setBusy(false);
    }
  }, [sessionId, topic, body]);

  const topicSay = (id: string) =>
    topics.find((t) => t.id === id)?.say ?? id;

  return (
    <section className="mydata" aria-labelledby="mydata-h">
      <h2 id="mydata-h">내 자료와 문의</h2>

      {err && <p className="warn" role="alert">{err}</p>}

      {/* ── 문의 ─────────────────────────────────────── */}
      <div className="mdbox">
        <h3>이 집에 말 걸기</h3>
        <p className="sm">
          답은 여기서 보시오. 연락처는 안 묻소 — 안 받아도 될 것을
          받지 않으려는 것이오.
        </p>
        <div className="mdtopics" role="group" aria-label="무엇에 대한 말이오">
          {topics.map((t) => (
            <button key={t.id} type="button"
                    className={topic === t.id ? "on" : ""}
                    aria-pressed={topic === t.id}
                    onClick={() => setTopic(t.id)}>{t.say}</button>
          ))}
        </div>
        <label className="mdlabel" htmlFor="md-body">무슨 일이오</label>
        <textarea id="md-body" className="fld" rows={4} maxLength={1000}
                  value={body} onChange={(e) => setBody(e.target.value)}
                  placeholder="겪으신 일을 적어 주시오." />
        <p className="sm">{body.length} / 1000자</p>
        <button className="btn" disabled={busy || !topic || body.trim().length < 5}
                onClick={() => void ask()}>
          {busy ? "보내는 중…" : "문의를 보내겠습니다"}
        </button>
        {sent && <p role="status">받았소. 답이 오면 아래에 뜨오.</p>}

        {!!threads.length && (
          <ul className="mdthreads">
            {threads.map((t) => (
              <li key={t.id}>
                <b>{topicSay(t.topic)}</b>
                <small>{t.status === "closed" ? "답했소" : "보는 중"}</small>
                <p className="mdask">{t.body}</p>
                {t.reply && <p className="mdreply">{t.reply}</p>}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* ── 열람 · 삭제 ──────────────────────────────── */}
      <div className="mdbox">
        <h3>맡긴 것 되가져가기</h3>
        <p className="sm">
          이 집이 그대에 대해 들고 있는 것을 받아 가거나 지울 수 있소.
          생년월일시는 여기 없소 — 그건 그대 브라우저에만 있고 셈할 때만
          받아 쓰오.
        </p>
        <div className="mdrow">
          <button className="btn gh" disabled={busy} onClick={() => void download()}>
            내 자료를 내려받겠습니다
          </button>
          {!gone && (
            <button className="btn gh danger" disabled={busy}
                    onClick={() => void forget(false)}>
              지우면 어떻게 되는지 보겠습니다
            </button>
          )}
        </div>

        {plan && !gone && (
          <div className="mdplan" role="group" aria-label="지우면 어떻게 되는가">
            <p><b>지우는 것</b>{" "}
              {Object.entries(plan.removes)
                .map(([k, v]) => `${k} ${v}`).join(" · ")}</p>
            <p><b>남는 것</b> {String(plan.keeps["왜"])}</p>
            <button className="btn danger" disabled={busy}
                    onClick={() => void forget(true)}>
              {busy ? "지우는 중…" : "그래도 지우겠습니다"}
            </button>
          </div>
        )}
        {gone && (
          <p className="mddone" role="status">
            지웠소. 이 브라우저와 이어진 자리는 더 없소.
          </p>
        )}
      </div>
    </section>
  );
}
