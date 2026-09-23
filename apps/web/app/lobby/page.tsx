"use client";
import { CHARACTER_QUESTIONS } from "@/lib/curiosity";

/**
 * @screen b1 b2 b3 b4
 * B · 둘러보다 — b1 진열대 · b2 스무 사람 · b3 그 사람 · b4 내 명식
 *
 * 미출시 캐릭터는 실루엣으로 둡니다. 결제 버튼을 붙이지 않습니다.
 */
import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Shell from "@/components/Shell";
import Scene from "@/components/scene/Scene";
import CharArt from "@/components/CharArt";
import ActOut from "@/components/ActOut";
import { Narration, Say } from "@/components/Narration";
import { CalcPanel, ElementBar, Pillars, Summary } from "@/components/Chart";
import { LENSES, LENS_BY_ID } from "@/lib/lenses";
import { useSession } from "@/lib/store";
import { useScreen } from "@/lib/track";
import { characterConcern } from "@/lib/character-topic";

type Tab = "b1" | "b2" | "b3" | "b4";

const GROUPS = ["정통", "검사", "술수", "관계", "맥락", "정서"];

const TABS: Tab[] = ["b1", "b2", "b3", "b4"];

/** 못 움직이는 손님에게는 부드러운 스크롤이 멀미가 됩니다. */
function reducedMotion(): boolean {
  if (typeof window === "undefined") return false;
  return !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
}

