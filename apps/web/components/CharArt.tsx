"use client";

/**
 * 캐릭터 초상 — 스무 사람의 얼굴.
 *
 * ★ 여기가 통째로 없었습니다.
 *   `docs/10_에셋제작_발주서.md` §7 은 `/char/{id}/bust.png` 768×1024 를
 *   요구하고 제작 순서(§6)까지 정해 놓았는데, **그걸 그리는 코드가
 *   하나도 없었습니다.** `LensInfo` 에는 색(color)만 있고 그림을 가리키는
 *   필드가 없었습니다. 스무 장을 만들어도 갈 데가 없는 상태였습니다.
 *   (tools/asset_audit.py 가 잡았습니다)
 *
 * ★ 장면(Scene)과 같은 규칙입니다.
 *   파일이 있으면 그걸 쓰고, 없으면 자리표시로 버팁니다. 코드를 안 고치고
 *   `/public/char/{id}/` 에 넣기만 하면 그때부터 그게 나옵니다.
 *
 *     public/char/{id}/bust.png     768×1024 투명 PNG · 눈높이 y=380
 *     public/char/{id}/clip.webm    움직이는 초상 (선택)
 *     public/char/{id}/poster.jpg   clip 의 첫 프레임
 *
 * ★ 자리표시는 얼굴을 흉내내지 않습니다.
 *   반쯤 그린 얼굴은 없는 것보다 나쁩니다. 그 사람의 색과 한자 한 글자로
 *   자리만 잡습니다 — 에셋이 오면 그대로 갈아 끼웁니다.
 */
import { useEffect, useState } from "react";
import type { LensInfo } from "@/lib/lenses";
import { useSession } from "@/lib/store";
import PromptModal from "@/components/scene/PromptModal";

type Size = "chip" | "talk" | "card" | "full";

/*
 * ★ 표정.
 *
 *   얼굴 한 장으로 다 하면 **짚는 순간과 누그러뜨리는 순간이 같은
 *   얼굴**이 됩니다. 훅 0단은 아픈 데를 찌르는 자리이고, 만류 문구는
 *   그만 보라고 달래는 자리인데, 같은 표정이면 둘 다 힘을 잃습니다.
 *
 *   문장 뱅크를 세어 보고 셋으로 정했습니다 —
 *     짚는 말 26 · 누그러뜨리는 말 19 · 아니라고 하는 말 7
 *   「아니라고 하는 말」은 짚는 얼굴에 접습니다. 일곱 마디를 위해
 *   스무 명분을 더 그리는 것은 값이 안 맞습니다.
 *
 *   파일이 없으면 기본 얼굴로 내려옵니다 — 장면과 같은 규칙입니다.
 */
export type Mood = "base" | "cut" | "soft";

const FILE: Record<Mood, string> = {
  base: "bust.png",
  cut: "bust_cut.png",     // 짚는 얼굴 — 훅 찌르기
  soft: "bust_soft.png",   // 누그러뜨리는 얼굴 — 만류·마무리
};

const BOX: Record<Size, { w: number; h: number }> = {
  chip: { w: 48, h: 64 },     // 진열대 목록
  /*
   * 대사 옆. 얼굴이 글을 이기면 안 되고, 안 보이면 놓은 뜻이 없습니다.
   * 한 줄 높이(약 3.5줄)에 맞춥니다.
   */
  talk: { w: 66, h: 88 },
  card: { w: 132, h: 176 },   // 릴레이 카드 · 인장첩
  full: { w: 288, h: 384 },   // 그 사람의 자리 (b3)
};

/** 파일이 있는지 본다. 없으면 자리표시로 간다 — Scene 과 같은 방식. */
function useBust(id: string, mood: Mood) {
  const [src, setSrc] = useState<string | null | undefined>(undefined);
  useEffect(() => {
    let alive = true;
    const want = `/char/${id}/${FILE[mood]}`;
    const base = `/char/${id}/bust.png`;
    const ok = (u: string) =>
      fetch(u, { method: "HEAD" }).then((r) => r.ok).catch(() => false);

    (async () => {
      // 그 표정이 있으면 그걸, 없으면 기본 얼굴로 내려옵니다.
      if (mood !== "base" && (await ok(want))) {
        if (alive) setSrc(want);
        return;
      }
      if (alive) setSrc((await ok(base)) ? base : null);
    })();
    return () => { alive = false; };
  }, [id, mood]);
  return src;
}

