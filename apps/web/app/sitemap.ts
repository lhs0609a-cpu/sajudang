import type { MetadataRoute } from "next";
import { PUBLIC_PAGES, SITE } from "@/lib/site";

/**
 * 크롤러가 걸어 다닐 길 (§26).
 *
 * ★ **공개된 자리만** 적습니다.
 *   내 첩·리포트·공유 링크는 그 사람 것이라 robots.ts 에서 닫았습니다.
 *   여기에 적으면 닫아 놓고 문 앞에 안내판을 세우는 꼴이 됩니다.
 *
 * ★ 없는 날짜를 지어내지 않습니다.
 *   `lastModified` 는 빌드 시각입니다. 배포할 때마다 바뀌는 값이고,
 *   실제로 그때 다시 올라간 것이 맞습니다.
 *
 * ★ 자리 목록은 `lib/site.ts` 한 벌에서 받습니다 (2026-09-24).
 *   전에는 여기 두 줄(첫 화면·법정 고지)만 있었고, 진열대·추가 분석·
 *   일진은 크롤러가 걸어 들어올 수는 있는데 지도에는 없었습니다.
 *   그리고 주소가 이 파일에도 박혀 있어, 환경변수가 안 걸린 배포에서
 *   **고유 도메인의 지도가 다른 도메인만 가리켰습니다.**
 */
export default function sitemap(): MetadataRoute.Sitemap {
  const at = new Date();
  return PUBLIC_PAGES.filter((p) => p.inSitemap).map((p) => ({
    url: `${SITE}${p.path}`,
    lastModified: at,
    changeFrequency: p.changeFrequency,
    priority: p.priority,
  }));
}
