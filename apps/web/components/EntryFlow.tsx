"use client";

import { useRouter } from "next/navigation";
import Shell from "./Shell";
import Scene from "./scene/Scene";
import GuideIntro from "./GuideIntro";
import RestHere from "./RestHere";
import EntryReading from "./EntryReading";
import { ConcernArtwork } from "./ConcernArtwork";
import Doubts from "./Doubts";
import { CalcPanel, ManseTable, Pillars } from "./Chart";
import { Progress } from "./Narration";
import { birthProblem } from "@/lib/birth";
import { needsGuardian } from "@/lib/biz";
import { ENTRY_CONCERNS } from "@/lib/entry-copy";
import { LENS_BY_ID } from "@/lib/lenses";
import { CONCERNS, useSession } from "@/lib/store";
import { track } from "@/lib/track";
import type { HookSegment } from "@shared/chart";

/*
 * 진입부 — 값을 치르기 전에 보는 전부 (docs/45).
 *
 * ★ 2026-09-20 에 재 보니 첫 해석 전까지 읽는 **서비스 설명이 1,824자**인데
 *   받는 보상이 96자였습니다. 화면 여섯에 상호작용 열다섯 번이었고요.
 *   그 96자에는 숫자가 하나도 없었습니다.
 *
 *   고친 것은 셋입니다.
 *     ① A1 의 「설명용 예시」를 뺐습니다. 개인 결과로 위장하지 않은 것은
 *        옳았으나, **그 자리에 있으면 안 되는 물건**이었습니다 — 같은 글도
 *        「일반적으로 해당되는 것」이라 말하면 수용도가 가장 낮습니다
 *        (Snyder 1974: 4.38 → 3.24). 대신 **이 집이 무엇을 세는지**를 둡니다.
 *     ② 출생 정보를 한 화면으로 합치고 **칸마다 왜 묻는지**를 답니다.
 *        「단계를 줄여라」에는 통제된 근거가 없고, 있는 근거는
 *        「납득 안 되는 것을 묻지 마라」입니다(Baymard: 계정 강요 18% ·
 *        길고 복잡 17%).
 *     ③ 성향 4글자(a4b)를 **본길에서 뺐습니다.** 무료 해석 직전의 마지막
 *        관문이 선택 입력이면 그건 이탈만 만듭니다. 이제 a6·a7 에서
 *        손님이 원할 때 엽니다.
 *
 * ★ 시간 모름은 **세 단**입니다 (a3 → a4).
 *     ① 분까지 적는 칸을 먼저 보이고
 *     ② 모르겠다 하면 「집에 물어보기」를 내고
 *     ③ 그래도 모르면 시주를 빼고 **무엇이 빠지는지 적습니다.**
 *   ②까지만 하고 ③에서 임의 시각을 채우는 집이 업계 표준입니다.
 *   우리는 채우지 않습니다 — 그게 이 집의 상품입니다.
 */
export type EntryStep = "a1" | "a2" | "a3" | "a4" | "a4b" | "a5" | "a6" | "a7";
const AXIS4 = ["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP", "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"];
const CITIES = ["서울", "인천", "수원", "춘천", "강릉", "대전", "청주", "전주", "광주", "목포", "대구", "안동", "포항", "부산", "울산", "창원", "제주"];
// 집에 보낼 문자. 보내는 것은 손님이고 우리는 **문면만** 적어 둡니다.
const ASK_HOME = "sms:?body=" + encodeURIComponent("제가 태어난 정확한 시각(몇 시 몇 분)을 아세요?");

