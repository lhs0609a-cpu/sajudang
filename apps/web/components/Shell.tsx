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
  Suspense, useEffect, useLayoutEffect, useRef, useState,
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
    </div>
  );
}

export function TopBar({ title, skipTo, onBack }: {
  title: string; skipTo?: string; onBack?: () => void;
}) {
  const router = useRouter();
  const seals = useSession((s) => s.seals);
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
      <span className="tt">{title}</span>
      <Link className="tb" href="/daily" aria-label="오늘의 일진">日</Link>
      <Link className="tb" href="/me" aria-label="인장첩">印 {seals.length}</Link>
      <Link className="tb" href="/lobby">진열대</Link>
      {skipTo && <Link className="tb sk" href={skipTo}>건너뛰기</Link>}
    </div>
  );
}

export default function Shell({
  title, skipTo, bare, legal, onBack, children,
}: {
  title?: string;
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
   * ★ 화면 전체가 대화처럼 한 줄씩 뜬다.
   *
   *   전에는 나레이션 블록 **안에서만** 0.72초씩 늦었습니다. 그래서
   *   「붓을 내려놓고, 그가 물었다」 와 「무엇이 걸려서 예까지 왔소?」 와
   *   고민 여섯 칸이 **한꺼번에** 떴습니다. 대화가 아니라 게시물입니다.
   *
   *   순서는 화면 단위여야 합니다. 여기서 놓인 순서(DOM 순서 = 보이는
   *   순서)대로 다시 매깁니다. 페이지마다 손댈 필요가 없습니다.
   *
   *   빠르기 — 한 칸 0.16초, 전체는 1.5초에서 멈춥니다. 대화처럼 이어
   *   보이면서, 버튼을 누르려는 사람이 기다리지 않는 선입니다. 느리면
   *   연출이 아니라 지연입니다.
   *
   *   장면과 진행 막대는 뺍니다 — 배경이라 처음부터 있어야 합니다.
   */
  const scrRef = useRef<HTMLDivElement>(null);
  useBeforePaint(() => {
    const root = scrRef.current;
    if (!root) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
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

    let t = 0;
    seq.forEach((el) => {
      // 이미 떠 있는 것은 건드리지 않습니다 — 훅처럼 한 마디씩 늘어나는
      // 화면에서 앞말이 다시 떠오르면 읽던 자리를 잃습니다.
      if (el.dataset.beat === undefined) {
        el.style.animationDelay = t.toFixed(2) + "s";
        // 표를 다는 순간 CSS 가 움직이기 시작합니다. 지연을 **먼저**
        // 적어야 합니다 — 순서가 바뀌면 지연 없이 튀어 오릅니다.
        el.dataset.beat = "";
      }
      t = Math.min(t + 0.16, 1.5);
    });
  });

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
      </div>
      </div>
    </>
  );
}
