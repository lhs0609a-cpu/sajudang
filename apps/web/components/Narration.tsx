"use client";

/** 나레이션·대사·근거칩 — 참조 구현체의 nr() / say() / .src 를 옮긴 것. */
export function Narration({ lines }: { lines: string[] }) {
  let delay = 0;
  return (
    <div className="nr">
      {lines.map((l, i) => {
        if (l === "") return <span className="ps" key={i} />;
        const style = { animationDelay: `${delay}s` };
        delay += 0.72;   // docs/09 §6 — 나레이션 줄 간격 0.7s
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
