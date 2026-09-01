/**
 * @screen s1 s2
 * 공유 링크의 서버 껍데기.
 *
 * ★ 이 파일이 서버 컴포넌트인 이유
 *   카톡·슬랙·트위터 크롤러는 자바스크립트를 돌리지 않습니다.
 *   미리보기(og:title, og:description)를 서버에서 만들어 주지 않으면
 *   링크가 제목 없는 맨 주소로 뜨고, 그 링크는 눌리지 않습니다.
 *
 * ★ 미리보기에도 생년월일시는 넣지 않습니다.
 */
import type { Metadata } from "next";
import SharedView from "./SharedView";

/**
 * ★ 서버에서는 API_BASE(런타임)를 먼저 봅니다.
 *   NEXT_PUBLIC_* 은 빌드 시점에 값이 박혀 버려서, 배포 후 API 주소가
 *   바뀌면 미리보기가 조용히 깨집니다. 서버 컴포넌트는 런타임에 읽습니다.
 */
const BASE =
  process.env.API_BASE ??
  process.env.NEXT_PUBLIC_API_BASE ??
  "http://localhost:8000";

async function fetchShared(token: string) {
  try {
    const res = await fetch(
      `${BASE}/v1/share/${encodeURIComponent(token)}`,
      { next: { revalidate: 60 } },
    );
    if (!res.ok) return null;
    return (await res.json()) as {
      from_name: string | null;
      day_gan: string;
      ilgan_name: string;
      headline: string;
      three_lines: string[];
    };
  } catch {
    return null;
  }
}

export async function generateMetadata(
  { params }: { params: { token: string } },
): Promise<Metadata> {
  const d = await fetchShared(params.token);
  if (!d) {
    return {
      title: "성신당 星辰堂",
      description: "맞히는 집이 아니라, 근거 대는 집.",
    };
  }
  const who = d.from_name ? `${d.from_name}님이 보낸 ` : "";
  const title = `${who}${d.day_gan} · ${d.ilgan_name}`;
  const description = [d.headline, ...d.three_lines].join(" / ");
  return {
    title,
    description,
    openGraph: {
      title,
      description,
      siteName: "성신당 星辰堂",
      type: "article",
      locale: "ko_KR",
    },
    twitter: { card: "summary_large_image", title, description },
  };
}

export default function SharedPage({ params }: { params: { token: string } }) {
  return <SharedView token={params.token} />;
}
