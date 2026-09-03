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
 *   a4b "모르겠습니다 · 사주만으로 보겠습니다" 를 그리드 **위**로 올렸다.
 *   a7  값을 아직 묻지 않는다. 무료 6단이 먼저다.
 *
 * ★ 계산은 서버(/v1/chart)가 합니다. 여기서 사주를 세지 않습니다.
 */
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Shell from "@/components/Shell";
import { useScreen } from "@/lib/track";
import { birthMessageFrom, birthProblem } from "@/lib/birth";
import { needsGuardian } from "@/lib/biz";
import Scene from "@/components/scene/Scene";
import { Narration, Progress, Say } from "@/components/Narration";
import { CalcPanel, ElementBar, ManseTable, Pillars, Summary } from "@/components/Chart";
import HookSegments from "@/components/HookSegments";
import Doubts from "@/components/Doubts";
import Meet from "@/components/Meet";
import ActOut from "@/components/ActOut";
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
 * 대문에 적는 약속.
 *
 * ★ 여기가 만 명이 들어오는 문인데 심리 장치가 하나뿐이었습니다
 *   (tools/persuasion_audit.py). 그렇다고 많이 붙이면 대문이
 *   시끄러워집니다 — 첫 화면에서 설득하려 들면 광고로 읽힙니다.
 *   **셋만** 정확히 넣습니다.
 *
 *     구체   여덟 글자 · 다섯 마디   — 수가 박혀야 말이 선다
 *     선물   여기까지 값은 안 받소   — 받은 것이 있어야 갚고 싶어진다
 *     궁금   왜 하필 지금            — 열어 놓고 안 닫은 고리
 *
 * ★ 「맞힌다」 는 말은 여전히 안 씁니다. 문턱을 낮추는 말(날 하나면
 *   되오)이 앞에 오고, 못 하는 말은 뒤에 그대로 둡니다.
 *
 * ★ 글을 상수에서 화면으로 옮겼습니다 (2026-09-03).
 *
 *   전에는 `const PROMISE = "…<b>날</b>…"` 한 덩이를
 *   `dangerouslySetInnerHTML` 로 부었습니다. 그래서
 *
 *     · 화면 글이 화면 밖에 있어 **대문이 80자로 잡혔습니다.**
 *       실제로 손님이 읽는 것은 그 네 배입니다.
 *     · 태그가 낀 문자열이라 글 긁는 자가 「그대가 태어난 」 처럼
 *       **태그 앞 조각을 통째로 잃었습니다.**
 *     · 손으로 쓴 HTML 을 그대로 붓는 자리라 늘 위험합니다.
 *
 *   JSX 로 적으면 셋이 한꺼번에 없어집니다. 아래 a1 안에 있습니다.
 */

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

/**
 * 24시간으로 받은 값을 사람 말로 되읽는다.
 *
 * ★ 왜 되읽나
 *
 *   가장 흔한 실수는 **오후를 12시간 빼고 적는 것**입니다. 오후 3시
 *   55분생이 「3」 을 적으면 새벽 3시가 되고, 시주가 甲申 에서 甲寅 으로
 *   통째로 달라집니다. 여덟 글자 중 둘이 틀리는 것이라 리포트 전체가
 *   다른 사람 것이 됩니다.
 *
 *   막을 방법은 되읽어 주는 것뿐입니다 — 「새벽 3시 55분에 나셨소」 를
 *   보면 손님이 그 자리에서 알아봅니다.
 */
