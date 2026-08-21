"use client";

/**
 * @screen b1 b2 b3 b4
 * B · 둘러보다 — b1 진열대 · b2 스무 사람 · b3 그 사람 · b4 내 명식
 *
 * 미출시 캐릭터는 실루엣으로 둡니다. 결제 버튼을 붙이지 않습니다.
 */
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Shell from "@/components/Shell";
import Scene from "@/components/scene/Scene";
import { Narration, Say } from "@/components/Narration";
import { CalcPanel, ElementBar, Pillars, Summary } from "@/components/Chart";
import { LENSES, LENS_BY_ID } from "@/lib/lenses";
import { useSession } from "@/lib/store";

type Tab = "b1" | "b2" | "b3" | "b4";

const GROUPS = ["정통", "검사", "술수", "관계", "맥락", "정서"];

const TABS: Tab[] = ["b1", "b2", "b3", "b4"];

function LobbyInner() {
  const router = useRouter();
  const params = useSearchParams();
  const s = useSession();
  const asked = params.get("tab") as Tab | null;
  const [tab, setTab] = useState<Tab>(asked && TABS.includes(asked) ? asked : "b1");
  useEffect(() => { if (asked && TABS.includes(asked)) setTab(asked); }, [asked]);
  const lens = LENS_BY_ID[s.cur] ?? LENSES[0];

  const released = LENSES.filter((l) => l.released);

  if (tab === "b2") {
    return (
      <Shell title="스무 사람">
        <Scene id="hall" />
        <Narration lines={["스무 개의 자리가 있다.", "불이 켜진 자리는 몇 되지 않는다."]} />
        {GROUPS.map((g) => (
          <div key={g}>
            <div className="lab">{g}</div>
            <div className="og c2">
              {LENSES.filter((l) => l.group === g).map((l) => (
                <button key={l.id} className={`op ${l.released ? "" : "off"}`}
                        disabled={!l.released}
                        onClick={() => { s.set({ cur: l.id }); setTab("b3"); }}>
                  <b style={{ color: l.released ? l.color : "var(--paper3)" }}>
                    {l.released ? l.name : "● ● ●"}
                  </b>
                  <span>{l.released ? l.archetype : "아직 자리에 없소"}</span>
                </button>
              ))}
            </div>
          </div>
        ))}
        <button className="btn gh mt" onClick={() => setTab("b1")}>진열대로</button>
      </Shell>
    );
  }

  if (tab === "b3") {
    return (
      <Shell title={lens.name}>
        <Scene id="seat" />
        <div className="mec">
          <div>
            <div className="gz" style={{ color: lens.color }}>{lens.name} · {lens.hanja}</div>
            <div className="nm">{lens.archetype}</div>
            <div className="tr">{lens.group}</div>
          </div>
        </div>
        <Say who={lens.name}>{lens.quote}</Say>
        {lens.released ? (
          <>
            <button className="btn mt" onClick={() => {
              s.markRead(lens.id);
              router.push(`/report/${lens.id}`);
            }}>
              이 사람에게 듣는다
            </button>
            <p className="sm mt">
              무료 구간까지는 값을 묻지 않소. {lens.price.toLocaleString()}원부터.
            </p>
          </>
        ) : (
          <p className="sm mt">아직 자리에 없는 사람이오.</p>
        )}
        <button className="btn gh" onClick={() => setTab("b2")}>스무 사람으로</button>
      </Shell>
    );
  }

  if (tab === "b4") {
    return (
      <Shell title="내 명식">
        {s.features ? (
          <>
            <Pillars f={s.features} />
            <Summary f={s.features} />
            <ElementBar f={s.features} />
            <CalcPanel f={s.features} />
          </>
        ) : (
          <>
            <Narration lines={["아직 글자를 세우지 않았소."]} />
            <button className="btn mt" onClick={() => router.push("/")}>글자를 세운다</button>
          </>
        )}
        <button className="btn gh mt" onClick={() => setTab("b1")}>진열대로</button>
      </Shell>
    );
  }

  /* b1 · 진열대 */
  return (
    <Shell title="진열대">
      <Scene id="shelf" />
      <Narration lines={["목패가 늘어서 있다.", "이름과 값이 적혀 있다."]} />
      <div className="og">
        <button className="op" onClick={() => setTab("b2")}>
          <b>스무 사람</b><span>불이 켜진 자리 {released.length} · 전체 {LENSES.length}</span>
        </button>
        <button className="op" onClick={() => setTab("b4")}>
          <b>내 명식</b>
          <span>{s.features ? "여덟 글자와 셈에 쓴 것" : "아직 세우지 않았소"}</span>
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
    </Shell>
  );
}

export default function LobbyPage() {
  return (
    <Suspense fallback={<Shell title="진열대"><p className="sm">…</p></Shell>}>
      <LobbyInner />
    </Suspense>
  );
}
