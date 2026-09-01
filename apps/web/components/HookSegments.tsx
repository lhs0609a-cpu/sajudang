"use client";

/**
 * 훅 5단 — 한 단씩 열리고, 응답하면 다음이 열린다.
 *
 * ★ html 은 서버가 렌더한 것입니다. 여기서 문장을 만들지 않습니다.
 * ★ 공감률은 서버가 shown=true 를 줄 때만 그립니다. 100건 미만이면 안 그립니다.
 */
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Say } from "@/components/Narration";
import CharArt from "@/components/CharArt";
import { LENS_BY_ID } from "@/lib/lenses";
import { speakRemote } from "@/lib/sound";
import { track } from "@/lib/track";
import type { HookSegment } from "@shared/chart";

function Agreement({ statementId }: { statementId: string }) {
  const [data, setData] = useState<
    { shown: boolean; rate?: number; total?: number; seen?: number } | null>(null);
  useEffect(() => {
    let alive = true;
    api.agreement(statementId).then((d) => alive && setData(d)).catch(() => {});
    return () => { alive = false; };
  }, [statementId]);

  if (!data) return null;

  // 응답 100건 미만 → 공감률은 안 그립니다 (숫자를 지어내지 않습니다).
  //
  // ★ 다만 그 자리를 **비워 두지도** 않습니다. 전에는 사회적 증거가
  //   0인 채로 결제 갈림길까지 갔습니다. 몇 번 나갔는지는 지어내지
  //   않고 낼 수 있습니다 — 정확도 주장이 아니라 사실 진술입니다.
  //   0이면 아무것도 안 그립니다.
  if (!data.shown || data.rate == null) {
    if (!data.seen) return null;
    return (
      <div className="agr seen">
        <span className="dot" />
        <span>이 문장을 <b>{data.seen.toLocaleString()}명</b>이 받아 갔소</span>
      </div>
    );
  }
  return (
    <div className="agr">
      <span>이 문장에</span>
      <div className="bar"><i style={{ ["--w" as string]: `${data.rate}%` }} /></div>
      <b>{data.rate}%</b>
      <span>가 &quot;그렇다&quot; · {data.total?.toLocaleString()}명</span>
    </div>
  );
}

