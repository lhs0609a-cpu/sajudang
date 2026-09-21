"use client";

/** @screen a1 a2 a3 a4 a4b a5 a6 a7 */

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Shell from "@/components/Shell";
import EntryArt, { ENTRY_QUESTIONS } from "@/components/EntryArt";
import RestHere from "@/components/RestHere";
import { ConcernArtwork } from "@/components/ConcernArtwork";
import { track, useScreen } from "@/lib/track";
import { birthMessageFrom, birthProblem } from "@/lib/birth";
import { needsGuardian } from "@/lib/biz";
import Scene from "@/components/scene/Scene";
import { Narration, Progress } from "@/components/Narration";
import { CalcPanel, ManseTable, Pillars } from "@/components/Chart";
import HookSegments from "@/components/HookSegments";
import { api, ApiError } from "@/lib/api";
import { LENS_BY_ID } from "@/lib/lenses";
import { CONCERNS, useSession } from "@/lib/store";
import type { HookSegment } from "@shared/chart";

type Step = "a1" | "a2" | "a3" | "a4" | "a4b" | "a5" | "a6" | "a7";

const AXIS4 = [
  "INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
  "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP",
];

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

const ORDER: Step[] = ["a1", "a5", "a3", "a4", "a4b", "a6", "a7", "a2"];
const STEPS: Step[] = ORDER;

const PROGRESS_TOTAL = 3;

function EntryInner() {
  const router = useRouter();
  const params = useSearchParams();
  const s = useSession();
  // 관리자 레일이 ?step=a5 로 바로 건너뛸 수 있게 한다
  const asked = params.get("step") as Step | null;
  const [step, setStep] = useState<Step>(
    asked && STEPS.includes(asked) ? asked : "a1");

  const [trail, setTrail] = useState<Step[]>([]);

  useEffect(() => {
    if (asked && STEPS.includes(asked)) {
      setStep(asked);
    } else if (!asked) {
      setStep("a1");
      setTrail([]);
    }
  }, [asked]);

  const go = (next: Step) => {
    setTrail((t) => [...t, step]);
    setStep(next);

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

  const [error, setError] = useState<string | null>(null);
  const [hookRetry, setHookRetry] = useState(0);
  const [segments, setSegments] = useState<HookSegment[] | null>(null);
  const [hookDone, setHookDone] = useState(false);

  const [misses, setMisses] = useState(0);
  const [turned, setTurned] = useState(false);
  useEffect(() => {
    setSegments(null);setHookDone(false);setMisses(0);setTurned(false);
  }, [s.chartId,s.concern,s.cur,s.axis4,s.name]);

  // 화면 이름이 곧 step 입니다. 어디서 나가는지 이걸로 셉니다.
  useScreen(step);

  const lens = LENS_BY_ID[s.cur] ?? LENS_BY_ID.pungun;

  const buildChart = async () => {

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

  useEffect(() => {
    if (step === "a6" && s.features) {
      track("chart_completed", "a6");
    }
  }, [step, s.features]);

  useEffect(() => {
    if (step !== "a7" || !s.chartId || segments) return;
    let alive = true;
    api.hook({
      chart_id: s.chartId, concern: s.concern, axis4: s.axis4,
      name: s.name, lens_id: s.cur,
      misses: Math.max(misses, s.hookReview?.edition === "first-reading-v2" && s.hookReview.chartId === s.chartId && s.hookReview.concern === s.concern && s.hookReview.lensId === s.cur
        ? Object.values(s.hookReview.answers).filter(answer=>answer===false).length : 0),
    })
      .then((r) => alive && setSegments(r.segments))
      .catch((e) => alive && setError(e instanceof ApiError ? e.message : "훅을 만들지 못했소."));
    return () => { alive = false; };
  }, [step, s.chartId, s.concern, s.axis4, s.name, s.cur, segments, misses, hookRetry]);

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
        prev ? prev.map((seg, i) => (i < n ? seg : r.segments[i] ?? seg)) : r.segments))
      .catch(() => {  });
  };

