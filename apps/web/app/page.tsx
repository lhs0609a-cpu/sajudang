"use client";

/**
 * @screen a1 a2 a3 a4 a4b a5 a6 a7
 * A · 들어가다 — a1 골목 → a2 이름 → **a5 고민** → a3 날 → a4 때
 *                → a4b 성향 → a6 명식 → a7 훅 5단
 *
 * ★ 순서를 바꿨습니다.
 *   「무엇이 걸려서 예까지 왔소?」 는 이 흐름 전체에서 가장 좋은 한 줄인데
 *   손님은 그 앞에 이름·날짜·고을·성별·시각·넉 자 열여섯 칸을 지나야
 *   그걸 만났습니다. 그때쯤이면 이미 사무적인 모드입니다.
 *   마음을 먼저 정한 사람은 뒤이은 수고를 자기 결정과 맞추려 합니다.
 *   그래서 고민을 이름 바로 뒤로 올렸고, 그 뒤 화면들이 답을 되받습니다.
 *
 * 이탈 방어 (docs/08 §3)
 *   a2~a5 **건너뛰기를 뗐습니다.** 이 구간을 건너뛴 손님은 명식이 없어
 *         진열대에서 아무것도 못 봅니다 — 이탈로만 이어지는 버튼이었습니다.
 *   a4  "모르오" 를 **크게**. 여기서 막히면 그대로 이탈한다.
 *   a4b "모르오 · 사주만으로 보겠소" 를 그리드 **위**로 올렸다.
 *   a7  값을 아직 묻지 않는다. 무료 6단이 먼저다.
 *
 * ★ 계산은 서버(/v1/chart)가 합니다. 여기서 사주를 세지 않습니다.
 */
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Shell from "@/components/Shell";
import { useScreen } from "@/lib/track";
import { birthMessageFrom, birthProblem } from "@/lib/birth";
import Scene from "@/components/scene/Scene";
import { Narration, Progress, Say } from "@/components/Narration";
import { CalcPanel, ElementBar, Pillars, Summary } from "@/components/Chart";
import HookSegments from "@/components/HookSegments";
import Doubts from "@/components/Doubts";
import { api, ApiError } from "@/lib/api";
import { LENS_BY_ID } from "@/lib/lenses";
import { CONCERNS, seasonOf, useSession, type Concern } from "@/lib/store";
import { SEASON_PALETTE } from "@/components/scene/manifest";
import type { HookSegment } from "@shared/chart";

type Step = "a1" | "a2" | "a3" | "a4" | "a4b" | "a5" | "a6" | "a7";

/*
 * a1 오프닝.
 *
 * ★ 비트가 셋이었습니다. 그 셋을 다 눌러야 이름 칸이 나왔고, 그 사이에
 *   **여기서 무엇을 얻는지가 한 줄도 없었습니다.** 방문자가 머물지 말지
 *   정하는 데 쓰는 시간은 그보다 짧습니다. 분위기에 그 예산을 다 쓰면
 *   약속할 자리가 안 남습니다.
 *
 *   그래서 비트를 **하나로** 줄이고, 남은 자리에 결과를 약속하는 줄을
 *   박았습니다. 계절 문장은 버리지 않고 한 비트로 합쳤습니다.
 */
const OPENING: Record<string, string[]> = {
  spring: ["담장 위로 벚꽃이 넘어와 있었다.", "돌바닥에 꽃잎이 깔렸고,", "대문은 열려 있었다."],
  summer: ["비가 막 그친 밤이었다.", "물 고인 돌바닥에 불빛이 흔들리고,", "대문은 열려 있었다."],
  autumn: ["국화 냄새가 났다.", "마당에 낙엽이 쌓였고,", "대문은 열려 있었다."],
  winter: ["눈이 소리 없이 내리고 있었다.", "댓돌 위에 신발이 없는데,", "문은 열려 있었다."],
};

/*
 * 결과 약속 한 줄. 값을 언제 묻는지까지 여기서 말합니다 —
 * "결국 돈 내라는 거 아니냐" 가 첫 화면에서 가장 큰 의심입니다.
 */
const PROMISE =
  "여덟 글자를 세우고, <b>무엇을 보고 한 말인지</b>까지 적어 드리오.<br>" +
  "맞힌다고는 안 하오. 값은 나중에 묻소.";

