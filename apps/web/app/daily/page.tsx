"use client";

/**
 * @screen g1 g2 g3
 * G · 다시 오다 — g1 오늘의 운세 · g2 회고 · g3 차 한 잔
 *
 * ★ 하루 3회 넘게 오면 만류합니다. 브레이크는 매출보다 앞섭니다.
 *   (CLAUDE.md 절대 규칙 4)
 */
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Shell from "@/components/Shell";
import Scene from "@/components/scene/Scene";
import { Narration, Say } from "@/components/Narration";
import { api } from "@/lib/api";
import { useSession } from "@/lib/store";
import { useScreen } from "@/lib/track";
import type { DailyResponse } from "@shared/chart";

const VISIT_WARN_AT = 3;

export default function DailyPage() {
  useScreen("daily");
  const router = useRouter();
  const s = useSession();
  const [data, setData] = useState<DailyResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    s.set({ visits: s.visits + 1 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!s.chartId) return;
    let alive = true;
    api.daily(s.chartId)
      .then((d) => alive && setData(d))
      .catch(() => alive && setErr("일진을 셈하지 못했소."));
    return () => { alive = false; };
  }, [s.chartId]);

  if (!s.chartId) {
    return (
      <Shell title="오늘의 일진">
        <Narration lines={["먼저 글자를 세워야 하오."]} />
        <button className="btn mt" onClick={() => router.push("/")}>글자를 세운다</button>
      </Shell>
    );
  }

  return (
    <Shell title="오늘의 일진">
      <Scene id="banner" />
      {err && <Say who="도령">{err}</Say>}

      {/* 하루 3회 접속 시 만류 — 늘리지 마세요 */}
      {s.visits >= VISIT_WARN_AT && (
        <div className="warn">
          <p>오늘 벌써 {s.visits}번째요.</p>
          <p className="sm">
            운은 하루에 여러 번 바뀌지 않소. 자꾸 들여다본다고 달라질 것도 아니오.
            오늘은 그만 보시고, 내일 오시오.
          </p>
        </div>
      )}

      {data && (
        <>
          <div className="dz">
            <div className="k">{data.date}</div>
            <p style={{ fontFamily: "var(--serif)", fontSize: 26, color: "var(--c)" }}>
              {data.gz}
            </p>
            <p className="sm">{data.relation} 날</p>
          </div>
          <span className="src">근거 · {data.source}</span>
          <div className="bar" style={{ margin: "12px 0" }}>
            <i style={{ ["--w" as string]: `${data.score}%` }} />
          </div>
          <p className="sm">오늘 기운 {data.score} / 100 — 적중률이 아니라 배치 점수요.</p>
          <Say who="도령">{data.text}</Say>
          {data.notes.map((n) => <p className="sm" key={n}>· {n}</p>)}
        </>
      )}

      {/* g2 회고 — statement_log 가 쌓이기 전에는 지어내지 않는다 */}
      <div className="lab mt">g2 · 되짚기</div>
      <p className="sm">
        여섯 달 전 그대가 &quot;그렇다&quot;고 한 문장을 여기 다시 꺼내오.
        아직 쌓인 것이 없어 비워 두었소.
      </p>

      {/* g3 차 한 잔 */}
      <div className="lab mt">g3 · 차 한 잔</div>
      <Scene id="tea" />
      <p className="sm">
        용신에 맞는 차를 내오. 리포트를 열면 함께 나오오.
      </p>

      <button className="btn gh mt" onClick={() => router.push("/lobby")}>진열대로</button>
    </Shell>
  );
}
