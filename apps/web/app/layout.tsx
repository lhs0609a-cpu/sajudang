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
      <body spellCheck={false}>{children}</body>
    </html>
  );
}
