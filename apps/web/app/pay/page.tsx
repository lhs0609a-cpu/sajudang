"use client";

/**
 * @screen d0 d1 d1b d2 d3
 * D · 값을 치르다 — d0 무료 6단 · d1 어디까지 · d1b 엿보기 ·
 *                  d2 결제 · d3 완료
 *
 * ★ 금액과 하루 2건 상한은 **서버가 정합니다.** 여기서 계산하지 마세요.
 *   (CLAUDE.md 절대 규칙 4)
 * ★ PG 키가 없으면 결제창을 띄우지 않고 그 사실을 그대로 알립니다.
 *   성공한 척하지 않습니다.
 */
const INPUT_LABELS: Record<string,string> = {partner:'상대 생년월일·성별',meet:'관계 대상과 만난 경위',context:'현재 상황과 태도',blood:'혈액형 선택',image:'그림 선택',cards:'카드 세 장 선택'};
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Shell from "@/components/Shell";
import PracticeCard from "@/components/PracticeCard";
import ReadingGuide from '@/components/ReadingGuide';
import CompanionCat from "@/components/CompanionCat";
import Scene from "@/components/scene/Scene";
import ActOut from "@/components/ActOut";
import { Narration, Say } from "@/components/Narration";
import { api, ApiError } from "@/lib/api";
import { LENS_BY_ID, youOf } from "@/lib/lenses";
import { useSession, type Tier } from "@/lib/store";
import { track, useScreen, analyticsId } from "@/lib/track";
import { openCheckout, registerCard } from "@/lib/toss";
import { SELLABLE } from "@/lib/biz";
import SinsalSlots from "@/components/SinsalSlots";
import type { ReportResponse } from "@shared/chart";

/* 목패의 모양은 lib/api.ts 한 곳에만 적습니다 — 여기 또 적으면
   서버가 필드를 늘려도 이 화면만 모릅니다. */
import type { Granted, TierCard, SubView } from "@/lib/api";

/** 카드를 걸기 전에 서버가 내려보내는 것 — 손님 열쇠와 고지 문구. */
type SubOffer = Awaited<ReturnType<typeof api.subPrepare>>;

/** 엿보기 한 줄 — 답은 안 옵니다. 앞머리와 가린 글자 수만. */
interface PeekRow {
  lens_id: string; lens_name: string;
  ask: string; head: string; mask: number;
  source: string | null; chars: number;
}

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

