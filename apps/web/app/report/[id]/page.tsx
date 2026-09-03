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
import ActOut from "@/components/ActOut";
import { Narration, Say } from "@/components/Narration";
import { api, ApiError } from "@/lib/api";
import { LENS_BY_ID, youOf } from "@/lib/lenses";
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
  /* 이 사람이 손님을 부르는 말 (engine/lens.you_of 와 같은 규칙). */
  const you = youOf(lensId, s.name, s.sex);

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
        <button className="btn mt" onClick={() => router.push("/")}>내 사주부터 보겠습니다</button>
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
          다시 펴 보겠습니다
        </button>
        <button className="btn gh" onClick={() => router.push("/lobby")}>
          진열대로
        </button>
        <button className="btn gh" onClick={() => router.push("/me")}>
          치른 것을 못 찾겠습니다
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

  /*
   * 액트아웃이 쓰는 값 셋. **셈에서 나온 것만** 씁니다 —
   * 「곧 큰 일이 있소」 같은 지어낸 말은 이 집이 금지한 것입니다.
   *
   *   ownCount   그 캐릭터만 보는 자리(lc_) 가 몇인가
   *   firstOwn   그중 첫 자리의 이름 — 「더 있소」는 예고가 아닙니다
   *   nextTurn   다음으로 대운이 바뀌는 나이. 그 해에 무슨 일이 난다는
   *              말은 안 합니다. **읽는 자리가 바뀐다**는 말입니다.
   */
  const ownCuts = rep.cuts.filter((c) => c.id.startsWith("lc_"));
  const ownCount = ownCuts.length;
  const firstOwn = ownCuts[0];
  const nextTurn = (() => {
    const f = s.features;
    if (!f?.daeun || typeof f.daeun_now !== "number") return null;
    const nx = f.daeun[f.daeun_now + 1];
    return nx && typeof nx.start_age === "number" ? nx.start_age : null;
  })();

  /* c1 · 표지 */
  if (tab === "c1") {
    return (
      <Shell screen="c1" title={`${rep.lens.name} · 표지`}>
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
        <span className="src">
          근거 · 여덟 글자 하나 · {rep.lens.name}의 눈 하나 · 읽는 자리
          {" "}{rep.cuts.length}컷
        </span>
        <p className="sm">
          여덟 글자는 하나요. 읽는 눈이 스물이오.
          <b> 같은 산을 스무 군데서 그린 그림</b> 같은 것이라, 어느 그림도
          거짓이 아니고 어느 하나도 산 전부가 아니오.
        </p>
        {/*
          ★ 표지가 일곱째로 낮았습니다 (연출 57).

            이름과 컷 수와 「같은 산」 비유가 전부였습니다. 여는
            자리인데 **읽으러 온 사람 얘기가 없어서**, 책 표지에
            제목만 적힌 꼴이었습니다. 울림 20 · 팩폭 43.

            표지에서 본문을 미리 말하면 안 됩니다. 그래서 여기
            적는 건 **이 화면이 이미 아는 것**뿐입니다 — 기둥 4자리
            8글자, 이 사람이 먼저 보는 자리, 그리고 읽는 법.
        */}
        <Say who={rep.lens.name} lens={lensId}>
          {you}가 적어 낸 건 태어난 해·달·날·시 4자리요. 그걸 옮기니
          8글자가 되었소. 여기 적힌 건 전부 그 여덟에서 나온 것이라,
          없는 말은 한 줄도 안 얹었고 앞으로도 안 얹소.
          <br />
          <b>여태 사주를 본 적이 없지는 않을 것이오.</b>
          {" "}보고 나서도 안 믿긴 채로 덮어 둔 일이 있었소. 맞는
          말 같기는 한데 누구한테나 맞는 말 같아서, 물어보려다 참고
          혼자 접어 둔 것이오. 그래서 이 집은 칸마다 <b>근거 줄</b>을
          답니다 — 대 보시오. 못 대는 줄이 있으면 그건 내 잘못이오.
          <br />
          내가 먼저 보는 자리는 「{rep.lens.specialty ?? rep.lens.name}」이오.
          나머지 19명은 같은 8글자를 놓고 다른 데를 먼저 짚소.
          두루마리처럼 위에서 아래로 한 컷씩 뜨니, 훑지 말고
          한 칸씩 보시오.
        </Say>
        {/*
           ★ 표지가 「N컷이오」로 끝났습니다. 수는 있는데 **그중 무엇이
             그대만의 것인지**가 없었습니다. 관점 컷(lc_)은 이 사람을
             고른 까닭 그 자체라, 표지에서 이름을 불러 줘야 합니다.
         */}
        <ActOut kind="끊긴 동작" next={firstOwn?.title}>
          {rep.cuts.length}컷이오. 그중 <b>{ownCount}</b>은 {rep.lens.name}만
          보는 자리요 — 다른 열아홉은 그 자리를 안 보오.<br />
          <b>펴기 전까지는 무엇이 적혔는지 나도 말하지 않소.</b>
        </ActOut>
        <button className="btn mt" onClick={() => setTab("c2")}>내 것을 펴겠습니다</button>
      </Shell>
    );
  }

  /* c3 · 대운 맵 */
  if (tab === "c3") {
    return (
      <Shell screen="c3" title="대운 맵">
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
              <button className="btn mt" onClick={() => setTab("c4")}>어디까지 볼지 고르겠습니다</button>
            )}
          </>
        )}
        {nextTurn != null && (
          <ActOut kind="밝힘" next="지금 어디에">
            다음으로 마디가 바뀌는 때는 <b>{nextTurn}살</b>이오.
            그 해에 무슨 일이 난다는 말은 하지 않소 — <b>읽는 자리가
            바뀐다</b>는 말이오.
          </ActOut>
        )}
        <button className="btn gh mt" onClick={() => setTab("c2")}>본문으로</button>
      </Shell>
    );
  }

  /* c4 · 페이월 — ★ 안 파는 자리에서는 아예 안 그립니다 */
  if (tab === "c4" && !rep.sells) {
    return (
      <Shell screen="c4" title={rep.lens.name}>
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
      <Shell screen="c4" title="여기서부터" legal>
        <Scene id="fold" />
        <Narration lines={["두루마리가 반쯤 접혀 있다."]} />
        <Say who={rep.lens.name} lens={lensId}>
          여기까지가 값 없이 하는 얘기요. 나머지에는 <b>왜</b>와 <b>언제</b>가 들어 있소.
          <br />
          {you}가 여기서 손을 뗄 것도 아오. 나가도 붙잡지 않소.
          {" "}<b>여태 이런 데서 결제 단추를 눌렀다 후회한 적이 있소.</b>
          {" "}그래서 접힌 자리마다 <b>무엇을 보고 한 말인지</b>를 먼저
          적어 두었소 — 제목과 근거 줄은 값을 안 치러도 다 보이오.
          가려 둔 건 <b>그 안의 글</b>뿐이오.
          <br />
          접힌 데를 억지로 궁금하게 만들 생각은 없소. 밥값 한 끼를
          두고 재는 일이니, 오늘 밤 잠이 안 올 만큼 걸리는 게 아니면
          접어 두고 가시오. 두루마리는 내일도 여기 그대로 있소 —
          장에 내놓고 파는 물건이 아니라, 상 위에 펴 둔 종이처럼
          말이오.
          <br />
          스무 사람 중 이 자리를 보는 건 나 1명이오. 같은 8글자를
          두고 나머지 19명은 다른 데를 짚소. 그러니 여기서 접어도
          그대가 놓치는 건 <b>내 눈 하나</b>지 그대의 여덟 글자가
          아니오. 돈을 먼저 보고 싶으면 돈 보는 사람에게, 끊긴
          연락이 걸리면 그 사람에게 가시오 — 열쇠 꾸러미에서 맞는
          열쇠 하나를 골라 쥐는 것같이 하면 되오.
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
        {/*
          ★ 막이 그냥 끝나고 있었습니다. 접힌 목록 다음에 곧바로
            버튼 둘이라, 값을 치를지 말지를 **목록만 보고** 정하게
            했습니다. 여기는 딜레마로 끊는 자리입니다 — 다만 재촉이
            아니라 접어 두는 쪽도 같이 냅니다.
        */}
        <ActOut kind="딜레마" next="어디까지 볼지">
          접힌 자리는 오늘 다 열어도 되고, 하나도 안 열어도 되오.
          <br />
          <b>둘 다 답이오.</b> 다만 절반만 열어 두고 저녁 내내 그
          생각을 붙들고 있는 것 — 그것만은 안 하시는 게 좋소.
        </ActOut>
        <button className="btn mt" onClick={() => router.push("/pay?step=d1")}>
          어디까지 볼지 고르겠습니다
        </button>
        <button className="btn gh" onClick={() => setTab("c2")}>본문으로</button>
      </Shell>
    );
  }

  /* c5 · 공유 카드 */
  if (tab === "c5") {
    const nameCut = rep.cuts.find((c) => c.id === "lack");
    return (
      <Shell screen="c5" title="공유 카드">
        <Narration lines={["도령이 종이 한 장을 잘라 내밀었다."]} />
        <span className="src">
          근거 · {s.features?.day_gan} 일간 · {s.features?.strength} ·
          {" "}읽은 자리 {rep.cuts.length}컷
        </span>
        <p className="sm">
          <b>일간(日干)</b>은 여덟 글자 가운데 <b>그대 자신</b>을 가리키는
          한 글자요. 여덟이 다 그대인 게 아니라, <b>그중 하나가 그대이고
          나머지 일곱이 그 둘레</b>요 — 마당 한가운데 선 사람과 담장
          같은 것이오.
        </p>
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
        <ActOut kind="남긴 물음" next="남기다">
          이 카드에는 <b>여덟 글자와 읽은 자리</b>만 담기오.
          생년월일시도 고을도 안 담기오.<br />
          <b>그런데 받은 사람은 제 것을 세워 보고 싶어지오.</b> 왜 그렇겠소?
        </ActOut>
        <button className="btn gh mt" onClick={() => setTab("c6")}>다 읽었습니다</button>
      </Shell>
    );
  }

  /* c6 · 피드백 */
  if (tab === "c6") {
    return (
      <Shell screen="c6" title="남기다" legal>
        <Scene id="wall" />
        <Narration lines={["벽에 붉은 인장이 줄지어 찍혀 있다.",
                           "빈 칸이 하나 남아 있다."]} />
        {/*
          ★ 여기가 셋째로 낮았습니다 (연출 53).

            「어떻게 보셨소?」 한 줄과 별 다섯 개, 빈 칸이 전부였습니다.
            방금 스무 컷을 읽고 나온 사람에게 **아무 말도 안 걸고**
            평점부터 물었습니다. 울림 20 · 명확 38 이 거기서 나왔습니다.

            후기를 더 받으려고 재촉하는 게 아닙니다. 끝까지 읽은 것
            자체가 이 화면이 아는 사실이라, 그걸 먼저 짚습니다.
        */}
        <Say who={rep.lens.name} lens={lensId}>
          {you}는 이 자리를 여기까지 다 폈소. 도중에 덮고 나가는
          사람이 훨씬 많소.
          <br />
          읽는 동안 어느 줄에선가 손이 멈췄소. 맞아서 멈춘 게 아니라,
          <b> 여태 아무한테도 안 한 말</b>이 거기 적혀 있어서 멈추는
          것이오. 혼자 삼키고 지나간 자리요. 그 줄이 어디였는지는
          내가 모르오.
          <br />
          별을 다는 건 나를 위한 게 아니오. 다음에 이 자리 앞에 설
          사람은 {you}가 남긴 줄을 먼저 읽고 값을 치를지 정하오.
          {" "}벽에 인장을 하나 더 얹는 것처럼, 뒤에 오는 사람이
          디딜 자리를 하나 놓는 셈이오.
          {" "}빈 칸으로 두고 가도 되오. 그것도 답이오.
        </Say>
        <span className="src">
          근거 · 이 자리를 끝까지 편 사람에게만 뜨는 칸이오 ·
          별 5개 · 1,000글자까지 · 값을 치른 후기에만 「결제 확인됨」이
          붙고, 인장은 1개 찍히오
        </span>
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
            {reviewBusy ? "받아 적는 중입니다" : "남기겠습니다"}
          </button>
        )}

        <ActOut kind="끊긴 동작" next="이어지는 자리">
          다 읽으셨소. <b>인장이 하나 남았소.</b><br />
          인장은 이 자리를 끝까지 본 사람에게만 붙소 —
          모으면 인장첩에 남고, 남긴 말은 다음 사람이 보오.
        </ActOut>
        <button className="btn gh mt" onClick={async () => {
          /* 아직 안 보낸 말이 있으면 나가기 전에 보냅니다.
             손님이 친 글자를 버리지 않습니다. */
          await sendReview();
          if (!s.seals.includes(lensId)) s.set({ seals: [...s.seals, lensId] });
          router.push("/relay");
        }}>
          인장을 받고 나가겠습니다
        </button>
      </Shell>
    );
  }

  /* c2 · 본문 — 두루마리 */
  const body = rep.cuts.filter((c) => c.id !== "daeun_map");
  const pillars = s.features?.pillars ?? [];

  return (
    <Shell screen="c2" title={rep.lens.name}>
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
          내 것을 종이로 받겠습니다 (PDF)
        </button>
        <button onClick={() => void makeLink()} disabled={sharing}>
          {sharing ? "고리를 엮는 중…" : shareUrl ? "고리 다시 복사" : "고리 만들어 나누기"}
        </button>
        {rep.locked.length > 0 && (
          <button onClick={() => setTab("c4")}>잠긴 {rep.locked.length}컷</button>
        )}
        {daeunCut && <button onClick={() => setTab("c3")}>대운 맵</button>}
        <button onClick={() => setTab("c6")}>다 읽었습니다</button>
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
