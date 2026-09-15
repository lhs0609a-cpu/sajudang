"use client";

import { useState } from "react";

export type PictureChoice = { id: string; label: string; image?: string; detail?: string };

export function ChoiceImage({ src, label }: { src: string; label: string }) {
  const [failed, setFailed] = useState(false);
  return failed ? <span className="choice-image-missing">{label}</span> :
    // The adjacent button label describes the choice; repeating it as alt is noisy.
    <img src={src} alt="" width={320} height={320} loading="lazy"
         style={src.endsWith(".svg") ? { objectFit: "contain", background: "#eee4d3" } : undefined}
         decoding="async" onError={() => setFailed(true)} />;
}

export default function ChoiceGrid({ choices, selected, onPick, disabled, ordered = false,
  concealed = false, limit, label }: {
  choices: PictureChoice[]; selected: string[]; onPick: (id: string) => void;
  disabled?: boolean; ordered?: boolean; concealed?: boolean; limit?: number; label: string;
}) {
  return <div className={`choice-grid ${concealed ? "choice-deck" : ""}`} role="group" aria-label={label}>
    {choices.map((o, index) => {
      const order = selected.indexOf(o.id);
      const picked = order >= 0;
      const blocked = disabled || (!picked && limit !== undefined && selected.length >= limit);
      const faceDown = concealed && !picked;
      return <button type="button" key={o.id} className={`choice-tile ${picked ? "is-picked" : ""}`}
        aria-pressed={picked} disabled={blocked} onClick={() => onPick(o.id)}>
        {o.image && <span className="choice-picture">
          <ChoiceImage key={faceDown ? "back" : o.image} src={faceDown ? "/choices/card-back.webp" : o.image} label={o.label} />
          {picked && <span className="choice-mark" aria-hidden="true">{ordered ? order + 1 : "✓"}</span>}
        </span>}
        <span className="choice-label">{faceDown ? `${index + 1}번째 패` : o.label}</span>
        {!faceDown && o.detail && <span className="choice-detail">{o.detail}</span>}
      </button>;
    })}
  </div>;
}
