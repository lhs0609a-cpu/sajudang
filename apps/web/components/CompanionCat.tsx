"use client";

/** 하묘: a small, soft companion with its own cat voice. */
export default function CompanionCat({ state = "rest", message }: {
  state?: "welcome" | "selected" | "rest" | "saved";
  message?: string;
}) {
  return (
    <div className={`companion-cat companion-cat--${state}`}>
      <svg viewBox="0 0 120 120" aria-hidden="true" focusable="false">
        <ellipse cx="59" cy="111" rx="35" ry="4" fill="#080e0a" opacity=".18" />
        <path d="M85 97q22 3 19-15" fill="none" stroke="#e8cfaa" strokeWidth="13" strokeLinecap="round" />
        <path d="M85 95q20 3 17-13" fill="none" stroke="#fff0d8" strokeWidth="9" strokeLinecap="round" />
        <ellipse cx="59" cy="87" rx="28" ry="24" fill="#fff2dc" stroke="#ddc6a6" strokeWidth="1.5" />
        <ellipse cx="59" cy="92" rx="18" ry="16" fill="#fffaf0" />
        <ellipse cx="42" cy="106" rx="13" ry="7" fill="#fff7e8" />
        <ellipse cx="76" cy="106" rx="13" ry="7" fill="#fff7e8" />
        <path d="M24 42Q19 15 28 17L44 30Q60 25 77 30L91 17Q101 14 96 43Q105 52 98 66Q90 80 60 81Q30 81 22 67Q14 52 24 42Z" fill="#fff7e8" stroke="#ddc6a6" strokeWidth="1.8" strokeLinejoin="round" />
        <path d="M27 25q-1 8 3 14l8-7Z M90 25q2 8-2 14l-8-7Z" fill="#f2bcb8" />
        <path d="M47 30q5 9 9 0m5-1q4 8 8 0" fill="none" stroke="#edd6b2" strokeWidth="3.5" strokeLinecap="round" />
        <g className="hamyo-eyes" fill="#59473f">
          <ellipse cx="43" cy="53" rx="3.2" ry="4.2" />
          <ellipse cx="77" cy="53" rx="3.2" ry="4.2" />
          <circle cx="42.2" cy="51.5" r=".9" fill="#fff" />
          <circle cx="76.2" cy="51.5" r=".9" fill="#fff" />
        </g>
        <ellipse cx="33" cy="62" rx="8" ry="4.5" fill="#f4b6b4" opacity=".7" />
        <ellipse cx="87" cy="62" rx="8" ry="4.5" fill="#f4b6b4" opacity=".7" />
        <path d="M57 58q3-2 6 0l-3 3Z" fill="#d49690" />
        <path d="M54 63q3 5 6-2 3 7 6 2" fill="none" stroke="#8a6258" strokeWidth="1.8" strokeLinecap="round" />
        <path d="m24 56 8 1m-8 7 7-1m65-7-8 1m8 7-7-1" stroke="#d6b89d" strokeWidth="1.5" strokeLinecap="round" />
        <path d="M49 80q11 4 22 0" fill="none" stroke="#a6bea5" strokeWidth="5" strokeLinecap="round" />
        <path d="M57 82q-10-9-12-1t12 4m5-3q10-9 12-1t-12 4" fill="#b9cfb3" />
        <circle cx="60" cy="84" r="4" fill="#e7bf75" />
        <path d="M60 84v2" stroke="#aa8251" strokeWidth="1.3" strokeLinecap="round" />
        <g className="hamyo-paw">
          <ellipse cx="34" cy="86" rx="9" ry="12" transform="rotate(-24 34 86)" fill="#fffaf0" stroke="#e4cdae" strokeWidth="1.2" />
          <ellipse cx="34" cy="87" rx="3.4" ry="3" fill="#f2beb9" />
          <circle cx="30" cy="82" r="1.6" fill="#f2beb9" /><circle cx="34" cy="80.5" r="1.6" fill="#f2beb9" /><circle cx="38" cy="82" r="1.6" fill="#f2beb9" />
        </g>
        {state === "welcome" || state === "saved" ? <path className="hamyo-heart" d="M101 31c-12-7-9-15-4-14q4 0 4 4 2-5 6-3c6 3 0 10-6 13Z" fill="#eca9a6" /> : null}
      </svg>
      {message && <div className="hamyo-speech"><span className="hamyo-name">안내묘 · 하묘</span><p>{message}</p></div>}
    </div>
  );
}