function clockWord(h: number, m: number): string {
  const mm = m ? `${m}분` : "정각";
  if (h === 0) return `자정 무렵 0시 ${mm}`;
  if (h < 6) return `새벽 ${h}시 ${mm}`;
  if (h < 12) return `아침 ${h}시 ${mm}`;
  if (h === 12) return `한낮 12시 ${mm}`;
  if (h < 18) return `오후 ${h - 12}시 ${mm}`;
  return `밤 ${h - 12}시 ${mm}`;
}

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
  /*
   * ★ 지나온 단계를 쌓아 둔다.
   *
   *   진입 흐름은 주소가 `/` 하나입니다. 상단 화살표는 `router.back()`
   *   이라 **한 단계 뒤가 아니라 사이트 밖으로** 나갔습니다. 그래서
   *   성향 넉 자에서 잘못 누르면 — 열여섯 칸이 한 줄에 넷씩 붙어 있어
   *   손가락이 흔히 미끄러집니다 — 되돌릴 길이 없었습니다.
   *   걸리는 것 화면은 「뒤에 바꿔도 되오」 라고 적어 두기까지 했는데,
   *   바꿀 자리가 개발용 레일 말고는 없었습니다.
   */
  /*
   * 다음 대운이 바뀌는 나이. 지금 대운의 **다음** 칸이 시작하는 해입니다.
   * 마지막 칸이면 없습니다 — 없으면 그 줄을 안 냅니다.
   */
  const nextTurn = (() => {
    const f = s.features;
    if (!f?.daeun || typeof f.daeun_now !== "number") return null;
    const nx = f.daeun[f.daeun_now + 1];
    return nx && typeof nx.start_age === "number" ? nx.start_age : null;
  })();

  const [trail, setTrail] = useState<Step[]>([]);
  const go = (next: Step) => {
    setTrail((t) => [...t, step]);
    setStep(next);
    /*
     * ★ 주소도 따라오게 합니다.
     *
     *   진입 흐름은 주소가 `/` 하나 위의 여러 단계라, 화면이 넘어가도
     *   주소는 그대로였습니다. 그래서 관리자 레일의 「지금 자리」가
     *   **거짓말을 했습니다** — 화면은 훅인데 레일은 「a4 · 때」라고
     *   찍혀 있었습니다. 레일은 주소를 보고 판단하기 때문입니다.
     *
     *   replace 를 씁니다 — push 로 쌓으면 뒤로 가기가 한 화면에
     *   여러 번 걸려 손님이 밖으로 못 나갑니다. 되돌아가는 길은
     *   trail 이 따로 들고 있습니다.
     */
    router.replace("/?step=" + next, { scroll: false });
  };
  const back = trail.length
    ? () => {
        setTrail((t) => t.slice(0, -1));
        setStep(trail[trail.length - 1]);
      }
    : undefined;
  const [busy, setBusy] = useState(false);
  /* 고을을 펼쳤는가. 접어 두면 a3 의 필드가 다섯에서 넷이 됩니다. */
  const [cityOpen, setCityOpen] = useState(false);
  /*
   * ★ 때를 묻는 길을 셋으로 세웠습니다 (2026-09-02).
   *
   *       ① 시·분을 적는다        ← 기본. 적은 그대로 셈합니다
   *       ② 모르겠다 → 대강 칸    ← 새벽·아침·한낮…
   *       ③ 그것도 모르겠다       ← 세 기둥으로
   *
   *   전에는 ② 가 **먼저** 있었고 ① 은 칸을 고른 뒤 작은 링크를 눌러야
   *   열렸습니다. 그래서 시각을 아는 사람도 칸으로 흘러갔고, 재보니
   *   칸을 고른 사람의 **51.7%** 가 틀린 시주를 받았습니다
   *   (.\dev.ps1 hours). 틀린 시주는 여덟 글자 중 둘을 바꾸고, 오행
   *   개수를 바꾸고, 용신과 신강약까지 바꿉니다.
   *
   *   ② 를 없애지는 않습니다 — 정말 대강만 아는 사람에게는 세 기둥보다
   *   낫습니다. 다만 **모르겠다고 한 사람에게만** 보이고, 고르면 무엇을
   *   무릅쓰는지 그 자리에 적습니다.
   */
  /* 「모르겠다」를 눌렀는가. 그때만 대강 칸이 나옵니다. */
  const [vague, setVague] = useState(false);
  /*
   * 어느 칸을 골랐는가. **s.hour 로 되찾으면 안 됩니다** — 시를 고치는
   * 순간 어느 칸에도 안 맞아 칸 표시가 사라집니다.
   */
  const [pickedHour, setPickedHour] = useState<number | null>(
    // 되돌아온 손님이면 전에 고른 칸을 되살립니다. 처음 한 번만 봅니다.
    () => {
      const i = HOURS.findIndex(([, , h]) => h === useSession.getState().hour);
      return i >= 0 && useSession.getState().hourKnown ? i : null;
    });
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
    // ★ 만 14세 미만은 법정대리인 동의 없이 개인정보를 못 받습니다
    //   (개인정보보호법 제22조의2). 나이를 **또 묻지 않습니다** —
    //   생년월일은 사주를 보려고 이미 받았습니다. 한 번 받은 것으로
    //   셈할 수 있는 걸 다시 물으면 그 자리에서 나갑니다.
    if (needsGuardian(year, month, day)) {
      setError(
        "만 열네 살이 안 되었소. 그 나이에는 부모님 동의가 있어야 "
        + "생년월일을 받을 수 있소 — 법이 그러하오. 어른과 함께 오시오."
      );
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
      s.set({ chartId: res.chart_id, features: res.features,
              rarity: res.rarity ?? null,
              divergence: res.divergence ?? null });
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
      <Shell screen="a1" bare>
        <div className="gatehero" onClick={() => go("a2")}>
          <Scene id="gate" className="fill" bleed />
          <div className="gatecopy">
            <Narration lines={OPENING[season]} />
            <p className="promise">
              그대가 태어난 <b>날</b> 하나면 되오. 시는 몰라도 되오.<br />
              여덟 글자를 세우고 <b>다섯 마디</b>를 하리다 —
              여기까지 값은 안 받소.<br />
              <b>왜 하필 지금</b> 이걸 보고 있는지, 그 자리부터 짚소.
            </p>
            {/* 막을 끊는 한 줄 — 묻고 답하지 않습니다 */}
            <ActOut kind="남긴 물음" next="이름을 적다">
              들어오는 사람은 하나같이 같은 걸 묻소.<br />
              <b>「어제도 있던 일인데, 왜 하필 오늘이오?」</b><br />
              그건 대문에서 답할 말이 아니오.
              {/* ★ 대문은 조용해야 합니다. 여기 붙이는 건 한 줄뿐이고,
                  그 한 줄도 **이미 참인 것**입니다 — 여덟 글자는 8자이고
                  여기까지 값은 0원입니다. 지어낸 압박이 아닙니다. */}
              <br />
              여태 미뤄 두고 오늘 여기까지 오신 것이오.
              {" "}8글자를 세우고 마디 5개를 듣는 데 값은 0원이오.
              때를 모르시면 6글자로 보오.
            </ActOut>
            <button className="btn mt" onClick={() => go("a2")}>
              내 운명을 확인하겠습니다
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
      <Shell screen="a2" title="이름을 적다" onBack={back}>
        <Progress step={progressAt("a2")!} total={PROGRESS_TOTAL} />
        <Scene id="desk" />
        {/* ★ 그림에는 붓이 **떠 있습니다** — 잡은 손이 없습니다.
            「붓을 들었다」 고 적으면 손님이 둘 중 무엇을 믿을지 몰라
            합니다. 그림이 더 좋으니 글을 맞춥니다. */}
        <Narration lines={["붓이 저 혼자 떠올랐다.", "종이는 아직 비어 있다."]} />

        {/*
          ★ 첫 등장은 여기입니다.

            전에는 큰 초상이 a4 에 있었습니다. 그런데 도령이 **처음
            말하는 자리는 a2** 입니다 — 세 화면을 말만 듣다가 네 번째에
            얼굴을 보는 셈이었습니다.

            사람은 처음 본 얼굴로 그 뒤의 목소리를 듣습니다. 얼굴이
            늦게 나오면 앞의 세 마디는 **누가 하는 말인지 모르는 채**
            지나갑니다.

            들어올 때 한 번 떠오르게 합니다(meet-in). 동작 줄이기를
            켠 사람에게는 그냥 있습니다.
        */}
        <Meet note="처음 뵙겠소" />
        <Say who="도령" lens="pungun">그대를 뭐라 적으면 되겠소?</Say>
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
        {/*
          ★ 여기가 63점이었습니다.

            「셈에는 안 쓰이오」 한 줄이라 **왜 묻는지**가 반만
            서 있었습니다. 이름은 훅 0단의 첫 글자로 박히는 자리라,
            여기서 적고 안 적고가 뒤의 다섯 단을 바꿉니다. 그 말을
            안 하면 손님은 그냥 개인정보를 내주는 칸으로 봅니다.
            팩폭 60 · 명확 45 · 비유 0.
        */}
        <Say who="도령" lens="pungun">
          셈에는 안 쓰이오. 다만 <b>내가 그대를 부를 때</b> 쓰오.
          <br />
          이름은 12글자까지 받고, 셈에 쓰는 건 태어난 해·달·날·시
          4자리뿐이오. 이름을 넣든 안 넣든 8글자는 한 글자도
          안 바뀌오.
          <br />
          <b>여태 이런 칸에서 가짜 이름을 적어 본 적이 있소.</b>
          {" "}적고 나서 뭐가 어떻게 쓰이나 싶어 찜찜했던 자리요.
          <br />
          그래서 여기는 별명이어도 되오 — <b>부르는 데만</b> 쓰니,
          찻집에서 「손님」 대신 뭐라 불러 드릴까 묻는 것처럼,
          붓끝이 종이에 닿기 전에 한 번 여쭙는 것이오.
        </Say>

        <button className="btn" onClick={() => go("a5")}>
          {named ? "이 이름으로 하겠습니다" : "그냥 넘어가겠습니다"}
        </button>
        {/* 빈 채로 넘어가는 것도 **고른 것**이 되게 합니다. */}
        {!named && (
          <p className="sm mt" style={{ textAlign: "center" }}>
            안 적으시면 그냥 <b>&quot;그대&quot;</b>라 부르겠소.
          </p>
        )}
        {/*
          ★ 이름 칸에서 망설이는 사람이 많습니다 — 뭘 하려고 이름을
            받나 싶어서입니다. 무엇을 받고 무엇을 안 받는지, 그리고
            여기까지 값이 없다는 것을 한 줄로 말합니다.
        */}
        {true && (
          <p className="sm mt" style={{ textAlign: "center" }}>
            셈에 쓰는 것은 <b>태어난 날</b> 하나요. 이름은 안 쓰오.
            <b> 여기까지 값은 안 받소.</b>
          </p>
        )}
        <ActOut kind="끊긴 동작" next="걸리는 것">
          이름은 셈에 <b>한 글자도</b> 안 들어가오.<br />
          <b>그런데 딱 한 번, 부를 일이 생기오.</b> 그게 어디겠소?
        </ActOut>
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
      <Shell screen="a3" title="날을 대다" onBack={back}>
        <Progress step={progressAt("a3")!} total={PROGRESS_TOTAL} />
        <Scene id="ink" />
        <Narration lines={["붓끝이 종이에 닿았다.", "먹이 한 방울 번졌다."]} />
        {/* ★ 앞에서 고른 고민을 되받습니다. 먼저 마음을 정한 사람은
            뒤이은 수고를 자기 결정과 맞추려 합니다. */}
        <Say who="도령" lens="pungun">
          {askWord ? `${askWord}이 걸려 오셨다 했지. 그럼 날부터 대시오.` : "태어난 날을 대시오."}
          <br />
          {/*
            ★ 여기가 72점이었습니다. 물음 한 줄과 입력 칸 셋이 전부라,
              **왜 이걸 묻는지**가 없었습니다. 생년월일은 손님이 가장
              내주기 싫어하는 값인데 이유를 안 대고 받고 있었습니다.
          */}
          그대가 적는 건 숫자 3개요 — 해와 달과 날.
          {" "}그 3개로 기둥 3자리, 글자 6개가 서오. 나머지 한 자리는
          다음 장에서 때를 여쭙고 세우오.
          <br />
          <b>여태 생년월일을 적다가 그만둔 적이 있었소.</b>
          {" "}어디에 쌓이는지 안 적혀 있어서요.
          <br /> 이 집은 그 숫자로
          글자를 세우고 나면 더 쓸 데가 없소 — 공유 고리에도 안 담기고,
          계측에도 안 실리오. 자를 대고 치수만 재는 것처럼, 재고 나면
          자는 치웁니다.
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
        {/*
          ★ 여기가 가장 약한 화면이었습니다 (열 중 둘).

            날을 받는 자리라 붙일 게 없어 보이지만, **이 날 하나로
            무엇이 서는지**를 말해 주면 손님이 지금 무엇을 하고 있는지
            압니다. 그냥 칸을 채우는 것과 「내 여덟 글자를 세우는 중」은
            같은 동작인데 다른 일입니다.

            그리고 값을 안 받는다는 말을 여기서 한 번 더 합니다 —
            생년월일을 적는 자리가 이 흐름에서 가장 망설이는 데입니다.
        */}
        {/* ★ 「여덟 글자가 선다」 는 여기서 아직 참이 아닙니다. 때를
              안 물었으니 여기서 서는 것은 **여섯**입니다. 셀 수 있는
              말로 적어야 손님이 다음 화면이 왜 있는지 압니다. */}
        <p className="sm mt">
          이 날 하나로 여덟 글자 중 <b>여섯</b>이 서오. 남은 둘은 때를
          알아야 서오. 절기 (계절이 바뀌는 마디 스물넷) 와 표준시까지
          셈에 넣소 — <b>여기까지 값은 안 받소.</b>
        </p>

        {!cityOpen ? (
          <p className="sm mt">
            고을은 <b>{s.city}</b>로 두었소.{" "}
            <button className="lk" onClick={() => setCityOpen(true)}>
              서울이 아닙니다
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
              고을마다 해가 가장 높이 뜨는 때가 다르오. 같은 시계를 고을마다
              다른 자리에 걸어 둔 셈이오 — 서울은 <b>32분</b>을 되돌리오.
              그만큼 시주 (태어난 시각의 두 글자) 가 갈릴 수 있소.
            </p>
          </>
        )}

        <Say who="도령" lens="pungun">남녀에 따라 운이 흐르는 방향이 반대요. 이건 반드시 있어야 하오.</Say>
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

        {/* ★ 막이 그냥 끝나고 있었습니다. 다음 자리를 이름으로
            부르지 않아 「다 적었습니다」 가 어디로 가는 문인지
            몰랐습니다. 예고는 재촉이 아니라 안내입니다. */}
        <ActOut kind="끊긴 동작" next="때를 묻다">
          날까지는 섰소. <b>아직 한 자리가 비어 있소.</b>
          <br />
          기둥 넷 중 셋이 서고, 마지막 하나는 태어난 때가 정하오.
        </ActOut>
        {/* ★ 자동 진행을 없앴습니다. 되돌릴 여지를 줍니다. */}
        <button className="btn mt" disabled={!filled || !!bad}
                onClick={() => go("a4")}>
          다 적었습니다
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
    /*
     * ★ 여기가 고쳐지지 않던 자리입니다.
     *
     *   고른 칸(bucket)을 `s.hour` 로 되찾고 있었습니다. 그런데 손님이
     *   시를 고치는 순간 그 값이 어느 칸에도 안 맞습니다 — 13에서 한
     *   글자만 지워도 1이 되고, 1은 칸이 아닙니다. 그러면 `bucket` 이
     *   undefined 가 되고 **정밀 입력 칸이 통째로 사라집니다.**
     *   그래서 한 글자도 못 고쳤습니다.
     *
     *   고른 칸은 따로 기억합니다. 시를 아무리 고쳐도 칸은 안 없어집니다.
     */
    const bucket = pickedHour !== null ? HOURS[pickedHour] : undefined;
    return (
      <Shell screen="a4" title="때를 묻다" onBack={back}>
        <Progress step={progressAt("a4")!} total={PROGRESS_TOTAL} />
        <Scene id="room" figure />
        <Narration lines={["도령이 고개를 들었다."]} />
        {/*
          ★ 첫 대면. 여기가 손님이 그 사람의 얼굴을 처음 보는 자리입니다.

            전에는 일곱 화면을 지나도록 얼굴이 한 번도 안 나왔고, 초상은
            진열대(b2)에서야 나왔습니다 — 결제 갈림길 **뒤**입니다.
            얼굴을 보고 값을 치를지 정하는 것이지, 치를 마음을 먹은 뒤에
            얼굴을 보는 게 아닙니다.

            하필 여기인 까닭은 바로 윗줄에 있습니다 — 「도령이 고개를
            들었다」. 고개를 드는데 얼굴이 없으면 그 문장이 거짓말입니다.
        */}
        {/*
          ★ 도령을 **장면 안에** 세웠습니다 (위 Scene 의 figure).

            전에는 배경 한 칸, 그 아래 초상 한 칸이었습니다. 두 그림이
            따로 놓이면 손님에게는 「그림 두 장」이지 그 방에 있는
            사람이 아닙니다. 여기서는 이름만 답니다.
        */}
        <Meet nameOnly />
        <Say who="도령" lens="pungun">때는 아시오?</Say>
        <Narration lines={["", "대부분은 모른다.", "모른다고 해도 그는 개의치 않았다."]} />

        {/*
          ★ 순서를 뒤집었습니다 (2026-09-02).

            손님이 1993-11-25 **15시 55분**생인데 화면이 13시로 셈해
            시주가 壬午 로 섰습니다. 만세력은 甲申 이오 — 여덟 글자 중
            둘이 다르고, 그래서 **불이 하나 생기고 나무가 하나
            사라졌습니다.**

            까닭은 계산이 아니라 **입력**이었습니다. 네 시간짜리 칸을
            한 시각으로 뭉개고 있었습니다. 재보니 —

                칸을 고른 사람의 51.7% 가 틀린 시주를 받습니다.
                다섯 칸은 정확히 절반씩 틀립니다.
                (tools/hour_bucket_audit.py)

            시·분 칸은 있었습니다. 다만 **칸을 먼저 고른 뒤 작은 링크를
            눌러야** 열렸고, 칸을 고르는 순간 이미 한복판 시각이
            적혔습니다. 아는 사람이 두 번 더 눌러야 제 시각을 쓰는
            구조였습니다 — 그러니 아무도 안 눌렀습니다.

            그래서 시·분을 **먼저, 그냥** 냅니다. 칸은 대강만 아는
            사람의 길로 내려갑니다.
        */}
        {/* ① 시·분 — 기본 길. 적은 그대로 셈합니다 */}
        <div className="exact first">
          <p className="sm">
            태어난 <b>시각</b>을 적으시오. <b>적은 그대로 셈하오</b> —
            반올림도 어림도 하지 않소.
          </p>
          <div className="f3 hm">
            <div>
              <label>시 (0–23)</label>
              <input className="fld" inputMode="numeric" maxLength={2}
                     placeholder="15"
                     value={s.hourKnown && s.hour !== null ? s.hour : ""}
                     onChange={(e) => {
                       const t = e.target.value.replace(/[^0-9]/g, "").slice(0, 2);
                       // 손으로 적은 시각은 칸이 아닙니다. 칸 표시를
                       // 지워야 대강 칸 경고가 따라다니지 않습니다.
                       setPickedHour(null);
                       if (t === "") {
                         s.set({ hourKnown: true, hour: null,
                                 features: null, chartId: null });
                         return;
                       }
                       // 24 를 치면 23 으로 잡아 둡니다. 지우고 다시
                       // 칠 수 있어야 하므로 값 자체는 막지 않습니다.
                       s.set({ hourKnown: true, hour: Math.min(23, Number(t)),
                               features: null, chartId: null });
                     }} />
            </div>
            <div>
              <label>분 (0–59)</label>
              <input className="fld" inputMode="numeric" maxLength={2}
                     placeholder="55"
                     value={s.minute ? String(s.minute) : ""}
                     onChange={(e) => {
                       const t = e.target.value.replace(/[^0-9]/g, "").slice(0, 2);
                       setPickedHour(null);
                       s.set({ minute: t === "" ? 0 : Math.min(59, Number(t)),
                               features: null, chartId: null });
                     }} />
            </div>
            <div />
          </div>

          {/*
            ★ 되읽어 줍니다.

              가장 흔한 실수는 **오후를 12시간 빼고 적는 것**입니다 —
              오후 3시 55분을 「3」 으로 적으면 새벽 3시가 되고 시주가
              통째로 달라집니다. 24시간으로 받되, 받은 값을 사람 말로
              되읽어 주면 손님이 그 자리에서 알아봅니다.
          */}
          {s.hourKnown && s.hour !== null && (
            <p className="echo">
              {clockWord(s.hour, s.minute ?? 0)}에 나셨소.
              {s.hour >= 1 && s.hour <= 11 && (
                <span className="warn2">
                  {" "}오후였다면 <b>{s.hour + 12}</b>으로 적으시오.
                </span>
              )}
            </p>
          )}

          <button className="btn mt"
                  disabled={!s.hourKnown || s.hour === null}
                  onClick={() => go("a4b")}>
            이 시각으로 세우겠습니다
          </button>
        </div>

        {/* ② 모르겠다 → 대강 칸 */}
        {!vague ? (
          <button className="btn gh mt" onClick={() => setVague(true)}>
            시각은 모르겠습니다
          </button>
        ) : (
          <div className="vague">
            <p className="sm">
              그럼 <b>대강</b>이라도 아시오? 새벽인지 아침인지 한낮인지.
            </p>
            <div className="og c2">
              {HOURS.map(([label, range, h], idx) => (
                <button key={label}
                        className={`op ${pickedHour === idx ? "on" : ""}`}
                        onClick={() => {
                          s.set({ hourKnown: true, hour: h, minute: 0,
                                  features: null, chartId: null });
                          setPickedHour(idx);
                        }}>
                  <b>{label}</b><span>{range}</span>
                </button>
              ))}
            </div>

            {/*
              고르면 무엇을 무릅쓰는지 그 자리에 적습니다. 감추면
              손님은 정확히 셈한 줄 압니다.
            */}
            {bucket && (
              <div className="exact bucketwarn">
                <p className="sm">
                  <b>{bucket[0]}</b>({bucket[1]}) 은 <b>네 시간</b>이오.
                  시주는 두 시간마다 바뀌니 이 칸은 <b>두 시주에 걸치오.</b>
                  {" "}지금은 한복판인{" "}
                  <b>{String(bucket[2]).padStart(2, "0")}시</b>로 셈하는데,
                  이 칸에 태어난 사람의 <b>절반</b>은 다른 시주요.
                  <br />
                  시각을 아시면 위에 적으시오. 그게 훨씬 낫소.
                </p>
                <button className="btn mt" disabled={s.hour === null}
                        onClick={() => go("a4b")}>
                  그래도 이 칸으로 세우겠습니다
                </button>
              </div>
            )}

            {/* ③ 그것도 모르겠다 → 세 기둥 */}
            <button className="btn gh mt"
                    onClick={() => {
                      s.set({ hourKnown: false, hour: null,
                              features: null, chartId: null });
                      setPickedHour(null);
                      go("a4b");
                    }}>
              그것도 모르겠습니다 · 세 기둥으로 보겠습니다
            </button>
          </div>
        )}

        <ActOut kind="밝힘" next="성향 넉 자">
          같은 시각에 나도 <b>서울에서는 32분을 되돌려</b> 셈하오.
          해가 서울 위에 오는 때가 시계보다 그만큼 늦기 때문이오.<br />
          <b>그 32분에서 시주(時柱)가 갈리는 사람이 있소.</b>
        </ActOut>
        {/*
          ★ 쉬움이 0점이던 자리입니다.

            「시주」를 일곱 번 쓰면서 한 번도 안 풀었습니다. 손님은
            여덟 글자를 오늘 처음 보는 사람인데, 이 화면이 묻는 것이
            바로 그 글자 둘입니다. 풀지 않으면 왜 분까지 적어야
            하는지가 안 서고, 그러면 대강 칸으로 내려갑니다.
        */}
        <p className="sm mt">
          <b>시주(時柱)</b>란 태어난 때를 두 글자로 옮긴 것이오.
          기둥 넷 중 마지막 하나요 — 해·달·날이 셋을 세우고, 때가
          나머지 하나를 세우오. 네 다리 상에서 다리 하나처럼, 없다고
          못 쓰는 건 아니나 기우뚱하오.
          <br />
          때를 모르면 그 기둥을 안 세우오. 열두 시로 채워 넣는 집도
          있으나, 그건 없는 걸 지어내는 것이오. 여태 다른 데서
          「모르면 그냥 12시로 하죠」 소리를 들으셨을 게요 — 그리
          채워 넣은 여덟 글자는 둘이 틀린 채로 나가오. 없는 다리를
          나무토막으로 괴어 놓은 것처럼 말이오.<br />
          {/* 구체 — 무엇이 몇 개 서는지 */}
          때를 알면 <b>여덟 글자</b>가 다 서고, 모르면 <b>여섯 글자</b>로
          보오. 여섯으로도 <b>다섯 마디</b>는 그대로 하오.
        </p>
      </Shell>
    );
  }

  if (step === "a4b") {
    return (
      <Shell screen="a4b" title="성향 4글자" onBack={back}>
        <Progress step={progressAt("a4b")!} total={PROGRESS_TOTAL} />
        <Scene id="mirror" />
        <Narration lines={["그가 종이 한 장을 더 꺼냈다.",
                           "이번 것은 그가 적은 게 아니었다."]} />
        <Say who="도령" lens="pungun" html="혹시 <b>성향 검사</b>를 해본 적 있소?<br>네 글자로 나오는 그것 말이오." />

        {/*
          ★ 무엇을 위해 묻는지를 **먼저** 말합니다.
            전에는 열여섯 칸을 보여 주고 보상은 말하지 않았습니다. 안 적은
            사람이 열에 넷이 넘는데(45.5%), 그 사람들은 훅에서 가장
            "나에 대한 말" 같은 자리를 대체 단으로 받습니다.
        */}
        <p className="sm">
          적으시면 <b>사주와 어긋나는 자리</b>를 한 겹 더 봐 드리오.
          여덟 글자에서도 넉 자가 나오는데, 그 둘을 맞대 보는 것이오 —
          <b>거울 두 장을 마주 세우는 셈이오.</b> 겹치는 데는 넘기고
          <b>어긋난 자리</b>만 짚소.
        </p>
        {/*
          ★ 팩폭 37점 — 「어긋나는 자리」 는 뜬 말입니다. 무엇이
            어긋나면 살림에서 무엇이 달라지는지를 대야 합니다.
            아래 넉 줄은 전부 셀 수 있는 것으로 적었습니다.
        */}
        <p className="sm">
          넉 자는 4글자고 여덟 글자에서 나오는 것도 4글자요. 그 8개를
          한 칸씩 맞대면 겹치는 칸과 어긋난 칸이 나오오.
          {" "}어긋난 칸이 2개를 넘으면 그 자리를 따로 짚소.
          <br />
          어긋난다는 건 이런 것이오 — 밖에서는 말수가 많은 사람으로
          통하는데 집에 오면 연락을 안 받고 잠으로 도망가는 것,
          일은 벌여 놓고 돈 세는 자리에서 손이 굳는 것. 겉옷과 속옷이
          치수가 2개쯤 어긋난 것처럼, 입고는 다니는데 하루 종일
          불편한 자리요.
          <b> 남이 아는 나</b>와 <b>혼자 있을 때의 나</b>가 갈리는 자리요.
        </p>
        <span className="src">
          근거 · 넉 자 4글자와 여덟 글자에서 뽑은 4글자를 한 칸씩 맞대오 ·
          어긋난 칸이 2개를 넘으면 따로 짚소 · 안 적으셔도 5마디는
          그대로 하오
        </span>
        {/*
          ★ 여기가 팩폭 25점, 스물일곱 화면 중 꼴찌였습니다.
            「어긋나는 자리를 한 겹 더」 는 무슨 말인지 알 수 없는 말입니다 —
            어긋나면 **무슨 말을 듣는지**를 한 번도 안 보여 줬습니다.
            훅이 실제로 내는 말을 한 줄 미리 답니다. 지어낸 예가 아니라
            `bank` 의 E→I 대체 단이 하는 말과 같은 자리입니다.
        */}
        <p className="sm">
          이를테면 스스로는 <b>안으로 도는 쪽</b>이라 적었는데 글자는
          드러나는 쪽이면 — <b>사람을 만나고 온 날 지치는 것</b>이
          성격이 아니라 눌러 온 값일 수 있소. 그런 자리를 짚소.
        </p>
        <p className="sm">
          열에 넷은 안 적고 지나가오. 안 적으셔도 되오 —
          그때는 걸려 오신 것과 글자를 맞대 보겠소.
          <b> 여기까지 값은 안 받소.</b>
        </p>

        {/* ★ "모르오" 를 그리드 **위**로. a4 에서 이미 내린 판단을
            여기에도 적용합니다 — 훑는 순서상 아래에 두면 가장 늦게 보입니다. */}
        <button className="btn gh" style={{ marginBottom: 12 }}
                onClick={() => { s.set({ axis4: null }); go("a6"); }}>
          모르겠습니다 · 사주만으로 보겠습니다
        </button>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 5, margin: "14px 0" }}>
          {AXIS4.map((t) => (
            <button key={t} className={`op ${s.axis4 === t ? "on" : ""}`}
                    style={{ textAlign: "center", padding: "11px 2px",
                             fontFamily: "var(--mono)", fontSize: 12, letterSpacing: ".06em" }}
                    onClick={() => { s.set({ axis4: t }); go("a6"); }}>
              {t}
            </button>
          ))}
        </div>
        <Narration lines={["", "네 글자는 셈에 넣지 않는다.",
          "<em>사주와 어긋나는 자리</em>를 찾는 데만 쓴다."]} />
        {/* ★ 다음이 무엇인지 한 번도 안 불렀습니다. 넉 자를 고르든 안
              고르든 다음 자리는 하나입니다 — 글자가 서는 자리. */}
        <ActOut kind="딜레마" next="글자가 서다">
          넉 자는 <b>그대가 고른 답</b>이고, 여덟 글자는 <b>고를 수 없었던
          것</b>이오.<br />
          둘이 다 있으면 <b>어긋난 칸</b>부터 짚고, 넉 자가 없으면
          여덟 글자만으로 가오. 어느 쪽이든 다음은 글자가 서는 자리요.
        </ActOut>
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
      <Shell screen="a5" title="걸리는 것" onBack={back}>
        <Progress step={progressAt("a5")!} total={PROGRESS_TOTAL} />
        <Scene id="fork" />
        {/*
          ★ 글이 그림과 어긋나 있었습니다.

            여기 그림은 밤 들판의 갈림길입니다 — 등 셋과 팻말 셋.
            그런데 글은 「붓을 내려놓고, 그가 물었다」 였습니다. 실내에서
            붓을 내려놓는 장면인데 화면은 바깥입니다.

            손님은 둘 중 무엇을 믿을지 몰라 합니다. 그림을 다시 뽑는
            것보다 글을 맞추는 것이 싸고, 여기서는 글이 그림을 받아
            주는 편이 더 낫습니다 — 갈림길이 이 화면의 뜻입니다.
        */}
        <Narration lines={["길이 세 갈래로 갈리는 데서, 그가 물었다."]} />
        <Say who="도령" lens="pungun">
          {s.name ? `${s.name}. 무엇이 걸려서 예까지 왔소?` : "무엇이 걸려서 예까지 왔소?"}
        </Say>
        {/*
          ★ 여기가 68점이었습니다. 물음은 이 흐름에서 가장 좋은 한
            줄인데, **고르고 나면 무엇이 달라지는지**가 없었습니다.
            그래서 여섯 칸이 설문지처럼 보였습니다.
        */}
        <Say who="도령" lens="pungun">
          여기서 고른 하나가 뒤의 5마디를 다 바꾸오. 같은 8글자를 놓고도
          돈이 걸린 사람과 사람이 걸린 사람은 짚는 자리가 다르오.
          {" "}칸은 6개고, 고른 것은 뒤에서 바꿀 수 있소.
          <br />
          <b>여태 「뭐가 걸리냐」는 물음에 바로 답해 본 적이 없었을
          것이오.</b> 하나로 줄이면 나머지가 아닌 게 되어 버려서요.
          <br />
          그래도 하나만 고르시오. 안경알을 한 번에 하나만 끼우는
          것처럼, 8글자를 보는 자리도 한 번에 하나요.
          <br />
          6개 중 1개를 고르는 것이 여기서 할 일의 전부요.
          <br />
          고르기를 미루다 그냥 닫은 사람이 적지 않소. 그 자리에서
          참고 지나가면 뒤의 5마디가 아무 데도 안 걸리오.
        </Say>
        <Narration lines={["", "한참 답이 나오지 않았다.", "하나만 고르라면—"]} />
        <div className="og c2">
          {CONCERNS.map((c) => (
            <button key={c.id} className={`op ${s.concern === c.id ? "on" : ""}`}
                    onClick={() => { s.set({ concern: c.id as Concern }); go("a3"); }}>
              <b>{c.label}</b><span>{c.sub}</span>
            </button>
          ))}
        </div>
        <p className="sm mt">
          고르신 것이 <b>여덟 글자</b>의 어느 자리를 볼지 정하오.
          바꾸시려면 왼쪽 위 <b>←</b> 로 돌아오면 되오.
          <b> 여기까지 값은 안 받소.</b>
        </p>
        <ActOut kind="뒤집기" next="글자가 서다">
          미리 말해 두겠소. <b>넉 자와 여덟 글자는 자주 어긋나오.</b><br />
          어긋난다고 검사가 틀린 것도, 글자가 틀린 것도 아니오 —
          <b>넉 자는 그대가 스스로 고른 답이고, 여덟 글자는 고를 수
          없었던 것</b>이오. 그 틈에 할 말이 있소.
        </ActOut>
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
      <Shell screen="a6" title="글자가 서다" onBack={back}>
        <Scene id="altar" />
        {busy && <Narration lines={["도령이 종이를 폈다.", "붓이 움직인다."]} />}
        {error && (
          <>
            <Say who="도령" lens="pungun">{error}</Say>
            {/* ★ 여기가 막다른 길이었습니다.
                '다시 세운다' 는 같은 값으로 재시도만 해서, 잘못 적은
                사람은 영영 빠져나올 수 없었습니다. 고치러 갈 길을 냅니다. */}
            <button className="btn" onClick={() => go("a3")}>
              날을 고쳐 적겠습니다
            </button>
            <button className="btn gh" onClick={() => void buildChart()}>
              다시 세워 보겠습니다
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
              다 됐습니다 · 건너뛰겠습니다
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
            {/*
              ★ 여기가 73점이었습니다. 여덟 글자가 서는 자리인데,
                **선 것을 보고 있는 사람 얘기**가 없었습니다. 표만
                뜨고 근거 줄도 없었습니다.
            */}
            <span className="src">
              근거 · 기둥 4자리 · 글자 8개 ·
              절입(節入, 계절이 바뀌는 마디에 드는 시각)까지 재어 세운
              것이오 · 때를 모르시면 6글자로 섭니다
            </span>
            <Say who="도령" lens="pungun">
              그대의 8글자가 섰소. 이 여덟은 오늘 바뀌지 않고, 내일도
              바뀌지 않소.
              <br />
              <b>여태 이 글자를 한 번도 제 눈으로 본 적이 없었소.</b>
              {" "}어디선가 풀이만 듣고 나왔지, 무엇을 보고 한 말인지는
              못 물어봤을 것이오. 물어보려다 참은 자리요.
              <br />
              그래서 표를 먼저 내오. 자를 대기 전에 자를 보여 주는
              것처럼, 셈에 쓴 것부터 펴 놓소.
            </Say>
            <Pillars f={s.features} />

            {/*
              ★ 다른 만세력과 갈릴 수 있는 자리는 **우리가 먼저** 말합니다.

                손님은 다른 만세력과 대 봅니다. 백 명 중 **스물여덟**이
                다르게 나옵니다 (tools/divergence.py — 고을 보정 23.7명 ·
                밤 11시대 4.0명 · 절입 언저리 0.1명).

                ★ 여기 「넷다섯」 이라 적혀 있었습니다. 셋 중 **가장 흔한**
                  고을 보정을 아예 안 세고 있었기 때문입니다. 그래서
                  1993-11-25 13:00 서울 손님에게 「갈리는 자리 없음」 으로
                  잠자코 있었습니다 — 우리는 壬午, 저쪽은 癸未인데요.

                그때 「우리가 맞소」 도 「그쪽이 맞소」 도 답이 아닙니다.
                갈리는 자리는 **계산이 아니라 선택**이기 때문입니다.

                발견당하면 「틀린 집」이 되고, 먼저 말하면 「아는 집」이
                됩니다. 같은 사실인데 순서가 다릅니다.

                저쪽 답까지 적습니다 — 감추면 숨긴 것이 됩니다.
            */}
            {s.divergence?.cases?.map((c, i) => (
              <div className="fork8" key={i}>
                <div className="lab">여기는 집마다 갈리는 자리요</div>
                <p className="sm">{c.why}. 그래서 <b>{c.moved.join(" · ")}</b>가
                  달라질 수 있소.</p>
                <table className="forkt">
                  <tbody>
                    <tr className="on">
                      <td>이 집</td>
                      <td>{c.ours}</td>
                      <td className="gz">{c.mine}</td>
                    </tr>
                    <tr>
                      <td>다른 집</td>
                      <td>{c.theirs}</td>
                      <td className="gz">{c.alt}</td>
                    </tr>
                  </tbody>
                </table>
                <p className="sm">
                  둘 다 명리에서 쓰는 법이오. 어느 쪽이 맞다고는 안 하오 —
                  <b> 이 집은 위엣것으로 봅니다.</b> 다른 만세력과 대 보고
                  다르거든, 틀린 게 아니라 여기서 갈린 것이오.
                </p>
              </div>
            ))}

            {/*
              ★ 값 없이 줄 수 있는 것 중 가장 센 한 줄.

                여기까지 손님이 받은 것은 **자기 여덟 글자**뿐입니다.
                그건 숫자가 아니라 글자라 「그래서 뭐」 로 끝납니다.
                희소도는 다릅니다 — 「1만 명에 165명」 은 자기 자리를
                단번에 알려 주고, 그 다음이 궁금해집니다.

                ★ 지어낸 숫자가 아닙니다. 표는 4만 명을 세어 만듭니다
                  (tools/make_rarity.py). 표가 없거나 낡았으면 서버가
                  아무것도 안 보내고, 여기는 조용히 접힙니다.

                ★ 「드물다」 고만 말하지 않습니다. 흔하면 흔하다고
                  합니다 — 골라 담으면 누구나 드물어집니다.
            */}
            {s.rarity && (
              <div className="rare">
                <div className="lab">이 배치를 가진 사람</div>
                <p className="rarebig">
                  <b>{s.rarity.words}</b>
                  <em>{s.rarity.band}</em>
                </p>
                {s.rarity.ilju && (
                  <p className="sm">
                    그중 <b>{s.rarity.ilju_gz}</b> 일주(그대를 가리키는
                    두 글자)는 {s.rarity.ilju}요.
                  </p>
                )}
                <p className="sm rarenote">
                  사람 4만을 세어 만든 표요. 맞힌다는 말이 아니라
                  <b> 몇 명인지</b> 센 것이오.
                </p>
              </div>
            )}

            <Summary f={s.features} />
            <ElementBar f={s.features} />

            {/* ★ 쓰던 만세력과 나란히 놓고 볼 수 있게. 모양이 다르면
                한 줄씩 눈으로 옮겨 가며 견줘야 하고, 그러다 지칩니다. */}
            <ManseTable f={s.features} />
            <CalcPanel f={s.features} />
            {/*
              ★ 여기가 「셈이 끝났다」로 끝나고 있었습니다. 셈은 끝났지만
                **해석은 한 마디도 안 했습니다.** 그걸 말해 줘야 다음이
                궁금해집니다 — 끝난 일보다 안 끝난 일이 오래 남습니다.
            */}
            <ActOut kind="끊긴 동작" next="왜 하필 지금">
              여덟 글자가 다 섰소. <b>아직 아무 말도 안 했소.</b><br />
              여기까지는 <b>재는 일</b>이오 — 옷감을 펴 놓고 치수만
              적은 셈이오. 마름질은 지금부터요.<br />
              {s.features?.hour_known
                ? <>때를 아셨으니 <b>여덟</b> 글자가 다 섰소.</>
                : <>때를 모르신다 하여 <b>시주(時柱, 태어난 시각의 두
                    글자)</b>는 안 세웠소. <b>여섯</b> 글자로 보겠소.</>}
            </ActOut>
            <button className="btn mt" onClick={() => go("a7")}>
              무슨 말인지 듣겠습니다
            </button>
          </>
        )}
      </Shell>
    );
  }

  /* a7 · 훅 5단 — 값은 아직 묻지 않는다 */
  return (
    <Shell screen="a7" title="도령이 말하다" onBack={back}>
      {/* ★ 진행 막대를 뗐습니다. 결과가 보상인 구간에서 막대는 남은
          보상이 아니라 **남은 노동**을 강조합니다. */}
      <Scene id="facing" />
      {!segments && !error && <Narration lines={["도령이 종이를 들여다본다."]} />}

      {/*
        ★ 훅이 아무 설명 없이 대뜸 시작하고 있었습니다.
          손님은 "이현석. 모으기는 하는데 그걸로 뭘 할지가 없다." 를
          갑자기 만납니다. 이게 무슨 화면인지, 왜 이런 말을 하는지,
          「그렇소/아니오」가 무엇을 하는지 아무 데도 없었습니다.

          찌르기의 세기를 죽이지 않으면서 **무엇이 벌어질지만** 먼저
          한 줄로 말합니다. 값은 여기서 안 묻습니다.
      */}
      {segments && (
        <div className="hookintro">
          {/*
            ★ 무엇에 대한 말인지가 없었습니다.

              손님은 앞에서 고민을 골랐는데(돈·일·사랑…), 훅에 들어오면
              그 말이 어디로 갔는지 안 보입니다. 그래서 갑자기 자기
              얘기가 시작되는데 **뭐에 대한 건지 모르는 채로** 읽습니다.
              「무슨 말인지 모르겠다」 는 말이 나온 자리입니다.

              고른 것을 먼저 되짚습니다. 되짚는 것만으로도 「내 말을
              들었구나」 가 됩니다.
          */}
          {/* ★ 첫 줄이 설명이었습니다. 손을 놓는 동작 하나로 엽니다. */}
          <Narration lines={["도령이 종이에서 눈을 뗐다."]} />
          <p>
            <b>{CONCERNS.find((c) => c.id === s.concern)?.label ?? "걸리는 것"}</b>
            에 대해서요. 여기서부터 <b>5마디</b>요.<br />
            기둥 4자리를 옮긴 8글자만 보고 하는 말이오 —
            이름도 사연도 안 들었소.
          </p>
          <p>
            {/*
              ★ 「아니오」 가 무엇을 하는지 말은 했는데, 그게 어떤 일인지는
                그림이 안 그려졌습니다. 실제로 두 번 어긋나면 2단이 축을
                바꿉니다 (`bank.TURN_AT`). 그걸 손에 잡히게 적습니다.
            */}
            한 마디가 끝날 때마다 <b>맞는지 물어보겠소.</b> 맥을 짚듯
            자리를 옮겨 가며 짚는 셈이오. <b>두 번</b> 어긋나면 짚는
            자리를 아예 바꾸오. 값은 아직 안 묻소.
          </p>
        </div>
      )}
      {error && <Say who="도령" lens="pungun">{error}</Say>}
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
            남은 자리에는 <b>왜 하필 지금</b>과 <b>언제 바뀌는가</b>가 있소.
          </p>

          {/*
            ★ 여기까지 「안 하면 무엇을 잃는가」 가 한 줄도 없었습니다.
              여덟 화면 전부에서 0 이었습니다 (tools/persuasion_audit.py).

              사람은 얻는 것보다 잃는 것에 두 배쯤 민감합니다. 「남은
              자리에는 …가 있소」 는 얻는 말이라 안 눌러도 그만입니다.

              ★ 다만 **앞을 깎지 않습니다.** 「셋으로만 본 것」 같은 말은
                방금 좋았다고 느낀 손님에게 8분의 3짜리였다고 말하는
                셈입니다. 대신 **그 사람의 실제 수**를 하나 박습니다 —
                다음 대운이 바뀌는 나이. 지어낸 말이 아니라 셈에서 나온
                값이고, 그 해에 무슨 일이 난다고는 말하지 않습니다.
                바뀌는 때만 셉니다.
          */}
          {nextTurn && (
            <p className="tx losing">
              그대의 다음 고비는 <b>{nextTurn}살</b>이오.
              지금 나가면 그게 <b>왜 그때인지</b> 모른 채로 지나가오.
            </p>
          )}
          {/*
            ★ 여기가 당김 0점이던 자리입니다. 손님이 가장 오래 머물고
              (「그렇소/아니오」를 다섯 번) 결제 갈림길이 바로 뒤인데,
              다섯 단이 끝나면 그냥 끝났습니다.

              앞을 깎지 않고 **안 한 말**로 끊습니다 — 다섯을 했다는
              것은 참이고, 이름 붙은 자리를 아직 안 했다는 것도 참입니다.
          */}
          <ActOut kind="남긴 물음" next="없는 것부터">
            다섯 마디를 했소. 다 <b>여덟 글자 겉</b>에서 한 말이오.<br />
            <b>정작 없는 것은 아직 안 셌소.</b> 그건 어디서 채우겠소?
          </ActOut>
          <button className="btn mt" onClick={() => router.push("/pay?step=d0")}>
            값 없이 내 것을 한 겹 더
          </button>
          <button className="btn gh" onClick={() => router.push("/pay?step=d1")}>
            어디까지 볼지 고르겠습니다
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
