"use client";

/**
 * 전역 껍데기 — 상단바 + 모바일 프레임 + 하단 고지. (docs/08 §4)
 *
 * 상단바는 a1(골목)에서만 숨깁니다. a2~a5 에는 [건너뛰기]를 답니다.
 */
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { useSession } from "@/lib/store";
import { LENS_BY_ID } from "@/lib/lenses";
import { api, apiMisconfigured } from "@/lib/api";
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

export function TopBar({ title, skipTo }: { title: string; skipTo?: string }) {
  const router = useRouter();
  const seals = useSession((s) => s.seals);
  return (
    <div className="top">
      <button className="tb" onClick={() => router.back()} aria-label="뒤로">←</button>
      <span className="tt">{title}</span>
      <Link className="tb" href="/daily" aria-label="오늘의 일진">日</Link>
      <Link className="tb" href="/me" aria-label="인장첩">印 {seals.length}</Link>
      <Link className="tb" href="/lobby">진열대</Link>
      {skipTo && <Link className="tb sk" href={skipTo}>건너뛰기</Link>}
    </div>
  );
}

export default function Shell({
  title, skipTo, bare, legal, children,
}: {
  title?: string;
  skipTo?: string;
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
        {!bare && <TopBar title={title ?? ""} skipTo={skipTo} />}
        {noApi && (
          <div className="warn" style={{ margin: "12px 16px 0" }}>
            <p>계산 서버가 아직 붙지 않았소.</p>
            <p className="sm">
              화면과 서사는 볼 수 있으나 명식은 세울 수 없습니다.
              <code> NEXT_PUBLIC_API_BASE </code>를 API 주소로 설정하세요.
            </p>
          </div>
        )}
        <div className="scr">
          {children}
          {legal && <Legal />}
        </div>
      </div>
      </div>
    </>
  );
}
