"use client";

import CharArt from "@/components/CharArt";
import { LENS_BY_ID } from "@/lib/lenses";
import { useSession } from "@/lib/store";

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

export function Say({ who, children, html, lens }: {
  who: string; children?: React.ReactNode; html?: string;
  /** 말하는 사람. 없으면 지금 고른 캐릭터. */
  lens?: string;
}) {
  const cur = useSession((s) => s.cur);
  const l = LENS_BY_ID[lens ?? cur];

  /*
   * ★ 얼굴이 없었습니다.
   *
   *   「도령이 고개를 들었다」 「그대를 뭐라 적으면 되겠소?」 — 도령이
   *   내내 말을 하는데 화면에는 **배경과 글자뿐**이었습니다. 초상은
   *   진열대에서만 그리고 있었습니다.
   *
   *   이 서비스가 파는 것은 해석이 아니라 **그 사람**입니다. 스무 명이
   *   각자의 관점으로 본다는 것이 한 줄인데, 그 사람이 안 보이면
   *   손님에게는 그냥 글입니다. 값을 치를 이유가 얼굴에 있습니다.
   *
   *   자리표시라도 **자리는 잡아 둡니다.** 그래야 그림이 오는 날
   *   코드를 안 고치고 갈아 끼웁니다 — 지금까지는 갈아 끼울 자리조차
   *   없었습니다.
   */
  return (
    <div className="say">
      {l && <span className="sayface"><CharArt lens={l} size="talk" /></span>}
      <span className="saybody">
        <small>{who}</small>
        {html ? <span dangerouslySetInnerHTML={{ __html: html }} /> : children}
      </span>
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
