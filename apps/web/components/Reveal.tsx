"use client";

/*
 * 한 컷씩 — 스크롤을 내리면 뜨고, 뜨기 전에 무엇을 보는지 말한다.
 *
 * ★ 손님이 한 말
 *
 *   "너무 한번에 다 분석하면 안 되니까 스크롤 내리면 뜨고, 내리면 뜨고
 *   하고, 분석하면 분석중·고민하는중·사주를 심도있게 보는중 이러면서
 *   중간 텀을 두고 심도있게 낸 결과처럼 보이게."
 *
 * ★ 다만 **없는 일을 하는 척은 안 합니다**
 *
 *   이 집은 근거 대는 집입니다. 아무 일도 안 하면서 「분석중…」 을
 *   돌리면 그게 이 집이 하는 거짓말 중 제일 큰 것이 됩니다. 손님이
 *   나중에 알면 나머지 근거까지 다 의심합니다.
 *
 *   대신 **그 컷이 실제로 보는 자리**를 말합니다. 컷마다 근거 줄이
 *   있고 거기에 무엇을 읽었는지가 적혀 있습니다 —
 *
 *       「월지를 봅니다…」        (실제로 월지를 보는 컷)
 *       「대운을 십 년 단위로 셉니다…」
 *       「없는 기운부터 셉니다…」
 *
 *   같은 뜸인데 이쪽은 **사실**입니다. 그리고 뭘 보는지 알려 주니
 *   손님이 다음 문단을 더 잘 읽습니다. a6 의 계산 장면과 같은 결입니다.
 *
 * ★ 왜 스크롤에 거는가
 *
 *   전에는 열여덟~스물두 컷이 한꺼번에 쏟아졌습니다. 그러면 손님은
 *   읽는 게 아니라 **훑습니다.** 한 컷씩 뜨면 그 컷 하나를 보게 되고,
 *   읽는 속도를 손님이 정합니다.
 *
 * ★ 두 번은 안 합니다
 *
 *   한 번 뜬 컷은 다시 올라갔다 내려와도 그대로 있습니다. 되풀이되면
 *   그건 연출이 아니라 고장입니다.
 *
 * ★ 못 움직이는 손님
 *
 *   `prefers-reduced-motion` 이면 뜸 없이 바로 보여 줍니다. 관찰자를
 *   못 쓰는 브라우저에서도 바로 보여 줍니다 — 안 보이는 것보다
 *   낫습니다.
 */

import { useEffect, useRef, useState } from "react";

/** 뜸을 들이는 시간. 너무 길면 답답하고 너무 짧으면 안 보입니다. */
const THINK_MS = 620;

export default function Reveal({
  think,
  eager = false,
  children,
  className = "",
}: {
  /** 뜨기 전에 보여 줄 한 줄. 없으면 그냥 뜹니다. */
  think?: string;
  /** 첫 컷처럼 이미 화면에 있는 것 — 기다리지 않습니다. */
  eager?: boolean;
  children: React.ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  // 0 안 보임 · 1 생각중 · 2 떴음
  const [phase, setPhase] = useState<0 | 1 | 2>(eager || !think ? 2 : 0);

  /*
   * ★ 종이로 받을 때는 다 펴 둡니다.
   *
   *   안 뜬 컷은 **아예 안 그려져 있습니다.** 그대로 인쇄하면 값을
   *   치른 사람이 빈 종이를 받습니다. 인쇄창이 열리기 전에 펴 둡니다.
   *   (`beforeprint` 는 사파리가 안 부르므로 미디어 질의도 함께 겁니다)
   */
  useEffect(() => {
    if (phase === 2) return;
    const open = () => setPhase(2);
    window.addEventListener("beforeprint", open);
    const mq = window.matchMedia?.("print");
    mq?.addEventListener?.("change", (e) => { if (e.matches) open(); });
    return () => window.removeEventListener("beforeprint", open);
  }, [phase]);

  useEffect(() => {
    if (phase === 2) return;
    const el = ref.current;
    if (!el) return;

    const reduced =
      typeof window !== "undefined" &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (reduced || typeof IntersectionObserver === "undefined") {
      setPhase(2);
      return;
    }

    let timer: ReturnType<typeof setTimeout> | undefined;
    const io = new IntersectionObserver(
      (entries) => {
        if (!entries[0]?.isIntersecting) return;
        io.disconnect();
        setPhase(1);
        timer = setTimeout(() => setPhase(2), THINK_MS);
      },
      // 아래에서 올라올 때 조금 일찍 잡습니다 — 손님이 다 올린 뒤에
      // 생각을 시작하면 그건 기다림이 됩니다.
      { rootMargin: "0px 0px -18% 0px", threshold: 0.01 }
    );
    io.observe(el);
    return () => {
      io.disconnect();
      if (timer) clearTimeout(timer);
    };
  }, [phase]);

  return (
    <div
      ref={ref}
      className={
        className + " rv" + (phase === 0 ? " rv0" : phase === 1 ? " rv1" : " rv2")
      }
    >
      {phase === 1 && think && (
        <p className="thinking" aria-live="polite">
          <i />
          <i />
          <i />
          <span>{think}</span>
        </p>
      )}
      {phase === 2 && children}
      {/* 아직 안 뜬 자리도 높이를 잡아 둡니다 — 안 그러면 아래 것이
          위로 튀어 올라와 손님이 읽던 자리를 잃습니다. */}
      {phase === 0 && <div className="rvhold" aria-hidden="true" />}
    </div>
  );
}
