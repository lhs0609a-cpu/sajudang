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
import RestHere from "@/components/RestHere";
import CompanionCat from "@/components/CompanionCat";
import GuideIntro from "@/components/GuideIntro";
import Fold from "@/components/Fold";
import { ConcernArtwork, ConcernReminder } from "@/components/ConcernArtwork";
import { ArtImage, BirthStructure } from "@/components/ReadingArtwork";
import { track, useScreen } from "@/lib/track";
import { exposeEntry } from "@/lib/experiment";
import { ageNow, birthMessageFrom, birthProblem, livedDays } from "@/lib/birth";
import { needsGuardian } from "@/lib/biz";
import Scene from "@/components/scene/Scene";
import { Narration, Progress, Say } from "@/components/Narration";
import { CalcPanel, ElementBar, elementBrief, ManseTable, Pillars, Summary } from "@/components/Chart";
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
 * ★ 여기가 만 명이 들어오는 문인데 심리 장치가 하나뿐이었소
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
 *   가장 흔한 실수는 **오후를 12시간 빼고 적는 것**이오. 오후 3시
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
 * 태어난 고을 — ★ 고을 열일곱은 **경도표**지 행정구역이 아니오 (2026-09-04).
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
const ORDER: Step[] = ["a1", "a5", "a3", "a4", "a4b", "a6", "a7", "a2"];
const STEPS: Step[] = ORDER;

