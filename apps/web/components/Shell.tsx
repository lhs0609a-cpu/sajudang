"use client";

/**
 * 전역 껍데기 — 상단바 + 모바일 프레임 + 하단 고지. (docs/08 §4)
 *
 * 상단바는 a1(골목)에서만 숨깁니다.
 *
 * ★ [건너뛰기] 를 뗐습니다.
 *   입력 네 화면 내내 상단에 떠 있었고, **탈출 버튼이 CTA보다 위**에
 *   있었습니다. 목적지는 값이 붙은 진열대였는데, 이 구간을 건너뛴 손님은
 *   명식이 없어서 진열대에서 아무것도 못 봅니다 — 즉 이 버튼은 이탈로만
 *   이어졌습니다. 뒤로 버튼은 그대로 있습니다.
 *
 *   `skipTo` 는 자리만 남겨 둡니다. 다시 달 일이 있으면 목적지를
 *   /lobby 가 아니라 "이름 없이 세운다"(입력을 건너뛰고 계속)로 두세요.
 */
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Suspense, useCallback, useEffect, useLayoutEffect, useRef, useState,
} from "react";

/*
 * 그리기 **전에** 도는 효과.
 *
 * ★ 이게 이번 버그의 자리입니다. useEffect 는 화면이 그려진 **뒤**에
 *   돕니다. 그때는 CSS 가 지연 0 으로 시작한 애니메이션이 이미 끝난
 *   뒤라, 뒤늦게 animation-delay 를 적어도 다시 돌지 않습니다.
 *   그래서 전부 처음부터 떠 있었습니다.
 *
 *   useLayoutEffect 는 DOM 을 고친 직후·그리기 직전에 돕니다. 지연을
 *   먼저 박고 그린 뒤에 애니메이션이 시작하므로 순서대로 뜹니다.
 *   서버에서는 없는 물건이라 useEffect 로 내려갑니다(거기선 안 그립니다).
 */
const useBeforePaint =
  typeof window === "undefined" ? useEffect : useLayoutEffect;

/* ══════════════════════════════════════════════════════════
 * 읽는 속도 — 손님이 읽을 만큼 두고 다음 것을 낸다
 * ══════════════════════════════════════════════════════════
 *
 * ★ 손님이 두 번 한 말 (2026-09-02 · 09-03)
 *
 *   "처음부터 모든 대사가 나오게 하지 말라니까. 사람이 읽는 속도가
 *   있을 거 아냐. 전체 페이지 전부 다 설계해야지."
 *
 * ★ 무엇이 잘못이었나
 *
 *   차례는 있었는데 **전체가 3.2초에서 멈췄습니다.** 그래서 스무 줄이든
 *   두 줄이든 3.2초 뒤에는 화면이 통째로 차 있었습니다. 그건 읽는
 *   속도가 아니라 **뜨는 순서**입니다 — 늦게 뜨는 것뿐이지, 손님이
 *   첫 줄을 읽기도 전에 마지막 줄과 버튼이 이미 거기 있습니다.
 *
 *   이제 한 덩이는 **그 덩이를 읽을 만한 시간**을 두고 다음으로 넘깁니다.
 *   한글 묵독은 분당 오륙백 자쯤 — 초당 열 자로 잡습니다.
 *
 * ★ 그래서 세 가지를 함께 답니다. 이게 없으면 연출이 아니라 지연입니다.
 *
 *   ① 누르면 즉시 다 뜬다   화면 아무 데나 누르거나, 키를 치거나,
 *                          아래로 굴리면 그 화면은 그 자리에서 다 폅니다.
 *                          읽는 속도를 정하는 건 결국 손님입니다.
 *   ② 두 번째는 안 늦춘다   한 번 본 화면은 이 세션 동안 바로 다 뜹니다.
 *                          같은 뜸을 두 번 보면 그건 지연입니다.
 *   ③ 접힌 데는 안 센다     첫 화면 밖으로 넘어가는 것은 기다리지
 *                          않습니다 — 아직 아무도 안 읽는 자리입니다.
 */

