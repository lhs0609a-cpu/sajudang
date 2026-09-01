"use client";

/** 나레이션·대사·근거칩 — 참조 구현체의 nr() / say() / .src 를 옮긴 것. */
export function Narration({ lines }: { lines: string[] }) {
  /*
   * ★ 줄 간격 0.72초는 너무 느렸습니다. 그리고 이건 **이 블록 안에서만**
   *   먹혀서, 대사·버튼은 첫 줄과 같이 한꺼번에 떴습니다. 화면 전체가
   *   대화처럼 이어지려면 순서가 화면 단위여야 합니다 —
   *   Shell 이 화면에 놓인 순서대로 다시 매깁니다(BEAT).
   *   여기 값은 그 전에 보이는 한 프레임과, 스크립트가 안 돌 때의 몫입니다.
   */
  let delay = 0;
  return (
    <div className="nr">
      {lines.map((l, i) => {
        if (l === "") return <span className="ps" key={i} />;
        const style = { animationDelay: `${delay}s` };
        delay += 0.2;
        return <span className="l" style={style} key={i}
                     dangerouslySetInnerHTML={{ __html: l }} />;
      })}
    </div>
  );
}

export function Say({ who, children, html }: {
  who: string; children?: React.ReactNode; html?: string;
}) {
  return (
    <div className="say">
      <small>{who}</small>
      {html ? <span dangerouslySetInnerHTML={{ __html: html }} /> : children}
    </div>
  );
}

/** 근거 칩 — 보조 정보. 필수 정보를 여기 두지 말 것. (docs/09 §7) */
export function Source({ children }: { children: React.ReactNode }) {
  return <span className="src">근거 · {children}</span>;
}

export function Progress({ step, total }: { step: number; total: number }) {
  return (
    <div className="prog">
      {Array.from({ length: total }, (_, i) => (
        <i key={i} className={i < step ? "d" : undefined} />
      ))}
    </div>
  );
}
