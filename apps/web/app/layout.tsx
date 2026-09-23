import type { Metadata, Viewport } from "next";
import "./globals.css";
import WebVitals from '@/components/WebVitals';
import SeatsShortcut from '@/components/SeatsShortcut';
import FortuneShortcut from '@/components/FortuneShortcut';

/*
 * ★ 공유되는 링크가 **카드로 서야** 합니다.
 *
 *   이 집의 성장 루프는 공유입니다 — 분석지 한 장을 받아 건네는 것.
 *   그런데 미리보기가 붙어 있던 곳은 공유 화면(`/s/[token]`) 하나뿐이고,
 *   정작 가장 많이 도는 주소인 **첫 화면에는 og 가 한 줄도** 없었습니다.
 *   제목 없는 맨 주소로 뜨는 링크는 눌리지 않습니다.
 *
 * ★ metadataBase 가 없으면 상대 주소가 깨집니다.
 *   og:image 는 절대 주소라야 크롤러가 받아 갑니다.
 */
const SITE =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://sajudang-three.vercel.app";

const OG_DESC =
  "사주로 읽는 나의 반복 패턴. 지금의 고민에 맞는 해석과 오늘 해볼 행동을 만나보시오.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE),
  title: { default: "성신당 星辰堂", template: "%s · 성신당 星辰堂" },
  description: OG_DESC,
  applicationName: "성신당 星辰堂",
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    siteName: "성신당 星辰堂",
    locale: "ko_KR",
    url: "/",
    title: "성신당 星辰堂 — 맞히는 집이 아니라, 근거 대는 집",
    description: OG_DESC,
    images: [{ url: "/og.jpg", width: 1200, height: 630,
               alt: "밤의 성신당" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "성신당 星辰堂 — 맞히는 집이 아니라, 근거 대는 집",
    description: OG_DESC,
    images: ["/og.jpg"],
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#141614",
};

import MemberSync from '@/components/MemberSync';
import AccountBar from '@/components/AccountBar';
import BackgroundMusic from '@/components/BackgroundMusic';
import LiveActivity from '@/components/LiveActivity';
import InvitationArrival from '@/components/InvitationArrival';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    /*
     * ★ spellCheck={false} — 글 밑에 빨간 물결이 그어지던 것.
     *
     *   우리 CSS 에도 문장 뱅크에도 밑줄을 긋는 것이 없습니다(뱅크는
     *   <b> 만 씁니다). 브라우저와 맞춤법 검사 확장이 그린 것입니다.
     *   「엄살」 「아낀다」 처럼 사전에 없는 말이 밑줄을 답니다.
     *
     *   손님에게는 그게 **오탈자로 보입니다.** 근거 대는 집인데 글이
     *   틀린 것처럼 보이면 안 됩니다. 읽기만 하는 글이라 검사가 필요
     *   없으므로 통째로 끕니다. (확장 프로그램은 이걸 무시할 수도
     *   있습니다 — 그건 손님 브라우저 쪽입니다.)
     *
     *   translate="no" 도 같이 답니다. 자동 번역이 켜지면 하오체가
     *   뭉개지고 명리 용어가 엉뚱하게 바뀝니다.
     */
    <html lang="ko" translate="no">
      {/*
       * ★ 글꼴을 여기서 받아 옵니다.
       *
       *   tokens.css 는 이름만 적어 뒀고 받아 오는 자리가 없었습니다.
       *   그래서 본문이 시스템 고정폭으로 그려졌습니다 — 사주 보는
       *   집인데 터미널처럼 보였습니다.
       *
       *   next/font 대신 <link> 를 씁니다. 구글의 css2 는 한글을
       *   unicode-range 로 백여 조각으로 쪼개 **쓰는 조각만** 내려
       *   보냅니다. 한글 글꼴은 통째로 받으면 수 MB 라, CJK 에서는
       *   이 쪽이 훨씬 가볍습니다.
       *
       *   display=swap — 글꼴을 기다리며 글을 감추지 않습니다.
       *   첫 화면이 비어 보이는 것보다 잠깐 대체 글꼴로 보이는 게
       *   낫습니다.
       */}
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          rel="stylesheet"
          href={
            "https://fonts.googleapis.com/css2" +
            "?family=Noto+Serif+KR:wght@400;600;700" +
            "&family=Noto+Sans+KR:wght@400;500;700" +
            "&display=swap"
          }
        />
      </head>
      <body spellCheck={false}><BackgroundMusic /><MemberSync /><AccountBar /><InvitationArrival />{children}<FortuneShortcut /><SeatsShortcut /><LiveActivity /><WebVitals /></body>
    </html>
  );
}