/*
 * 움직이는 초상이 있는가.
 *
 * ★ 작은 칸에서는 안 씁니다. 48×64 짜리 조각에서 눈 깜빡임은 안 보이고
 *   영상만 스무 벌 받아 옵니다. 큰 자리(첫 대면·그 사람의 자리)에서만
 *   씁니다.
 *
 * ★ 기본 얼굴일 때만 씁니다. 표정이 따로 있는 자리는 그 표정이 뜻이라,
 *   움직이는 기본 얼굴로 덮으면 뜻이 사라집니다.
 */
function useClip(id: string, on: boolean) {
  const [ok, setOk] = useState(false);
  useEffect(() => {
    if (!on) return;
    let alive = true;
    fetch(`/char/${id}/clip.webm`, { method: "HEAD" })
      .then((r) => { if (alive) setOk(r.ok); })
      .catch(() => {});
    return () => { alive = false; };
  }, [id, on]);
  return ok;
}


export default function CharArt({
  lens, size = "card", className, mood = "base",
}: {
  lens: LensInfo;
  size?: Size;
  className?: string;
  /** 어떤 얼굴인가. 없으면 기본 얼굴로 내려옵니다. */
  mood?: Mood;
}) {
  const bust = useBust(lens.id, mood);
  const wantClip = (size === "full" || size === "card") && mood === "base";
  const clip = useClip(lens.id, wantClip && !!bust);

  /* 동작 줄이기를 켠 사람에게는 멈춘 그림으로 냅니다 */
  const [still, setStill] = useState(false);
  useEffect(() => {
    setStill(window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }, []);
  const { w, h } = BOX[size];
  const dim = !lens.released;

  /*
   * ★ 관리자는 눌러서 제작 프롬프트를 봅니다.
   *
   *   장면은 눌러서 볼 수 있는데 **캐릭터는 못 봤습니다.** 그림을
   *   맡기려면 그 사람 앞에서 바로 프롬프트가 나와야지, 도구를 따로
   *   돌려 찾아야 하면 안 찾습니다.
   *
   *   손님에게는 아무 일도 안 일어납니다 — 누를 수 있다는 표도 안 냅니다.
   */
  const admin = useSession((st) => st.admin);
  const [open, setOpen] = useState(false);

  return (
    <div
      className={`charart ${size} ${dim ? "off" : ""} ${className ?? ""}`}
      style={{ width: w, height: h, ["--cc" as string]: lens.color }}
      role={admin ? "button" : undefined}
      tabIndex={admin ? 0 : undefined}
      title={admin ? `${lens.name} — 눌러서 제작 프롬프트 보기` : undefined}
      onClick={admin ? (ev) => { ev.stopPropagation(); setOpen(true); } : undefined}
      onKeyDown={admin ? (ev) => {
        if (ev.key === "Enter" || ev.key === " ") {
          ev.preventDefault(); ev.stopPropagation(); setOpen(true);
        }
      } : undefined}
    >
      {admin && <span className="slot">프롬프트</span>}
      {open && (
        <PromptModal kind="char" id={lens.id} onClose={() => setOpen(false)} />
      )}
      {clip && !still ? (
        <video width={w} height={h} poster={bust ?? undefined}
               autoPlay muted playsInline loop aria-label={lens.name}>
          <source src={`/char/${lens.id}/clip.webm`} type="video/webm" />
          {/* mp4 는 투명이 없어 바탕색이 구워져 있습니다 */}
          <source src={`/char/${lens.id}/clip.mp4`} type="video/mp4" />
        </video>
      ) : bust ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={bust} alt={lens.name} width={w} height={h} loading="lazy" />
      ) : (
        /* 자리표시 — 얼굴을 흉내내지 않습니다. 색과 한자 한 글자. */
        <span className="ph" aria-label={lens.name}>
          <i>{lens.hanja?.[0] ?? lens.name[0]}</i>
        </span>
      )}
    </div>
  );
}
