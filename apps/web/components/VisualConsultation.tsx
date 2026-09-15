"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import ChoiceGrid, { ChoiceImage, type PictureChoice } from "./ChoiceGrid";
import BodyMap from "./BodyMap";

type Group = { id: string; label: string; options: PictureChoice[] };
type Catalog = {
  face: PictureChoice[]; face_features: Group[];
  body_regions: PictureChoice[]; body_states: PictureChoice[];
  body_duration: PictureChoice[]; body_impact: PictureChoice[];
  scene: { title: string; options: PictureChoice[] } | null;
  image: PictureChoice[]; cards: PictureChoice[];
};
const SPECIAL: Record<string, string> = { myeonsang: "face", yakcho: "body", monghwa: "image", paeseon: "cards" };
const TITLE: Record<string, string> = { face: "그림으로 나를 비춰 보오", body: "어디가 불편하시오?", image: "눈에 걸리는 그림 하나", cards: "마음이 가는 패 셋" };
const WHY: Record<string, string> = {
  face: "닮은 얼굴형을 고른 뒤 눈·눈썹·코·입·턱을 더 고를 수 있소. 성신당이 만든 그림과 상징으로 즐기는 관상 놀이요.",
  body: "불편한 위치와 지금의 상태를 함께 정리하겠소. 몸 그림과 사주로 원인을 진단하는 자리는 아니오.",
  image: "지금 유난히 눈에 남는 장면을 하나 고르시오.",
  cards: "고른 순서대로 첫째·둘째·셋째 자리에 놓이오. 재미로 보는 패요.",
};

function Chips({ options, selected, onPick, label, disabled }: { options: PictureChoice[]; selected: string; onPick: (id: string) => void; label: string; disabled?: boolean }) {
  return <div className="visual-chips" role="group" aria-label={label}>{options.map(x =>
    <button type="button" key={x.id} disabled={disabled} aria-pressed={selected === x.id} onClick={() => onPick(x.id)}>{x.label}</button>)}</div>;
}

