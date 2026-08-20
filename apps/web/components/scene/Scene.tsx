"use client";

/**
 * 장면 컴포넌트 — docs/10_에셋제작_발주서.md
 *
 * 폴백 순서
 *   1. public/scene/{id}/clip.webm|mp4  가 있으면 영상
 *   2. 없으면 SVG 자리표시 (docs/09 §4 의 공통 네 요소로 구성)
 *   3. prefers-reduced-motion 이면 poster.jpg 정지컷 (없으면 정지 SVG)
 *
 * 무채색 클립 + 색 입히기는 docs/10 §4 대상 장면에만 적용합니다.
 */
import { useEffect, useState } from "react";
import { RATIO_BOX, SCENE_BY_ID, SEASON_PALETTE } from "./manifest";
import { seasonOf, type Season } from "@/lib/store";

function useReducedMotion() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const on = () => setReduced(mq.matches);
    on();
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return reduced;
}

/** 에셋이 실제로 있는지 확인. 없으면 SVG 자리표시로 간다. */
function useHasClip(id: string) {
  const [has, setHas] = useState<boolean | null>(null);
  useEffect(() => {
    let alive = true;
    fetch(`/scene/${id}/poster.jpg`, { method: "HEAD" })
      .then((r) => alive && setHas(r.ok))
      .catch(() => alive && setHas(false));
    return () => { alive = false; };
  }, [id]);
  return has;
}

/**
 * 자리표시 SVG.
 * 모든 실내 장면의 공통 네 요소 — 빛기둥 · 부유 입자 · 성좌 원륜 · 주렴.
 * (실제 아트는 reference/sajudang.html 의 SVG 와 발주 에셋으로 대체됩니다.)
 */
function Placeholder({ id, season }: { id: string; season: Season }) {
  const spec = SCENE_BY_ID[id];
  const [w, h] = RATIO_BOX[spec?.ratio ?? "16:9"];
  const pal = SEASON_PALETTE[season];
  const uid = `s-${id}`;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label={spec?.name ?? id}>
      <defs>
        <linearGradient id={`${uid}-sky`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={pal.sky} />
          <stop offset="1" stopColor="#0C0A12" />
        </linearGradient>
        <linearGradient id={`${uid}-beam`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="var(--c)" stopOpacity=".22" />
          <stop offset="1" stopColor="var(--c)" stopOpacity="0" />
        </linearGradient>
      </defs>

      <rect width={w} height={h} fill={`url(#${uid}-sky)`} />

      {/* 빛기둥 — 위에서 내려오는 광선 */}
      <polygon points={`${w * 0.34},0 ${w * 0.66},0 ${w * 0.8},${h} ${w * 0.2},${h}`}
               fill={`url(#${uid}-beam)`} />

      {/* 성좌 원륜 — 12방위 눈금 */}
      <g className="scnRing" transform={`translate(${w / 2} ${h * 0.52})`}>
        <circle r={Math.min(w, h) * 0.26} fill="none"
                stroke="var(--c)" strokeOpacity=".3" strokeWidth="1" />
        {Array.from({ length: 12 }, (_, i) => {
          const a = (i * Math.PI) / 6;
          const r1 = Math.min(w, h) * 0.26;
          const r2 = r1 + 5;
          return (
            <line key={i}
                  x1={Math.cos(a) * r1} y1={Math.sin(a) * r1}
                  x2={Math.cos(a) * r2} y2={Math.sin(a) * r2}
                  stroke="var(--c)" strokeOpacity=".45" strokeWidth="1" />
          );
        })}
      </g>

      {/* 부유 입자 — 금빛 알갱이 */}
      {Array.from({ length: 9 }, (_, i) => (
        <circle key={i} className="scnDust"
                cx={(w / 10) * (i + 0.5)} cy={h * (0.35 + (i % 4) * 0.16)} r="1.6"
                fill="var(--c)" opacity=".5"
                style={{ animationDelay: `${(i * 0.4).toFixed(1)}s` }} />
      ))}

      {/* 주렴 — 구슬발 */}
      {["#E5B87A", "#D98BA5", "#A896D4", "#7FC4BC"].map((c, i) => (
        <line key={c} x1={(w / 5) * (i + 1)} y1="0"
              x2={(w / 5) * (i + 1)} y2={h * 0.2}
              stroke={c} strokeOpacity=".3" strokeWidth="1.5" />
      ))}

      {/* 계절 꽃 */}
      {Array.from({ length: 5 }, (_, i) => (
        <circle key={`f${i}`} cx={w * (0.1 + i * 0.2)} cy={h * 0.1} r="3"
                fill={pal.flower} opacity=".55" />
      ))}
    </svg>
  );
}

export default function Scene({ id, className }: { id: string; className?: string }) {
  const spec = SCENE_BY_ID[id];
  const reduced = useReducedMotion();
  const hasClip = useHasClip(id);
  const season = seasonOf();

  if (!spec) return null;

  const body = hasClip ? (
    reduced ? (
      // eslint-disable-next-line @next/next/no-img-element
      <img src={`/scene/${id}/poster.jpg`} alt={spec.name} />
    ) : (
      <video
        className={spec.tint ? "scene-video" : undefined}
        poster={`/scene/${id}/poster.jpg`}
        autoPlay muted playsInline loop={spec.loop}
      >
        <source src={`/scene/${id}/clip.webm`} type="video/webm" />
        <source src={`/scene/${id}/clip.mp4`} type="video/mp4" />
      </video>
    )
  ) : (
    <Placeholder id={id} season={season} />
  );

  return (
    <div className={`sceneart ${className ?? ""}`}>
      {body}
      {hasClip && spec.tint && <span className="scene-tint" />}
      {!hasClip && <span className="slot">IMG · {id}</span>}
    </div>
  );
}
