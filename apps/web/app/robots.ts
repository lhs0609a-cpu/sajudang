import type { MetadataRoute } from "next";

/**
 * 크롤러에게 주는 지도 (§26).
 *
 * ★ 열어 둘 것과 닫을 것을 가릅니다.
 *
 *   여는 곳   첫 화면 · 법정 고지. 이 집을 찾아오는 길입니다.
 *   닫는 곳   주인 자리(/admin) · 내 서재(/me) · 결제(/pay) ·
 *            리포트(/report/*) · 공유 링크(/s/*)
 *
 *   뒤쪽은 **그 사람 것**입니다. 리포트와 공유 링크는 주소만 알면
 *   열리는 자리라(그렇게 설계했습니다), 검색 결과에 실리면 건네받은
 *   사람만 보라고 만든 것이 아무나 보는 것이 됩니다.
 *   공유 링크에 생년월일시가 없다 해도 그 사람의 해석입니다.
 */
const SITE =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://sajudang-three.vercel.app";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [{
      userAgent: "*",
      allow: ["/", "/legal"],
      disallow: ["/admin", "/admin/", "/me", "/pay", "/report/", "/s/",
                 "/relay", "/summary", "/api/"],
    }],
    sitemap: `${SITE}/sitemap.xml`,
    host: SITE,
  };
}
