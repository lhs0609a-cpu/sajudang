"use client";

/**
 * @screen a1 a2 a3 a4 a4b a5 a6 a7
 * A · 들어가다 — a1 골목 → a2 이름 → a3 날 → a4 때 → a4b 성향 → a5 고민
 *                → a6 명식 → a7 훅 5단
 *
 * 이탈 방어 (docs/08 §3)
 *   a4  "모르오" 를 **크게**. 여기서 막히면 그대로 이탈한다.
 *   a4b "모르오 · 사주만으로 보겠소" 를 유지한다.
 *   a7  값을 아직 묻지 않는다. 무료 6단이 먼저다.
 *
 * ★ 계산은 서버(/v1/chart)가 합니다. 여기서 사주를 세지 않습니다.
 */
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Shell from "@/components/Shell";
import Scene from "@/components/scene/Scene";
import { Narration, Progress, Say } from "@/components/Narration";
import { CalcPanel, ElementBar, Pillars, Summary } from "@/components/Chart";
import HookSegments from "@/components/HookSegments";
import { api, ApiError } from "@/lib/api";
import { LENS_BY_ID } from "@/lib/lenses";
import { CONCERNS, seasonOf, useSession, type Concern } from "@/lib/store";
import { SEASON_PALETTE } from "@/components/scene/manifest";
import type { HookSegment } from "@shared/chart";

type Step = "a1" | "a2" | "a3" | "a4" | "a4b" | "a5" | "a6" | "a7";

const OPENING: Record<string, string[][]> = {
  spring: [
    ["담장 위로 벚꽃이 넘어와 있었다."],
    ["초롱이 줄지어 걸려 있고,", "바람에 꽃잎이 흩날린다."],
    ["돌바닥에 꽃잎이 깔렸다.", "", "대문은 열려 있었다."],
  ],
  summer: [
    ["비가 막 그친 밤이었다."],
    ["담장 위로 능소화가 늘어져 있고,", "초롱이 줄지어 걸려 있다."],
    ["물 고인 돌바닥에 불빛이 흔들린다.", "", "대문은 열려 있었다."],
  ],
  autumn: [
    ["국화 냄새가 났다."],
    ["처마 끝에 등이 걸려 있고,", "마당에 낙엽이 쌓였다."],
    ["발밑에서 잎이 바스러진다.", "", "대문은 열려 있었다."],
  ],
  winter: [
    ["눈이 소리 없이 내리고 있었다."],
    ["처마 밑에 고드름이 달렸고,", "창마다 불이 켜져 있다."],
    ["댓돌 위에 신발이 없다.", "", "그런데 문은 열려 있었다."],
  ],
};

