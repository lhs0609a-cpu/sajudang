import { PUBLIC_PAGES, SITE, SITE_DESC, SITE_NAME } from "@/lib/site";

/**
 * RSS 2.0 피드 — 네이버 서치어드바이저·구글에 낼 자리.
 *
 * ★ 왜 사이트맵만으로 안 되나
 *
 *   사이트맵은 「이런 주소가 있소」 만 말합니다. 네이버는 그 위에 **RSS 제출**
 *   을 따로 받습니다 — 제목과 한 줄 소개가 함께 들어와야 무엇을 내놓는
 *   집인지 읽습니다. 지금 이 집은 화면마다 제목이 같았고(성신당 한 줄),
 *   그래서 사이트맵만 내면 다섯 자리가 한 자리로 접혔습니다.
 *
 * ★ 날짜를 지어내지 않습니다
 *
 *   `pubDate` 와 `lastBuildDate` 는 **빌드 시각**입니다. 이 자리는 손님마다
 *   달라지는 글이 아니라 배포할 때 바뀌는 글이라, 그때 다시 올라간 것이
 *   맞습니다 (`app/sitemap.ts` 의 `lastModified` 와 같은 규칙).
 *   하루마다 다시 굽지 않습니다 — 안 바뀐 날에 바뀌었다고 말하면 그건
 *   피드를 읽는 쪽을 속이는 것이오.
 *
 * ★ 그 사람 것은 안 싣습니다
 *
 *   리포트·공유 링크·내 첩·결제는 `robots.ts` 에서 닫아 둔 자리입니다.
 *   피드는 문 앞에 세우는 안내판이라 닫은 자리를 여기 적으면 안 됩니다.
 *   목록은 `lib/site.PUBLIC_PAGES` 한 벌에서 받습니다.
 */
function esc(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export async function GET(): Promise<Response> {
  const built = new Date();
  const stamp = built.toUTCString();

  const items = PUBLIC_PAGES.map((p) => {
    const url = `${SITE}${p.path}`;
    return [
      "    <item>",
      `      <title>${esc(p.title)}</title>`,
      `      <link>${esc(url)}</link>`,
      `      <guid isPermaLink="true">${esc(url)}</guid>`,
      `      <description>${esc(p.desc)}</description>`,
      `      <pubDate>${stamp}</pubDate>`,
      "    </item>",
    ].join("\n");
  }).join("\n");

  const xml = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
    "  <channel>",
    `    <title>${esc(SITE_NAME)}</title>`,
    `    <link>${esc(SITE)}/</link>`,
    `    <description>${esc(SITE_DESC)}</description>`,
    "    <language>ko</language>",
    `    <lastBuildDate>${stamp}</lastBuildDate>`,
    `    <atom:link href="${esc(SITE)}/rss.xml" rel="self" type="application/rss+xml" />`,
    items,
    "  </channel>",
    "</rss>",
    "",
  ].join("\n");

  return new Response(xml, {
    headers: {
      "Content-Type": "application/rss+xml; charset=utf-8",
      // 배포된 것을 그대로 내줍니다. 사이 서버가 하루쯤 들고 있어도
      // 무방한 글이라 재검증 여유를 줍니다.
      "Cache-Control": "public, max-age=0, s-maxage=3600, stale-while-revalidate=86400",
    },
  });
}
