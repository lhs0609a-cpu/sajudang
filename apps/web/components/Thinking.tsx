"use client";

/*
 * 뜸 — 읽는 사람이 오는 동안 무엇을 보고 있는지 한 줄씩 찍는다.
 *
 * ★ 손님이 한 말 (2026-09-02)
 *
 *   "분석할 때는 심도있게 분석하는 중, 풍운도령이든 다른 캐릭터든
 *   사주 유심히 관찰하는 중, 사주를 풀이하는 중 이런 식으로 텀을 들여.
 *   너무 빨라. 나오는 속도가 기대감도 어느 정도 줘야지."
 *
 * ★ 없는 일을 하는 척은 안 합니다
 *
 *   이 집은 근거 대는 집입니다. 그런데 여기서의 뜸은 **진짜**입니다 —
 *   이 사이에 서버가 명식을 다시 읽고, 대운을 세고, 그 캐릭터 몫의
 *   관점 컷을 짓습니다. a6 의 계산 장면과 같은 자리입니다.
 *
 *   그래서 줄도 **실제로 보는 자리**를 적습니다. "심도 있게 분석" 같은
 *   말은 아무것도 안 가리키지만 "월지와 일지를 견주는 중" 은 그 컷의
 *   근거 줄에 그대로 적혀 나옵니다. 손님이 나중에 대 볼 수 있습니다.
 *
 * ★ 서버가 빨라도 지우지 않습니다
 *
 *   a6 이 이미 그렇게 합니다 — "여기서의 기다림은 비용이 아니라
 *   값입니다." 다만 **건너뛰는 길**은 반드시 냅니다. 두 번째 오는
 *   사람에게 같은 뜸은 지연입니다.
 */

import { useEffect, useState } from "react";

/** 한 줄이 서 있는 시간. 너무 길면 답답하고 너무 짧으면 못 읽습니다. */
const BEAT_MS = 760;

export default function Thinking({
  who,
  lines,
  onSkip,
}: {
  /** 누가 보고 있는가. 첫 줄에 이름을 세웁니다. */
  who?: string;
  lines: string[];
  /** 건너뛰기. 없으면 버튼을 안 답니다 (아직 도착 안 한 자리). */
  onSkip?: () => void;
}) {
  const [at, setAt] = useState(0);

  useEffect(() => {
    if (at >= lines.length) return;
    const t = setTimeout(() => setAt((n) => n + 1), at === 0 ? 260 : BEAT_MS);
    return () => clearTimeout(t);
  }, [at, lines.length]);

  /*
   * 못 움직이는 손님에게는 뜸이 그냥 빈 화면입니다. 줄을 한 번에
   * 다 보여 줍니다 — 읽을 것이 있는 편이 낫습니다.
   */
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    setReduced(
      !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
    );
  }, []);
  const shown = reduced ? lines : lines.slice(0, at);

  return (
    <>
      <div className="calcrun think" aria-live="polite">
        {who && <p className="whoIs">{who}가 보고 있소.</p>}
        {shown.map((l, i) => (
          <p key={i} className={!reduced && i === at - 1 ? "on" : undefined}>
            {l}
            {!reduced && i === at - 1 && (
              <span className="dots" aria-hidden>
                <i />
                <i />
                <i />
              </span>
            )}
          </p>
        ))}
      </div>
      {onSkip && (
        <button className="btn gh mt" onClick={onSkip}>
          다 됐습니다 · 건너뛰겠습니다
        </button>
      )}
    </>
  );
}
