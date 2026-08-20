"use client";

/**
 * @screen d0 d1 d2 d3
 * D · 값을 치르다 — d0 무료 6단 · d1 어디까지 · d2 결제 · d3 완료
 *
 * ★ 금액과 하루 2건 상한은 **서버가 정합니다.** 여기서 계산하지 마세요.
 *   (CLAUDE.md 절대 규칙 4)
 * ★ PG 키가 없으면 결제창을 띄우지 않고 그 사실을 그대로 알립니다.
 *   성공한 척하지 않습니다.
 */
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Shell from "@/components/Shell";
import Scene from "@/components/scene/Scene";
import { Narration, Say } from "@/components/Narration";
import { api, ApiError } from "@/lib/api";
import { LENS_BY_ID } from "@/lib/lenses";
import { TIERS, useSession, type Tier } from "@/lib/store";
import type { ReportResponse } from "@shared/chart";

interface Order {
  order_id: string;
  amount: number;
  tier: string;
  client_key: string | null;
  enabled: boolean;
  refund_notice: string;
  purchases_today: number;
  per_day_limit: number;
}

function PayInner() {
  const router = useRouter();
  const params = useSearchParams();
  const s = useSession();
  const step = params.get("step") ?? "d1";
  const lens = LENS_BY_ID[s.cur];
  const charName = lens?.name ?? "도령";

  const [free, setFree] = useState<ReportResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [pick, setPick] = useState<Tier>("all");
  const [order, setOrder] = useState<Order | null>(null);
  const [busy, setBusy] = useState(false);

  /* d0 · 무료 구간 */
  useEffect(() => {
    if (step !== "d0" || !s.chartId || free) return;
    let alive = true;
    api
      .report({
        chart_id: s.chartId, lens_id: s.cur, tier: "free",
        concern: s.concern, axis4: s.axis4,
      })
      .then((r) => { if (alive) setFree(r); })
      .catch((e) => {
        if (alive) setErr(e instanceof ApiError ? e.message : "펴지 못했소.");
      });
    return () => { alive = false; };
  }, [step, s.chartId, s.cur, s.concern, s.axis4, free]);

  /* d2 · 주문 만들기 — 금액·상한은 서버가 판정한다 */
  useEffect(() => {
    if (step !== "d2" || !s.chartId || order) return;
    let alive = true;
    setErr(null);
    api
      .payPrepare({
        session_id: s.sessionId, chart_id: s.chartId,
        lens_id: s.cur, tier: pick, concern: s.concern,
      })
      .then((o) => { if (alive) setOrder(o); })
      .catch((e) => {
        if (alive) setErr(e instanceof ApiError ? e.message : "값을 매기지 못했소.");
      });
    return () => { alive = false; };
  }, [step, s.chartId, s.sessionId, s.cur, s.concern, pick, order]);

  if (step === "d0") {
    return (
      <Shell title="값 없이 한 겹 더">
        <Scene id="oldpaper" />
        {err && <Say who={charName}>{err}</Say>}
        {free?.cuts.map((c) => (
          <div className="blk in" key={c.id}>
            <div className="lab">{c.title}</div>
            <span className="src">근거 · {c.source}</span>
            <div dangerouslySetInnerHTML={{ __html: c.html }} />
          </div>
        ))}
        {free && (
          <>
            <Narration lines={[charName + "가 붓을 내려놓았다."]} />
            <Say
              who={charName}
              html={"여기까지가 값 없이 하는 얘기요.<br><b>왜</b> 그런지와 <b>언제</b> 그런지는 아직 안 했소."}
            />
            <button className="btn mt" onClick={() => router.push("/pay?step=d1")}>
              어디까지 볼지 고른다
            </button>
            <button className="btn gh" onClick={() => router.push("/lobby")}>
              오늘은 여기까지
            </button>
          </>
        )}
      </Shell>
    );
  }

  /* d2 · 결제 */
  if (step === "d2") {
    const tier = TIERS.find((t) => t.id === pick);
    return (
      <Shell title="값을 치르다" legal>
        <Scene id="coin" />

        {err && (
          <div className="warn">
            <p>{err}</p>
            <button className="btn gh mt" onClick={() => router.push("/lobby")}>
              진열대로
            </button>
          </div>
        )}

        {order && (
          <>
            <div className="dz">
              <div className="k">{tier?.name}</div>
              <p>{order.amount.toLocaleString()}원</p>
              <p className="sm">{tier?.desc}</p>
            </div>
            <p className="sm">오늘 치른 값 {order.purchases_today} / {order.per_day_limit}건</p>
            <p className="sm">{order.refund_notice}</p>

            {order.enabled ? (
              <button
                className="btn mt"
                disabled={busy}
                onClick={async () => {
                  setBusy(true);
                  setErr(null);
                  try {
                    // 실제 결제창은 토스 SDK 가 띄웁니다. SDK 가 돌려준
                    // paymentKey 를 서버로 넘겨 승인합니다.
                    const key = window.prompt("토스 결제창에서 받은 paymentKey");
                    if (!key) return;
                    const r = await api.payConfirm({
                      session_id: s.sessionId,
                      order_id: order.order_id,
                      payment_key: key,
                    });
                    s.set({
                      tier: r.tier as Tier, paid: true,
                      seals: s.seals.includes(r.seal) ? s.seals : [...s.seals, r.seal],
                    });
                    router.push("/pay?step=d3");
                  } catch (e) {
                    setErr(e instanceof ApiError ? e.message : "결제에 실패했소.");
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                값을 치른다
              </button>
            ) : (
              <div className="warn">
                <p>아직 값을 받을 수 없소.</p>
                <p className="sm">
                  결제가 연결되지 않았습니다 (TOSS_CLIENT_KEY 미설정).
                  연결 전까지 유료 구간은 열리지 않습니다.
                </p>
              </div>
            )}
            <button className="btn gh" onClick={() => router.push("/pay?step=d1")}>
              다시 고른다
            </button>
          </>
        )}
      </Shell>
    );
  }

  /* d3 · 완료 */
  if (step === "d3") {
    return (
      <Shell title="열렸소">
        <Scene id="untie" />
        <Narration lines={["붉은 끈이 풀렸다."]} />
        <Say who={charName}>이제 나머지를 보시오.</Say>
        <button className="btn mt" onClick={() => router.push("/report/" + s.cur)}>
          읽으러 간다
        </button>
      </Shell>
    );
  }

  /* d1 · 어디까지 */
  return (
    <Shell title="어디까지 볼지">
      <Scene id="tray" />
      <Narration lines={["목패 셋이 상 위에 놓였다."]} />
      <div className="og">
        {TIERS.map((t) => (
          <button
            key={t.id}
            className={"op " + (pick === t.id ? "on" : "")}
            onClick={() => { setPick(t.id); setOrder(null); }}
          >
            <b>{t.name} · {t.price}</b>
            <span>{t.desc}</span>
          </button>
        ))}
      </div>
      <button className="btn mt" onClick={() => router.push("/pay?step=d2")}>
        이걸로 하겠소
      </button>
      <button className="btn gh" onClick={() => router.push("/pay?step=d0")}>
        값 없이 볼 수 있는 것부터
      </button>
    </Shell>
  );
}

export default function PayPage() {
  return (
    <Suspense fallback={<Shell title="값을 치르다"><p className="sm">…</p></Shell>}>
      <PayInner />
    </Suspense>
  );
}
