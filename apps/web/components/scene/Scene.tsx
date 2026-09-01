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
import { LENS_BY_ID } from "@/lib/lenses";

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
 * 쓸 에셋이 어디 있는지 고른다. 없으면 SVG 자리표시로 간다.
 *
 * 대문은 계절 그림을 넣을 수 있게 열어 두되 **한 장이면 충분합니다.**
 *   /scene/gate/{계절}/  있으면 이걸 씁니다
 *   /scene/gate/         없으면 이걸로 내려옵니다  ← 기본
 *
 * 한 장만 넣어도 사계절 내내 나옵니다. 나중에 계절을 넣고 싶어지면
 * 계절 폴더에 넣기만 하면 그때부터 그게 우선합니다. 코드는 그대로입니다.
 *
 * 계절 폴더를 먼저 보고 없을 때만 내려오는 순서라야 합니다. 반대로 하면
 * 계절 그림을 넣어도 영영 안 쓰입니다.
 */
function useClipBase(seasonal: string | null, fallback: string) {
  const [base, setBase] = useState<string | null | undefined>(undefined);
  useEffect(() => {
    let alive = true;
    const ok = (dir: string) =>
      fetch(`${dir}poster.jpg`, { method: "HEAD" })
        .then((r) => r.ok)
        .catch(() => false);

    (async () => {
      if (seasonal && (await ok(seasonal))) { if (alive) setBase(seasonal); return; }
      if (alive) setBase((await ok(fallback)) ? fallback : null);
    })();
    return () => { alive = false; };
  }, [seasonal, fallback]);
  return base;   // undefined = 아직 확인 중 · null = 에셋 없음
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

/**
 * 장면 하나를 그리는 미디어 한 겹. 같은 에셋을 두 번 쓸 때(가운데 + 흘림)
 * 이 함수를 두 번 부릅니다. 브라우저는 같은 URL 을 한 번만 받아 옵니다.
 */
function Media({ base, name, loop, tintClass, reduced, decorative }: {
  base: string; name: string; loop: boolean;
  tintClass?: string; reduced: boolean; decorative?: boolean;
}) {
  if (reduced) {
    // eslint-disable-next-line @next/next/no-img-element
    return <img className={tintClass} src={`${base}poster.jpg`}
                alt={decorative ? "" : name} />;
  }
  return (
    <video
      className={tintClass}
      poster={`${base}poster.jpg`}
      autoPlay muted playsInline loop={loop}
      key={base}
    >
      <source src={`${base}clip.webm`} type="video/webm" />
      <source src={`${base}clip.mp4`} type="video/mp4" />
    </video>
  );
}

/**
 * bleed — 같은 장면을 크게 흐려 뒤에 한 겹 더 깝니다.
 *
 * 9:16 에셋을 넓은 창에 `cover` 로 늘리면 세로 구도가 가로 한 줄로 잘려
 * 그림이 사라집니다. 그래서 가운데는 `contain`(세로를 창에 맞춤)으로
 * 두고, 남는 좌우를 이 겹이 채웁니다.
 *
 * ★ 이 겹도 **영상**입니다. 가운데가 움직이는데 배경이 정지컷이면
 *   어긋나 보입니다. 같은 파일이라 내려받기는 한 번입니다.
 *   prefers-reduced-motion 이면 두 겹 다 poster.jpg 로 내려갑니다.
 */
/**
 * 장면 안에 선 사람.
 *
 * 그림이 없으면 아무것도 안 그립니다 — 자리표시 한자를 배경 위에
 * 띄우면 그건 사람이 아니라 도장입니다.
 */
function SceneFigure({ lens }: { lens?: string }) {
  const cur = useSession((st) => st.cur);
  const l = LENS_BY_ID[lens ?? cur];
  const [has, setHas] = useState(false);
  useEffect(() => {
    if (!l) return;
    let alive = true;
    fetch(`/char/${l.id}/bust.png`, { method: "HEAD" })
      .then((r) => { if (alive) setHas(r.ok); })
      .catch(() => {});
    return () => { alive = false; };
  }, [l]);
  if (!l || !has) return null;
  return (
    <span className="scenefig">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={`/char/${l.id}/bust.png`} alt={l.name} />
    </span>
  );
}


export default function Scene({ id, className, bleed, figure }: {
  id: string; className?: string; bleed?: boolean;
  /**
   * ★ 사람을 **장면 안에 세웁니다** (레이어드).
   *
   *   전에는 배경 한 칸, 그 아래 초상 한 칸이었습니다. 두 그림이 따로
   *   놓이면 손님에게는 「그림 두 장」이지 **그 방에 있는 사람**이
   *   아닙니다. 도령이 방 안에 있어야 마주 앉은 느낌이 납니다.
   *
   *   장면 위에 겹칩니다 — 바닥에 발을 딛듯 아래 가운데에 세우고,
   *   장면의 페이드가 그 위로 흐르게 둡니다.
   *
   *   캐릭터 id 를 주면 그 사람, `true` 면 지금 고른 사람입니다.
   */
  figure?: string | true;
}) {
  const spec = SCENE_BY_ID[id];
  const reduced = useReducedMotion();
  const override = useSession((st) => st.seasonOverride);
  const admin = useSession((st) => st.admin);
  const season = override ?? seasonOf();
  // 훅은 조건 앞에 와야 합니다. spec 이 없어도 순서가 흔들리면 안 됩니다.
  const chosen = useClipBase(
    spec?.seasonal ? `/scene/${id}/${season}/` : null,
    `/scene/${id}/`,
  );
  const base = chosen ?? `/scene/${id}/`;
  const hasClip = chosen === undefined ? null : chosen !== null;
  const [open, setOpen] = useState(false);

  if (!spec) return null;

  const body = hasClip ? (
    <Media base={base} name={spec.name} loop={spec.loop} reduced={reduced}
           tintClass={spec.tint ? `scene-video ${spec.tint}` : undefined} />
  ) : (
    <Placeholder id={id} season={season} />
  );

  /*
   * 장면을 클릭하면 제작 프롬프트가 뜹니다.
   * 참조 구현체의 showScn() 을 옮긴 것입니다 — 에셋을 뽑을 때 씁니다.
   *
   * ★ 레일이 켜져 있을 때만 눌립니다. 두 가지 이유입니다.
   *   1) 제작 프롬프트는 내부 문서입니다. 손님에게 보일 것이 아닙니다.
   *   2) 대문(a1)은 그림이 화면을 다 덮습니다. 그림이 항상 눌리면
   *      "다음으로" 를 누를 자리가 없어지고 매 클릭이 모달에 막힙니다.
   * 레일이 켜졌을 때는 stopPropagation 으로 부모의 '다음으로' 를 막습니다.
   */
  const pickable = admin;

  return (
    <>
      {bleed && (
        <span className="scene-bleed" aria-hidden>
          {hasClip
            ? <Media base={base} name={spec.name} loop={spec.loop}
                     reduced={reduced} decorative />
            : <Placeholder id={id} season={season} />}
        </span>
      )}
      <div
        /* box 가 있으면 가로 원본이라 높이 대신 비율로 잡습니다 */
        className={`sceneart ${spec.box ? "boxed" : ""} ${className ?? ""}`}
        role={pickable ? "button" : undefined}
        tabIndex={pickable ? 0 : undefined}
        title={pickable ? `${spec.name} — 눌러서 제작 프롬프트 보기` : undefined}
        /*
         * ★ 상자 비율(--sr)과 초점(--sf).
         *   들어오는 영상은 전부 9:16 인데 글 위 장면은 16:9 띠로
         *   보여 줍니다. 상자를 잡고 object-fit:cover 로 채웁니다 —
         *   안 그러면 세로 영상이 폭의 178% 높이로 흘러 아래 버튼이
         *   화면 밖으로 밀립니다.
         */
        style={{
          ["--sr" as string]:
            (spec.box ?? (spec.ratio === "1:1" ? "1:1" : "4:3"))
              .replace(":", " / "),
          ...(spec.focus ? { ["--sf" as string]: spec.focus } : {}),
          ...(pickable ? {} : { cursor: "inherit" }),
        } as React.CSSProperties}
        onClick={pickable ? (ev) => { ev.stopPropagation(); setOpen(true); } : undefined}
        onKeyDown={pickable ? (ev) => {
          if (ev.key === "Enter" || ev.key === " ") {
            ev.preventDefault(); ev.stopPropagation(); setOpen(true);
          }
        } : undefined}
      >
        {body}
        {figure && <SceneFigure lens={figure === true ? undefined : figure} />}
        {hasClip && spec.tint && <span className={`scene-tint ${spec.tint}`} />}
        {pickable && (
          <span className="slot">{hasClip ? "프롬프트" : `IMG · ${id}`}</span>
        )}
      </div>
      {open && (
        <PromptModal kind="scene" id={id} onClose={() => setOpen(false)} />
      )}
    </>
  );
}
