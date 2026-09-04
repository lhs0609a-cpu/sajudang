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
        {/*
          ★ 여기가 스물일곱 중 둘째로 낮았습니다 (연출 51).

            얼굴 20장과 이름표만 있었습니다. 고르는 자리인데 **고르는
            사람 얘기가 한 줄도 없어서**, 손님은 남의 명단을 보는
            사람이 됩니다. 울림 20 · 팩폭 43 이 거기서 나왔습니다.

            얼굴을 늘리는 대신 앞에 한 마디를 답니다 — 여기 서 있는
            사람이 이미 한 일(여덟 글자를 세운 것)을 짚고, 고르기가
            왜 어려운지를 먼저 말합니다.
        */}
        <Say who="도령" lens="pungun">
          그대의 여덟 글자는 이미 상에 올라와 있소. 바뀌지 않소.
          <br />
          바뀌는 건 <b>누가 그걸 읽느냐</b>요.
          {" "}같은 글자를 두고 스무 사람이 다 다른 데를 짚소 —
          돈을 먼저 보는 이가 있고, 끊긴 연락을 먼저 보는 이가 있소.
          <br />
          <b>여기서 오래 망설이셨을 게요.</b>
          {" "}골라 본 적이 없어서가 아니라, 여태 고르고 나서
          후회한 적이 있어서요. 목록을 위아래로 훑다가 아무도 안
          누르고 나간 사람이 적지 않소.
          <br />
          불이 켜진 자리는 20자리인데 <b>오늘 앉을 수 있는 건 2명</b>이오.
          값은 사람마다 다르고 4,900원부터 시작하오.
          <br />
          스물을 한 상에 올려 놓고 견주는 건 촛불 20개를 한꺼번에
          들여다보는 것과 같소. 밝기만 보이고, 어느 불이 내 쪽을
          비추는지는 안 보이오.
          <br /> 저울에 스무 개를 같이 올리면 눈금이
          안 서는 것처럼 말이오.
          {" "}지금 걸린 것 하나를 들고, 그 하나를 잘 보는 사람 앞에
          서시오. 나머지 열여덟은 오늘 안 꺼지오.
        </Say>
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
        {/* ★ 여는 줄이 없었습니다. 초상이 대뜸 뜨고 이름이 붙습니다. */}
        <Narration lines={["자리에 사람이 앉아 있다.", "이쪽을 보고 있지는 않다."]} />
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
        {/*
          ★ 80점이던 자리. 초상과 이름표와 한마디 인용이 전부라
            **이 사람 앞에 선 손님 얘기**가 없었습니다. 울림 45 ·
            팩폭 60. 파는 말을 더하는 대신, 이 사람이 **안 보는
            자리**를 적습니다 — 고르는 데 쓸 수 있는 말입니다.
        */}
        <Say who="도령" lens="pungun">
          이 사람이 먼저 보는 자리는 「{lens.specialty}」 하나요.
          나머지 19명은 같은 8글자를 놓고 다른 데를 짚소.
          <br />
          <b>여태 사주를 보러 가서 「무엇을 물을지」부터 막힌 적이
          있었소.</b> 물어볼 게 없어서가 아니라 여러 개가 엉켜 있어
          하나로 못 줄여 참고 만 것이오.
          <br />
          여기서는 줄일 필요가 없소. <b>이 사람이 대신 좁혀 주오</b> —
          돋보기를 한 자리에만 대는 것처럼, 걸린 것이 그 자리면
          앉고 아니면 지나치시오. 20명 중 1명이오. 값은 앉은 뒤에
          묻고, 무료 구간까지는 0원이오.
        </Say>
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
        {/*
          ★ 이 자리가 무엇을 근거로 한 말인지 없었습니다.
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
          같은 여덟 글자인데 다른 <b>열아홉</b>은 거기를 안 보오 —
          여덟 글자에 <b>돋보기를 한 자리에만</b> 대는 셈이오.<br />
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
            <Narration lines={["도령이 셈한 종이를 그대로 내밀었다.",
                               "먹이 아직 번져 있다."]} />
            <p className="sm">
              감춘 것 없이 그대로요. 이 표 하나로 뒤의 모든 말이 나오오 —
              집을 짓기 전에 재어 둔 <b>땅의 치수</b> 같은 것이오.
            </p>
            {/*
              ★ 여기가 61점이었습니다 (900자 자리에 334자).

                표와 막대는 다 있는데 **표를 읽는 사람 얘기가**
                없었습니다. 숫자만 들이밀면 손님은 자기 것으로
                안 봅니다. 울림 45 · 팩폭 60.

                해석은 안 얹습니다 — 그건 값을 치르는 자리 몫이오.
                여기서는 이 표가 무엇을 센 것인지만 말합니다.
            */}
            <Say who="도령" lens="pungun">
              이건 그대의 것이오. 태어난 해·달·날·시 4자리를 각각
              두 글자로 옮기니 8글자가 되었소. 여기서 한 글자라도
              다르면 뒤의 말이 전부 달라지오.
              <br />
              <b>여태 사주라 하면 이 표를 안 보여 주는 집이
              많았소.</b> 결과만 듣고 나와서, 맞는지 대 볼 데가 없어
              혼자 삼킨 적이 있었소. 그래서 이 집은 표를 먼저 내오.
              <br />
              막대 다섯은 여덟 글자를 나무·불·흙·쇠·물로 나눠 센
              것이오. 0.3처럼 자투리가 붙는 건 아랫글자 속에 숨은
              글자까지 저울에 올렸기 때문이오 — 됫박으로 되면 셋인데
              저울에 달면 조금 더 나가는 것처럼 말이오.
            </Say>
            <span className="src">
              근거 · 태어난 해·달·날·시를 각각 두 글자로 옮긴 것 · 여덟 글자
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
      {/*
        ★ 여기가 58점이었습니다.

          목패 다섯 개와 버튼이 전부였습니다. 진열대는 손님이 가장
          자주 되돌아오는 자리인데 **되돌아온 사람 얘기가 없어서**,
          메뉴판 한 장이 됐습니다. 울림 45 · 명확 45.

          여기서 파는 말을 얹으면 안 됩니다. 그래서 적는 건 이
          화면이 이미 세고 있는 수뿐입니다 — 목패 5장, 들은 자리,
          모은 인장.
      */}
      <Say who="도령" lens="pungun">
        그대의 8글자는 셈해 두었소. 오늘 다시 온다고 바뀌지 않소.
        <br />
        여기 목패는 5장이오. 8글자는 그대로 두고 보는 자리만 갈리오.
        오른쪽으로 갈수록 값이 붙는 게 아니라,
         보는 자리가 달라질 뿐이오. 값이 안 드는 목패가 그중
        둘이오 — 오늘의 일진과 인장첩이요.
        <br />
        여태 여기까지 왔다가 아무것도 안 누르고 나간 날이 있었소.
        {" "}뭘 눌러야 할지 몰라서가 아니라, 눌렀다가 또 뻔한 말을
        들을까 봐 참은 것이오.
          <br /> 그럴 땐 값이 안 드는 쪽을 먼저
        누르시오. 상 위의 반찬을 한 젓가락 떠 보는 것처럼요.
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
          <span>{s.features ? "여덟 글자와 셈에 쓴 것" : "아직 세우지 않았습니다"}</span>
        </button>
        {/* ★ 「일진」 이 풀이 없이 지나가고 있었습니다. 여덟 글자를 아직
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
        {/* ★ 스물이 왜 스물인지가 없었습니다. 「관점이 여럿」 은 뜬 말이라,
              같은 집을 어디서 보느냐로 바꿔 말합니다. */}
        한 사람이 여덟 글자를 다 보지는 않소. 저마다 <b>제 눈에 드는
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
