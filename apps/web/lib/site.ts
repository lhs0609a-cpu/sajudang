/**
 * 이 집의 **정본 주소** — 한 자리.
 *
 * ★ 같은 예비값이 세 곳에 적혀 있었습니다 (2026-09-24).
 *   `app/layout.tsx` · `app/robots.ts` · `app/sitemap.ts` 가 각자
 *   `"https://sajudang-three.vercel.app"` 를 들고 있었고, Vercel 에
 *   `NEXT_PUBLIC_SITE_URL` 이 안 걸려 있어 그 예비값이 그대로 나갔습니다.
 *
 *   그래서 고유 도메인으로 들어온 손님의 페이지가 **정본은 저쪽이라고**
 *   말하고 있었습니다 —
 *
 *       saju.megaload.co.kr 의 canonical → sajudang-three.vercel.app
 *       saju.megaload.co.kr/sitemap.xml  → vercel.app 주소만 나열
 *       robots.txt 의 Host·Sitemap      → vercel.app
 *
 *   검색엔진은 이걸 「이 주소는 사본이오」 로 읽습니다. 소유 확인을 해도
 *   색인은 저쪽으로 갑니다. 주소는 한 자리에서만 정합니다.
 *
 * ★ 환경변수가 이깁니다.
 *   미리보기 배포(vercel.app)에서도 그 주소로 두려면 `NEXT_PUBLIC_SITE_URL`
 *   을 걸면 됩니다. 안 걸면 **고유 도메인**이 정본입니다.
 */
export const SITE =
  (process.env.NEXT_PUBLIC_SITE_URL ?? "https://saju.megaload.co.kr")
    .replace(/\/+$/, "");

/** 사이트 이름 — 제목 틀과 피드가 같이 씁니다. */
export const SITE_NAME = "성신당 星辰堂";

/** 한 줄 소개. 공유 카드와 피드가 같이 씁니다. */
export const SITE_DESC =
  "사주로 읽는 나의 반복 패턴. 지금의 고민에 맞는 해석과 오늘 해볼 행동을 만나보시오.";

/**
 * 검색엔진에 내놓는 **공개된 자리**.
 *
 * ★ 사이트맵·RSS·화면별 제목이 이 한 벌을 같이 봅니다. 세 곳에 따로
 *   적으면 한 곳만 고치는 날이 옵니다.
 *
 * ★ 여기에 **그 사람 것**은 안 적습니다 — 리포트(`/report/*`) · 공유
 *   링크(`/s/*`) · 내 첩(`/me`) · 결제(`/pay`)는 `robots.ts` 에서
 *   닫아 두었습니다. 닫아 놓고 문 앞에 안내판을 세우지 않습니다.
 */
export interface PublicPage {
  path: string;
  /** 화면 제목. 제목 틀(`%s · 성신당 星辰堂`)에 들어갑니다. */
  title: string;
  /** 검색 결과와 피드에 나가는 한 줄. */
  desc: string;
  /** 사이트맵에 적을 것인가. 손님 입력 없이는 빈 화면인 자리는 뺍니다. */
  inSitemap: boolean;
  changeFrequency: "daily" | "weekly" | "monthly";
  priority: number;
}

export const PUBLIC_PAGES: readonly PublicPage[] = [
  {
    path: "/",
    title: "별에 묻고, 나를 읽다",
    desc: SITE_DESC,
    inSitemap: true,
    changeFrequency: "weekly",
    priority: 1,
  },
  {
    path: "/lobby",
    title: "스무 사람의 진열대",
    desc: "같은 여덟 글자를 스무 사람이 각자의 눈으로 읽소. 누구에게 물을지 고르는 자리요.",
    inSitemap: true,
    changeFrequency: "weekly",
    priority: 0.8,
  },
  {
    path: "/fortune",
    title: "대운·세운·궁합 따로 보기",
    desc: "십 년 단위 흐름과 해마다의 흐름, 궁합과 택일을 따로 펴 보는 자리요. 무엇을 세어 본 것인지 함께 적소.",
    inSitemap: true,
    changeFrequency: "weekly",
    priority: 0.6,
  },
  {
    path: "/daily",
    title: "오늘의 일진",
    desc: "오늘 하루에 붙는 두 글자를 그대 여덟 글자와 맞대어 보오. 좋은 날·나쁜 날을 정하지는 않소.",
    inSitemap: true,
    changeFrequency: "daily",
    priority: 0.5,
  },
  {
    path: "/legal",
    title: "이용 안내와 개인정보",
    desc: "무엇을 받아 무엇을 남기는지, 무엇을 말하지 않는지 적어 두었소. 환불과 탈퇴도 여기 있소.",
    inSitemap: true,
    changeFrequency: "monthly",
    priority: 0.3,
  },
];
