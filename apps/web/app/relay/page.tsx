"use client";

/**
 * @screen h1
 * H · 이어지다 — h1 릴레이
 *
 * ★ 브레이크 (CLAUDE.md 절대 규칙 4)
 *     세션당 릴레이 2명 — **서버가 판정합니다.** 화면에서 우회하지 마세요.
 *     거절한 캐릭터는 다시 권하지 않습니다.
 *     무거운 자리 다음에는 무료 캐릭터를 강제로 앞에 붙입니다.
 * ★ 근거를 반드시 함께 보여줍니다. 강매로 읽히지 않게. (docs/08 §3)
 */
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Shell from "@/components/Shell";
import Scene from "@/components/scene/Scene";
import { Narration, Say } from "@/components/Narration";
import { api } from "@/lib/api";
import { LENS_BY_ID } from "@/lib/lenses";
import { useSession } from "@/lib/store";
import type { RelayResponse } from "@shared/chart";

export default function RelayPage() {
  const router = useRouter();
  const s = useSession();
  const [data, setData] = useState<RelayResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const chartId = s.chartId;
  const sessionId = s.sessionId;
  const read = s.read;
  const skipped = s.skipped;
  const cur = s.cur;

  const load = useCallback(() => {
    if (!chartId) return;
    api
      .relay({
        chart_id: chartId, session_id: sessionId,
        read, skipped, last_lens: cur,
      })
      .then(setData)
      .catch(() => setErr("이을 자리를 찾지 못했소."));
  }, [chartId, sessionId, read, skipped, cur]);

  useEffect(() => { load(); }, [load]);

  const go = async (lensId: string) => {
    // 브레이크 카운터는 서버가 셉니다.
    // 이 호출을 빠뜨리면 세션 2명 제한이 헐거워집니다.
    const r = await api.consumeRelay(sessionId);
    s.set({ cur: lensId, relayUsed: r.used });
    s.markRead(lensId);
    router.push("/report/" + lensId);
  };

  if (!chartId) {
    return (
      <Shell title="이어지다">
        <Narration lines={["먼저 글자를 세워야 하오."]} />
        <button className="btn mt" onClick={() => router.push("/")}>글자를 세운다</button>
      </Shell>
    );
  }

  return (
    <Shell title="이어지다" legal>
      <Scene id="handle" />
      {err && <Say who="도령">{err}</Say>}

      {data?.blocked ? (
        <div className="warn">
          <p>{data.block_reason}</p>
          <p className="sm">
            한 자리에서 여러 사람을 몰아 듣는다고 더 알게 되지 않소.
            오늘 들은 것을 먼저 두고 보시오.
          </p>
          <button className="btn gh mt" onClick={() => router.push("/lobby")}>진열대로</button>
        </div>
      ) : (
        <>
          {/* 정서 안전망 — 무거운 자리 다음엔 무료 캐릭터가 먼저 */}
          {data?.forced.map((id) => {
            const l = LENS_BY_ID[id];
            return (
              <div className="dz" key={id} style={{ borderColor: "var(--teal)" }}>
                <div className="k">값 없이</div>
                <p style={{ fontFamily: "var(--serif)", fontSize: 18, color: l?.color }}>
                  {l?.name}
                </p>
                <p className="sm">{l?.quote}</p>
                <button className="btn gh mt" onClick={() => void go(id)}>
                  차 한 잔 하고 간다
                </button>
              </div>
            );
          })}

          {data && data.recommend.length > 0 ? (
            <>
              <Narration lines={["도령이 옆자리를 가리켰다."]} />
              {data.recommend.map((r) => {
                const l = LENS_BY_ID[r.lens_id];
                return (
                  <div className="dz" key={r.lens_id}>
                    <p style={{ fontFamily: "var(--serif)", fontSize: 18, color: l?.color }}>
                      {r.name}
                    </p>
                    <span className="src">근거 · {r.reason}</span>
                    {r.quote && <p className="sm" style={{ marginTop: 6 }}>{r.quote}</p>}
                    <div className="og c2 mt">
                      <button
                        className="op"
                        disabled={!r.released}
                        onClick={() => void go(r.lens_id)}
                      >
                        <b>{r.released ? "듣는다" : "아직 자리에 없소"}</b>
                        <span>{r.price ? r.price.toLocaleString() + "원" : "값 없이"}</span>
                      </button>
                      <button
                        className="op"
                        onClick={() => { s.markSkipped(r.lens_id); }}
                      >
                        <b>나중에</b>
                        <span>다시 권하지 않소</span>
                      </button>
                    </div>
                  </div>
                );
              })}
              <p className="sm mt">
                이번 자리에서 이을 수 있는 사람은 {data.breaks.per_session_relay}명까지요.
                지금까지 {s.relayUsed}명.
              </p>
            </>
          ) : (
            data && <Narration lines={["오늘 이을 자리는 없소."]} />
          )}
        </>
      )}

      <button className="btn gh mt" onClick={() => router.push("/lobby")}>진열대로</button>
    </Shell>
  );
}