export default function HookSegments({
  segments, chartId, lensId, concern, charName, onMiss, onDone,
}: {
  segments: HookSegment[];
  chartId: string;
  lensId: string;
  concern: string;
  charName: string;
  /** 「아니오」가 몇 번 나왔는지 알린다. 부모가 훅을 다시 받아 온다. */
  onMiss?: (misses: number) => void;
  onDone?: () => void;
}) {
  const [open, setOpen] = useState(1);
  const [replies, setReplies] = useState<Record<number, string>>({});
  const [misses, setMisses] = useState(0);

  /*
   * 몇 단까지 열렸는지 남깁니다. 초반이 어디서 끊기는지 여기가 답합니다.
   * 훅 첫 단이 안 꽂히면 두 번째를 안 누릅니다 — 그걸 숫자로 봐야
   * 문장을 고칠지 순서를 고칠지 정할 수 있습니다.
   */
  useEffect(() => {
    const i = Math.min(open, segments.length) - 1;
    if (i >= 0) track("hook_shown", "a7", { stage: i });
  }, [open, segments.length]);

  /*
   * yes=true 그렇소 · yes=false 아니오 · yes=null **글쎄올시다**
   *
   * ★ 이분법이 두 가지를 망가뜨리고 있었습니다.
   *   ① 애매한 사람이 **거짓 '그렇소'** 를 눌러 공감률을 오염시켰습니다.
   *   ② 답을 안 하면 다음 단이 안 열려서, 판단을 미루고 싶은 손님이나
   *      스크롤로 훑고 싶은 손님에게는 **막다른 화면**이었습니다.
   *      그 자리가 훅의 첫 단이면 그대로 이탈입니다.
   *
   *   중립은 서버가 **노출로만** 셉니다 (answer 를 안 보냅니다).
   */
  /*
   * 새로 열린 마디를 읽어 준다.
   *
   * 훅은 사람마다 문장이 달라 미리 만들어 둘 수 없습니다. 서버가 그때
   * 만들어 곳간에 두므로, 같은 말은 두 번 안 만듭니다.
   */
  const [said, setSaid] = useState(0);
  useEffect(() => {
    if (open <= said) return;
    const seg = segments[open - 1];
    setSaid(open);
    if (seg?.statement_id && seg.html) {
      void speakRemote(() => api.voice({
        kind: "hook", statement_id: seg.statement_id!, html: seg.html,
      }));
    }
  }, [open, said, segments]);

  const vote = async (i: number, yes: boolean | null) => {
    track("hook_answer", "a7", { stage: i, yes: yes === null ? 2 : yes ? 1 : 0 });
    const seg = segments[i];
    const say = yes === null
      ? "그럴 수 있소. 판단은 미뤄 두고 계속 보시오."
      : yes ? seg.yes : seg.no;
    setReplies((r) => ({ ...r, [i]: say }));

    if (yes === false) {
      const n = misses + 1;
      setMisses(n);
      onMiss?.(n);
    }
    try {
      await api.feedback({
        statement_id: seg.statement_id, chart_id: chartId,
        answer: yes === null ? null : yes ? 1 : 0,
        stage: seg.stage, lens_id: lensId, concern,
      });
    } catch {
      /* 기록 실패가 읽기를 막아서는 안 된다 */
    }
    setTimeout(() => {
      setOpen((n) => Math.max(n, i + 2));
      if (i + 1 >= segments.length) onDone?.();
    }, 660);
  };

  const lens = LENS_BY_ID[lensId];

  return (
    <>
      {/*
        ★ 새로 열린 마디만 읽어 줍니다.
          이미 읽은 마디를 다시 읽으면 손님이 아래로 내릴 때마다
          도령이 처음부터 다시 말합니다. 그리고 소리가 꺼져 있으면
          **청하지도** 않습니다 — 만드는 데 값이 나가는 자리입니다.
      */}
      {segments.slice(0, open).map((seg, i) => (
        <div className="blk in" key={seg.statement_id}>
          {/* ★ 몇 번째 마디인지. 0단은 label 이 비어 있어서 손님이
              어디쯤 왔는지 알 길이 없었습니다. */}
          {/*
            ★ 마디마다 그 사람의 얼굴을 답니다.

              0단은 아픈 데를 찌르는 자리라 **짚는 얼굴**로 나갑니다.
              말만 세고 얼굴이 평온하면 그 말이 안 꽂힙니다.
              마지막 단은 마무리라 누그러뜨립니다.
          */}
          {lens && <span className="hookface">
            <CharArt lens={lens} size="talk"
                     mood={i === 0 ? "cut"
                           : i >= segments.length - 1 ? "soft" : "base"} />
          </span>}
          <div className="stepno">{i + 1} / {segments.length}</div>
          {seg.label && <div className="lab">{seg.label}</div>}
          {/*
            ★ 0단만 근거가 본문 **아래**로 갑니다 (seg.source_below).
              전에는 0단에 근거가 아예 없었습니다 — 손님이 이 집에서
              처음 읽는 문장이 하필 근거 없는 문장이라, "근거 대는 집"
              이라는 자리가 가장 센 첫 문장에서 사라졌습니다.
              그렇다고 찌르기 **위**에 놓으면 첫 문장이 강의가 됩니다.
              그래서 자리만 옮깁니다: 찌르고, 그 아래에 무엇을 보고 한
              말인지 적습니다.
          */}
          {seg.source && !seg.source_below && (
            <span className="src">근거 · {seg.source}</span>
          )}
          <div dangerouslySetInnerHTML={{ __html: seg.html }} />
          {seg.source && seg.source_below && (
            <span className="src below">근거 · {seg.source}</span>
          )}
          {/* ★ 조건을 source 가 아니라 statement_id 로 바꿉니다.
              source 로 걸어 두면, 근거가 없는 단은 응답이 100건 쌓여도
              공감률이 **영영** 안 붙습니다. 실제로 0단이 그랬습니다. */}
          {seg.statement_id && <Agreement statementId={seg.statement_id} />}

          {replies[i] === undefined ? (
            <>
              <div className="vt">
                <button onClick={() => vote(i, true)}>그렇소</button>
                <button onClick={() => vote(i, false)}>아니오</button>
              </div>
              {/* ★ 세 번째 길. 이게 없어서 애매한 사람이 거짓 '그렇소' 를
                  눌렀고, 아무것도 안 누르면 다음 단이 안 열렸습니다. */}
              <button className="lk vt3" onClick={() => vote(i, null)}>
                글쎄올시다 · 그냥 계속 듣겠소
              </button>
            </>
          ) : (
            <div className="react on">
              {/*
                ★ 여기가 얼굴이 없던 자리입니다.

                  `<div className="say">` 를 직접 그리고 있어서, 얼굴을
                  다는 `<Say>` 를 안 거쳤습니다. 그래서 **훅에만** 얼굴이
                  없었습니다 — 손님이 「그렇소/아니오」를 다섯 번 누르며
                  가장 오래 머무는 자리이고, 결제 갈림길 바로 앞입니다.

                  표정도 갈립니다. 그렇다 하면 짚는 얼굴(cut), 아니라
                  하면 물러서는 얼굴(soft)입니다. 세 번 아니라 했는데
                  같은 얼굴로 계속 짚으면 그때 손님은 이게 녹음이라는
                  걸 압니다.
              */}
              <Say who={charName}
                   mood={replies[i] && seg.no === replies[i] ? "soft" : "cut"}>
                {replies[i]}
              </Say>
            </div>
          )}
        </div>
      ))}
    </>
  );
}