const HOURS: [string, string, number | null][] = [
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

const STEPS: Step[] = ["a1", "a2", "a3", "a4", "a4b", "a5", "a6", "a7"];

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
  const [beat, setBeat] = useState(0);          // a1 나레이션 진행
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [segments, setSegments] = useState<HookSegment[] | null>(null);
  const [hookDone, setHookDone] = useState(false);

  const season = s.seasonOverride ?? seasonOf();
  const lens = LENS_BY_ID[s.cur] ?? LENS_BY_ID.pungun;
  const beats = OPENING[season];

  /* ── a6 · 명식 세우기 — 서버 호출 ─────────────────────── */
  const buildChart = async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await api.chart({
        year: s.year, month: s.month, day: s.day,
        hour: s.hourKnown ? s.hour : null,
        minute: s.hourKnown ? s.minute : null,
        hour_known: s.hourKnown,
        sex: s.sex, birth_city: s.city,
      });
      s.set({ chartId: res.chart_id, features: res.features });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "명식을 세우지 못했소.");
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    if (step === "a6" && !s.features && !busy && !error) void buildChart();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  /* ── a7 · 훅 5단 ─────────────────────────────────────── */
  useEffect(() => {
    if (step !== "a7" || !s.chartId || segments) return;
    let alive = true;
    api.hook({
      chart_id: s.chartId, concern: s.concern, axis4: s.axis4,
      name: s.name, lens_id: s.cur,
    })
      .then((r) => alive && setSegments(r.segments))
      .catch((e) => alive && setError(e instanceof ApiError ? e.message : "훅을 만들지 못했소."));
    return () => { alive = false; };
  }, [step, s.chartId, s.concern, s.axis4, s.name, s.cur, segments]);

  /* ══════════════════════════════════════════════════════ */
  if (step === "a1") {
    const line = beats[Math.min(beat, beats.length - 1)];
    const last = beat >= beats.length;
    const advance = () => (last ? setStep("a2") : setBeat((b) => b + 1));
    return (
      <Shell bare>
        <div style={{ textAlign: "center", paddingTop: 14, cursor: "pointer" }}
             onClick={advance}>
          <Scene id="gate" className="hero" />
          {last ? (
            <Say who="도령" html={
              "오셨소.<br><span style='font-size:15.5px;color:var(--paper2)'>" +
              "비를 맞으셨군. …거기 앉으시오. 손부터 보겠소 — 아니, 글자부터.</span>"} />
          ) : (
            <Narration lines={line} />
          )}
          <button className="btn mt" onClick={advance}>{last ? "앉는다" : "…"}</button>
          <p className="sm mt" style={{ color: "var(--paper3)" }}>
            {SEASON_PALETTE[season].ko}
          </p>
        </div>
      </Shell>
    );
  }

  if (step === "a2") {
    return (
      <Shell title="이름을 적다" skipTo="/lobby">
        <Progress step={1} total={5} />
        <Scene id="desk" />
        <Narration lines={["도령이 붓을 들었다.", "종이는 아직 비어 있다."]} />
        <Say who="도령">그대를 뭐라 적으면 되겠소?</Say>
        <input className="fld ser" placeholder="이름 또는 별명" maxLength={12}
               value={s.name} onChange={(e) => s.set({ name: e.target.value })} />
        <Narration lines={["", "본명을 적을 이유는 없다.", "셈에는 쓰이지 않는다."]} />
        <button className="btn" onClick={() => setStep("a3")}>적는다</button>
      </Shell>
    );
  }

  if (step === "a3") {
    return (
      <Shell title="날을 대다" skipTo="/lobby">
        <Progress step={2} total={5} />
        <Scene id="ink" />
        <Narration lines={["붓끝이 종이에 닿았다.", "먹이 한 방울 번졌다."]} />
        <Say who="도령">
          {s.name ? `${s.name}이 태어난 날은 언제요?` : "태어난 날을 대시오."}
        </Say>
        <div className="f3">
          <div>
            <label>년</label>
            <input className="fld" inputMode="numeric" value={s.year}
                   onChange={(e) => s.set({ year: Number(e.target.value) || 0 })} />
          </div>
          <div>
            <label>월</label>
            <input className="fld" inputMode="numeric" value={s.month}
                   onChange={(e) => s.set({ month: Number(e.target.value) || 0 })} />
          </div>
          <div>
            <label>일</label>
            <input className="fld" inputMode="numeric" value={s.day}
                   onChange={(e) => s.set({ day: Number(e.target.value) || 0 })} />
          </div>
        </div>

        <label className="sm" style={{ display: "block", marginTop: 12 }}>태어난 고을</label>
        <select className="fld" value={s.city}
                onChange={(e) => s.set({ city: e.target.value })}>
          {CITIES.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <p className="sm">고을에 따라 진태양시가 달라지오. 서울은 32분을 되돌리오.</p>

        <Say who="도령">남녀에 따라 운이 흐르는 방향이 반대요. 이건 반드시 있어야 하오.</Say>
        <div className="og c2">
          {([["F", "여인"], ["M", "사내"]] as const).map(([v, label]) => (
            <button key={v} className={`op ${s.sex === v ? "on" : ""}`}
                    style={{ textAlign: "center", fontFamily: "var(--serif)", fontSize: 15 }}
                    onClick={() => { s.set({ sex: v, features: null, chartId: null }); setStep("a4"); }}>
              {label}
            </button>
          ))}
        </div>
      </Shell>
    );
  }

  if (step === "a4") {
    return (
      <Shell title="때를 묻다" skipTo="/lobby">
        <Progress step={3} total={5} />
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
            <button key={label} className="op"
                    onClick={() => {
                      s.set({ hourKnown: true, hour: h ?? 0, minute: 0,
                              features: null, chartId: null });
                      setStep("a4b");
                    }}>
              <b>{label}</b><span>{range}</span>
            </button>
          ))}
        </div>
        <p className="sm mt">
          때를 모르면 시주를 세우지 않소. 열두 시로 채워 넣는 집도 있으나,
          그건 없는 걸 지어내는 것이오.
        </p>
      </Shell>
    );
  }

  if (step === "a4b") {
    return (
      <Shell title="성향 4글자" skipTo="/lobby">
        <Progress step={4} total={5} />
        <Scene id="ink" />
        <Narration lines={["그가 종이 한 장을 더 꺼냈다."]} />
        <Say who="도령" html="혹시 <b>성향 검사</b>를 해본 적 있소?<br>네 글자로 나오는 그것 말이오." />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 5, margin: "14px 0" }}>
          {AXIS4.map((t) => (
            <button key={t} className={`op ${s.axis4 === t ? "on" : ""}`}
                    style={{ textAlign: "center", padding: "11px 2px",
                             fontFamily: "var(--mono)", fontSize: 12, letterSpacing: ".06em" }}
                    onClick={() => { s.set({ axis4: t }); setStep("a5"); }}>
              {t}
            </button>
          ))}
        </div>
        <button className="btn gh" onClick={() => { s.set({ axis4: null }); setStep("a5"); }}>
          모르오 · 사주만으로 보겠소
        </button>
        <Narration lines={["", "네 글자는 셈에 넣지 않는다.",
          "<em>사주와 어긋나는 자리</em>를 찾는 데만 쓴다."]} />
        <p className="sm mt">본 서비스의 성향 검사는 특정 상표의 검사가 아닙니다.</p>
      </Shell>
    );
  }

  if (step === "a5") {
    return (
      <Shell title="걸리는 것" skipTo="/lobby">
        <Progress step={5} total={5} />
        <Scene id="fork" />
        <Narration lines={["붓을 내려놓고, 그가 물었다."]} />
        <Say who="도령">무엇이 걸려서 예까지 왔소?</Say>
        <Narration lines={["", "한참 답이 나오지 않았다.", "하나만 고르라면—"]} />
        <div className="og c2">
          {CONCERNS.map((c) => (
            <button key={c.id} className={`op ${s.concern === c.id ? "on" : ""}`}
                    onClick={() => { s.set({ concern: c.id as Concern }); setStep("a6"); }}>
              <b>{c.label}</b><span>{c.sub}</span>
            </button>
          ))}
        </div>
      </Shell>
    );
  }

  if (step === "a6") {
    return (
      <Shell title="글자가 서다">
        <Scene id="altar" />
        {busy && <Narration lines={["도령이 종이를 폈다.", "붓이 움직인다."]} />}
        {error && (
          <>
            <Say who="도령">{error}</Say>
            <button className="btn" onClick={() => void buildChart()}>다시 세운다</button>
          </>
        )}
        {s.features && (
          <>
            <Narration lines={["여덟 글자가 섰다."]} />
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
          onDone={() => setHookDone(true)}
        />
      )}
      {hookDone && (
        <div className="blk in">
          <Narration lines={[`${lens.name}가 종이를 덮었다.`]} />
          <p style={{ fontFamily: "var(--serif)", fontSize: 18, lineHeight: 1.78, color: "var(--c)" }}>
            여기까지가 <b>여덟 글자 중 {s.features?.hour_known ? "셋" : "둘"}</b>로 본 것이다.
          </p>
          <p className="tx mt">나머지에는 <b>왜</b>와 <b>언제</b>가 들어 있다.</p>
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