export default function VisualConsultation({ lensId, busy, onSubmit, saved, locked = false }: {
  lensId: string; busy?: boolean; onSubmit: (extras: Record<string, unknown>) => void;
  saved?: Record<string, unknown> | null;
  locked?: boolean;
}) {
  const kind = SPECIAL[lensId] ?? "scene";
  const previous = (saved?.[kind] ?? {}) as {
    pick?: string; picks?: string[]; shape?: string; features?: Record<string, string>;
    regions?: string[]; state?: string; duration?: string; impact?: string;
  };
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [error, setError] = useState(false);
  const [retry, setRetry] = useState(0);
  const [editing, setEditing] = useState(!saved?.[kind]);
  const [pick, setPick] = useState(previous.pick ?? previous.state ?? "");
  const [picks, setPicks] = useState<string[]>(previous.picks ?? []);
  const [shape, setShape] = useState(previous.shape ?? "");
  const [features, setFeatures] = useState<Record<string, string>>(previous.features ?? {});
  const [tab, setTab] = useState("eyes");
  const [regions, setRegions] = useState<string[]>(previous.regions ?? []);
  const [duration, setDuration] = useState(previous.duration ?? "unknown");
  const [impact, setImpact] = useState(previous.impact ?? "");

  useEffect(() => {
    let alive = true;
    setCatalog(null); setError(false);
    api.reportChoices(lensId).then(c => {
      if (!alive) return;
      const next = c as Catalog;
      const deck = [...next.cards];
      for (let i = deck.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [deck[i], deck[j]] = [deck[j], deck[i]];
      }
      setCatalog({ ...next, cards: deck });
    })
      .catch(() => { if (alive) setError(true); });
    return () => { alive = false; };
  }, [lensId, retry]);

  // If report validation rejected or cleared the answer, keep correction available.
  useEffect(() => { if (!saved?.[kind]) setEditing(true); }, [saved, kind]);

  if (error) return <section className="visual-consultation"><p role="alert">고를 그림을 불러오지 못했소.</p><button className="btn gh" onClick={() => setRetry(n => n + 1)}>다시 불러오겠습니다</button></section>;
  if (!catalog) return <p className="sm" role="status">고를 그림을 펴는 중이오…</p>;
  if (kind === "scene" && !catalog.scene) return null;

  const options = kind === "image" ? catalog.image : kind === "cards" ? catalog.cards : catalog.scene?.options ?? [];
  const selectedFeatures = catalog.face_features.flatMap(g => g.options.filter(o => features[g.id] === o.id));
  const faceChoice = catalog.face.find(x => x.id === shape);
  const chosen = kind === "face" ? [...(faceChoice ? [faceChoice] : []), ...selectedFeatures]
    : kind === "body" ? catalog.body_states.filter(x => x.id === pick)
    : kind === "cards" ? picks.map(id => options.find(o => o.id === id)!).filter(Boolean)
    : options.filter(x => x.id === pick);
  const ready = kind === "face" ? !!faceChoice || selectedFeatures.length > 0
    : kind === "body" ? regions.length > 0 && !!pick && !!impact
    : kind === "cards" ? picks.length === 3 : !!pick;
  const toggleRegion = (id: string) => setRegions(prev => {
    if (prev.includes(id)) return prev.filter(x => x !== id);
    if (id === "whole") return [id];
    const current = prev.filter(x => x !== "whole");
    return current.length >= 3 ? current : [...current, id];
  });
  const submit = () => {
    if (!ready || busy) return;
    const value = kind === "face" ? { shape: shape || "unknown", features }
      : kind === "body" ? { regions, state: pick, duration, impact }
      : kind === "cards" ? { picks }
      : kind === "scene" ? { lens_id: lensId, pick } : { pick };
    setEditing(false); onSubmit({ [kind]: value });
  };

  return <section className="visual-consultation noprint" aria-label="캐릭터별 그림 상담" data-visual-kind={kind}>
    <div className="visual-heading"><span className="lab">그림으로 건네는 이야기</span>
      <h3>{TITLE[kind] ?? catalog.scene?.title}</h3>
      <p>{WHY[kind] ?? "지금 겪고 있는 상황에 가까운 장면을 고르시오. 고른 이야기에서 풀이를 이어가겠소."}</p>
    </div>
    {!editing && saved?.[kind] ? <div className="visual-confirmation" aria-live="polite">
      <div className="visual-chosen">{chosen.map(x => <figure key={x.id}>{x.image && <ChoiceImage src={x.image} label={x.label} />}<figcaption>{x.label}</figcaption></figure>)}</div>
      {kind === "body" && <p>{catalog.body_regions.filter(r => regions.includes(r.id)).map(r => r.label).join(" · ")} · {catalog.body_duration.find(x => x.id === duration)?.label} · {catalog.body_impact.find(x => x.id === impact)?.label}</p>}
      <p>{busy ? "고른 이야기로 풀이를 이어가는 중이오…" : locked ? "고른 내용은 리포트에 반영했소. 이 풀이는 이용권으로 열리는 자리에 있소." : "고른 내용의 풀이는 아래 본문에서 볼 수 있소."}</p>
      {!locked && <button type="button" className="btn" disabled={busy} onClick={() => {
        const reading = document.getElementById(`reading-${kind}`);
        const fold = reading?.closest("details");
        if (fold) fold.open = true;
        reading?.scrollIntoView({ behavior: "auto", block: "start" });
        reading?.focus({ preventScroll: true });
      }}>고른 내용의 풀이를 읽겠습니다</button>}
      <button type="button" className="btn gh" disabled={busy} onClick={() => setEditing(true)}>다시 고르겠습니다</button>
    </div> : <>
      {kind === "face" ? <>
        <h4>1. 가까운 얼굴형</h4>
        <ChoiceGrid label="대표 얼굴형" choices={catalog.face} selected={[shape]} onPick={setShape} disabled={busy} />
        <button type="button" className="visual-skip" aria-pressed={shape === "unknown"} onClick={() => setShape("unknown")}>닮은 얼굴형이 없습니다</button>
        <details className="face-details" open={shape === "unknown" ? true : undefined}>
          <summary>2. 눈·눈썹·코·입·턱 더 고르기 <span>선택 사항 · 30종</span></summary>
          <Chips label="살펴볼 얼굴 부위" options={catalog.face_features} selected={tab} onPick={setTab} />
          {catalog.face_features.filter(g => g.id === tab).map(g => <div key={g.id}>
            <h4>{g.label}에서 가까운 특징</h4>
            <ChoiceGrid label={`${g.label} 특징`} choices={g.options} selected={[features[g.id] ?? ""]} onPick={id => setFeatures(prev => ({ ...prev, [g.id]: id }))} disabled={busy} />
            <button type="button" className="visual-skip" onClick={() => setFeatures(prev => ({ ...prev, [g.id]: "unknown" }))}>이 부위는 잘 모르겠습니다</button>
          </div>)}
        </details>
        {selectedFeatures.length > 0 && <p className="sm" aria-live="polite">고른 특징: {selectedFeatures.map(x => x.label).join(" · ")}</p>}
        <p className="sm">얼굴형은 도감의 비교 예시요. 실제 성격·건강·미래를 얼굴로 판정하지 않소.</p>
      </> : kind === "body" ? <>
        <h4>1. 불편한 곳</h4>
        <BodyMap regions={catalog.body_regions} selected={regions} onPick={toggleRegion} disabled={busy} />
        <h4>2. 지금의 상태</h4>
        <ChoiceGrid label="지금의 몸 상태" choices={catalog.body_states} selected={[pick]} onPick={setPick} disabled={busy} />
        <h4>3. 언제부터 그러셨소?</h4>
        <Chips label="불편이 시작한 때" options={catalog.body_duration} selected={duration} onPick={setDuration} disabled={busy} />
        <h4>4. 일상에는 어떠하오?</h4>
        <Chips label="일상에 미치는 영향" options={catalog.body_impact} selected={impact} onPick={setImpact} disabled={busy} />
        {(impact === "severe" || regions.includes("chest")) && <p className="body-care-note" role="status">갑작스럽고 지속되는 가슴 통증이나 숨쉬기 어려움은 풀이를 기다리지 말고 의료 도움을 받으시오. 위급하면 <a href="tel:119">119</a>에 연락하시오.</p>}
        <p className="sm">고른 부위와 상태는 이 상담에서만 사용하오. 불편이 계속되면 의료진과 상의하시오.</p>
      </> : <>
        <ChoiceGrid label={kind === "cards" ? "패 석 장 선택" : "상황 그림 선택"} choices={options}
          selected={kind === "cards" ? picks : [pick]} disabled={busy}
          ordered={kind === "cards"} concealed={kind === "cards"} limit={kind === "cards" ? 3 : undefined}
          onPick={id => kind === "cards" ? setPicks(prev => prev.includes(id) ? prev.filter(x => x !== id) : prev.length < 3 ? [...prev, id] : prev) : setPick(id)} />
        {kind === "cards" && <div className="card-order" aria-live="polite"><p>{picks.length} / 3장 · 고른 패를 다시 누르면 뺄 수 있소.</p>
          {picks.map((id, i) => <span key={id}>{i + 1}. {options.find(x => x.id === id)?.label}</span>)}
        </div>}
      </>}
      <button type="button" className="btn visual-submit" disabled={!ready || busy} onClick={submit}>
        {busy ? "풀이를 이어가는 중이오…" : kind === "face" ? "이 특징으로 풀이를 보겠습니다" : kind === "body" ? "이 상태로 이야기하겠습니다" : "이 그림으로 풀이를 보겠습니다"}
      </button>
      <p className="sm">고르지 않고 아래 풀이를 읽으셔도 되오.</p>
    </>}
  </section>;
}
