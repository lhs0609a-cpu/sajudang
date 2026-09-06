"use client";

/**
 * 물으신 자리가 묻는 것 — 고민 물음.
 *
 * ★ 캐릭터가 받는 것(ExtraAsk)과 **다른 자리**입니다.
 *   저건 그 사람을 고른 까닭이고, 이건 손님이 여섯 칸에서 고른
 *   자리가 묻는 것입니다 — 돈을 물었으면 돈이 어디서 오고 어디서
 *   새는지. (engine/topic.py · docs/20 §4-5)
 *
 * ★ 고를 것만 냅니다.
 *   자유 입력은 안 받습니다 — 개인정보가 섞이고 가드를 우회합니다.
 *   목록도 문장도 서버가 정합니다(`rep.asks`). 화면이 제 손으로
 *   물음을 적으면 엔진이 달라져도 이 줄만 안 바뀌어 또 어긋납니다.
 *
 * ★ 「모르겠소」는 답이 아니라 **노출**입니다.
 *   그렇소·아니오 둘만 두면 애매한 사람이 거짓 답을 눌러 공감률이
 *   오염되고, 아무것도 안 누르면 그 자리에서 나갑니다.
 *
 * ★ 저장하지 않습니다. 요청에 실어 보내고 그걸로 끝입니다.
 *
 * ★ 버튼은 **손님의 말**로 적습니다 (합쇼체). 집의 말투로 적으면
 *   손님은 그게 자기 말인 줄 모릅니다. (.\dev.ps1 buttons)
 */
import { useState } from "react";

export type TopicAskSpec = {
  id: string;
  title: string;
  q: string;
  options: { id: string; label: string }[];
  q2?: string;
  options2?: { id: string; label: string }[];
};

export default function TopicAsk({
  spec, onSubmit, busy,
}: {
  spec: TopicAskSpec;
  onSubmit: (extras: Record<string, unknown>) => void;
  busy?: boolean;
}) {
  const [pick, setPick] = useState<string | null>(null);
  const [pick2, setPick2] = useState<string | null>(null);

  /* 둘째 물음이 있으면 둘 다 고른 뒤에야 보냅니다 — 하나만 보내면
     반쪽 컷이 서고, 손님은 나머지를 물어본 적도 없다고 여깁니다. */
  const ready = !!pick && (!spec.options2 || !!pick2);

  return (
    <section className="extraask noprint">
      <p className="ttl">{spec.title}</p>
      <p className="why">
        고르신 것을 여덟 글자와 <b>맞대 봅니다</b>. 맞히려는 것이 아니라
        겹치는지 어긋나는지를 보는 것이오. 적으신 것은 남기지 않소.
      </p>

      <p className="q">{spec.q}</p>
      <div className="og c2">
        {spec.options.map((o) => (
          <button key={o.id}
                  className={`op ${pick === o.id ? "on" : ""}`}
                  aria-pressed={pick === o.id}
                  onClick={() => setPick(o.id)}>
            <b>{o.label}</b>
          </button>
        ))}
      </div>

      {spec.q2 && spec.options2 && (
        <>
          <p className="q">{spec.q2}</p>
          <div className="og c2">
            {spec.options2.map((o) => (
              <button key={o.id}
                      className={`op ${pick2 === o.id ? "on" : ""}`}
                      aria-pressed={pick2 === o.id}
                      onClick={() => setPick2(o.id)}>
                <b>{o.label}</b>
              </button>
            ))}
          </div>
        </>
      )}

      <button className="go" disabled={!ready || busy}
              onClick={() => onSubmit({
                topic: { choice: pick, ...(pick2 ? { choice2: pick2 } : {}) },
              })}>
        {busy ? "맞대 보는 중입니다" : "이걸로 보겠습니다"}
      </button>
    </section>
  );
}
