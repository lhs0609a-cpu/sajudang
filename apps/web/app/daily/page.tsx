"use client";

/**
 * @screen g1 g2 g3
 * G · 다시 오다 — g1 오늘의 운세 · g2 회고 · g3 차 한 잔
 *
 * ★ 하루 3회 넘게 오면 만류합니다. 브레이크는 매출보다 앞섭니다.
 *   (CLAUDE.md 절대 규칙 4)
 */
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Shell from "@/components/Shell";
import Scene from "@/components/scene/Scene";
import ActOut from "@/components/ActOut";
import { Narration, Say } from "@/components/Narration";
import { api } from "@/lib/api";
import { useSession } from "@/lib/store";
import { useScreen } from "@/lib/track";
import type { DailyResponse } from "@shared/chart";

const VISIT_WARN_AT = 3;

export default function DailyPage() {
  useScreen("daily");
  const router = useRouter();
  const s = useSession();
  const [data, setData] = useState<DailyResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    s.set({ visits: s.visits + 1 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!s.chartId) return;
    let alive = true;
    api.daily(s.chartId)
      .then((d) => alive && setData(d))
      .catch(() => alive && setErr("일진을 셈하지 못했소."));
    return () => { alive = false; };
  }, [s.chartId]);

  if (!s.chartId) {
    return (
      <Shell screen="g1" title="오늘의 일진">
        <Narration lines={["먼저 글자를 세워야 하오."]} />
        <button className="btn mt" onClick={() => router.push("/")}>내 사주부터 보겠습니다</button>
      </Shell>
    );
  }

  return (
    <Shell screen="g1" title="오늘의 일진">
      <Scene id="banner" />
      {/* ★ 여는 줄이 없어 첫 줄이 「일진이란…」 이라는 뜻풀이였습니다.
          매일 오는 자리라 더 그렇습니다 — 같은 설명을 매일 읽습니다. */}
      <Narration lines={["오늘 자 종이가 상 위에 새로 올라와 있다.",
                         "어제 것은 치워져 있었다."]} />
      {/*
        ★ 72점이던 자리. 비유 0 · 겪은 일 없음 — 매일 오는 화면이라
          같은 뜻풀이를 매일 읽게 됩니다. 오늘 것이 어제와 **무엇이
          다른지**를 그림으로 한 줄 답니다.
      */}
      <Say who="도령" lens="pungun">
        여덟 글자는 그대로 두고, 오늘 자 두 글자만 그 위에 얹는 것이오.
        <br />
        <b>여태 「오늘 왜 이렇게 안 풀리지」 싶은 날이 있었소.</b>
        {" "}그런 날 대개는 참고 넘겼을 것이오. 그 날짜를 여기 대 보면
        얹힌 글자가 무엇이었는지 보이오.
        <br />
        날마다 다른 손님이 상에 앉는 것처럼, 두 글자가 매일 바뀌오.
        같은 짝은 60일 뒤에나 돌아오오 — 예순 칸짜리 수레바퀴가 한
        바퀴 도는 것과 같소.
      </Say>
      {/*
        ★ 「일진」이 무엇인지 아무 데도 안 적혀 있었습니다.
          그리고 「그날의 기운」 은 모르는 말을 **뜬 말로** 바꾼 것이라
          아직 그림이 안 그려집니다. 세는 것으로 바꿔 적습니다.
      */}
      <p className="lede8">
        일진 (그날에 새로 서는 두 글자) 이오. 날마다 <b>두 글자가 다</b>
        바뀌고, <b>예순 날</b>만에 같은 짝이 돌아오오. 그 둘이 그대 여덟
        글자와 어디서 맞물리는지 보오.
      </p>
      {err && <Say who="도령" lens="pungun">{err}</Say>}

      {/* 하루 3회 접속 시 만류 — 늘리지 마세요 */}
      {s.visits >= VISIT_WARN_AT && (
        <div className="warn">
          <p>오늘 벌써 {s.visits}번째요.</p>
          <p className="sm">
            운은 하루에 여러 번 바뀌지 않소. 자꾸 들여다본다고 달라질 것도 아니오.
            오늘은 그만 보시고, 내일 오시오.
          </p>
        </div>
      )}

      {data && (
        <>
          <div className="dz">
            <div className="k">{data.date}</div>
            <p style={{ fontFamily: "var(--serif)", fontSize: 26, color: "var(--c)" }}>
              {data.gz}
            </p>
            <p className="sm">{data.relation} 날</p>
          </div>
          <span className="src">근거 · {data.source}</span>
          <div className="bar" style={{ margin: "12px 0" }}>
            <i style={{ ["--w" as string]: `${data.score}%` }} />
          </div>
          <p className="sm">오늘 기운 {data.score} / 100</p>

          {/*
            ★ 전에는 "적중률이 아니라 배치 점수요" 한 줄이었습니다.
              아닌 것만 말하고 무엇인지는 안 말하면, 손님에게 76은
              아무 뜻도 없는 수입니다. 여기는 근거 대는 집이니 방어가
              아니라 **셈법 공개**로 처리합니다. 무엇이 몇 점을 올리고
              내렸는지 서버가 그대로 내려보냅니다.
          */}
          <div className="scw">
            {data.score_why.map((w, i) => (
              <p key={i}>
                <b>{w.k}</b>
                <i>{w.v > 0 ? `+${w.v}` : w.v}</i>
                <span>{w.t}</span>
              </p>
            ))}
          </div>
          <p className="sm">{data.score_says}</p>
          {/* ★ 줄 단위로 그립니다. 관계·일간·신강약·계절·용신을 곱해 만든
              다섯 줄이라, 한 문단으로 뭉치면 읽히지 않습니다. */}
          <Say who="도령" lens="pungun">
            {data.lines.map((l, i) => (
              <p key={i} style={i ? { marginTop: 8 } : undefined}>{l}</p>
            ))}
          </Say>
          {data.notes.map((n) => <p className="sm" key={n}>· {n}</p>)}
          {/*
            ★ 어려운 말이 여섯 개 지나가는데 풀이가 한 줄도 없었습니다
              (쉬움 30점). 리포트 컷이 쓰는 상자를 그대로 답니다 —
              모르는 말을 만난 **그 자리**에 있어야 읽습니다.
          */}
          {data.terms_html && (
            <div dangerouslySetInnerHTML={{ __html: data.terms_html }} />
          )}
        </>
      )}

      {/* g2 회고 — statement_log 가 쌓이기 전에는 지어내지 않는다 */}
      <div className="lab mt">g2 · 되짚기</div>
      <p className="sm">
        여섯 달 전 그대가 &quot;그렇다&quot;고 한 문장을 여기 다시 꺼내오.
        아직 쌓인 것이 없어 비워 두었소.
      </p>

      {/* g3 차 한 잔 */}
      <div className="lab mt">g3 · 차 한 잔</div>
      <Scene id="tea" />
      <p className="sm">
        용신(모자란 것을 채워 줄 기운)에 맞는 차를 내오.
        리포트를 열면 함께 나오오.
      </p>

      {/*
        ★ 일진이 「오늘은 이렇소」로 끝났습니다. 매일 오는 자리라
          **왜 어제와 다른지**를 말해 줘야 내일도 옵니다.

        ★ 그런데 여기 적혀 있던 「내일은 글자가 하나 바뀌오」 는
          **틀린 말이었습니다.** 일진은 천간과 지지가 함께 한 칸씩
          갑니다 — 庚辰 다음은 辛巳라 두 글자가 다 바뀝니다. 같은 짝은
          예순 날 뒤에 돌아옵니다. 셈에서 나온 값으로 고쳤습니다.
      */}
      <ActOut kind="남긴 물음" next="스무 사람">
        오늘은 이렇소. <b>내일은 두 글자가 다 바뀌오.</b><br />
        같은 짝은 <b>예순 날</b> 뒤에나 돌아오오 — 같은 사람인데 날마다
        다른 까닭이 거기 있소.
      </ActOut>
      <button className="btn gh mt" onClick={() => router.push("/lobby")}>진열대로</button>
    </Shell>
  );
}
