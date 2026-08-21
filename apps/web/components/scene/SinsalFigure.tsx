"use client";

/**
 * 신살 인물 — 이름표가 아니라 곁에 선 사람으로 보이게.
 *
 * 폴백 순서 (Scene 과 같은 구조)
 *   1. public/sinsal/{key}/clip.webm|mp4  가 있으면 영상
 *   2. 없으면 SVG 실루엣 + 등장 연출
 *   3. prefers-reduced-motion 이면 정지 (poster 또는 정지 SVG)
 *
 * 모션은 참조 구현체의 캐릭터 관례를 그대로 씁니다.
 *   mBody 호흡 4.6s · mFx 입자 상승 · mProp 소품 흔들림 · blinkk 눈 깜빡임
 *   docs/09 §6 — 얼굴은 눈 깜빡임 정도만, 움직임은 화면의 20% 이내
 */
import { useEffect, useRef, useState } from "react";
import PromptModal from "./PromptModal";
import { figureOf, type Fx, type Prop, type SinsalFigure } from "@/lib/sinsalFigures";

function useReducedMotion() {
  const [r, setR] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const on = () => setR(mq.matches);
    on();
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return r;
}

/** 화면에 들어올 때 한 번 등장시킨다 (스크롤 진입) */
function useAppear<T extends HTMLElement>() {
  const ref = useRef<T | null>(null);
  const [seen, setSeen] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || seen) return;
    const io = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) { setSeen(true); io.disconnect(); } },
      { threshold: 0.35 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [seen]);
  return { ref, seen };
}

function useHasClip(key: string) {
  const [has, setHas] = useState(false);
  useEffect(() => {
    let alive = true;
    fetch(`/sinsal/${key}/poster.jpg`, { method: "HEAD" })
      .then((r) => alive && setHas(r.ok))
      .catch(() => {});
    return () => { alive = false; };
  }, [key]);
  return has;
}

/* ── 소품 ────────────────────────────────────────────────── */
function PropArt({ prop, col }: { prop: Prop; col: string }) {
  switch (prop) {
    case "sleeve":   // 소매를 펼쳐 앞을 가린다
      return (
        <path className="mProp" d="M40 96c14-10 30-14 35-6 5 8-12 20-35 22z"
              fill={col} opacity=".5" />
      );
    case "ring":     // 태극 원륜
      return (
        <g className="mRing">
          <circle cx="75" cy="58" r="26" fill="none" stroke={col}
                  strokeOpacity=".55" strokeWidth="1.2" />
          <circle cx="75" cy="58" r="18" fill="none" stroke={col}
                  strokeOpacity=".3" strokeWidth="1" />
        </g>
      );
    case "brush":
      return (
        <g className="mProp">
          <rect x="97" y="52" width="3" height="30" rx="1.5" fill={col} opacity=".8" />
          <path d="M97 82h3l-1.5 8z" fill={col} opacity=".6" />
        </g>
      );
    case "palanquin":
      return (
        <g className="mProp">
          <rect x="46" y="104" width="58" height="3" rx="1.5" fill={col} opacity=".6" />
          <circle cx="46" cy="112" r="4" fill="none" stroke={col}
                  strokeOpacity=".5" strokeWidth="1.2" />
          <circle cx="104" cy="112" r="4" fill="none" stroke={col}
                  strokeOpacity=".5" strokeWidth="1.2" />
        </g>
      );
    case "hand":     // 뒤에서 받치는 손
      return (
        <path className="mProp" d="M104 100c8-3 14 1 13 6-1 5-8 7-15 5z"
              fill={col} opacity=".55" />
      );
    case "blade":
      return (
        <g className="mProp">
          <rect x="104" y="46" width="2.4" height="46" rx="1.2" fill={col} opacity=".85" />
          <rect x="100" y="90" width="11" height="2.6" rx="1.3" fill={col} opacity=".6" />
        </g>
      );
    case "star":
      return (
        <g className="mProp">
          {[[62, 34], [72, 28], [83, 30], [90, 38], [86, 47], [75, 50], [66, 44]]
            .map(([x, y], i) => (
              <circle key={i} cx={x} cy={y} r="1.6" fill={col} opacity=".8" />
            ))}
        </g>
      );
    case "canopy":   // 꽃 일산
      return (
        <g className="mProp">
          <path d="M48 44c8-14 46-14 54 0z" fill={col} opacity=".45" />
          <rect x="74" y="44" width="2" height="26" fill={col} opacity=".5" />
        </g>
      );
    case "flower":
      return (
        <g className="mProp">
          {[0, 1, 2, 3, 4].map((i) => {
            const a = (i * Math.PI * 2) / 5 - Math.PI / 2;
            return (
              <ellipse key={i} cx={104 + Math.cos(a) * 6} cy={54 + Math.sin(a) * 6}
                       rx="4" ry="2.6" fill={col} opacity=".55"
                       transform={`rotate(${(a * 180) / Math.PI} ${104 + Math.cos(a) * 6} ${54 + Math.sin(a) * 6})`} />
            );
          })}
        </g>
      );
    default:
      return null;
  }
}

