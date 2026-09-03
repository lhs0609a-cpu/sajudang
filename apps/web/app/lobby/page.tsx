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
        <Narration lines={["스무 개의 자리가 있다.",
                           "스무 자리에 다 불이 켜져 있다.",
                           "오늘 앉을 수 있는 자리는 그중 둘이다."]} />
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
                      {l.released ? l.specialty : "아직 자리에 없습니다"}
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
            <Say who={pickedLens.name} lens={pickedLens.id}>{pickedLens.quote}</Say>
            <button className="btn mt" onClick={() => {
              s.markRead(pickedLens.id);
              router.push(`/report/${pickedLens.id}`);
            }}>
              이 사람에게 듣겠습니다
            </button>
            <p className="sm">
              무료 구간까지는 값을 묻지 않소.
              {" "}{pickedLens.price.toLocaleString()}원부터.
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
            그걸 **고를 이유**로 씁니다 — 지어낸 압박이 아닙니다.
        */}
        <ActOut kind="딜레마" next="그 사람의 자리">
          스물을 다 들을 수는 없소. <b>한 자리에서 이을 수 있는 건 둘이오.</b><br />
          여덟 글자는 하나인데 읽는 눈이 스물이라, 누구를 고르느냐가
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
        <Say who={lens.name} lens={lens.id}>{lens.quote}</Say>
        {lens.released ? (
          <>
            <button className="btn mt" onClick={() => {
              s.markRead(lens.id);
              router.push(`/report/${lens.id}`);
            }}>
              이 사람에게 듣겠습니다
            </button>
            <p className="sm mt">
              무료 구간까지는 값을 묻지 않소. {lens.price.toLocaleString()}원부터.
            </p>
          </>
        ) : (
          <p className="sm mt">아직 자리에 없는 사람이오.</p>
        )}
        <ActOut kind="남긴 물음" next="무료 구간">
          {lens.name}이 먼저 보는 자리는 <b>「{lens.specialty}」</b>요.
          같은 여덟 글자인데 다른 <b>열아홉</b>은 거기를 안 보오.<br />
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
              ★ 표부터 들이밀고 있었습니다. 표는 셈이지 말이 아닙니다.
                무슨 화면인지 한 줄 먼저 놓습니다 (콜드 오픈).
            */}
            <Narration lines={["도령이 셈한 종이를 그대로 내밀었다."]} />
            <p className="sm">
              감춘 것 없이 그대로요. <b>이 표 하나로 뒤의 모든 말이 나오오</b> —
              집을 짓기 전에 재어 둔 <b>땅의 치수</b> 같은 것이오.
            </p>
            <span className="src">
              근거 · 태어난 해·달·날·시를 각각 두 글자로 옮긴 것 · 여덟 글자
            </span>
            <Pillars f={s.features} />
            <Summary f={s.features} />
            <ElementBar f={s.features} />
            <CalcPanel f={s.features} />
            <ActOut kind="밝힘" next="스무 사람">
              여덟 글자 중 <b>둘</b>은 태어난 <b>시각</b>에서 나오오
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
      <Scene id="shelf" />
      <Narration lines={["목패가 늘어서 있다.", "이름과 값이 적혀 있다."]} />
      <div className="og">
        <button className="op" onClick={() => setTab("b2")}>
          <b>스무 사람</b><span>불이 켜진 자리 {released.length} · 전체 {LENSES.length}</span>
        </button>
        <button className="op" onClick={() => setTab("b4")}>
          <b>내 명식</b>
          <span>{s.features ? "여덟 글자와 셈에 쓴 것" : "아직 세우지 않았습니다"}</span>
        </button>
        <button className="op" onClick={() => router.push("/daily")}>
          <b>오늘의 일진</b><span>값 없이 매일</span>
        </button>
        <button className="op" onClick={() => router.push("/summary")}>
          <b>분석지</b><span>한 장으로 받아보고 내보내기</span>
        </button>
        <button className="op" onClick={() => router.push("/me")}>
          <b>인장첩</b><span>모은 인장 {s.seals.length}</span>
        </button>
      </div>
      <ActOut kind="끊긴 동작" next="스무 사람">
        목패는 <b>{LENSES.length}</b>이오. 그대가 들은 자리는{" "}
        <b>{s.read.length}</b>이오.<br />
        같은 여덟 글자를 두 사람이 읽으면 <b>겹치는 데가 어디고 갈리는
        데가 어딘지</b>가 보이오. 그게 이 집이 파는 것이오.
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