export default function EntryFlow({ step, go, back, error, busy, calculate, segments, done, onDone, onMiss, retry, misses }: {
  step: EntryStep; go: (step: EntryStep) => void; back?: () => void;
  error: string | null; busy: boolean; calculate: () => void;
  segments: HookSegment[] | null; done: boolean; onDone: () => void; onMiss: () => void; retry: () => void; misses: number;
}) {
  const s = useSession();
  const router = useRouter();
  const copy = ENTRY_CONCERNS[s.concern];
  const lens = LENS_BY_ID[s.cur] ?? LENS_BY_ID.pungun;
  const context = <div className="entry-context">오늘의 질문<span>{copy.question}</span></div>;
  const axisLink = <button className="entry-text-button" onClick={() => go("a4b")}>
    {s.axis4 ? `내가 아는 나와 대 보기 · ${s.axis4}` : "내가 아는 나와도 대 보기 · 선택"}</button>;

  if (step === "a1") return <Shell screen="a1" bare>
    <section className="entry-gate">
      <div className="entry-gate-art"><Scene id="gate" className="fill" /></div>
      <div className="entry-gate-content">
        <div className="gate-wordmark"><span className="brand-seal" aria-hidden="true">星<br />辰</span><span>성신당<small>내 고민에서 시작하는 사주</small></span></div>
        <p className="entry-eyebrow">돈 · 일 · 사랑 · 관계 · 방향 · 휴식</p>
        <h1>잘해보려 했는데,<br />왜 같은 고민으로<br /><em>돌아오게 될까.</em></h1>
        <p className="entry-lead">맞히는 집이 아니라 <em>근거 대는 집</em>이오.<br />여덟 글자를 세어 보이고, 그 셈이 그대의 고민에서<br />어디로 나오는지까지 말하겠소.</p>
        <button className="btn" onClick={() => { s.set({ cur: "pungun" }); go("a5"); }}>무료로 첫 해석을 받겠습니다</button>
        <p className="entry-footnote">첫 해석 무료 · 태어난 시각을 몰라도 됩니다</p>
        <div className="entry-deliverables"><span>세어 본 것</span><span>그래서 이렇게</span><span>언제 바뀌오</span><span>오늘 한 가지</span></div>
      </div>
    </section>
    {/*
      ★ 여기 있던 「설명용 예시」를 뺐습니다 (2026-09-20).
        남의 결과를 386자 읽히고 「위 문장은 예시예요」라고 적는 자리였습니다.
        그 자리에 **우리만 하는 셈**을 둡니다 — 조사한 서른한 곳과 바깥
        열한 곳을 통틀어 시주를 비우는 집이 여기뿐입니다.
    */}
    <section className="entry-sample"><p className="entry-eyebrow">이 집이 세는 것</p>
      <h2>모르는 것은<br />모른다고 적소.</h2>
      {/* ★ 「여덟 글자」는 이 집이 가장 자주 쓰는 말이오. 뜻을 한 번은
          밝혀야 뒤가 읽힙니다 (tests/test_screen_copy). */}
      <p className="entry-lead">명식은 태어난 해·달·날·시각을 각각 <b>두 글자로 옮긴 것</b>이오. 넷을 합쳐 여덟 글자요.</p>
      <ul className="entry-preview">
        <li><span>절기</span><div><b>절입 시각까지 계산하오</b><p>하루 차이로 글자가 바뀌는 자리요.</p></div></li>
        <li><span>시각</span><div><b>모르면 두 글자를 비웁니다</b><p>12시로 채우지 않소. 채우면 여덟 자 중 둘이 틀리오.</p></div></li>
        <li><span>기록</span><div><b>생일은 계측에 안 싣소</b><p>화면 이름과 숫자 몇 개만 남습니다.</p></div></li>
      </ul>
    </section>
    <GuideIntro />
    {/*
      ★ 의심 풀기 여섯 문답 — **직접 들어온 사람에게도** 보입니다.
        공유 화면에만 두면, 검색·광고로 들어온 사람은 가장 센 설득 자산을
        한 번도 못 보고 결제 갈림길까지 갑니다 (CLAUDE.md 금칙).
    */}
    <Doubts />
    {/*
      ★ 열어 둡니다. 「돈 아깝다」의 첫째 사유가 **「무료와 다르지 않다」**이고,
        경쟁사 리뷰에 「그 돈을 내면 뭘 받는지조차 볼 수가 없다」가 있습니다.
        접어 두면 결제 갈림길에서 처음 보게 됩니다.
    */}
    <details className="entry-evidence" open><summary>무료와 유료는 무엇이 다른가요?</summary>
      <p>첫 해석 네 장을 무료로 읽습니다 — 세어 본 것 · 그래서 이렇게 · 언제 바뀌오 · 오늘 한 가지. 이어지는 무료 풀이도 값을 치르지 않고 끝까지 읽을 수 있어요.</p>
      <p>이 집에는 스무 사람이 있고, 무료로 듣는 것은 그중 <b>한 사람의 눈</b>이에요. 다른 사람의 관점과 더 깊은 장은 그 사람의 값을 치른 뒤에 열려요. 포함 내용과 분량은 서버가 세어 보여드리니 결제 전에 확인해 주세요.</p>
    </details>
  </Shell>;

  if (step === "a5") return <Shell screen="a5" title="오늘의 고민" onBack={back}><div className="entry-step">
    <Progress step={1} total={2} /><p className="entry-eyebrow">01 · 오늘의 고민</p><h1>답을 듣고 싶은<br />질문 하나를 골라주세요.</h1>
    <p className="entry-lead">아래 여섯 가운데 <b>하나를 골라주시오.</b><br />고민이 바뀌면 <em>보는 자리</em>가 바뀌오 — 이름만 바뀌는 게 아니오.</p>
    <div className="entry-concerns" role="group" aria-label="오늘의 고민 선택">
      {CONCERNS.map(item => <button key={item.id} aria-pressed={s.concernSet && s.concern === item.id}
        onClick={() => {
          s.set({ concern: item.id, concernSet: true, hookReview: null });
          // ★ 고른 **갈래는 안 싣습니다.** 화면 이름만 — `topic_ask` 와 같은 규칙.
          //   여태 「골랐다」는 사실조차 안 남아서, 진열대 앞에서 몇이 돌아서는지
          //   알 수 없었습니다.
          track("concern_pick", "a5");
        }}>
        <span className="entry-concern-art"><ConcernArtwork concern={item.id} /></span>
        <span><small>{item.id === "health" ? "휴식" : item.label}</small><strong>{ENTRY_CONCERNS[item.id].question}</strong><span>{ENTRY_CONCERNS[item.id].detail}</span></span>
        <span className="entry-check" aria-hidden="true">{s.concernSet && s.concern === item.id ? "✓" : "＋"}</span>
      </button>)}
    </div>
    {s.concernSet && <p className="entry-selection" role="status">“{copy.question}”<br />이 질문을 중심으로 첫 해석을 준비할게요.</p>}
    <button className="btn" disabled={!s.concernSet} onClick={() => go("a3")}>이 질문으로 시작하겠습니다</button>
  </div></Shell>;

  if (step === "a2") return <Shell screen="a2" title="별칭 · 선택" onBack={back}><div className="entry-step">
    <p className="entry-eyebrow">선택 입력</p><h1>어떻게 불러드릴까요?</h1>
    <p className="entry-lead">실명 대신 편한 별칭을 적어도 좋아요. 해석에서 부르는 이름에만 사용해요.</p>
    <label htmlFor="entry-alias">별칭 · 최대 12글자</label><input id="entry-alias" className="fld" maxLength={12} value={s.name} onChange={event => s.set({ name: event.target.value })} />
    <button className="btn" onClick={() => go("a3")}>이 별칭으로 하겠습니다</button>
    <button className="btn gh" onClick={() => { s.set({ name: "" }); go("a3"); }}>별칭 없이 하겠습니다</button>
  </div></Shell>;

  if (step === "a3") {
    const filled = s.year !== null && s.month !== null && s.day !== null;
    const bad = filled ? birthProblem(s.year, s.month, s.day) : null;
    const minor = filled && !bad && needsGuardian(s.year!, s.month!, s.day!);
    const ready = filled && !bad && !minor && s.sexSet;
    return <Shell screen="a3" title="출생 정보" onBack={back}><div className="entry-step">
      <Progress step={2} total={2} /><p className="entry-eyebrow">02 · 나의 출생 정보</p>{context}
      <h1>같은 고민도,<br />출발점은 다르니까.</h1>
      <p className="entry-lead">아래 넷이 여덟 글자를 세우는 전부요.</p>

      <div className="f3">{([["year", "태어난 해", 4, "1993"], ["month", "월", 2, "11"], ["day", "일", 2, "25"]] as const).map(([key, label, max, placeholder]) =>
        <div key={key}><label htmlFor={`birth-${key}`}>{label}</label><input id={`birth-${key}`} className="fld" inputMode="numeric" maxLength={max} placeholder={placeholder}
          aria-invalid={!!bad} aria-describedby={bad ? "birth-error" : "birth-calendar"} value={s[key] ?? ""}
          onChange={event => { const value = event.target.value.replace(/[^0-9]/g, "").slice(0, max); s.set({ [key]: value ? Number(value) : null, chartId: null, features: null }); }} /></div>)}</div>
      <p id="birth-calendar" className="entry-footnote">여덟 글자 가운데 <b>여섯 자</b>가 여기서 나와요. 양력으로 적어 주세요 — 음력 생일이면 양력으로 바꾼 날짜예요.</p>
      {bad && <p id="birth-error" className="warn" role="alert">{bad}</p>}
      {minor && <p className="warn" role="alert">만 14세 미만은 보호자 동의 절차가 필요해 현재 서비스를 이용할 수 없어요.</p>}

      <fieldset className="entry-fieldset"><legend>사주 계산에 사용할 성별</legend><div className="og c2">
        {([["F", "여성"], ["M", "남성"]] as const).map(([value, label]) => <button key={value} className={`op ${s.sexSet && s.sex === value ? "on" : ""}`}
          aria-pressed={s.sexSet && s.sex === value} onClick={() => s.set({ sex: value, sexSet: true, features: null, chartId: null })}>{label}</button>)}
      </div><p className="entry-footnote">둘 가운데 <b>하나를 선택해 주시오.</b> <b>대운이 앞으로 가는지 뒤로 가는지</b>가 성별로 갈려요. 열 해마다 오는 마디의 나이가 달라집니다.</p></fieldset>

      <label htmlFor="birth-city">태어난 고을</label><select id="birth-city" className="fld" value={s.city} onChange={event => s.set({ city: event.target.value, features: null, chartId: null })}>
        {CITIES.map(city => <option key={city} value={city}>{city}</option>)}
      </select><p className="entry-footnote"><b>진태양시 보정</b>에 써요. 서울과 부산은 해가 뜨는 시각이 달라, 경계에 선 시각이면 글자가 갈립니다. 목록에 없으면 가까운 고을을 골라 주세요.</p>

      {/*
        ★ 시·분을 **여기서 먼저** 묻습니다. 대강 칸(한낮 11–15 …)을 위로
          올리면 아는 사람까지 그리로 흘러가고, 시주가 절반쯤 틀립니다
          (`.\dev.ps1 hours` — 51.7%).
      */}
      <label htmlFor="birth-hour">태어난 시각</label>
      <div className="f3 entry-time"><div><input id="birth-hour" className="fld" inputMode="numeric" maxLength={2} placeholder="15" aria-label="시 · 0–23" value={s.hourKnown ? s.hour ?? "" : ""}
        onChange={event => { const value = event.target.value.replace(/[^0-9]/g, "").slice(0, 2); s.set({ hourKnown: true, hour: value ? Math.min(23, Number(value)) : null, chartId: null, features: null }); }} /></div>
        <div><input id="birth-minute" className="fld" inputMode="numeric" maxLength={2} placeholder="00" aria-label="분 · 0–59" value={s.minute ?? ""}
          onChange={event => s.set({ minute: Math.min(59, Number(event.target.value.replace(/[^0-9]/g, "")) || 0), chartId: null, features: null })} /></div></div>
      <p className="entry-footnote">나머지 <b>두 글자</b>가 여기서 나와요. <b>분까지</b> 적어 주세요 — 오후 3시는 <b>15</b>시예요.</p>
      {s.hourKnown && s.hour !== null && <p className="entry-selection" role="status">{s.hour < 12 ? "오전" : "오후"} {s.hour % 12 || 12}시 {String(s.minute ?? 0).padStart(2, "0")}분 · {s.city} 기준</p>}

      <button className="btn" disabled={!ready || !s.hourKnown || s.hour === null} onClick={() => go("a6")}>이대로 계산하겠습니다</button>
      <button className="btn gh" disabled={!ready} onClick={() => go("a4")}>태어난 시각을 모릅니다</button>
      <button className="entry-text-button" onClick={() => go("a2")}>{s.name ? `별칭 바꾸기 · ${s.name}` : "별칭도 정하고 싶어요 · 선택"}</button>
    </div></Shell>;
  }

  if (step === "a4") return <Shell screen="a4" title="태어난 시각" onBack={back}><div className="entry-step">
    <p className="entry-eyebrow">03 · 모르면 모르는 대로</p><h1>시각은<br />물어보면 나오오.</h1>
    <p className="entry-lead">출생 시각은 집에 남아 있는 경우가 많소.<br />먼저 물어보고, 그래도 모르면 그대로 갑시다.</p>
    <a className="btn" href={ASK_HOME} onClick={() => track("hour_help", "a4")}>집에 문자로 물어보겠습니다</a>
    <p className="entry-footnote">문자 앱이 열리고 보낼 말이 적혀 있어요. 보내는 것은 직접 하시면 돼요.</p>
    <details className="entry-evidence" open><summary>모르는 채로 보면 무엇이 빠지나요?</summary>
      <p>여덟 글자 가운데 <b>시주 두 글자</b>를 비웁니다. 임의의 시각으로 채우지 않아요.</p>
      <p><b>그대로 남는 것</b> — 여섯 글자, 오행 개수, 대표로 잡히는 자리, 대운이 바뀌는 나이, 희소도.</p>
      <p><b>빠지는 것</b> — 시주에 걸린 신살과 자식·아랫사람 자리, 그리고 시주가 더했을 오행 무게.</p>
    </details>
    <button className="btn gh" onClick={() => { s.set({ hourKnown: false, hour: null, minute: 0, chartId: null, features: null }); go("a6"); }}>모르는 채로 보겠습니다</button>
    <button className="entry-text-button" onClick={() => go("a3")}>시각을 알아냈어요 · 다시 적기</button>
  </div></Shell>;

  if (step === "a4b") return <Shell screen="a4b" title="성향 비교 · 선택" onBack={back}><div className="entry-step">
    <p className="entry-eyebrow">선택 항목</p><h1>내가 아는 나와도<br />비교해볼까요?</h1>
    <p className="entry-lead">알고 있는 성향 유형이 있다면 골라주세요. 이어지는 무료 풀이에서 사주 해석과 나란히 볼 수 있어요.</p>
    <p className="entry-footnote">아래 <b>열여섯 칸</b> 가운데 하나를 눌러 주시오. 사주 계산값을 바꾸거나 성격을 진단하는 항목은 아니에요. 특정 상표와 무관한 성향 비교예요.</p>
    <div className="entry-axis" role="group" aria-label="성향 4글자 선택">{AXIS4.map(type => <button key={type} aria-pressed={s.axis4 === type} onClick={() => s.set({ axis4: s.axis4 === type ? null : type })}>{type}</button>)}</div>
    <button className="btn" disabled={!s.axis4} onClick={() => go(s.features ? "a7" : "a6")}>이 성향을 더해 보겠습니다</button>
    <button className="btn gh" onClick={() => { s.set({ axis4: null }); go(s.features ? "a7" : "a6"); }}>사주만으로 보겠습니다</button>
  </div></Shell>;

  if (step === "a6") return <Shell screen="a6" title="해석 준비" onBack={back}>
    {/*
      ★ 입력 화면 다섯이 연출 점수 최하위였습니다(a6 43 · a4b 46 · a2 48 ·
        a3 56 · a4 57). 글로 메울 자리가 아니오 — 그림이 없었습니다.
        발주 목록에 있는데 아무 화면도 안 부르던 장면 셋을 제자리에
        놓습니다 (`altar` 명식 · `facing` 훅 · `fold` 페이월).
    */}
    <Scene id="altar" />
    <div className="entry-step">
    <p className="entry-eyebrow">내 정보 확인</p><h1>{s.features ? <>그대의 질문을<br />읽을 준비가 됐소.</> : <>태어난 정보로<br />여덟 글자를 세고 있소.</>}</h1>{context}
    <p className="entry-footnote">{s.year}년 {s.month}월 {s.day}일 · {s.city} · {s.hourKnown ? `${s.hour}시 ${s.minute ?? 0}분` : "시각 모름 · 시주 제외"}</p>
    {error && <div className="warn" role="alert"><p>{error}</p><button className="btn gh" onClick={() => go("a3")}>입력 정보 수정하기</button><button className="btn" disabled={busy} onClick={calculate}>다시 계산하기</button></div>}
    {!s.features && !error && <p role="status">출생 날짜와 고을을 확인하고 있어요.</p>}
    {s.features && <><Pillars f={s.features} />
      <p className="entry-lead">네 장으로 읽어드리겠소.</p>
      <ol className="entry-preview">
        <li><span>01</span><div><b>세어 본 것</b></div></li>
        <li><span>02</span><div><b>그래서 이렇게</b></div></li>
        <li><span>03</span><div><b>언제 바뀌오</b></div></li>
        <li><span>04</span><div><b>오늘 한 가지</b></div></li>
      </ol>
      <button className="btn" onClick={() => go("a7")}>첫 해석을 읽겠습니다 · 무료</button>
      {axisLink}
      <details className="entry-evidence"><summary>계산한 명식과 보정 내역 확인하기</summary><ManseTable f={s.features} /><CalcPanel f={s.features} />
        {/*
          ★ 유파가 갈리는 자리는 **저쪽 답까지** 냅니다. 감추면 숨긴 것이
            됩니다 — 다른 만세력과 대 봤을 때 「오행부터 잘못 나옴」이
            실사용자 불만 6위입니다(docs/45 §3-3).
        */}
        {s.divergence?.cases?.map((c, index) => <div key={index}><p>{c.why}</p><p>{c.ours} · {c.mine}</p><p>다른 방식: {c.theirs} · {c.alt}</p></div>)}
        {!!s.divergence?.cases?.length && <p className="entry-footnote">이 서비스는 위의 첫 번째 명식으로 해석하오. 어느 쪽도 틀린 것이 아니라 읽는 기준이 다른 것이오.</p>}
      </details></>}
  </div></Shell>;

  return <Shell screen="a7" title={`${lens.name}의 첫 해석`} onBack={back}>
    <Scene id="facing" />{context}
    {!s.chartId && <div className="entry-step"><h1>해석할 출생 정보가 필요해요.</h1><button className="btn" onClick={() => go("a3")}>생년월일 입력하기</button></div>}
    {s.chartId && !segments && !error && <p className="entry-lead" role="status">{lens.name}이 그대의 질문과 사주를 함께 살펴보고 있소.</p>}
    {error && <div className="warn" role="alert"><p>{error}</p><button className="btn" onClick={retry}>첫 해석 다시 불러오기</button></div>}
    {segments && s.chartId && <EntryReading key={`${s.chartId}:${s.concern}:${s.cur}`} segments={segments} chartId={s.chartId} concern={s.concern} lensId={s.cur} onMiss={onMiss} onDone={onDone} />}
    {/*
      ★ 마감에서 **앞을 깎지 않습니다.** 「여덟 글자 중 셋으로 본 것」은
        방금 좋았다고 느낀 손님에게 8분의 3짜리였다고 말하는 셈입니다.
        격차는 **남은 것**으로 말합니다.
      ★ 그리고 **분모를 바꿉니다.** 방금 읽은 것은 줄이지 않고 그대로 두되,
        그것이 스무 관점 가운데 하나라는 **사실**을 적습니다. 무료를
        깎는 말이 아니라 세는 말입니다.
    */}
    {done && <section className="entry-next"><p className="entry-eyebrow">첫 해석을 읽었어요</p>
      <h2>여기까지가<br />스무 사람 중 <em>한 사람</em>의 셈이오.</h2>
      <p>{misses
        ? "맞지 않았던 장면은 따로 남겨 뒀소. 아니라고 한 자리는 다시 세우지 않겠소 — 남은 셈으로 이어 가오."
        : "읽으면서 ‘이걸 어떻게 알았지’ 싶은 대목이 있었다면, 그건 지어낸 말이 아니라 세어 본 값이오. 근거 줄을 펴면 그 셈이 그대로 있소."}</p>
      <p>같은 여덟 글자를 {lens.name} 말고도 열아홉 사람이 저마다 다른 자리에서 보오. 다음 풀이도 값을 치르지 않고 끝까지 읽을 수 있소.</p>
      <button className="btn" onClick={() => router.push("/pay?step=d0")}>{copy.next} · 무료</button>
      <p className="entry-footnote">다음 풀이까지 무료예요. 유료 해석은 가격과 포함 내용을 확인한 뒤 선택할 수 있어요.</p>
      {axisLink}
      <button className="entry-text-button" onClick={() => router.push("/summary")}>여기까지 보고 내 분석지 열기</button>
    </section>}
    <RestHere visits={s.visits} hookMisses={misses} hour={new Date().getHours()} concern={s.concern} returning={s.visits > 1} />
  </Shell>;
}
