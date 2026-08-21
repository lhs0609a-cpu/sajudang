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
import PromptModal from "./PromptModal";
import { RATIO_BOX, SCENE_BY_ID, SEASON_PALETTE } from "./manifest";
import { seasonOf, useSession, type Season } from "@/lib/store";

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

/**
 * 에셋이 실제로 있는지 확인. 없으면 SVG 자리표시로 간다.
 *
 * 계절을 타는 장면(대문)은 계절 폴더를 봅니다 — /scene/gate/spring/ ….
 * 꽃이 계절마다 다릅니다(벚꽃·능소화·국화·매화). 착색으로는 꽃 모양을
 * 못 바꾸므로 그림 자체가 넉 장이어야 합니다. 한 폴더만 보면 넉 장을
 * 만들어 넣어도 한 장만 쓰이고 나머지 세 계절은 자리표시로 남습니다.
 */
function useHasClip(base: string) {
  const [has, setHas] = useState<boolean | null>(null);
  useEffect(() => {
    let alive = true;
    fetch(`${base}poster.jpg`, { method: "HEAD" })
      .then((r) => alive && setHas(r.ok))
      .catch(() => alive && setHas(false));
    return () => { alive = false; };
  }, [base]);
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
  const override = useSession((st) => st.seasonOverride);
  const season = override ?? seasonOf();
  // 훅은 조건 앞에 와야 합니다. spec 이 없어도 순서가 흔들리면 안 됩니다.
  const base = spec?.seasonal
    ? `/scene/${id}/${season}/`
    : `/scene/${id}/`;
  const hasClip = useHasClip(base);
  const [open, setOpen] = useState(false);

  if (!spec) return null;

  const body = hasClip ? (
    reduced ? (
      // eslint-disable-next-line @next/next/no-img-element
      <img src={`${base}poster.jpg`} alt={spec.name} />
    ) : (
      <video
        className={spec.tint ? "scene-video" : undefined}
        poster={`${base}poster.jpg`}
        autoPlay muted playsInline loop={spec.loop}
        key={base}
      >
        <source src={`${base}clip.webm`} type="video/webm" />
        <source src={`${base}clip.mp4`} type="video/mp4" />
      </video>
    )
  ) : (
    <Placeholder id={id} season={season} />
  );

  /*
   * 장면을 클릭하면 제작 프롬프트가 뜹니다.
   * 참조 구현체의 showScn() 을 옮긴 것입니다 — 에셋을 뽑을 때 씁니다.
   */
  return (
    <>
      <div
        className={`sceneart ${className ?? ""}`}
        role="button"
        tabIndex={0}
        title={`${spec.name} — 눌러서 제작 프롬프트 보기`}
        onClick={() => setOpen(true)}
        onKeyDown={(ev) => {
          if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); setOpen(true); }
        }}
      >
        {body}
        {hasClip && spec.tint && <span className="scene-tint" />}
        <span className="slot">{hasClip ? "프롬프트" : `IMG · ${id}`}</span>
      </div>
      {open && (
        <PromptModal kind="scene" id={id} onClose={() => setOpen(false)} />
      )}
    </>
  );
}
