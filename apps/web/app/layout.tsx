import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "성신당 星辰堂",
  description: "맞히는 집이 아니라, 근거 대는 집.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0C0A12",
};

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
            "?family=Nanum+Myeongjo:wght@400;700;800" +
            "&family=Noto+Serif+KR:wght@400;500;600;700" +
            "&family=Noto+Sans+KR:wght@400;500;700" +
            "&family=IBM+Plex+Mono:wght@400;500" +
            "&display=swap"
          }
        />
      </head>
      <body spellCheck={false}>{children}</body>
    </html>
  );
}
