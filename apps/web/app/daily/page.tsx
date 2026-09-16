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
import RestHere from "@/components/RestHere";
import Scene from "@/components/scene/Scene";
import ActOut from "@/components/ActOut";
import { Narration, Say } from "@/components/Narration";
import { api } from "@/lib/api";
import { useSession } from "@/lib/store";
import { useScreen } from "@/lib/track";
import type { DailyResponse } from "@shared/chart";
import ServerText from "@/components/ServerText";

const VISIT_WARN_AT = 3;

export default function DailyPage() {
  useScreen("daily");
  const router = useRouter();
  const s = useSession();
  const [data, setData] = useState<DailyResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);

  /*
   * ★ 방문 세기를 걷었습니다 (2026-09-16).
   *
   *   여기서 세면 **스토어가 되살아나기 전**에 셉니다. `useEffect([])`
   *   가 잡는 `s.visitDate` 는 아직 `null` 이라, 매번 「오늘 처음」 이
   *   되어 `visits` 가 1 로 돌아갔습니다. 그래서 바로 아래 「하루 3회
   *   만류」 는 **여태 한 번도 뜬 적이 없습니다.** 브레이크를 달아
   *   두고 안 걸리게 해 둔 셈이오.
   *
   *   이제 처마(`Shell`)가 되살아난 뒤에 한 벌로 셉니다.
   */

  useEffect(() => {
    if (!s.chartId) return;
    let alive = true;
    api.daily(s.chartId, s.concern)
      .then((d) => alive && setData(d))
      .catch(() => alive && setErr("일진을 셈하지 못했소."));
    return () => { alive = false; };
  }, [s.chartId, s.concern, retry]);

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
      <header className="editorial-heading"><p className="conversion-kicker">오늘의 한 장</p><h1>오늘은 어떤 마음으로<br/>하루를 열겠소?</h1><p>오늘의 기운을 읽고, 작은 행동 하나를 골라보시오.</p></header>
      <Scene id="banner" />
      {/* ★ 여는 줄이 없어 첫 줄이 「일진이란…」 이라는 뜻풀이였습니다.
          매일 오는 자리라 더 그렇습니다 — 같은 설명을 매일 읽습니다. */}
      <Narration lines={["오늘 자 종이가 상 위에 새로 올라와 있다.",
                         "어제 것은 치워져 있었다."]} />
      {/* ★ 비유 40 · 겪은 일 0. 매일 오는 자리라 같은 설명을 매일
          읽습니다. 지나온 날을 짚는 한 줄을 답니다. */}
      <p className="sm">어제도 그제도 이 종이가 있었을 것이오. 오늘 것은 오늘만 맞소 — 날씨를 보는 것처럼, 옷을 고르는 데 쓰지 하루를 정하는 데 쓰지 않소.</p>
      {/*
        ★ 비유 63 · 팩폭 86 — 물러서는 말이 둘 섞여 있었고 셀 수 있는
          값이 넷뿐이었습니다. 일진은 **매일** 서는 것이라 수를 대야
          손님이 대 볼 수 있소 (1년 365일 중 걸리는 날만 냅니다).
      */}
      <p className="sm">일진은 하루에 <b>2글자</b>씩 서오. <b>1년</b>이면 <b>365</b>번 서고, 그중 그대 여덟 글자에 걸리는 날만 냅니다 — 달력에 압정을 꽂아 두는 셈이오.</p>
      {/*
        ★ 72점이던 자리. 비유 0 · 겪은 일 없음 — 매일 오는 화면이라
          같은 뜻풀이를 매일 읽게 됩니다. 오늘 것이 어제와 **무엇이
          다른지**를 그림으로 한 줄 답니다.
      */}
      <Say who="도령" lens="pungun">
        입력한 명식은 그대로 두고, 오늘 자 두 글자만 그 위에 얹는 것이오.
        <br />
        오늘의 두 글자가 입력한 명식과 어떻게 놓이는지 전통 해석으로 살펴보오.
        오늘 일어날 사건이나 하루의 좋고 나쁨을 확정하는 결과는 아니오.
        <br />
        날마다 다른 손님이 상에 앉는 것처럼, 두 글자가 매일 바뀌오.
        같은 짝은 60일 뒤에나 돌아오오 — 예순 칸짜리 수레바퀴가 한
        바퀴 도는 것과 같소.
      </Say>
      {/*
        ★ 「일진」이 무엇인지 아무 데도 안 적혀 있었소.
          그리고 「그날의 기운」 은 모르는 말을 **뜬 말로** 바꾼 것이라
          아직 그림이 안 그려집니다. 세는 것으로 바꿔 적습니다.
      */}
      <p className="lede8">
        일진 (그날에 새로 서는 두 글자) 이오. 날마다 <b>두 글자가 다</b>
        바뀌고, <b>예순 날</b>만에 같은 짝이 돌아오오. 그 둘이 그대의
        명식과 어디서 맞물리는지 보오.
      </p>
      {err && <><Say who="도령" lens="pungun">{err}</Say><button className="btn" onClick={() => {setErr(null);setRetry(n => n + 1);}}>일진 다시 불러오기</button></>}

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
      {/* 만류 곁에 **도움 받을 곳**을 둡니다. 여기까지 온 사람은
          이미 여러 번 온 사람이오 (2026-09-16). */}
      <RestHere visits={s.visits} hour={new Date().getHours()}
                concern={s.concern} returning={s.visits > 1} />

      {data && (
        <>
          <div className="dz">
            <div className="k">{data.date}</div>
            <p style={{ fontFamily: "var(--serif)", fontSize: 26, color: "var(--c)" }}>
              {data.gz}
            </p>
            <p className="sm">{data.relation} 날</p>
          </div>
          <ServerText className="src" html={`근거 · ${data.source}`} />
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
            {/* ★ 오늘의 줄에도 엔진이 굵은 글씨를 답니다 —
                「돈이 <b>나가는 쪽</b>으로 도는 날이오」. 글자로 꽂으면
                꺾쇠가 그대로 보입니다 (2026-09-15). */}
            {data.lines.map((l, i) => (
              <ServerText as="p" key={i} html={l} />
            ))}
          </Say>
          {data.notes.map((n) => <ServerText as="p" className="sm" key={n} html={`· ${n}`} />)}
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
          **틀린 말이었소.** 일진은 천간과 지지가 함께 한 칸씩
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
