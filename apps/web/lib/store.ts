/**
 * 세션 상태 — Zustand. 가벼운 세션 값만 둡니다.
 *
 * ★ features 는 서버가 준 값을 그대로 들고만 있습니다. 여기서 고치지 마세요.
 * ★ 브레이크(세션 릴레이 2명 등)의 판정은 서버가 합니다. 여기 값은 표시용입니다.
 */
"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Features } from "@shared/chart";
import { DEFAULT_LENS } from "./lenses";

export type Concern = "money" | "work" | "love" | "people" | "dir" | "health";
export type Tier = "free" | "one" | "all" | "sub";
export type Season = "spring" | "summer" | "autumn" | "winter";

export interface SessionState {
  sessionId: string;

  /* 입력 */
  name: string;
  /* ★ 빈칸으로 시작합니다. 채워 두면 그냥 넘기고 **남의 사주**를 봅니다.
     "근거 대는 집" 에서 가장 나쁜 실패는 틀린 것을 근거까지 붙여 보여주는
     것입니다. 0 이 아니라 null 이라야 화면이 빈칸을 그립니다. */
  year: number | null;
  month: number | null;
  day: number | null;
  hour: number | null;      // null = 시각 미상
  minute: number;
  hourKnown: boolean;
  sex: "M" | "F";
  city: string;
  axis4: string | null;     // 성향 4글자. 선택.
  concern: Concern;

  /* 서버 결과 */
  chartId: string | null;
  /** 희소도 — 센 값. 없으면 화면이 그 자리를 접는다 */
  rarity: import("@shared/chart").Rarity | null;
  features: Features | null;

  /* 진행 */
  cur: string;              // 현재 렌즈 id
  read: string[];
  skipped: string[];
  seals: string[];
  tier: Tier;
  paid: boolean;
  relayUsed: number;
  visits: number;

  /* ── 관리자 레일 ──
     ?admin=1 로 켜고 ?admin=0 으로 끕니다. 전체 화면을 오가며
     플로우를 확인하는 용도입니다.

     기본값은 빌드가 정합니다 — NEXT_PUBLIC_ADMIN_DEFAULT (docs/17 §4).
     출시 전에는 켜짐이라 새 브라우저에서도 바로 보입니다.
     출시할 때 그 값을 0 으로 두면 기본 꺼짐이 됩니다.

     adminSet 은 **사람이 직접 정했는가**를 기억합니다. 이게 없으면
     ?admin=0 으로 끈 것을 다음 방문에서 기본값이 도로 켜 버립니다. */
  admin: boolean;
  adminSet: boolean;
  seasonOverride: Season | null;   // 진입 서사 4계절 확인
  ilganOverride: string | null;    // 일간 10색 테마 확인

  set: (patch: Partial<SessionState>) => void;
  markRead: (id: string) => void;
  markSkipped: (id: string) => void;
  reset: () => void;
}

const today = new Date();

function newSessionId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID();
  return "s" + Math.random().toString(36).slice(2) + Date.now().toString(36);
}

const initial = {
  sessionId: newSessionId(),
  name: "",
  year: null as number | null,
  month: null as number | null,
  day: null as number | null,
  hour: null as number | null,
  minute: 0,
  hourKnown: false,
  sex: "F" as const,
  city: "서울",
  axis4: null as string | null,
  concern: "love" as Concern,
  chartId: null,
  rarity: null,
  features: null,
  cur: DEFAULT_LENS,
  read: [] as string[],
  skipped: [] as string[],
  seals: [] as string[],
  tier: "free" as Tier,
  paid: false,
  relayUsed: 0,
  visits: 0,
  admin: false,          // 첫 그림(SSR)에는 레일이 없다 — 켜는 것은 DevRail 이 한다
  adminSet: false,
  seasonOverride: null as Season | null,
  ilganOverride: null as string | null,
};

export const useSession = create<SessionState>()(
  persist(
    (set) => ({
      ...initial,
      set: (patch) => set(patch),
      markRead: (id) =>
        set((s) => (s.read.includes(id) ? s : { read: [...s.read, id] })),
      markSkipped: (id) =>
        set((s) => (s.skipped.includes(id) ? s : { skipped: [...s.skipped, id] })),
      reset: () => set({ ...initial, sessionId: newSessionId() }),
    }),
    {
      name: "sajudang-session",
      // features 는 서버 캐시에서 다시 받을 수 있으므로 저장하지 않는다
      partialize: (s) => ({
        sessionId: s.sessionId, name: s.name, year: s.year, month: s.month,
        day: s.day, hour: s.hour, minute: s.minute, hourKnown: s.hourKnown,
        sex: s.sex, city: s.city, axis4: s.axis4, concern: s.concern,
        chartId: s.chartId, cur: s.cur, read: s.read, skipped: s.skipped,
        seals: s.seals, tier: s.tier, paid: s.paid, visits: s.visits,
        admin: s.admin, adminSet: s.adminSet, seasonOverride: s.seasonOverride,
        ilganOverride: s.ilganOverride,
      }),
    },
  ),
);

