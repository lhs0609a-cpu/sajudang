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
import { useSession, type Tier } from "@/lib/store";
import { track, useScreen } from "@/lib/track";
import { openCheckout } from "@/lib/toss";
import type { ReportResponse } from "@shared/chart";

/* 목패의 모양은 lib/api.ts 한 곳에만 적습니다 — 여기 또 적으면
   서버가 필드를 늘려도 이 화면만 모릅니다. */
import type { Granted, TierCard } from "@/lib/api";

interface Order {
  order_id: string;
  amount: number;
  tier: string;
  client_key: string | null;
  enabled: boolean;
  refund_notice: string;
  /** 같은 약속을 이 집의 말로. 결제 버튼 **바로 위**에 놓습니다. */
  refund_say: string;
  purchases_today: number;
  per_day_limit: number;
}

/*
 * 무료 구간의 숨 고르는 자리.
 *
 * ★ 8컷 1,592자가 한 번에 쏟아지고 상호작용이 0이었습니다. 훅에서 다섯 번
 *   쌓아 올린 참여가 여기서 끊깁니다. 세 컷마다 한 번, 가볍게 묻습니다.
 *   「글쎄올시다」를 여기에도 둡니다 — 이분법이 공감률을 오염시킵니다.
 */
function Beat({ cut, chartId, lensId, concern, charName }: {
  cut: { id: string; statement_id: string | null };
  chartId: string;
  lensId: string;
  concern: string;
  charName: string;
}) {
  const [said, setSaid] = useState<string | null>(null);
  const answer = async (yes: boolean | null) => {
    setSaid(yes === null ? "그럼 그냥 마저 보시오."
      : yes ? "그럴 게요. 아래를 마저 보시오."
            : "그럼 그 자리는 접어 두겠소.");
    track("free_beat", "d0", { yes: yes === null ? 2 : yes ? 1 : 0 });
    if (!cut.statement_id) return;
    try {
      await api.feedback({
        statement_id: cut.statement_id, chart_id: chartId,
        answer: yes === null ? null : yes ? 1 : 0,
        stage: "free", lens_id: lensId, concern,
      });
    } catch {
      /* 기록 실패가 읽기를 막아서는 안 된다 */
    }
  };
  if (said) {
    return <div className="react on"><div className="say"><small>{charName}</small>{said}</div></div>;
  }
  return (
    <div className="beat">
      <span className="q">…짚이오?</span>
      <div className="vt">
        <button onClick={() => answer(true)}>그렇소</button>
        <button onClick={() => answer(false)}>아니오</button>
      </div>
      <button className="lk vt3" onClick={() => answer(null)}>글쎄올시다</button>
    </div>
  );
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
  /*
   * ★ 기본 선택이 「스무 사람 전부」였습니다.
   *   세 목패의 힘은 가운데가 팔리는 데서 나오는데, 그때 가운데는
   *   **지배당하는 목패**였습니다. 기본값은 지금 읽고 있던 사람이고,
   *   값이 가장 낮고, 다음 결제로 이어지는 문입니다 — 「이 자리 하나」.
   *   값이 없는 캐릭터(청동자)면 서버가 그 목패를 안 주므로,
   *   목패가 오면 첫 장으로 맞춰 둡니다.
   */
  const [pick, setPick] = useState<Tier>("one");
  const [order, setOrder] = useState<Order | null>(null);
  const [busy, setBusy] = useState(false);
  /* 목패 — ★ 값도 분량도 서버가 셉니다. 화면은 받아 적기만 합니다. */
  const [tiers, setTiers] = useState<TierCard[] | null>(null);
  /* 값을 치른 직후 **무엇을 얻었는지**. ★ 서버가 셉니다. */
  const [granted, setGranted] = useState<Granted | null>(null);

  useScreen(step);

  /* 목패 셋 — 서버가 센 값과 분량 */
  useEffect(() => {
    if (!s.chartId || tiers) return;
    if (step !== "d1" && step !== "d2") return;
    let alive = true;
    api
      .payTiers({ chart_id: s.chartId, lens_id: s.cur,
                  concern: s.concern, axis4: s.axis4 })
      .then((r) => {
        if (!alive) return;
        const list = r.tiers as TierCard[];
        setTiers(list);
        // 고른 목패가 이 캐릭터에 없으면(값 없는 캐릭터의 '이 자리 하나')
        // 첫 장으로 물러섭니다. 없는 것을 고른 채로 두지 않습니다.
        if (list.length && !list.some((t) => t.id === pick)) {
          setPick(list[0].id as Tier);
        }
      })
      .catch((e) => { if (alive) setErr(e instanceof ApiError ? e.message : "목패를 펴지 못했소."); });
    return () => { alive = false; };
  }, [step, s.chartId, s.cur, s.concern, s.axis4, tiers]);

  /* d0 · 무료 구간 */
  useEffect(() => {
    if (step !== "d0" || !s.chartId || free) return;
    let alive = true;
    api
      .report({
        chart_id: s.chartId, lens_id: s.cur, tier: "free",
        session_id: s.sessionId, concern: s.concern, axis4: s.axis4,
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
        setGranted(r.granted);
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
    /*
     * ★ 리듬이 여기서 끊기고 있었습니다.
     *
     *   훅은 한 단씩 열리고 응답을 받습니다. 그런데 무료 리포트는 8컷
     *   1,592자를 **한 번에 쏟습니다.** 상호작용이 0입니다. 훅에서 다섯 번
     *   쌓아 올린 참여가 여기서 끊기고, 결제 갈림길은 이 벽 **바로 뒤**에
     *   있습니다 — 가장 지친 자리에서 값을 묻는 구조였습니다.
     *
     *   세 컷마다 한 번 가볍게 묻습니다. 응답은 이미 feedback 이 받습니다.
     */
    const cuts = free?.cuts ?? [];
    const names = (free?.locked ?? []).map((l) => l.title).slice(0, 3);
    return (
      <Shell title="값 없이 한 겹 더">
        <Scene id="oldpaper" />
        {err && <Say who={charName}>{err}</Say>}
        {cuts.map((c, i) => (
          <div key={c.id}>
            <div className="blk in">
              <div className="lab">{c.title}</div>
              <span className="src">근거 · {c.source}</span>
              <div dangerouslySetInnerHTML={{ __html: c.html }} />
            </div>
            {/* 세 컷마다 한 번. 벽을 걷는 리듬으로 되돌립니다. */}
            {i % 3 === 2 && i < cuts.length - 1 && c.statement_id && (
              <Beat cut={c} chartId={s.chartId!} lensId={s.cur}
                    concern={s.concern} charName={charName} />
            )}
          </div>
        ))}
        {free && (
          <>
            <Narration lines={[charName + "가 붓을 내려놓았다."]} />
            {/*
              ★ a7 과 d0 이 거의 같은 말로 끝나고 있었습니다 —
                "여기까지가 값 없이 하는 얘기요. 왜와 언제는 아직 안 했소."
                두 번째는 무게가 떨어지고, 손님은 **앞에서 이미 들은 말**이라
                새 정보로 읽지 않습니다.

                a7 은 격차를 **열고**, d0 은 격차를 **채웁니다** —
                이 명식에서 지금 잠긴 자리를 **이름으로 부릅니다.**
                막연한 미끼는 오히려 안 끌립니다. 제목은 이미 좋습니다.
            */}
            <Say who={charName} html={
              names.length
                ? `아직 안 편 자리가 <b>${free.locked.length}</b> 남았소.<br>` +
                  `「${names.join("」 「")}」${names.length >= 3 ? " …" : ""}`
                : "여기까지가 값 없이 하는 얘기요."} />
            <button className="btn mt" onClick={() => router.push("/pay?step=d1")}>
              어디까지 볼지 고른다
            </button>
            {/*
              ★ 이 버튼은 그대로 둡니다 — 브레이크는 매출보다 앞섭니다.
                다만 목적지가 /lobby 라 **아무것도 안 남기고** 나갔습니다.
                여기서 나간 손님을 다시 부를 고리가 없었습니다.
                손에 뭔가를 들고 나가게 합니다.
            */}
            <button className="btn gh" onClick={() => router.push("/summary")}>
              오늘은 여기까지 · 본 것을 한 장으로 받아 간다
            </button>
          </>
        )}
      </Shell>
    );
  }

  /* d2 · 결제 */
  if (step === "d2") {
    const tier = tiers?.find((t) => t.id === pick);

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
              <p className="sm">{tier?.note}</p>
              {tier && (
                <p className="sm">
                  이 명식으로 열리는 자리 <b>{tier.cuts}컷</b> ·
                  {" "}{tier.chars.toLocaleString()}자 · 약 {tier.minutes}분
                  {tier.locked > 0 && ` · 남는 자리 ${tier.locked}컷`}
                </p>
              )}
            </div>
            <p className="sm">오늘 치른 값 {order.purchases_today} / {order.per_day_limit}건</p>

            {/*
              ★ 법이 요구하는 고지 안에 **점집이 하지 않는 약속**이 하나
                들어 있습니다 — "계산 오류가 확인되면 전액 환불 후 재발행".
                이 집의 포지션을 값으로 증명하는 문장인데 회색 잔글씨에
                묻혀 아무도 안 읽고 있었습니다. 결제 버튼 바로 위에
                이 집의 말로 한 번 더 놓습니다.
            */}
            <div className="vow">{order.refund_say}</div>
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

        {/*
          ★ 여기가 "붉은 끈이 풀렸다 / 이제 나머지를 보시오" 한 줄이었습니다.
            사람은 경험의 **끝**으로 전체를 기억합니다. 재구매·후기·추천이
            갈리는 자리인데 방금 무엇을 얻었는지가 화면에 없었습니다.
            수는 서버가 셉니다 — 화면이 적지 않습니다. 셈이 안 되면
            (명식 캐시가 지워졌으면) 지어내지 않고 그냥 안 적습니다.
        */}
        {/* ★ 인장이 c6 에서 **조용히 배열에 들어갈 뿐**이었습니다.
            값을 치른 직후가 이 집이 가장 따뜻해야 할 자리인데, 얻은
            표식이 화면에 한 번도 안 보였습니다. 여기서 찍습니다. */}
        <div className="seal">
          <i>印</i>
          <span>{charName}의 인장을 받았소</span>
        </div>

        {granted?.counted && (
          <div className="dz">
            <div className="k">{granted.tier_name}</div>
            <p>
              {granted.lenses && granted.lenses > 1
                ? `${granted.lenses}사람이 열렸소.`
                : "이 사람이 열렸소."}
            </p>
            <p className="sm">
              읽을 자리 {granted.cuts}컷 · {granted.chars?.toLocaleString()}자 ·
              {" "}약 {granted.minutes}분
            </p>
          </div>
        )}

        {/* 값을 치른 직후가 이 집이 가장 따뜻해야 할 자리입니다. */}
        <Say who={charName}>
          잘 오셨소. 이제 감춰 둔 자리를 펴 드리리다.
        </Say>
        {/* ★ 결제 직후에 탭을 한 번 더 누르게 하고 있었습니다.
            "읽으러 간다" → 표지(c1) → "편다" → 본문. 값을 치른 직후는
            마찰을 0으로 둬야 할 구간입니다. 표지는 다시 읽으러 올 때 씁니다. */}
        <button className="btn mt"
                onClick={() => router.push("/report/" + s.cur + "?tab=c2")}>
          바로 읽으러 간다
        </button>
      </Shell>
    );
  }

  /* d1 · 어디까지 */
  return (
    <Shell title="어디까지 볼지">
      <Scene id="tray" />
      <Narration lines={["목패 셋이 상 위에 놓였다."]} />
      {!tiers ? (
        <p className="sm">목패를 편다…</p>
      ) : (
        <div className="og">
          {tiers.map((t) => (
            <button
              key={t.id}
              className={"op " + (pick === t.id ? "on" : "")}
              onClick={() => { setPick(t.id as Tier); setOrder(null); track("tier_pick", "d1"); }}
            >
              <b>
                {t.name} · {t.price.toLocaleString()}원
              </b>
              <span>{t.note}</span>
              {/*
                ★ 서버가 이 명식으로 세어 준 수. 부풀리지 않습니다.

                  '컷' 은 손님의 말이 아닙니다 — 그게 얼마나 되는지
                  알려면 글자 수와 읽는 시간이 있어야 합니다. 그리고
                  `all`·`sub` 은 **스무 사람**을 엽니다. 한 사람 몫만
                  적어 두면 달삯과 견줄 때 같은 것으로 보였습니다.
              */}
              <span>
                이 명식으로 <b>{t.cuts}컷</b> · {t.chars.toLocaleString()}자 ·
                {" "}읽는 데 약 {t.minutes}분
              </span>
              <span>
                {t.lenses > 1 ? `${t.lenses}사람이 한꺼번에` : "이 사람 하나"}
                {" · "}
                {t.forever ? "한 번 치르면 계속" : `${t.days ?? 30}일 동안`}
              </span>
              {/* ★ 열리는 자리의 **이름**. 서버가 이미 주고 있었는데
                  목패에서 안 쓰이고 있었습니다. 막연한 미끼는 오히려
                  덜 끌립니다 — 무엇이 열리는지 알아야 값을 견줍니다. */}
              {t.opens.length > 0 && (
                <span className="opens">
                  「{t.opens.slice(0, 3).join("」 「")}」
                  {t.opens.length > 3 ? ` 외 ${t.opens.length - 3}` : ""}
                </span>
              )}
            </button>
          ))}
        </div>
      )}
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
