"use client";

import React from "react";

import CharArt, { type Mood } from "@/components/CharArt";
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

/*
 * 한 덩이를 **마디로 가른다** — 줄바꿈(<br />)이 마디의 경계입니다.
 *
 * ★ 왜 (2026-09-03)
 *
 *   손님이 a5 에서 멈췄습니다. 도령의 말이 **열세 줄짜리 말풍선 하나**
 *   였습니다. 재보니 마흔둘 중 스물넷이 문턱을 넘었고, 가장 긴 것은
 *   **1,160자 · 26문장**이었습니다 (tools/say_length.py).
 *
 *       "말이 너무 길어, 적당하면서도 임팩트있게, 그리고 대화형식으로
 *        글이 띄어져야할거아냐 자연스럽게"
 *
 *   글은 이미 마디로 쓰여 있었습니다 — `<br />` 로 세 번 끊어 두었죠.
 *   **화면이 그걸 무시하고 한 상자에 부었을 뿐입니다.** 그러니 글을
 *   다시 쓸 일이 아니라 끊어 둔 대로 놓아 주면 됩니다.
 *
 *   대화는 주고받는 것이라, 한 마디씩 놓여야 사람이 말하는 것으로
 *   읽힙니다. 한 상자에 부으면 연설이고, 손님은 읽는 게 아니라 훑습니다.
 *
 * ★ 얼굴은 **첫 마디에만**. 같은 사람이 이어 말하는 것이라, 마디마다
 *   얼굴을 붙이면 스무 명이 번갈아 말하는 것처럼 보입니다.
 */
function beats(children: React.ReactNode): React.ReactNode[][] {
  const out: React.ReactNode[][] = [[]];
  for (const node of React.Children.toArray(children)) {
    if (React.isValidElement(node) && node.type === "br") {
      if (out[out.length - 1].length) out.push([]);
      continue;
    }
    out[out.length - 1].push(node);
  }
  return out.filter((b) => b.some(
    (n) => typeof n !== "string" || n.trim() !== ""));
}

/** html 로 받은 글도 같은 자리에서 가릅니다. */
function htmlBeats(html: string): string[] {
  return html.split(/<br\s*\/?>/i)
             .map((t) => t.trim())
             .filter((t) => t && t !== "&nbsp;");
}

export function Say({ who, children, html, lens, mood }: {
  who: string; children?: React.ReactNode; html?: string;
  /** 말하는 사람. 없으면 지금 고른 캐릭터. */
  lens?: string;
  /** 어떤 얼굴로 말하는가 — 짚는 말인가, 누그러뜨리는 말인가. */
  mood?: Mood;
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
  const parts: React.ReactNode[] = html
    ? htmlBeats(html).map((t, i) => (
        <span key={i} dangerouslySetInnerHTML={{ __html: t }} />))
    : beats(children).map((b, i) => <span key={i}>{b}</span>);
  // 마디가 없으면(빈 대사) 예전처럼 한 덩이로 둡니다.
  const rows = parts.length ? parts : [html ? null : children];

  return (
    <>
      {rows.map((body, i) => (
        <div className={"say" + (i ? " cont" : "")} key={i}>
          {/* 얼굴과 이름은 첫 마디에만 — 이어 말하는 것이니까. */}
          {i === 0 && l && (
            <span className="sayface">
              <CharArt lens={l} size="talk" mood={mood} />
            </span>
          )}
          <span className="saybody">
            {i === 0 && <small>{who}</small>}
            {body}
          </span>
        </div>
      ))}
    </>
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