/** 초당 몇 자를 읽는가. 한글 묵독 분당 600자쯤. */
const CPS = 10;
/** 짧은 줄도 이만큼은 둔다 — 안 그러면 두 줄이 한 줄처럼 보입니다. */
const HOLD_MIN = 0.42;
/** 한 덩이가 아무리 길어도 여기서 끊는다. 긴 문단은 눈으로 훑습니다. */
const HOLD_MAX = 2.8;
/** 버튼·입력칸 — 글이 아니니 곧바로. 누르려는 사람을 세우지 않습니다. */
const HOLD_UI = 0.26;
/**
 * 굴려 내려온 자리에서 줄이 밀려도 이보다는 안 기다린다.
 *
 * ★ 빨리 굴린 손님이 앞의 열 덩이를 다 기다리면 그건 연출이 아니라
 *   고장입니다. 눈에 들어온 순서대로 세되, 밀린 줄은 여기서 끊습니다.
 */
const QUEUE_MAX = 1.6;
/**
 * 마디가 더 안 뜨면 이만큼 뒤에 **도로 다 밝힙니다.**
 *
 * ★ 물러난 채로 두면 다시 읽을 수가 없습니다. 흐름이 멎었다는 건
 *   손님이 따라잡았다는 뜻이고, 그때부터 화면은 읽는 자리입니다.
 */
const DIM_REST = 1.1;

/** 이 화면을 이미 봤는가. 세션이 끝나면 잊습니다. */
const SEEN_KEY = "sajudang-beat-seen";

function seenBefore(screen?: string): boolean {
  if (!screen) return false;
  try {
    return (sessionStorage.getItem(SEEN_KEY) ?? "").split(",").includes(screen);
  } catch {
    return false;                   // 사생활 보호 모드 — 조용히 늦춥니다
  }
}

function markSeen(screen?: string) {
  if (!screen) return;
  try {
    const got = (sessionStorage.getItem(SEEN_KEY) ?? "").split(",")
      .filter(Boolean);
    if (!got.includes(screen)) {
      sessionStorage.setItem(SEEN_KEY, [...got, screen].join(","));
    }
  } catch { /* 못 적어도 화면은 돕니다 */ }
}

/** 이 덩이 하나를 읽는 데 걸리는 시간(초). */
function holdOf(el: HTMLElement): number {
  // 버튼·칸은 글이 아닙니다. 안에 버튼을 품은 무리도 마찬가지입니다 —
  // 여섯 칸을 하나씩 띄우면 고르는 화면이 느려집니다.
  if (el.tagName === "BUTTON"
      || el.querySelector("button, input, select, textarea")) {
    return HOLD_UI;
  }
  const chars = (el.textContent ?? "").trim().length;
  if (!chars) return HOLD_UI;
  // 대사는 말하고 나서 **잠깐 둡니다.** 사람이 말하면 상대가 읽을 틈이
  // 있어야 대화입니다. 서술은 장면이라 조금 빠르게 흘러갑니다.
  const settle = el.classList.contains("say") ? 0.34 : 0.12;
  return Math.min(HOLD_MAX, Math.max(HOLD_MIN, chars / CPS + settle));
}
import { useSession } from "@/lib/store";
import { LENS_BY_ID } from "@/lib/lenses";
import { api, apiMisconfigured } from "@/lib/api";
import { playBgm } from "@/lib/sound";
import SoundToggle from "@/components/SoundToggle";
import DevRail from "@/components/DevRail";

export const LEGAL = [
  "본 서비스는 전통 명리학 해석에 기반한 자기이해·오락 목적 콘텐츠입니다.",
  "의학적·법률적·재무적 판단의 근거가 아니며, 특정 결과를 보장하지 않습니다.",
  "응답률 수치는 실제 사용자 응답 집계값이며 예측 적중률이 아닙니다.",
];

export function Legal() {
  return (
    <div className="legal">
      {LEGAL.map((l) => <p key={l}>{l}</p>)}
      {/*
       * ★ 전자상거래법 제10조 — 사업자 표시와 약관·방침·환불은
       *   **상시** 닿을 수 있어야 합니다. 결제 화면에만 두면
       *   결제 전에 못 읽습니다.
       */}
      <p className="llinks">
        <a href="/legal">이용약관</a>
        <span aria-hidden="true"> · </span>
        <a href="/legal">개인정보처리방침</a>
        <span aria-hidden="true"> · </span>
        <a href="/legal">환불정책</a>
        <span aria-hidden="true"> · </span>
        <a href="/legal">사업자 정보</a>
      </p>
    </div>
  );
}

