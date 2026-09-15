"use client";

/**
 * 확인 문항 — 리포트 앞에 묻는 행동 물음 여섯. (engine/probe.py · 2026-09-11)
 *
 * ★ 왜 묻나
 *   날카로운 풀이는 사주만으로 안 나옵니다. 「돈 되는 걸 보면 먼저 무엇을
 *   하오」 같은 **실제로 하는 일**이 있어야, 여덟 글자가 가리키는 쪽과
 *   맞대어 「같다 · 다르다」 를 말할 수 있습니다.
 *
 * ★ 고를 것만 냅니다. 자유 입력은 안 받습니다 — 개인정보가 섞이고
 *   가드를 우회합니다. 물음도 보기도 서버가 정합니다(`rep.probes`).
 *   판정 규칙은 안 내려옵니다 — 그건 분기표입니다.
 *
 * ★ 저장하지 않습니다. 요청에 실어 보내고 그걸로 끝입니다.
 *
 * ★ 다 답하지 않아도 보냅니다. 답한 물음만 맞댑니다. 건너뛰는 길도
 *   늘 있습니다 — 막다른 칸을 만들지 않습니다.
 *
 * ★ 버튼은 손님의 말(합쇼체)로 적습니다. (.\dev.ps1 buttons)
 */
import { useState } from "react";

export type ProbeSpec = {
  id: string;
  title: string;
  why: string;
  items: { id: string; q: string; options: { id: string; label: string }[] }[];
};

export default function ProbeAsk({
  spec, onSubmit, onSkip, busy,
}: {
  spec: ProbeSpec;
  onSubmit: (extras: Record<string, unknown>) => void;
  onSkip?: () => void;
  busy?: boolean;
}) {
  const [picks, setPicks] = useState<Record<string, string>>({});
  const n = Object.keys(picks).length;

  return (
    <section className="extraask noprint">
      <p className="ttl">{spec.title}</p>
      <p className="why" dangerouslySetInnerHTML={{ __html: spec.why }} />

      {spec.items.map((it) => (
        <div key={it.id}>
          <p className="q">{it.q}</p>
          <div className="og c2">
            {it.options.map((o) => (
              <button key={o.id}
                      className={`op ${picks[it.id] === o.id ? "on" : ""}`}
                      aria-pressed={picks[it.id] === o.id}
                      onClick={() => setPicks((p) => ({ ...p, [it.id]: o.id }))}>
                <b>{o.label}</b>
              </button>
            ))}
          </div>
        </div>
      ))}

      <button className="go" disabled={n === 0 || busy}
              onClick={() => onSubmit({ probe: { answers: picks } })}>
        {busy ? "맞대 보는 중입니다"
              : n < spec.items.length
                ? `고른 ${n}가지로 보겠습니다`
                : "이걸로 보겠습니다"}
      </button>
      <button className="lk" disabled={busy} onClick={() => onSkip?.()}>
        잘 모르겠습니다 · 건너뛰겠습니다
      </button>
    </section>
  );
}
