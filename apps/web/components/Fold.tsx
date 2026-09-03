"use client";

/**
 * 접어 두는 말 — 읽고 싶은 사람만 편다.
 *
 * ★ 왜 이게 생겼는가 (2026-09-03)
 *
 *   손님이 말했습니다 — "전체적으로 글자가 너무 많아. 글 길이도
 *   연출점수에 포함시켜서 가독성을 극대화시켜. 가독성이 너무 안좋아."
 *
 *   재보니 **적는 자리**가 특히 심했습니다. 넉 자를 적는 화면(a4b)에
 *   853자, 이름 한 줄 적는 자리(a2)에 477자. 손님은 적으러 왔는데
 *   읽고 있습니다.
 *
 * ★ 그런데 그 글을 **지우면 안 됩니다**
 *
 *   그 안에 이 집이 파는 것이 들어 있습니다 — 왜 묻는지, 안 적으면
 *   어떻게 되는지, 여태 왜 가짜 이름을 적었는지. 지우면 연출 점수의
 *   팩폭·울림이 같이 죽고, 무엇보다 **안 물어봤는데 답해 주는 집**이
 *   아니게 됩니다.
 *
 *   그래서 **접습니다.** 화면은 짧아지고 글은 남습니다. 궁금한 사람만
 *   폅니다. 접힌 글은 분량(pace) 축에서 빠집니다 — 기본으로는 아무도
 *   안 읽으니까요. 대신 팩폭·울림·비유에는 그대로 셉니다. 편 사람은
 *   읽으니까요. (`engine/screenscan.py` 가 갈라 셉니다)
 *
 * ★ 여는 말은 **손님의 물음**으로 적습니다
 *
 *   「자세히 보기」 는 이 집의 말이 아닙니다. 손님이 속으로 하는 물음을
 *   그대로 답니다 — 「왜 묻소?」 「안 적으면 어찌 되오?」. 버튼은
 *   손님의 말이라는 규칙과 같은 자리입니다 (CLAUDE.md).
 */
import { useEffect, useRef, type ReactNode } from "react";

export default function Fold({
  label = "왜 묻소?", children,
}: {
  /** 접힌 것을 여는 한 마디. 손님이 속으로 하는 물음으로. */
  label?: string;
  children: ReactNode;
}) {
  /*
   * ★ 종이에는 접힌 자리가 없습니다.
   *   값을 치른 사람이 「＋ 왜 묻소?」 만 찍힌 종이를 받으면 안 됩니다.
   *   CSS 로는 안 열립니다(details 는 open 속성으로만 열립니다).
   *   Reveal 이 뜸을 펴는 것과 같은 자리입니다.
   */
  const ref = useRef<HTMLDetailsElement>(null);
  useEffect(() => {
    const open = () => { if (ref.current) ref.current.open = true; };
    window.addEventListener("beforeprint", open);
    const mq = window.matchMedia("print");
    mq.addEventListener?.("change", (e) => { if (e.matches) open(); });
    return () => window.removeEventListener("beforeprint", open);
  }, []);

  return (
    <details className="fold" ref={ref}>
      <summary>{label}</summary>
      <div className="foldin">{children}</div>
    </details>
  );
}