/*
 * 대문 밖 처마 — 어느 화면에나 서는 아래 띠.
 *
 * ★ 손님이 시킨 것 (2026-09-03)
 *
 *   "사람들이 이 프로그램 잘 쓸 수 있도록 관리유지할 수 있는 전반적인
 *   관리자페이지도 신설해서 하단에 네비게이터푸터링크로 관리자
 *   로그인하고 들어갈 수 있도록 설계해야해."
 *
 * ★ 두 가지가 여기서 한꺼번에 풀립니다
 *
 *   ① 주인 자리로 가는 길이 **없었습니다.** 주소를 외운 사람만
 *      들어갔습니다 — `.\dev.ps1 screens` 가 `/admin` 을 고아 화면으로
 *      찍고 있었습니다. `/legal` 도 같았습니다.
 *
 *   ② 약관·방침·환불은 전자상거래법 제10조상 **상시** 닿을 수
 *      있어야 합니다. 그런데 `<Legal>` 은 `legal` 을 켠 화면에만
 *      붙어 있었습니다. 처마는 어느 화면에나 섭니다.
 *
 * ★ 주인 자리는 링크만 열려 있고 **문은 잠겨 있습니다.**
 *   `/admin` 은 FUNNEL_KEY 를 받아야 열립니다 (keyguard). 길을
 *   숨기는 것은 잠금이 아닙니다 — 그건 가림입니다.
 */
export function SiteFooter() {
  return (
    <nav className="sitefoot noprint" aria-label="아래 길">
      {/* ★ 넉 줄을 한 줄에 다 걸면 마지막 줄에 「정보」만 홀로 남습니다
          (tests/test_widow.py). 셋과 하나로 나눠 답니다. */}
      <p className="lk">
        <a href="/legal">이용약관</a>
        <span aria-hidden="true"> · </span>
        <a href="/legal">개인정보처리방침</a>
        <span aria-hidden="true"> · </span>
        <a href="/legal">환불정책</a>
      </p>
      <p className="hn">
        성신당 星辰堂
        <span aria-hidden="true"> · </span>
        <a href="/legal">사업자 정보</a>
        <span aria-hidden="true"> · </span>
        <a className="own" href="/admin">주인 자리</a>
      </p>
    </nav>
  );
}

export function TopBar({ title, skipTo, onBack }: {
  title: string; skipTo?: string; onBack?: () => void;
}) {
  const router = useRouter();
  const seals = useSession((s) => s.seals);
  const admin = useSession((s) => s.admin);
  const setSession = useSession((s) => s.set);
  return (
    <div className="top">
      {/*
        ★ 진입 흐름은 주소 하나 위의 일곱 단계입니다. 그런데 이 화살표는
          `router.back()` 이라 **한 단계 뒤가 아니라 밖으로** 나갔습니다.
          성향 넉 자 열여섯 칸에서 잘못 누르면 곧바로 셈 화면으로 넘어가고,
          고칠 길이 이 화살표뿐인데 그걸 누르면 나가집니다.
          단계를 아는 화면은 `onBack` 을 줍니다.
      */}
      <button className="tb" onClick={() => (onBack ? onBack() : router.back())}
              aria-label="뒤로">←</button>
      <SoundToggle />
      {/*
        ★ 관리자만 보이는 모드 전환.

          전에는 레일을 열어야만 「유저 모드로」 가 있었습니다. 레일을
          닫아 두고 화면을 보다가 손님 눈으로 보고 싶어지면 주소를
          손으로 고쳐야 했습니다.

          손님에게는 이 칸이 아예 없습니다 — 있는지도 모릅니다.
      */}
      {admin && (
        <button className="tb mode" onClick={() => {
          setSession({ admin: false });
          // ★ 갈 데를 또렷이 적습니다. 그냥 `/` 로 밀면 `?step=a7`
          //   에서는 같은 길이라 화면이 안 바뀌었습니다 (2026-09-05).
          router.push("/?step=a1");
        }}>
          회원 화면
        </button>
      )}
      {admin && (
        <Link className="tb mode" href="/admin">주인</Link>
      )}
      <span className="tt">{title}</span>
      <Link className="tb" href="/daily" aria-label="오늘의 일진">日</Link>
      <Link className="tb" href="/me" aria-label="인장첩">印 {seals.length}</Link>
      <Link className="tb" href="/lobby">진열대</Link>
      {skipTo && <Link className="tb sk" href={skipTo}>건너뛰기</Link>}
    </div>
  );
}