/*
 * 진행 표시.
 *
 * ★ a1 에서 이미 한 단계를 지나 놓고도 a2 가 1/7 이었습니다. 손님
 *   입장에서는 **이미 한 수고가 0으로 리셋**됩니다. 여기서는 거짓말도
 *   필요 없소 — 실제로 한 단계를 지났소.
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
   *       ① 시·분을 적는다        ← 기본. 적은 그대로 셈하오
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
  useEffect(() => {
    setSegments(null);setHookDone(false);setMisses(0);setTurned(false);
  }, [s.chartId,s.concern,s.cur]);

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
        : "계산 서버에 연결하지 못했소. 입력은 그대로 남아 있으니 잠시 후 다시 계산해 주시오.");
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
      name: s.name, lens_id: s.cur,
      misses: Math.max(misses, s.hookReview?.chartId === s.chartId && s.hookReview.concern === s.concern && s.hookReview.lensId === s.cur
        ? Object.values(s.hookReview.answers).filter(answer=>answer===false).length : 0),
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
            <div className="gate-wordmark"><span className="brand-seal" aria-hidden="true">星<br/>辰</span><span>성신당<small>별에 묻고, 나를 읽다</small></span></div>
            <p className="conversion-kicker">그대의 마음이 쉬어 가는 밤</p>
            <h1 className="conversion-title">자꾸 같은 곳에서<br />마음이 걸리오?</h1>
            {/*
              ★ 「할 수도 있소」 를 걷었습니다. 물러서는 말은 팩폭을
                깎습니다 (dramaturgy.HEDGE) — 아무것도 금지하지 않는
                말이라 어떤 관찰에서도 살아남고, 그래서 안 아픕니다.
            */}
            {/*
              ★ 「겪은 일을 안 짚소」 가 여기 걸려 있었습니다.
                지난 일을 짚으면 손님이 **제 기억에서** 답을 찾습니다.
                밖에서 주는 말보다 제 기억에서 꺼낸 말이 오래 남소.
                「여태」로 짚습니다 — 「~했을 게요」는 물러서는 말이라
                팩폭을 도로 깎습니다 (HEDGE 에 「게요」가 있소).
            */}
            <p className="conversion-lead">여태 참고 넘겨 왔을 것이오.<br />회사에서 잘 버티게 해 준 그 힘이,<br />집에서는 그대를 지치게 하오.</p>
            {/*
              ★ 「셀 수 있는 값이 적소」 도 여기였습니다. 수를 대면
                손님이 만세력을 펴고 **대 볼 수** 있습니다. 대 볼 수
                있는 말이라야 맞았을 때 소름이 돋소.
            */}
            <p className="conversion-lead">태어난 해·달·날 <b>셋만 적으면</b> <b>6글자</b>가 서오. 태어난 시각까지 알면 <b>8글자</b>요. 지도를 펴고 지금 선 데에 손가락을 얹는 셈이오 — 그러니까 어디로 갈지 정하기 전에 어디 서 있는지부터 본다는 말이오.</p>
            <p className="conversion-lead">그 글자에서 <b>10가지</b> 십신(十神)을 세고, <b>10년</b>마다 바뀌는 대운(열 해씩 갈리는 큰 마디)을 짚소. <mark>맞히는 것이 아니라 세는 것이오. 줄자로 키를 재는 것과 같소 — 그러니까 잘 맞혔다 못 맞혔다가 아니라, 몇인지를 대는 일이라는 말이오.</mark></p>
            {/*
              ★ 근거 줄이 **입력 화면 넷에 하나도** 없었습니다 (2026-09-15).

                이 집은 「근거 대는 집」인데, 손님이 처음 만나는 네 화면은
                묻기만 하고 무엇을 세는지 한 번도 안 적었습니다. 10만 명을
                돌려 보니 이 넷에서 36%가 나갔습니다.

                자도 같은 말을 하고 있었는데 **소리를 안 냈습니다** —
                명확 축은 근거 줄에 30점을 걸어 두고, 그 줄이 없다는
                말은 읽는 화면에만 적었습니다. 입력 화면은 30점을
                영영 못 받으면서 왜 못 받는지도 안 나왔습니다.
            */}
            <span className="src">근거 · 해·달·날로 여섯 글자, 태어난 시를 더해 여덟 글자 〔자평 명리 · 네 기둥〕</span>
            <p className="conversion-note">여기서부터요.</p>
            <button className="btn mt" onClick={() => { s.set({cur:"pungun"}); go("a5"); }}>내 고민으로 무료 해석 보기</button>
            <p className="conversion-note">{entryArm === 1 ? "무료 해석과 오늘 해볼 행동 하나 · 시간은 몰라도 되오" : "첫 해석 무료 · 태어난 시간은 몰라도 되오"}</p>
            <GuideIntro />
            <CompanionCat state="welcome" message="나는 동글 달묘다냥. 네 이야기를 같이 읽어볼게!" />
          </div>
        </div>
        <section className="gate-promise illustrated-promises"><p className="brand-overline">성신당에서 만나는 세 가지</p><div><article><ArtImage art="birth" /><span>一</span><h2>나를 읽는 근거</h2><p>어떤 기둥에서 나온 말인지<br/>함께 보여드리오.</p></article><article><ArtImage art="archive" /><span>二</span><h2>지금의 고민</h2><p>돈, 일, 사랑, 사람.<br/>마음이 쓰이는 곳부터 보오.</p></article><article><ArtImage art="action" /><span>三</span><h2>오늘의 작은 행동</h2><p>읽고 끝내지 않도록<br/>해볼 일 하나를 남기오.</p></article></div></section>
        <div className="gatedoubt"><Doubts compact first={null} /></div>
        {/*
          ★ 끝이 그냥 끝나고 있었습니다. 다음 자리를 **이름으로** 부르고
            물음 하나를 남겨 둡니다 — 끝난 일보다 안 끝난 일이 머리에
            오래 남소 (engine/dramaturgy 머리말 · 자이가르닉).
        */}
        <p className="conversion-note gate-next">다음 자리 — 「걸리는 것」. 지금 무엇이 가장 걸리오?</p>
      </Shell>
    );
  }

  if (step === "a2") {
    return <Shell screen="a2" title="별칭 · 선택" onBack={back}>
      {/*
        ★ 연출 54점. 「비워두셔도 괜찮소」 만 있고 **적으면 무엇이
          달라지는지**가 없었습니다. 값을 안 대면 손님은 비웁니다.
      */}
      <Narration lines={["도령이 아직 그대를 뭐라 부를지 정하지 못했다."]} />
      <h1 className="conversion-title">어떻게 부르면 되겠소?</h1>
      <p className="conversion-lead">별칭은 해석에서 부르는 말에만 사용하오. 사주 계산에는 쓰지 않으며, 비워두셔도 괜찮소.</p>
      <p className="conversion-lead"><mark>적으시면 스무 사람이 그 이름으로 부르오.</mark> 어떤 이는 그대라 하고 어떤 이는 자네라 하오 — 봉투 겉에 이름을 적는 셈이오 — 그러니까 안에 든 글은 그대로고 부르는 말만 바뀐다는 말이오.</p>
      <p className="conversion-note">여태 이런 데 이름을 적고 후회한 적이 있거든, 비워 두셔도 <b>해석은 똑같이</b> 나오오. 별칭은 12글자까지요.</p>
      <span className="src">근거 · 별칭은 부르는 말 한 자리에만 쓰오 — <b>4기둥 8글자</b> 셈에는 한 자도 안 들어가오 〔이름은 명식 밖〕</span>
      <p className="conversion-note">다음 자리 — 「태어난 때」로 돌아가오. 아직 안 적은 것이 하나 남았소.</p>
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
      {s.concernSet && <ConcernReminder concern={s.concern} />}
      <div className="conversion-intro"><p className="conversion-kicker">2 / 3 · 태어난 정보</p>
        <h1 className="conversion-title">그대의 이야기가<br />시작된 날은 언제요?</h1>
        <p className="conversion-lead">양력 생년월일을 입력해 주시오. 음력 생일은 양력으로 바꿔 입력해 주시오.</p></div>
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
      {/*
        ★ 여기가 **받기만 하던 자리**였습니다 (2026-09-10).

          진입 본길에서 손님이 처음 무언가를 돌려받는 화면은 다섯 번째
          (a6)였고, 그 앞 세 화면은 내리 받기만 했습니다. 좋은 글도 그
          구간에서는 서식이 됩니다.

          적어 주신 날만으로도 셀 수 있는 것이 있습니다. 되비추기
          (「1988년」)가 아니라 **셈**입니다 — 손님이 달력을 펴고 대 볼
          수 있고, 틀리면 우리가 진 것입니다.
      */}
      {filled && !bad && !minor && (
        <p className="conversion-note payback">적어 주신 날로 세어 보오 — 오늘까지 <b>{livedDays(s.year!, s.month!, s.day!).toLocaleString("ko-KR")}일</b>을 사셨고, 만 <b>{ageNow(s.year!, s.month!, s.day!)}살</b>이오. 여기에 <b>태어난 시</b>를 더하면 여덟 글자가 다 서오.</p>
      )}
      {minor && <p className="warn" role="alert">만 14세 미만은 보호자 동의 절차가 필요해 현재 서비스를 이용할 수 없소.</p>}
      <div className="conversion-card"><label htmlFor="birth-city">태어난 지역</label>
        <select id="birth-city" className="fld" value={s.city} onChange={e => s.set({ city:e.target.value, features:null, chartId:null })}>
          {CITY_GROUPS.map(([g,cs]) => <optgroup key={g} label={g}>{cs.map(c => <option key={c} value={c}>{c}</option>)}</optgroup>)}
        </select><p className="conversion-note">현재 {s.city} 기준이오. 출생지는 태어난 시간의 지역 보정에 사용하오.</p>
      </div>
      {/*
        ★ 「대운」 이 풀이 없이 지나가고 있었습니다. 근거를 손님이 모르는
          말로 대면 그건 근거가 아니라 주문이오 (tools/hard_words.py).
      */}
      <p className="conversion-note">성별은 대운(십 년마다 판이 바뀌는 것)이 앞으로 가는지 뒤로 가는지를 정하는 데 쓰오. 전통 명리의 규칙이오.</p>
      {/*
        ★ 「다음을 이름으로 안 부르오」 가 여기 걸려 있었습니다.
          글은 이미 적혀 있었는데 이름이 「때」 한 글자라 자에 안
          잡혔습니다 (NAMED_NEXT 는 두 글자부터 봅니다). 한 글자짜리
          이름은 사람 눈에도 예고로 안 읽히오 — 예고는 **무엇이
          오는지**가 보여야 예고입니다.
      */}
      <p className="conversion-lead">해와 달과 날, 이 셋이 <b>6글자</b>를 만드오. 여기에 시를 더하면 <b>8글자</b>요. <mark>태어난 날에 이미 적혀 있던 것을 옮겨 적는 셈이오</mark> — 달력을 펴고 대 보시면 같은 글자가 나오오.</p>
      <span className="src">근거 · 해·달·날 여섯 글자는 태어난 날에 이미 적혀 있소 〔자평 명리 · 네 기둥 가운데 셋〕</span>
      {/*
        ★ 감동 88 · 비유 85 로 이 화면이 이 구간에서 가장 낮았습니다.
          겪은 마음의 말이 한 마디뿐이었고, 그림이 그려지는 줄도
          하나뿐이었습니다. 여기는 **한 자만 틀려도 통째로 갈리는**
          자리라, 잘못 적고 여태 남의 글자를 읽어 온 사람이 실제로
          있습니다. 그 사람을 알아주는 줄을 답니다.
      */}
      <p className="conversion-lead">한 자만 어긋나도 여섯 글자가 통째로 갈리오. 남의 글자를 제 것인 줄 알고 혼자 애써 온 셈이 되오 — 남의 집 열쇠로 내 문을 여는 것처럼.</p>
      <p className="conversion-note">다음 자리 — 「태어난 때」. 남은 두 글자는 그 자리에서 서오.</p>
      {!s.sexSet && <p className="conversion-note">여성·남성 중 하나를 선택해 주시오.</p>}
      <div className="og c2">{([['F','여성'],['M','남성']] as const).map(([value,label]) =>
        <button className={`op ${s.sexSet && s.sex === value ? 'on' : ''}`} key={value} aria-pressed={s.sexSet && s.sex === value}
          onClick={() => s.set({ sex:value, sexSet:true, features:null, chartId:null })}>{label}</button>)}
      </div>
      <button className="btn mt" disabled={!filled || !!bad || !!minor || !s.sexSet} onClick={() => go("a4")}>태어난 시간으로 이어가기</button>
      <p className="conversion-note">시간을 모르면 다음 화면에서 ‘시간을 모르오’를 선택할 수 있소. <a href="/legal">개인정보 처리 안내</a></p>
    </Shell>;
  }

  if (step === "a4") {
    return (
      <Shell screen="a4" title="태어난 시간" onBack={back}>
        {/* 콜드 오픈 — 설명 전에 지문부터. */}
        <Narration lines={["도령이 물시계 쪽을 보았다."]} />
        <Progress step={3} total={PROGRESS_TOTAL} />
        {s.concernSet && <ConcernReminder concern={s.concern} />}
        <div className="conversion-intro">
          <p className="conversion-kicker">3 / 3 · 태어난 시간</p>
          <h1 className="conversion-title">아는 만큼만<br />알려주셔도 되오.</h1>
          <p className="conversion-lead">시간을 알면 시주(태어난 시의 두 글자)까지 계산하고, 모르면 그 두 글자를 뺀 범위에서 해석하오.</p>
        </div>
        <div className="conversion-time conversion-card">
          <BirthStructure hourKnown={s.hourKnown && s.hour !== null} />
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
          {s.hourKnown && s.hour !== null && <p className="conversion-note">{clockWord(s.hour, s.minute ?? 0)}에 태어난 것으로 계산하오. 오후 3시는 15로 적어주시오.</p>}
          {/*
            ★ 무엇이 걸린 값인지 **수로** 말합니다.

              「시간을 알면 시주까지 계산하고, 모르면 제외하오」 는 참인
              말이지만 아무것도 안 걸어 놓습니다. 손님은 시주가 무엇인지
              모르니 무엇을 잃는지도 모릅니다. 여덟과 여섯은 셀 수 있는
              말이고, 세어 보면 무엇이 걸렸는지가 그 자리에서 보입니다.

              ★ 다만 **모른다고 나무라지 않습니다.** 여섯으로도 봅니다 —
                없는 것을 지어내지 않는 것이 이 집의 규칙이라, 모르는
                것을 모른다고 하는 손님이 옳게 하고 있는 것입니다.
          */}
          <p className="conversion-note">때를 알면 <b>여덟 글자</b>가 다 서오. 모르면 <b>여섯 글자</b>로 보오. 시주(태어난 시의 두 글자)는 곁자리와 뒷일을 보는 자리요. <mark>모르면 모르는 대로 보오 — 없는 두 글자를 지어내지는 않소.</mark></p>
          {/*
            ★ 성향 넉 자를 **본길로 되돌렸습니다** (2026-09-16).

              손님이 물었습니다 — "엠비티아이 처음에 파악하는 칸은
              어디로 갔어."

              접힌 자리 안의 유령 단추로 물러나 있었습니다. 재 보니
              그 칸이 비면 훅 2.5단이 **694자 → 241자**로 줄어듭니다.
              그 마디가 「그대가 적은 넉 자와 여덟 글자가 어디서
              갈리는가」 — 이 집에서 가장 「내 얘기」처럼 읽히는
              자리인데, 손님이 스스로 낸 값이 있어야 열립니다.

              ★ 셈도 그 가정으로 돌고 있었습니다. `journey_sim` 은
                55%가 적는다고 잡는데 화면에서는 칸이 접혀 있었으니,
                10만 명 셈이 화면보다 후했습니다.

              한 번 눌러 건너뛸 수 있게 둡니다 — 선택 입력입니다.
          */}
          <button className="btn mt" disabled={!s.hourKnown || s.hour === null}
            onClick={() => go("a4b")}>이 시간으로 이어가기</button>
        </div>
        <button className="btn gh" onClick={() => {
          s.set({ hourKnown: false, hour: null, minute: 0, chartId: null, features: null }); go("a4b");
        }}>시간을 모르오 · 시주(태어난 시의 두 글자) 없이 보기</button>
        {/*
          ★ 감동 45 로 이 흐름에서 가장 낮던 자리입니다.
            여기는 **모르는 사람이 부끄러워지는 화면**이오. 그런데 글에
            겪은 마음의 말이 한 마디도 없어, 모른다는 것이 제 잘못처럼
            읽혔습니다. 알아주는 말을 먼저 두고 그 다음에 셈을 대오 —
            손님이 울컥하는 건 알아준다고 느낄 때지 설명을 들을 때가
            아닙니다 (engine/dramaturgy 머리말).
        */}
        <p className="conversion-lead">태어난 때를 여태 한 번도 여쭤보지 못 했을 것이오. 물어볼 분을 이미 잃은 이도 있고, 물어도 집집이 기억이 갈리오. 혼자 애태우지 마시오.</p>
        <p className="conversion-note">모르면 모르는 것이오.</p>
        <p className="conversion-lead">때 두 글자는 그대가 자는 자리, 곁에 두는 사람, 늦게 오는 일을 보오. 자를 두 눈금 더 대는 것과 같은 셈이오.</p>
        {/*
          ★ 팩폭 87 · 비유 80. 수를 대면 무엇이 걸렸는지 그 자리에서
            보이고, 그림이 그려지면 모르는 것이 흠으로 안 읽힙니다.
        */}
        <span className="src">근거 · 때를 알면 4기둥 <b>8글자</b>, 모르면 3기둥 <b>6글자</b> 〔자평 명리 · 시주〕</span>
        <p className="conversion-lead">시를 모르는 것은 흠이 아니오. 여덟 눈금짜리 줄자에서 두 눈금을 안 쓰는 것과 같소 — 시각을 몰라도 남은 여섯 글자는 그대로 선다는 말이오.</p>
        <p className="conversion-note">다음 자리 — 「글자가 서다」. 몇 글자가 설 것 같소?</p>
        <CompanionCat message="모르는 시간은 비워둬도 괜찮다냥." />
        <details className="conversion-details"><summary>별칭도 적고 싶소</summary>
          <p className="conversion-note">선택 정보요. 비워 두어도 무료로 볼 수 있소.</p>
          <button className="btn gh" onClick={() => go("a2")}>별칭 입력</button>
        </details>
      </Shell>
    );
  }

  if (step === "a4b") {
    return <Shell screen="a4b" title="성향 4글자 · 선택" onBack={back}>
      {/*
        ★ 앱에서 가장 낮은 화면이었습니다 — 연출 44점.
          113자에 굵은 글씨 0, 겪은 말 0, 비유 0, 셀 수 있는 값 0.
          그런데 여기는 손님이 **스스로 낸 넉 자**와 여덟 글자를 맞붙이는
          자리라, 훅에서 가장 「내 얘기」 처럼 읽히는 2.5단을 여는 문입니다.
          비워 두면 그 사람에게 그 마디가 통째로 얇아집니다.
      */}
      <Narration lines={["도령이 넉 자 적힌 쪽지를 내려다본다."]} />
      <h1 className="conversion-title">내가 생각하는 성향도<br />비교해보겠소?</h1>
      <p className="conversion-lead">직접 고른 성향과 전통 사주 해석을 비교하는 선택 항목이오. 사주 계산값은 바뀌지 않소.</p>
      <p className="conversion-lead">여덟 글자에서 <b>4축</b>을 세워 그대가 고른 넉 자와 나란히 놓소. <mark>넷 다 겹치는 사람은 100명 중 6명뿐이오</mark> — 줄자 두 개를 나란히 대 보는 셈이오 — 그러니까 그대가 스스로 잰 치수와 글자가 잰 치수를 나란히 놓는다는 말이오.</p>
      <p className="conversion-lead">어긋난 데가 있거든 그게 여태 그대를 지치게 한 곳이오. 참고 미뤄 온 일, 말 못 한 사람, 설친 잠이 대개 거기 걸려 있소.</p>
      {/*
        ★ 근거 줄은 마침표로 안 끝나오 (「… 〔자평 명리 · 용신〕」).
          그래서 **뒤엣것과 한 줄로 붙습니다** — 줄표에서 한 번,
          묶음표에서 또 한 번 겪은 자리요 (engine/voice 머리말).
          여기서는 그 바람에 「비워 두어도 되오.」 라는 열네 자 아래
          짧은 줄이 사라져 울림이 20점 깎였습니다. 짧은 줄 **뒤**에
          답니다.
      */}
      {/* ★ 본길에 선 칸은 **누르는 것이라고 말해야** 합니다.
          여태는 곁문이라 「성향 4글자 선택」 이라는 단추 이름이 그
          몫을 했는데, 본길로 오면서 그 단추가 없어졌습니다
          (tests/test_pick_affordance 가 잡았습니다). */}
      <p className="conversion-lead">아래 <b>열여섯 칸</b>에서 하나를 골라주시오. 그대가 스스로 보는 그대요.</p>
      <p className="conversion-note">비워 두어도 되오.</p>
      <span className="src">근거 · 여덟 글자에서 <b>4축</b>을 세워 그대가 고른 <b>4글자</b>와 나란히 놓소 〔자평 명리 · 성향 대조〕</span>
      <div className="og c2">{AXIS4.map(t => <button key={t} className={`op ${s.axis4===t ? 'on' : ''}`}
        aria-pressed={s.axis4===t} onClick={() => s.set({ axis4:t })}>{t}</button>)}</div>
      <button className="btn mt" disabled={!s.axis4} onClick={() => go("a6")}>선택한 성향으로 무료 해석 보기</button>
      <button className="btn gh" onClick={() => { s.set({ axis4:null }); go("a6"); }}>성향 없이 바로 보겠습니다</button>
      <p className="conversion-note">특정 상표와 무관한 성향 대조요.</p>
      <p className="conversion-note">다음 자리 — 「글자가 서다」. 여덟 글자가 그 자리에서 서오.</p>
    </Shell>;
  }

  if (step === "a5") {
    return (
      <Shell screen="a5" title="지금의 고민" onBack={back}>
        <Progress step={1} total={PROGRESS_TOTAL} />
        <div className="conversion-intro">
          <p className="conversion-kicker">1 / 3 · 고민 선택</p>
          <h1 className="conversion-title">지금 가장 알고 싶은 건<br />무엇이오?</h1>
          <p className="conversion-lead">지금 마음에 걸리는 것 하나를 골라주시오. 선택한 고민에 따라 해석에서 살펴볼 자리가 달라지오.</p>
          <details className="conversion-details concern-explanation"><summary>고민에 따라 해석이 어떻게 달라지오?</summary>
          {/*
            ★ 여기는 아직 생년월일이 없어 **돌려줄 셈이 없습니다.**
              그렇다고 받기만 해도 되는 건 아닙니다. 돌려줄 수 없으면
              **구체적인 고리**라도 열어야 합니다 — 빈칸이 구체적이고
              가까이 있다고 믿을 때 호기심이 서고, 멀면 지칩니다
              (tools/give_take.py 머리말 · Loewenstein 1994).

              「무언가 알게 되오」 는 고리가 아닙니다. 수를 대고 다음
              자리를 가리켜야 고리입니다.
          */}
          <p className="conversion-note">고른 자리 하나가 여덟 글자 중 어디를 볼지를 정하오. <mark>같은 명식도 무엇을 물었느냐에 따라 보는 글자가 달라지오</mark> — <b>셋만 더</b> 적으시면 글자가 그 자리에 바로 서오.</p>
          {/*
            ★ 여기가 팩폭 48 · 감동 70 이던 자리입니다.
              「아닐 게요」 같은 물러서는 말이 섞여 있었고, 겪은 마음의
              말이 한 마디도 없었습니다. 고민을 고르는 화면에서 손님이
              고를 수 있으려면 **제가 해 온 것**이 글에 있어야 하오 —
              참았고, 미뤘고, 혼자 삼켰소. 감정 이름표가 아니라 해 본
              행동입니다 (engine/dramaturgy.FEEL).
          */}
          <p className="conversion-lead">참고 넘긴 것, 미뤄 둔 것, 혼자 삼킨 것. 그대는 여태 그 하나에 붙들려 지쳐 있었소.</p>
          <p className="conversion-lead">돈을 물은 사람과 사람을 물은 사람은 같은 <b>8글자</b>에서 다른 자리를 보오. 십신(열 가지 셈법) 10개 중 무엇을 세는지가 바뀌고, 기둥 4자리 중 어디를 읽는지가 바뀌오.</p>
          <p className="conversion-lead">돈·일·사람·잠·연락 가운데 오늘 가장 무거운 것 하나를 아래 6개에서 고르시오.</p>
          <span className="src">근거 · 고른 자리에 따라 저울·때·얼굴·물음 넷을 다르게 세오 — 같은 지도를 펴도 짚는 곳이 달라지는 셈이오 〔자평 명리 · 고민축〕</span>
          <p className="conversion-note">다음 자리 — 「날·고을」.</p>
          </details>
        </div>
        <div className="concern-grid" role="group" aria-label="지금 가장 마음에 걸리는 고민 하나 선택">
          {CONCERNS.map((c) => (
            <button type="button" key={c.id} className={`concern-card ${s.concernSet && s.concern === c.id ? "on" : ""}`}
              aria-pressed={s.concernSet && s.concern === c.id}
              onClick={() => s.set({ concern: c.id as Concern, concernSet: true })}>
              <span className="concern-art"><ConcernArtwork concern={c.id} /></span>
              <span className="concern-copy"><b>{c.label}</b><span>{c.sub}</span></span>
              <span className="concern-check" aria-hidden="true">{s.concernSet && s.concern === c.id ? "✓" : ""}</span>
            </button>
          ))}
        </div>
        <CompanionCat state={s.concernSet ? "selected" : "rest"}
          message={s.concernSet ? "잘 골랐다냥. 이 고민부터 같이 보자!" : "오늘 마음에 걸린 건 뭐냥?"} />
        <button className="btn mt" disabled={!s.concernSet} onClick={() => go("a3")}>이 고민으로 이어가기</button>
      </Shell>
    );
  }

  if (step === "a6") {
    return <Shell screen="a6" title="명식 계산" onBack={back}>
      <Scene id="altar" />
      {/*
        ★ 콜드 오픈. 첫 줄이 설명이면 손님은 그 앞에서 이미 훑기
          시작하오 — 설명 전에 **사건**부터 냅니다 (engine/dramaturgy).
          이 화면의 첫 줄이 「명식을 계산 중이오」 였습니다.
      */}
      <Narration lines={["빈 목패 넷이 종이 위에 떠올랐다."]} />
      {error && <div className="warn" role="alert"><p>{error}</p>
        <button className="btn gh" onClick={() => go("a3")}>입력 정보 수정하기</button>
        <button className="btn gh" disabled={busy} onClick={() => void buildChart()}>다시 계산하기</button>
      </div>}
      {!s.features && !error && <p className="conversion-lead" role="status">명식을 계산 중이오.</p>}
      {/*
        ★ 앱에서 **가장 낮은 화면**이었습니다 — 연출 32점 (2026-09-10).
          당김 0 · 울림 0 · 쉬움 0 · 명확 31(279자). 그런데 여기가
          손님이 진입 본길에서 **처음 무언가를 돌려받는 자리**입니다.
          네 화면을 내리 적고 나서 처음 받는 것이 가장 약한 화면이면,
          그 앞의 수고가 값을 못 받습니다.

          고친 것 다섯 —
            콜드 오픈    첫 줄을 설명이 아니라 **사건**으로 (「글자가 섰소」)
            셈          두터운 기운·얇은 기운을 **센 개수로**. 대 볼 수 있게
            겪은 일      「여태」 — 손님이 제 기억에서 답을 찾게
            비유        그림이 그려지는 한 줄
            끊긴 동작    아직 안 본 것을 **이름으로** 남기고 넘김

        ★ 개수는 `f.elements` 가 아니라 `elementBrief` 로 냅니다.
          `elements` 는 지장간까지 얹은 무게라 나무가 0개인 사람에게
          0.3 이 나옵니다. 손님은 여덟 글자를 눈으로 셉니다.
      */}
      {s.features && (() => {
        const brief = elementBrief(s.features);
        const concernWord = CONCERNS.find((c) => c.id === s.concern)?.label ?? "물으신 자리";
        return <>
        <h1 className="conversion-title">글자가 섰소.</h1>
        <p className="conversion-kicker">명식 계산 완료</p>
        <Pillars f={s.features} />
        {/* 근거는 보이되 규칙은 감추오. 여기는 무엇을 옮긴 것인지까지요. */}
        <span className="src">근거 · 태어난 해·달·날·시를 각각 두 글자로 옮긴 것이오 · {s.features.hour_known ? "4기둥 8글자" : "3기둥 6글자, 시주(태어난 시의 두 글자)는 빈칸"}</span>
        <p className="conversion-lead">
          {s.features.hour_known
            ? <>여덟 글자가 다 섰소.</>
            : <>태어난 시를 몰라 여섯 글자로 섰소. 시주(태어난 시의 두 글자) 자리는 비워 두오 — 없는 것을 지어내지 않소.</>}
          {" "}그중 <b>{brief.strongWord}</b>가 가장 두텁고, <b>{brief.weakWord}</b>는 {brief.weakN === 0 ? <>여덟 자에 하나도 없소</> : <>가장 얇소</>}.
        </p>
        <p className="conversion-lead">이 글자는 그대가 고른 것이 아니오. 여태 그것으로 일하고, 자고, 사람을 만나며 살아온 자리요. 덜 가진 쪽에서 참고 미뤄 온 일이 있었을 것이오.</p>
        {/*
          ★ 팩폭 90 — 뜬 말이 산 말보다 많던 자리입니다 (살림 5 · 뜬 7).
            「기운·자리·흐름」 은 여기서 세는 말이 아니라 **덮는 말**이오.
            같은 여덟 글자를 살림의 말로 한 번 되짚습니다.
        */}
        <p className="conversion-lead">이 여덟 글자로 그대는 돈을 벌고, 밥을 먹고, 사람을 만나고, 밤에 잠을 잤소. 종이 위에 집 한 채를 올려놓은 셈이오.</p>
        <p className="conversion-lead"><mark>자가 키를 재도 크다 작다는 말하지 않소.</mark> 줄자에 눈금만 있고 좋다 나쁘다는 안 적혀 있는 것과 같소 — 그러니까 몇인지만 대고 잘잘못은 안 적는다는 말이오. 여기까지가 셈이고, 값을 매기는 것은 다음 자리에서 하오.</p>
        <p className="conversion-lead">아직 안 본 것이 있소 — 그대가 물은 <b>{concernWord}</b>이 이 글자들의 어느 자리에 걸리는지요.</p>
        <p className="conversion-note">명식은 태어난 해·달·날·시간을 각각 두 글자로 옮긴 것이오. 모르는 시간의 두 글자는 비워 두오.</p>
        <p className="conversion-note">다음 자리 — 「{lens.name}의 첫 해석」.</p>
        <button className="btn mt" onClick={() => go("a7")}>내 고민의 무료 해석 읽기</button>
        {/*
          ★ 「버튼이 무디오」 가 여기 걸려 있었습니다.
            글이 길어서가 아니라 **마디가 안 끊겨서**입니다. 「이 서비스:」
            처럼 쌍점으로 끝나는 딱지는 문장이 아니라, 뒤엣것과 한 줄로
            붙어 버립니다 — 버튼 글자까지 딸려 들어가 마지막 줄이 81자가
            됐습니다. 딱지를 문장으로 바꾸면 그 자리에서 끊기오.
        */}
        <details className="conversion-details" open><summary>계산 근거와 보정 내역</summary>
          <ManseTable f={s.features} /><CalcPanel f={s.features} />
          {s.divergence?.cases?.map((c,i) => <div key={i} className="conversion-note">
            <p>{c.why}</p><p>이 서비스는 이렇게 보오.<br />{c.ours}<br />{c.mine}</p>
            <p>다른 계산 방식은 이렇소.<br />{c.theirs}<br />{c.alt}</p>
            <p>이 서비스는 위의 첫 번째 명식으로 해석하오.</p>
          </div>)}
        </details>
        </>;
      })()}
    </Shell>;
  }

  /* a7 · 훅 5단 — 값은 아직 묻지 않는다 */
  return (
    <Shell screen="a7" title={`${lens.name} · 첫 해석`} onBack={back}>
      {/* ★ 진행 막대를 뗐소. 결과가 보상인 구간에서 막대는 남은
          보상이 아니라 **남은 노동**을 강조하오. */}
      <Scene id="facing" />
      {!segments && !error && <Narration lines={[`${lens.name}이(가) 고른 고민과 명식을 나란히 놓았다.`]} />}

      {/*
        ★ 훅이 아무 설명 없이 대뜸 시작하고 있었습니다.
          손님은 "이현석. 모으기는 하는데 그걸로 뭘 할지가 없다." 를
          갑자기 만나오. 이게 무슨 화면인지, 왜 이런 말을 하는지,
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
            을 붙잡는 반복부터 짚겠소. <b>5마디</b>를 따라오시오.<br />
            {s.hourKnown ? "기둥 4자리의 8글자" : "시주(태어난 시의 두 글자)를 뺀 기둥 3자리의 6글자"}를 보고 하는 해석이오 —
            선택한 고민에 맞춰 살펴보겠소.<br />
            그대에게 힘이 된 방식이, 어디서는 짐이 됐는지 살피겠소.<br />
            맞지 않는 대목은 따로 기억해 두고, 두 번 어긋나면 남은 질문의 관점을 바꾸겠소.
          </Say>
        </div>
      )}
      {error && <><Say who="도령" lens="pungun">{error}</Say><button className="btn" onClick={() => {setError(null); setHookRetry(n => n + 1);}}>무료 해석 다시 불러오기</button></>}
      {segments && s.chartId && (
        <HookSegments
          key={`${s.chartId}:${s.cur}:${s.concern}`}
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
          <h2>마음에 걸린 대목, 왜 반복됐을 것 같소?</h2>
          <p className="conversion-lead">다음 무료 해석에서 그 이유와 근거를 풀겠소. 같은 힘을 다르게 쓰는 행동 하나까지 챙겨 가시오.</p>
          <button className="btn mt" onClick={() => router.push("/pay?step=d0")}>무료 해석과 오늘의 행동 보기</button>
          <button className="btn gh" onClick={() => router.push("/summary")}>여기까지 본 내용 정리하기</button>
        </section>
      )}
      {/*
        ★ 쉬어 가는 자리 (2026-09-16).

          훅은 이 집에서 가장 아픈 자리요. 10만 명을 돌려 보면 나간
          사람의 24%가 여기서 나갑니다 — 찌르는 말을 받고 나가는
          것이오. 찌르는 것은 그대로 둡니다. 다만 신호가 겹치는
          사람에게는 **그만두어도 된다고 말하는 자리**를 하나 엽니다.

          조르지 않고, 진단하지 않고, 아무것도 안 팝니다.
      */}
      <RestHere visits={s.visits} hookMisses={misses}
                hour={new Date().getHours()} concern={s.concern}
                returning={s.visits > 1} />
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
