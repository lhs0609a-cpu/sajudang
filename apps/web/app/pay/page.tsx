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
import { track, useScreen } from "@/lib/track";
import { openCheckout } from "@/lib/toss";
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

  useScreen(step);

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

  /*
   * 결제창에서 돌아왔다 — 토스가 ?toss=ok&paymentKey=… 로 되돌려 보냅니다.
   *
   * 결제창은 페이지를 통째로 떠났다 옵니다. 그래서 승인은 여기서 합니다.
   * 금액은 안 보냅니다 — 서버가 주문에 적어 둔 값을 씁니다.
   */
  const tossBack = params.get("toss");
  const [settling, setSettling] = useState(tossBack === "ok");
  useEffect(() => {
    if (tossBack !== "ok") return;
    const orderId = params.get("order") ?? params.get("orderId");
    const paymentKey = params.get("paymentKey");
    if (!orderId || !paymentKey) {
      setErr("결제 정보가 모자라오. 값은 빠져나가지 않았소.");
      setSettling(false);
      return;
    }
    let alive = true;
    api
      .payConfirm({ session_id: s.sessionId, order_id: orderId,
                    payment_key: paymentKey })
      .then((r) => {
        if (!alive) return;
        s.set({
          tier: r.tier as Tier, paid: true,
          seals: s.seals.includes(r.seal) ? s.seals : [...s.seals, r.seal],
        });
        track("pay_done", "d2");
        router.replace("/pay?step=d3");
      })
      .catch((e) => {
        if (!alive) return;
        track("pay_fail", "d2");
        setErr(e instanceof ApiError ? e.message : "결제 승인에 실패했소.");
        setSettling(false);
      });
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tossBack]);

  /* 결제창에서 물러섰다 */
  useEffect(() => {
    if (tossBack !== "fail") return;
    track("pay_fail", "d2");
    setErr(params.get("message") ?? "결제가 중단되었소. 값은 빠져나가지 않았소.");
  }, [tossBack, params]);

  /* d2 · 주문 만들기 — 금액·상한은 서버가 판정한다 */
  useEffect(() => {
    if (step !== "d2" || !s.chartId || order || tossBack) return;
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

    /* 결제창에서 막 돌아왔다 — 승인이 끝날 때까지 아무것도 누르지 못하게 */
    if (settling) {
      return (
        <Shell title="값을 치르다" legal>
          <Scene id="coin" />
          <Narration lines={["값이 건너가는 중이오.", "잠시만 기다리시오."]} />
          <p className="sm mt" style={{ textAlign: "center" }}>
            창을 닫지 마시오.
          </p>
        </Shell>
      );
    }

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
                  track("pay_start", "d2");
                  try {
                    /*
                     * 토스 결제창을 띄웁니다. 여기서 페이지를 떠났다가
                     * successUrl 로 돌아오고, 승인은 위의 effect 가 합니다.
                     *
                     * customerKey 에 sessionId 를 씁니다 — 익명 난수입니다.
                     * 이름·생년월일을 넣으면 PG 로 넘어갑니다. 넣지 마세요.
                     */
                    if (!order.client_key) {
                      throw new Error("결제 열쇠가 없소.");
                    }
                    await openCheckout({
                      clientKey: order.client_key,
                      orderId: order.order_id,
                      amount: order.amount,
                      orderName: tier?.name ?? "사주당",
                      customerKey: s.sessionId,
                    });
                    // 여기 아래는 보통 안 옵니다 — 결제창이 페이지를 넘깁니다.
                  } catch (e) {
                    track("pay_fail", "d2");
                    setErr(e instanceof Error ? e.message : "결제에 실패했소.");
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
            onClick={() => { setPick(t.id); setOrder(null); track("tier_pick", "d1"); }}
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
