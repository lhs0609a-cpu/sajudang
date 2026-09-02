"use client";

/**
 * @screen c1 c2 c3 c4 c5 c6
 * C · 읽다 — c1 표지 · c2 웹툰 · c3 대운맵 · c4 페이월 · c5 공유카드 · c6 피드백
 *
 * ★ 잠긴 컷은 본문이 아예 내려오지 않습니다. 블러로 가린 게 아니라
 *   서버가 안 줍니다. (docs/02 §7)
 */
import { Suspense, useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Shell from "@/components/Shell";
import Scene from "@/components/scene/Scene";
import ExtraAsk from "@/components/ExtraAsk";
import Reveal from "@/components/Reveal";
import Thinking from "@/components/Thinking";
import { Narration, Say } from "@/components/Narration";
import { api, ApiError } from "@/lib/api";
import { LENS_BY_ID } from "@/lib/lenses";
import { useSession } from "@/lib/store";
import { thinkOf } from "@/lib/think";
import type { ReportResponse } from "@shared/chart";

type Tab = "c1" | "c2" | "c3" | "c4" | "c5" | "c6";

const TABS: Tab[] = ["c1", "c2", "c3", "c4", "c5", "c6"];

/*
 * 두루마리를 펴는 동안 찍는 줄.
 *
 * ★ 넷 다 **실제로 이 사이에 서버가 하는 일**입니다. 지어낸 뜸이
 *   아닙니다 — 근거 줄에 같은 말이 그대로 적혀 나옵니다.
 *   (engine/report.py 의 컷 순서와 같습니다)
 */
const OPENING_BEATS = [
  "여덟 글자를 다시 펴는 중",
  "월지와 일지를 견주는 중",
  "대운을 십 년 단위로 세는 중",
  "이 사람 눈으로 다시 읽는 중",
];
/** 뜸 넉 줄이 다 서는 데 걸리는 시간. Thinking 의 박자와 맞춥니다. */
const OPENING_MS = 260 + OPENING_BEATS.length * 760 + 320;

/** 두루마리를 얼마나 내려왔는가. 얇은 막대 한 줄. */
function ScrollProgress() {
  const [pct, setPct] = useState(0);
  useEffect(() => {
    const on = () => {
      const h = document.documentElement;
      const max = h.scrollHeight - h.clientHeight;
      setPct(max > 0 ? Math.min(100, Math.round((h.scrollTop / max) * 100)) : 0);
    };
    on();
    window.addEventListener("scroll", on, { passive: true });
    window.addEventListener("resize", on);
    return () => {
      window.removeEventListener("scroll", on);
      window.removeEventListener("resize", on);
    };
  }, []);
  return (
    <div className="rprog noprint" aria-hidden>
      <i style={{ width: `${pct}%` }} />
    </div>
  );
}


function ReportInner() {
  const params = useParams<{ id: string }>();
  const query = useSearchParams();
  const router = useRouter();
  const s = useSession();
  const lensId = params.id;
  const lens = LENS_BY_ID[lensId];

  const asked = query.get("tab") as Tab | null;
  const [tab, setTab] = useState<Tab>(asked && TABS.includes(asked) ? asked : "c1");
  useEffect(() => { if (asked && TABS.includes(asked)) setTab(asked); }, [asked]);
  const [rep, setRep] = useState<ReportResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [rating, setRating] = useState(0);
  /* 뜸이 끝났는가. 서버가 빨라도 이 장면을 지우지 않습니다 (a6 과 같은 결). */
  const [opened, setOpened] = useState(false);

  /*
   * 이 캐릭터가 따로 받는 것.
   *
   * ★ 서버는 `needs_input` 으로 무엇이 필요한지 말하고 있었는데
   *   **화면이 그걸 한 번도 안 읽었습니다.** 그래서 그 컷이 조용히
   *   사라졌습니다 — 재보니 51.3%입니다. 값을 치른 사람도 잃습니다.
   *   저장하지 않습니다: 요청에 실어 보내고 그걸로 끝입니다.
   */
  const [extras, setExtras] = useState<Record<string, unknown> | null>(null);
  const [asking, setAsking] = useState(false);

  /*
   * ★ 캐릭터를 옮겨도 앞사람 것이 그대로 남아 있었습니다.
   *
   *   `/report/[id]` 는 같은 화면이라 이름표만 바뀝니다. 리액트는
   *   그걸 같은 자리로 보고 **상태를 물려줍니다.** 그래서
   *
   *     · 갑에게 적은 추가 입력(extras)이 을에게 그대로 실려 갔습니다.
   *       을은 그림을 묻는데 갑에게 적은 혈액형이 갑니다.
   *     · 갑에서 한 번 깨지면(err) 을로 옮겨도 그 오류 화면이 계속
   *       떴습니다. 새 글이 도착해도 err 가 안 지워져 안 보입니다.
   *
   *   그리는 중에 바로 지웁니다(리액트가 권하는 자리). 효과로 지우면
   *   앞사람 것으로 한 번 부르고 다시 부릅니다.
   */
  const [seenLens, setSeenLens] = useState(lensId);
  if (seenLens !== lensId) {
    setSeenLens(lensId);
    setExtras(null);
    setAsking(false);
    setErr(null);
    setRep(null);
    /* 사람이 바뀌면 뜸도 처음부터. 새 사람이 새로 읽는 것입니다. */
    setOpened(false);
  }

  /*
   * 후기 — ★ 여기가 받는 척만 하고 버리던 자리입니다.
   *
   *   별점은 화면 상태만 바꿨고, 후기 칸에는 value 도 onChange 도
   *   없었습니다. 손님이 친 글자는 **버튼을 누르는 순간 사라졌습니다.**
   *   바로 아래에는 "결제하고 끝까지 읽은 분의 후기에만 '결제 확인됨'
   *   표시가 붙습니다" 라고 적혀 있었는데, 붙일 후기가 한 건도 저장되지
   *   않았습니다.
   */
  const [reviewBody, setReviewBody] = useState("");
  const [reviewSay, setReviewSay] = useState<string | null>(null);
  const [reviewBusy, setReviewBusy] = useState(false);
  const [reviewSent, setReviewSent] = useState(false);

  const hasReview = rating > 0 || reviewBody.trim().length > 0;

  async function sendReview() {
    if (!hasReview || reviewSent || reviewBusy) return;
    setReviewBusy(true);
    try {
      /* '결제 확인됨' 은 서버가 치른 주문을 보고 정합니다.
         여기서 paid 를 실어 보내지 않습니다 — 그건 광고 문구를
         손님이 스스로 다는 것과 같습니다. */
      const r = await api.review({
        lens_id: lensId, rating: rating || null, body: reviewBody,
        session_id: s.sessionId, chart_id: s.chartId ?? undefined,
      });
      setReviewSay(r.say);
      setReviewSent(true);
    } catch (e) {
      setReviewSay(e instanceof ApiError ? e.message : "말을 받아 두지 못했소.");
    } finally {
      setReviewBusy(false);
    }
  }

  /* 고리 — 공유 링크. 생년월일시는 담기지 않습니다. (services/api/routers/share.py) */
  const [sharing, setSharing] = useState(false);
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [shareMsg, setShareMsg] = useState<string | null>(null);

  /* 종이에 찍히는 날. 인쇄물에 언제 뽑았는지가 없으면 나중에 못 알아봅니다. */
  const printedOn = new Date().toLocaleDateString("ko-KR", {
    year: "numeric", month: "long", day: "numeric",
  });

  async function makeLink() {
    if (!s.chartId) return;
    if (shareUrl) {
      await copy(shareUrl);
      return;
    }
    setSharing(true);
    setShareMsg(null);
    try {
      const r = await api.share({
        chart_id: s.chartId, concern: s.concern, axis4: s.axis4,
        lens_id: lensId, name: s.name, from_name: s.name,
      });
      const url = window.location.origin + r.path;
      setShareUrl(url);
      await copy(url);
    } catch (e) {
      setShareMsg(e instanceof ApiError ? e.message : "고리를 엮지 못했소.");
    } finally {
      setSharing(false);
    }
  }

  async function copy(url: string) {
    try {
      await navigator.clipboard.writeText(url);
      setShareMsg("고리를 옮겨 담았소 — " + url);
    } catch {
      /* 클립보드를 막아 둔 브라우저가 있습니다. 그럴 땐 주소를 보여 줍니다. */
      setShareMsg("이 고리를 쓰시오 — " + url);
    }
  }

  useEffect(() => {
    if (!s.chartId) return;
    let alive = true;
    api.report({
      chart_id: s.chartId, lens_id: lensId, tier: s.tier,
      session_id: s.sessionId, concern: s.concern, axis4: s.axis4,
      name: s.name, extras,
    })
      .then((r) => {
        if (!alive) return;
        setRep(r);
        setAsking(false);
        // ★ 서버가 낮춰서 보냈으면 우리 기록이 틀린 것입니다.
        //   여기 적힌 tier 는 치른 것이 아니라 **보여 준 것**이라,
        //   맞춰 두지 않으면 화면이 계속 없는 값을 부릅니다.
        if (r.tier !== s.tier) s.set({ tier: r.tier as typeof s.tier });
      })
      .catch((e) => {
        if (!alive) return;
        // ★ 실패했을 때 `asking` 을 안 껐습니다. 추가 입력을 넣고 요청이
        //   깨지면 그 버튼이 「다시 펴는 중이오」 에서 영영 안 풀렸습니다.
        setAsking(false);
        setErr(e instanceof ApiError ? e.message : "리포트를 펴지 못했소.");
      });
    return () => { alive = false; };
  }, [s.chartId, lensId, s.tier, s.concern, s.axis4, s.sessionId, extras]);

  /*
   * 뜸은 **글이 도착한 뒤부터** 셉니다. 도착 전부터 세면 느린 날에는
   * 뜸이 끝나고도 빈 화면이 남습니다.
   */
  useEffect(() => {
    if (!rep || opened) return;
    const t = setTimeout(() => setOpened(true), OPENING_MS);
    return () => clearTimeout(t);
  }, [rep, opened]);

  if (!s.chartId) {
    return (
      <Shell title="읽다">
        <Narration lines={["먼저 글자를 세워야 하오."]} />
        <button className="btn mt" onClick={() => router.push("/")}>내 사주부터 본다</button>
      </Shell>
    );
  }
  if (err) {
    /*
     * ★ 여기가 막다른 화면이었습니다.
     *   오류 문구만 있고 버튼이 하나도 없어서, 한 번 깨지면 뒤로 버튼
     *   말고는 나갈 길이 없었습니다. 값을 치른 사람일 수도 있습니다.
     */
    return (
      <Shell title="읽다">
        <Say who={lens?.name ?? "도령"} lens={lensId}>{err}</Say>
        <button className="btn mt" onClick={() => {
          setErr(null); setExtras(null); setRep(null);
        }}>
          다시 펴 본다
        </button>
        <button className="btn gh" onClick={() => router.push("/lobby")}>
          진열대로
        </button>
        <button className="btn gh" onClick={() => router.push("/me")}>
          치른 것을 못 찾겠소
        </button>
      </Shell>
    );
  }
  /*
   * ★ 여기가 "두루마리를 편다." 한 줄이던 자리입니다.
   *
   *   그 사이에 서버는 명식을 다시 읽고, 대운을 세고, 그 캐릭터 몫의
   *   관점 컷을 짓습니다. 진짜로 일하는데 화면은 한 줄이었고, 빠를
   *   때는 그 한 줄조차 안 보이고 열여덟 컷이 통째로 떨어졌습니다.
   *   손님이 2026-09-02 에 그걸 짚었습니다 — "너무 빨라. 나오는
   *   속도가 기대감도 어느 정도 줘야지."
   *
   *   그래서 무엇을 보는 중인지 한 줄씩 찍고, 다 찍기 전에는 넘기지
   *   않습니다. 건너뛰는 길은 냅니다.
   */
  if (!rep || !opened) {
    return (
      <Shell title="읽다">
        <Scene id="scroll" className="hero" />
        <Thinking
          who={lens?.name}
          lines={OPENING_BEATS}
          onSkip={rep ? () => setOpened(true) : undefined}
        />
        {!rep && (
          <p className="sm mt">
            글은 다 펼치면 한 컷씩 뜨오. 내리는 만큼만 나오니 서두르지 마시오.
          </p>
        )}
      </Shell>
    );
  }

  const daeunCut = rep.cuts.find((c) => c.id === "daeun_map");

  /* c1 · 표지 */
  if (tab === "c1") {
    return (
      <Shell title={`${rep.lens.name} · 표지`}>
        <Scene id="scroll" className="hero" />
        <div style={{ textAlign: "center" }}>
          <p style={{ fontFamily: "var(--serif)", fontSize: 24, color: lens?.color ?? "var(--c)" }}>
            {rep.lens.name}
          </p>
          <p className="sm">{rep.lens.hanja} · {rep.lens.group}</p>
          <p className="sm mt">
            {s.name ? `${s.name}의 ` : ""}여덟 글자를 {rep.lens.name}의 눈으로 본 것
          </p>
          <p className="sm">
            읽는 자리 {rep.cuts.length}컷
            {rep.locked.length > 0 && ` · 잠긴 자리 ${rep.locked.length}컷`}
          </p>
        </div>
        <button className="btn mt" onClick={() => setTab("c2")}>내 것을 편다</button>
      </Shell>
    );
  }

  /* c3 · 대운 맵 */
  if (tab === "c3") {
    return (
      <Shell title="대운 맵">
        <Scene id="roadmap" />
        {daeunCut ? (
          <>
            <span className="src">근거 · {daeunCut.source}</span>
            <div className="cutbody" dangerouslySetInnerHTML={{ __html: daeunCut.html }} />
          </>
        ) : (
          <>
            <Narration lines={["대운 맵은 아직 잠겨 있소."]} />
            {rep.sells && (
              <button className="btn mt" onClick={() => setTab("c4")}>어디까지 볼지 고른다</button>
            )}
          </>
        )}
        <button className="btn gh mt" onClick={() => setTab("c2")}>본문으로</button>
      </Shell>
    );
  }

  /* c4 · 페이월 — ★ 안 파는 자리에서는 아예 안 그립니다 */
  if (tab === "c4" && !rep.sells) {
    return (
      <Shell title={rep.lens.name}>
        <Scene id="oldpaper" />
        {/* 청동자는 무거운 리포트 뒤에 붙는 안전망입니다.
            여기서는 값을 권하지 않습니다. 브레이크는 매출보다 앞섭니다. */}
        <Say who={rep.lens.name} lens={lensId}>여기선 값을 받지 않소. 본 것이 전부요.</Say>
        <button className="btn mt" onClick={() => setTab("c2")}>본문으로</button>
      </Shell>
    );
  }
  if (tab === "c4") {
    return (
      <Shell title="여기서부터" legal>
        <Scene id="fold" />
        <Narration lines={["두루마리가 반쯤 접혀 있다."]} />
        <Say who={rep.lens.name} lens={lensId}>
          여기까지가 값 없이 하는 얘기요. 나머지에는 <b>왜</b>와 <b>언제</b>가 들어 있소.
        </Say>
        {/*
          ★ 여기가 `가가가가 가가가가가 가가가` 였습니다. 자리표시
            문자열이 그대로 배포돼 있었습니다.

            궁금증은 **구체적일 때만** 생깁니다 — 무엇을 놓치는지 모르면
            아쉽지도 않습니다. 이제 서버가 그 컷의 첫 줄을 잘라서
            내려보냅니다 (engine/report._teaser). 본문의 40%를 넘지
            않고, 조사에서 끊기지 않습니다.

            읽히는 것은 맛보기까지. 그 뒤에 흐려진 자락을 이어 붙여
            **이 아래로 더 있다**는 것만 보입니다.
        */}
        {rep.locked.map((l) => (
          <div className="dz" key={l.id}>
            <div className="k">{l.title}</div>
            <p className="sm">근거 · {l.source}</p>
            {l.teaser ? (
              <p className="tz">
                {l.teaser}
                <span className="bl">그 다음은 값을 치른 뒤에 보이오</span>
              </p>
            ) : (
              <p className="bl">가려 둔 자리요</p>
            )}
            {/* 분량은 서버가 셉니다. 화면이 적지 않습니다. */}
            <p className="sm">
              {l.need_tier_name}부터 열리오 · {l.chars.toLocaleString()}자
            </p>
          </div>
        ))}
        <button className="btn mt" onClick={() => router.push("/pay?step=d1")}>
          어디까지 볼지 고른다
        </button>
        <button className="btn gh" onClick={() => setTab("c2")}>본문으로</button>
      </Shell>
    );
  }

  /* c5 · 공유 카드 */
  if (tab === "c5") {
    const nameCut = rep.cuts.find((c) => c.id === "lack");
    return (
      <Shell title="공유 카드">
        <div className="card">
          <Scene id="cardbg" />
          <div className="cardin">
            <p className="sm">성신당 星辰堂</p>
            <p style={{ fontFamily: "var(--serif)", fontSize: 20, color: "var(--c)" }}>
              {s.features?.day_gan} 일간 · {s.features?.strength}
            </p>
            {nameCut && (
              <p className="sm">가장 약한 것 {s.features?.weak_el} · 흐름 {s.features?.flow}</p>
            )}
            <p className="sm">— {rep.lens.name}</p>
          </div>
        </div>
        <p className="sm mt">
          중앙 문양은 에셋이 들어오면 교체됩니다. (docs/10 §5 — 정지 PNG 필수)
        </p>
        <button className="btn gh mt" onClick={() => setTab("c6")}>다 읽었소</button>
      </Shell>
    );
  }

  /* c6 · 피드백 */
  if (tab === "c6") {
    return (
      <Shell title="남기다" legal>
        <Scene id="wall" />
        <Say who={rep.lens.name} lens={lensId}>어떻게 보셨소?</Say>
        <div className="og c2" style={{ gridTemplateColumns: "repeat(5,1fr)" }}>
          {[1, 2, 3, 4, 5].map((n) => (
            <button key={n} className={`op ${rating === n ? "on" : ""}`}
                    style={{ textAlign: "center" }} onClick={() => setRating(n)}>
              {"★".repeat(n)}
            </button>
          ))}
        </div>
        <textarea
          className="fld"
          rows={4}
          placeholder="남기고 싶은 말"
          maxLength={1000}
          value={reviewBody}
          disabled={reviewSent}
          onChange={(e) => setReviewBody(e.target.value)}
        />
        <p className="sm">
          결제하고 끝까지 읽은 분의 후기에만 &quot;결제 확인됨&quot; 표시가 붙습니다.
          대가를 주고받은 글은 싣지 않습니다.
        </p>
        {/* 연락처를 적어 두고 가는 손님이 있습니다. 미리 말합니다. */}
        <p className="sm">
          연락처나 주민번호가 섞이면 저장하기 전에 지웁니다. 보관할 이유가 없소.
        </p>

        {reviewSay ? (
          <Say who={rep.lens.name} lens={lensId}>{reviewSay}</Say>
        ) : (
          <button
            className="btn mt"
            disabled={!hasReview || reviewBusy}
            onClick={sendReview}
          >
            {reviewBusy ? "받아 적는 중이오" : "남긴다"}
          </button>
        )}

        <button className="btn gh mt" onClick={async () => {
          /* 아직 안 보낸 말이 있으면 나가기 전에 보냅니다.
             손님이 친 글자를 버리지 않습니다. */
          await sendReview();
          if (!s.seals.includes(lensId)) s.set({ seals: [...s.seals, lensId] });
          router.push("/relay");
        }}>
          인장을 받고 나간다
        </button>
      </Shell>
    );
  }

  /* c2 · 본문 — 두루마리 */
  const body = rep.cuts.filter((c) => c.id !== "daeun_map");
  const pillars = s.features?.pillars ?? [];

  return (
    <Shell title={rep.lens.name}>
      {/*
        ★ 18~22컷이 진행 표시 없이 한 두루마리로 이어졌습니다.
          어디쯤 읽고 있는지, 얼마나 남았는지가 없어서 중도 이탈이 그대로
          미완독이 됩니다 — 미완독은 후기도 재구매도 없습니다.
          훅에서 이미 단계 감각을 만들어 놨으니 결이 맞습니다.
      */}
      <ScrollProgress />
      <Scene id="oldpaper" />

      {/* ★ 추가 입력이 틀렸을 때. 리포트를 통째로 막지 않습니다 —
          그 컷만 빠지고 무엇이 틀렸는지 말해 줍니다. */}
      {/* ★ 이 캐릭터가 따로 받는 것. 안 물으면 그 컷이 조용히 사라집니다. */}
      {rep.needs_input && !rep.extra_error && (
        <ExtraAsk
          /* ★ 고른 것이 다음 캐릭터로 넘어갔습니다. 갑에게 고른 「A형」이
             남아 있어 을의 그림 물음에서 곧바로 「이걸로 보시오」가 켜지고,
             누르면 그림 자리에 혈액형이 실려 갔습니다. */
          key={lensId + ":" + rep.needs_input}
          need={rep.needs_input}
          busy={asking}
          onSubmit={(x) => { setAsking(true); setExtras(x); }}
        />
      )}

      {rep.extra_error && (
        <div className="warn noprint">
          <p>{rep.extra_error}</p>
          <p className="sm">
            그 자리 하나만 접었소. 나머지는 아래 그대로 있소.
          </p>
        </div>
      )}

      <div className="scroll" id="scroll">
        <div className="scrollhead">
          <p className="who">{rep.lens.name}</p>
          <p className="hanja">{rep.lens.hanja}</p>
          {pillars.length > 0 && (
            <div className="eight">
              {pillars.map((p) => <span key={p.label}>{p.gz}</span>)}
            </div>
          )}
          <p className="cnt">
            읽는 자리 {rep.cuts.length}컷
            {rep.locked.length > 0 && ` · 잠긴 자리 ${rep.locked.length}컷`}
          </p>
        </div>

        {rep.opening && (
          <p className="saying" dangerouslySetInnerHTML={{ __html: rep.opening }} />
        )}

        {/*
          ★ 한 컷씩 뜹니다 (2026-09-02).

            전에는 열여덟~스물두 컷이 한꺼번에 쏟아졌습니다. 그러면
            손님은 읽는 게 아니라 **훑습니다.** 한 컷씩 뜨면 그 컷
            하나를 보게 되고, 읽는 속도를 손님이 정합니다.

            뜨기 전 한 줄은 그 컷이 **실제로 보는 자리**입니다 —
            근거 줄에서 뽑습니다(lib/think.ts). 지어낸 뜸이 아니라
            대 볼 수 있는 말이라야 합니다.

            첫 컷은 이미 화면에 있으니 기다리지 않습니다(eager).
        */}
        {body.map((c, i) => (
          <Reveal key={c.id} think={thinkOf(c.source)} eager={i === 0}>
            <div className={"blk in" + (c.id.startsWith("lc_") ? " own" : "")}>
              {/* ★ 끝이 끝으로 읽히게 합니다.
                  closing_cut 의 자리 고정은 이미 돼 있는데, 손님은 그게
                  마지막인 줄 모른 채 지나갑니다. 기억은 마지막이 지배합니다. */}
              {i === body.length - 1 && body.length > 1 && (
                <p className="lastcut">이제 마지막 자리요.</p>
              )}
              <div className="lab">{c.title}</div>
              {/* ★ 근거를 본문 위에, 본문과 같은 급으로 둡니다.
                  전에는 8.5px 딱지라 아무도 안 봤습니다. */}
              <span className="src">{c.source}</span>
              <div className="cutbody"
                   dangerouslySetInnerHTML={{ __html: c.html }} />
            </div>
          </Reveal>
        ))}

        {rep.closing && (
          <p className="saying close"
             dangerouslySetInnerHTML={{ __html: rep.closing }} />
        )}

        {/* 종이에만 실립니다 — 어디서 나온 종이인지 */}
        <div className="printfoot">
          성신당 星辰堂 · {rep.lens.name}이 본 것 · {printedOn}
          <br />
          여덟 글자는 하나요. 읽는 눈이 스물이오.
          맞힌다는 말은 하지 않소 — 무엇을 보고 한 말인지만 적어 두었소.
        </div>
      </div>

      <div className="handles noprint">
        <button onClick={() => window.print()}>
          내 것을 종이로 받는다 (PDF)
        </button>
        <button onClick={() => void makeLink()} disabled={sharing}>
          {sharing ? "고리를 엮는 중…" : shareUrl ? "고리 다시 복사" : "고리 만들어 나누기"}
        </button>
        {rep.locked.length > 0 && (
          <button onClick={() => setTab("c4")}>잠긴 {rep.locked.length}컷</button>
        )}
        {daeunCut && <button onClick={() => setTab("c3")}>대운 맵</button>}
        <button onClick={() => setTab("c6")}>다 읽었소</button>
      </div>

      {shareMsg && <p className="handlenote noprint">{shareMsg}</p>}
      <p className="handlenote noprint">
        내려받기는 인쇄창에서 <b>“PDF로 저장”</b>을 고르면 되오.
        고리에는 <b>생년월일시와 고을이 담기지 않소</b> — 여덟 글자와 읽은
        자리만 가오. 90일이 지나면 스스로 닫히오.
      </p>
    </Shell>
  );
}

export default function ReportPage() {
  return (
    <Suspense fallback={<Shell title="읽다"><p className="sm">…</p></Shell>}>
      <ReportInner />
    </Suspense>
  );
}
