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
  year: number;
  month: number;
  day: number;
  hour: number | null;      // null = 시각 미상
  minute: number;
  hourKnown: boolean;
  sex: "M" | "F";
  city: string;
  axis4: string | null;     // 성향 4글자. 선택.
  concern: Concern;

  /* 서버 결과 */
  chartId: string | null;
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
  year: 1993,
  month: 5,
  day: 15,
  hour: null as number | null,
  minute: 0,
  hourKnown: false,
  sex: "F" as const,
  city: "서울",
  axis4: null as string | null,
  concern: "love" as Concern,
  chartId: null,
  features: null,
  cur: DEFAULT_LENS,
  read: [] as string[],
  skipped: [] as string[],
  seals: [] as string[],
  tier: "free" as Tier,
  paid: false,
  relayUsed: 0,
  visits: 0,
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
      }),
    },
  ),
);

/** 절기 기준으로 계절을 고른다. (docs/09 §5 — 같은 사람이 계절마다 다른 화면을 본다) */
export function seasonOf(d: Date = today): Season {
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

export const TIERS: { id: Tier; name: string; price: string; desc: string }[] = [
  { id: "one", name: "이 자리 하나", price: "3,900원", desc: "고른 영역 전부 · 시기 포함" },
  { id: "all", name: "여덟 글자 전부", price: "19,900원", desc: "평생운 18컷 · 25페이지" },
  { id: "sub", name: "스무 사람 모두", price: "9,900원/월", desc: "전 캐릭터 무제한 · 월간 세운" },
];