/* ── 입자 ────────────────────────────────────────────────── */
function FxLayer({ fx, col }: { fx: Fx; col: string }) {
  if (fx === "none") return null;
  const n = fx === "spark" ? 7 : 6;
  return (
    <g>
      {Array.from({ length: n }, (_, i) => {
        const x = 24 + i * 17;
        const delay = `${(i * 0.62).toFixed(2)}s`;
        if (fx === "petal") {
          return (
            <ellipse key={i} className="mFx" cx={x} cy={40 + (i % 3) * 22}
                     rx="3.4" ry="2.2" fill={col} opacity=".5"
                     style={{ animationDelay: delay }} />
          );
        }
        if (fx === "leaf") {
          return (
            <path key={i} className="mFx"
                  d={`M${x} ${44 + (i % 3) * 20}q4 -3 7 0q-3 4 -7 0z`}
                  fill={col} opacity=".45" style={{ animationDelay: delay }} />
          );
        }
        if (fx === "dust") {
          return (
            <circle key={i} className="mFx" cx={x} cy={70 + (i % 4) * 12} r="1.3"
                    fill={col} opacity=".4" style={{ animationDelay: delay }} />
          );
        }
        return (   // spark
          <circle key={i} className="mFx" cx={x} cy={46 + (i % 4) * 18} r="1.7"
                  fill={col} opacity=".65" style={{ animationDelay: delay }} />
        );
      })}
    </g>
  );
}

/* ── 실루엣 ──────────────────────────────────────────────── */
function Silhouette({ f, uid }: { f: SinsalFigure; uid: string }) {
  const col = f.color;

  if (f.aura === "absent") {
    // 공망 — 아무도 앉지 않았다. 윤곽선만 남긴다.
    return (
      <g>
        <path d="M75 34c-13 0-21 9-21 20 0 8 4 13 9 17-16 6-26 19-26 40v42h76v-42
                 c0-21-10-34-26-40 5-4 9-9 9-17 0-11-8-20-21-20z"
              fill="none" stroke={col} strokeOpacity=".65" strokeWidth="1"
              strokeDasharray="4 5" />
      </g>
    );
  }

  if (!f.human) {
    // 백호 — 사람이 아니라 짐승
    return (
      <g className="mBody">
        <path d="M32 118c6-26 24-40 43-40s37 14 43 40c2 9 1 16-3 18H35c-4-2-5-9-3-18z"
              fill={`url(#${uid}-g)`} />
        <path d="M56 78c-3-10-1-18 4-20 4-2 8 2 10 8m24 12c3-10 1-18-4-20-4-2-8 2-10 8"
              stroke={col} strokeOpacity=".55" strokeWidth="1.4" fill="none" />
        <g fill="#08060D" opacity=".55">
          <ellipse className="blinkk2" cx="64" cy="96" rx="2.2" ry="1.6" />
          <ellipse className="blinkk2" cx="86" cy="96" rx="2.2" ry="1.6" />
        </g>
        {[46, 60, 74, 88, 102].map((x) => (
          <path key={x} d={`M${x} 108q4 6 0 12`} stroke={col}
                strokeOpacity=".25" strokeWidth="1" fill="none" />
        ))}
      </g>
    );
  }

  if (f.prop === "twin") {
    // 원진 — 등을 돌린 둘
    return (
      <g className="mBody">
        <g opacity=".85">
          <circle cx="58" cy="54" r="11" fill={`url(#${uid}-g)`} />
          <path d="M58 66c-13 0-21 11-21 28v40h42v-40c0-17-8-28-21-28z"
                fill={`url(#${uid}-g)`} />
        </g>
        <g opacity=".45" transform="translate(34 0) scale(-1 1) translate(-150 0)">
          <circle cx="58" cy="58" r="10" fill={`url(#${uid}-g)`} />
          <path d="M58 69c-12 0-19 10-19 26v39h38v-39c0-16-7-26-19-26z"
                fill={`url(#${uid}-g)`} />
        </g>
      </g>
    );
  }

  const horse = f.prop === "horse";
  return (
    <g className="mBody">
      {horse && (
        <path d="M26 128c4-18 16-28 30-28h34c14 0 26 10 30 28z"
              fill={col} opacity=".22" />
      )}
      {f.female ? (
        <>
          <path d="M84 22c8-3 14 2 12 9-1.5 6-6 9-9 14l-3-8z" fill={`url(#${uid}-g)`} />
          <path d="M75 30c-12 0-19 8-19 19 0 3 .5 6 1.5 8l-4-2c-2 6 1 10 5 12"
                fill={`url(#${uid}-g)`} />
        </>
      ) : (
        <path d="M75 28c-13 0-20 8-20 18 0 4 1 7 3 10l-5-2c-1 6 2 10 6 12"
              fill={`url(#${uid}-g)`} />
      )}
      <circle cx="75" cy="52" r="12" fill={`url(#${uid}-g)`} />
      <g fill="#08060D" opacity=".5">
        <ellipse className="blinkk2" cx="70.5" cy="51" rx="1.6" ry="2.1" />
        <ellipse className="blinkk2" cx="79.5" cy="51" rx="1.6" ry="2.1" />
      </g>
      <path d="M75 64c-16 0-26 13-26 34v42h52v-42c0-21-10-34-26-34z"
            fill={`url(#${uid}-g)`} />
      <PropArt prop={f.prop} col={col} />
    </g>
  );
}