function LobbyInner() {
  const router = useRouter();
  const params = useSearchParams();
  const s = useSession();
  const asked = params.get("tab") as Tab | null;
  const [tab, setTab] = useState<Tab>(asked && TABS.includes(asked) ? asked : "b1");
  useEffect(() => { if (asked && TABS.includes(asked)) setTab(asked); }, [asked]);
  const lens = LENS_BY_ID[s.cur] ?? LENSES[0];

  const released = LENSES.filter((l) => l.released);

  const openLens = (lensId: string) => {
    const concern = characterConcern(lensId, s.concern);
    const topic = s.topicPick;
    const hasSpecificSituation = topic?.concern === concern && topic?.lensId === lensId
      && !!topic.choice && !!topic.choice2 && !!topic.choice3 && !!topic.choice4 && !!topic.choice5;
    s.set({ cur: lensId, concern, tier: s.chartId ? 'all' : s.tier });
    s.markRead(lensId);
    if (!s.chartId) {
      router.push('/?step=a5');
      return;
    }
    const reportPath = `/report/${lensId}?tab=c2`;
    router.push(hasSpecificSituation
      ? reportPath
      : `/?step=a5b&next=${encodeURIComponent(reportPath)}`);
  };

  /*
   * ★ 스무 사람 화면에서 고른 사람 (2026-09-02).
   *
   *   손님이 말했습니다 — "캐릭터 클릭하면 그 캐릭터가 비추이면서,
   *   아래 그 캐릭터 있는 곳으로 이동해줘야지."
   *
   *   그래서 화면을 갈아 치우는 대신 **불을 켜고 데려갑니다.**
   *   목록이 위에 남아 있어야 스무 명을 견줄 수 있습니다.
   */
  const [picked, setPicked] = useState<string | null>(null);
  const pickedLens = picked ? LENS_BY_ID[picked] : null;
  const seatRef = useRef<HTMLDivElement>(null);
  const topRef = useRef<HTMLDivElement>(null);

  /* 열린 자리로 데려갑니다. 그림이 그려진 뒤라야 자리가 정해집니다. */
  useEffect(() => {
    if (!picked) return;
    const t = setTimeout(() => {
      seatRef.current?.scrollIntoView({
        behavior: reducedMotion() ? "auto" : "smooth",
        block: "start",
      });
    }, 40);
    return () => clearTimeout(t);
  }, [picked]);

  /* 화면이 바뀌면 고른 것을 놓습니다 — 남겨 두면 딴 데서 튀어나옵니다. */
  useEffect(() => { setPicked(null); }, [tab]);

  if (tab === "b2") {
    return (
      <Shell screen="b2" title="스무 사람">
        <Scene id="hall" />
        {/*
          ★ 울림 20 · 명확 45 로 낮던 자리입니다. 스무 명을 늘어놓기만
            하고 **그대 얘기가 한 줄도** 없었습니다. 고르기 어려운 게
            아니라 **골라야 할 까닭**이 없는 화면이었소.
        */}
        <header className="editorial-heading"><p className="conversion-kicker">스무 사람, 스무 가지 질문</p><h1>읽는 순간 마음에 걸린<br/>그 질문부터.</h1><p>같은 명식에서도 먼저 짚는 대목은 다르오.<br/>계속 생각나는 질문을 가진 사람을 골라보시오.</p></header>
        <p className="conversion-note">입력 전에도 자유롭게 둘러보시오. 인물을 누르면 소개가 열리오. 이미 입력한 정보는 이어 쓰고, 구매한 해석은 바로 다시 읽을 수 있소.</p>
        <div ref={topRef} />
        {GROUPS.map((g) => (
          <div key={g}>
            <div className="lab">{g}</div>
            <div className="og c2">
              {LENSES.filter((l) => l.group === g).map((l) => (
                <button key={l.id}
                        className={`op face ${l.released ? "" : "off"}`
                                   + (picked === l.id ? " on lit" : "")}
                        aria-current={picked === l.id ? "true" : undefined}
                        disabled={!l.released}
                        /*
                         * ★ 누르면 **화면을 갈아 치우지 않습니다** (2026-09-02).
                         *
                         *   전에는 곧바로 b3 으로 넘어가, 스무 명을 견주려던
                         *   손님이 한 명 볼 때마다 목록을 잃었습니다. 이제
                         *   누른 사람에 불이 들어오고 아래 자리가 열립니다.
                         *   목록은 그대로 위에 있습니다.
                         */
                        onClick={() => { s.set({ cur: l.id }); setPicked(l.id); }}>
                  {/* ★ 초상이 들어올 자리. 파일이 없으면 색과 한자로 버팁니다.
                      전에는 이 자리가 아예 없어서, 스무 장을 만들어도
                      갈 데가 없었습니다. (tools/asset_audit.py) */}
                  <CharArt lens={l} size="chip" />
                  <span className="who">
                    <b style={{ color: l.released ? l.color : "var(--paper3)" }}>
                      {l.released ? l.name : "● ● ●"}
                    </b>
                    {/*
                      ★ 생김새 말고 **무엇을 잘 보는 사람인지**를 앞에 냅니다.
                        전에는 「차가운 미남」 같은 생김새뿐이라, 손님이
                        무엇을 사는지 모른 채 골라야 했습니다. 재회가 걸린
                        사람은 연담을, 돈이 걸린 사람은 행수를 찾아야 합니다.
                    */}
                    {/*
                      ★ 무엇을 들고 오는 자리인지를 **맨 앞**에 냅니다
                        (2026-09-02). 전에는 「왜 하필 지금」 「신살과
                        자리」처럼 **읽는 법**만 적혀 있었습니다. 그건 이
                        집이 쓰는 말이지 손님이 쓰는 말이 아닙니다 —
                        재회가 걸린 사람이 연담을 못 찾고 나갔습니다.
                    */}
                    {l.released && (
                      <span className="topics">
                        {l.topics.split(" · ").map((t) => (
                          <i key={t}>{t}</i>
                        ))}
                      </span>
                    )}
                    <span className="spec">
                      {l.released ? l.specialty : "아직 자리에 없음"}
                    </span>
                    {l.released && <span className="character-question">{CHARACTER_QUESTIONS[l.id]}</span>}
                  </span>
                </button>
              ))}
            </div>
          </div>
        ))}

        {/*
          ★ 고른 사람의 자리. 목록 **아래**에 열리고 그리로 데려갑니다.
            여기서 바로 들을 수 있고, 목록으로 되돌아가는 길도 둡니다.
        */}
        {pickedLens && (
          <div className="seatnow" ref={seatRef}>
            <div className="lab">고른 자리</div>
            <div className="consultant-intro"><CharArt lens={pickedLens} size="chip" /><h2>{CHARACTER_QUESTIONS[pickedLens.id]}</h2></div>
            <div className="mec">
              <div>
                <div className="gz" style={{ color: pickedLens.color }}>
                  {pickedLens.name} · {pickedLens.hanja}
                </div>
                <div className="nm">
                  <b className="spec">{pickedLens.specialty}</b> · {pickedLens.epithet}
                </div>
                <div className="tr">{pickedLens.group}</div>
              </div>
            </div>
            <div className="topicrow">
              <span className="k">이런 걸 들고 오시오</span>
              <span className="topics">
                {pickedLens.topics.split(" · ").map((t) => <i key={t}>{t}</i>)}
              </span>
            </div>
            {/* ★ 말하는 사람을 못박습니다. 안 넘기면 얼굴은 **지금 고른
                사람**이 나와, 이름과 얼굴이 어긋납니다. */}
            <p className="conversion-note">먼저 무료 판정에서 내 실제 장면과 맞는지 대보시오. 결제 전에는 이 사람이 추가로 가를 질문·첫 문장·분량·가격을 모두 보여드리오.</p>
            <button className="btn mt" onClick={() => {
              openLens(pickedLens.id);
            }}>
              {s.chartId ? '이 사람의 판정 바로 읽기 · 구매 본문 열기' : '내 고민을 이 사람에게 무료로 판정받기'}
            </button>
            <p className="sm">
              {pickedLens.price > 0 ? `첫 분석 무료 · 심층 해석 ${pickedLens.price.toLocaleString()}원` : '이 인물의 해석은 무료요.'}
            </p>
            <button className="btn gh" onClick={() => setTab("b3")}>
              이 사람 자리를 크게 보겠습니다
            </button>
            <button className="btn gh" onClick={() => {
              setPicked(null);
              topRef.current?.scrollIntoView({
                behavior: reducedMotion() ? "auto" : "smooth", block: "start",
              });
            }}>
              스무 사람 목록으로 돌아가겠습니다
            </button>
          </div>
        )}

        {/*
          ★ 당김 0점이던 자리입니다. 스무 명을 늘어놓고 끝났습니다.
            고르기 어려운 것이 문제가 아니라 **골라야 할 이유**가
            없던 것이 문제입니다. 브레이크(세션당 둘)를 그대로 두고
            그걸 **고를 이유**로 쓰오 — 지어낸 압박이 아닙니다.
        */}
        <ActOut kind="딜레마" next="그 사람의 자리">
          궁금한 자리를 자유롭게 오가시오.<br />
          생년월일을 다시 적지 않고 다른 판정 기준으로 읽으며, <b>구매한 본문도 즉시 다시 열 수 있소.</b>
        </ActOut>
        <button className="btn gh mt" onClick={() => setTab("b1")}>진열대로</button>
      </Shell>
    );
  }

  if (tab === "b3") {
    return (
      <Shell screen="b3" title={lens.name}>
        <Scene id="seat" />
        <p className="conversion-kicker">상담 전에 · 이 사람이 먼저 보는 질문</p>
        <h1 className="reading-title">{CHARACTER_QUESTIONS[lens.id] ?? lens.specialty}</h1>
        <div className="consultant-intro">
          <CharArt lens={lens} size="chip" />
          <div><h2>{lens.name}</h2><p>{lens.specialty}</p><p className="conversion-note">{lens.topics}</p></div>
        </div>
        <p className="conversion-lead">지금 마음에 걸린 일이 이 질문과 닿아 있소? 태어난 정보와 고른 고민을 놓고, {lens.name}이 먼저 짚는 대목부터 읽어보시오.</p>
        <section className="consultation-scope" aria-label="상담 전에 확인할 내용">
          <div><span>먼저, 무료로</span><strong>반복 원인 판정 + 오늘 행동 1개</strong><p>계산 근거와 내가 고른 실제 상황을 맞대어 읽소.</p></div>
          {lens.price > 0 ? <div><span>결제 전에 공개</span><strong>추가 질문 3개 + 실제 첫 문장 + 전체 분량</strong><p>가려진 결론이 무엇인지 먼저 보고 살지 정하시오.</p><b>{lens.price.toLocaleString()}원 · 이 인물의 전체 본문</b></div>
            : <div><span>이 자리의 해석</span><strong>값 없이 읽을 수 있소.</strong><p>오늘 마음에 남길 한 가지를 골라보시오.</p></div>}
        </section>
        {lens.released ? <button className="btn mt" onClick={() => {
          openLens(lens.id);
        }}>{s.chartId ? `${lens.name}의 판정과 구매 본문 바로 열기` : '내 고민과 태어난 정보로 무료 판정받기'}</button>
          : <p className="conversion-note">아직 자리에 앉지 않은 사람이오.</p>}
        <p className="conversion-note">무료 분석을 읽는 것만으로 결제되지 않소.</p>
        <button className="btn gh" onClick={() => setTab("b2")}>나와 맞는 질문을 던지는 다른 해석자 고르기</button>
      </Shell>
    );
  }

  if (tab === "b4") {
    return (
      <Shell screen="b4" title="내 명식">
        {s.features ? (
          <>
            {/*
              ★ 표부터 들이밀고 있었습니다. 표는 셈이지 말이 아니오.
                무슨 화면인지 한 줄 먼저 놓습니다 (콜드 오픈).
            */}
            <Narration lines={["도령이 셈한 종이를 그대로 내밀었다.",
                               "먹이 아직 번져 있다."]} />
            <p className="sm">
              <mark>감춘 것 없이 그대로요. 이 표 하나로 뒤의 모든 말이 나오오</mark> —
              집을 짓기 전에 재어 둔 땅의 치수 같은 것이오.
            </p>
            {/* ★ 팩폭 50 · 셀 수 있는 값 0. 표는 수로 가득한데
                **글에는 수가 하나도** 없었습니다. 표를 안 읽는
                손님에게는 이 줄이 표 전부요. */}
            <p className="sm">
              여덟 칸 중 시를 모르면 6글자로 서고, 알면 <b>8글자</b>요.
              막대는 5개, 십신(나를 기준으로 다른 글자에 붙인 이름 열 가지)은
              10개. 여태 한 번도 제 글자를 세어 본 적이 없었을 것이오 —
              여기 그대로 있소. 눌러 두고 혼자 지쳐 온 일도 이 여덟 글자 어딘가에 있소.
            </p>
            {/*
              ★ 여기가 61점이었습니다 (900자 자리에 334자).

                표와 막대는 다 있는데 **표를 읽는 사람 얘기가**
                없었습니다. 숫자만 들이밀면 손님은 자기 것으로
                안 보오. 울림 45 · 팩폭 60.

                해석은 안 얹습니다 — 그건 값을 치르는 자리 몫이오.
                여기서는 이 표가 무엇을 센 것인지만 말하오.
            */}
            <Say who="도령" lens="pungun">
              {s.hourKnown ? '태어난 해·달·날·시의 네 기둥을 계산했소.' : '태어난 시간을 몰라 시주(태어난 시의 두 글자) 없이 세 기둥을 계산했소.'}
              입력한 생년월일과 지역이 맞는지 먼저 확인하시오.
              <br />
              막대 다섯은 명식의 글자를 나무·불·흙·쇠·물로 나눠 센
              것이오. 0.3처럼 자투리가 붙는 건 아랫글자 속에 숨은
              글자까지 저울에 올렸기 때문이오 — 됫박으로 되면 셋인데
              저울에 달면 조금 더 나가는 것처럼 말이오.
            </Say>
            <span className="src">
              근거 · 입력한 출생 정보로 계산 · 시각 미상은 시주(태어난 시의 두 글자) 제외
            </span>
            <Pillars f={s.features} />
            <Summary f={s.features} />
            <ElementBar f={s.features} />
            <CalcPanel f={s.features} />
            <ActOut kind="밝힘" next="스무 사람">
              여덟 글자 중 <b>둘</b>은 태어난 시각에서 나오오
              — 그 둘을 <b>시주(時柱, 태어난 시각의 두 글자)</b>라 하오.<br />
              시각을 <b>네 시간</b> 칸으로만 알면 그 둘이 <b>절반</b>은
              어긋나오. 자를 한 눈금 잘못 대고 옷을 짓는 것과 같소 — 그러니까
              <b>없던 글자가 생기고 있던 글자가 사라진다는 말이오.</b><br />
              그래서 이 집은 그 시주(時柱)를 지어내지 않소. 모르면 <b>여섯 글자</b>로 보오.
            </ActOut>
          </>
        ) : (
          <>
            <Narration lines={["아직 글자를 세우지 않았소."]} />
            <button className="btn mt" onClick={() => router.push("/")}>내 사주부터 보겠습니다</button>
          </>
        )}
        <button className="btn gh mt" onClick={() => setTab("b1")}>진열대로</button>
      </Shell>
    );
  }

  /* b1 · 진열대 */
  return (
    <Shell screen="b1" title="진열대">
      <button className="btn gh" onClick={() => router.push("/fortune")}>대운·세운·월운·궁합 상세 상품 보기</button>
      <Scene id="shelf" />
      <p className="conversion-kicker">다시 마음에 남은 질문</p>
      <h1 className="reading-title">오늘은 어떤 이야기가<br />궁금하오?</h1>
      <p className="conversion-lead">다른 시선이 필요하다면 사람을 고르고, 이미 읽은 이야기는 내 첩에서 이어보시오.</p>
      <div className="og">
        <button className="op" onClick={() => setTab("b2")}>
          <span className="nm">스무 사람</span><span>불이 켜진 자리 {released.length} · 전체 {LENSES.length}</span>
        </button>
        <button className="op" onClick={() => setTab("b4")}>
          <span className="nm">내 명식</span>
          <span>{s.features ? "명식과 계산 근거" : "아직 세우지 않음"}</span>
        </button>
        {/* ★ 「일진」 이 풀이 없이 지나가고 있었소. 여덟 글자를 아직
              한 번도 못 본 손님이 여기서 처음 만나는 말입니다. */}
        <button className="op" onClick={() => router.push("/daily")}>
          <span className="nm">오늘의 일진</span><span>일진 (그날에 서는 두 글자) · 값 없이 매일</span>
        </button>
        <button className="op" onClick={() => router.push("/summary")}>
          <span className="nm">분석지</span><span>한 장으로 받아보고 내보내기</span>
        </button>
        <button className="op" onClick={() => router.push("/me")}>
          <span className="nm">인장첩</span><span>모은 인장 {s.seals.length}</span>
        </button>
      </div>
      <p className="conversion-note">{released.length}명의 질문을 살펴볼 수 있소. 짧은 분석부터 무료로 읽고, 마음에 남는 해석을 고르시오.</p>
    </Shell>
  );
}

export default function LobbyPage() {
  useScreen("b1");
  return (
    <Suspense fallback={<Shell title="진열대"><p className="sm">…</p></Shell>}>
      <LobbyInner />
    </Suspense>
  );
}
