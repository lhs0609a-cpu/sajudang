import type { MetadataRoute } from "next";

/**
 * 크롤러가 걸어 다닐 길 (§26).
 *
 * ★ **공개된 자리만** 적습니다.
 *   내 서재·리포트·공유 링크는 그 사람 것이라 robots.ts 에서 닫았습니다.
 *   여기에 적으면 닫아 놓고 문 앞에 안내판을 세우는 꼴이 됩니다.
 *
 * ★ 없는 날짜를 지어내지 않습니다.
 *   `lastModified` 는 빌드 시각입니다. 배포할 때마다 바뀌는 값이고,
 *   실제로 그때 다시 올라간 것이 맞습니다.
 */
const SITE =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://sajudang-three.vercel.app";

export default function sitemap(): MetadataRoute.Sitemap {
  const at = new Date();
  return [
    { url: `${SITE}/`, lastModified: at, changeFrequency: "weekly", priority: 1 },
    { url: `${SITE}/legal`, lastModified: at, changeFrequency: "monthly", priority: 0.3 },
  ];
}