/* ── 본체 ────────────────────────────────────────────────── */
export default function SinsalFigure({
  sinsalKey, at, size = 150,
}: {
  sinsalKey: string;
  /** 어느 기둥에 앉았는가 — 인물 아래에 적는다 */
  at?: string[];
  size?: number;
}) {
  const f = figureOf(sinsalKey);
  const reduced = useReducedMotion();
  const hasClip = useHasClip(sinsalKey);
  const { ref, seen } = useAppear<HTMLDivElement>();
  const [open, setOpen] = useState(false);

  if (!f) return null;
  const uid = "sf-" + sinsalKey;
  const still = reduced;

  return (
    <figure
      ref={ref}
      className={
        "sfig" +
        (seen && !still ? " in" : "") +
        (still ? " still" : "") +
        " aura-" + f.aura
      }
      style={{ ["--c" as string]: f.color }}
    >
      <div
        className="sfig-art"
        style={{ width: size, cursor: "pointer" }}
        role="button"
        tabIndex={0}
        title={`${f.title} — 눌러서 제작 프롬프트 보기`}
        onClick={() => setOpen(true)}
        onKeyDown={(ev) => {
          if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); setOpen(true); }
        }}
      >
        <span className="halo" />
        {hasClip && !still ? (
          <video autoPlay muted playsInline loop
                 poster={`/sinsal/${sinsalKey}/poster.jpg`}>
            <source src={`/sinsal/${sinsalKey}/clip.webm`} type="video/webm" />
            <source src={`/sinsal/${sinsalKey}/clip.mp4`} type="video/mp4" />
          </video>
        ) : hasClip && still ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={`/sinsal/${sinsalKey}/poster.jpg`} alt={f.title} />
        ) : (
          <svg viewBox="0 0 150 150" role="img" aria-label={f.title}>
            <defs>
              <linearGradient id={`${uid}-g`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stopColor={f.color} stopOpacity=".72" />
                <stop offset="1" stopColor={f.color} stopOpacity=".12" />
              </linearGradient>
            </defs>
            <FxLayer fx={f.fx} col={f.color} />
            <Silhouette f={f} uid={uid} />
          </svg>
        )}
        <span className="slot">{hasClip ? "프롬프트" : `IMG · ${sinsalKey}`}</span>
      </div>
      {open && (
        <PromptModal kind="figure" id={sinsalKey} onClose={() => setOpen(false)} />
      )}

      <figcaption>
        <b className="t">{f.title}</b>
        <span className="w">{f.who}</span>
        {at && at.length > 0 && <span className="at">{at.join(" · ")}에 앉았소</span>}
        <p className="b">{f.beside}</p>
      </figcaption>
    </figure>
  );
}
