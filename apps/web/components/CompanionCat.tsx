"use client";

/** One quiet companion. Only completed user actions receive a short reaction. */
export default function CompanionCat({ state = "rest", message }: {
  state?: "welcome" | "selected" | "rest" | "saved";
  message?: string;
}) {
  return (
    <div className={`companion-cat companion-cat--${state}`}>
      <svg viewBox="0 0 120 120" aria-hidden="true" focusable="false">
        <path d="M90 92q28 12 23-14" fill="none" stroke="#393044" strokeWidth="12" strokeLinecap="round" />
        <ellipse cx="60" cy="87" rx="32" ry="25" fill="#30283b" />
        <path d="M27 54 25 15 48 32Q61 27 75 32L96 16 93 57Z" fill="#393044" />
        <path d="m31 27 3 19 11-10M87 28l-3 18-10-10" fill="#be8f9e" />
        <ellipse cx="60" cy="56" rx="35" ry="29" fill="#393044" />
        <g className="cat-eyes">
          <ellipse cx="46" cy="55" rx="8" ry="10" fill="#e9bd83" />
          <ellipse cx="75" cy="55" rx="8" ry="10" fill="#e9bd83" />
          <ellipse cx="47" cy="55" rx="3" ry="8" fill="#100d18" />
          <ellipse cx="74" cy="55" rx="3" ry="8" fill="#100d18" />
          <circle cx="44" cy="51" r="2" fill="white" /><circle cx="72" cy="51" r="2" fill="white" />
        </g>
        <path d="m56 68 4 4 4-4" fill="#dfb2b3" />
        <path d="M51 74q5 6 9-2 4 8 9 2" fill="none" stroke="#dfb2b3" strokeWidth="1.5" />
        <path d="M60 33a7 7 0 0 0 7 8 7 7 0 0 1-7-8" fill="#e9bd83" />
        <ellipse cx="45" cy="104" rx="12" ry="6" fill="#46394e" />
        <ellipse cx="74" cy="104" rx="12" ry="6" fill="#46394e" />
      </svg>
      {message && <p>{message}</p>}
    </div>
  );
}
