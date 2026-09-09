"use client";

/** One quiet companion. Only completed user actions receive a short reaction. */
export default function CompanionCat({ state = "rest", message }: {
  state?: "welcome" | "selected" | "rest" | "saved";
  message?: string;
}) {
  return (
    <div className={`companion-cat companion-cat--${state}`}>
      <svg viewBox="0 0 120 120" aria-hidden="true" focusable="false">
        <ellipse cx="60" cy="109" rx="37" ry="6" fill="#09060f" opacity=".25" />
        <path d="M86 95q28 6 21-17" fill="none" stroke="#d2b89d" strokeWidth="11" strokeLinecap="round" />
        <ellipse cx="60" cy="88" rx="28" ry="23" fill="#ead6b9" />
        <ellipse cx="60" cy="91" rx="17" ry="17" fill="#fff0d8" />
        <path d="M24 47Q13 8 35 19L48 31M73 31 88 19Q109 11 98 49" fill="#ead6b9" stroke="#c5a88d" strokeWidth="2" strokeLinejoin="round" />
        <path d="m26 28 4 18 11-10M91 28l-4 18-11-10" fill="#e9aaa9" />
        <ellipse cx="60" cy="55" rx="41" ry="33" fill="#f3e2c9" />
        <path d="M52 25q8 9 16 0" fill="none" stroke="#c6a888" strokeWidth="4" strokeLinecap="round" />
        <g className="cat-eyes">
          <ellipse cx="44" cy="54" rx="10" ry="12" fill="#36273b" />
          <ellipse cx="76" cy="54" rx="10" ry="12" fill="#36273b" />
          <circle cx="41" cy="49" r="4" fill="#fffaf0" /><circle cx="73" cy="49" r="4" fill="#fffaf0" />
          <circle cx="48" cy="59" r="2" fill="#d6b484" /><circle cx="80" cy="59" r="2" fill="#d6b484" />
        </g>
        <ellipse cx="30" cy="68" rx="8" ry="4" fill="#e8a8ab" opacity=".7" />
        <ellipse cx="90" cy="68" rx="8" ry="4" fill="#e8a8ab" opacity=".7" />
        <path d="M56 65q4-4 8 0l-4 4Z" fill="#bc7c83" />
        <path d="M51 71q5 7 9-2 4 9 9 2" fill="none" stroke="#79556a" strokeWidth="2" strokeLinecap="round" />
        <path d="m20 61 10 2m-10 8 10-2m70-8-10 2m10 8-10-2" stroke="#a18481" strokeWidth="1.4" strokeLinecap="round" />
        <path d="M42 84q18 8 36 0" fill="none" stroke="#816285" strokeWidth="5" />
        <circle cx="60" cy="90" r="6" fill="#e7ba72" /><path d="M60 89v4" stroke="#967245" strokeWidth="1.5" />
        <ellipse cx="43" cy="105" rx="13" ry="8" fill="#f3e2c9" />
        <ellipse cx="77" cy="105" rx="13" ry="8" fill="#f3e2c9" />
      </svg>
      {message && <p>{message}</p>}
    </div>
  );
}
