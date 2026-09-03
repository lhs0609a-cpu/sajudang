"use client";

/**
 * @screen h1
 * H · 이어지다 — h1 릴레이
 *
 * ★ 브레이크 (CLAUDE.md 절대 규칙 4)
 *     세션당 릴레이 2명 — **서버가 판정합니다.** 화면에서 우회하지 마세요.
 *     거절한 캐릭터는 다시 권하지 않습니다.
 *     무거운 자리 다음에는 무료 캐릭터를 강제로 앞에 붙입니다.
 * ★ 근거를 반드시 함께 보여줍니다. 강매로 읽히지 않게. (docs/08 §3)
 */
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Shell from "@/components/Shell";
import Scene from "@/components/scene/Scene";
import CharArt from "@/components/CharArt";
import ActOut from "@/components/ActOut";
import { Narration, Say } from "@/components/Narration";
import { api } from "@/lib/api";
import { LENS_BY_ID } from "@/lib/lenses";
import { useSession } from "@/lib/store";
import { useScreen } from "@/lib/track";
import type { RelayResponse } from "@shared/chart";

export default function RelayPage() {
  useScreen("relay");
  const router = useRouter();
  const s = useSession();
  const [data, setData] = useState<RelayResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const chartId = s.chartId;
  const sessionId = s.sessionId;
  const read = s.read;
  const skipped = s.skipped;
  const cur = s.cur;

  const load = useCallback(() => {
    if (!chartId) return;
    api
      .relay({
        chart_id: chartId, session_id: sessionId,
        read, skipped, last_lens: cur,
      })
      .then(setData)
      .catch(() => setErr("이을 자리를 찾지 못했소."));
  }, [chartId, sessionId, read, skipped, cur]);

  useEffect(() => { load(); }, [load]);

  const go = async (lensId: string) => {
    // 브레이크 카운터는 서버가 셉니다.
    // 이 호출을 빠뜨리면 세션 2명 제한이 헐거워집니다.
    const r = await api.consumeRelay(sessionId);
    s.set({ cur: lensId, relayUsed: r.used });
    s.markRead(lensId);
    router.push("/report/" + lensId);
  };

  if (!chartId) {
    return (
      <Shell screen="h1" title="이어지다">
        <Narration lines={["먼저 글자를 세워야 하오."]} />
        <button className="btn mt" onClick={() => router.push("/")}>내 사주부터 보겠습니다</button>
      </Shell>
    );
  }

  return (
    <Shell screen="h1" title="이어지다" legal>
      <Scene id="handle" />
      {/*
        ★ 콜드 오픈이 없었습니다. 화면이 목록부터 시작해서, 손님은
          여기가 무슨 자리인지 모른 채 이름 넷을 봅니다.
      */}
      <Narration lines={["도령이 문고리를 놓았다.",
                         "옆방에서 인기척이 났다."]} />
      {/*
        ★ 여기가 여섯째로 낮았습니다 (연출 55).

          문고리 두 줄 다음에 곧바로 이름 카드가 나왔습니다. 왜 이
          사람이 불려 나왔는지는 카드마다 근거 줄이 들고 있는데,
          **여기가 무슨 자리인지**는 아무도 말하지 않았습니다.
          울림 20 · 팩폭 37 이 거기서 나왔습니다.

          이어 붙이는 자리라 파는 말이 되기 쉽습니다. 그래서 여는
          말에 **브레이크를 먼저** 답니다 — 한 자리에 2명, 오늘은
          거기까지. 거절한 사람은 다시 안 부른다는 것까지 적습니다.
      */}
      <Say who="도령" lens="pungun">
        그대의 여덟 글자는 아까 그대로요. 바뀐 건 <b>다음에 누가
        읽느냐</b>뿐이오.
        <br />
        옆방에서 나온 이름은 내가 고른 게 아니오. 그대의 글자가
        걸린 자리를 세어 보니 그 사람들이 남은 것이오. 카드마다
        근거 줄을 달아 두었으니 대 보시오 — 못 대면 안 들으셔도 되오.
        <br />
        <b>여기서 그만 일어서고 싶은 마음이 여태 몇 번 들었소.</b>
        {" "}이만하면 됐다 싶다가도, 하나만 더 들으면 뭔가 풀릴 것
        같아 자리를 못 뜨고 미뤄 둔 것이오.
          <br /> 그러다 지치는 사람을
        여럿 봤소. 그 마음을 알고 하는
        말이라 <b>한 자리에서 이을 수 있는 건 2명까지</b>로 잘라
        두었소. 그 뒤로는 내가 문을 닫소.
        <br />
        지나친 사람은 다시 안 권하오. 한 번 접은 부채를 자꾸
        펴 보이는 것처럼 굴지는 않겠소. 상 위에 남은 이름은
        접시에 덜어 놓은 것같이 그대로 두오.
      </Say>
      <span className="src">
        근거 · 규칙 20개를 이 명식에 대 보고 남은 사람들이오 ·
        한 자리 2명 · 무거운 자리 뒤에는 값 없는 사람이 먼저 서오
      </span>
      {err && <Say who="도령" lens="pungun">{err}</Say>}

      {data?.blocked ? (
        <div className="warn">
          <p>{data.block_reason}</p>
          <p className="sm">
            한 자리에서 여러 사람을 몰아 듣는다고 더 알게 되지 않소.
            오늘 들은 것을 먼저 두고 보시오.
          </p>
          <button className="btn gh mt" onClick={() => router.push("/lobby")}>진열대로</button>
        </div>
      ) : (
        <>
          {/* 정서 안전망 — 무거운 자리 다음엔 무료 캐릭터가 먼저 */}
          {data?.forced.map((id) => {
            const l = LENS_BY_ID[id];
            return (
              <div className="dz face" key={id} style={{ borderColor: "var(--teal)" }}>
                <div className="k">값 없이</div>
                {/* ★ 얼굴이 없었습니다 (2026-09-02). 이 집이 파는 것은
                    해석이 아니라 **그 사람**인데, 이어 붙이는 자리에
                    이름과 값만 있었습니다. */}
                <div className="dzhead">
                  {l && <CharArt lens={l} size="card" />}
                  <div>
                    <p style={{ fontFamily: "var(--serif)", fontSize: 18,
                                color: l?.color }}>
                      {l?.name}
                    </p>
                    {l && (
                      <span className="topics">
                        {l.topics.split(" · ").map((t) => <i key={t}>{t}</i>)}
                      </span>
                    )}
                  </div>
                </div>
                <p className="sm">{l?.quote}</p>
                <button className="btn gh mt" onClick={() => void go(id)}>
                  차 한 잔 하고 가겠습니다
                </button>
              </div>
            );
          })}

          {data && data.recommend.length > 0 ? (
            <>
              <Narration lines={["도령이 옆자리를 가리켰다."]} />
              {data.recommend.map((r) => {
                const l = LENS_BY_ID[r.lens_id];
                return (
                  <div className="dz face" key={r.lens_id}>
                    {/* ★ 얼굴을 붙입니다. 이름·근거·값만으로는 스무 명이
                        서로 구별되지 않습니다. 그림이 없으면 그 사람의
                        색과 한자로 자리만 잡습니다 (CharArt). */}
                    <div className="dzhead">
                      {l && <CharArt lens={l} size="card" />}
                      <div>
                        <p style={{ fontFamily: "var(--serif)", fontSize: 18,
                                    color: l?.color }}>
                          {r.name}
                        </p>
                        {l && (
                          <span className="topics">
                            {l.topics.split(" · ").map((t) => <i key={t}>{t}</i>)}
                          </span>
                        )}
                      </div>
                    </div>
                    <span className="src">근거 · {r.reason}</span>
                    {r.quote && (
                      <Say who={r.name} lens={r.lens_id}>{r.quote}</Say>
                    )}
                    <div className="og c2 mt">
                      <button
                        className="op"
                        disabled={!r.released}
                        onClick={() => void go(r.lens_id)}
                      >
                        <b>{r.released ? "듣겠습니다" : "아직 자리에 없습니다"}</b>
                        {/* ★ 여기 보이는 값이 그대로 청구됩니다.
                            전에는 카드가 캐릭터 값을 보여 주고 결제는
                            티어 값을 물려, 스무 캐릭터의 값이 한 번도
                            청구되지 않았습니다. (payments.price_of) */}
                        <span>
                          {r.price
                            ? `${r.price.toLocaleString()}원 · 이 자리 하나`
                            : "값 없이"}
                        </span>
                      </button>
                      {/*
                        ★ 레이블과 결과가 어긋나 있었습니다.
                          손님은 "나중에" 를 **유예**로 읽는데 시스템은
                          **영구 제외**로 처리했습니다. 작은 글씨로 적어
                          뒀지만, 나중에 후회할 종류의 비가역 선택입니다.
                          거절한 캐릭터를 재권유하지 않는 브레이크는 그대로
                          두고, 레이블을 결과에 맞춥니다.
                      */}
                      <button
                        className="op"
                        onClick={() => { s.markSkipped(r.lens_id); }}
                      >
                        <b>이 사람은 됐습니다</b>
                        <span>다시 권하지 않습니다</span>
                      </button>
                    </div>
                  </div>
                );
              })}
              <p className="sm mt">
                이번 자리에서 이을 수 있는 사람은 {data.breaks.per_session_relay}명까지요.
                지금까지 {s.relayUsed}명.
              </p>
              {/* ★ 유예하는 길을 따로 냅니다. 세션만 닫고 제외는 안 합니다 —
                  브레이크는 그대로면서 손님이 무엇을 고르는지 알게 됩니다. */}
              {/*
                ★ 당김 0점이던 자리입니다. 옆자리를 늘어놓고 끝났습니다.
                  브레이크(세션당 둘)는 그대로 두고, 그걸 **고를 이유**로
                  씁니다 — 지어낸 압박이 아니라 이미 있는 규칙입니다.
              */}
              <ActOut kind="딜레마" next="그 사람이 먼저 보는 자리">
                오늘 이을 수 있는 자리는{" "}
                <b>{Math.max(0, data.breaks.per_session_relay - s.relayUsed)}</b>이오.
                {" "}스물 중 <b>{s.read.length}</b>은 이미 들으셨소.
                <br />
                한 상에 열 그릇을 놓으면 맛을 못 보오.{" "}
                <b>한 사람을 끝까지 듣는 편이 낫소</b> — 그래서 하루에
                둘까지만 잇소.
              </ActOut>
              <button className="btn gh mt" onClick={() => router.push("/lobby")}>
                오늘은 그만 듣겠습니다
              </button>
            </>
          ) : (
            data && <Narration lines={["오늘 이을 자리는 없소."]} />
          )}
        </>
      )}

      <button className="btn gh mt" onClick={() => router.push("/lobby")}>진열대로</button>
    </Shell>
  );
}
