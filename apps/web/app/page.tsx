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
import CompanionCat from "@/components/CompanionCat";
import GuideIntro from "@/components/GuideIntro";
import Fold from "@/components/Fold";
import { track, useScreen } from "@/lib/track";
import { exposeEntry } from "@/lib/experiment";
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
import { iga } from "@/lib/josa";
import { SEASON_PALETTE } from "@/components/scene/manifest";
import type { Features, HookSegment } from "@shared/chart";

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
/*
 * ★ 계절 문장도 **두 줄로** 줄였습니다 (2026-09-06).
 *
 *   가운데 줄(「마당에 낙엽이 쌓였고,」)은 냄새와 열린 문 사이를
 *   잇는 말인데, 앞뒤 두 줄이 이미 그 자리를 세웁니다. 대문에서
 *   손님이 읽는 것은 **분위기 한 번 · 열린 문 하나**입니다.
 */
const OPENING: Record<string, string[]> = {
  spring: ["담장 위로 벚꽃이 넘어와 있었다.", "대문은 열려 있었다."],
  summer: ["비가 막 그친 밤이었다.", "대문은 열려 있었다."],
  autumn: ["국화 냄새가 났다.", "대문은 열려 있었다."],
  winter: ["눈이 소리 없이 내리고 있었다.", "문은 열려 있었다."],
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

/*
 * 태어난 고을 — ★ 고을 열일곱은 **경도표**지 행정구역이 아닙니다 (2026-09-04).
 *
 *   `calendar.CITY_LON` 이 이 열일곱의 경도만 들고 있고, 하는 일은 진태양시
 *   보정 하나입니다. 그런데 화면에는 이름만 나열돼 있어서, 경기도에서 난
 *   사람이 제 고을을 찾다가 목록에 없다고 봅니다 — 인구가 가장 많은
 *   광역단체입니다. 수원이 거기 있는데도 못 찾습니다.
 *
 *   경도를 늘리지 않고 **묶음 이름만** 답니다. 성남·고양을 넣어 봐야
 *   서울과 0.1° (24초) 차이라 시주가 갈리지 않습니다 — 없는 정밀도를
 *   있는 것처럼 보이게 할 뿐입니다.
 */
const CITY_GROUPS: [string, string[]][] = [
  ["서울", ["서울"]],
  ["경기·인천", ["인천", "수원"]],
  ["강원", ["춘천", "강릉"]],
  ["충청·세종", ["대전", "청주"]],
  ["전라", ["전주", "광주", "목포"]],
  ["경북", ["대구", "안동", "포항"]],
  ["경남·부산·울산", ["부산", "울산", "창원"]],
  ["제주", ["제주"]],
];
const CITIES = CITY_GROUPS.flatMap(([, cs]) => cs);

/*
 * 화면 순서. ★ 고민(a5)이 이름(a2) 바로 뒤로 올라왔습니다.
 *   id 는 그대로 둡니다 — 계측 화이트리스트와 docs/08 이 이 이름을 씁니다.
 */
const ORDER: Step[] = ["a1", "a5", "a3", "a4", "a6", "a7", "a2", "a4b"];
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
const PROGRESS_TOTAL = 3;
function progressAt(step: Step): number | null {
  return ({ a5: 1, a3: 2, a4: 3 } as Partial<Record<Step, number>>)[step] ?? null;
}

function EntryInner() {
  const [entryArm, setEntryArm] = useState<number | null>(null);
  const router = useRouter();
  const params = useSearchParams();
  const s = useSession();
  // 관리자 레일이 ?step=a5 로 바로 건너뛸 수 있게 한다
  const asked = params.get("step") as Step | null;
  const [step, setStep] = useState<Step>(
    asked && STEPS.includes(asked) ? asked : "a1");
  /* 지나온 자리. 주소가 맨 앞으로 돌아가면 이것도 비웁니다. */
  const [trail, setTrail] = useState<Step[]>([]);

  /*
   * ★ 주소가 곧 자리요 — **없으면 맨 앞**입니다 (2026-09-05).
   *
   *   전에는 `?step=` 이 있을 때만 따라갔습니다. 그래서 `/?step=a7`
   *   에서 `router.push("/")` 를 하면 — 같은 길이라 화면이 다시
   *   그려지지 않고, `step` 은 화면이 들고 있는 값이라 아무도 안
   *   되돌려서 — 훅 5단에 그대로 서 있었습니다.
   *
   *   손님이 짚었습니다 — "맨 처음 화면으로 가야 하는데 중간지점으로
   *   가는 포인터가 있어."
   *
   *   여기가 뿌리입니다. 이렇게 두면 어디서 `/` 로 밀든 맨 앞으로
   *   갑니다.
   */
  useEffect(() => {
    if (asked && STEPS.includes(asked)) {
      setStep(asked);
    } else if (!asked) {
      setStep("a1");
      setTrail([]);
    }
  }, [asked]);

  /*
   * ★ 굴려 내린 뒤에는 대문이 클릭을 안 먹습니다 (2026-09-06).
   *
   *   대문은 그림 아무 데나 눌러도 다음으로 갑니다. 좋은 일인데,
   *   넓은 화면에서는 대문이 `position: fixed` 로 창에 **계속 남습니다.**
   *   그래서 아래 여섯 문답을 읽으러 굴려 내린 사람이 문답 상자
   *   바깥(좌우 여백)을 누르면 읽던 자리가 통째로 사라지고 이름 칸이
   *   떴습니다. 손님은 「나중에」를 눌렀는데 영구 제외였던 자리와
   *   같은 병입니다 — **레이블과 결과가 어긋납니다.**
   *
   *   반 창을 넘게 내렸으면 손님은 읽으러 내려온 것입니다. 그때는
   *   대문이 배경으로 물러섭니다. 「내 운명을 확인하겠습니다」 는
   *   제 손잡이가 따로 있어 그대로 듣습니다.
   *
   *   ★ 문턱을 **반 창**으로 잡은 까닭 — 문답은 한 창 아래에
   *     앉습니다(overrides.css `.gatedoubt`). 반 창까지는 아직 대문만
   *     보이는 자리라 눌러서 넘어가는 것이 맞습니다.
   */
  const [gateRead, setGateRead] = useState(false);
  useEffect(() => {
    if (step !== "a1") { setGateRead(false); return; }
    const on = () => setGateRead(window.scrollY > window.innerHeight * 0.5);
    on();
    window.addEventListener("scroll", on, { passive: true });
    window.addEventListener("resize", on);
    return () => {
      window.removeEventListener("scroll", on);
      window.removeEventListener("resize", on);
    };
  }, [step]);
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
    /*
     * ★ `scroll: false` 는 그대로 둡니다.
     *
     *   여기서 next 로 올리면 주소가 바뀔 때마다 브라우저가 한 번,
     *   Shell 이 또 한 번 올려 두 번 뜁니다. 맨 위로 올리는 일은
     *   `Shell` 한 자리가 맡습니다 (화면 이름이 바뀔 때).
     */
    router.replace("/?step=" + next, { scroll: false });
  };
  const back = trail.length
    ? () => {
        setTrail((t) => t.slice(0, -1));
        setStep(trail[trail.length - 1]);
        router.replace("/?step=" + trail[trail.length - 1], { scroll: false });
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
  const [error, setError] = useState<string | null>(null);
  const [hookRetry, setHookRetry] = useState(0);
  const [segments, setSegments] = useState<HookSegment[] | null>(null);
  const [hookDone, setHookDone] = useState(false);
  /* 「아니오」가 몇 번 나왔는가 · 이미 방향을 틀었는가 */
  const [misses, setMisses] = useState(0);
  const [turned, setTurned] = useState(false);

  // 화면 이름이 곧 step 입니다. 어디서 나가는지 이걸로 셉니다.
  useScreen(step);
  useEffect(() => { if (step === "a1") setEntryArm(exposeEntry()); }, [step]);

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
      setError(e instanceof ApiError && e.status < 500
        ? (birthMessageFrom(raw) ?? raw)
        : "계산 서버에 연결하지 못했어요. 입력은 그대로 남아 있으니 잠시 후 다시 계산해 주세요.");
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
    if (step === "a6" && s.features) {
      track("chart_completed", "a6");
    }
  }, [step, s.features]);

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
  }, [step, s.chartId, s.concern, s.axis4, s.name, s.cur, segments, misses, hookRetry]);

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
    return (
      <Shell screen="a1" bare>
        <div className={`gatehero${gateRead ? " read" : ""}`}>
          <Scene id="gate" className="fill" bleed />
          <div className="gatecopy">
            <p className="conversion-kicker">성신당 星辰堂 · 사주로 읽는 나의 반복 패턴</p>
            <h1 className="conversion-title">왜 나는 비슷한 일에서<br />자꾸 마음이 걸릴까.</h1>
            <p className="conversion-lead">태어난 정보와 지금의 고민을 바탕으로,<br />반복되는 패턴과 오늘 해볼 행동을 읽어보세요.</p>
            <GuideIntro />
            <button className="btn mt" onClick={() => { s.set({cur:"pungun"}); go("a5"); }}>내 고민으로 무료 해석 보기</button>
            <p className="conversion-note">{entryArm === 1 ? "무료 해석과 오늘 해볼 행동 하나 · 시간은 몰라도 돼요" : "첫 해석 무료 · 태어난 시간은 몰라도 돼요"}</p>
            <p className="conversion-note">전통 사주를 바탕으로 한 자기 이해 콘텐츠예요.</p>
          </div>
        </div>
        <div className="gatedoubt"><Doubts compact first={null} /></div>
      </Shell>
    );
  }

  if (step === "a2") {
    return <Shell screen="a2" title="별칭 · 선택" onBack={back}>
      <h1 className="conversion-title">어떻게 불러드릴까요?</h1>
      <p className="conversion-lead">별칭은 해석에서 부르는 말에만 사용해요. 사주 계산에는 쓰지 않으며, 비워두셔도 괜찮아요.</p>
      <label htmlFor="entry-alias">별칭 (선택, 최대 12글자)</label>
      <input id="entry-alias" className="fld" maxLength={12} value={s.name} onChange={e => s.set({ name: e.target.value })} />
      <button className="btn mt" onClick={() => go("a4")}>이 별칭으로 이어가기</button>
      <button className="btn gh" onClick={() => { s.set({ name: "" }); go("a4"); }}>별칭 없이 이어가기</button>
    </Shell>;
  }

  if (step === "a3") {
    const filled = s.year !== null && s.month !== null && s.day !== null;
    const bad = filled ? birthProblem(s.year,s.month,s.day) : null;
    const minor = filled && !bad && needsGuardian(s.year!,s.month!,s.day!);
    return <Shell screen="a3" title="태어난 정보" onBack={back}>
      <Progress step={2} total={PROGRESS_TOTAL} />
      <div className="conversion-intro"><p className="conversion-kicker">2 / 3 · 태어난 정보</p>
        <h1 className="conversion-title">해석에 필요한 정보를<br />알려주세요.</h1>
        <p className="conversion-lead">양력 생년월일을 입력해 주세요. 음력 생일은 양력으로 바꿔 입력해 주세요.</p></div>
      <div className="f3">
        {([['year','태어난 해',4,'1993'],['month','월',2,'11'],['day','일',2,'25']] as const).map(([key,label,max,placeholder]) =>
          <div key={key}><label htmlFor={`birth-${key}`}>{label}</label>
            <input id={`birth-${key}`} className="fld" inputMode="numeric" maxLength={max} placeholder={placeholder}
              aria-invalid={!!bad} aria-describedby={bad ? "birth-error" : undefined}
              value={s[key] ?? ""} onChange={e => {const value=e.target.value.replace(/[^0-9]/g, "").slice(0,max);
                s.set({ [key]: value === "" ? null : Number(value), features:null, chartId:null }); setError(null); }} />
          </div>)}
      </div>
      {bad && <p className="warn" id="birth-error" role="alert">{bad}</p>}
      {minor && <p className="warn" role="alert">만 14세 미만은 보호자 동의 절차가 필요해 현재 서비스를 이용할 수 없어요.</p>}
      <div className="conversion-card"><label htmlFor="birth-city">태어난 지역</label>
        <select id="birth-city" className="fld" value={s.city} onChange={e => s.set({ city:e.target.value, features:null, chartId:null })}>
          {CITY_GROUPS.map(([g,cs]) => <optgroup key={g} label={g}>{cs.map(c => <option key={c} value={c}>{c}</option>)}</optgroup>)}
        </select><p className="conversion-note">현재 {s.city} 기준이에요. 출생지는 태어난 시간의 지역 보정에 사용합니다.</p>
      </div>
      <p className="conversion-note">성별은 전통 명리의 대운 방향을 계산하는 데 사용해요.</p>
      {!s.sexSet && <p className="conversion-note">여성·남성 중 하나를 선택해 주세요.</p>}
      <div className="og c2">{([['F','여성'],['M','남성']] as const).map(([value,label]) =>
        <button className={`op ${s.sexSet && s.sex === value ? 'on' : ''}`} key={value} aria-pressed={s.sexSet && s.sex === value}
          onClick={() => s.set({ sex:value, sexSet:true, features:null, chartId:null })}>{label}</button>)}
      </div>
      <button className="btn mt" disabled={!filled || !!bad || !!minor || !s.sexSet} onClick={() => go("a4")}>태어난 시간으로 이어가기</button>
      <p className="conversion-note">시간을 모르면 다음 화면에서 ‘시간을 몰라요’를 선택할 수 있어요. <a href="/legal">개인정보 처리 안내</a></p>
    </Shell>;
  }

  if (step === "a4") {
    return (
      <Shell screen="a4" title="태어난 시간" onBack={back}>
        <Progress step={3} total={PROGRESS_TOTAL} />
        <div className="conversion-intro">
          <p className="conversion-kicker">3 / 3 · 태어난 시간</p>
          <h1 className="conversion-title">아는 만큼만<br />알려주셔도 돼요.</h1>
          <p className="conversion-lead">시간을 알면 시주까지 계산하고, 모르면 시주를 제외한 범위에서 해석해요.</p>
        </div>
        <div className="conversion-time conversion-card">
          <div className="f3 hm">
            <div><label htmlFor="birth-hour">시 (0–23)</label>
              <input id="birth-hour" className="fld" inputMode="numeric" maxLength={2} placeholder="15"
                value={s.hourKnown && s.hour !== null ? s.hour : ""}
                onChange={(e) => { const value=e.target.value.replace(/[^0-9]/g, "").slice(0,2);
                  s.set({ hourKnown: true, hour: value === "" ? null : Math.min(23, Number(value)), features: null, chartId: null }); }} />
            </div>
            <div><label htmlFor="birth-minute">분 (0–59)</label>
              <input id="birth-minute" className="fld" inputMode="numeric" maxLength={2} placeholder="00"
                value={s.minute ?? ""}
                onChange={(e) => { const value=e.target.value.replace(/[^0-9]/g, "").slice(0,2);
                  s.set({ minute: value === "" ? 0 : Math.min(59, Number(value)), features: null, chartId: null }); }} />
            </div>
          </div>
          {s.hourKnown && s.hour !== null && <p className="conversion-note">{clockWord(s.hour, s.minute ?? 0)}에 태어난 것으로 계산해요. 오후 3시는 15로 적어주세요.</p>}
          <button className="btn mt" disabled={!s.hourKnown || s.hour === null}
            onClick={() => go("a6")}>이 시간으로 무료 해석 보기</button>
        </div>
        <button className="btn gh" onClick={() => {
          s.set({ hourKnown: false, hour: null, minute: 0, chartId: null, features: null }); go("a6");
        }}>시간을 몰라요 · 시주 없이 보기</button>
        <CompanionCat message="모르는 시간을 추측해서 채우지 않아도 괜찮아요." />
        <details className="conversion-details"><summary>별칭·성향도 추가하고 싶어요</summary>
          <p className="conversion-note">선택 정보예요. 비워 두어도 무료로 볼 수 있어요.</p>
          <button className="btn gh" onClick={() => go("a2")}>별칭 입력</button>
          <button className="btn gh" onClick={() => go("a4b")}>성향 4글자 선택</button>
        </details>
      </Shell>
    );
  }

  if (step === "a4b") {
    return <Shell screen="a4b" title="성향 4글자 · 선택" onBack={back}>
      <h1 className="conversion-title">내가 생각하는 성향도<br />비교해볼까요?</h1>
      <p className="conversion-lead">직접 고른 성향과 전통 사주 해석을 비교하는 선택 항목이에요. 사주 계산값은 바뀌지 않아요.</p>
      <div className="og c2">{AXIS4.map(t => <button key={t} className={`op ${s.axis4===t ? 'on' : ''}`}
        aria-pressed={s.axis4===t} onClick={() => s.set({ axis4:t })}>{t}</button>)}</div>
      <button className="btn mt" disabled={!s.axis4} onClick={() => go("a4")}>선택한 성향으로 이어가기</button>
      <button className="btn gh" onClick={() => { s.set({ axis4:null }); go("a4"); }}>성향 없이 이어가기</button>
      <p className="conversion-note">본 서비스의 성향 검사는 특정 상표의 검사가 아닙니다.</p>
    </Shell>;
  }

  if (step === "a5") {
    return (
      <Shell screen="a5" title="지금의 고민" onBack={back}>
        <Progress step={1} total={PROGRESS_TOTAL} />
        <div className="conversion-intro">
          <p className="conversion-kicker">1 / 3 · 고민 선택</p>
          <h1 className="conversion-title">지금 가장 알고 싶은 건<br />무엇인가요?</h1>
          <p className="conversion-lead">지금 마음에 걸리는 것 하나를 골라주세요. 선택한 고민에 따라 해석에서 살펴볼 자리가 달라져요.</p>
        </div>
        <div className="og c2">
          {CONCERNS.map((c) => (
            <button key={c.id} className={`op ${s.concernSet && s.concern === c.id ? "on" : ""}`}
              aria-pressed={s.concernSet && s.concern === c.id}
              onClick={() => s.set({ concern: c.id as Concern, concernSet: true })}>
              <b>{c.label}</b><span>{c.sub}</span>
            </button>
          ))}
        </div>
        <CompanionCat state={s.concernSet ? "selected" : "rest"}
          message={s.concernSet ? "좋아요. 이 고민부터 살펴봐요." : "오늘 마음에 걸린 것부터 살펴봐요."} />
        <button className="btn mt" disabled={!s.concernSet} onClick={() => go("a3")}>이 고민으로 이어가기</button>
      </Shell>
    );
  }

  if (step === "a6") {
    return <Shell screen="a6" title="명식 계산" onBack={back}>
      <Scene id="altar" />
      {error && <div className="warn" role="alert"><p>{error}</p>
        <button className="btn gh" onClick={() => go("a3")}>입력 정보 수정하기</button>
        <button className="btn gh" disabled={busy} onClick={() => void buildChart()}>다시 계산하기</button>
      </div>}
      {!s.features && !error && <p className="conversion-lead" role="status">명식을 계산 중이에요.</p>}
      {s.features && <>
        <p className="conversion-kicker">명식 계산 완료</p>
        <h1 className="conversion-title">이제, 지금의 고민과<br />함께 읽어볼게요.</h1>
        <p className="conversion-note">{s.features.hour_known ? "태어난 시간까지 네 기둥을 계산했어요." : "태어난 시간을 몰라 시주를 제외한 세 기둥으로 읽어요."}</p>
        <p className="conversion-note">다음은 {lens.name}의 첫 해석이에요. 입력한 고민을 바탕으로 다섯 가지 질문을 차례로 살펴봐요.</p>
        <Pillars f={s.features} />
        <p className="conversion-note">명식은 태어난 해·달·날·시간을 각각 두 글자로 옮긴 것이에요.<br />모르는 시간의 두 글자는 비워 둡니다.</p>
        <button className="btn mt" onClick={() => go("a7")}>내 고민의 무료 해석 읽기</button>
        <details className="conversion-details"><summary>계산 근거와 보정 내역 보기</summary>
          <ManseTable f={s.features} /><CalcPanel f={s.features} />
          {s.divergence?.cases?.map((c,i) => <div key={i} className="conversion-note">
            <p>{c.why}</p><p>이 서비스: {c.ours}<br />{c.mine}</p>
            <p>다른 계산 방식: {c.theirs}<br />{c.alt}</p>
            <p>이 서비스는 위의 첫 번째 명식으로 해석해요.</p>
          </div>)}
        </details>
      </>}
    </Shell>;
  }

  /* a7 · 훅 5단 — 값은 아직 묻지 않는다 */
  return (
    <Shell screen="a7" title={`${lens.name} · 첫 해석`} onBack={back}>
      {/* ★ 진행 막대를 뗐습니다. 결과가 보상인 구간에서 막대는 남은
          보상이 아니라 **남은 노동**을 강조합니다. */}
      <Scene id="facing" />
      {!segments && !error && <Narration lines={[`${lens.name}, 선택한 고민과 명식을 함께 살펴본다.`]} />}

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
          <Narration lines={[`${lens.name}의 첫 해석이 준비됐다.`]} />
          {/*
            ★ 여는 말에만 얼굴이 없었습니다 (2026-09-07).

              훅 다섯 단은 `HookSegments` 가 `Say` 로 그려 초상이
              붙는데, **그 앞의 여는 말 넉 줄만** 맨 `<p>` 였습니다.
              손님 화면에서는 「도령이 종이에서 눈을 뗐다」 다음에
              말하는 사람 없이 글만 나왔습니다.

              이 집이 파는 것은 해석이 아니라 **그 사람**입니다.
              말을 시작하는 자리에 얼굴이 없으면 그냥 안내문입니다.

            ★ `Say` 는 `<br />` 에서 마디를 끊고 **첫 마디에만** 얼굴을
              답니다. 한 말풍선에 넉 줄을 붓지 않으려는 자리라
              (`.\dev.ps1 say`), 문단 사이도 `<br />` 로 넘깁니다.

            ★ 「아니오」 가 무엇을 하는지 — 두 번 어긋나면 2단이 축을
              바꿉니다 (`bank.TURN_AT`). 그걸 손에 잡히게 적습니다.
          */}
          <Say who={lens.name} lens={lens.id}>
            <b>{CONCERNS.find((c) => c.id === s.concern)?.label ?? "걸리는 것"}</b>
            에 대해서요. 여기서부터 <b>5마디</b>요.<br />
            {s.hourKnown ? "기둥 4자리의 8글자" : "시주를 제외한 기둥 3자리의 6글자"}를 보고 하는 해석이오 —
            선택한 고민에 맞춰 살펴보겠소.<br />
            한 마디가 끝날 때마다 맞는지 물어보겠소. 맥을 짚듯
            자리를 옮겨 가며 짚는 셈이오.<br />
            <b>두 번</b> 어긋나면 짚는 자리를 아예 바꾸오.
            값은 아직 안 묻소.
          </Say>
        </div>
      )}
      {error && <><Say who="도령" lens="pungun">{error}</Say><button className="btn" onClick={() => {setError(null); setHookRetry(n => n + 1);}}>무료 해석 다시 불러오기</button></>}
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
        <section className="conversion-card">
          <h2>내 경험과 가까웠던 장면이 있나요?</h2>
          <p className="conversion-lead">이어지는 무료 해석에서 근거를 더 살펴보고, 오늘 해볼 행동 하나를 가져가세요.</p>
          <button className="btn mt" onClick={() => router.push("/pay?step=d0")}>무료 해석과 오늘의 행동 보기</button>
          <button className="btn gh" onClick={() => router.push("/summary")}>여기까지 본 내용 정리하기</button>
        </section>
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
