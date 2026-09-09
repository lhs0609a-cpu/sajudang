"use client";

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
        <header className="editorial-heading"><p className="conversion-kicker">스무 사람, 스무 가지 시선</p><h1>같은 이야기에도<br/>다른 빛이 들 수 있소.</h1><p>지금의 고민을 먼저 보는 이를 만나보시오.<br/>인물마다 해석하는 관점과 가격이 다르오.</p></header>
        <Say who="풍운도령" lens="pungun">첫 이야기는 나와 읽었으니, 이제 다른 시선도 만나보시오. 소개에서 다루는 고민과 열람 범위를 확인할 수 있소.</Say>
        <p className="sm">
          이름을 누르면 아래에 그 사람 자리가 열리오.
        </p>
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
                      {l.released ? l.specialty : "아직 자리에 없소"}
                    </span>
                    {l.released && <span className="arch">{l.epithet}</span>}
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
            <div className="facebox"><CharArt lens={pickedLens} size="full" /></div>
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
            <p className="conversion-note">캐릭터 말투 예시 · 내 명식의 해석은 다음 화면에서 확인하오.</p>
            <Say who={pickedLens.name} lens={pickedLens.id}>{pickedLens.quote}</Say>
            <button className="btn mt" onClick={() => {
              s.markRead(pickedLens.id);
              router.push(`/report/${pickedLens.id}`);
            }}>
              이 사람에게 듣겠소
            </button>
            <p className="sm">
              무료 구간까지는 값을 묻지 않소.
              {" "}{pickedLens.price.toLocaleString()}원부터.
            </p>
            <button className="btn gh" onClick={() => setTab("b3")}>
              이 사람 자리를 크게 보겠소
            </button>
            <button className="btn gh" onClick={() => {
              setPicked(null);
              topRef.current?.scrollIntoView({
                behavior: reducedMotion() ? "auto" : "smooth", block: "start",
              });
            }}>
              스무 사람 목록으로 돌아가겠소
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
          스물을 다 들을 수는 없소. <b>한 자리에서 이을 수 있는 건 둘이오.</b><br />
          명식은 하나인데 읽는 눈이 스물이라, 누구를 고르느냐가
          곧 <b>무엇을 볼 것인가</b>요.
        </ActOut>
        <button className="btn gh mt" onClick={() => setTab("b1")}>진열대로</button>
      </Shell>
    );
  }

  if (tab === "b3") {
    return (
      <Shell screen="b3" title={lens.name}>
        <Scene id="seat" />
        {/* ★ 여는 줄이 없었습니다. 초상이 대뜸 뜨고 이름이 붙습니다. */}
        <Narration lines={["자리에 사람이 앉아 있소.", "이쪽을 보고 있지는 않소."]} />
        {/* 그 사람의 자리 — 초상이 서는 곳 */}
        <div className="facebox"><CharArt lens={lens} size="full" /></div>
        <div className="mec">
          <div>
            <div className="gz" style={{ color: lens.color }}>{lens.name} · {lens.hanja}</div>
            <div className="nm">
              <b className="spec">{lens.specialty}</b> · {lens.epithet}
            </div>
            <div className="tr">{lens.group}</div>
          </div>
        </div>
        {lens.released && (
          <div className="topicrow">
            <span className="k">이런 걸 들고 오시오</span>
            <span className="topics">
              {lens.topics.split(" · ").map((t) => <i key={t}>{t}</i>)}
            </span>
          </div>
        )}
        <p className="conversion-note">캐릭터 말투 예시 · 아래 대사는 내 명식을 계산한 결과가 아니에요.</p>
        <Say who={lens.name} lens={lens.id}>{lens.quote}</Say>
        {/*
          ★ 80점이던 자리. 초상과 이름표와 한마디 인용이 전부라
            **이 사람 앞에 선 손님 얘기**가 없었습니다. 울림 45 ·
            팩폭 60. 파는 말을 더하는 대신, 이 사람이 **안 보는
            자리**를 적소 — 고르는 데 쓸 수 있는 말이오.
        */}
        <Say who="도령" lens="pungun">
          이 사람이 먼저 보는 자리는 「{lens.specialty}」 하나요.
          나머지 19명은 같은 명식를 놓고 다른 데를 짚소.
          <br />
          지금의 고민과 이 관점이 맞는지 무료 본문부터 확인하시오.
          다른 해석자를 골라도 출생 정보가 바뀌지는 않소. 결제 전 상품 범위와 가격을 따로 안내하오.
        </Say>
        {lens.released ? (
          <>
            <button className="btn mt" onClick={() => {
              s.markRead(lens.id);
              router.push(`/report/${lens.id}`);
            }}>
              이 사람에게 듣겠소
            </button>
            <p className="sm mt">
              무료 구간까지는 값을 묻지 않소. {lens.price.toLocaleString()}원부터.
            </p>
          </>
        ) : (
          <p className="sm mt">아직 자리에 없는 사람이오.</p>
        )}
        {/*
          ★ 이 자리가 무엇을 근거로 한 말인지 없었소.
            「먼저 보는 자리」 는 취향이 아니라 이 집이 스무 사람에게
            **하나씩 나눠 준 자리**입니다. 그걸 밝혀야 스물이 왜
            스물인지가 섭니다.
        */}
        <span className="src">
          근거 · 먼저 보는 자리 「{lens.specialty}」 — 스무 사람이 하나씩
          나눠 가진 것이오
        </span>
        <ActOut kind="남긴 물음" next="무료 구간">
          {lens.name}이 먼저 보는 자리는 <b>「{lens.specialty}」</b>요.
          같은 명식인데 다른 <b>열아홉</b>은 거기를 안 보오 —
          명식에 <b>돋보기를 한 자리에만</b> 대는 셈이오.<br />
          그럼 {lens.name}은 그대 글자에서 <b>무엇을 먼저 짚겠소?</b>
          여기까지는 값이 안 드오.
        </ActOut>
        <button className="btn gh" onClick={() => setTab("b2")}>스무 사람으로</button>
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
            <Narration lines={["도령이 셈한 종이를 그대로 내밀었소.",
                               "먹이 아직 번져 있소."]} />
            <p className="sm">
              감춘 것 없이 그대로요. 이 표 하나로 뒤의 모든 말이 나오오 —
              집을 짓기 전에 재어 둔 <b>땅의 치수</b> 같은 것이오.
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
              {s.hourKnown ? '태어난 해·달·날·시의 네 기둥을 계산했소.' : '태어난 시간을 몰라 시주 없이 세 기둥을 계산했소.'}
              입력한 생년월일과 지역이 맞는지 먼저 확인하시오.
              <br />
              막대 다섯은 명식의 글자를 나무·불·흙·쇠·물로 나눠 센
              것이오. 0.3처럼 자투리가 붙는 건 아랫글자 속에 숨은
              글자까지 저울에 올렸기 때문이오 — 됫박으로 되면 셋인데
              저울에 달면 조금 더 나가는 것처럼 말이오.
            </Say>
            <span className="src">
              근거 · 입력한 출생 정보로 계산 · 시각 미상은 시주 제외
            </span>
            <Pillars f={s.features} />
            <Summary f={s.features} />
            <ElementBar f={s.features} />
            <CalcPanel f={s.features} />
            <ActOut kind="밝힘" next="스무 사람">
              여덟 글자 중 <b>둘</b>은 태어난 시각에서 나오오
              — 그 둘을 <b>시주(時柱, 태어난 시각의 두 글자)</b>라 하오.<br />
              시각을 <b>네 시간</b> 칸으로만 알면 그 둘이 <b>절반</b>은
              어긋나오. 자를 한 눈금 잘못 대고 옷을 짓는 것과 같소 —
              <b>없던 기운이 생기고 있던 기운이 사라지오.</b><br />
              그래서 이 집은 시주를 지어내지 않소. 모르면 <b>여섯 글자</b>로 보오.
            </ActOut>
          </>
        ) : (
          <>
            <Narration lines={["아직 글자를 세우지 않았소."]} />
            <button className="btn mt" onClick={() => router.push("/")}>내 사주부터 보겠소</button>
          </>
        )}
        <button className="btn gh mt" onClick={() => setTab("b1")}>진열대로</button>
      </Shell>
    );
  }

  /* b1 · 진열대 */
  return (
    <Shell screen="b1" title="진열대">
      <Scene id="shelf" />
      <Narration lines={["목패가 늘어서 있소.", "이름과 값이 적혀 있소."]} />
      {/*
        ★ 여기가 58점이었습니다.

          목패 다섯 개와 버튼이 전부였습니다. 진열대는 손님이 가장
          자주 되돌아오는 자리인데 **되돌아온 사람 얘기가 없어서**,
          메뉴판 한 장이 됐소. 울림 45 · 명확 45.

          여기서 파는 말을 얹으면 안 됩니다. 그래서 적는 건 이
          화면이 이미 세고 있는 수뿐입니다 — 목패 5장, 들은 자리,
          모은 인장.
      */}
      <Say who="도령" lens="pungun">
        그대의 명식은 셈해 두었소. 오늘 다시 온다고 바뀌지 않소.
        <br />
        여기 목패는 5장이오. 명식은 그대로 두고 보는 자리만 갈리오.
        오른쪽으로 갈수록 값이 붙는 게 아니라,
         보는 자리가 달라질 뿐이오. 값이 안 드는 목패가 그중
        둘이오 — 오늘의 일진과 인장첩이요.
        <br />
        어디부터 볼지 정하지 못했다면 무료인 오늘의 일진부터 살펴보시오.
        구매한 해석을 다시 찾는다면 내 첩의 구매 내역으로 가시오.
      </Say>
      <span className="src">
        근거 · 목패 5장 · 불이 켜진 사람과 들은 자리는 이 기기에
        남은 기록으로 센 것이오 · 값이 안 드는 목패 2장
      </span>
      <div className="og">
        <button className="op" onClick={() => setTab("b2")}>
          <b>스무 사람</b><span>불이 켜진 자리 {released.length} · 전체 {LENSES.length}</span>
        </button>
        <button className="op" onClick={() => setTab("b4")}>
          <b>내 명식</b>
          <span>{s.features ? "명식과 계산 근거" : "아직 세우지 않았소"}</span>
        </button>
        {/* ★ 「일진」 이 풀이 없이 지나가고 있었소. 여덟 글자를 아직
              한 번도 못 본 손님이 여기서 처음 만나는 말입니다. */}
        <button className="op" onClick={() => router.push("/daily")}>
          <b>오늘의 일진</b><span>일진 (그날에 서는 두 글자) · 값 없이 매일</span>
        </button>
        <button className="op" onClick={() => router.push("/summary")}>
          <b>분석지</b><span>한 장으로 받아보고 내보내기</span>
        </button>
        <button className="op" onClick={() => router.push("/me")}>
          <b>인장첩</b><span>모은 인장 {s.seals.length}</span>
        </button>
      </div>
      <ActOut kind="끊긴 동작" next="스무 사람">
        목패는 {LENSES.length}개요. 그대가 들은 자리는{" "}
        <b>{s.read.length}곳</b>이오.<br />
        {/* ★ 스물이 왜 스물인지가 없었소. 「관점이 여럿」 은 뜬 말이라,
              같은 집을 어디서 보느냐로 바꿔 말합니다. */}
        한 사람이 명식을 다 보지는 않소. 저마다 <b>제 눈에 드는
        자리만</b> 짚소 — 같은 집을 대문에서 본 그림과 뒷마당에서 본
        그림 같은 것이오.<br />
        겹치는 데와 갈리는 데, 그게 이 집이 파는 것이오.
      </ActOut>
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