/** 절기 기준으로 계절을 고른다. (docs/09 §5 — 같은 사람이 계절마다 다른 화면을 본다) */
export function seasonOf(d: Date = new Date()): Season {
  const m = d.getMonth() + 1;
  if (m >= 2 && m <= 4) return "spring";
  if (m >= 5 && m <= 7) return "summer";
  if (m >= 8 && m <= 10) return "autumn";
  return "winter";
}

export const CONCERNS: { id: Concern; label: string; sub: string }[] = [
  { id: "money", label: "돈", sub: "버는 것, 모이는 것" },
  { id: "work", label: "일", sub: "직장, 사업, 방향" },
  { id: "love", label: "사랑", sub: "연애, 결혼, 이별" },
  { id: "people", label: "사람", sub: "관계, 배신, 외로움" },
  { id: "dir", label: "방향", sub: "이대로 맞나" },
  { id: "health", label: "몸", sub: "기운, 잠, 지침" },
];

/**
 * 목패의 이름만 여기 둡니다.
 *
 * ★ 값과 분량은 **서버가 셉니다** — `POST /v1/pay/tiers`.
 *   여기 "평생운 18컷 · 25페이지" 라고 적혀 있었는데 실제로 나오는 것은
 *   11~12컷 · 6탭이었습니다. 화면이 제 손으로 분량을 적으면 엔진이
 *   달라져도 이 줄은 안 바뀌므로, 다시 어긋납니다.
 *   값도 같습니다 — 캐릭터마다 다르고, 서버가 청구하는 값만이 참입니다.
 */
export const TIER_ORDER: Tier[] = ["one", "all", "sub"];

/** 화면 대장 — 관리자 레일이 이걸로 목록을 그립니다. docs/08 §1 */
export interface ScreenLink {
  id: string;
  name: string;
  href: string;
}
export const SCREEN_GROUPS: { group: string; label: string; items: ScreenLink[] }[] = [
  {
    group: "A", label: "들어가다",
    items: [
      { id: "a1", name: "골목", href: "/?step=a1" },
      { id: "a2", name: "이름", href: "/?step=a2" },
      { id: "a3", name: "날·고을", href: "/?step=a3" },
      { id: "a4", name: "때", href: "/?step=a4" },
      { id: "a4b", name: "성향 4글자", href: "/?step=a4b" },
      { id: "a5", name: "고민", href: "/?step=a5" },
      { id: "a6", name: "명식", href: "/?step=a6" },
      { id: "a7", name: "훅 5단", href: "/?step=a7" },
    ],
  },
  {
    group: "B", label: "둘러보다",
    items: [
      { id: "b1", name: "진열대", href: "/lobby?tab=b1" },
      { id: "b2", name: "스무 사람", href: "/lobby?tab=b2" },
      { id: "b3", name: "그 사람", href: "/lobby?tab=b3" },
      { id: "b4", name: "내 명식", href: "/lobby?tab=b4" },
    ],
  },
  {
    group: "C", label: "읽다",
    items: [
      { id: "c1", name: "표지", href: "/report/pungun?tab=c1" },
      { id: "c2", name: "본문", href: "/report/pungun?tab=c2" },
      { id: "c3", name: "대운 맵", href: "/report/pungun?tab=c3" },
      { id: "c4", name: "페이월", href: "/report/pungun?tab=c4" },
      { id: "c5", name: "공유 카드", href: "/report/pungun?tab=c5" },
      { id: "c6", name: "피드백", href: "/report/pungun?tab=c6" },
      { id: "c7", name: "분석지", href: "/summary" },
      { id: "c8", name: "내보내기", href: "/summary#share" },
    ],
  },
  {
    group: "D", label: "값을 치르다",
    items: [
      { id: "d0", name: "무료 6단", href: "/pay?step=d0" },
      { id: "d1", name: "어디까지", href: "/pay?step=d1" },
      { id: "d2", name: "결제", href: "/pay?step=d2" },
      { id: "d3", name: "완료", href: "/pay?step=d3" },
    ],
  },
  {
    group: "H·G·F·R", label: "이어지다 · 다시 오다 · 모으다",
    items: [
      { id: "h1", name: "릴레이", href: "/relay" },
      { id: "g1", name: "오늘의 일진", href: "/daily" },
      { id: "f2", name: "인장첩", href: "/me?tab=f2" },
      { id: "r1", name: "후기", href: "/me?tab=r1" },
    ],
  },
  {
    group: "S", label: "건너오다 (공유 유입)",
    items: [{ id: "s1", name: "받은 분석지", href: "/summary" }],
  },
];