/*
 * 때 — 네 시간짜리 여섯 칸.
 *
 * ★ 이 칸이 시주를 바꿔 놓고 있었습니다.
 *   각 칸이 한 시각으로 뭉개져서, 07:50 에 태어난 사람이 "아침" 을
 *   고르면 09:00 으로 기록되고 **진시가 사시가 됩니다.** 시주는 두 시간
 *   단위입니다. 서울 진태양시 −32분까지 얹히면 더 벌어집니다.
 *
 *   그런데 같은 화면 아래에 "열두 시로 채워 넣는 집도 있으나, 그건 없는
 *   걸 지어내는 것이오" 라고 적혀 있었습니다. **시각을 정확히 아는
 *   손님이 이 집이 스스로 한 말을 어기는 걸 자기 눈으로 봤습니다.**
 *
 *   여섯 칸은 **모르는 사람을 위한 길로 남기고**, 고른 뒤에 시·분을
 *   아는 사람에게 한 겹 더 엽니다.
 */
const HOURS: [string, string, number][] = [
  ["새벽", "03–07", 5],
  ["아침", "07–11", 9],
  ["한낮", "11–15", 13],
  ["저녁", "15–19", 17],
  ["밤", "19–23", 21],
  ["자정 무렵", "23–03", 0],
];

const AXIS4 = [
  "INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
  "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP",
];

const CITIES = ["서울", "인천", "수원", "춘천", "강릉", "대전", "청주", "전주",
  "광주", "목포", "대구", "안동", "포항", "부산", "울산", "창원", "제주"];

/*
 * 화면 순서. ★ 고민(a5)이 이름(a2) 바로 뒤로 올라왔습니다.
 *   id 는 그대로 둡니다 — 계측 화이트리스트와 docs/08 이 이 이름을 씁니다.
 */
const ORDER: Step[] = ["a1", "a2", "a5", "a3", "a4", "a4b", "a6", "a7"];
const STEPS: Step[] = ORDER;

/*
 * 진행 표시.
 *
 * ★ a1 에서 이미 한 단계를 지나 놓고도 a2 가 1/7 이었습니다. 손님
 *   입장에서는 **이미 한 수고가 0으로 리셋**됩니다. 여기서는 거짓말도
 *   필요 없습니다 — 실제로 한 단계를 지났습니다.
 *
 * ★ a6·a7 은 진행을 안 그립니다. 결과가 보상인 구간에서 막대는 남은
 *   보상이 아니라 **남은 노동**을 강조합니다.
 */
const PROGRESS_TOTAL = ORDER.length;
function progressAt(step: Step): number | null {
  if (step === "a6" || step === "a7") return null;
  return ORDER.indexOf(step) + 1;
}

