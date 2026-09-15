"use client";

import Image from "next/image";

/**
 * 동글 달묘 — 읽는 내내 곁에 있는 안내묘.
 *
 * ★ 왜 그림으로 바꿨나 (2026-09-15)
 *
 *   2026-09-14 에 「동글 달묘」로 다시 그려 놓고도 저장소에는 한 번도
 *   안 들어갔습니다 — 배포용 사본 폴더(output/deploy-dalmyo)에만 살아
 *   있었고, 그 폴더는 .gitignore 에 들어 있습니다. 그래서 손님 눈에는
 *   「바뀐」 것이 아니라 **한 번도 안 온** 것이었습니다.
 *
 * ★ 그림은 폰 크기로 줄여서 넣습니다
 *
 *   원본은 1254×1254 · 1.6MB 였습니다. 화면에서 쓰는 크기는 폰 88px ·
 *   넓은 화면 104px 이라, 3배 화면을 받아도 312px 이면 넉넉합니다.
 *   320×320 으로 줄이니 124KB 가 됐습니다 (7.4%). 폰으로 들어오는
 *   손님에게 1.6MB 를 내려보낼 까닭이 없습니다.
 */
export default function CompanionCat({ state = "rest", message }: {
  state?: "welcome" | "selected" | "rest" | "saved";
  message?: string;
}) {
  return (
    <div className={`companion-cat companion-cat--${state}`}>
      <Image className="dalmyo-portrait" src="/images/dalmyo-v1.png"
        alt={message ? "" : "동글 달묘"} width={320} height={320}
        sizes="(max-width: 767px) 88px, 104px" priority={state === "welcome"} />
      {message && <div className="hamyo-speech"><span className="hamyo-name">안내묘 · 동글 달묘</span><p>{message}</p></div>}
    </div>
  );
}
