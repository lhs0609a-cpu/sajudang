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
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Shell from "@/components/Shell";
import Scene from "@/components/scene/Scene";
import Reveal from "@/components/Reveal";
import ActOut from "@/components/ActOut";
import { Narration, Say } from "@/components/Narration";
import { api, ApiError } from "@/lib/api";
import { LENS_BY_ID, youOf } from "@/lib/lenses";
import { useSession, type Tier } from "@/lib/store";
import { track, useScreen } from "@/lib/track";
import { openCheckout } from "@/lib/toss";
import { SELLABLE } from "@/lib/biz";
import { thinkOf } from "@/lib/think";
import SinsalSlots from "@/components/SinsalSlots";
import type { ReportResponse } from "@shared/chart";

/* 목패의 모양은 lib/api.ts 한 곳에만 적습니다 — 여기 또 적으면
   서버가 필드를 늘려도 이 화면만 모릅니다. */
import type { Granted, TierCard } from "@/lib/api";

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
        <button onClick={() => answer(true)}>그렇습니다</button>
        <button onClick={() => answer(false)}>아닙니다</button>
      </div>
      <button className="lk vt3" onClick={() => answer(null)}>잘 모르겠습니다</button>
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
  /* 이 사람이 손님을 부르는 말. 화면에 박은 대사도 서버가 짓는 글과
     같은 호칭을 써야 합니다 — 스무 명 중 「그대」는 셋뿐입니다. */
  const you = youOf(s.cur, s.name, s.sex);

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
  }, [step, s.chartId, s.cur, s.concern, s.axis4, tiers]);

  /* d1b · 엿보기 — 고른 목패가 여는 자리들 */
  useEffect(() => {
    if (step !== "d1b" || !s.chartId || !pick) return;
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
    // ★ 안 고르고 d2 로 바로 들어온 자리(주소를 치거나 레일로 뛰거나).
    //   없는 값으로 주문을 만들지 않고 목패로 돌려보냅니다.
    if (!pick) { router.replace("/pay?step=d1"); return; }
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
    /*
     * ★ 안 편 자리를 **목차로 부르지 않습니다** (2026-09-04).
     *
     *   여기 「4 · 지금 어디에」 「5 · 필요한 것」 「6 · 대운 맵」 이라
     *   적혀 있었습니다. 그건 이 집이 컷을 세는 말입니다. 「대운 맵」이
     *   무엇인지 모르는 사람에게 그게 남았다고 해 봐야 아무것도 안
     *   남습니다 — 값을 치를 까닭이 안 생깁니다.
     *
     *   손님이 궁금한 것은 **재물 · 사랑 · 운명 · 사람** 넷이고, 그 넷은
     *   이미 그 사람의 여덟 글자 안에 세어져 있습니다. 세어 놓고 안
     *   부르고 있었습니다 (engine/peek.build_wants).
     */
    const wants = free?.wants ?? [];
    const names = (free?.locked ?? []).map((l) => l.title).slice(0, 3);
    return (
      <Shell screen="d0" title="값 없이 한 겹 더">
        <Scene id="oldpaper" />
        {/* ★ 여는 줄이 없어 첫 줄이 곧바로 해석이었습니다. 값을 안
            받는 구간이라는 것도 글에 안 적혀 있었습니다. */}
        <Narration lines={["도령이 종이를 한 겹 더 넘겼다.",
                           "값 이야기는 아직 나오지 않았다."]} />
        {err && <Say who={charName} lens={s.cur}>{err}</Say>}
        {/*
          ★ 한 컷씩 뜹니다 (2026-09-02). 여기가 손님이 "압도당한다" 고
            짚은 자리입니다 — 여덟 컷 1,592자가 한 화면에 통째로
            서 있었습니다. 뜨기 전 한 줄은 그 컷이 실제로 보는 자리라,
            뜸이 곧 근거 예고가 됩니다 (lib/think.ts).
        */}
        {cuts.map((c, i) => (
          <Reveal key={c.id} think={thinkOf(c.source)} eager={i === 0}>
            <div className="blk in">
              <div className="lab">{c.title}</div>
              <span className="src">근거 · {c.source}</span>
              {/*
                ★ 신살 컷에 **인물이 안 붙고 있었습니다** (2026-09-04).

                  서버는 이름마다 빈 자리를 남기고
                  (`<div class="ssfig" data-sinsal="taegeuk">`),
                  `SinsalSlots` 가 거기에 그림을 꽂습니다. 리포트(c2)와
                  분석지(c7)와 건너온 자리(s1)에는 붙어 있었는데
                  **무료 6단만 빠져 있었습니다** — 그냥 innerHTML 로
                  부어서 빈 자리가 빈 채로 남았습니다.

                  하필 신살은 **무료 컷**입니다. 값을 치르기 전에
                  태극귀인·문창귀인·금여·양인을 만나는 자리가 여기인데,
                  거기서 한자만 보고 있었습니다.
              */}
              {c.id === "sinsal"
                ? <SinsalSlots html={c.html} />
                : <div dangerouslySetInnerHTML={{ __html: c.html }} />}
            </div>
            {/* 세 컷마다 한 번. 벽을 걷는 리듬으로 되돌립니다. */}
            {i % 3 === 2 && i < cuts.length - 1 && c.statement_id && (
              <Beat cut={c} chartId={s.chartId!} lensId={s.cur}
                    concern={s.concern} charName={charName} />
            )}
          </Reveal>
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
            <Say who={charName} lens={s.cur} html={
              wants.length
                ? `아직 안 편 자리가 <b>${free.locked.length}</b> 남았소.<br>` +
                  `그 중 넷은 ${wants.map((w) => w.want).join(" · ")}이오.`
                : names.length
                  ? `아직 안 편 자리가 <b>${free.locked.length}</b> 남았소.<br>` +
                    `「${names.join("」 「")}」${names.length >= 3 ? " …" : ""}`
                  : "여기까지가 값 없이 하는 얘기요."} />
            {/*
              ★ 여는 줄(fact)은 **센 것**이라 대 볼 수 있고, 답은 앞머리만
                진짜로 왔습니다. 흐린 칸은 글을 가린 게 아니라 **빈 칸**
                입니다 — 서버가 안 보냈으니 브라우저를 뒤져도 안 나옵니다.
                근거 줄은 안 가립니다. 그게 이 집이 값을 받는 방식입니다.
            */}
            {wants.map((w, i) => (
              <div className="peek" key={w.want + i}>
                <div className="pk">
                  {w.want}
                  <span dangerouslySetInnerHTML={{ __html: w.fact }} />
                </div>
                <p className="pkbody">
                  <span className="pkask">{w.ask}</span> {w.head}
                  <span className="pkmask" aria-label={`가려진 ${w.mask}자`}>
                    {"▒".repeat(Math.min(22, Math.max(6, Math.round(w.mask / 12))))}
                  </span>
                </p>
                {w.source && <span className="src">근거 · {w.source}</span>}
                <p className="pkmore">여기서부터 <b>{w.mask}자</b>가 더 있소</p>
              </div>
            ))}
            {/*
              ★ 막을 끊는 줄이 없었습니다. 「아직 안 편 자리가 N 남았소」
                는 수를 대지만 **다음 자리를 이름으로 안 부릅니다.**
                여기 적는 건 전부 이미 참인 것입니다.
            */}
            <ActOut kind="딜레마" next="어디까지 볼지">
              여기까지가 값 없이 하는 몫이오. 다음 장은 값을 묻소.
              <br />
              값 없이 여는 6단은 같은 여덟 글자를 겉에서 훑은 것이고,
              접힌 데는 그 속을 갈라 본 것이오 — 겉껍질을 보고 열매를
              말한 것과, 쪼개어 씨를 세어 본 것처럼 다르오.
              <br />
              <b>오늘 안 열어도 되오.</b> 이 집은 하루에 2번까지만 받소.
            </ActOut>
            <button className="btn mt" onClick={() => router.push("/pay?step=d1")}>
              어디까지 볼지 고르겠습니다
            </button>
            {/*
              ★ 이 버튼은 그대로 둡니다 — 브레이크는 매출보다 앞섭니다.
                다만 목적지가 /lobby 라 **아무것도 안 남기고** 나갔습니다.
                여기서 나간 손님을 다시 부를 고리가 없었습니다.
                손에 뭔가를 들고 나가게 합니다.
            */}
            <button className="btn gh" onClick={() => router.push("/summary")}>
              오늘은 여기까지 · 본 것을 한 장으로 받겠습니다
            </button>
          </>
        )}
      </Shell>
    );
  }

  /* d2 · 결제 */
  /* ── d1b · 엿보기 ─────────────────────────────────── */
  if (step === "d1b") {
    const tier = tiers?.find((t) => t.id === pick);
    return (
      <Shell screen="d1b" title="무엇이 열리는가" onBack={() => router.push("/pay?step=d1")}>
        {/* ★ 접힌 두루마리(fold)는 페이월(c4)이 씁니다. 잇달아 나오는
            두 화면이 같은 그림이면 손님은 화면이 안 넘어간 줄 압니다
            (tests/test_scene_not_shared.py). 「열리는 문」을 되살렸습니다 —
            문이 열리며 빛이 새는데 안은 아직 안 보이는 그림이오. */}
        <Scene id="door" />
        <Narration lines={["도령이 접힌 자리에 손을 얹었다.",
                           "아직 펴지는 않았다."]} />
        <Say who={charName} lens={s.cur}>
          {you}가 고른 것은 「{tier?.name ?? "그 목패"}」요. 여기 적힌
          물음은 그대의 8글자에서 나온 것이오 — 아무에게나 하는 말이
          아니오.
          <br />
          앞머리만 보이고 나머지는 안 보내오. 흐려 놓은 게
          아니라 <b>여기 없소</b> — 브라우저를 뒤져도 안 나오오.
          그게 이 집이 값을 받는 방식이오.
          <br />
          근거는 안 가리오. 무엇을 보고 한 말인지는 값을 치르기
          전에도 보이오. 대 보고 아니다 싶으면 돌아가시오.
          <br />
          <b>여기서 창을 닫고 며칠 생각난 적이 있었소.</b> 값이
          아까워서가 아니라, 뭐라 적혀 있었을까가 남아서요.
          <br />
          참고 미뤄 두면 그 자리가 더 커지오. 그 마음을 알고 하는
          말이니 오늘 안 여셔도 되오.
          <br />
          이 집은 하루에 2번까지만 받고, 한 자리에 2명까지만 붙이오.
          내일도 같은 자리에 있소.
          <br />
          아래 흐린 칸은 글을 가린 게 아니라 <b>빈 칸</b>이오.
          자물쇠 안쪽이 안 보이는 것처럼, 열기 전에는 여기 아무것도
          없소. 물음 6개에 근거 6줄은 지금 다 보이오.
        </Say>

        {err && <Say who="도령" lens="pungun">{err}</Say>}
        {!peek && !err && <p className="sm">접힌 자리를 세는 중이오…</p>}

        {peek && peek.map((r, i) => (
          <div className="peek" key={r.lens_id + i}>
            <div className="pk">
              <b>{r.lens_name}</b>
              <span>{r.ask}</span>
            </div>
            {/*
              ★ 가린 칸은 **글자가 아니라 길이**입니다.
                서버가 안 보낸 것을 화면이 그릴 수는 없습니다.
                남은 글자 수만큼 칸을 그립니다.
            */}
            <p className="pkbody">
              {r.head}
              <span className="pkmask" aria-label={`가려진 ${r.mask}자`}>
                {"▒".repeat(Math.min(22, Math.max(6, Math.round(r.mask / 12))))}
              </span>
            </p>
            <span className="src">근거 · {r.source}</span>
            <p className="pkmore">
              여기서부터 <b>{r.mask}자</b>가 더 있소 ·
              {" "}약 {Math.max(1, Math.round(r.chars / 550))}분치
            </p>
          </div>
        ))}

        {peek && peek.length > 0 && (
          <ActOut kind="끊긴 동작" next="값을 치르다">
            지금 안 보이는 글자가 <b>{hidden.toLocaleString()}자</b>요.
            <br />
            <b>물음은 그대 것이고, 답은 아직 내 쪽에 있소.</b>
          </ActOut>
        )}

        <button className="btn mt" onClick={() => router.push("/pay?step=d2")}>
          값을 치르고 펴겠습니다
        </button>
        {/* ★ 물러설 길은 늘 둡니다. 브레이크는 매출보다 앞섭니다. */}
        <button className="btn gh" onClick={() => router.push("/pay?step=d1")}>
          다른 목패를 보겠습니다
        </button>
        <button className="btn gh" onClick={() => router.push("/lobby")}>
          오늘은 여기까지 하겠습니다
        </button>
      </Shell>
    );
  }

  if (step === "d2") {
    const tier = tiers?.find((t) => t.id === pick);

    /* 결제창에서 막 돌아왔다 — 승인이 끝날 때까지 아무것도 누르지 못하게 */
    if (settling) {
      return (
        <Shell screen="d2" title="값을 치르다" legal>
          <Scene id="coin" />
          <Narration lines={["값이 건너가는 중이오.", "잠시만 기다리시오."]} />
          <p className="sm mt" style={{ textAlign: "center" }}>
            창을 닫지 마시오.
          </p>
        </Shell>
      );
    }

    return (
      <Shell screen="d2" title="값을 치르다" legal>
        <Scene id="coin" />
        {/*
          ★ 값부터 들이밀고 있었습니다. 스물일곱 화면에서 **여는 줄이
            아예 없는** 유일한 자리였는데, 하필 지갑을 여는 자리입니다.
            무슨 일이 벌어지는지 한 줄 놓고 시작합니다.
        */}
        <Narration lines={["도령이 셈한 종이를 상 위에 올려놓았다.",
                           "값이 적힌 목패가 그 옆에 섰다."]} />
        {/*
          ★ 79점이던 자리. 팩폭 46 · 울림 45 — 값과 컷 수만 있고
            **지갑을 여는 사람 얘기**가 없었습니다. 여기서 파는 말을
            더하면 안 되니, 물러설 길을 먼저 적습니다.
        */}
        <Say who="도령" lens="pungun">
          여기서 손이 한 번 멈추오. 값이 아까워서가 아니라, 치르고 나서
          별것 아니면 어쩌나 싶어 망설이는 것이오.
          <br />
          <b>여태 그런 자리에서 창을 닫아 본 적이 있었소.</b> 참고
          닫았는데 며칠 생각났을 것이오 — 아까워서가 아니라 안 본
          채로 남아서요.
          <br />
          그러니 이것만 아시오. 값은 <b>지금 보이는 그대로</b> 청구되오 —
          목패에 적힌 수가 곧 청구서요. 다른 이름으로 더 붙는 것은
          1원도 없소.
          <br />
          {" "}이 집은 하루에 2번까지만 받고, 한 자리에 2명까지만
          붙이오. 물러 달라 하시면 물러 드리오 — 저울에 올린 것을
          도로 내려놓는 것처럼요.
        </Say>

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
            {/*
              ★ 이 수가 어디서 나온 것인지 한 번도 안 밝혔습니다.
                컷 수는 **서버가 이 명식으로 실제로 뽑아 셉니다**
                (`POST /v1/pay/tiers`). 미리 적어 둔 홍보 문구였던 적이
                있어서 — 「18컷」이라 적고 11컷이 나갔습니다 — 어디서 센
                수인지를 값 옆에 답니다.
            */}
            <span className="src">
              근거 · 컷 수와 글자 수는 이 명식으로 실제로 뽑아 센 것이오
            </span>
            <p className="sm">
              이 값은 <b>이 자리 하나</b> 값이오. 스무 사람을 다 사는 것이
              아니라 <b>한 사람의 눈</b>을 빌리는 셈이오 — 목패에 적힌 값이
              그대로 건너가오.
            </p>
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
                    /*
                     * ★ 사업자 표시가 없으면 값을 안 받습니다.
                     *
                     *   전자상거래법 제10조는 파는 사람이 누구인지를
                     *   밝히라 합니다. 표시 없이 돈을 받으면 미신고
                     *   영업으로 보입니다. 결제 열쇠가 없으면 거절하는
                     *   것과 **같은 규칙**입니다 — 열린 쪽이 기본이면
                     *   언젠가 그대로 배포됩니다.
                     *
                     *   무료 구간은 그대로 열어 둡니다. 표시 의무는
                     *   **판매**에 붙는 것이라, 안 파는 동안 서비스를
                     *   닫을 이유가 없습니다.
                     */
                    if (!SELLABLE) {
                      throw new Error(
                        "아직 값을 받을 수 없소. 가게 표시가 덜 되었소."
                      );
                    }
                    await openCheckout({
                      clientKey: order.client_key,
                      orderId: order.order_id,
                      amount: order.amount,
                      orderName: tier?.name ?? "성신당",
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
                값을 치르겠습니다
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
            <ActOut kind="끊긴 동작" next="감춰 둔 자리">
              값이 건너가면 <b>그 자리에서</b> 열리오. 기다릴 것 없소.<br />
              마음이 바뀌면 <b>7일 안에</b> 도로 무르오 — 안 연 자리는 그대로 돌려주오.
            </ActOut>
            <button className="btn gh" onClick={() => router.push("/pay?step=d1")}>
              다시 고르겠습니다
            </button>
          </>
        )}
      </Shell>
    );
  }

  /* d3 · 완료 */
  if (step === "d3") {
    return (
      <Shell screen="d3" title="열렸소">
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
        {/*
          ★ 여기가 넷째로 낮았습니다 (연출 54).

            「잘 오셨소」 한 줄이 전부였습니다. 값을 치른 **직후**인데
            치른 사람 얘기가 없어서, 인장과 컷 수만 뜨는 영수증
            화면이 됐습니다. 울림 20 · 명확 43 이 거기서 나왔습니다.

            더 팔려고 붙이는 말이 아닙니다. 여기서 할 일은 **판 것을
            줄이는 것**입니다 — 하루 2번 상한과 인장 1개를 다시
            말하고, 다 읽고 나서 무엇을 하면 되는지까지 적습니다.
        */}
        <Say who={charName} lens={s.cur}>
          잘 오셨소. 이제 감춰 둔 자리를 펴 드리리다.
          <br />
          {you}는 여기 오기까지 창을 닫았다 다시 열었소. 값이
          아까워서가 아니라, 안 맞으면 어쩌나 싶어 미룬 것이오.
          <b> 여태 그런 식으로 미뤄 둔 것이 하나 더 있소.</b>
          <br />
          붉은 끈은 한 번 풀면 다시 못 묶소. 그러니 오늘은 이것으로
          그만두시오 — 이 집은 하루에 2번까지만 받고, 한 자리에
          2명까지만 붙이오.
          <br /> 그 둘째 것도 웬만하면 말리오. 인장은
          1개 찍혔고, 남은 자리는 내일도 그대로 있소.
          <br />
          글은 두루마리처럼 위에서 아래로 한 컷씩 뜨오. 훑지 말고
          손가락으로 짚어 가며 보시오.
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
            마찰을 0으로 둬야 할 구간입니다. 표지는 다시 읽으러 올 때 씁니다. */}
        <button className="btn mt"
                onClick={() => router.push("/report/" + s.cur + "?tab=c2")}>
          바로 읽겠습니다
        </button>
      </Shell>
    );
  }

  /* d1 · 어디까지 */
  return (
    <Shell screen="d1" title="어디까지 볼지">
      <Scene id="tray" />
      <Narration lines={["목패 셋이 상 위에 놓였다.",
                         "도령이 그 앞에서 손을 뗀다."]} />
      {/*
        ★ 이 자리가 스물일곱 중 가장 낮았습니다 (연출 48).

          목패 셋과 버튼만 있었습니다. 값을 견주는 자리인데 **누구
          얘기인지가 없어서**, 손님은 남의 상 앞에 선 사람이 됩니다.
          울림이 0 이었던 까닭입니다.

          그래서 목패 앞에 한 마디를 답니다 — 여기까지 온 사람이
          이미 한 일(무료 6단을 다 본 것)을 짚고, 이 집이 스스로
          건 브레이크(하루 2번 · 한 자리 2명)를 먼저 말합니다.
          파는 자리에서 상한을 먼저 말하는 게 이 집의 방식입니다.
      */}
      <Say who="도령" lens="pungun">
        그대는 값 없이 여는 6단을 이미 다 보셨소.
        <br />
        거기서 그만두지 못하고 여기까지 오셨을 게요.
        <br />
        <b>고르기를 미루는 사람일수록 오래 서 있소.</b>
        {" "}상 앞에서 망설이는 것은 값이 아까워서가 아니라,
        고르고 나면 되돌릴 수 없다는 걸 알아서요.
        <br />
        이 집은 하루에 2번까지만 받고, 한 자리에 사람을 2명까지만
        붙이오. 목패는 3장이고 그중 1장만 고르는 것이오.
          <br /> 팔 수 있는 만큼 파는 집이 아니라 <b>재 놓고 파는
        집</b>이라 그렇소. 목패는 저울 눈금처럼 칸이 갈려 있소 —
        칸마다 컷 수와 글자 수를 적어 두었으니 견주어 보시오.
      </Say>
      <span className="src">
        근거 · 목패 3장 · 컷 수와 글자 수는 이 명식으로 실제로 뽑아
        센 것이오 (미리 적어 둔 홍보 문구가 아니오) · 하루 2번 ·
        한 자리 2명
      </span>
      <p className="pickme">
        {pick ? <><b>고르셨소.</b> 아래에서 여시오.</>
              : <><b>목패를 눌러 고르시오.</b> 고르기 전에는 안 열리오.</>}
      </p>
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
      <ActOut kind="딜레마" next="값을 치르다">
        셋을 다 열 수는 없소.
        <br />
        고르는 것은 <b>어느 목패</b>가 아니라, 그대가 여태 안 물어본
        것 중 <b>무엇을 먼저 물을 것인가</b>요. 나머지는 오늘 안 열리오.
      </ActOut>
      {/*
        ★ 고르고 나서 곧바로 결제창으로 보내지 않습니다 (2026-09-04).

          손님이 시킨 것 — "누르면 다음에는 각 캐릭터들이 나와서
          «당신에게 가장 중요한 건 ~~» 블러 처리하고 … 궁금해서 결제
          안 하고는 미칠 정도로."

          엿보기 한 자리를 사이에 둡니다. 거기서 보이는 것은 **이미
          계산된 그 사람의 컷**이고, 답은 서버에 남습니다.
      */}
      <button className="btn mt" disabled={!pick}
              onClick={() => router.push("/pay?step=d1b")}>
        {pick ? "무엇이 열리는지 보겠습니다" : "먼저 목패를 고르시오"}
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