function EntryInner() {
  const router = useRouter();
  const params = useSearchParams();
  const s = useSession();
  // 관리자 레일이 ?step=a5 로 바로 건너뛸 수 있게 한다
  const asked = params.get("step") as Step | null;
  const [step, setStep] = useState<Step>(
    asked && STEPS.includes(asked) ? asked : "a1");

  useEffect(() => {
    if (asked && STEPS.includes(asked)) setStep(asked);
  }, [asked]);
  const [busy, setBusy] = useState(false);
  /* 고을을 펼쳤는가. 접어 두면 a3 의 필드가 다섯에서 넷이 됩니다. */
  const [cityOpen, setCityOpen] = useState(false);
  /* 시·분을 직접 적는 겹을 열었는가. 네 시간 칸이 시주를 바꿔 놓습니다. */
  const [exact, setExact] = useState(false);
  /* a6 계산 장면이 몇 줄까지 찍혔는가. 0 이면 아직 아무것도 안 찍혔다. */
  const [calcAt, setCalcAt] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [segments, setSegments] = useState<HookSegment[] | null>(null);
  const [hookDone, setHookDone] = useState(false);
  /* 「아니오」가 몇 번 나왔는가 · 이미 방향을 틀었는가 */
  const [misses, setMisses] = useState(0);
  const [turned, setTurned] = useState(false);

  // 화면 이름이 곧 step 입니다. 어디서 나가는지 이걸로 셉니다.
  useScreen(step);

  const season = s.seasonOverride ?? seasonOf();
  const lens = LENS_BY_ID[s.cur] ?? LENS_BY_ID.pungun;
  const beats = OPENING[season];

  /* ── a6 · 명식 세우기 — 서버 호출 ─────────────────────── */
  const buildChart = async () => {
    /*
     * 날짜를 지역 변수로 빼서 타입을 좁힙니다. a3 과 아래 useEffect 가
     * birthProblem 으로 이미 막지만, 컴파일러가 보는 것은 store 의
     * number | null 뿐입니다. null 을 서버로 보내지 않는 자리가 여기입니다.
     */
    const { year, month, day } = s;
    if (year === null || month === null || day === null) {
      setError("날을 다 적어야 명식을 세우오.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await api.chart({
        year, month, day,
        hour: s.hourKnown ? s.hour : null,
        minute: s.hourKnown ? s.minute : null,
        hour_known: s.hourKnown,
        sex: s.sex, birth_city: s.city,
      });
      s.set({ chartId: res.chart_id, features: res.features });
    } catch (e) {
      // 서버가 거절한 이유를 이 집의 말로 옮깁니다. 영어 원문이 뜨면
      // 그 순간 몰입이 깨지고, 무엇을 고쳐야 하는지도 모릅니다.
      const raw = e instanceof ApiError ? e.message : "";
      setError(birthMessageFrom(raw) ?? "명식을 세우지 못했소. 적은 것을 한 번 보시오.");
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    if (step !== "a6" || s.features || busy || error) return;
    // 잘못 적힌 채로 서버를 부르지 않습니다. a3 이 막지만, 관리자 레일이나
    // 주소로 바로 들어오는 길이 있어 여기서도 한 번 봅니다.
    const bad = birthProblem(s.year, s.month, s.day);
    if (bad) { setError(bad); return; }
    void buildChart();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  /*
   * 계산 장면을 한 줄씩 찍습니다. 여섯 줄 · 420ms.
   * 서버가 빨리 답해도 이 장면을 지우지 않습니다 — 여기서의 기다림은
   * 비용이 아니라 값입니다. 건너뛰는 길은 따로 냈습니다.
   */
  useEffect(() => {
    if (step !== "a6" || !s.features || calcAt >= 6) return;
    const t = setTimeout(() => setCalcAt((n) => n + 1), calcAt === 0 ? 240 : 420);
    return () => clearTimeout(t);
  }, [step, s.features, calcAt]);

  /* ── a7 · 훅 5단 ─────────────────────────────────────── */
  useEffect(() => {
    if (step !== "a7" || !s.chartId || segments) return;
    let alive = true;
    api.hook({
      chart_id: s.chartId, concern: s.concern, axis4: s.axis4,
      name: s.name, lens_id: s.cur, misses,
    })
      .then((r) => alive && setSegments(r.segments))
      .catch((e) => alive && setError(e instanceof ApiError ? e.message : "훅을 만들지 못했소."));
    return () => { alive = false; };
  }, [step, s.chartId, s.concern, s.axis4, s.name, s.cur, segments, misses]);

  /*
   * ★ 「아니오」가 쌓이면 도령이 방향을 틉니다.
   *
   *   전에는 응답이 즉답 한 줄만 바꾸고 다음 단은 그대로였습니다. 세 번
   *   아니라 해도 한 번도 방향을 안 틀었고, 그 순간 손님은 이게 녹음이라는
   *   걸 압니다. 둘이 쌓이면 아직 안 연 단을 **다시 받아 옵니다.**
   *   이미 읽은 단은 건드리지 않습니다 — 읽은 글이 뒤에서 바뀌면 그게
   *   더 이상합니다.
   */
  const onMiss = (n: number) => {
    if (n !== 2 || turned) return;
    setTurned(true);
    setMisses(n);
    if (!s.chartId) return;
    api.hook({
      chart_id: s.chartId, concern: s.concern, axis4: s.axis4,
      name: s.name, lens_id: s.cur, misses: n,
    })
      .then((r) => setSegments((prev) =>
        // 연 데까지는 그대로 두고, 그 뒤만 새로 짚은 것으로 바꿉니다.
        prev ? prev.map((seg, i) => (i <= n ? seg : r.segments[i] ?? seg)) : r.segments))
      .catch(() => { /* 못 받아 오면 원래 훅으로 계속합니다 */ });
  };

  /* ══════════════════════════════════════════════════════ */
  if (step === "a1") {
    /*
     * 대문은 프레임을 다 덮습니다. 그림이 배경이고 글이 그 위에 얹힙니다.
     * .gatehero 가 위치·키를 잡고 Scene 의 .fill 이 그 안을 채웁니다.
     *
     * ★ 비트를 셋에서 하나로 줄이고, 그 자리에 **얻는 것에 대한 약속**을
     *   놓았습니다. 버튼도 "…" 이 아니라 무슨 일이 일어나는지 말합니다.
     */
    return (
      <Shell bare>
        <div className="gatehero" onClick={() => setStep("a2")}>
          <Scene id="gate" className="fill" bleed />
          <div className="gatecopy">
            <Narration lines={beats} />
            <p className="promise" dangerouslySetInnerHTML={{ __html: PROMISE }} />
            <button className="btn mt" onClick={() => setStep("a2")}>
              글자를 세우러 들어간다
            </button>
            <p className="sm mt" style={{ color: "var(--paper3)" }}>
              {SEASON_PALETTE[season].ko}
            </p>
          </div>
        </div>

        {/* ★ 의심 풀기를 여기로 가져왔습니다.
            전에는 공유 링크로 온 사람만 봤습니다. 검색·광고로 직접 들어온
            사람은 이 여섯 문답을 한 번도 못 만난 채 의심을 안고 일곱
            화면을 지났습니다. 클릭을 막지 않게 접어 둡니다. */}
        <div className="gatedoubt">
          <Doubts compact first={null} />
        </div>
      </Shell>
    );
  }

  if (step === "a2") {
    const named = s.name.trim().length > 0;
    return (
      <Shell title="이름을 적다">
        <Progress step={progressAt("a2")!} total={PROGRESS_TOTAL} />
        <Scene id="desk" />
        <Narration lines={["도령이 붓을 들었다.", "종이는 아직 비어 있다."]} />
        <Say who="도령">그대를 뭐라 적으면 되겠소?</Say>
        <input className="fld ser" placeholder="이름 또는 별명" maxLength={12}
               value={s.name} onChange={(e) => s.set({ name: e.target.value })} />
        {/*
          ★ 여기가 이름의 쓸모를 **부정하는 쪽으로만** 말하고 있었습니다.
            "본명을 적을 이유는 없다 · 셈에는 쓰이지 않는다" — 사실이지만
            왜 묻는지는 안 말합니다. 이름은 훅 0단의 **첫 글자**로 박히는
            자리고, 개인화됐다고 믿을수록 그 문장을 자기 말로 읽습니다.
            빼앗기지 않게 하려면 무엇에 쓰는지를 말해야 합니다.
        */}
        <Narration lines={["", "본명을 적을 이유는 없다.", "셈에는 쓰이지 않는다."]} />
        <Say who="도령">셈에는 안 쓰이오. 다만 <b>내가 그대를 부를 때</b> 쓰오.</Say>

        <button className="btn" onClick={() => setStep("a5")}>
          {named ? "적는다" : "그냥 넘어간다"}
        </button>
        {/* 빈 채로 넘어가는 것도 **고른 것**이 되게 합니다. */}
        {!named && (
          <p className="sm mt" style={{ textAlign: "center" }}>
            안 적으시면 그냥 <b>&quot;그대&quot;</b>라 부르겠소.
          </p>
        )}
      </Shell>
    );
  }

  if (step === "a3") {
    /*
     * ★ 여기서 막습니다.
     *
     * 예전에는 a3 을 그냥 통과시키고 a6 에서 서버가 거절했습니다. 오타 하나
     * 낸 사람이 세 화면을 더 지나서야 영어 오류를 보고, 되돌아갈 버튼도
     * 없었습니다. 틀린 자리에서 바로 말해 줍니다.
     *
     * ★ 그리고 이 화면에 필드가 **다섯** 있었습니다 — 년·월·일·고을·성별.
     *   이 흐름에서 유일하게 다섯이 겹치는 자리입니다. 게다가 성별 버튼이
     *   누르는 즉시 다음 화면으로 넘어가서, 고을을 잘못 골랐다는 걸 그때
     *   깨달으면 되돌아갈 길이 뒤로 버튼뿐이었습니다.
     *
     *   고을은 **서울로 접어 두고**, 성별에는 확인 버튼을 답니다.
     *   그리고 이 집이 성별에만 대던 이유를 고을에도 답니다 — 이유를
     *   대면 필드가 요구가 아니라 설명이 됩니다.
     */
    const bad = birthProblem(s.year, s.month, s.day);
    const filled = s.year !== null && s.month !== null && s.day !== null;
    const num = (v: string): number | null => {
      const t = v.replace(/[^0-9]/g, "");
      return t === "" ? null : Number(t);
    };
    const askWord = CONCERNS.find((c) => c.id === s.concern)?.label ?? "";
    return (
      <Shell title="날을 대다">
        <Progress step={progressAt("a3")!} total={PROGRESS_TOTAL} />
        <Scene id="ink" />
        <Narration lines={["붓끝이 종이에 닿았다.", "먹이 한 방울 번졌다."]} />
        {/* ★ 앞에서 고른 고민을 되받습니다. 먼저 마음을 정한 사람은
            뒤이은 수고를 자기 결정과 맞추려 합니다. */}
        <Say who="도령">
          {askWord ? `${askWord}이 걸려 오셨다 했지. 그럼 날부터 대시오.` : "태어난 날을 대시오."}
        </Say>
        <div className="f3">
          <div>
            <label>년</label>
            <input className="fld" inputMode="numeric" placeholder="1993" maxLength={4}
                   value={s.year ?? ""}
                   onChange={(e) => s.set({ year: num(e.target.value), features: null, chartId: null })} />
          </div>
          <div>
            <label>월</label>
            <input className="fld" inputMode="numeric" placeholder="5" maxLength={2}
                   value={s.month ?? ""}
                   onChange={(e) => s.set({ month: num(e.target.value), features: null, chartId: null })} />
          </div>
          <div>
            <label>일</label>
            <input className="fld" inputMode="numeric" placeholder="15" maxLength={2}
                   value={s.day ?? ""}
                   onChange={(e) => s.set({ day: num(e.target.value), features: null, chartId: null })} />
          </div>
        </div>
        {filled && bad && (
          <p className="sm" style={{ color: "var(--ember)", marginTop: 8 }}>{bad}</p>
        )}

        {/* ★ 고을은 접어 둡니다. 대부분은 안 건드립니다. */}
        {!cityOpen ? (
          <p className="sm mt">
            고을은 <b>{s.city}</b>로 두었소.{" "}
            <button className="lk" onClick={() => setCityOpen(true)}>
              서울이 아니시오?
            </button>
          </p>
        ) : (
          <>
            <label className="sm" style={{ display: "block", marginTop: 12 }}>태어난 고을</label>
            <select className="fld" value={s.city}
                    onChange={(e) => s.set({ city: e.target.value, features: null, chartId: null })}>
              {CITIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
            <p className="sm">
              고을마다 해가 남중하는 때가 다르오. 서울은 32분을 되돌리오 —
              그만큼 시주가 갈릴 수 있소.
            </p>
          </>
        )}

        <Say who="도령">남녀에 따라 운이 흐르는 방향이 반대요. 이건 반드시 있어야 하오.</Say>
        <div className="og c2">
          {([["F", "여인"], ["M", "사내"]] as const).map(([v, label]) => (
            <button key={v} className={`op ${s.sex === v ? "on" : ""}`}
                    disabled={!!bad}
                    style={{ textAlign: "center", fontFamily: "var(--serif)", fontSize: 15 }}
                    onClick={() => s.set({ sex: v, features: null, chartId: null })}>
              {label}
            </button>
          ))}
        </div>

        {/* ★ 자동 진행을 없앴습니다. 되돌릴 여지를 줍니다. */}
        <button className="btn mt" disabled={!filled || !!bad}
                onClick={() => setStep("a4")}>
          다 적었소
        </button>
        {(!filled || bad) && (
          <p className="sm mt" style={{ textAlign: "center" }}>
            날을 다 적어야 다음으로 가오.
          </p>
        )}
      </Shell>
    );
  }

  if (step === "a4") {
    const bucket = HOURS.find(([, , h]) => h === s.hour);
    return (
      <Shell title="때를 묻다">
        <Progress step={progressAt("a4")!} total={PROGRESS_TOTAL} />
        <Scene id="room" />
        <Narration lines={["도령이 고개를 들었다."]} />
        <Say who="도령">때는 아시오?</Say>
        <Narration lines={["", "대부분은 모른다.", "모른다고 해도 그는 개의치 않았다."]} />

        {/* ★ "모르오" 를 눈에 띄게. 여기서 막히면 그대로 이탈한다. (docs/08 §3) */}
        <button className="btn" style={{ marginBottom: 12 }}
                onClick={() => {
                  s.set({ hourKnown: false, hour: null, features: null, chartId: null });
                  setStep("a4b");
                }}>
          모르오 · 세 기둥으로 보겠소
        </button>

        <div className="og c2">
          {HOURS.map(([label, range, h]) => (
            <button key={label}
                    className={`op ${s.hourKnown && s.hour === h ? "on" : ""}`}
                    onClick={() => {
                      s.set({ hourKnown: true, hour: h, minute: 0,
                              features: null, chartId: null });
                      setExact(false);
                    }}>
              <b>{label}</b><span>{range}</span>
            </button>
          ))}
        </div>

        {/*
          ★ 여기가 이 집의 1번 규칙을 어기고 있었습니다.
            네 시간짜리 칸이 한 시각으로 뭉개져서, 07:50 생이 "아침" 을
            고르면 09:00 으로 기록되고 **진시가 사시가 됩니다.** 아래
            문구는 "지어내지 않는다" 고 말하는데 칸은 지어내고 있었습니다.

            여섯 칸은 모르는 사람의 길로 남기고, 아는 사람에게 한 겹
            더 엽니다. 안 열면 경계에 걸린 사실을 그대로 적습니다.
        */}
        {s.hourKnown && bucket && (
          <div className="exact">
            {!exact ? (
              <>
                <p className="sm">
                  <b>{bucket[0]}</b>({bucket[1]}) 으로 두면 <b>{String(bucket[2]).padStart(2, "0")}시</b>로 셈하오.
                  두 시간 안으로만 아시면 <b>두 시주 중 어디인지 갈리오.</b>
                </p>
                <button className="lk" onClick={() => setExact(true)}>
                  시·분을 아시오? 적으면 그대로 셈하겠소
                </button>
              </>
            ) : (
              <>
                <p className="sm">아는 만큼만 적으시오. 모르는 자리는 비워 두시오.</p>
                <div className="f3">
                  <div>
                    <label>시</label>
                    <input className="fld" inputMode="numeric" maxLength={2}
                           placeholder={String(bucket[2])}
                           value={s.hour ?? ""}
                           onChange={(e) => {
                             const t = e.target.value.replace(/[^0-9]/g, "");
                             const v = t === "" ? null : Math.min(23, Number(t));
                             s.set({ hour: v, features: null, chartId: null });
                           }} />
                  </div>
                  <div>
                    <label>분</label>
                    <input className="fld" inputMode="numeric" maxLength={2}
                           placeholder="0"
                           value={s.minute || ""}
                           onChange={(e) => {
                             const t = e.target.value.replace(/[^0-9]/g, "");
                             s.set({ minute: t === "" ? 0 : Math.min(59, Number(t)),
                                     features: null, chartId: null });
                           }} />
                  </div>
                  <div />
                </div>
              </>
            )}
            <button className="btn mt" disabled={s.hour === null}
                    onClick={() => setStep("a4b")}>
              이 때로 하겠소
            </button>
          </div>
        )}

        <p className="sm mt">
          때를 모르면 시주를 세우지 않소. 열두 시로 채워 넣는 집도 있으나,
          그건 없는 걸 지어내는 것이오.
        </p>
      </Shell>
    );
  }

  if (step === "a4b") {
    return (
      <Shell title="성향 4글자">
        <Progress step={progressAt("a4b")!} total={PROGRESS_TOTAL} />
        <Scene id="ink" />
        <Narration lines={["그가 종이 한 장을 더 꺼냈다."]} />
        <Say who="도령" html="혹시 <b>성향 검사</b>를 해본 적 있소?<br>네 글자로 나오는 그것 말이오." />

        {/*
          ★ 무엇을 위해 묻는지를 **먼저** 말합니다.
            전에는 열여섯 칸을 보여 주고 보상은 말하지 않았습니다. 안 적은
            사람이 열에 넷이 넘는데(45.5%), 그 사람들은 훅에서 가장
            "나에 대한 말" 같은 자리를 대체 단으로 받습니다.
        */}
        <p className="sm">
          적으시면 <b>사주와 어긋나는 자리</b>를 한 겹 더 봐 드리오.
          안 적으셔도 되오 — 그때는 걸려 오신 것과 글자를 맞대 보겠소.
        </p>

        {/* ★ "모르오" 를 그리드 **위**로. a4 에서 이미 내린 판단을
            여기에도 적용합니다 — 훑는 순서상 아래에 두면 가장 늦게 보입니다. */}
        <button className="btn gh" style={{ marginBottom: 12 }}
                onClick={() => { s.set({ axis4: null }); setStep("a6"); }}>
          모르오 · 사주만으로 보겠소
        </button>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 5, margin: "14px 0" }}>
          {AXIS4.map((t) => (
            <button key={t} className={`op ${s.axis4 === t ? "on" : ""}`}
                    style={{ textAlign: "center", padding: "11px 2px",
                             fontFamily: "var(--mono)", fontSize: 12, letterSpacing: ".06em" }}
                    onClick={() => { s.set({ axis4: t }); setStep("a6"); }}>
              {t}
            </button>
          ))}
        </div>
        <Narration lines={["", "네 글자는 셈에 넣지 않는다.",
          "<em>사주와 어긋나는 자리</em>를 찾는 데만 쓴다."]} />
        <p className="sm mt">본 서비스의 성향 검사는 특정 상표의 검사가 아닙니다.</p>
      </Shell>
    );
  }

  if (step === "a5") {
    /*
     * ★ 이 화면이 여섯 번째에 있었습니다.
     *   「무엇이 걸려서 예까지 왔소?」 는 이 흐름 전체에서 가장 좋은 한
     *   줄인데, 손님은 그 앞에 이름·날짜·고을·성별·시각·넉 자 열여섯
     *   칸을 지나야 이걸 만났습니다. 그때쯤이면 이미 사무적인 모드입니다.
     *   이름 바로 뒤로 올렸습니다.
     */
    return (
      <Shell title="걸리는 것">
        <Progress step={progressAt("a5")!} total={PROGRESS_TOTAL} />
        <Scene id="fork" />
        <Narration lines={["붓을 내려놓고, 그가 물었다."]} />
        <Say who="도령">
          {s.name ? `${s.name}. 무엇이 걸려서 예까지 왔소?` : "무엇이 걸려서 예까지 왔소?"}
        </Say>
        <Narration lines={["", "한참 답이 나오지 않았다.", "하나만 고르라면—"]} />
        <div className="og c2">
          {CONCERNS.map((c) => (
            <button key={c.id} className={`op ${s.concern === c.id ? "on" : ""}`}
                    onClick={() => { s.set({ concern: c.id as Concern }); setStep("a3"); }}>
              <b>{c.label}</b><span>{c.sub}</span>
            </button>
          ))}
        </div>
        <p className="sm mt">
          고른 것이 여덟 글자의 어느 자리를 볼지 정하오. 뒤에 바꿔도 되오.
        </p>
      </Shell>
    );
  }

  if (step === "a6") {
    /*
     * ★ 이 집이 가진 가장 큰 자산을 안 쓰던 자리입니다.
     *
     *   절기를 시각까지 세고, 표준시 변천을 되돌리고, 고을마다 진태양시를
     *   보정합니다. 그게 이 서비스의 차별점 그 자체인데 — **계산이 끝난
     *   뒤 정적인 표로 한꺼번에** 나왔습니다. 그 사이 화면은 "도령이
     *   종이를 폈다. 붓이 움직인다." 두 줄뿐이었습니다.
     *
     *   일하는 모습을 보여주면 결과가 같아도 더 값지게 봅니다. 여기는
     *   그 조건이 갖춰져 있습니다 — **진짜로 계산합니다.**
     *   그러니 한 줄씩 찍습니다. 서버가 빨리 답해도 이 장면을 지우지
     *   않습니다. 여기서의 기다림은 비용이 아니라 값입니다.
     */
    const c = s.features?.correction;
    const beats: string[] = c ? [
      `표준시(그 시절 쓰던 시계 기준)를 되돌린다… ${c.std_label}`,
      c.dst ? "서머타임 구간이오. 한 시간 되돌린다…"
            : "서머타임은 해당 없소.",
      `고을을 본다… ${c.city} ${c.lon_min > 0 ? "+" : ""}${c.lon_min}분`,
      c.hour_used ? `때를 고친다… ${c.before} → ${c.after}`
                  : "때를 모르신다 했으니, 시주는 세우지 않소.",
      `절기(계절이 바뀌는 마디)를 찾는다… ${c.jieqi_name} 절입 ${c.jieqi_at_kst}`,
      "여덟 글자가 섰다.",
    ] : [];
    const done = calcAt >= beats.length;

    return (
      <Shell title="글자가 서다">
        <Scene id="altar" />
        {busy && <Narration lines={["도령이 종이를 폈다.", "붓이 움직인다."]} />}
        {error && (
          <>
            <Say who="도령">{error}</Say>
            {/* ★ 여기가 막다른 길이었습니다.
                '다시 세운다' 는 같은 값으로 재시도만 해서, 잘못 적은
                사람은 영영 빠져나올 수 없었습니다. 고치러 갈 길을 냅니다. */}
            <button className="btn" onClick={() => setStep("a3")}>
              날을 고쳐 적는다
            </button>
            <button className="btn gh" onClick={() => void buildChart()}>
              다시 세워 본다
            </button>
          </>
        )}

        {s.features && !done && (
          <>
            <div className="calcrun">
              {beats.slice(0, calcAt).map((b, i) => (
                <p key={i} className={i === calcAt - 1 ? "on" : undefined}>{b}</p>
              ))}
            </div>
            <button className="btn gh mt" onClick={() => setCalcAt(beats.length)}>
              다 됐소, 건너뛰겠소
            </button>
            {/* 세는 동안 읽을 것을 둡니다 — 기다림이 빈 시간이 되지 않게. */}
            <Doubts compact first={null} />
          </>
        )}

        {s.features && done && (
          <>
            <Narration lines={["여덟 글자가 섰다."]} />
            {/* ★ "여덟 글자가 섰다" 만 있었습니다. 그게 무슨 뜻인지
                아무 데도 안 적혀 있었습니다. 첫 화면에서 한 번은
                말해 줘야 뒤가 읽힙니다. */}
            <p className="lede8">
              태어난 <b>해 · 달 · 날 · 시</b>를 각각 두 글자로 옮긴 것이오.
              넷씩 두 줄, 그래서 <b>여덟 글자</b>요. 이 여덟이 이 집이 읽는
              전부요 — 더도 덜도 없소.
            </p>
            <Pillars f={s.features} />
            <Summary f={s.features} />
            <ElementBar f={s.features} />
            <CalcPanel f={s.features} />
            <button className="btn mt" onClick={() => setStep("a7")}>
              이 글자가 무슨 말인지 듣는다
            </button>
          </>
        )}
      </Shell>
    );
  }

  /* a7 · 훅 5단 — 값은 아직 묻지 않는다 */
  return (
    <Shell title="도령이 말하다">
      {/* ★ 진행 막대를 뗐습니다. 결과가 보상인 구간에서 막대는 남은
          보상이 아니라 **남은 노동**을 강조합니다. */}
      <Scene id="facing" />
      {!segments && !error && <Narration lines={["도령이 종이를 들여다본다."]} />}
      {error && <Say who="도령">{error}</Say>}
      {segments && s.chartId && (
        <HookSegments
          segments={segments}
          chartId={s.chartId}
          lensId={s.cur}
          concern={s.concern}
          charName={lens.name}
          onMiss={onMiss}
          onDone={() => setHookDone(true)}
        />
      )}
      {hookDone && (
        <div className="blk in">
          <Narration lines={[`${lens.name}가 종이를 덮었다.`]} />
          {/*
            ★ 마감이 자기 빈약함을 자백하고 있었습니다.
              "여기까지가 여덟 글자 중 셋으로 본 것이다" — 정보 격차를 여는
              구조는 좋은데, **방금 좋았다고 느낀 손님에게 그건 8분의 3짜리였다고
              말하는 셈**입니다. 앞을 깎지 않으면서 격차는 그대로 둡니다:
              덜어낸 것이 아니라 **남은 것**으로 말합니다.
          */}
          <p style={{ fontFamily: "var(--serif)", fontSize: 18, lineHeight: 1.78, color: "var(--c)" }}>
            여기까지는 <b>그대가 어떤 사람인가</b>였소.
          </p>
          <p className="tx mt">
            남은 자리에는 <b>왜 하필 지금</b>과 <b>언제 바뀌는가</b>가 있소.
          </p>
          <button className="btn mt" onClick={() => router.push("/pay?step=d0")}>
            값 없이 한 겹 더
          </button>
          <button className="btn gh" onClick={() => router.push("/pay?step=d1")}>
            어디까지 볼지 고른다
          </button>
          <p className="sm mt" style={{ textAlign: "center" }}>값은 아직 묻지 않았다</p>
        </div>
      )}
    </Shell>
  );
}

export default function EntryPage() {
  return (
    <Suspense fallback={<Shell bare><Narration lines={["대문을 여는 중이오."]} /></Shell>}>
      <EntryInner />
    </Suspense>
  );
}
