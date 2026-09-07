"use client";

/*
 * 아래로 — **더 있다는 표시.**
 *
 * ★ 손님이 짚은 것 (2026-09-07)
 *
 *   "지금 화면 내리면 글자 뜨는건 좋은데, 아래로 이런 표시가 항상
 *   떠야 사람들이 내릴거 아냐."
 *
 *   맞습니다. `Reveal` 은 스크롤을 내려야 다음 컷이 뜨는데, **내릴
 *   까닭을 화면이 말한 적이 없었습니다.** 한 컷을 다 읽은 손님이
 *   보기에는 거기가 끝입니다 — 스물몇 컷이 아래에 있는데도요.
 *   연출이 손님을 기다리는데 손님은 끝난 줄 압니다.
 *
 * ★ 안 뜨는 자리
 *
 *   · 바닥에 닿았을 때 — 더 없는데 내리라 하면 거짓말입니다.
 *   · 스크롤이 아예 없을 때 (짧은 화면).
 *   · 인쇄할 때. 종이에는 아래가 없습니다.
 *
 * ★ 표지판이지 말이 아닙니다
 *
 *   「아래로」는 캐릭터의 대사가 아니라 **표지판**입니다. 그래서
 *   말투 층에 안 태웁니다 — 해요체 캐릭터에게서 「아래로예요」가
 *   나오면 그게 비문입니다. (「이게 무슨 말인가」 상자와 같은 규칙)
 *
 * ★ 못 움직이는 손님
 *
 *   `prefers-reduced-motion` 이면 까딱임을 멈춥니다. 표시는 남깁니다 —
 *   움직임이 싫은 것이지 길 안내가 싫은 것은 아닙니다.
 */

import { useEffect, useState } from "react";

/** 바닥을 이만큼 남기면 «다 왔다» 로 봅니다. */
const BOTTOM_SLACK = 120;

export default function ScrollHint({
  label = "아래로",
}: {
  /** 표지판 글. 기본은 「아래로」. */
  label?: string;
}) {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const look = () => {
      const doc = document.documentElement;
      const left = doc.scrollHeight - (window.scrollY + window.innerHeight);
      setShow(doc.scrollHeight > window.innerHeight + BOTTOM_SLACK
              && left > BOTTOM_SLACK);
    };
    look();
    window.addEventListener("scroll", look, { passive: true });
    window.addEventListener("resize", look);
    /*
     * ★ 컷이 뜨면 문서가 길어집니다.
     *   스크롤·리사이즈만 보면 «다 왔다» 로 굳은 채 남습니다 —
     *   새 컷이 밑에 붙어도 표시가 안 돌아옵니다.
     */
    const grow = new ResizeObserver(look);
    grow.observe(document.body);
    return () => {
      window.removeEventListener("scroll", look);
      window.removeEventListener("resize", look);
      grow.disconnect();
    };
  }, []);

  return (
    <div className={"sdown" + (show ? " on" : "")} aria-hidden="true">
      <span className="t">{label}</span>
      <span className="a" />
    </div>
  );
}
