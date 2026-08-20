"use client";

/**
 * @screen c1 c2 c3 c4 c5 c6
 * C · 읽다 — c1 표지 · c2 웹툰 · c3 대운맵 · c4 페이월 · c5 공유카드 · c6 피드백
 *
 * ★ 잠긴 컷은 본문이 아예 내려오지 않습니다. 블러로 가린 게 아니라
 *   서버가 안 줍니다. (docs/02 §7)
 */
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Shell from "@/components/Shell";
import Scene from "@/components/scene/Scene";
import { Narration, Say } from "@/components/Narration";
import { api, ApiError } from "@/lib/api";
import { LENS_BY_ID } from "@/lib/lenses";
import { useSession } from "@/lib/store";
import type { ReportResponse } from "@shared/chart";

type Tab = "c1" | "c2" | "c3" | "c4" | "c5" | "c6";

export default function ReportPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const s = useSession();
  const lensId = params.id;
  const lens = LENS_BY_ID[lensId];

  const [tab, setTab] = useState<Tab>("c1");
  const [rep, setRep] = useState<ReportResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [rating, setRating] = useState(0);

  useEffect(() => {
    if (!s.chartId) return;
    let alive = true;
    api.report({
      chart_id: s.chartId, lens_id: lensId, tier: s.tier,
      concern: s.concern, axis4: s.axis4,
    })
      .then((r) => alive && setRep(r))
      .catch((e) => alive && setErr(e instanceof ApiError ? e.message : "리포트를 펴지 못했소."));
    return () => { alive = false; };
  }, [s.chartId, lensId, s.tier, s.concern, s.axis4]);

  if (!s.chartId) {
    return (
      <Shell title="읽다">
        <Narration lines={["먼저 글자를 세워야 하오."]} />
        <button className="btn mt" onClick={() => router.push("/")}>글자를 세운다</button>
      </Shell>
    );
  }
  if (err) {
    return <Shell title="읽다"><Say who="도령">{err}</Say></Shell>;
  }
  if (!rep) {
    return <Shell title="읽다"><Narration lines={["두루마리를 편다."]} /></Shell>;
  }

  const daeunCut = rep.cuts.find((c) => c.id === "daeun_map");

  /* c1 · 표지 */
  if (tab === "c1") {
    return (
      <Shell title={`${rep.lens.name} · 표지`}>
        <Scene id="scroll" className="hero" />
        <div style={{ textAlign: "center" }}>
          <p style={{ fontFamily: "var(--serif)", fontSize: 24, color: lens?.color ?? "var(--c)" }}>
            {rep.lens.name}
          </p>
          <p className="sm">{rep.lens.hanja} · {rep.lens.group}</p>
          <p className="sm mt">
            {s.name ? `${s.name}의 ` : ""}여덟 글자를 {rep.lens.name}의 눈으로 본 것
          </p>
          <p className="sm">읽는 자리 {rep.cuts.length}컷 · 잠긴 자리 {rep.locked.length}컷</p>
        </div>
        <button className="btn mt" onClick={() => setTab("c2")}>편다</button>
      </Shell>
    );
  }

  /* c3 · 대운 맵 */
  if (tab === "c3") {
    return (
      <Shell title="대운 맵">
        <Scene id="roadmap" />
        {daeunCut ? (
          <>
            <span className="src">근거 · {daeunCut.source}</span>
            <div dangerouslySetInnerHTML={{ __html: daeunCut.html }} />
          </>
        ) : (
          <>
            <Narration lines={["대운 맵은 아직 잠겨 있소."]} />
            <button className="btn mt" onClick={() => setTab("c4")}>어디까지 볼지 고른다</button>
          </>
        )}
        <button className="btn gh mt" onClick={() => setTab("c2")}>본문으로</button>
      </Shell>
    );
  }

  /* c4 · 페이월 */
  if (tab === "c4") {
    return (
      <Shell title="여기서부터" legal>
        <Scene id="fold" />
        <Narration lines={["두루마리가 반쯤 접혀 있다."]} />
        <Say who={rep.lens.name}>
          여기까지가 값 없이 하는 얘기요. 나머지에는 <b>왜</b>와 <b>언제</b>가 들어 있소.
        </Say>
        {rep.locked.map((l) => (
          <div className="dz" key={l.id}>
            <div className="k">{l.title}</div>
            <p className="sm">근거 · {l.source}</p>
            <p className="bl">가가가가 가가가가가 가가가</p>
            <p className="sm">
              {l.need_tier === "one" ? "이 자리 하나" : "여덟 글자 전부"}부터 열리오
            </p>
          </div>
        ))}
        <button className="btn mt" onClick={() => router.push("/pay?step=d1")}>
          어디까지 볼지 고른다
        </button>
        <button className="btn gh" onClick={() => setTab("c2")}>본문으로</button>
      </Shell>
    );
  }

  /* c5 · 공유 카드 */
  if (tab === "c5") {
    const nameCut = rep.cuts.find((c) => c.id === "lack");
    return (
      <Shell title="공유 카드">
        <div className="card">
          <Scene id="cardbg" />
          <div className="cardin">
            <p className="sm">사주당 四柱堂</p>
            <p style={{ fontFamily: "var(--serif)", fontSize: 20, color: "var(--c)" }}>
              {s.features?.day_gan} 일간 · {s.features?.strength}
            </p>
            {nameCut && (
              <p className="sm">가장 약한 것 {s.features?.weak_el} · 흐름 {s.features?.flow}</p>
            )}
            <p className="sm">— {rep.lens.name}</p>
          </div>
        </div>
        <p className="sm mt">
          중앙 문양은 에셋이 들어오면 교체됩니다. (docs/10 §5 — 정지 PNG 필수)
        </p>
        <button className="btn gh mt" onClick={() => setTab("c6")}>다 읽었소</button>
      </Shell>
    );
  }

  /* c6 · 피드백 */
  if (tab === "c6") {
    return (
      <Shell title="남기다" legal>
        <Scene id="wall" />
        <Say who={rep.lens.name}>어떻게 보셨소?</Say>
        <div className="og c2" style={{ gridTemplateColumns: "repeat(5,1fr)" }}>
          {[1, 2, 3, 4, 5].map((n) => (
            <button key={n} className={`op ${rating === n ? "on" : ""}`}
                    style={{ textAlign: "center" }} onClick={() => setRating(n)}>
              {"★".repeat(n)}
            </button>
          ))}
        </div>
        <textarea className="fld" rows={4} placeholder="남기고 싶은 말" />
        <p className="sm">
          결제하고 끝까지 읽은 분의 후기에만 &quot;결제 확인됨&quot; 표시가 붙습니다.
          대가를 주고받은 글은 싣지 않습니다.
        </p>
        <button className="btn mt" onClick={() => {
          if (!s.seals.includes(lensId)) s.set({ seals: [...s.seals, lensId] });
          router.push("/relay");
        }}>
          인장을 받고 나간다
        </button>
      </Shell>
    );
  }

  /* c2 · 본문 (웹툰 뷰어) */
  return (
    <Shell title={rep.lens.name}>
      <Scene id="oldpaper" />
      {rep.cuts.filter((c) => c.id !== "daeun_map").map((c) => (
        <div className="blk in" key={c.id}>
          <div className="lab">{c.title}</div>
          <span className="src">근거 · {c.source}</span>
          <div dangerouslySetInnerHTML={{ __html: c.html }} />
        </div>
      ))}

      {rep.locked.length > 0 && (
        <button className="btn mt" onClick={() => setTab("c4")}>
          잠긴 {rep.locked.length}컷 보기
        </button>
      )}
      {daeunCut && (
        <button className="btn gh" onClick={() => setTab("c3")}>대운 맵</button>
      )}
      <button className="btn gh" onClick={() => setTab("c5")}>공유 카드</button>
      <button className="btn gh" onClick={() => setTab("c6")}>다 읽었소</button>
    </Shell>
  );
}
