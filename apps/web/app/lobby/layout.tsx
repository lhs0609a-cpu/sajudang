import type { Metadata } from "next";
import { PUBLIC_PAGES } from "@/lib/site";

/**
 * 이 화면의 제목과 한 줄 — **화면마다 따로** (2026-09-24).
 *
 * ★ 다섯 화면이 제목·설명이 전부 같았습니다 (「성신당 星辰堂」 · 같은 한 줄).
 *   그러면 사이트맵과 RSS 를 내도 검색엔진이 중복으로 보고 하나만 남기거나
 *   버립니다 — 지도를 그려 놓고 자리마다 같은 이름을 붙인 셈이오.
 *
 * ★ 화면이 `"use client"` 라 여기에 둡니다. 클라이언트 컴포넌트는 metadata
 *   를 내놓을 수 없으니, 라우트마다 서버 layout 을 세워 제목만 답니다.
 *   보이는 것은 하나도 안 바뀝니다 — children 을 그대로 돌려줍니다.
 */
const page = PUBLIC_PAGES.find((p) => p.path === "/lobby")!;

export const metadata: Metadata = {
  title: page.title,
  description: page.desc,
  alternates: { canonical: page.path },
  openGraph: {
    title: `${page.title} · 성신당 星辰堂`,
    description: page.desc,
    url: page.path,
  },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