export default function Shell({
  title, screen, skipTo, bare, legal, onBack, children,
}: {
  title?: string;
  /*
   * 이 화면의 **이름**. docs/08 §1 의 것을 그대로 씁니다 (a7 · b1 · d1 …).
   *
   * ★ 왜 제목 말고 이름을 따로 다나
   *
   *   제목은 손님에게 보이는 말이라 바뀝니다 — 「도령이 말하다」 는
   *   a7 이지만 제목만 봐서는 알 수 없습니다. 그리고 여러 화면이 같은
   *   제목을 씁니다(읽다 · 분석지 · 값을 치르다).
   *
   *   자를 대는 쪽에서는 그동안 `step === "a7"` 같은 **조건문**을 찾아
   *   화면을 갈랐습니다. 그런데 마지막 return 으로 떨어지는 화면
   *   — a7 훅 · b1 진열대 · c2 본문 · d1 어디까지 — 은 그런 조건문이
   *   없어서 **앞 화면에 섞였습니다.** a7 의 막 끝이 a6 의 점수로
   *   올라가고, 진열대와 「어디까지」 는 아예 안 재지고 있었습니다.
   *
   *   화면이 제 이름을 적으면 그건 **있는 것**입니다. 액트아웃을
   *   선언으로 받은 것과 같은 까닭입니다.
   */
  screen?: string;
  skipTo?: string;
  onBack?: () => void;     // 한 주소 위 여러 단계인 화면 (진입 흐름)
  bare?: boolean;          // a1 — 진입 서사 중에는 상단바를 숨긴다
  legal?: boolean;         // h1 · d2 · r1
  children: React.ReactNode;
}) {
  const features = useSession((s) => s.features);
  const cur = useSession((s) => s.cur);
  const admin = useSession((s) => s.admin);
  const ilganOverride = useSession((s) => s.ilganOverride);
  const themeColor = LENS_BY_ID[cur]?.color;

  /*
   * 새로고침하면 features 는 사라지고 chartId 만 남습니다(용량 때문에
   * 저장하지 않습니다). 그대로 두면 "아직 세우지 않았소" 로 돌아갑니다.
   * chart_id 로 서버에서 되찾아 옵니다.
   */
  const chartId = useSession((s) => s.chartId);
  const hasFeatures = useSession((s) => !!s.features);
  const setSession = useSession((s) => s.set);
  useEffect(() => {
    if (!chartId || hasFeatures) return;
    let alive = true;
    api.getChart(chartId)
      .then((r) => { if (alive) setSession({ features: r.features }); })
      .catch(() => { /* 못 찾으면 각 화면이 알아서 안내한다 */ });
    return () => { alive = false; };
  }, [chartId, hasFeatures, setSession]);

  // 레일이 켜지면 무대를 오른쪽으로 민다
  useEffect(() => {
    document.body.classList.toggle("has-rail", admin);
    return () => document.body.classList.remove("has-rail");
  }, [admin]);

  /*
   * 지금 어느 화면인지 알린다 — 관리자 레일이 **이 화면의** 연출 점수를
   * 띄우는 데 씁니다. 손님 화면에서는 아무 일도 안 합니다.
   */
  useEffect(() => {
    if (screen) setSession({ screen });
  }, [screen, setSession]);

  /*
   * ★ 화면 전체가 손님이 읽는 속도로 뜬다.
   *
   *   순서는 화면 단위입니다. 여기 놓인 순서(DOM 순서 = 보이는 순서)대로
   *   차례를 매깁니다 — 페이지마다 손댈 필요가 없습니다. 스물일곱 화면이
   *   전부 이 한 자리를 지납니다.
   *
   *   장면과 진행 막대는 뺍니다 — 배경이라 처음부터 있어야 합니다.
   */
  const scrRef = useRef<HTMLDivElement>(null);
  const doneRef = useRef(false);
  const [pacing, setPacing] = useState(false);
  /*
   * ★ 접힌 자리를 지켜보는 눈 (2026-09-03).
   *
   *   전에는 첫 화면(fold) 안만 늦추고, 그 아래는 **처음부터 다 떠**
   *   있었습니다. 「아직 아무도 안 읽는 자리를 기다리면 지연이다」 는
   *   맞는 말인데, 그 결론이 「그럼 그냥 다 띄우자」 였습니다. 그래서
   *   긴 화면은 위 몇 줄만 대화이고 나머지는 벽이었습니다.
   *
   *   손님이 말했습니다 — "글자 사람이 읽어내려가는 속도에 맞춰서
   *   전부 나오게 하라니까 모든 페이지 전부."
   *
   *   답은 기다리는 게 아니라 **눈에 들어올 때 세는** 것입니다. 굴려서
   *   그 자리에 닿으면 그때부터 읽는 속도로 뜹니다. 천천히 굴리면
   *   닿는 대로 바로 뜨고, 빨리 굴리면 줄을 서서 차례로 뜹니다.
   */
  const eyeRef = useRef<IntersectionObserver | null>(null);
  /*
   * ★ 누르는 것은 따로 봅니다 (2026-09-04).
   *
   *   글은 화면 아래 22%에 걸치면 「아직 안 읽은 것」으로 두고 굴림을
   *   기다립니다. 그런데 **버튼에 같은 문턱을 걸면 안 됩니다.** 대문의
   *   「내 운명을 확인하겠습니다」 는 첫 화면 아래쪽에 있어서, 그대로
   *   두면 손님이 굴려야 버튼이 나타납니다 — 굴릴 이유를 만들려다
   *   누를 것을 감추는 꼴입니다.
   *
   *   누르는 것이 든 덩이는 **보이면 곧바로** 냅니다. 차례는 줄이
   *   잡으므로 위의 글보다 먼저 튀어나오지 않습니다.
   */
  const eyeUiRef = useRef<IntersectionObserver | null>(null);
  /** 줄 선 것들이 언제까지 차 있는가 (performance.now 기준) */
  const queueRef = useRef(0);
  /*
   * ★ 한 마디만 밝게 (2026-09-04).
   *
   *   한 마디씩 뜨기는 했는데 **앞엣것이 안 물러나서**, 다 뜨고 나면
   *   결국 벽이었습니다. 손님이 말했습니다 —
   *
   *       "처음부터 글이 너무 많잖아. 차례대로 글을 띄어주던가.
   *        누가 한번에 이걸 읽어. 차례대로 띄어주고 사라지고 하는것도
   *        아니고. 전반적으로 이게 제일 중요해."
   *
   *   그래서 새 마디가 뜨면 앞 마디는 **물러납니다**(옅어짐). 지금 읽을
   *   한 마디만 밝습니다.
   *
   *   ★ 지우지는 않습니다. 대문의 「여기까지 값은 안 받소」 는 약속이고,
   *     지운 약속은 안 한 약속입니다. 그리고 자리가 사라지면 굴리는
   *     동안 화면이 출렁여 읽던 데를 잃습니다.
   *
   *   ★ 흐름이 멎으면 **도로 다 밝힙니다.** 손님이 따라잡았다는 뜻이라,
   *     그때부터는 다시 읽을 수 있어야 합니다.
   */
  const litRef = useRef<HTMLElement | null>(null);
  const restoreRef = useRef<number | null>(null);
  const timersRef = useRef<number[]>([]);

  /* 이 마디를 밝히고 앞엣것을 물린다. */
  const lightUp = useCallback((el: HTMLElement) => {
    const prev = litRef.current;
    if (prev && prev !== el) prev.classList.add("dim");
    litRef.current = el;
    // 흐름이 멎으면 도로 다 밝힙니다 — 따라잡은 사람은 다시 읽습니다.
    if (restoreRef.current) window.clearTimeout(restoreRef.current);
    restoreRef.current = window.setTimeout(() => {
      scrRef.current?.querySelectorAll(".dim")
        .forEach((e) => e.classList.remove("dim"));
      litRef.current = null;
    }, DIM_REST * 1000);
  }, []);

  /* 다 편다 — 손님이 서두를 때, 인쇄할 때, 모션을 줄일 때. */
  const revealAll = useCallback(() => {
    doneRef.current = true;
    eyeRef.current?.disconnect();
    eyeUiRef.current?.disconnect();
    timersRef.current.forEach(window.clearTimeout);
    timersRef.current = [];
    if (restoreRef.current) window.clearTimeout(restoreRef.current);
    scrRef.current?.querySelectorAll(".dim")
      .forEach((e) => e.classList.remove("dim"));
    litRef.current = null;
    scrRef.current?.classList.add("beatskip");
    setPacing(false);
    markSeen(screen);
  }, [screen]);

  /* 화면을 뜨면 지켜보던 것과 시계를 놓습니다. */
  useEffect(() => () => {
    eyeRef.current?.disconnect();
    eyeUiRef.current?.disconnect();
    timersRef.current.forEach(window.clearTimeout);
    if (restoreRef.current) window.clearTimeout(restoreRef.current);
  }, []);

  useBeforePaint(() => {
    const root = scrRef.current;
    if (!root || doneRef.current) return;

    // 움직임을 줄이는 손님, 그리고 이 세션에서 이미 본 화면은 안 늦춥니다.
    //
    // ★ 다만 **관리자는 뺍니다** (2026-09-04). 화면을 고치는 사람은 같은
    //   화면을 스무 번 엽니다. 두 번째부터 안 늦추면 고친 연출을 볼 수가
    //   없어, 손님이 「차례대로 안 뜬다」 고 한 것도 실은 이 자리였습니다.
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches
        || (!admin && seenBefore(screen))) {
      revealAll();
      return;
    }

    /*
     * 대화 알갱이 — 나레이션 한 줄, 대사 한 마디. 어디에 있든 줍니다.
     *
     * ★ 처음에는 `:scope >` 로 **바로 밑**만 봤습니다. 그런데 재 보니
     *   56개 중 12개가 한 겹 안에 들어 있었습니다(상자로 묶은 자리).
     *   그것들은 통째로 떠서, 그 화면만 대화가 아니었습니다.
     */
    const atoms = Array.from(
      root.querySelectorAll<HTMLElement>(".nr > .l, .say"));

    /*
     * 나머지는 바로 밑 한 겹만 봅니다 — 버튼 여섯 칸을 하나씩 띄우면
     * 고르는 화면이 느려집니다. 무리는 무리째 뜨는 게 맞습니다.
     * 다만 알갱이를 **품고 있는 상자**는 뺍니다. 안엣것이 따로 뜨는데
     * 상자까지 늦으면 두 번 늦습니다.
     */
    const tops = Array.from(root.children).filter((el) =>
      el instanceof HTMLElement
      && !el.classList.contains("prog")
      && !el.classList.contains("sceneart")
      && !el.classList.contains("nr")
      && !atoms.some((a) => el.contains(a))) as HTMLElement[];

    const seq = [...tops, ...atoms].sort((a, b) =>
      a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1);

    /*
     * ★ 차례는 **이번에 새로 온 것**만 셉니다.
     *
     *   훅처럼 한 마디씩 늘어나는 화면에서는 이 효과가 여러 번 돕니다.
     *   이미 뜬 것은 다시 안 겁니다 (`data-beat` 를 보고 거릅니다).
     */
    /*
     * ★ 굴리는 대로 뜹니다 — 미리 띄우는 자리는 없습니다 (2026-09-04).
     *
     *   전에는 **첫 화면 안은 시계로** 다 띄우고 그 아래만 굴림에
     *   맡겼습니다. 그러니 첫 화면은 손 하나 안 대도 몇 초 만에 다
     *   떠 버렸고, 손님이 말한 그대로였습니다 —
     *
     *       "사용자가 화면 내리는거에 맞춰서 글을 띄워줘.
     *        미리 다 띄우면 안돼. 전체적으로 다. 모든 부분이 다 그래야해."
     *
     *   그래서 시계로 띄우는 길을 없앴습니다. **모든 마디가 눈에
     *   들어올 때 뜹니다.** 한꺼번에 여럿이 들어오면(첫 화면) 줄을
     *   세워 읽는 속도로 하나씩 냅니다 — 그래야 첫 화면도 대화입니다.
     *
     *   ★ 아래 22%는 아직 「눈에 들어온 것」이 아닙니다. 화면 끝에
     *     걸친 글을 미리 띄우면 굴릴 이유가 없어집니다.
     *
     *   ★ 굴릴 수 없는 화면은 그 문턱을 안 겁니다. 굴릴 데가 없는데
     *     아래 22%를 잠그면 그 글은 **영영 안 뜹니다.**
     */
    const canScroll =
      document.documentElement.scrollHeight > window.innerHeight + 4;
    const reveal = (entries: IntersectionObserverEntry[],
                    who: IntersectionObserver) => {
        for (const en of entries) {
          if (!en.isIntersecting) continue;
          const el = en.target as HTMLElement;
          who.unobserve(el);
          if (el.dataset.beat !== undefined) continue;
          const now = performance.now();
          const wait = Math.min(QUEUE_MAX,
                                Math.max(0, (queueRef.current - now) / 1000));
          el.style.animationDelay = wait.toFixed(2) + "s";
          delete el.dataset.beatwait;
          el.dataset.beat = "";
          timersRef.current.push(window.setTimeout(
            () => lightUp(el), wait * 1000));
          queueRef.current = now + (wait + holdOf(el)) * 1000;
          // 다 떴으면 「한 번에 다 보겠습니다」 를 거둡니다.
          if (!root.querySelector("[data-beatwait]")) {
            timersRef.current.push(window.setTimeout(() => {
              setPacing(false);
              markSeen(screen);
            }, (wait + holdOf(el)) * 1000 + 400));
          }
        }
    };
    if (!eyeRef.current) {
      eyeRef.current = new IntersectionObserver(
        (e) => reveal(e, eyeRef.current!),
        { rootMargin: canScroll ? "0px 0px -22% 0px" : "0px" });
    }
    if (!eyeUiRef.current) {
      eyeUiRef.current = new IntersectionObserver(
        (e) => reveal(e, eyeUiRef.current!), { rootMargin: "0px" });
    }

    let added = 0;
    seq.forEach((el) => {
      if (el.dataset.beat !== undefined
          || el.dataset.beatwait !== undefined) return;
      el.dataset.beatwait = "";
      // 누르는 것이 든 덩이는 문턱 없이 — 보이면 곧바로.
      const ui = el.tagName === "BUTTON"
        || el.querySelector("button, input, select, textarea, a");
      (ui ? eyeUiRef.current! : eyeRef.current!).observe(el);
      added += 1;
    });

    if (added > 0) setPacing(true);
  });

  /*
   * 「한 번에 다 보겠습니다」 를 거두는 것은 **관찰자가** 합니다 —
   * 마지막 마디가 뜬 뒤에요. 시간으로 재면 굴림에 맡긴 뒤로는 맞지
   * 않습니다: 손님이 안 굴리면 영영 안 끝나고, 그동안 「다 보겠습니다」
   * 를 거두면 서두를 길이 사라집니다.
   */

  /*
   * ★ 읽는 속도를 정하는 건 결국 손님입니다 — 다만 **굴림은 아닙니다.**
   *
   *   전에는 `wheel` 과 `touchmove` 도 다 펴는 손잡이였습니다. 그런데
   *   이제 굴림이 **글을 띄우는 손잡이**입니다. 둘을 같이 걸면 굴리는
   *   순간 통째로 펴져서, 손님은 늘 다 떠 있는 화면만 보게 됩니다.
   *   모바일은 더합니다 — 손가락을 대는 순간 `pointerdown` 이 먼저
   *   울려서, 굴리려던 사람이 건너뛰기를 누른 셈이 됐습니다.
   *
   *   그래서 **누름(click)과 키만** 답니다. 굴림은 굴림입니다.
   *   서두르는 사람에게는 「한 번에 다 보겠습니다」 가 있습니다.
   */
  useEffect(() => {
    if (!pacing) return;
    const go = () => revealAll();
    const tap = (e: MouseEvent) => {
      // 버튼·링크·입력칸을 누른 것은 그 일을 하러 누른 것입니다.
      const el = e.target as HTMLElement | null;
      if (el?.closest("button, a, input, textarea, select, summary")) return;
      go();
    };
    const keys = (e: KeyboardEvent) => {
      // 글자를 치는 중이면 건드리지 않습니다 — 이름·생년월일 칸입니다.
      const el = e.target as HTMLElement | null;
      if (el && /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName)) return;
      go();
    };
    window.addEventListener("click", tap);
    window.addEventListener("keydown", keys);
    window.addEventListener("beforeprint", go);
    return () => {
      window.removeEventListener("click", tap);
      window.removeEventListener("keydown", keys);
      window.removeEventListener("beforeprint", go);
    };
  }, [pacing, revealAll]);

  /*
   * ★ 바닥에 닿았는데 아직 안 뜬 것이 있으면 띄웁니다.
   *
   *   굴림에 맡기는 값에는 늘 이 위험이 있습니다 — 더 굴릴 데가 없는데
   *   문턱 아래에 남은 글은 **영영 안 뜹니다.** 바닥은 「더 볼 것이
   *   없다」 는 뜻이니, 거기서는 남은 것을 냅니다.
   */
  useEffect(() => {
    if (!pacing) return;
    const onScroll = () => {
      const d = document.documentElement;
      if (d.scrollTop + window.innerHeight < d.scrollHeight - 8) return;
      const left = scrRef.current
        ?.querySelectorAll<HTMLElement>("[data-beatwait]");
      left?.forEach((el) => {
        delete el.dataset.beatwait;
        el.dataset.beat = "";
      });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [pacing]);

  /*
   * 배경음.
   *
   * ★ 화면마다 새로 걸지 않습니다. 옮길 때마다 처음부터 다시 나면
   *   그게 더 거슬립니다. 같은 이름이면 lib/sound 가 손을 안 댑니다.
   *
   * ★ 소리가 꺼져 있으면 아무 일도 안 합니다. 켜는 순간 이어집니다.
   */
  useEffect(() => { playBgm("hall"); }, []);

  // 계산 서버가 안 붙은 배포본이면 조용히 실패하지 않고 알린다
  const [noApi, setNoApi] = useState(false);
  useEffect(() => setNoApi(apiMisconfigured()), []);

  return (
    <>
      {/* useSearchParams 를 쓰므로 Suspense 로 감싼다.
          안 감싸면 모든 페이지의 정적 프리렌더가 깨진다. */}
      <Suspense fallback={null}>
        <DevRail />
      </Suspense>
      <div className="stage">
      <div
        className="phone"
        data-screen={screen}
        data-ilgan={ilganOverride ?? features?.day_gan ?? undefined}
        style={themeColor ? ({ ["--c" as string]: themeColor }) : undefined}
      >
        {!bare && <TopBar title={title ?? ""} skipTo={skipTo} onBack={onBack} />}
        {noApi && (
          <div className="warn" style={{ margin: "12px 16px 0" }}>
            <p>계산 서버가 아직 붙지 않았소.</p>
            <p className="sm">
              화면과 서사는 볼 수 있으나 명식은 세울 수 없습니다.
              <code> NEXT_PUBLIC_API_BASE </code>를 API 주소로 설정하세요.
            </p>
          </div>
        )}
        <div className="scr" ref={scrRef}>
          {children}
          {legal && <Legal />}
          {/* 처마는 어느 화면에나 섭니다 — 대문(bare)만 빼고.
              대문은 첫 3초를 파는 자리라 아래 띠가 시선을 나눕니다. */}
          {!bare && <SiteFooter />}
        </div>
        {/*
          ★ 늦추는 데는 반드시 **건너뛰는 길**이 있어야 합니다.
            뜸에 그렇게 하기로 이미 정해 두었고(lib/think), 화면 전체를
            읽는 속도로 내보내는 지금은 더 그렇습니다. 화면 아무 데나
            눌러도 되지만, **눌러도 된다는 걸 알아야** 누릅니다.

          ★ 손님의 말이라 합쇼체입니다. 도령의 말이 아닙니다.
        */}
        {pacing && (
          <button className="beatskip-hint noprint" onClick={revealAll}>
            한 번에 다 보겠습니다
          </button>
        )}
      </div>
      </div>
    </>
  );
}