if (step === "a1") {
    return <Shell screen="a1" bare>
      <div className="entry-welcome">
        <div className="entry-cover"><EntryArt scene="threshold" priority />
          <div className="entry-brand"><span className="brand-seal" aria-hidden="true">星<br/>辰</span><span>성신당<small>별에 묻고, 나를 읽다</small></span></div>
          <span className="entry-cover-note">오늘의 마음을 들고 오시오.</span>
        </div>
        <div className="entry-invitation">
          <p className="entry-eyebrow">나를 이해하는 첫 번째 밤</p>
          <h1>왜 나는, 비슷한 일에<br/>마음이 걸릴까.</h1>
          <p className="entry-lead">돈, 일, 사랑, 사람.<br/>지금 그대가 품은 질문부터 읽겠소.</p>
          <button className="btn" onClick={() => { s.set({cur:"pungun"}); go("a5"); }}>내 고민으로 무료 해석 보기 <span aria-hidden="true">↗</span></button>
          <p className="entry-footnote">첫 해석 무료 · 태어난 시간은 몰라도 되오</p>
        </div>
      </div>
      <section className="entry-letter">
        <span className="entry-eyebrow">풍운도령의 초대</span>
        <p>그대를 한마디로 정하지 않겠소.<br/>어떤 마음으로 여기까지 왔는지,<br/><b>함께 읽어 보겠소.</b></p>
        <div className="entry-benefits"><span>고민에 맞는 해석</span><span>확인할 수 있는 근거</span><span>오늘 해볼 일 하나</span></div>
      </section>
      <details className="entry-faq"><summary>무엇을 알려주면 되오?</summary><p>생년월일과 성별, 태어난 지역을 알려주시오. 시간과 별칭, 성향은 아는 만큼만 적어도 되오. 전통 사주를 바탕으로 자신을 돌아보는 해석이오.</p></details>
      <details className="entry-faq"><summary>무료로 어디까지 볼 수 있소?</summary><p>첫 해석과 고민에 대한 무료 풀이를 볼 수 있소. 더 깊이 읽고 싶을 때, 포함된 내용과 가격을 확인하고 선택하시오.</p></details>
    </Shell>;
  }
  if (step === "a2") {
    return <Shell screen="a2" title="별칭 · 선택" onBack={back}>
      <EntryArt scene="desk" caption="그대의 이름으로 남기는 이야기" priority />
      <p className="entry-eyebrow">선택 입력</p>
      <h1 className="conversion-title">어떻게 부르면<br/>되겠소?</h1>
      <p className="conversion-lead">별명도 좋소. 비워두어도 해석은 같소.</p>
      <label htmlFor="entry-alias">별칭 · 최대 12글자</label>
      <input id="entry-alias" className="fld" maxLength={12} placeholder="듣고 싶은 이름" value={s.name} onChange={e => s.set({name:e.target.value,hookReview:null})} />
      <button className="btn mt" onClick={() => go("a4")}>이 이름으로 이어가기</button>
      <button className="btn gh" onClick={() => {s.set({name:"",hookReview:null});go("a4");}}>별칭 없이 이어가기</button>
    </Shell>;
  }
  if (step === "a3") {
    const filled = s.year !== null && s.month !== null && s.day !== null;
    const bad = filled ? birthProblem(s.year,s.month,s.day) : null;
    const minor = filled && !bad && needsGuardian(s.year!,s.month!,s.day!);
    return <Shell screen="a3" title="태어난 정보" onBack={back}>
      <Progress step={2} total={PROGRESS_TOTAL} />
      <EntryArt scene="desk" caption="누구의 이야기도 아닌, 그대의 이야기" priority />
      <p className="entry-eyebrow">02 · 태어난 날</p>
      <h1 className="conversion-title">그대의 이야기가<br/>시작된 날.</h1>
      <p className="conversion-lead">태어난 날로 사주를 세우고,<br/>고른 고민에 맞춰 해석하오.</p>
      <form onSubmit={e => {e.preventDefault();if(filled && !bad && !minor && s.sexSet)go("a4");}}>
        <p className="entry-input-note">양력 기준 · 음력 생일은 양력으로 바꿔 적어주시오.</p>
        <div className="f3">
          {([['year','태어난 해',4,'1993'],['month','월',2,'11'],['day','일',2,'25']] as const).map(([key,label,max,placeholder]) =>
            <div key={key}><label htmlFor={`birth-${key}`}>{label}</label><input id={`birth-${key}`} className="fld" inputMode="numeric" maxLength={max} placeholder={placeholder}
              aria-invalid={!!bad} aria-describedby={bad ? 'birth-error' : undefined} value={s[key] ?? ''}
              onChange={e => {const v=e.target.value.replace(/[^0-9]/g,'').slice(0,max);s.set({[key]:v===''?null:Number(v),features:null,chartId:null});setError(null);}} /></div>)}
        </div>
        {bad && <p className="warn" id="birth-error" role="alert">{bad}</p>}
        {minor && <p className="warn" role="alert">만 14세 미만은 보호자 동의 절차가 필요해 현재 서비스를 이용할 수 없소.</p>}
        <fieldset className="entry-fieldset"><legend>성별</legend><div className="og c2">
          {([['F','여성'],['M','남성']] as const).map(([value,label]) => <button type="button" key={value} className={`op ${s.sexSet && s.sex===value?'on':''}`} aria-pressed={s.sexSet && s.sex===value} onClick={() => s.set({sex:value,sexSet:true,features:null,chartId:null})}>{label}</button>)}
        </div><p className="entry-input-note">전통 사주에서 십 년 단위의 흐름을 계산하는 데 쓰오.</p></fieldset>
        <label htmlFor="birth-city">태어난 지역</label>
        <select id="birth-city" className="fld" value={s.city} onChange={e => s.set({city:e.target.value,features:null,chartId:null})}>
          {CITY_GROUPS.map(([g,cs]) => <optgroup key={g} label={g}>{cs.map(c => <option key={c} value={c}>{c}</option>)}</optgroup>)}
        </select>
        <button type="submit" className="btn mt" disabled={!filled || !!bad || !!minor || !s.sexSet}>태어난 시간으로 이어가기</button>
      </form>
      <p className="entry-footnote">입력 정보는 사주 계산에 사용하오. <a href="/legal">개인정보 처리 안내</a></p>
    </Shell>;
  }
  if (step === "a4") {
    return <Shell screen="a4" title="태어난 시간" onBack={back}>
      <Progress step={3} total={PROGRESS_TOTAL} />
      <EntryArt scene="night" caption="기억하는 만큼만, 천천히" priority />
      <p className="entry-eyebrow">03 · 태어난 시간</p>
      <h1 className="conversion-title">아는 만큼만<br/>알려주시오.</h1>
      <p className="conversion-lead">정확한 시간을 모르면 비워두시오.<br/>태어난 날까지의 정보로 읽을 수 있소.</p>
      <div className="f3 hm entry-time-fields">
        <div><label htmlFor="birth-hour">시 · 0–23</label><input id="birth-hour" className="fld" inputMode="numeric" maxLength={2} placeholder="15" value={s.hourKnown && s.hour!==null?s.hour:''}
          onChange={e => {const v=e.target.value.replace(/[^0-9]/g,'').slice(0,2);s.set({hourKnown:true,hour:v===''?null:Number(v),features:null,chartId:null});}} /></div>
        <div><label htmlFor="birth-minute">분 · 0–59</label><input id="birth-minute" className="fld" inputMode="numeric" maxLength={2} placeholder="00" value={s.minute}
          onChange={e => s.set({minute:Number(e.target.value.replace(/[^0-9]/g,'').slice(0,2)),features:null,chartId:null})} /></div>
      </div>
      {s.hourKnown && ((s.hour ?? 0)>23 || s.minute>59) && <p className="warn" role="alert">시는 0~23, 분은 0~59 사이로 적어주시오.</p>}
      <button className="btn mt" disabled={!s.hourKnown || s.hour===null || s.hour>23 || s.minute>59} onClick={() => go("a4b")}>이 시간으로 이어가기</button>
      <button className="btn gh" onClick={() => {s.set({hourKnown:false,hour:null,minute:0,chartId:null,features:null});go("a4b");}}>시간을 모르오 · 그대로 이어가기</button>
      <p className="entry-footnote">다음은 성향 비교요. 선택하지 않고 바로 해석을 볼 수도 있소.</p>
      <details className="entry-faq"><summary>별칭도 적고 싶소</summary><p>풀이에서 그 이름으로 부르겠소.</p><button className="btn gh" onClick={() => go("a2")}>별칭 입력</button></details>
    </Shell>;
  }
  if (step === "a4b") {
    return <Shell screen="a4b" title="성향 비교 · 선택" onBack={back}>
      <EntryArt scene="night" caption="내가 아는 나, 새롭게 읽는 나" priority />
      <p className="entry-eyebrow">선택 · 나를 보는 또 하나의 시선</p>
      <h1 className="conversion-title">내가 생각하는 나와<br/>어디가 닮았을까.</h1>
      <p className="conversion-lead">알고 있는 성향이 있다면 골라주시오.<br/>사주 해석과 나란히 놓고 함께 읽겠소.</p>
      <button className="btn gh entry-skip" onClick={() => {s.set({axis4:null,hookReview:null});go("a6");}}>잘 모르오 · 사주만으로 보기</button>
      <div className="entry-axis-grid" role="group" aria-label="성향 네 글자 선택">{AXIS4.map(t => <button key={t} className={`op ${s.axis4===t?'on':''}`} aria-pressed={s.axis4===t} onClick={() => s.set({axis4:t,hookReview:null})}>{t}</button>)}</div>
      <button className="btn mt" disabled={!s.axis4} onClick={() => go("a6")}>선택한 성향으로 무료 해석 보기</button>
      <p className="entry-footnote">성향 선택은 사주 계산을 바꾸지 않소.<br/>둘 중 어느 쪽이 진짜 그대인지 판정하는 검사도 아니오.</p>
    </Shell>;
  }
  if (step === "a5") {
    return <Shell screen="a5" title="지금의 고민" onBack={back}>
      <Progress step={1} total={PROGRESS_TOTAL} />
      <p className="entry-eyebrow">01 · 오늘의 마음</p>
      <h1 className="conversion-title">오늘은 어떤 답이<br/>가장 필요하오?</h1>
      <p className="conversion-lead">하나만 골라도 좋소.<br/>그 이야기부터 시작하겠소.</p>
      <div className="entry-concern-grid" role="group" aria-label="지금 가장 마음에 걸리는 고민 하나 선택">
        {CONCERNS.map(c => <button type="button" key={c.id} className={`entry-concern ${s.concernSet && s.concern===c.id?'selected':''}`} aria-pressed={s.concernSet && s.concern===c.id}
          onClick={() => s.set({concern:c.id,concernSet:true,topicPick:null})}>
          <span className="entry-concern-image"><ConcernArtwork concern={c.id}/><span className="entry-concern-check" aria-hidden="true">{s.concernSet && s.concern===c.id?'✓':'↗'}</span></span>
          <span className="entry-concern-text"><b>{c.label}</b><span>{ENTRY_QUESTIONS[c.id].question}</span></span>
        </button>)}
      </div>
      <p className="entry-selection" aria-live="polite">{s.concernSet?ENTRY_QUESTIONS[s.concern].promise:'지금 마음이 가는 질문을 고르시오.'}</p>
      <button className="btn" disabled={!s.concernSet} onClick={() => go("a3")}>{s.concernSet?`${CONCERNS.find(c=>c.id===s.concern)?.label} 이야기로 이어가기`:'고민을 하나 골라주시오'}</button>
    </Shell>;
  }
  if (step === "a6") {
    return <Shell screen="a6" title="나의 사주" onBack={back}>
      <EntryArt scene="desk" caption="태어난 순간에서, 지금의 고민으로" priority />
      {error && <div className="warn" role="alert"><p>{error}</p><button className="btn gh" onClick={() => go("a3")}>입력 정보 수정하기</button><button className="btn gh" disabled={busy} onClick={() => void buildChart()}>다시 계산하기</button></div>}
      {!s.features && !error && <div className="entry-loading" role="status"><span className="entry-loading-orbit" aria-hidden="true">✧</span><h1 className="conversion-title">그대의 이야기를<br/>펼치고 있소.</h1><p>태어난 정보를 바탕으로 사주를 계산 중이오.</p></div>}
      {s.features && <>
        <p className="entry-eyebrow">그대의 사주가 준비되었소</p>
        <h1 className="conversion-title">이제, 그대의<br/>{CONCERNS.find(c=>c.id===s.concern)?.label} 이야기를 보오.</h1>
        <div className="entry-chart"><Pillars f={s.features} /><p className="entry-footnote">태어난 해·달·날·시를 각각 두 글자로 옮긴 것이오.<br/>{s.features.hour_known?'네 기둥, 여덟 글자로 보오.':'시간은 몰라 세 기둥, 여섯 글자로 보오.'}</p></div>
        <p className="entry-personal-promise">{ENTRY_QUESTIONS[s.concern].promise}</p>
        <button className="btn" onClick={() => go("a7")}>내 고민의 무료 해석 읽기 <span aria-hidden="true">↗</span></button>
        <details className="entry-faq"><summary>계산 근거와 보정 내역</summary><ManseTable f={s.features}/><CalcPanel f={s.features}/>
          {s.divergence?.cases?.map((c,i)=><div className="conversion-note" key={i}><p>{c.why}</p><p>{c.ours}<br/>{c.mine}</p><p>다른 계산 방식: {c.theirs}<br/>{c.alt}</p></div>)}
        </details>
      </>}
    </Shell>;
  }
  return <Shell screen="a7" title={`${lens.name} · 첫 해석`} onBack={back}>
    {lens.id==='pungun'?<EntryArt scene="reading" caption="풍운도령 · 그대의 이야기를 듣다" priority />:<Scene id="facing"/>}
    <p className="entry-eyebrow">{CONCERNS.find(c=>c.id===s.concern)?.label} · 그대에게 건네는 다섯 마디</p>
    <h1 className="entry-reading-title">{ENTRY_QUESTIONS[s.concern].question}</h1>
    <p className="entry-reading-note">맞는 말은 마음에 담고, 다른 말은 알려주시오.</p>
    {!segments && !error && <p role="status" className="entry-selection">고른 고민에 맞는 해석을 준비하고 있소.</p>}
    {error && <div className="warn" role="alert"><p>{error}</p><button className="btn" onClick={() => {setError(null);setHookRetry(n=>n+1);}}>무료 해석 다시 불러오기</button></div>}
    {segments && s.chartId && <HookSegments key={`${s.chartId}:${s.cur}:${s.concern}`} segments={segments} chartId={s.chartId} lensId={s.cur} concern={s.concern} charName={lens.name} onMiss={onMiss} onDone={() => setHookDone(true)}/>}
    {hookDone && <section className="entry-afterword">
      <p className="entry-eyebrow">이야기는 여기서 이어지오</p><h2>마음에 남은 한마디,<br/>그 이유까지 읽어보시오.</h2>
      <p>{ENTRY_QUESTIONS[s.concern].promise}<br/>다음 무료 풀이에서 핵심 근거를 확인하고, 더 궁금한 질문을 골라보오.</p>
      <button className="btn" onClick={() => router.push('/pay?step=d0')}>{ENTRY_QUESTIONS[s.concern].next}</button>
      <p className="entry-footnote">다음 요약까지 무료요. 심층 해석은 내용을 확인한 뒤 선택할 수 있소.</p>
      <button className="btn gh" onClick={() => router.push('/summary')}>여기까지 본 내용 간직하기</button>
    </section>}
    <RestHere visits={s.visits} hookMisses={misses} hour={new Date().getHours()} concern={s.concern} returning={s.visits>1}/>
  </Shell>;
}

export default function EntryPage() {
  return (
    <Suspense fallback={<Shell bare><Narration lines={["대문을 여는 중이오."]} /></Shell>}>
      <EntryInner />
    </Suspense>
  );
}
