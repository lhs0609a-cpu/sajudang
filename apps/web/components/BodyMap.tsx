"use client";

import { useState } from "react";
import type { PictureChoice } from "./ChoiceGrid";

const HEAD = "M93 42 C93 8 147 8 147 42 C147 75 136 90 120 90 C104 90 93 75 93 42Z";
const NECK = "M106 88 L134 88 L138 108 L102 108Z";
const SHOULDER = "M102 106 L138 106 L174 121 L180 147 L148 142 L142 126 L98 126 L92 142 L60 147 L66 121Z";
const ARM = "M60 147 L90 142 L78 226 L65 274 L44 266 L50 216Z M150 142 L180 147 L190 216 L196 266 L175 274 L162 226Z";
const HAND = "M44 268 L65 277 L59 308 Q51 324 38 308 L36 290Z M175 277 L196 268 L204 290 L202 308 Q189 324 181 308Z";
const HIP = "M89 235 L151 235 L160 278 L145 298 L120 284 L95 298 L80 278Z";
const LEG = "M80 280 L118 288 L115 346 L110 402 L84 402 L79 346Z M122 288 L160 280 L161 346 L156 402 L130 402 L125 346Z";
const FOOT = "M84 404 L110 404 L110 427 Q103 443 73 436 L73 426Z M130 404 L156 404 L167 426 L167 436 Q137 443 130 427Z";
const COMMON = { head: HEAD, neck: NECK, shoulder: SHOULDER, arm: ARM, hand: HAND, hip: HIP, leg: LEG, foot: FOOT };
const FRONT = { ...COMMON, chest: "M98 128 L142 128 L150 180 L90 180Z", abdomen: "M90 183 L150 183 L150 232 L90 232Z" };
const BACK = { ...COMMON, back: "M98 128 L142 128 L150 200 L90 200Z", waist: "M90 203 L150 203 L150 232 L90 232Z" };

export default function BodyMap({ regions, selected, onPick, disabled }: {
  regions: PictureChoice[]; selected: string[]; onPick: (id: string) => void; disabled?: boolean;
}) {
  const [view, setView] = useState<"front" | "back">("front");
  const paths = view === "front" ? FRONT : BACK;
  return <div className="body-picker">
    <div className="body-view" role="group" aria-label="몸 그림 방향">
      <button type="button" aria-pressed={view === "front"} onClick={() => setView("front")}>앞모습</button>
      <button type="button" aria-pressed={view === "back"} onClick={() => setView("back")}>뒷모습</button>
    </div>
    <div className="body-map-panel">
      <svg viewBox="0 0 240 460" className="body-map" role="group" aria-label={`${view === "front" ? "앞" : "뒤"}에서 본 몸. 불편한 부위를 고르시오.`}>
        <title>불편한 부위 선택</title>
        {Object.entries(paths).map(([id, d]) => {
          const picked = selected.includes(id);
          const blocked = disabled || (!picked && selected.length >= 3 && !selected.includes("whole"));
          const label = regions.find(x => x.id === id)?.label ?? id;
          return <path key={id} d={d} role="button" tabIndex={blocked ? -1 : 0}
            aria-label={label} aria-pressed={picked} aria-disabled={!!blocked}
            className={picked ? "selected" : ""}
            onClick={() => !blocked && onPick(id)}
            onKeyDown={e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); if (!blocked) onPick(id); } }}>
            <title>{label}</title>
          </path>;
        })}
        {view === "front" && <g className="body-face" fill="none" stroke="currentColor" aria-hidden="true">
          <path d="M104 49h6m20 0h6m-16 4v10m-7 10q7 4 14 0" />
        </g>}
      </svg>
      <p>그림이나 아래 이름을 눌러<br />세 곳까지 고를 수 있소.</p>
    </div>
    <div className="body-region-list" role="group" aria-label="신체 부위 목록">
      {regions.map(r => <button type="button" key={r.id} aria-pressed={selected.includes(r.id)}
        disabled={disabled || (!selected.includes(r.id) && r.id !== "whole" && selected.length >= 3)}
        onClick={() => onPick(r.id)}>{r.label}</button>)}
    </div>
    <p className="sm" aria-live="polite">{selected.length ? `고른 곳: ${regions.filter(r => selected.includes(r.id)).map(r => r.label).join(" · ")}` : "아직 고른 부위가 없소."}</p>
  </div>;
}
