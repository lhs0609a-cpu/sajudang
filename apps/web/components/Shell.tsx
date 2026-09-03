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
          router.push("/");
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
  const endRef = useRef(0);
  const [pacing, setPacing] = useState(false);

  /* 다 편다 — 손님이 서두를 때, 인쇄할 때, 모션을 줄일 때. */
  const revealAll = useCallback(() => {
    doneRef.current = true;
    scrRef.current?.classList.add("beatskip");
    setPacing(false);
    markSeen(screen);
  }, [screen]);

  useBeforePaint(() => {
    const root = scrRef.current;
    if (!root || doneRef.current) return;

    // 움직임을 줄이는 손님, 그리고 이 세션에서 이미 본 화면은 안 늦춥니다.
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches
        || seenBefore(screen)) {
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
     *   그때 이미 뜬 것들의 시간까지 더하면, 새로 온 한 줄이 앞선 열
     *   줄만큼 기다립니다 — 전체 상한이 있을 때는 안 보이던 탈입니다.
     *   이미 뜬 것은 차례에서 빼고 0 부터 다시 셉니다.
     */
    let t = 0;
    // 첫 화면 밖은 안 셉니다. 아직 아무도 안 읽는 자리를 기다리면
    // 그건 연출이 아니라 지연입니다.
    const fold = window.innerHeight;
    let folded = false;

    seq.forEach((el) => {
      if (el.dataset.beat !== undefined) return;
      el.style.animationDelay = t.toFixed(2) + "s";
      // 표를 다는 순간 CSS 가 움직이기 시작합니다. 지연을 **먼저**
      // 적어야 합니다 — 순서가 바뀌면 지연 없이 튀어 오릅니다.
      el.dataset.beat = "";
      if (folded) return;
      if (el.getBoundingClientRect().top > fold) {
        folded = true;
        return;
      }
      t += holdOf(el);
    });

    if (t <= 0) return;
    endRef.current = Math.max(endRef.current, performance.now() + t * 1000);
    setPacing(true);
  });

  /* 다 뜨고 나면 「한 번에 다 보겠습니다」 를 거둡니다. */
  useEffect(() => {
    if (!pacing) return;
    const left = Math.max(0, endRef.current - performance.now());
    const id = setTimeout(() => {
      setPacing(false);
      markSeen(screen);
    }, left + 400);
    return () => clearTimeout(id);
  }, [pacing, screen]);

  /*
   * ★ 읽는 속도를 정하는 건 결국 손님입니다.
   *
   *   누르거나, 키를 치거나, 아래로 굴리면 그 화면은 그 자리에서 다
   *   폅니다. 이게 없으면 연출이 아니라 지연입니다 — 두 번째 오는
   *   사람에게 같은 뜸은 특히요.
   */
  useEffect(() => {
    if (!pacing) return;
    const go = () => revealAll();
    const keys = (e: KeyboardEvent) => {
      // 글자를 치는 중이면 건드리지 않습니다 — 이름·생년월일 칸입니다.
      const el = e.target as HTMLElement | null;
      if (el && /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName)) return;
      go();
    };
    window.addEventListener("pointerdown", go);
    window.addEventListener("wheel", go, { passive: true });
    window.addEventListener("touchmove", go, { passive: true });
    window.addEventListener("keydown", keys);
    window.addEventListener("beforeprint", go);
    return () => {
      window.removeEventListener("pointerdown", go);
      window.removeEventListener("wheel", go);
      window.removeEventListener("touchmove", go);
      window.removeEventListener("keydown", keys);
      window.removeEventListener("beforeprint", go);
    };
  }, [pacing, revealAll]);

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