function PayInner() {
  const router = useRouter();
  const params = useSearchParams();
  const s = useSession();
  const step = params.get("step") ?? "d1";
  const lens = LENS_BY_ID[s.cur];
  const charName = lens?.name ?? "도령";
  /* 이 사람이 손님을 부르는 말. 화면에 박은 대사도 서버가 짓는 글과
     같은 호칭을 써야 합니다 — 스무 명 중 「그대」는 셋뿐입니다. */
  const you = youOf(s.cur, s.name, s.sex);

  const [free, setFree] = useState<ReportResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  /*
   * ★ 기본 선택이 「스무 사람 전부」였습니다.
   *   세 목패의 힘은 가운데가 팔리는 데서 나오는데, 그때 가운데는
   *   **지배당하는 목패**였습니다. 기본값은 지금 읽고 있던 사람이고,
   *   값이 가장 낮고, 다음 결제로 이어지는 문입니다 — 「이 자리 하나」.
   *   값이 없는 캐릭터(청동자)면 서버가 그 목패를 안 주므로,
   *   목패가 오면 첫 장으로 맞춰 둡니다.
   */
  /*
   * ★ 목패 하나가 **이미 켜진 채** 서 있었습니다 (2026-09-04).
   *
   *   기본값이 "one" 이라 셋 중 하나에 불이 들어와 있었고, 손님은
   *   고른 적이 없는데 「이걸로 열겠습니다」 를 누를 수 있었습니다.
   *   값을 치르는 자리에서 **안 고른 것이 골라져 있으면** 안 됩니다.
   */
  const [pick, setPick] = useState<Tier | null>(null);
  const [order, setOrder] = useState<Order | null>(null);
  const [busy, setBusy] = useState(false);
  const [sales, setSales] = useState<{ready:boolean;reason:string|null}|null>(null);
  useEffect(() => {
    if (!["d1", "d1b", "d2"].includes(step)) return;
    let alive = true;
    fetch("/api/sales-status").then(r => {if (!r.ok) throw new Error(); return r.json();})
      .then(value => {if (alive) {setSales(value); if (!value.ready) track("checkout_blocked", "d1", {n:value.reason === "seller_setup" ? 1 : value.reason === "gateway_setup" ? 2 : 3});}})
      .catch(() => {if(alive) setSales({ready:false,reason:"temporary"});});
    return () => {alive=false;};
  }, [step, retry]);
  /* 목패 — ★ 값도 분량도 서버가 셉니다. 화면은 받아 적기만 합니다. */
  const [tiers, setTiers] = useState<TierCard[] | null>(null);
  /* 값을 치른 직후 **무엇을 얻었는지**. ★ 서버가 셉니다. */
  const [granted, setGranted] = useState<Granted | null>(null);
  /*
   * 엿보기 — 목패를 고른 뒤, 값을 치르기 전에 보는 자리.
   *
   * ★ 답은 **안 옵니다.** 앞머리와 가린 글자 수만 옵니다.
   *   블러가 아니라 서버가 안 보내는 것입니다 (engine/peek.py).
   */
  const [peek, setPeek] = useState<PeekRow[] | null>(null);
  const [hidden, setHidden] = useState(0);
  /*
   * 걸어 둔 카드 — 「한 달 듣기」.
   *
   * ★ 값을 치르는 자리가 셋인데 **사는 길이 둘**입니다. 「이 자리
   *   하나」와 「스무 사람 전부」는 결제창에서 한 번 긁고 끝이고,
   *   달삯은 카드를 걸어 두고 달마다 나갑니다. 그 차이를 화면이
   *   말해야 합니다 — 안 말하면 손님은 한 번 치른 줄로 압니다.
   */
  const [sub, setSub] = useState<SubView | null>(null);

  useScreen(step);
  useEffect(() => {
    setTiers(null); setPick(null); setOrder(null); setFree(null); setPeek(null); setOffer(null);
  }, [s.chartId, s.cur, s.concern, s.axis4]);

  /* 목패 셋 — 서버가 센 값과 분량 */
  useEffect(() => {
    if (!s.chartId || tiers) return;
    if (!["d1", "d1b", "d2"].includes(step)) return;
    let alive = true;
    api
      .payTiers({ chart_id: s.chartId, lens_id: s.cur,
                  concern: s.concern, axis4: s.axis4 })
      .then((r) => {
        if (!alive) return;
        const list = r.tiers as TierCard[];
        setTiers(list);
        // ★ 여기서 **대신 골라 주지 않습니다.**
        //
        //   전에는 목패가 오면 첫 장을 켜 놓았습니다. 그러면 손님은
        //   고른 적이 없는데 하나가 켜져 있고, 「이걸로 열겠습니다」 가
        //   눌리는 상태가 됩니다. 값을 치르는 자리라 더 그렇습니다.
        //
        //   고른 것이 이 캐릭터에 없을 때만 **놓습니다** (값 없는
        //   캐릭터의 '이 자리 하나'). 켜 주지는 않습니다.
        if (pick && list.length && !list.some((t) => t.id === pick)) {
          setPick(null);
        }
      })
      .catch((e) => { if (alive) setErr(e instanceof ApiError ? e.message : "목패를 펴지 못했소."); });
    return () => { alive = false; };
  }, [step, s.chartId, s.cur, s.concern, s.axis4, tiers, retry]);

  /* d1b · 엿보기 — 고른 목패가 여는 자리들 */
  useEffect(() => {
    if (!["d1", "d1b", "d2"].includes(step) || !s.chartId || !pick) return;
    let alive = true;
    api
      .payPeek({ chart_id: s.chartId, lens_id: s.cur, tier: pick,
                 concern: s.concern, axis4: s.axis4 })
      .then((r) => {
        if (!alive) return;
        setPeek(r.rows);
        setHidden(r.hidden);
      })
      .catch((e) => {
        if (alive) setErr(e instanceof ApiError ? e.message : "엿보지 못했소.");
      });
    return () => { alive = false; };
  }, [step, s.chartId, s.cur, s.concern, s.axis4, pick]);

  /* d0 · 무료 구간 */
  useEffect(() => {
    if (step !== "d0" || !s.chartId || free) return;
    let alive = true;
    api
      .report({
        chart_id: s.chartId, lens_id: s.cur, tier: "free",
        session_id: s.sessionId, concern: s.concern, axis4: s.axis4,
        name: s.name,
      })
      .then((r) => { if (alive) setFree(r); })
      .catch((e) => {
        if (alive) setErr(e instanceof ApiError ? e.message : "펴지 못했소.");
      });
    return () => { alive = false; };
  }, [step, s.chartId, s.cur, s.concern, s.axis4, free, retry]);

  /*
   * 결제창에서 돌아왔다 — 토스가 ?toss=ok&paymentKey=… 로 되돌려 보냅니다.
   *
   * 결제창은 페이지를 통째로 떠났다 옵니다. 그래서 승인은 여기서 하오.
   * 금액은 안 보냅니다 — 서버가 주문에 적어 둔 값을 씁니다.
   */
  const tossBack = params.get("toss");
  const [settling, setSettling] = useState(tossBack === "ok");
  useEffect(() => {
    if (tossBack !== "ok") return;
    const orderId = params.get("order") ?? params.get("orderId");
    const paymentKey = params.get("paymentKey");
    if (!orderId || !paymentKey) {
      setErr("결제 정보를 확인할 수 없소. 결제 내역에서 상태를 먼저 확인해 주시오.");
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
    setErr("결제창이 닫혔소. 결제 내역을 확인한 뒤 다시 진행해 주시오.");
  }, [tossBack, params]);

  /*
   * 카드 등록에서 돌아왔다 — 「한 달 듣기」.
   *
   * ★ 결제창과 **다른 길**입니다. 토스가 돌려보내는 것은 paymentKey 가
   *   아니라 `authKey` 이고, 이 시점에는 **아직 아무 돈도 안 빠져나갔습니다.**
   *   서버가 authKey 를 빌링키로 바꾸고, 그 열쇠로 첫 달을 긁소.
   *   그러니 여기서 "치렀다" 고 화면을 넘기면 안 되오 — 서버 대답을
   *   받고 넘깁니다.
   */
  const subBack = params.get("sub");
  const [carding, setCarding] = useState(subBack === "ok");
  useEffect(() => {
    if (subBack !== "ok") return;
    const customerKey = params.get("customerKey");
    const authKey = params.get("authKey");
    if (!customerKey || !authKey) {
      setErr("카드 등록 정보를 확인할 수 없소. 내 첩에서 구독 상태를 확인해 주시오.");
      setCarding(false);
      return;
    }
    let alive = true;
    api
      .subRegister({
        session_id: s.sessionId, customer_key: customerKey,
        auth_key: authKey, chart_id: s.chartId, concern: s.concern, analytics_sid: analyticsId(),
      })
      .then((r) => {
        if (!alive) return;
        setSub(r.sub);
        s.set({ tier: "sub" as Tier, paid: true });
        track("pay_done", "d2");
        router.replace("/pay?step=d3&sub=done");
      })
      .catch((e) => {
        if (!alive) return;
        track("pay_fail", "d2");
        setErr(e instanceof ApiError ? e.message : "카드를 걸지 못했소.");
        setCarding(false);
      });
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [subBack]);

  useEffect(() => {
    if (subBack !== "fail") return;
    track("pay_fail", "d2");
    setErr("카드 등록이 중단되었소. 내 첩에서 구독 상태를 확인해 주시오.");
  }, [subBack, params]);

  /* d2 · 주문 만들기 — 금액·상한은 서버가 판정한다 */
  useEffect(() => {
    if (!["d1", "d1b", "d2"].includes(step) || !s.chartId || order || tossBack || subBack) return;
    // ★ 안 고르고 d2 로 바로 들어온 자리(주소를 치거나 레일로 뛰거나).
    //   없는 값으로 주문을 만들지 않고 목패로 돌려보내오.
    if (!pick || !sales?.ready) return;
    // ★ 달삯은 주문이 아니오 — 카드를 걸어 두는 일이라 길이 다릅니다.
    //   서버도 이 길로 오면 409 로 돌려보냅니다 (pay.prepare).
    if (pick === "sub") return;
    let alive = true;
    setErr(null);
    api
      .payPrepare({
        session_id: s.sessionId, chart_id: s.chartId,
        lens_id: s.cur, tier: pick, concern: s.concern, analytics_sid: analyticsId(),
      })
      .then((o) => { if (alive) setOrder(o); })
      .catch((e) => {
        if (alive) setErr(e instanceof ApiError ? e.message : "값을 매기지 못했소.");
      });
    return () => { alive = false; };
  }, [step, s.chartId, s.sessionId, s.cur, s.concern, pick, order, sales?.ready, retry]);

  /*
   * d2 · 달삯 — 손님 열쇠와 **고지 문구**를 받아 온다.
   *
   * ★ 고지가 서버에서 오는 까닭: 값·주기·다음 날은 서버가 정합니다.
   *   화면이 제 손으로 "매달 9,900원" 이라 적어 두면 값을 고쳤을 때
   *   그 줄만 옛말로 남습니다 — 목패 이름이 두 벌이라 어긋났던 자리와
   *   같은 종류의 사고입니다.
   */
  const [offer, setOffer] = useState<SubOffer | null>(null);
  useEffect(() => {
    if (!["d1", "d1b", "d2"].includes(step) || pick !== "sub" || offer || subBack || !sales?.ready) return;
    let alive = true;
    setErr(null);
    api
      .subPrepare({ session_id: s.sessionId })
      .then((o) => { if (alive) setOffer(o); })
      .catch((e) => {
        if (alive) setErr(e instanceof ApiError ? e.message : "카드 자리를 열지 못했소.");
      });
    return () => { alive = false; };
  }, [step, pick, s.sessionId, offer, subBack, sales?.ready, retry]);

  if (step === "d0") {
    if (!s.chartId) return <Shell screen="d0" title="무료 해석 시작하기">
      <p className="conversion-lead">아직 태어난 정보가 없소. 생년월일과 고민을 고르면 무료로 요약해 드리겠소.</p>
      <button className="btn" onClick={() => router.push("/?step=a5")}>내 고민으로 무료 해석 시작하기</button>
    </Shell>;
    const cuts = free?.cuts ?? [];
    const review = s.hookReview;
    const same = review?.chartId === s.chartId && review.concern === s.concern && review.lensId === s.cur;
    const rejected = same ? Object.entries(review.answers).filter(([, answer]) => answer === false).map(([stage]) => stage) : [];
    const stageNames: Record<string,string> = {"0":"처음 짚은 반복 패턴", "1":"고민을 대하는 방식", "2":"기운을 쓰는 방식", "2.5":"고민과 타고난 성향의 차이", "3":"마지막 확인 질문"};
    const openPrice = () => {track("price_view", "d0"); router.push("/pay?step=d1");};
    return (
      <Shell screen="d0" title="무료 요약과 오늘의 행동">
        <p className="conversion-kicker">{charName}의 해석 · 무료</p>
        <h1 className="conversion-title reading-title">내 고민을 짧게 정리해 보겠소.</h1>
        {err && <><Say who={charName} lens={s.cur}>{err}</Say><button className="btn" onClick={() => {setErr(null);setRetry(n => n + 1);}}>무료 해석 다시 불러오기</button></>}
        {!free && !err && <p role="status">해석과 근거를 정리하고 있소…</p>}
        {free && <>
          {rejected.length > 0 ? <section className="conversion-card" aria-label="맞지 않았던 해석 다시 보기">
            <h2>맞지 않았던 {rejected.length}마디는 접어 두겠소.</h2>
            <p>그대가 아니라고 답한 해석을 성격으로 단정하지 않겠소. 생년월일에서 계산한 기둥은 그대로지만, 그 해석이 실제 경험과 같다는 뜻은 아니오.</p>
            <ul>{rejected.map(stage => <li key={stage}>{stageNames[stage] ?? "확인 질문"}</li>)}</ul>
            {free.editorial && <p className="conversion-note">계산에서 확인한 근거 · {free.editorial.observation}</p>}
            <p><strong>오늘은 이것부터 해보시오.</strong><br />맞지 않았던 문장 하나와 실제로 겪은 장면 하나를 나란히 적으시오. 다른 점이 무엇인지 먼저 살피는 것으로 충분하오.</p>
            <button className="btn gh" onClick={() => {track("reading_mismatch", "d0", {n: 1}); router.push("/?step=a3");}}>태어난 정보 다시 확인하기</button>
            <button className="btn gh" onClick={() => {track("reading_mismatch", "d0", {n: 2}); router.push("/lobby");}}>다른 해석자의 관점 살펴보기</button>
          </section> : free.editorial ? <ReadingGuide guide={free.editorial} /> :
            <div className="conversion-card"><p>기둥과 해석 근거를 아래에서 확인할 수 있소. 맞는 부분만 경험에 대입해 보시오.</p></div>}
          {(lens?.price ?? 0) > 0 && <div className="reading-next">
            <p>무료 해석은 여기까지요. 추가 내용과 가격을 먼저 살펴보거나, 아래 근거를 더 읽어도 되오.</p>
            {!SELLABLE && <p className="conversion-note">현재 유료 판매를 준비하고 있소. 무료 해석은 계속 읽을 수 있소.</p>}
            <button className="btn" onClick={openPrice}>추가 해석과 가격 보기</button>
          </div>}
          <details className="conversion-details reading-evidence" onToggle={e => {if(e.currentTarget.open) track("reading_expand", "d0");}}>
            <summary>{rejected.length ? "원래 해석과 계산 근거 확인하기" : "무료 해석의 자세한 근거 펼치기"} · {cuts.length}개 항목</summary>
            {rejected.length > 0 && <p className="conversion-note">아래는 응답 전 생년월일과 고민으로 만든 원래 해석이오. 아니라고 답한 대목이 맞는 것으로 바뀐 것은 아니오.</p>}
            {cuts.map(c => <section className="blk" key={c.id}>
              <h2 className="lab">{c.title}</h2><p className="src">근거 · {c.source}</p>
              {c.id === "sinsal" ? <SinsalSlots html={c.html} /> : <div dangerouslySetInnerHTML={{__html:c.html}} />}
            </section>)}
            {!rejected.length && free.practice && <PracticeCard key={free.practice.id} practice={free.practice} />}
          </details>
          <button className="btn gh" onClick={() => router.push("/summary")}>오늘은 여기까지 · 본 것을 한 장으로 받겠소</button>
        </>}
      </Shell>
    );
  }

  if (["d1", "d1b", "d2"].includes(step)) {
    if (lens?.price === 0 && !tossBack && !subBack) return (
      <Shell screen="d0" title="무료로 읽는 자리">
        <CompanionCat message="이 인물의 해석은 무료로 읽을 수 있소." />
        <button className="btn" onClick={() => router.push("/report/" + s.cur + "?tab=c2")}>무료 해석 읽기</button>
      </Shell>
    );
    const tier = tiers?.find((t) => t.id === pick);
    const selectTier = (t: TierCard) => {
      if (pick === t.id) return;
      setPick(t.id as Tier); setOrder(null); setOffer(null); setPeek(null); setErr(null);
      track("tier_pick", "d1");
    };
    const product = (t: TierCard) => (
      <button key={t.id} className="conversion-product" aria-pressed={pick === t.id}
        onClick={() => selectTier(t)}>
        <strong>{pick === t.id ? "✓ " : ""}{t.id === "one" ? `${charName} 해석` : t.name}</strong>
        <strong className="conversion-price">{t.price.toLocaleString()}원</strong>
        <span>{t.per_month ? `${t.days ?? 30}일마다 자동 결제` : "한 번 결제 · 영구 열람"}</span>
        <span>{t.lenses > 1 ? `${t.lenses}명의 해석을 함께 읽소.` : "이 인물의 추가 해석과 근거를 읽소. 다른 인물은 포함하지 않소."}</span>
        <span>전체 {t.cuts}개 항목 · 약 {t.minutes}분 분량</span>{t.needs_extra_input && <span>일부 항목은 추가 정보가 있어야 열리오. 선택 후 필요한 정보를 확인하시오.</span>}
      </button>
    );
    if (settling || carding) return (
      <Shell screen="d2" title="결제 결과 확인" legal>
        <div className="conversion-card" role="status"><h2>결제 결과를 확인하고 있소.</h2>
          <p>서버에서 결제와 열람 권한을 확인한 뒤 해석을 열어드리겠소.</p></div>
      </Shell>
    );
    return (
      <Shell screen="d1" title="추가 해석과 결제" legal onBack={() => router.push("/pay?step=d0")}>
        <div className="conversion-intro">
          <p className="conversion-kicker">내용 · 가격 · 열람 조건</p>
          <h1 className="conversion-title">무료 다음에는<br />무엇을 더 읽을 수 있소?</h1>
          <p className="conversion-lead">{charName}의 추가 해석을 미리 살펴보시오. 무료 내용과의 차이를 확인한 뒤 결정해도 늦지 않소.</p>
        </div>
        {sales?.reason === "seller_setup" && <div className="conversion-status" role="status"><strong>현재 유료 판매를 준비하고 있소.</strong><p>판매자 정보 등록이 끝나기 전에는 결제를 받지 않소. 다시 시도할 필요 없이 무료 해석을 계속 읽어도 되오.</p><a href="/legal">판매자 정보 확인하기</a></div>}
        {sales?.reason === "gateway_setup" && <p className="conversion-status" role="status">결제 서비스 연결을 준비하고 있소. 지금은 무료 해석을 이용해 주시오.</p>}
        {sales?.reason === "temporary" && <div className="conversion-status" role="alert"><p>결제 가능 상태를 확인하지 못했소. 입력과 선택은 그대로 남아 있소.</p><button className="btn gh" onClick={() => {setSales(null);setRetry(n => n + 1);}}>결제 연결 다시 확인하기</button></div>}
        {!sales && <p role="status">결제 가능 상태를 확인하고 있소…</p>}
        {!s.chartId && <div className="conversion-status"><p>먼저 태어난 정보로 무료 해석을 확인해 주시오.</p><button className="btn" onClick={() => router.push("/?step=a5")}>무료 해석 시작하기</button></div>}
        {err && <div className="warn" role="alert"><p>{err}</p>{!tiers && <button className="btn" onClick={() => {setErr(null);setRetry(n => n + 1);}}>상품 다시 불러오기</button>}<button className="btn gh" onClick={() => router.push("/me")}>결제 내역·구독 확인</button>
          {tiers && pick && !tossBack && !subBack && <button className="btn gh" onClick={() => {setErr(null);setRetry(n => n + 1);}}>선택한 상품의 결제 조건 다시 확인하기</button>}
          {(tossBack || subBack) && <button className="btn gh" onClick={() => router.replace("/pay?step=d1")}>상품으로 돌아가기</button>}</div>}
        {s.chartId && !tiers && !err && <p role="status">이 명식에서 열리는 내용을 확인하고 있소…</p>}
        {tiers && <>
          <div className="conversion-products">{tiers.filter(t => t.id === "one").map(product)}</div>
          <details className="conversion-details" open={pick === "all" || pick === "sub" || !tiers.some(t => t.id === "one") ? true : undefined}>
            <summary>다른 열람 방식 보기</summary><div className="conversion-products">{tiers.filter(t => t.id !== "one").map(product)}</div>
          </details>
        </>}
        {tier && <div className="conversion-checkout" aria-live="polite">
          <div className="conversion-card">
            <h2>{tier.id === "one" ? `${charName} 해석` : tier.name}</h2>
            {tier.needs_extra_input && <div className="conversion-note">
              <p>일부 해석에 필요한 추가 입력: {(tier.required_inputs ?? []).map(key => (INPUT_LABELS[key] ?? '현재 상황')).join(' · ') || '상대 정보 또는 현재 상황'}.</p>
              <p>입력은 선택이오. 생년월일로 읽는 본문은 볼 수 있고, 입력하지 않은 정보에 대한 추가 해석은 열리지 않소. 혈액형·그림·카드는 자기 성찰을 위한 보조 소재이오.</p>
            </div>}
            {tier.id === "all" && <p className="conversion-note">이미 읽은 내용도 포함되오. 전체 상품은 다른 인물의 관점을 함께 읽는 방식이며, 모든 인물에서 한 명 상품보다 본문이 길어지는 것은 아니오.</p>}
            {peek && peek.length > 0 && <section className="paid-preview"><h3>결제하면 더 읽는 질문</h3><p className="conversion-note">무료에서는 기둥·핵심 해석·오늘의 행동을 읽었소. 아래는 선택한 상품에서 추가로 열리는 해석의 실제 앞부분이오.</p>
              {peek.slice(0, 3).map((r, i) => <div key={r.lens_id+i}><h3>{r.ask}</h3><p>{r.head}… <span className="conversion-note">(본문 일부)</span></p>{r.source && <p className="conversion-note">해석 근거 · {r.source}</p>}</div>)}
            </section>}
            <details className="conversion-details"><summary>전체 분량과 열람 범위</summary>
              <p className="conversion-note">현재 명식 기준 {tier.cuts}개 내용 · {tier.chars.toLocaleString()}자 · 약 {tier.minutes}분. {tier.lenses}명의 관점으로 읽소.</p>
              {tier.opens.length > 0 && <ul>{tier.opens.map(title => <li key={title}>{title}</li>)}</ul>}
            </details>
            {pick !== "sub" && order && <>
              <p className="conversion-price">{order.amount.toLocaleString()}원 <small>한 번 결제</small></p>
              <p className="conversion-note">{pick === "all" ? "전체 인물의 해석" : `${charName}의 해석`} · 영구 열람 · 자동 결제 없음</p>
              <div className="vow">{order.refund_say}</div><p className="conversion-note">{order.refund_notice}</p>
              <p className="conversion-note">오늘 구매 {order.purchases_today} / {order.per_day_limit}건</p>
              {order.enabled && order.client_key && sales?.ready ? <button className="btn" disabled={busy} onClick={async () => {
                setBusy(true); setErr(null); track("pay_start", "d1");
                try { await openCheckout({ clientKey: order.client_key!, orderId: order.order_id, amount: order.amount, orderName: tier.name, customerKey: s.sessionId }); }
                catch (e) { track("pay_fail", "d1"); setErr(e instanceof Error ? e.message : "결제창을 열지 못했소. 다시 시도해 주시오."); }
                finally { setBusy(false); }
              }}>{busy ? "결제창 연결 중…" : `${order.amount.toLocaleString()}원 결제하기`}</button>
              : <p className="conversion-status">결제 서비스 연결이 준비되지 않았소. 무료 해석을 계속 읽거나 결제 내역을 확인해 주시오.</p>}
            </>}
            {pick === "sub" && offer && <>
              <p className="conversion-price">{offer.amount.toLocaleString()}원 <small>{tier.days ?? 30}일마다 자동 결제</small></p>
              <div className="vow">{offer.terms.map((t,i) => <p key={i}>{t}</p>)}</div>
              <p className="conversion-note">{offer.refund_notice}</p>
              {offer.enabled && offer.client_key && sales?.ready ? <button className="btn" disabled={busy} onClick={async () => {
                setBusy(true); setErr(null); track("pay_start", "d1");
                try { await registerCard({ clientKey: offer.client_key!, customerKey: offer.customer_key }); }
                catch (e) { track("pay_fail", "d1"); setErr(e instanceof Error ? e.message : "카드 등록을 연결하지 못했소."); }
                finally { setBusy(false); }
              }}>{busy ? "카드 등록 연결 중…" : `${offer.amount.toLocaleString()}원 정기결제 등록하기`}</button>
              : <p className="conversion-status">지금은 정기결제를 제공하지 않소. 한 번 결제하는 상품의 내용을 확인해 주시오.</p>}
            </>}
            {sales?.ready && !order && pick !== "sub" && !err && <p role="status">결제 금액과 조건을 확인하고 있소…</p>}
            {sales?.ready && !offer && pick === "sub" && !err && <p role="status">정기결제 조건을 확인하고 있소…</p>}
          </div>
        </div>}
        <button className="btn gh" onClick={() => router.push("/pay?step=d0")}>무료 해석으로 돌아가기</button>
        <p className="conversion-note">하루 구매는 2건까지요. 이미 구매했다면 내 첩에서 결제 내역과 복원 방법을 확인해 주시오.</p>
      </Shell>
    );
  }

  /* d3 · 완료 */
  if (step === "d3") {
    if (!s.paid && !granted && !sub?.has) return <Shell screen="d3" title="결제 내역 확인">
      <p className="conversion-lead">이 화면만으로는 결제 완료를 확인할 수 없소. 내 첩에서 결제 내역을 확인해 주시오.</p>
      <button className="btn" onClick={() => router.push("/me")}>결제 내역 확인</button>
    </Shell>;
    return (
      <Shell screen="d3" title="열렸소">
        <Scene id="untie" />
        <CompanionCat state="saved" message="해석이 열렸소. 내 속도로 천천히 읽어보시오." />
        <Narration lines={["붉은 끈이 풀렸다."]} />

        {/*
          ★ 여기가 "붉은 끈이 풀렸다 / 이제 나머지를 보시오" 한 줄이었습니다.
            사람은 경험의 **끝**으로 전체를 기억합니다. 재구매·후기·추천이
            갈리는 자리인데 방금 무엇을 얻었는지가 화면에 없었습니다.
            수는 서버가 셉니다 — 화면이 적지 않습니다. 셈이 안 되면
            (명식 캐시가 지워졌으면) 지어내지 않고 그냥 안 적소.
        */}
        {/* ★ 인장이 c6 에서 **조용히 배열에 들어갈 뿐**이었소.
            값을 치른 직후가 이 집이 가장 따뜻해야 할 자리인데, 얻은
            표식이 화면에 한 번도 안 보였습니다. 여기서 찍습니다. */}
        <div className="seal">
          <i>印</i>
          <span>{charName}의 인장을 받았소</span>
        </div>

        {/*
          ★ 달삯은 **다음이 있는** 결제이오.
            한 번 치르는 것과 달리, 여기서 말 안 하면 손님은 다음 달에
            빠져나가는 것을 카드 명세서에서 처음 봅니다. 그건 몰래
            빼간 것과 같습니다. 언제 · 얼마 · 어디서 그만두는지를
            **치른 직후에** 한 번 더 적습니다.
        */}
        {sub?.has && (
          <div className="dz">
            <div className="k">달마다 이어지오</div>
            <p>
              {sub.price.toLocaleString()}원 <small>/ 달</small>
              {sub.card && <small> · 끝자리 {sub.card}</small>}
            </p>
            <p className="sm">
              다음은 {(sub.next_charge ?? "").slice(0, 10)}이오.
              그만두시려거든 「내 첩」으로 오시오 — 버튼 하나면 되오.
            </p>
          </div>
        )}

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

        {/* 값을 치른 직후가 이 집이 가장 따뜻해야 할 자리이오. */}
        {/*
          ★ 여기가 넷째로 낮았소 (연출 54).

            「잘 오셨소」 한 줄이 전부였소. 값을 치른 **직후**인데
            치른 사람 얘기가 없어서, 인장과 컷 수만 뜨는 영수증
            화면이 됐습니다. 울림 20 · 명확 43 이 거기서 나왔습니다.

            더 팔려고 붙이는 말이 아닙니다. 여기서 할 일은 **판 것을
            줄이는 것**입니다 — 하루 2번 상한과 인장 1개를 다시
            말하고, 다 읽고 나서 무엇을 하면 되는지까지 적습니다.
        */}
        <Say who={charName} lens={s.cur}>
          결제가 확인됐소. 구매한 해석을 펼치시오.
          <br />
          먼저 확인 질문과 오늘 해볼 행동을 보고, 궁금한 제목을 펼치시오.
          맞지 않는 내용은 그대의 경험에 억지로 맞추지 않아도 되오.
          <br />
          구매 내역과 복원 방법은 내 첩에 남아 있소. 오늘 모두 읽지 않아도 되오.
        </Say>
        <span className="src">
          근거 · 오늘 치른 값과 열린 자리를 서버가 세어 적은 것이오 ·
          하루 2번 · 한 자리 2명 · 인장 1개 · 컷 수와 글자 수는
          이 명식으로 센 것이지 미리 적어 둔 문구가 아니오
        </span>
        <ActOut kind="끊긴 동작" next="본문">
          {granted?.cuts
            ? <>열렸소. <b>{granted.cuts}컷</b>이 기다리고 있소.</>
            : <>열렸소. 감춰 둔 자리가 기다리고 있소.</>}
          <br />
          <b>아직 한 줄도 안 보셨소.</b>
        </ActOut>
        {/* ★ 결제 직후에 탭을 한 번 더 누르게 하고 있었습니다.
            "읽으러 간다" → 표지(c1) → "편다" → 본문. 값을 치른 직후는
            마찰을 0으로 둬야 할 구간이오. 표지는 다시 읽으러 올 때 쓰오. */}
        <button className="btn mt"
                onClick={() => router.push("/report/" + s.cur + "?tab=c2")}>
          바로 읽겠소
        </button>
      </Shell>
    );
  }

  return <Shell screen="d1" title="추가 해석"><button className="btn" onClick={() => router.replace("/pay?step=d1")}>상품 확인하기</button></Shell>;
}

export default function PayPage() {
  return (
    <Suspense fallback={<Shell title="값을 치르다"><p className="sm">…</p></Shell>}>
      <PayInner />
    </Suspense>
  );
}
